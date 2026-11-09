#!/usr/bin/env python3
"""Require current independent-review evidence for changed methodology controls.

The manifest binds reviewed bytes, original request, independent framing and
review report. It detects stale or absent review; hashes cannot authenticate a
reviewer or determine whether their judgment is correct.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from blind_review import validate_frame


# Review is required only where an agent could grade its own work or switch a guard off:
# finish/outcome gates, trial evaluators, the proof, review and self-audit checks, and
# the routes CI uses to run them. Guidance prose is held by the guidance budget and
# ordinary tools by their tests and mutation proofs; neither needs a receipt.
CONTROLS = frozenset(('Makefile', 'tools/make') + tuple(f'tools/{name}.py' for name in (
    'finish_check', 'goal_control', 'outcome_control', 'control_evaluation', 'native_trial', 'run_trial',
    'check_review', 'blind_review', 'prove_guards', 'check_findings', 'check_guidance_budget', 'guard_command',
    'agent_hooks', 'work_audit')))


def relevant(path):
    return (path in CONTROLS or path.startswith('.github/workflows/') or
            (path.startswith('validation/trials/') and path.endswith('.py')))


def identity(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError('review paths must stay inside the repository')
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def check(root, base):
    changed = subprocess.run(['git', 'diff', '--name-only', base, '--'], cwd=root,
                             capture_output=True, text=True, check=True).stdout.splitlines()
    new = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], cwd=root,
                         capture_output=True, text=True, check=True).stdout.splitlines()
    required = {p for p in changed + new if relevant(p)}
    if not required:
        return []
    covered, invalid = set(), []
    for path in sorted((root / 'validation/reviews').glob('*.json')):
        try:
            review = json.loads(path.read_text())
            if review.get('schema') != 'methodology-review/v1':
                continue
            # The accepted report belongs to the exact independent framing inputs.
            for key in ('framing', 'request', 'failure_evidence'):
                if identity(root, review[key]) != review['input_hashes'][key]:
                    raise ValueError('review framing inputs changed: ' + key)
            validate_frame(root / review['framing'], root / review['request'], root / review['failure_evidence'])
            report = review['report']
            if not report.get('sha256') or identity(root, report['path']) != report['sha256']:
                raise ValueError('review report changed or is missing')
            if review.get('verdict') != 'accepted':
                continue
            for name, expected in review['files'].items():
                if name in required and identity(root, name) == expected:
                    covered.add(name)
        except (OSError, ValueError, KeyError, TypeError) as error:
            invalid.append(f'{path.name}: {error}')
    missing = required - covered
    return ([f'changed methodology needs current independent review: {p}' for p in sorted(missing)] + invalid)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--base', required=True)
    args = parser.parse_args(argv)
    try:
        errors = check(Path(args.root).resolve(), args.base)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        errors = [str(error)]
    for error in errors:
        print('review-check: ' + error)
    if not errors:
        print('review-check: changed methodology has current review evidence')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
