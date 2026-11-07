#!/usr/bin/env python3
"""Opt-in task authority, evidence and recovery gates. Python 3.9+, no commands from data."""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

# Must equal project_work.TASK_SCHEMAS; tools/tests/test_project_work.py enforces it.
TASK_SCHEMAS = ('task-record/v1', 'axioms-task/v1')

SCHEMA = 'outcome-control/v1'
CLAIMS = ('implemented', 'verified', 'integrated', 'available', 'accepted')
CLASSES = ('mechanical', 'expert', 'human')
WIP = ('assumptions', 'changes', 'claims', 'experiments')
EVENTS = ('start', 'resume', 'pre-write', 'pre-integration', 'pre-completion')
HEX = re.compile(r'^[0-9a-f]{64}$')
MAX_BYTES = 4 * 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def same_json(left, right):
    # Python equality conflates booleans and numbers, including inside containers.
    return canonical(left) == canonical(right)


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def obj(value, message):
    require(isinstance(value, dict), message + ' must be an object')
    return value


def exact(value, required, optional=()):
    obj(value, 'record')
    require(set(required) <= set(value) <= set(required) | set(optional),
            'record has missing or unknown fields: ' + ','.join(sorted(set(required) ^ set(value))))


def text(value, name):
    require(isinstance(value, str) and bool(value.strip()), name + ' must be nonempty text')


def strings(value, name):
    require(isinstance(value, list), name + ' must be an array')
    for item in value:
        text(item, name)
    require(len(value) == len(set(value)), name + ' must be unique')


def stamp(value):
    text(value, 'timestamp')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('invalid timestamp')
    require(result.tzinfo is not None and result.utcoffset() is not None, 'timestamp must have timezone')
    return result


def relative(value):
    text(value, 'path')
    path = PurePosixPath(value)
    require(not path.is_absolute() and value == path.as_posix() and
            all(p not in ('', '.', '..') for p in path.parts) and '\\' not in value,
            'path must be normalized repository-relative')
    return path


def safe_path(root, value):
    path = relative(value)
    require(not Path(root).is_symlink(), 'symlink root forbidden')
    root = Path(root).resolve()
    current = root
    for part in path.parts:
        current = current / part
        require(not current.is_symlink(), 'symlink input forbidden: ' + value)
    require(current.is_relative_to(root), 'path escapes root')
    return current


def read_bytes(path):
    require(path.is_file() and not path.is_symlink(), 'missing or symlink file: ' + str(path))
    require(path.stat().st_size <= MAX_BYTES, 'file exceeds 4 MiB')
    return path.read_bytes()


def read_json(path):
    return json.loads(read_bytes(Path(path)))


def checked_ref(root, ref):
    exact(ref, ('path', 'sha256'))
    require(isinstance(ref['sha256'], str) and HEX.fullmatch(ref['sha256']), 'invalid sha256')
    raw = read_bytes(safe_path(root, ref['path']))
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'altered file: ' + ref['path'])
    return raw


def source_digest(manifest):
    require(isinstance(manifest, list) and bool(manifest), 'source must be a nonempty manifest')
    paths = []
    for ref in manifest:
        exact(ref, ('path', 'sha256'))
        relative(ref['path'])
        require(isinstance(ref['sha256'], str) and HEX.fullmatch(ref['sha256']), 'invalid source sha256')
        paths.append(ref['path'])
    require(len(set(paths)) == len(paths), 'duplicate source path')
    return digest(sorted(manifest, key=lambda r: r['path']))


def authority_digest(task):
    """Binds meaning even when the author forgets to increment authorization.revision."""
    return digest({'task': task['id'], 'outcome': task['outcome'], 'acceptance': task['acceptance'],
                   'authorization': task['control']['authorization'],
                   'wipPolicy': {k: task['control']['wip'][k] for k in ('limits', 'exceptions')}})


def evidence(root, ref, task, claim, now):
    proof = json.loads(checked_ref(root, ref))
    exact(proof, ('schema', 'claim', 'scenario', 'authorityDigest', 'sourceDigest', 'conditions', 'class', 'producer',
                  'reviewer', 'observedAt', 'status', 'native'), ('expiresAt',))
    control = task['control']
    rule = control['authorization']['claims'][claim]
    require(proof['schema'] == 'outcome-evidence/v1', 'unknown evidence schema')
    require(proof['claim'] == claim and proof['scenario'] == rule['scenario'], 'evidence claim/scenario mismatch')
    require(proof['authorityDigest'] == authority_digest(task), 'stale evidence authority')
    require(proof['sourceDigest'] == source_digest(control['source']), 'wrong evidence source')
    require(same_json(proof['conditions'], control['conditions']), 'evidence condition mismatch')
    require(proof['class'] in rule['classes'], 'evidence class not authorized')
    require(proof['producer'] in rule['producers'] and proof['reviewer'] in rule['reviewers'],
            'evidence producer/reviewer not authorized')
    require(proof['status'] == 'passed', 'evidence is not passed')
    observed = stamp(proof['observedAt'])
    require(observed <= now, 'future evidence')
    if 'expiresAt' in proof:
        require(observed <= stamp(proof['expiresAt']) and now <= stamp(proof['expiresAt']), 'expired evidence')
    if 'maxAgeSeconds' in rule:
        require((now - observed).total_seconds() <= rule['maxAgeSeconds'], 'stale evidence age')
    native = proof['native']
    exact(native, ('completed', 'pass', 'errors', 'candidateDigest'), ('loadedDigest',))
    require(native['completed'] is True and native['pass'] is True and native['errors'] == [],
            'native proof requires completion, pass and no substantive errors')
    identity = source_digest(control['source'])
    require(native['candidateDigest'] == identity, 'wrong native candidate')
    if rule['loadedRequired']:
        require(native.get('loadedDigest') == identity, 'wrong or missing loaded source')
    return proof['class']


def _validate(task, root, now):
    control = task['control']
    exact(control, ('schema', 'authorization', 'assignment', 'source', 'conditions', 'claims', 'decisions', 'wip'))
    require(control['schema'] == SCHEMA, 'unknown control schema')
    auth = control['authorization']
    exact(auth, ('revision', 'owner', 'nonGoals', 'invariants', 'decisionRights', 'editScope', 'deniedScope', 'requiredCapabilities', 'claims'))
    for field in ('revision', 'owner'):
        text(auth[field], field)
    for field in ('nonGoals', 'invariants', 'decisionRights', 'editScope', 'deniedScope'):
        strings(auth[field], field)
    require(isinstance(auth['requiredCapabilities'], list), 'required capabilities must be array')
    capability_names = []
    for capability in auth['requiredCapabilities']:
        exact(capability, ('name', 'scope', 'producer'))
        text(capability['name'], 'capability name')
        text(capability['producer'], 'capability producer')
        relative(capability['scope'])
        capability_names.append(capability['name'])
    require(len(capability_names) == len(set(capability_names)), 'duplicate required capability')
    for field in ('editScope', 'deniedScope'):

        for path in auth[field]:
            relative(path)
    require(set(obj(auth['claims'], 'claim rules')) == set(CLAIMS), 'declare each claim applicability')
    for claim, rule in auth['claims'].items():
        exact(rule, ('applicable', 'reason', 'scenario', 'prerequisites', 'classes', 'producers', 'reviewers', 'loadedRequired'), ('maxAgeSeconds',))
        require(type(rule['applicable']) is bool and type(rule['loadedRequired']) is bool, 'claim flags must be boolean')
        text(rule['reason'], 'applicability reason')
        text(rule['scenario'], 'authorized scenario')
        for field in ('prerequisites', 'classes', 'producers', 'reviewers'):
            strings(rule[field], field)
        require(set(rule['prerequisites']) <= set(CLAIMS) - {claim}, 'invalid claim prerequisite')
        require(set(rule['classes']) <= set(CLASSES), 'invalid evidence class')
        if rule['applicable']:
            require(rule['classes'] and rule['producers'] and rule['reviewers'], 'applicable claim needs evidence policy')
        if 'maxAgeSeconds' in rule:
            require(type(rule['maxAgeSeconds']) in (int, float) and math.isfinite(rule['maxAgeSeconds']) and rule['maxAgeSeconds'] >= 0, 'invalid evidence age')
    # A cycle cannot supply an independent completion route.
    def visit(claim, trail):
        require(claim not in trail, 'claim prerequisite cycle')
        for dep in auth['claims'][claim]['prerequisites']:
            require(auth['claims'][dep]['applicable'], 'prerequisite is not applicable')
            visit(dep, trail | {claim})
    for claim in CLAIMS:
        visit(claim, set())
    assignment = control['assignment']
    exact(assignment, ('authorityDigest', 'sourceDigest', 'conditionsDigest', 'actor', 'rights'))
    require(assignment['authorityDigest'] == authority_digest(task), 'stale assignment authority')
    text(assignment['actor'], 'actor')
    strings(assignment['rights'], 'assignment rights')
    require(set(assignment['rights']) <= set(auth['decisionRights']), 'assignment exceeds decision rights')
    obj(control['conditions'], 'conditions')
    require(assignment['sourceDigest'] == source_digest(control['source']), 'stale assignment source')
    require(assignment['conditionsDigest'] == digest(control['conditions']), 'stale assignment conditions')
    source_digest(control['source'])
    for ref in control['source']:
        checked_ref(root, ref)
    require(set(obj(control['claims'], 'claims')) == set(CLAIMS), 'declare each claim state')
    for claim, state in control['claims'].items():
        exact(state, ('state', 'evidence'))
        rule = auth['claims'][claim]
        require(state['state'] in ('open', 'satisfied', 'not-applicable'), 'invalid claim state')
        require(isinstance(state['evidence'], list), 'claim evidence must be array')
        if not rule['applicable']:
            require(state['state'] == 'not-applicable' and not state['evidence'], 'inapplicable claim cannot be asserted')
        else:
            require(state['state'] != 'not-applicable', 'applicable claim cannot be skipped')
        if state['state'] == 'satisfied':
            require(all(control['claims'][dep]['state'] == 'satisfied' for dep in rule['prerequisites']), 'claim prerequisite open')
            classes = {evidence(root, ref, task, claim, now) for ref in state['evidence']}
            require(set(rule['classes']) <= classes, 'required evidence class missing')
        else:
            # History remains referenced and hash-checked, but failed/stale history is never a claim.
            for ref in state['evidence']:
                checked_ref(root, ref)
    source_paths = {ref['path'] for ref in control['source']}
    require(not any(ref['path'] in source_paths for state in control['claims'].values() for ref in state['evidence']), 'source cannot contain its own evidence')
    if task['status'] == 'done':
        require(all(not auth['claims'][c]['applicable'] or control['claims'][c]['state'] == 'satisfied' for c in CLAIMS),
                'done requires every applicable claim')
    decisions = control['decisions']
    require(isinstance(decisions, list), 'decisions must be array')
    ids = []
    pending = False
    for decision in decisions:
        exact(decision, ('id', 'owner', 'authorityDigest', 'sourceDigest', 'conditionsDigest', 'trigger', 'constraint', 'action', 'expected', 'reconsider', 'evidence', 'effect', 'state'))
        require(not pending, 'reconcile pending decision before a new batch')
        for field in ('id', 'owner', 'trigger', 'constraint', 'action', 'expected', 'reconsider'):
            text(decision[field], field)
        require(decision['trigger'] in ('result', 'goal', 'capability', 'repeated-failure', 'resume', 'completion'), 'invalid decision trigger')
        require(decision['state'] in ('continuation', 'blocked', 'stopped', 'complete'), 'invalid decision state')
        require(isinstance(decision['evidence'], list), 'decision evidence must be array')
        for ref in decision['evidence']:
            checked_ref(root, ref)
        for field in ('authorityDigest', 'sourceDigest', 'conditionsDigest'):
            require(isinstance(decision[field], str) and HEX.fullmatch(decision[field]), 'invalid decision identity')
        pending = decision['effect'] is None
        if not pending:
            exact(decision['effect'], ('decisionId', 'observed', 'matchesExpected', 'followUp', 'evidence'))
            require(decision['effect']['decisionId'] == decision['id'], 'effect decision mismatch')
            require(isinstance(decision['effect']['evidence'], list) and decision['effect']['evidence'], 'effect requires observed result evidence')
            for ref in decision['effect']['evidence']:
                checked_ref(root, ref)
            text(decision['effect']['observed'], 'observed effect')
            require(type(decision['effect']['matchesExpected']) is bool, 'effect comparison must be boolean')
            text(decision['effect']['followUp'], 'follow-up')
        ids.append(decision['id'])
    require(len(set(ids)) == len(ids), 'duplicate decision id')
    if decisions:
        latest = decisions[-1]
        require(latest['authorityDigest'] == authority_digest(task) and latest['sourceDigest'] == source_digest(control['source']) and
                latest['conditionsDigest'] == digest(control['conditions']), 'latest decision has stale authority or inputs')
    if task['status'] == 'done':
        require(not pending, 'done requires reconciled feedback')
        require(not decisions or decisions[-1]['state'] not in ('blocked', 'stopped'), 'done requires actionable completion state')
    wip = control['wip']
    exact(wip, ('limits', 'items', 'exceptions', 'history', 'overheadSeconds'))
    require(set(obj(wip['items'], 'WIP items')) == set(WIP), 'declare WIP categories')
    require(set(obj(wip['limits'], 'WIP limits')) <= set(WIP), 'unknown WIP limit')
    for category in WIP:
        strings(wip['items'][category], category)
    for limit in wip['limits'].values():
        require(type(limit) is int and limit >= 0, 'WIP limit must be nonnegative integer')
    require(isinstance(wip['exceptions'], list) and isinstance(wip['history'], list), 'WIP history/exceptions must be arrays')
    for exception in wip['exceptions']:
        exact(exception, ('owner', 'category', 'limit', 'expiresAt', 'reason'))
        require(exception['owner'] == auth['owner'], 'WIP exception requires authority owner')
        require(exception['category'] in WIP and type(exception['limit']) is int and exception['limit'] >= 0, 'invalid WIP exception')
        stamp(exception['expiresAt'])
        text(exception['reason'], 'exception reason')
    require(wip['overheadSeconds'] is None or (type(wip['overheadSeconds']) in (int, float) and math.isfinite(wip['overheadSeconds']) and wip['overheadSeconds'] >= 0), 'overhead is unknown or measured seconds')


def validate_control(task, root, now=None):
    if 'control' not in task:
        return []
    try:
        _validate(task, Path(root), now or datetime.now(timezone.utc))
        return []
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        return ['control: ' + str(exc)]


def check_gate(task, root, event, request, now=None):
    """Read-only native precondition gate. The existing writer owns task updates."""
    now = now or datetime.now(timezone.utc)
    errors = validate_control(task, root, now)
    if errors:
        return errors
    try:
        require('control' in task, 'gate requires controlled task')
        require(event in EVENTS, 'unknown gate')
        exact(request, ('authorityDigest', 'actor', 'purpose', 'paths', 'capabilities', 'wipAfter'))
        control = task['control']
        auth = control['authorization']
        require(request['authorityDigest'] == authority_digest(task), 'request has stale authority')
        require(request['actor'] == control['assignment']['actor'], 'wrong assigned actor')
        require(event in control['assignment']['rights'], 'event not authorized')
        require(request['purpose'] in ('admission', 'reduction', 'recovery'), 'invalid purpose')
        strings(request['paths'], 'requested paths')
        def within(path, scope):
            return path == scope or path.startswith(scope + '/')
        for path in request['paths']:
            relative(path)
            require(not any(within(path, scope) for scope in auth['deniedScope']), 'explicit edit denial')
            require(any(within(path, scope) for scope in auth['editScope']), 'edit outside authorized scope')
            safe_path(root, path)
        require(isinstance(request['capabilities'], list), 'capabilities must be array')
        names = []
        required = {c['name']: c for c in auth['requiredCapabilities']}
        for capability in request['capabilities']:
            exact(capability, ('name', 'status', 'evidence'))
            require(capability['name'] in required, 'undeclared capability')
            policy = required[capability['name']]
            require(capability['status'] == 'available', 'capability denied or unknown')
            observation = json.loads(checked_ref(root, capability['evidence']))
            exact(observation, ('schema', 'type', 'scope', 'authorization', 'authorizationRevision', 'observedAt',
                                'probe', 'effective', 'authorityDigest', 'conditionsDigest', 'producer'), ('error',))
            require(observation['schema'] == 'runtime-control/v1' and observation['type'] == 'capability', 'wrong capability receipt')
            require(observation['authorityDigest'] == authority_digest(task) and observation['authorizationRevision'] == auth['revision'] and
                    observation['conditionsDigest'] == digest(control['conditions']), 'stale capability authority or conditions')
            require(observation['producer'] == policy['producer'] and observation['scope'] == str(safe_path(root, policy['scope'])), 'capability producer/scope mismatch')
            require(observation['authorization'] == 'allowed' and observation['probe'] == 'passed' and observation['effective'] == 'observed-writable' and
                    'error' not in observation, 'capability denied, unknown or unsuccessful')
            require(stamp(observation['observedAt']) <= now, 'future capability observation')
            names.append(capability['name'])
        require(len(names) == len(set(names)) and set(required) <= set(names), 'missing or duplicate capability observation')
        wip = control['wip']
        require(set(obj(request['wipAfter'], 'projected WIP')) == set(WIP), 'declare projected WIP categories')
        for category in WIP:
            strings(request['wipAfter'][category], 'projected WIP')
            if request['purpose'] in ('reduction', 'recovery'):
                require(set(request['wipAfter'][category]) <= set(wip['items'][category]), 'reduction/recovery cannot admit WIP')
        if request['purpose'] == 'admission':
            require(not control['decisions'] or control['decisions'][-1]['state'] not in ('blocked', 'stopped'), 'latest decision blocks admission')
            require(not control['decisions'] or control['decisions'][-1]['effect'] is not None,
                    'reconcile pending outcome before new work')
            wip = control['wip']
            for category, limit in wip['limits'].items():
                limits = [limit] + [e['limit'] for e in wip['exceptions'] if e['category'] == category and stamp(e['expiresAt']) >= now]
                require(max(len(wip['items'][category]), len(request['wipAfter'][category])) <= max(limits), 'WIP admission limit: ' + category)
        if event == 'pre-completion':
            require(not control['decisions'] or control['decisions'][-1]['effect'] is not None, 'completion requires reconciled feedback')
        if event in ('pre-integration', 'pre-completion'):
            required = ('implemented', 'verified') if event == 'pre-integration' else CLAIMS
            require(all(not auth['claims'][c]['applicable'] or control['claims'][c]['state'] == 'satisfied' for c in required), 'gate claims remain open')
        return []
    except (ValueError, TypeError, KeyError, OSError) as exc:
        return ['gate: ' + str(exc)]


def checkpoint(root, task_path, destination):
    """Collect, read back and recheck inputs before publishing an immutable snapshot."""
    root = Path(root).resolve()
    destination = Path(destination).absolute()
    require(not destination.exists() and not destination.is_symlink(), 'checkpoint destination exists')
    require(not destination.resolve().is_relative_to(root), 'checkpoint must be outside source root')
    require(not any(p.is_symlink() for p in [destination.parent] + list(destination.parents)), 'symlink checkpoint parent')
    raw_task = read_bytes(safe_path(root, task_path))
    task = json.loads(raw_task)
    errors = validate_control(task, root)
    require(not errors and 'control' in task, '; '.join(errors) or 'controlled task required')
    refs = list(task['control']['source'])
    for state in task['control']['claims'].values():
        refs.extend(state['evidence'])
    for decision in task['control']['decisions']:
        refs.extend(decision['evidence'])
        if decision['effect'] is not None:
            refs.extend(decision['effect']['evidence'])
    collected = {task_path: raw_task}
    for ref in refs:
        raw = checked_ref(root, ref)
        require(ref['path'] not in collected or collected[ref['path']] == raw, 'ambiguous snapshot path')
        collected[ref['path']] = raw
    manifest = {'schema': 'outcome-checkpoint/v1', 'task': task_path, 'authorityDigest': authority_digest(task),
                'files': [{'path': p, 'sha256': hashlib.sha256(raw).hexdigest()} for p, raw in sorted(collected.items())]}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.outcome-checkpoint-', dir=str(destination.parent)))
    try:
        for path, raw in collected.items():
            target = temporary / 'files' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        (temporary / 'manifest.json').write_bytes(canonical(manifest))
        for ref in manifest['files']:
            checked_ref(temporary / 'files', ref)
            require(read_bytes(safe_path(root, ref['path'])) == collected[ref['path']], 'source changed during checkpoint')
        # mkdir is exclusive; publication must not replace another checkpoint, even an empty one.
        destination.mkdir()
        try:
            os.replace(temporary, destination / 'snapshot')
        except BaseException:
            destination.rmdir()
            raise
        return digest(manifest)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def resume(root, task_path, checkpoint_path, destination):
    """Validate current authority and complete snapshot; restore only into new destination."""
    root = Path(root).resolve()
    checkpoint_path = Path(checkpoint_path).absolute() / 'snapshot'
    require(not any(p.is_symlink() for p in [checkpoint_path, checkpoint_path / 'files'] + list(checkpoint_path.parents)), 'symlink checkpoint forbidden')
    manifest = read_json(checkpoint_path / 'manifest.json')
    exact(manifest, ('schema', 'task', 'authorityDigest', 'files'))
    require(manifest['schema'] == 'outcome-checkpoint/v1' and manifest['task'] == task_path, 'wrong checkpoint')
    task = read_json(safe_path(root, task_path))
    require(authority_digest(task) == manifest['authorityDigest'], 'stale resume authority')
    require(isinstance(manifest['files'], list), 'invalid checkpoint manifest')
    paths = [ref['path'] for ref in manifest['files']]
    require(len(paths) == len(set(paths)) and task_path in paths, 'ambiguous checkpoint files')
    collected = {ref['path']: checked_ref(checkpoint_path / 'files', ref) for ref in manifest['files']}
    require(read_bytes(safe_path(root, task_path)) == collected[task_path], 'stale resume task changed')
    snapshot_task = json.loads(collected[task_path])
    refs = list(snapshot_task['control']['source'])
    for state in snapshot_task['control']['claims'].values():
        refs.extend(state['evidence'])
    for decision in snapshot_task['control']['decisions']:
        refs.extend(decision['evidence'])
        if decision['effect'] is not None:
            refs.extend(decision['effect']['evidence'])
    require(set(paths) == {task_path} | {ref['path'] for ref in refs}, 'checkpoint has missing or unexpected files')
    require(authority_digest(snapshot_task) == manifest['authorityDigest'], 'checkpoint task authority mismatch')
    errors = validate_control(snapshot_task, checkpoint_path / 'files')
    require(not errors, '; '.join(errors))
    destination = Path(destination).absolute()
    require(not destination.exists() and not destination.is_symlink(), 'restore destination must be new; no overwrite')
    require(not any(p.is_symlink() for p in [destination.parent] + list(destination.parents)), 'symlink restore parent')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix='.outcome-restore-', dir=str(destination.parent)))
    try:
        for path, raw in collected.items():
            target = temporary / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        require(read_bytes(safe_path(root, task_path)) == collected[task_path], 'task changed during restore')
        destination.mkdir()
        try:
            os.replace(temporary, destination / 'restored')
        except BaseException:
            destination.rmdir()
            raise
        return digest(manifest)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def reconcile(root, task_path, expected_sha256, proposal):
    """Compare-and-swap the existing canonical task; never edit its authorization."""
    require(isinstance(expected_sha256, str) and HEX.fullmatch(expected_sha256), 'invalid expected task digest')
    target = safe_path(root, task_path)
    require(target.parent.name == 'tasks' and target.parent.parent.name == 'work', 'canonical work/tasks task required')
    lock = target.with_name(target.name + '.outcome.lock')
    descriptor = os.open(str(lock), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    temporary = None
    try:
        os.close(descriptor)
        original = read_bytes(target)
        require(hashlib.sha256(original).hexdigest() == expected_sha256, 'stale expected task digest')
        current = json.loads(original)
        proposed = read_json(proposal)
        require(isinstance(proposed, dict) and proposed.get('id') == target.stem == current.get('id') and
                proposed.get('schema') == current.get('schema') in TASK_SCHEMAS, 'different task identity')
        require(authority_digest(proposed) == authority_digest(current), 'reconcile cannot change authority or limits')
        require(same_json(proposed.get('depends'), current.get('depends')), 'reconcile cannot change dependency contract')
        mutable = {'status', 'current', 'evidence', 'updatedAt', 'completedAt', 'control', 'history'}
        for key, value in current.items():
            if key not in mutable:
                require(key in proposed and same_json(proposed[key], value), 'lost or changed task extension: ' + key)
        for key in ('history', 'evidence'):
            if key in current:
                require(isinstance(current[key], list) and isinstance(proposed.get(key), list) and
                        same_json(proposed[key][:len(current[key])], current[key]), 'task history/evidence prefix changed')
        old = current['control']
        new = proposed['control']
        require(len(new['decisions']) >= len(old['decisions']), 'decision history erased')
        for index, decision in enumerate(old['decisions']):
            next_decision = new['decisions'][index]
            if index == len(old['decisions']) - 1 and decision['effect'] is None:
                require(same_json({k: v for k, v in decision.items() if k not in ('effect', 'state')},
                                  {k: v for k, v in next_decision.items() if k not in ('effect', 'state')}), 'pending decision inputs changed')
            else:
                require(same_json(next_decision, decision), 'decision history changed')
        require(same_json(new['wip']['history'][:len(old['wip']['history'])], old['wip']['history']), 'WIP history erased')
        # Existing source may have changed: validate the complete replacement, not stale source proof.
        errors = validate_control(proposed, root)
        require(not errors, '; '.join(errors))
        require(proposed.get('status') in ('planned', 'in-progress', 'blocked', 'done', 'cancelled'), 'invalid task status')
        require(isinstance(proposed.get('current'), dict) and isinstance(proposed['current'].get('summary'), str) and
                isinstance(proposed['current'].get('nextAction'), str) and isinstance(proposed['current'].get('blockers'), list), 'invalid task current state')
        raw = canonical(proposed) + b'\n'
        require(len(raw) <= MAX_BYTES, 'task exceeds 4 MiB')
        require(isinstance(proposed.get('evidence'), list) and all(isinstance(item, str) for item in proposed['evidence']), 'task evidence must contain strings')
        handle, temporary = tempfile.mkstemp(prefix='.outcome-task-', dir=str(target.parent))
        os.chmod(temporary, target.stat().st_mode & 0o777)
        with os.fdopen(handle, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        require(read_bytes(safe_path(root, task_path)) == original, 'concurrent task change')
        os.replace(temporary, target)
        temporary = None
        require(read_bytes(target) == raw, 'task readback mismatch')
        return hashlib.sha256(raw).hexdigest()
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)
        lock.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--task', required=True, help='repository-relative canonical task JSON')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('digest')
    sub.add_parser('validate')
    writer = sub.add_parser('reconcile')
    writer.add_argument('--expected-sha256', required=True)
    writer.add_argument('--proposal', type=Path, required=True)
    gate = sub.add_parser('gate')
    gate.add_argument('event', choices=EVENTS)
    gate.add_argument('--request', type=Path, required=True)
    snap = sub.add_parser('checkpoint')
    snap.add_argument('--destination', type=Path, required=True)
    restore = sub.add_parser('resume')
    restore.add_argument('--checkpoint', type=Path, required=True)
    restore.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        task = read_json(safe_path(args.root, args.task))
        if args.command == 'digest':
            result = {'authorityDigest': authority_digest(task), 'sourceDigest': source_digest(task['control']['source'])}
        elif args.command in ('validate', 'gate'):
            errors = (validate_control(task, args.root) if args.command == 'validate' else
                      check_gate(task, args.root, args.event, read_json(args.request)))
            result = {'valid': not errors, 'errors': errors}
            print(json.dumps(result, indent=2))
            return int(bool(errors))
        elif args.command == 'reconcile':
            result = {'taskDigest': reconcile(args.root, args.task, args.expected_sha256, args.proposal)}
        elif args.command == 'checkpoint':
            result = {'checkpointDigest': checkpoint(args.root, args.task, args.destination)}
        else:
            result = {'checkpointDigest': resume(args.root, args.task, args.checkpoint, args.destination)}
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        print(json.dumps({'valid': False, 'errors': [str(exc)]}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
