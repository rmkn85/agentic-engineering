"""Fixed native activity bindings; values are argv data, never shell source."""
import subprocess
import sys
from pathlib import Path

ACTIVITIES = {
    'recurrence-smoke': ('smoke', {'ROOT': '--repository', 'AUDIT': '--audit'}),
    'recurrence-run': ('run', {'AUDIT': '--audit'}),
    'recurrence-score': ('score', {'AUDIT': '--audit'}),
    'recurrence-preflight': ('preflight', {'ROOT': '--repository'}),
}


def main(args=None):
    args = sys.argv[1:] if args is None else args
    if not args or args[0] not in ACTIVITIES:
        raise ValueError('unknown recurrence activity')
    activity = args[0]
    action, fields = ACTIVITIES[activity]
    optional = {'TRUST_RECEIPT': '--trust-receipt'} if activity in ('recurrence-run', 'recurrence-preflight') else {}
    if activity in ('recurrence-run', 'recurrence-preflight', 'recurrence-smoke'):
        optional['CODEX'] = '--codex'
    values = {}
    for argument in args[1:]:
        key, separator, value = argument.partition('=')
        if not separator or key not in {**fields, **optional} or key in values or not value or '\x00' in value or '\n' in value:
            raise ValueError('invalid, extra or duplicate activity parameter')
        if key == 'CODEX' and not Path(value).is_absolute():
            raise ValueError('CODEX must be an absolute executable path')
        values[key] = str(Path(value).resolve())
    if not set(fields) <= set(values):
        raise ValueError('activity requires exactly ' + ', '.join(fields))
    command = [sys.executable, str(Path(__file__).with_name('native_trial.py')), action]
    for key, flag in {**fields, **optional}.items():
        if key in values:
            command += [flag, values[key]]
    return subprocess.call(command)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
