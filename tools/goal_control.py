"""Cooperative goal contracts, input-bound receipts and corrective obligations.

These records detect accidental drift; they are not a security boundary against
an actor who can replace checks, inputs and receipts together.
"""
from __future__ import annotations

import json
import hashlib
import subprocess
from pathlib import Path

from outcome_control import canonical, digest


class ContractError(ValueError):
    pass


def read(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def declared(goal):
    values = list(goal.get('inputs', [])) + list(goal.get('requirement_refs', []))
    for item in goal.get('acceptance', []):
        values += list(item.get('inputs', [])) + list(item.get('requirement_refs', []))
    review = goal.get('review', {})
    if isinstance(review, dict):
        values += [review[key] for key in ('framing', 'request', 'failure_evidence') if key in review]
    return values


def file_ref(root, value):
    name = value if isinstance(value, str) else value.get('path') if isinstance(value, dict) else None
    if not isinstance(name, str) or not name:
        raise ContractError('declared inputs and requirement_refs need file paths')
    path = root / name
    try:
        raw = path.read_bytes()
        return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}
    except OSError as exc:
        raise ContractError('cannot read declared input ' + name) from exc


def contract(goal, root):
    # Evidence and progress are mutable; all other acceptance fields remain authority.
    items = [{k: v for k, v in item.items() if k not in ('status', 'evidence', 'blocker')}
             for item in goal['acceptance']]
    requirements = list(goal.get('requirement_refs', []))
    for item in goal['acceptance']:
        requirements += list(item.get('requirement_refs', []))
    review = goal.get('review', {})
    if isinstance(review, dict):
        requirements += [review[key] for key in ('framing', 'request', 'failure_evidence') if key in review]
    refs = [file_ref(root, ref) for ref in requirements]
    return {'goal': goal['goal'], 'kind': goal.get('kind'), 'review': goal.get('review'), 'acceptance': items,
            'requirement_refs': goal.get('requirement_refs', []),
            'inputs': goal.get('inputs', []), 'declared_files': refs}


def snapshot(root, goal):
    try:
        proc = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
                              cwd=root, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError('cannot inventory source inputs with git') from exc
    if proc.returncode:
        raise ContractError('cannot inventory source inputs with git')
    names = set(proc.stdout.decode().split('\0')) - {''}
    refs = []
    for name in sorted(names):
        if name.startswith('.agent/'):
            generated = {'.gitignore', 'goal.json', 'goal-status.json', 'goal-contract.json',
                         'finish-state.json', 'reflection-state.json', 'reflection-receipt.json',
                         'hook-state.json', 'hook-events.jsonl'}
            tail = name[len('.agent/'):]
            if tail in generated or tail.startswith('gaps/'):
                continue
        path = root / name
        refs.append(file_ref(root, name) if path.is_file() else {'path': name, 'missing': True})
    refs += [file_ref(root, ref) for ref in declared(goal)]
    # Explicit local evidence is an input even under the generated-state directory.
    import re
    for item in goal.get('acceptance', []):
        for token in re.findall(r"[\w./-]+", item.get('evidence', '')):
            candidate = (root / token).resolve()
            if candidate.is_relative_to(root) and candidate.is_file():
                refs.append(file_ref(root, token))
    # The executing validator is an input even when adopted outside its own repository.
    names = ['goal_control.py', 'finish_check.py', 'outcome_control.py']
    if goal.get('kind') in ('methodology', 'control') or isinstance(goal.get('review'), dict):
        names.append('blind_review.py')
    validators = [file_ref(Path(__file__).parent, p) for p in names]
    disk_goal = read(root / '.agent/goal.json')
    disk_contract = digest(contract(disk_goal, root)) if disk_goal.get('acceptance') else None
    return {'files': refs, 'validators': validators, 'goal_contract': disk_contract}


def pin_contract(root, goal):
    current = contract(goal, root)
    identity = digest(current)
    path = root / '.agent/goal-contract.json'
    previous = read(path)
    if previous.get('digest') and previous['digest'] != identity:
        revision = goal.get('supersedes', {})
        if not (isinstance(revision, dict) and revision.get('digest') == previous['digest']
                and isinstance(revision.get('reason'), str) and len(revision['reason'].split()) >= 3
                and isinstance(revision.get('authority'), str) and revision['authority'].strip()):
            raise ContractError('acceptance contract changed; supersedes needs previous digest, reason and authority evidence')
        # A pointer, not prose asserting authorization.
        from finish_check import cites
        if not cites(root, revision['authority']):
            raise ContractError('supersedes authority must cite a repository file or URL')
        history = previous.get('history', []) + [{k: v for k, v in previous.items() if k != 'history'}]
    else:
        history = previous.get('history', [])
    write(path, {'digest': identity, 'contract': current, 'supersedes': goal.get('supersedes'), 'history': history})
    return identity


def receipt_state(root, goal):
    receipt = read(root / '.agent/goal-status.json')
    if receipt.get('schema') != 'goal-receipt/v2':
        return 'unverified', 'missing or legacy receipt'
    try:
        if receipt.get('contract_digest') != digest(contract(goal, root)):
            return 'stale', 'acceptance contract changed'
        if receipt.get('snapshot') != snapshot(root, goal):
            return 'stale', 'source, validator or declared input changed'
    except (ContractError, OSError, ValueError) as exc:
        return 'stale', str(exc)
    return ('verified', 'current successful receipt') if receipt.get('met') is True else ('unverified', 'last checks did not pass')


def require_correction(root, trigger, evidence):
    path = root / '.agent/reflection-state.json'
    state = read(path)
    obligation = {'trigger': trigger, 'evidence': evidence}
    if obligation not in state.get('obligations', []):
        state.setdefault('obligations', []).append(obligation)
        state['resolved'] = False
        state['status'] = 'pending'
        write(path, state)


def reflection_check(goal, root, timeout, runner):
    path = root / '.agent/reflection-state.json'
    state = read(path)
    if not state.get('obligations') or state.get('resolved'):
        return None
    reflection = goal.get('reflection', {})
    interventions = reflection.get('interventions', []) if isinstance(reflection, dict) else []
    if not isinstance(interventions, list) or not interventions:
        return 'corrective intervention required: observation, evidence, hypothesis, expected_effect and run'
    from finish_check import sentence, cites, TARGET
    for intervention in interventions:
        if not isinstance(intervention, dict) or not all(sentence(intervention.get(k)) for k in
                ('observation', 'hypothesis', 'expected_effect')) or not isinstance(intervention.get('evidence'), str) \
                or not cites(root, intervention['evidence']) or not isinstance(intervention.get('run'), str) \
                or not TARGET.fullmatch(intervention['run']):
            return 'corrective intervention has incomplete observation, evidence, hypothesis, expected_effect or run'
        before = snapshot(root, goal)
        result, reason = runner(root, intervention['run'], timeout)
        after = snapshot(root, goal)
        status = 'supported' if result == 'met' and before == after else 'refuted' if before == after else 'inconclusive'
        write(root / '.agent/reflection-receipt.json', {'intervention': intervention, 'status': status,
              'contract_digest': digest(contract(goal, root)), 'snapshot': after, 'why': reason})
        if status != 'supported':
            return 'corrective intervention ' + status
    state['resolved'] = True
    state['status'] = 'supported'
    write(path, state)
    return None
