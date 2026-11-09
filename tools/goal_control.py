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


def intervention_specifications(goal):
    reflection = goal.get('reflection', {})
    interventions = reflection.get('interventions', []) if isinstance(reflection, dict) else []
    if not isinstance(interventions, list):
        return interventions
    return [{key: value for key, value in item.items() if key != 'status'}
            if isinstance(item, dict) else item for item in interventions]


def retained_goal(root):
    """Recover immutable authority only; never invent progress or evidence."""
    saved = read(root / '.agent/goal-contract.json').get('contract')
    if not isinstance(saved, dict) or not isinstance(saved.get('goal'), str) or not isinstance(saved.get('acceptance'), list):
        return None
    return {key: saved[key] for key in ('goal', 'kind', 'review', 'acceptance', 'requirement_refs', 'inputs') if key in saved}


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
    specifications = intervention_specifications(goal)
    evidence_items = list(goal.get('acceptance', [])) + (specifications if isinstance(specifications, list) else [])
    for item in evidence_items:
        if not isinstance(item, dict):
            continue
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
    if not (root / '.agent/goal.json').exists():
        disk_goal = retained_goal(root) or {}
    disk_contract = digest(contract(disk_goal, root)) if disk_goal.get('acceptance') else None
    return {'files': refs, 'validators': validators, 'goal_contract': disk_contract,
            'interventions': specifications, 'disk_interventions': intervention_specifications(disk_goal)}


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
        require_correction(root, 'acceptance-revision', previous['digest'] + ' -> ' + identity)
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
    reflection = read(root / '.agent/reflection-state.json')
    if reflection.get('obligations') and (not reflection.get('resolved') or reflection.get('resolution_identity') != observation_identity(root, goal)):
        return 'unverified', 'corrective obligation unresolved for current inputs'
    return ('verified', 'current successful receipt') if receipt.get('met') is True else ('unverified', 'last checks did not pass')


def observation_identity(root, goal):
    return {'contract_digest': digest(contract(goal, root)), 'snapshot_digest': digest(snapshot(root, goal))}


def require_correction(root, trigger, evidence):
    path = root / '.agent/reflection-state.json'
    state = read(path)
    goal = read(root / '.agent/goal.json')
    try:
        identity = observation_identity(root, goal) if goal.get('acceptance') else None
    except ContractError as exc:
        identity = {'unavailable': str(exc)}
    obligation = {'trigger': trigger, 'evidence': evidence, 'observation_identity': identity}
    if obligation not in state.get('obligations', []):
        state.setdefault('obligations', []).append(obligation)
        state['resolved'] = False
        state['status'] = 'pending'
        write(path, state)


def refresh_stale_evidence(root, goal, results, before, evaluated_contract):
    """Resolve only stale evidence using newly executed, stable full acceptance."""
    path = root / '.agent/reflection-state.json'
    state = read(path)
    obligations = state.get('obligations', [])
    if not obligations or any(item.get('trigger') != 'stale-evidence' for item in obligations):
        return False
    if not results or not all(item['state'] == 'met' for item in results):
        return False
    current = observation_identity(root, goal)
    if current != {'contract_digest': evaluated_contract, 'snapshot_digest': digest(before)}:
        return False
    if state.get('resolution_identity') == current and state.get('resolved'):
        return True
    previous = read(root / '.agent/goal-status.json')
    old_identity = {'contract_digest': previous.get('contract_digest'),
                    'snapshot_digest': digest(previous['snapshot']) if 'snapshot' in previous else None}
    receipt = {'kind': 'freshness-verification', 'status': 'supported',
               'before': old_identity, 'after': current, 'obligations': obligations,
               'observation': 'Prior acceptance evidence required freshness verification for the current observations.',
               'explanation': 'Input drift alone does not demonstrate a product failure.',
               'prediction': 'Explicit full acceptance verification passes on stable current inputs.',
               'checks': [dict(item) for item in results],
               'observed_effect': 'All current acceptance checks passed with stable inputs.',
               'interpretation': 'Fresh acceptance and input stability only; no causal correction claim.'}
    receipt_path = root / '.agent/reflection-receipt.json'
    previous = read(receipt_path)
    history = previous.get('history', []) + ([{k: v for k, v in previous.items() if k != 'history'}] if previous else [])
    write(receipt_path, dict(receipt, history=history))
    state['resolved'] = True
    state['status'] = 'supported'
    state['resolution_identity'] = current
    write(path, state)
    return True


def reflection_check(goal, root, timeout, runner):
    path = root / '.agent/reflection-state.json'
    state = read(path)
    current = observation_identity(root, goal)
    if not state.get('obligations'):
        return None
    if state.get('resolved') and state.get('resolution_identity') == current:
        return None
    # Resolution belongs to the exact contract and observations that were checked.
    if state.get('resolved'):
        state['resolved'] = False
        state['status'] = 'pending'
        write(path, state)
    reflection = goal.get('reflection', {})
    interventions = reflection.get('interventions', []) if isinstance(reflection, dict) else []
    if not isinstance(interventions, list) or not interventions:
        return 'corrective intervention required: observation, evidence, hypothesis, expected_effect and run'
    from finish_check import sentence, cites, TARGET
    targets = {item.get('run') for item in goal['acceptance'] if item.get('run')}
    for intervention in interventions:
        if not isinstance(intervention, dict) or not all(sentence(intervention.get(k)) for k in
                ('observation', 'hypothesis', 'expected_effect')) or not isinstance(intervention.get('evidence'), str) \
                or not cites(root, intervention['evidence']) or not isinstance(intervention.get('run'), str) \
                or not TARGET.fullmatch(intervention['run']):
            return 'corrective intervention has incomplete observation, evidence, hypothesis, expected_effect or run'
        if intervention['run'] not in targets:
            return 'corrective intervention run must be a current acceptance target'
        before = observation_identity(root, goal)
        result, reason = runner(root, intervention['run'], timeout)
        try:
            after = observation_identity(root, goal)
        except ContractError as exc:
            after = {'unavailable': str(exc)}
        status = 'supported' if result == 'met' and before == after else 'refuted' if before == after else 'inconclusive'
        receipt = {'intervention': intervention, 'status': status, 'before': before, 'after': after,
                   'observed_effect': 'acceptance target passed' if result == 'met' else 'acceptance target failed',
                   'interpretation': 'Target exit and input stability only; hypothesis causality and semantic expected effect remain unverified.',
                   'why': reason}
        receipt_path = root / '.agent/reflection-receipt.json'
        previous = read(receipt_path)
        history = previous.get('history', []) + ([{k: v for k, v in previous.items() if k != 'history'}] if previous else [])
        write(receipt_path, dict(receipt, history=history))
        if status != 'supported':
            return 'corrective intervention ' + status
    state['resolved'] = True
    state['status'] = 'supported'
    state['resolution_identity'] = observation_identity(root, goal)
    write(path, state)
    return None
