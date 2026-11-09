import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import native_trial as trial
FIXTURE = TOOLS.parent / 'validation/trials/recurrence/fixture.py'
spec = importlib.util.spec_from_file_location('recurrence_fixture', FIXTURE)
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)

class NativeTrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / 'source'; self.source.mkdir()
        (self.source / 'AGENTS.md').write_text('# normal instructions\n')
        (self.source / 'tools').mkdir()
        import shutil
        for helper in ('finish_check.py', 'work_audit.py'):
            shutil.copy(TOOLS / helper, self.source / 'tools' / helper)
        subprocess.run(['git', 'init', '-q'], cwd=self.source, check=True)
        subprocess.run(['git', 'add', '.'], cwd=self.source, check=True)
        subprocess.run(['git', '-c', 'user.name=Trial', '-c', 'user.email=trial@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'source'], cwd=self.source, check=True)
        self.ref = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.source, text=True).strip()
        self.repo = self.base / 'worker'; self.audit = self.base / 'audit'

    def prepare(self, scenario='workflow-false-completion'):
        return trial.prepare(self.source, self.ref, FIXTURE, scenario, self.repo, self.audit,
                             'baseline', 'pair-1', FIXTURE, self.ref, self.ref)

    def test_frozen_sources_prompt_and_independent_consumer(self):
        spec = self.prepare()
        self.assertEqual(spec['source_commits'], {'baseline': self.ref, 'candidate': self.ref})
        self.assertNotIn('normal instructions', (self.audit / 'prompt.txt').read_text())
        self.assertIn('.agentic-engineering/AGENTS.md', (self.repo / 'AGENTS.md').read_text())
        self.assertFalse(trial.score(self.audit)['passed'])
        (self.repo / 'summary.py').write_text('import json\ndef total(rows): return sum(r["quantity"]*r["price"] for r in rows)\ndef export(rows): return json.dumps({"total":total(rows),"count":len(rows)})\n')
        self.assertFalse(trial.score(self.audit)['calibration_passed'])
        with (self.repo / 'Makefile').open('a') as out:
            out.write('check: consumer-check\n')
        result = trial.score(self.audit)
        self.assertTrue(result['calibration_passed'])
        self.assertFalse(result['passed'])
        self.assertEqual(result['status'], 'calibration')
        trial.append(self.audit, {'phase':'run', 'status':'completed'})
        self.assertTrue(trial.score(self.audit)['passed'])
        (self.repo / 'Makefile').write_text('check:\n\ttrue\n')
        self.assertFalse(trial.score(self.audit)['passed'])

    def test_healthy_has_consumer_acceptance(self):
        self.prepare('healthy-small-change')
        self.assertFalse(trial.score(self.audit)['passed'])
        (self.repo / 'summary.py').write_text('import json\ndef total(rows): return sum(r["quantity"]*r["price"] for r in rows)\ndef export(rows,currency="USD"): return json.dumps({"total":total(rows),"currency":currency})\n')
        self.assertTrue(trial.score(self.audit)['calibration_passed'])

    def test_stale_success_was_produced_by_helper_then_invalidated(self):
        self.prepare('stale-successful-handoff')
        status = json.loads((self.repo / '.agent/goal-status.json').read_text())
        self.assertTrue(status['met'])
        self.assertIn('NotImplementedError', (self.repo / 'summary.py').read_text())
        self.assertFalse(trial.score(self.audit)['calibration_passed'])
        prompt = (self.audit / 'prompt.txt').read_text()
        self.assertIn('Improve this repository workflow', prompt)
        self.assertNotIn('Complete export', prompt)

    def test_prompt_and_spec_tampering_refused(self):
        self.prepare()
        (self.audit / 'prompt.txt').write_text('different')
        with self.assertRaisesRegex(ValueError, 'prompt changed'): trial.load(self.audit)

    def test_native_run_preserves_host_flags_and_logs_usage(self):
        self.prepare()
        preflight = {'cli_available': True, 'required_cli_flags': True, 'ephemeral_supported': True, 'authenticated': True,
                     'cached_model_available': True, 'hook_config_present': False, 'host_controls': trial.host_controls()}
        def fake_run(args, **kwargs):
            self.assertEqual(args[:3], ['codex', 'exec', '--json'])
            self.assertIn('--ephemeral', args)
            self.assertIn('model_reasoning_effort="medium"', args)
            self.assertFalse(any(a.startswith('--ignore') or 'bypass' in a for a in args))
            kwargs['stdout'].write(json.dumps({'type':'turn.completed','usage':{'input_tokens':12,'output_tokens':3}})+'\n')
            return subprocess.CompletedProcess(args, 0)
        with mock.patch.object(trial, 'preflight', return_value=preflight), mock.patch.object(trial.subprocess, 'run', side_effect=fake_run):
            result = trial.run(self.audit)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['usage']['input_tokens'], 12)
        self.assertIsNone(result['hook_calls'])
        self.assertEqual(len((self.audit / 'attempts.jsonl').read_text().splitlines()), 2)

    def test_smoke_uses_read_only_and_same_native_settings(self):
        audit = self.base / 'smoke'
        def fake_run(args, **kwargs):
            self.assertIn('--ephemeral', args)
            self.assertEqual(args[args.index('-s') + 1], 'read-only')
            self.assertEqual(kwargs['input'], 'Reply NATIVE_PREFLIGHT_OK. Do not edit files or run tools.')
            kwargs['stdout'].write(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'NATIVE_PREFLIGHT_OK'}}) + '\n')
            return subprocess.CompletedProcess(args, 0)
        with mock.patch.object(trial, 'preflight', return_value={'hook_config_present':False,'native_hook_trust':'unknown'}), mock.patch.object(trial.subprocess, 'run', side_effect=fake_run):
            result = trial.smoke(self.source, audit)
        self.assertTrue(result['feasible'])
        self.assertFalse(result['hook_adoption_proven'])
        self.assertIsNone(result['runtime_settings']['effort'])
        self.assertTrue((audit / 'stderr.log').exists())

    def test_hooks_require_native_trust_without_launch(self):
        self.prepare()
        preflight = {'cli_available': True, 'required_cli_flags': True, 'ephemeral_supported': True, 'authenticated': True,
                     'cached_model_available': True, 'hook_config_present': True, 'native_hook_trust': 'unknown', 'host_controls': trial.host_controls()}
        with mock.patch.object(trial, 'preflight', return_value=preflight), mock.patch.object(trial.subprocess, 'run') as run:
            result = trial.run(self.audit)
            run.assert_not_called()
        self.assertEqual(result['status'], 'native_hook_trust_required')

    def test_failed_and_interrupted_attempts_retained(self):
        self.prepare()
        preflight = {'cli_available': True, 'required_cli_flags': True, 'ephemeral_supported': True, 'authenticated': True,
                     'cached_model_available': None, 'hook_config_present': False, 'host_controls': trial.host_controls()}
        with mock.patch.object(trial, 'preflight', return_value=preflight), mock.patch.object(trial.subprocess, 'run', side_effect=KeyboardInterrupt):
            self.assertEqual(trial.run(self.audit)['status'], 'interrupted')
        with mock.patch.object(trial, 'preflight', return_value={**preflight, 'authenticated':False}):
            self.assertEqual(trial.run(self.audit)['status'], 'preflight_failed')
        rows = [json.loads(s) for s in (self.audit/'attempts.jsonl').read_text().splitlines()]
        self.assertEqual([r['status'] for r in rows], ['started','interrupted','started','preflight_failed'])

    def test_wrong_arm_source_and_internal_evaluator_refused(self):
        with self.assertRaisesRegex(ValueError, 'arm does not match'):
            trial.prepare(self.source,self.ref,FIXTURE,'workflow-false-completion',self.repo,self.audit,'other','p',FIXTURE,self.ref,self.ref)
        with self.assertRaisesRegex(ValueError, 'outside'):
            trial.prepare(self.source,self.ref,FIXTURE,'workflow-false-completion',self.repo,self.audit,'baseline','p',self.repo/'eval.py',self.ref,self.ref)

if __name__ == '__main__': unittest.main()
