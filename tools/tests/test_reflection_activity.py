import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / 'reflection_activity.py'
spec = importlib.util.spec_from_file_location('reflection_activity', TOOL)
activity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activity)


class ReflectionActivityTests(unittest.TestCase):
    def test_optional_trust_evidence_is_argv_data_without_granting_trust(self):
        evidence = '/tmp/review evidence;not-a-command.json'
        with patch.object(activity.subprocess, 'call', return_value=0) as call:
            self.assertEqual(activity.main(['recurrence-run', 'AUDIT=/tmp/frozen audit',
                                            'TRUST_RECEIPT=' + evidence]), 0)
        self.assertEqual(call.call_args.args[0], [sys.executable, str(TOOL.with_name('native_trial.py')),
                         'run', '--audit', '/tmp/frozen audit', '--trust-receipt', evidence])
        self.assertNotIn('shell', call.call_args.kwargs)

    def test_unknown_duplicate_missing_and_command_parameters_rejected(self):
        for arguments in (['recurrence-run'], ['recurrence-run', 'AUDIT=/tmp/a', 'COMMAND=anything'],
                          ['recurrence-run', 'AUDIT=/tmp/a', 'AUDIT=/tmp/b'],
                          ['recurrence-run', 'AUDIT=/tmp/a\nanything'],
                          ['recurrence-smoke', 'ROOT=/tmp/a', 'AUDIT=/tmp/b', 'TRUST_RECEIPT=/tmp/c']):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                activity.main(arguments)

    def test_optional_pinned_cli_is_one_literal_absolute_argv_value(self):
        pinned = '/tmp/CLI with spaces;literal/codex'
        for name, required in [('recurrence-preflight', ['ROOT=/tmp/repo']),
                               ('recurrence-smoke', ['ROOT=/tmp/repo', 'AUDIT=/tmp/audit']),
                               ('recurrence-run', ['AUDIT=/tmp/audit'])]:
            with self.subTest(name=name), patch.object(activity.subprocess, 'call', return_value=0) as call:
                self.assertEqual(activity.main([name, *required, 'CODEX=' + pinned]), 0)
                self.assertEqual(call.call_args.args[0][-2:], ['--codex', pinned])
                self.assertNotIn('shell', call.call_args.kwargs)
        for extra in (['CODEX=relative/codex'], ['CODEX=/tmp/codex', 'CODEX=/other/codex'], ['CODEX=/tmp/codex\ncommand']):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                activity.main(['recurrence-run', 'AUDIT=/tmp/audit', *extra])
        with self.assertRaises(ValueError):
            activity.main(['recurrence-score', 'AUDIT=/tmp/audit', 'CODEX=/tmp/codex'])

    def test_boundary_is_strict_enum_data_and_unavailable_at_run(self):
        for name, required in [('recurrence-preflight', ['ROOT=/tmp/repo']),
                               ('recurrence-smoke', ['ROOT=/tmp/repo', 'AUDIT=/tmp/audit'])]:
            with patch.object(activity.subprocess, 'call', return_value=0) as call:
                activity.main([name, *required, 'BOUNDARY=outer-codex-sandbox'])
                self.assertEqual(call.call_args.args[0][-2:], ['--boundary', 'outer-codex-sandbox'])
            for value in ('unknown', 'native;command', '/tmp/native'):
                with self.assertRaises(ValueError): activity.main([name, *required, 'BOUNDARY=' + value])
        with self.assertRaises(ValueError):
            activity.main(['recurrence-run', 'AUDIT=/tmp/audit', 'BOUNDARY=native'])

    def test_exact_smoke_route_preserves_result(self):
        with patch.object(activity.subprocess, 'call', return_value=1) as call:
            self.assertEqual(activity.main(['recurrence-smoke', 'ROOT=/tmp/repo', 'AUDIT=/tmp/audit']), 1)
        self.assertEqual(call.call_args.args[0][2:], ['smoke', '--repository', '/tmp/repo', '--audit', '/tmp/audit'])
