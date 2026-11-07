#!/usr/bin/env python3
"""Create a neutral controlled task and exercise its real local-file consumer."""
import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL = Path(__file__).resolve().parents[2] / 'tools/outcome_control.py'
spec = importlib.util.spec_from_file_location('outcome_control', TOOL)
oc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oc)


def write(root, path, value):
    raw = value if isinstance(value, bytes) else json.dumps(value, indent=2).encode() + b'\n'
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest()}


def build_example(root):
    root = Path(root)
    root.mkdir()  # Refuse to overwrite existing work, including an empty directory.
    source = write(root, 'src/result.txt', b'Observable result\n')
    applicable = ('implemented', 'verified')
    rules = {claim: {'applicable': claim in applicable,
                    'reason': 'Local file requirement' if claim in applicable else 'No separate boundary in this owner-authorized local example',
                    'scenario': 'local-result/' + claim, 'prerequisites': ['implemented'] if claim == 'verified' else [],
                    'classes': ['mechanical'], 'producers': ['file-check'], 'reviewers': ['example-owner'],
                    'loadedRequired': claim == 'verified'} for claim in oc.CLAIMS}
    task = {'schema': 'axioms-task/v1', 'id': 'RESULT-1', 'title': 'Deliver a local result',
            'status': 'in-progress', 'outcome': 'The local reader receives the exact expected result',
            'depends': [], 'acceptance': ['The local reader reads Observable result followed by a newline'], 'evidence': [],
            'current': {'summary': 'Consumer check pending', 'nextAction': 'Read the result', 'blockers': []},
            'control': {'schema': oc.SCHEMA, 'authorization': {'revision': '1', 'owner': 'example-owner',
                        'nonGoals': ['Remote publication'], 'invariants': ['Preserve the exact result'],
                        'decisionRights': list(oc.EVENTS), 'editScope': ['src'], 'deniedScope': [], 'requiredCapabilities': [], 'claims': rules},
                        'assignment': {}, 'source': [source], 'conditions': {'reader': 'local-file/v1'},
                        'claims': {claim: {'state': 'open' if claim in applicable else 'not-applicable', 'evidence': []} for claim in oc.CLAIMS},
                        'decisions': [], 'wip': {'limits': {'changes': 1}, 'items': {k: [] for k in oc.WIP},
                                               'exceptions': [], 'history': [], 'overheadSeconds': None}}}
    control = task['control']
    authority = oc.authority_digest(task)
    candidate = oc.source_digest(control['source'])
    control['assignment'] = {'authorityDigest': authority, 'sourceDigest': candidate,
                             'conditionsDigest': oc.digest(control['conditions']), 'actor': 'example-builder', 'rights': list(oc.EVENTS)}
    request = {'authorityDigest': authority, 'actor': 'example-builder', 'purpose': 'admission', 'paths': ['src/result.txt'],
               'capabilities': [], 'wipAfter': control['wip']['items']}
    errors = oc.check_gate(task, root, 'pre-write', request)
    if errors:
        raise ValueError('; '.join(errors))
    # The oracle is the authorized expected bytes, rather than a successful process exit.
    loaded = (root / source['path']).read_bytes()
    observed_source = [{'path': source['path'], 'sha256': hashlib.sha256(loaded).hexdigest()}]
    passed = loaded == b'Observable result\n'
    native = {'completed': True, 'pass': passed, 'errors': [] if passed else ['Unexpected consumer bytes'],
              'candidateDigest': candidate, 'loadedDigest': oc.source_digest(observed_source)}
    observed = datetime.now(timezone.utc).isoformat()
    for claim in applicable:
        proof = {'schema': 'outcome-evidence/v1', 'claim': claim, 'scenario': rules[claim]['scenario'], 'authorityDigest': authority, 'sourceDigest': candidate,
                 'conditions': control['conditions'], 'class': 'mechanical', 'producer': 'file-check', 'reviewer': 'example-owner',
                 'observedAt': observed, 'status': 'passed' if passed else 'failed', 'native': native}
        ref = write(root, 'evidence/' + claim + '.json', proof)
        control['claims'][claim] = {'state': 'satisfied', 'evidence': [ref]}
    errors = oc.check_gate(task, root, 'pre-completion', request)
    if errors:
        raise ValueError('; '.join(errors))
    task['status'] = 'done'
    task['current'] = {'summary': 'Exact local consumer result verified', 'nextAction': '', 'blockers': []}
    write(root, 'work/tasks/RESULT-1.json', task)
    write(root, 'work/frontier.json', {'schema': 'axioms-frontier/v1', 'repository': 'sample/result',
          'objective': 'Verify a local result', 'controlPolicy': {'schema': 'outcome-policy/v1', 'requiredTasks': ['RESULT-1']}, 'mode': 'product', 'product': ['RESULT-1'], 'maintenance': [], 'parallel': []})
    write(root, 'gate-request.json', request)
    return task


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True, help='new owned example directory')
    parser.add_argument('--checkpoint', type=Path, required=True, help='new durable directory outside destination')
    args = parser.parse_args()
    try:
        task = build_example(args.destination)
        errors = oc.validate_control(task, args.destination)
        if errors:
            raise ValueError('; '.join(errors))
        checkpoint = oc.checkpoint(args.destination, 'work/tasks/RESULT-1.json', args.checkpoint)
        print(json.dumps({'valid': True, 'claims': {k: v['state'] for k, v in task['control']['claims'].items()}, 'checkpointDigest': checkpoint}, indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
