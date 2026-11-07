#!/usr/bin/env python3
"""Bounded local observation, capability and owned scratch controls (stdlib only)."""
import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

SCHEMA = 'runtime-control/v1'
MARKER = '.runtime-owned.json'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    with open(path, encoding='utf-8') as stream:
        return json.load(stream)


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.runtime-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def lock(path):
    """Fail closed on concurrent writers; never auto-break an unknown stale lock."""
    lockpath = Path(str(path) + '.lock')
    fd = os.open(str(lockpath), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(fd)
        yield
    finally:
        lockpath.unlink()


def timestamp(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp requires timezone')
    return parsed


def safe_path(value):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise ValueError('path traversal')
    for ancestor in [path] + list(path.parents):
        if ancestor.is_symlink():
            raise ValueError('symlink path')
    return path


def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents


def observe(spec, observation, previous=None):
    fields = spec['fields']
    if not isinstance(fields, list) or not fields or any(not isinstance(key, str) or not key for key in fields) or len(set(fields)) != len(fields):
        raise ValueError('fields must be unique nonempty names')
    for key in ('completion', 'failure', 'denial', 'exhaustion'):
        if key in observation and not isinstance(observation[key], bool):
            raise ValueError('critical events must be explicit booleans')
    if not isinstance(spec.get('missingActionable', True), bool):
        raise ValueError('missingActionable must be boolean')
    jitter = spec.get('jitter', {})
    if not isinstance(jitter, dict):
        raise ValueError('jitter must be a mapping')
    if any(key not in fields or isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0 for key, val in jitter.items()):
        raise ValueError('invalid jitter')
    selected = {key: observation.get(key, {'unknown': True}) for key in fields}
    config = digest(spec)
    if previous is not None:
        if not isinstance(previous, dict) or previous.get('schema') != SCHEMA or previous.get('specDigest') != config:
            raise ValueError('invalid state or changed spec; use a new state')
        for key in ('observations', 'wakes', 'suppressed'):
            if type(previous.get(key)) is not int or previous[key] < 0:
                raise ValueError('invalid state counters')
        if previous['observations'] != previous['wakes'] + previous['suppressed']:
            raise ValueError('inconsistent state counters')
        if not isinstance(previous.get('baseline'), dict) or not set(previous['baseline']).issubset(fields):
            raise ValueError('invalid state baseline')
        for key, allowed in (('lastCritical', ('completion', 'failure', 'denial', 'exhaustion')), ('lastMissing', fields)):
            values = previous.get(key)
            if not isinstance(values, list) or any(not isinstance(value, str) or value not in allowed for value in values) or len(set(values)) != len(values):
                raise ValueError('invalid state incident sets')
    present_values = {key: observation[key] for key in fields if key in observation}
    baseline = previous['baseline'] if previous else present_values
    missing_actionable = spec.get('missingActionable', True)
    changed = []
    for key in fields:
        if key not in present_values:
            if missing_actionable and key in baseline:
                changed.append(key)
            continue
        if key not in baseline:
            changed.append(key)
            continue
        old, new = baseline[key], present_values[key]
        numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (old, new))
        # Canonical JSON preserves bool/number distinctions, including nested values.
        if (abs(new - old) > jitter[key] if key in jitter and numeric else digest(old) != digest(new)):
            changed.append(key)
    # Newly asserted/reasserted incidents bypass jitter; unchanged incidents coalesce.
    critical = [key for key in ('completion', 'failure', 'denial', 'exhaustion') if observation.get(key) is True]
    missing = [key for key in fields if key not in observation]
    new_critical = sorted(set(critical) - set((previous or {}).get('lastCritical', [])))
    new_missing = sorted(set(missing) - set((previous or {}).get('lastMissing', [])))
    wake = previous is None or bool(changed or new_critical or (new_missing and spec.get('missingActionable', True)))
    count = (previous or {}).get('observations', 0) + 1
    next_baseline = (present_values if missing_actionable else dict(baseline, **present_values)) if wake else baseline
    state = {'schema': SCHEMA, 'specDigest': config, 'baseline': next_baseline,
             'lastCritical': critical, 'lastMissing': missing,
             'observations': count, 'wakes': (previous or {}).get('wakes', 0) + int(wake),
             'suppressed': (previous or {}).get('suppressed', 0) + int(not wake)}
    return state, {'schema': SCHEMA, 'type': 'observation', 'wake': wake, 'changed': changed,
                   'critical': critical, 'newCritical': new_critical, 'unknown': missing, 'newUnknown': new_missing, 'fingerprint': digest(selected),
                   'stateDigest': digest(state), 'observations': count, 'wakes': state['wakes'], 'suppressed': state['suppressed']}


def capability(request):
    scope = safe_path(request['scope'])
    binding_keys = ('authorityDigest', 'conditionsDigest', 'producer')
    present = [key for key in binding_keys if key in request]
    if present:
        if len(present) != len(binding_keys):
            raise ValueError('capability binding metadata must be all-or-none')
        for key in ('authorityDigest', 'conditionsDigest'):
            if not isinstance(request[key], str) or not re.fullmatch(r'[0-9a-f]{64}', request[key]):
                raise ValueError('invalid capability binding digest')
        if not isinstance(request['producer'], str) or not request['producer'].strip():
            raise ValueError('capability producer must be nonempty')
    auth = request['authorization']
    if auth not in ('allowed', 'denied', 'unknown'):
        raise ValueError('authorization must be allowed, denied or unknown')
    result = {'schema': SCHEMA, 'type': 'capability', 'scope': str(scope), 'authorization': auth,
              'authorizationRevision': request['authorizationRevision'], 'observedAt': dt.datetime.now(dt.timezone.utc).isoformat(),
              'probe': 'unrun', 'effective': 'unknown'}
    result.update({key: request[key] for key in present})
    # Explicit permission data are observations, not credentials or authentication.
    if auth != 'allowed':
        result['effective'] = 'denied' if auth == 'denied' else 'unknown'
        return result
    if request.get('owned') is not True or not scope.is_dir():
        raise ValueError('probe requires existing declared owned directory')
    try:
        with tempfile.TemporaryDirectory(prefix='.runtime-probe-', dir=str(scope)) as temporary:
            target = Path(temporary) / 'probe'
            target.write_bytes(b'runtime capability probe\n')
            if target.read_bytes() != b'runtime capability probe\n':
                raise OSError('readback mismatch')
            target.unlink()
        result.update(probe='passed', effective='observed-writable')
    except OSError as error:
        result.update(probe='denied', effective='denied', error=type(error).__name__)
    return result


def resource_path(path, protected=()):
    path = safe_path(path)
    current = Path.cwd().resolve()
    if (path / '.git').exists():
        raise ValueError('Git checkout resources use native Git retirement')
    if path == Path(path.anchor) or overlaps(path, current):
        raise ValueError('protected root/current checkout/parent')
    for item in protected:
        if overlaps(path, safe_path(item)):
            raise ValueError('protected path overlap')
    return path


def init_resource(request):
    path = resource_path(request['resource'], request.get('protected', []))
    if not request.get('owner'):
        raise ValueError('owner required')
    path.mkdir(parents=False, exist_ok=True)
    if any(path.iterdir()):
        raise ValueError('initialize only an empty owned resource')
    marker = {'schema': SCHEMA, 'owner': request['owner'], 'id': uuid.uuid4().hex, 'path': str(path)}
    with (path / MARKER).open('x', encoding='utf-8') as stream:
        json.dump(marker, stream, sort_keys=True)
        stream.write('\n')
    return marker


def permission_mode(path):
    mode = path.stat().st_mode & 0o7777
    if mode & 0o7000:
        raise ValueError('special permission bits are unsupported')
    return mode


def tree(path):
    path = safe_path(path)
    if not path.is_dir():
        raise ValueError('manifest root must be a directory')
    result = {'.': {'directory': True, 'mode': permission_mode(path)}}
    for item in sorted(path.rglob('*')):
        if item.name == '.git':
            raise ValueError('Git resources use the native Git retirement route')
        relative = item.relative_to(path).as_posix()
        if item.is_symlink():
            raise ValueError('symlink in resource')
        stat = item.stat()
        if item.is_file():
            if stat.st_nlink != 1:
                raise ValueError('shared hard-linked file')
            result[relative] = {'sha256': hashlib.sha256(item.read_bytes()).hexdigest(), 'bytes': stat.st_size, 'mode': permission_mode(item)}
        elif item.is_dir():
            result[relative] = {'directory': True, 'mode': permission_mode(item)}
        else:
            raise ValueError('unsupported special file')
    return result


def resource_inputs(request):
    path = resource_path(request['resource'], request.get('protected', []))
    checkpoint = safe_path(request['checkpoint'])
    if overlaps(path, checkpoint):
        raise ValueError('checkpoint must be outside resource')
    marker = read(path / MARKER)
    if marker.get('owner') != request['owner'] or marker.get('id') != request['resourceId'] or marker.get('path') != str(path):
        raise ValueError('ownership binding mismatch')
    if request.get('shared') is not False or request.get('dependents') != [] or request.get('retire') is not True:
        raise ValueError('shared, active, unknown or non-retiring resource')
    lease = request.get('lease')
    if not isinstance(lease, dict) or lease.get('state') != 'released':
        raise ValueError('active or unknown lease')
    return path, checkpoint, marker


def plan_resource(request):
    path, checkpoint, marker = resource_inputs(request)
    result = {'schema': SCHEMA, 'type': 'resource-plan', 'request': request, 'marker': marker, 'manifest': tree(path)}
    result['planDigest'] = digest(result)
    return result


def check_plan(plan, request):
    unsigned = dict(plan)
    expected = unsigned.pop('planDigest')
    if digest(unsigned) != expected or request != plan['request']:
        raise ValueError('stale/changed plan or request')
    path, checkpoint, marker = resource_inputs(request)
    if marker != plan['marker'] or tree(path) != plan['manifest']:
        raise ValueError('resource changed since plan')
    return path, checkpoint


def verify_checkpoint(plan):
    checkpoint = safe_path(plan['request']['checkpoint'])
    if read(checkpoint / 'plan.json') != plan or tree(checkpoint / 'data') != plan['manifest']:
        raise ValueError('checkpoint readback failed')
    return {'schema': SCHEMA, 'type': 'preservation', 'status': 'verified', 'planDigest': plan['planDigest'], 'manifestDigest': digest(plan['manifest'])}


def preserve(plan, request):
    path, checkpoint = check_plan(plan, request)
    if checkpoint.exists():
        raise ValueError('checkpoint already exists; verify existing snapshot')
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.runtime-preserve-', dir=str(checkpoint.parent)))
    try:
        shutil.copytree(path, staging / 'data')
        atomic(staging / 'plan.json', plan)
        if tree(staging / 'data') != plan['manifest']:
            raise ValueError('preservation copy mismatch')
        check_plan(plan, request)
        # No overwrite: mkdir reservation before moving verified children.
        checkpoint.mkdir()
        for child in staging.iterdir():
            shutil.move(str(child), str(checkpoint / child.name))
        return verify_checkpoint(plan)
    finally:
        shutil.rmtree(staging)


def apply(plan, request):
    path, checkpoint = check_plan(plan, request)
    verify_checkpoint(plan)
    check_plan(plan, request)
    # A failed/interrupted removal leaves the verified external checkpoint intact.
    shutil.rmtree(path)
    if path.exists():
        raise ValueError('resource retirement incomplete')
    receipt = {'schema': SCHEMA, 'type': 'retirement', 'status': 'removed', 'planDigest': plan['planDigest'],
               'manifestDigest': digest(plan['manifest']), 'checkpoint': str(checkpoint), 'removed': str(path)}
    atomic(checkpoint / 'retirement.json', receipt)
    return receipt


def restore(plan, request):
    verify_checkpoint(plan)
    destination = resource_path(request['destination'], request.get('protected', []))
    checkpoint = safe_path(plan['request']['checkpoint'])
    if overlaps(destination, checkpoint):
        raise ValueError('restore overlaps checkpoint')
    marker = read(destination / MARKER)
    if marker.get('owner') != request['owner'] or marker.get('id') != request['resourceId'] or marker.get('path') != str(destination):
        raise ValueError('restore requires bound owned destination')
    if set(tree(destination)) != {'.', MARKER}:
        raise ValueError('restore destination is not empty')
    # Copy only after full checkpoint verification; partial restore is retained on failure.
    for item in (checkpoint / 'data').iterdir():
        if item.name == MARKER:
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            with target.open('xb') as stream:
                stream.write(item.read_bytes())
            target.chmod(plan['manifest'][item.name]['mode'])
    destination.chmod(plan['manifest']['.']['mode'])
    actual = tree(destination)
    expected = dict(plan['manifest'])
    actual.pop(MARKER)
    expected.pop(MARKER)
    if actual != expected:
        raise ValueError('restore readback failed')
    return {'schema': SCHEMA, 'type': 'restore', 'status': 'verified', 'planDigest': plan['planDigest'], 'destination': str(destination)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['observe', 'capability', 'init', 'plan', 'preserve', 'verify', 'apply', 'restore'])
    parser.add_argument('--request')
    parser.add_argument('--plan')
    parser.add_argument('--spec')
    parser.add_argument('--observation')
    parser.add_argument('--state')
    parser.add_argument('--expect', help='required CAS digest or absent for observe')
    parser.add_argument('--output', help='new JSON output file; no overwrite')
    args = parser.parse_args(argv)
    try:
        if args.command == 'observe':
            if not args.state or not args.expect:
                raise ValueError('observe requires state and expect')
            statepath = safe_path(args.state)
            statepath.parent.mkdir(parents=True, exist_ok=True)
            with lock(statepath):
                previous = read(statepath) if statepath.exists() else None
                identity = digest(previous) if previous else 'absent'
                if args.expect != identity:
                    raise ValueError('concurrent/stale state identity')
                state, result = observe(read(args.spec), read(args.observation), previous)
                atomic(statepath, state)
        else:
            request = read(args.request) if args.request else None
            plan = read(args.plan) if args.plan else None
            handlers = {'capability': lambda: capability(request), 'init': lambda: init_resource(request),
                        'plan': lambda: plan_resource(request), 'preserve': lambda: preserve(plan, request),
                        'verify': lambda: verify_checkpoint(plan), 'apply': lambda: apply(plan, request),
                        'restore': lambda: restore(plan, request)}
            result = handlers[args.command]()
        if args.output:
            with open(args.output, 'x', encoding='utf-8') as stream:
                json.dump(result, stream, sort_keys=True, indent=2)
                stream.write('\n')
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(json.dumps({'schema': SCHEMA, 'status': 'error', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
