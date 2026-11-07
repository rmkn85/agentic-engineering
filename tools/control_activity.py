#!/usr/bin/env python3
"""Strict native activity bindings; values are argv data, never shell code."""
from pathlib import Path
import subprocess
import sys


def command(arguments):
    if not arguments:
        raise ValueError('one control activity is required')
    activity, *items = arguments
    values = {}
    for item in items:
        key, separator, value = item.partition('=')
        if not separator or not value or key in values or '\x00' in value or '\n' in value:
            raise ValueError('use unique nonempty NAME=value parameters')
        values[key] = value
    runtime = {
        'control-observe': ('observe', ('SPEC', 'OBSERVATION', 'STATE', 'EXPECT'), ('OUTPUT',)),
        'control-capability': ('capability', ('REQUEST',), ('OUTPUT',)),
        'control-resource-init': ('init', ('REQUEST',), ('OUTPUT',)),
        'control-resource-plan': ('plan', ('REQUEST',), ('OUTPUT',)),
        'control-resource-preserve': ('preserve', ('REQUEST', 'PLAN'), ('OUTPUT',)),
        'control-resource-verify': ('verify', ('PLAN',), ('OUTPUT',)),
        'control-resource-apply': ('apply', ('REQUEST', 'PLAN'), ('OUTPUT',)),
        'control-resource-restore': ('restore', ('REQUEST', 'PLAN'), ('OUTPUT',)),
    }
    delivery = {
        'control-validate': ('validate', ('ROOT', 'TASK')),
        'control-gate': ('gate', ('ROOT', 'TASK', 'EVENT', 'REQUEST')),
        'control-checkpoint': ('checkpoint', ('ROOT', 'TASK', 'DESTINATION')),
        'control-resume': ('resume', ('ROOT', 'TASK', 'CHECKPOINT', 'DESTINATION')),
        'control-reconcile': ('reconcile', ('ROOT', 'TASK', 'EXPECTED_SHA256', 'PROPOSAL')),
    }
    if activity in runtime:
        operation, required, optional = runtime[activity]
        script = 'control_runtime.py'
        argv = [operation]
        order = required + optional
    elif activity in delivery:
        operation, required = delivery[activity]
        optional = ()
        script = 'outcome_control.py'
        argv = []
        order = required
    elif activity == 'control-evaluate':
        operation, required, optional = None, ('INPUT',), ()
        script, argv, order = 'control_evaluation.py', ['--'], ('INPUT',)
    else:
        raise ValueError('unknown control activity')
    if not set(required) <= values.keys() or values.keys() - set(required + optional):
        raise ValueError('unexpected or missing parameters for ' + activity)
    for key in order:
        if key not in values:
            continue
        if script == 'outcome_control.py' and key == 'EVENT':
            if values[key] not in ('start', 'resume', 'pre-write', 'pre-integration', 'pre-completion'):
                raise ValueError('unknown gate event')
            argv.append(values[key])
        elif script == 'control_evaluation.py':
            argv.append(values[key])
        else:
            argv.append('--' + key.lower().replace('_', '-') + '=' + values[key])
        if script == 'outcome_control.py' and key == 'TASK':
            argv.append(operation)
    return [sys.executable, str(Path(__file__).with_name(script)), *argv]


def main(argv=None):
    try:
        return subprocess.run(command(sys.argv[1:] if argv is None else argv), check=False).returncode
    except (ValueError, OSError) as error:
        print('control activity: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
