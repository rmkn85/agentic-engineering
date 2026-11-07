#!/usr/bin/env python3
"""Exercise native control activities together in disposable owned fixtures."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import outcome_control as oc


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def run_trial(work):
    work.mkdir()
    checks = []

    def command(label, argv, success=True):
        result = subprocess.run([str(v) for v in argv], cwd=REPO, text=True, capture_output=True, timeout=30)
        (work / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
        if (result.returncode == 0) != success:
            raise ValueError(label + ': unexpected exit; inspect retained log')
        checks.append(label)
        return json.loads(result.stdout) if result.stdout else None

    def activity(label, name, success=True, **values):
        return command(label, [sys.executable, REPO / 'tools/make', name,
                              *[key + '=' + str(value) for key, value in values.items()]], success)

    root = work / 'product'
    task_path = 'work/tasks/RESULT-1.json'
    command('example', [sys.executable, REPO / 'examples/outcome-control/run.py',
                        '--destination', root, '--checkpoint', work / 'initial-checkpoint'])
    native = [sys.executable, REPO / 'tools/project_work.py', 'validate', '--root', root]
    command('native-acceptance', native)
    task = json.loads((root / task_path).read_text())
    request = json.loads((root / 'gate-request.json').read_text())
    gate = dict(ROOT=root, TASK=task_path, EVENT='pre-completion', REQUEST=root / 'gate-request.json')
    activity('completion', 'control-gate', **gate)
    changed = copy.deepcopy(task)
    changed['outcome'] += ' with a changed requirement'
    write(root / task_path, changed)
    activity('stale-authority-rejected', 'control-gate', success=False, **gate)
    changed.pop('control')
    write(root / task_path, changed)
    command('removed-required-control-rejected', native, False)
    write(root / task_path, task)

    # A successful process is insufficient when the native producer did not finish.
    proof_path = root / 'evidence/verified.json'
    proof = json.loads(proof_path.read_text())
    incomplete = copy.deepcopy(proof)
    incomplete['native']['completed'] = False
    ref = write(proof_path, incomplete)
    ref['path'] = 'evidence/verified.json'
    changed = copy.deepcopy(task)
    changed['control']['claims']['verified']['evidence'] = [ref]
    write(root / task_path, changed)
    activity('incomplete-native-verdict-rejected', 'control-gate', success=False, **gate)
    write(proof_path, proof)
    write(root / task_path, task)

    # Consume the actual runtime producer's receipt through the separate gate.
    changed = copy.deepcopy(task)
    changed['status'] = 'in-progress'
    control = changed['control']
    control['authorization']['requiredCapabilities'] = [{'name': 'write-source', 'scope': 'src', 'producer': 'native-filesystem'}]
    for claim in control['claims'].values():
        if claim['state'] == 'satisfied':
            claim.update(state='open', evidence=[])
    authority = oc.authority_digest(changed)
    control['assignment']['authorityDigest'] = authority
    write(root / task_path, changed)
    current_request = copy.deepcopy(request)
    current_request['authorityDigest'] = authority
    write(root / 'gate-request.json', current_request)
    gate['EVENT'] = 'pre-write'
    activity('missing-capability-rejected', 'control-gate', success=False, **gate)
    capability_request = {'scope': str(root / 'src'), 'owned': True, 'authorization': 'allowed',
                          'authorizationRevision': control['authorization']['revision'],
                          'authorityDigest': authority, 'conditionsDigest': oc.digest(control['conditions']),
                          'producer': 'native-filesystem'}
    write(work / 'capability-request.json', capability_request)
    receipt = activity('native-capability-probe', 'control-capability', REQUEST=work / 'capability-request.json')
    ref = write(root / 'capability.json', receipt)
    current_request['capabilities'] = [{'name': 'write-source', 'status': 'available', 'evidence': ref}]
    write(root / 'gate-request.json', current_request)
    activity('native-capability-consumed', 'control-gate', **gate)
    capability_request['authorization'] = 'denied'
    write(work / 'capability-request.json', capability_request)
    receipt = activity('native-denial-probe', 'control-capability', REQUEST=work / 'capability-request.json')
    current_request['capabilities'][0]['evidence'] = write(root / 'capability.json', receipt)
    write(root / 'gate-request.json', current_request)
    activity('denial-cannot-grant', 'control-gate', success=False, **gate)

    write(root / task_path, task)
    write(root / 'gate-request.json', request)
    proposed = copy.deepcopy(task)
    proposed['current']['summary'] = 'Native activities independently checked'
    write(work / 'proposal.json', proposed)
    expected = hashlib.sha256((root / task_path).read_bytes()).hexdigest()
    reconcile = dict(ROOT=root, TASK=task_path, PROPOSAL=work / 'proposal.json')
    activity('stale-task-cas-rejected', 'control-reconcile', success=False, EXPECTED_SHA256='0' * 64, **reconcile)
    activity('task-cas-published', 'control-reconcile', EXPECTED_SHA256=expected, **reconcile)
    if json.loads((root / task_path).read_text()) != proposed:
        raise ValueError('task readback differs')
    command('native-reconciled-acceptance', native)
    activity('task-checkpoint', 'control-checkpoint', ROOT=root, TASK=task_path, DESTINATION=work / 'checkpoint')
    activity('task-resume', 'control-resume', ROOT=root, TASK=task_path, CHECKPOINT=work / 'checkpoint', DESTINATION=work / 'resume')
    if (work / 'resume/restored/src/result.txt').read_bytes() != b'Observable result\n':
        raise ValueError('resume consumer differs')

    write(work / 'spec.json', {'fields': ['progress'], 'jitter': {'progress': 1}})
    state = 'absent'
    for label, observation, wake in [('first-observation', {'progress': 10}, True),
                                    ('unchanged-quiet', {'progress': 10.8}, False),
                                    ('cumulative-drift', {'progress': 11.2}, True),
                                    ('critical-wake', {'progress': 11.2, 'failure': True}, True),
                                    ('persistent-critical-quiet', {'progress': 11.2, 'failure': True}, False)]:
        write(work / 'observation.json', observation)
        result = activity(label, 'control-observe', SPEC=work / 'spec.json', OBSERVATION=work / 'observation.json', STATE=work / 'state.json', EXPECT=state)
        if result['wake'] is not wake:
            raise ValueError(label + ': wrong wake decision')
        state = result['stateDigest']

    resource = work / 'scratch'
    write(work / 'init.json', {'resource': str(resource), 'owner': 'trial'})
    marker = activity('resource-init', 'control-resource-init', REQUEST=work / 'init.json')
    (resource / 'unique.sh').write_text('#!/bin/sh\nexit 0\n')
    (resource / 'unique.sh').chmod(0o750)
    resource_request = {'resource': str(resource), 'owner': 'trial', 'resourceId': marker['id'],
                        'checkpoint': str(work / 'resource-checkpoint'), 'shared': False, 'dependents': [],
                        'lease': {'state': 'released', 'revision': '1'}, 'retire': True}
    write(work / 'resource.json', resource_request)
    activity('resource-plan', 'control-resource-plan', REQUEST=work / 'resource.json', OUTPUT=work / 'plan.json')
    for operation in ('preserve', 'apply'):
        activity('resource-' + operation, 'control-resource-' + operation, REQUEST=work / 'resource.json', PLAN=work / 'plan.json')
    if resource.exists():
        raise ValueError('retired resource remains')
    restored = work / 'restored-scratch'
    write(work / 'restore-init.json', {'resource': str(restored), 'owner': 'trial'})
    marker = activity('restore-init', 'control-resource-init', REQUEST=work / 'restore-init.json')
    write(work / 'restore.json', {'destination': str(restored), 'owner': 'trial', 'resourceId': marker['id']})
    activity('resource-restore', 'control-resource-restore', REQUEST=work / 'restore.json', PLAN=work / 'plan.json')
    if (restored / 'unique.sh').read_bytes() != b'#!/bin/sh\nexit 0\n' or (restored / 'unique.sh').stat().st_mode & 0o777 != 0o750:
        raise ValueError('restored source or executable mode differs')
    result = activity('owner-policy-evaluation', 'control-evaluate', INPUT=REPO / 'examples/control-evaluation/pilot.json')
    if result['recommendation'] != 'adopt':
        raise ValueError('sample owner policy was not met')
    summary = {'valid': True, 'scope': 'disposable native control integration; no host adoption or productivity claim', 'checks': checks}
    write(work / 'summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, help='new directory to retain fixtures and logs')
    args = parser.parse_args()
    try:
        if args.evidence_dir:
            result = run_trial(args.evidence_dir.absolute())
        else:
            temporary = Path(tempfile.mkdtemp(prefix='outcome-controls-'))
            try:
                result = run_trial(temporary / 'trial')
            except BaseException:
                print('Failed trial evidence retained at ' + str(temporary), file=sys.stderr)
                raise
            shutil.rmtree(temporary)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
