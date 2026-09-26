import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / 'practice_feedback.py'
spec = importlib.util.spec_from_file_location('practice_feedback', TOOL)
feedback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feedback)


def record():
    return {'schema': 'practice-feedback/v1', 'record_kind': 'fixture', 'run_id': 'sample-1',
            'source': 'immutable-source', 'task_class': 'boundary-change',
            'practices': [{'id': 'preserve-invariants', 'revision': 'policy-revision',
                'stage': 'applied', 'basis': 'self_report', 'trigger': 'Review is narrowed, product scope is not.',
                'decision': 'Use the existing consumer mechanism instead of removing the invariant.', 'evidence': []}],
            'outcome': {'status': 'accepted', 'evidence': []}, 'measurements': {}}


class PracticeFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / 'native.log'
        self.log.write_bytes(b'consumer check\nPASS count=3\n')
        self.ref = {'path': 'native.log', 'sha256': hashlib.sha256(self.log.read_bytes()).hexdigest()}

    def test_deliberate_nonuse_is_visible_not_counted_as_application(self):
        data = record()
        data['practices'][0]['stage'] = 'not_used'
        result = feedback.summarize([feedback.analyze(data)])
        row = result['cohorts'][0]['practices'][0]
        self.assertEqual(row['stage'], 'not_used')
        self.assertFalse(row['evidence_resolved'])

    def test_claims_without_evidence_stay_unresolved(self):
        result = feedback.analyze(record(), self.root)
        self.assertFalse(result['practices'][0]['evidence_resolved'])
        self.assertFalse(result['outcome_evidence_resolved'])
        self.assertEqual(result['outcome_reported'], 'accepted')

    def test_matched_evidence_does_not_upgrade_self_report(self):
        data = record()
        data['practices'][0]['evidence'] = [self.ref]
        data['outcome']['evidence'] = [self.ref]
        result = feedback.analyze(data, self.root)
        self.assertTrue(result['practices'][0]['evidence_resolved'])
        self.assertEqual(result['practices'][0]['basis'], 'self_report')
        self.assertTrue(result['outcome_evidence_resolved'])

    def test_reference_failures_and_no_root(self):
        self.assertEqual(feedback.check_reference(self.ref, None)['state'], 'unchecked')
        self.assertEqual(feedback.check_reference({**self.ref, 'path': 'absent'}, self.root)['state'], 'missing')
        self.log.write_text('changed')
        self.assertEqual(feedback.check_reference(self.ref, self.root)['state'], 'mismatch')

    def test_fixed_line_range_survives_log_growth_not_truncation(self):
        ref = {'path': 'native.log', 'lines': [2, 2], 'sha256': hashlib.sha256(b'PASS count=3\n').hexdigest()}
        with self.log.open('ab') as stream:
            stream.write(b'later event\n')
        self.assertEqual(feedback.check_reference(ref, self.root)['state'], 'matched')
        self.log.write_text('one line\n')
        self.assertEqual(feedback.check_reference(ref, self.root)['state'], 'mismatch')

    def test_no_external_paths_or_symlink_escape(self):
        for path in ['/etc/passwd', '../private', 'dir/../../private']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                feedback.check_reference({**self.ref, 'path': path}, self.root)
        (self.root / 'escape').symlink_to(self.root.parent)
        with self.assertRaises(ValueError):
            feedback.check_reference({**self.ref, 'path': 'escape/private'}, self.root)

    def test_invalid_receipts_are_not_silently_counted(self):
        mutations = [lambda d: d.update(schema='other'), lambda d: d.update(run_id=''),
                     lambda d: d.update(record_kind='proven'),
                     lambda d: d['practices'][0].update(stage='understood'),
                     lambda d: d['practices'][0].update(basis='certain'),
                     lambda d: d['outcome'].update(preventable_corrections=True),
                     lambda d: d['measurements'].update(tokens=-1),
                     lambda d: d['measurements'].update(wall_seconds=float('nan')),
                     lambda d: d['practices'].append(copy.deepcopy(d['practices'][0]))]
        for mutation in mutations:
            data = record()
            mutation(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                feedback.analyze(data, self.root)

    def test_missing_fields_are_not_zero_and_cohorts_stay_separate(self):
        a, b, c = record(), record(), record()
        b['run_id'] = 'sample-2'
        b['measurements']['wall_seconds'] = 0
        b['outcome']['preventable_corrections'] = 2
        c.update(run_id='actual-1', record_kind='agent_run')
        results = [feedback.analyze(d) for d in [a, b, c]]
        report = feedback.summarize(results)
        cohort = next(g for g in report['cohorts'] if g['record_kind'] == 'fixture')
        self.assertEqual(cohort['measurements']['wall_seconds']['known'], 1)
        self.assertEqual(cohort['measurements']['wall_seconds']['total_runs'], 2)
        self.assertEqual(cohort['measurements']['wall_seconds']['observed_sum'], 0)
        self.assertIsNone(cohort['measurements']['tokens']['observed_sum'])
        self.assertEqual(len(report['cohorts']), 2)
        with self.assertRaises(ValueError):
            feedback.summarize([results[0], results[0]])

    def test_malformed_json_duplicate_keys_and_nonfinite_fail_closed(self):
        for body in ['{', '{"a":1,"a":2}', '{"value":NaN}']:
            path = self.root / 'record.json'
            path.write_text(body)
            with self.assertRaises(ValueError):
                feedback.load_record(path)

    def test_actual_cli_and_no_overwrite(self):
        path, output = self.root / 'record.json', self.root / 'summary.json'
        path.write_text(json.dumps(record()))
        args = [sys.executable, str(TOOL), str(path), '--evidence-root', str(self.root), '--output', str(output)]
        result = subprocess.run(args, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['runs'], 1)
        self.assertIn('details', json.loads(output.read_text()))
        self.assertEqual(subprocess.run(args, capture_output=True).returncode, 2)
        path.write_text('{broken')
        self.assertEqual(subprocess.run(args[:-2], capture_output=True).returncode, 2)

class BenchmarkFeedbackIntegrationTests(unittest.TestCase):
    """Exercise the real benchmark entry point with an offline fake CLI, not a model."""
    def run_trial(self, tmp, native_exit=0, feedback=True):
        import os
        root = Path(tmp)
        repo = root / 'repo'
        repo.mkdir()
        def git(*args):
            return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True)
        git('init', '-q')
        git('config', 'user.name', 'Fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        (repo / 'README.md').write_text('isolated test\n')
        git('add', '.')
        git('commit', '-qm', 'fixture')
        bindir = root / 'bin'; bindir.mkdir()
        fake = bindir / 'codex'
        fake.write_text('#!/bin/sh\nprintf \'{"type":"turn.completed","usage":{"input_tokens":1,"cached_input_tokens":0,"output_tokens":1,"reasoning_output_tokens":0}}\\n\'\n')
        fake.chmod(0o700)
        evaluator = root / 'evaluate.py'
        evaluator.write_text('''import os, json, hashlib, sys
from pathlib import Path
run = Path(os.environ['AGENT_RUN_ARTIFACTS'])
p = run / 'native-proof.txt'
p.write_text('actual fixture evaluation\\n')
record = {'schema':'practice-feedback/v1','record_kind':'fixture','run_id':'isolated-native-trial',
 'source':'fixture-only','task_class':'integration','practices':[],
 'outcome':{'status':'accepted','evidence':[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}}
if sys.argv[2] == 'yes':
 (run / 'practice-feedback.json').write_text(json.dumps(record))
raise SystemExit(int(sys.argv[1]))
''')
        import shlex
        command = shlex.join([sys.executable, str(evaluator), str(native_exit), 'yes' if feedback else 'no'])
        env = {**os.environ, 'PATH': str(bindir) + os.pathsep + os.environ['PATH']}
        # Keep a clean independent home so this fixture never scans a real user's Codex sessions.
        env['CODEX_HOME'] = str(root / 'empty-profile')
        result = subprocess.run([sys.executable, str(TOOL.parent / 'codex-bench.py'), '--repo', str(repo),
                                 '--label', 'offline', '--prompt', 'fixture', '--eval-command', command],
                                capture_output=True, text=True, env=env, timeout=30)
        metrics_path = next((repo / '.agent-bench/runs').glob('*/metrics.json'))
        return result, json.loads(metrics_path.read_text()), metrics_path.parent

    def test_real_entry_point_collects_feedback_and_preserves_native_failure(self):
        for code in (0, 7):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                result, metrics, run = self.run_trial(tmp, native_exit=code)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(metrics['eval_exit_code'], code)
                self.assertEqual(metrics['practice_feedback']['state'], 'recorded')
                self.assertTrue(metrics['practice_feedback']['outcome_evidence_resolved'])
                report = json.loads((run / 'practice-summary.json').read_text())
                self.assertEqual(report['cohorts'][0]['record_kind'], 'fixture')
                self.assertEqual(metrics['usage']['input_tokens'], 1)

    def test_optional_feedback_does_not_invent_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, metrics, run = self.run_trial(tmp, feedback=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(metrics['practice_feedback'], {'state': 'not_recorded'})
            self.assertFalse((run / 'practice-summary.json').exists())


if __name__ == '__main__':
    unittest.main()
