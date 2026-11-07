"""Activity parameters cannot become a shell, alternate script or extra goal."""
import importlib.util
from pathlib import Path
import unittest

TOOLS = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('control_activity', TOOLS / 'control_activity.py')
activity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(activity)


class ActivityTests(unittest.TestCase):
    def test_delivery_arguments_reach_only_fixed_native_entry(self):
        args = activity.command(['control-gate', 'ROOT=/tmp/owned', 'TASK=work/tasks/T.json',
                                 'EVENT=pre-write', 'REQUEST=/tmp/request.json'])
        self.assertEqual(args[1:], [str(TOOLS / 'outcome_control.py'), '--root=/tmp/owned',
                                   '--task=work/tasks/T.json', 'gate', 'pre-write',
                                   '--request=/tmp/request.json'])

    def test_literal_values_never_become_shell_or_extra_arguments(self):
        value = '/tmp/a space; $(touch injected)'
        args = activity.command(['control-resource-plan', 'REQUEST=' + value])
        self.assertEqual(args[1:], [str(TOOLS / 'control_runtime.py'), 'plan', '--request=' + value])

    def test_unknown_options_extra_goals_and_duplicates_rejected(self):
        for args in ([], ['control-shell', 'COMMAND=true'], ['control-validate', '-f', 'other'],
                     ['control-capability', 'REQUEST=a', 'REQUEST=b'],
                     ['control-capability', 'REQUEST=a', 'SHELL=b'],
                     ['control-capability', 'REQUEST=a', 'control-resource-apply'],
                     ['control-resource-apply', 'REQUEST=a'],
                     ['control-gate', 'ROOT=a', 'TASK=b', 'EVENT=--help', 'REQUEST=c'],
                     ['control-capability', 'REQUEST=']):
            with self.subTest(args=args), self.assertRaises(ValueError):
                activity.command(args)

    def test_evaluation_filename_cannot_select_an_option(self):
        self.assertEqual(activity.command(['control-evaluate', 'INPUT=-malformed'])[1:],
                         [str(TOOLS / 'control_evaluation.py'), '--', '-malformed'])


if __name__ == '__main__':
    unittest.main()
