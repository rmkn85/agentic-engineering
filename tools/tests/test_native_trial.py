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
        for helper in ('finish_check.py', 'work_audit.py', 'goal_control.py', 'outcome_control.py'):
            shutil.copy(TOOLS / helper, self.source / 'tools' / helper)
        subprocess.run(['git', 'init', '-q'], cwd=self.source, check=True)
        subprocess.run(['git', 'add', '.'], cwd=self.source, check=True)
        subprocess.run(['git', '-c', 'user.name=Trial', '-c', 'user.email=trial@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'source'], cwd=self.source, check=True)
        self.ref = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.source, text=True).strip()
        self.repo = self.base / 'worker'; self.audit = self.base / 'audit'

    def prepare(self, scenario='workflow-false-completion'):
        return trial.prepare(self.source, self.ref, FIXTURE, scenario, self.repo, self.audit,
                             'baseline', 'pair-1', FIXTURE, self.ref, self.ref)

    def outer_prepare(self):
        frozen = {'mode': 'outer-codex-sandbox', 'status': 'verified', 'signature_sha256': 'stable',
                  'mount_namespace': 'mnt:[prepare]'}
        with mock.patch.object(trial.native_boundary, 'observe', return_value=frozen):
            trial.prepare(self.source, self.ref, FIXTURE, 'healthy-small-change', self.repo, self.audit,
                          'baseline', 'pair-1', FIXTURE, self.ref, self.ref, boundary='outer-codex-sandbox')
        return frozen

    def test_failed_outer_prepare_retains_observation_before_build(self):
        failed = {'mode': 'outer-codex-sandbox', 'status': 'failed', 'checks': {'root_readonly': False}}
        with mock.patch.object(trial.native_boundary, 'observe', return_value=failed):
            with self.assertRaisesRegex(ValueError, 'outer execution boundary unavailable'):
                trial.prepare(self.source, self.ref, FIXTURE, 'healthy-small-change', self.repo, self.audit,
                              'baseline', 'pair-1', FIXTURE, self.ref, self.ref, boundary='outer-codex-sandbox')
        self.assertFalse(self.repo.exists())
        self.assertFalse((self.audit / 'corpus').exists())
        observation = self.audit / 'prepare-boundary.json'
        self.assertEqual(json.loads(observation.read_text()), failed)
        row = json.loads((self.audit / 'attempts.jsonl').read_text())
        self.assertEqual(row['boundary_sha256'], trial.digest(observation))

    def test_outer_boundary_failed_or_changed_retains_each_attempt_without_launch(self):
        frozen = self.outer_prepare()
        observations = [{'mode': frozen['mode'], 'status': 'failed'},
                        dict(frozen, signature_sha256='changed')]
        with mock.patch.object(trial, 'preflight', side_effect=[
                {'execution_boundary': observed, 'host_controls': trial.host_controls(),
                 'cli_available': True, 'required_cli_flags': True, 'ephemeral_supported': True,
                 'authenticated': True, 'cached_model_available': True, 'hook_config_present': False}
                for observed in observations]) as preflight, \
             mock.patch.object(trial.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as launch:
            results = []
            for _ in observations:
                results.append(trial.run(self.audit))
                launch.assert_not_called()
        for result, observed in zip(results, observations):
            self.assertEqual(result['status'], 'execution_boundary_failed')
            path = self.audit / result['preflight_file']
            self.assertEqual(trial.digest(path), result['preflight_sha256'])
            self.assertEqual(json.loads(path.read_text())['execution_boundary'], observed)
        self.assertEqual(preflight.call_args.args[-1], 'outer-codex-sandbox')
        self.assertFalse((self.audit / 'launch.json').exists())

    def test_outer_launch_uses_only_frozen_mode_and_accepts_new_namespace(self):
        frozen = self.outer_prepare()
        check = {'execution_boundary': dict(frozen, mount_namespace='mnt:[run]'),
                 'host_controls': trial.host_controls(), 'cli_available': True, 'required_cli_flags': True,
                 'ephemeral_supported': True, 'authenticated': True, 'cached_model_available': True,
                 'hook_config_present': False, 'read_only_sandbox_probe': {'status': 'not_applicable'}}
        with mock.patch.object(trial, 'preflight', return_value=check) as preflight, \
             mock.patch.object(trial.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as launch:
            self.assertEqual(trial.run(self.audit)['status'], 'completed')
        preflight.assert_called_once_with(self.repo, 'codex', None, 'outer-codex-sandbox')
        args = launch.call_args.args[0]
        self.assertEqual(args[args.index('--sandbox') + 1], 'danger-full-access')
        self.assertFalse(any('bypass' in arg for arg in args))
        with self.assertRaises(SystemExit):
            trial.main(['run', '--audit', str(self.audit), '--boundary', 'native'])

    def test_outer_preflight_skips_nested_probe_and_smoke_guard_refuses_launch(self):
        observed = subprocess.CompletedProcess([], 0, '--json --model --cd --ephemeral', '')
        with mock.patch.object(trial, 'command', return_value=observed), \
             mock.patch.object(trial.native_boundary, 'observe', return_value={'status': 'failed'}), \
             mock.patch.object(trial, 'read_only_sandbox_probe') as probe:
            check = trial.preflight(self.source, boundary='outer-codex-sandbox')
            probe.assert_not_called()
        self.assertEqual(check['read_only_sandbox_probe']['status'], 'not_applicable')
        with mock.patch.object(trial, 'preflight', return_value=check), mock.patch.object(trial.subprocess, 'run') as launch:
            result = trial.smoke(self.source, self.base / 'smoke', boundary='outer-codex-sandbox')
            launch.assert_not_called()
        self.assertEqual(result['status'], 'execution_boundary_failed')
        self.assertFalse(result['model_request_feasible'])
        self.assertEqual(result['preflight_sha256'], trial.digest(self.base / 'smoke/preflight.json'))

    def test_verified_outer_smoke_omits_inner_sandbox_without_claiming_tools(self):
        observed = {'execution_boundary': {'status': 'verified'}, 'hook_config_present': False,
                    'native_hook_trust': 'unknown', 'read_only_sandbox_probe': {'status': 'not_applicable'}}
        def fake_run(args, **kwargs):
            self.assertEqual(args[args.index('--sandbox') + 1], 'danger-full-access')
            self.assertNotIn('-s', args)
            kwargs['stdout'].write(json.dumps({'type': 'item.completed', 'item': {
                'type': 'agent_message', 'text': 'NATIVE_PREFLIGHT_OK'}}) + '\n')
            return subprocess.CompletedProcess(args, 0)
        with mock.patch.object(trial, 'preflight', return_value=observed), \
             mock.patch.object(trial.subprocess, 'run', side_effect=fake_run):
            result = trial.smoke(self.source, self.base / 'smoke', boundary='outer-codex-sandbox')
        self.assertTrue(result['model_request_feasible'])
        self.assertEqual(result['read_only_sandbox_probe']['status'], 'not_applicable')
        self.assertFalse(result['model_tool_execution_proven'])
        self.assertFalse(result['workspace_write_execution_proven'])

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
        trial.append(self.audit, {'phase':'run', 'status':'completed', 'final_state_sha256': trial.state_digest(trial.workspace_state(self.repo))})
        self.assertTrue(trial.score(self.audit)['passed'])
        (self.repo / 'Makefile').write_text('check:\n\ttrue\n')
        with self.assertRaisesRegex(ValueError, 'changed after native run'):
            trial.score(self.audit)

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
            self.assertNotIn('--sandbox', args)
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
        self.assertTrue(result['model_request_feasible'])
        self.assertNotIn('feasible', result)
        self.assertFalse(result['model_tool_execution_proven'])
        self.assertFalse(result['workspace_write_execution_proven'])
        self.assertFalse(result['hook_adoption_proven'])
        self.assertIsNone(result['runtime_settings']['effort'])
        self.assertTrue((audit / 'stderr.log').exists())

    def test_read_only_probe_preserves_managed_policy_and_failure_evidence(self):
        help_result = subprocess.CompletedProcess([], 0, '--permission-profile --include-managed-config --cd', '')
        failed = subprocess.CompletedProcess([], 1, '', 'sandbox startup denied')
        with mock.patch.object(trial.sys, 'platform', 'linux'), mock.patch.object(trial.subprocess, 'run', side_effect=[help_result, failed]) as run:
            result = trial.read_only_sandbox_probe(self.source, '/pinned/codex')
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['stderr'], 'sandbox startup denied')
        self.assertEqual(run.call_args.args[0], ['/pinned/codex', 'sandbox', '--permission-profile',
                         ':read-only', '--include-managed-config', '-C', str(self.source), '--', '/bin/true'])
        self.assertFalse(result['workspace_write_execution_proven'])

    def test_read_only_probe_success_is_only_command_startup(self):
        help_result = subprocess.CompletedProcess([], 0, '--permission-profile --include-managed-config --cd', '')
        with mock.patch.object(trial.sys, 'platform', 'linux'), mock.patch.object(trial.subprocess, 'run', side_effect=[help_result, subprocess.CompletedProcess([], 0, '', '')]):
            result = trial.read_only_sandbox_probe(self.source, 'codex')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(result['scope'], 'read_only_command_startup')
        self.assertFalse(result['workspace_write_execution_proven'])

    def test_unsupported_or_unobserved_probe_is_unknown(self):
        with mock.patch.object(trial.sys, 'platform', 'darwin'), mock.patch.object(trial.subprocess, 'run') as run:
            self.assertEqual(trial.read_only_sandbox_probe(self.source, 'codex')['status'], 'unknown')
            run.assert_not_called()
        with mock.patch.object(trial.sys, 'platform', 'linux'):
            for outcome in (subprocess.CompletedProcess([], 0, 'old CLI help', ''), OSError('unavailable'), subprocess.TimeoutExpired('codex', 15)):
                with self.subTest(outcome=outcome), mock.patch.object(trial.subprocess, 'run', side_effect=outcome if isinstance(outcome, Exception) else [outcome]):
                    self.assertEqual(trial.read_only_sandbox_probe(self.source, 'codex')['status'], 'unknown')

    def test_sandbox_failure_refuses_model_launch_and_retains_attempt(self):
        self.prepare()
        preflight = {'host_controls': trial.host_controls(), 'cli_available': True,
                     'required_cli_flags': True, 'ephemeral_supported': True, 'authenticated': True,
                     'cached_model_available': True, 'hook_config_present': False,
                     'read_only_sandbox_probe': {'status': 'failed', 'returncode': 1, 'stderr': 'sandbox startup denied'}}
        with mock.patch.object(trial, 'preflight', return_value=preflight), mock.patch.object(trial.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            result = trial.run(self.audit, '/pinned/codex')
            run.assert_not_called()
        self.assertEqual(result['status'], 'sandbox_preflight_failed')
        self.assertFalse((self.audit / 'launch.json').exists())
        retained = json.loads((self.audit / 'preflight.json').read_text())
        self.assertEqual(retained, preflight)
        rows = [json.loads(s) for s in (self.audit / 'attempts.jsonl').read_text().splitlines()]
        self.assertEqual([r['status'] for r in rows], ['started', 'sandbox_preflight_failed'])

    def test_failed_preflight_retries_keep_each_complete_hash_bound_observation(self):
        self.prepare()
        observations = [
            {'host_controls': trial.host_controls(), 'cli_available': True,
             'read_only_sandbox_probe': {'status': 'failed', 'returncode': 1,
                                         'stderr': diagnostic, 'argv': ['codex', 'sandbox']}}
            for diagnostic in ('first startup failure', 'second startup failure')
        ]
        with mock.patch.object(trial, 'preflight', side_effect=observations), mock.patch.object(trial.subprocess, 'run') as launch:
            results = [trial.run(self.audit) for _ in observations]
            launch.assert_not_called()
        self.assertEqual([r['status'] for r in results], ['sandbox_preflight_failed'] * 2)
        self.assertNotEqual(results[0]['preflight_file'], results[1]['preflight_file'])
        for result, observation in zip(results, observations):
            self.assertEqual(result['preflight_file'], result['attempt'] + '.preflight.json')
            path = self.audit / result['preflight_file']
            self.assertTrue(path.is_file())
            self.assertEqual(json.loads(path.read_text()), observation)
            self.assertEqual(trial.digest(path), result['preflight_sha256'])
        rows = [json.loads(s) for s in (self.audit / 'attempts.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows), 4)
        for row, result in zip(rows, [results[0]] * 2 + [results[1]] * 2):
            self.assertEqual(row['preflight_file'], result['preflight_file'])
            self.assertEqual(row['preflight_sha256'], result['preflight_sha256'])
        self.assertEqual(json.loads((self.audit / 'preflight.json').read_text()), observations[-1])
        self.assertFalse((self.audit / 'launch.json').exists())

    def test_model_smoke_success_does_not_hide_sandbox_failure(self):
        observed = {'hook_config_present': False, 'native_hook_trust': 'unknown',
                    'read_only_sandbox_probe': {'status': 'failed'}}
        def fake_run(args, **kwargs):
            kwargs['stdout'].write(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'NATIVE_PREFLIGHT_OK'}}) + '\n')
            return subprocess.CompletedProcess(args, 0)
        with mock.patch.object(trial, 'preflight', return_value=observed), mock.patch.object(trial.subprocess, 'run', side_effect=fake_run):
            result = trial.smoke(self.source, self.base / 'smoke')
        self.assertTrue(result['model_request_feasible'])
        self.assertEqual(result['read_only_sandbox_probe']['status'], 'failed')
        self.assertFalse(result['model_tool_execution_proven'])

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
        with self.assertRaisesRegex(ValueError, 'already launched'):
            trial.run(self.audit)
        rows = [json.loads(s) for s in (self.audit/'attempts.jsonl').read_text().splitlines()]
        self.assertEqual([r['status'] for r in rows], ['started','interrupted','reuse_rejected'])

    def test_instruction_export_excludes_oracles_before_generic_builder(self):
        directory = self.source / 'validation/trials/recurrence'
        directory.mkdir(parents=True)
        (directory / 'scoring.py').write_text('SEALED_ORACLE_MARKER = 17\n')
        external = self.source / 'standalone_evaluator.py'
        external.write_bytes(FIXTURE.read_bytes())
        subprocess.run(['git', 'add', '.'], cwd=self.source, check=True)
        subprocess.run(['git', '-c', 'user.name=Trial', '-c', 'user.email=trial@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Trial-only evaluator assets'], cwd=self.source, check=True)
        ref = subprocess.check_output(['git','rev-parse','HEAD'], cwd=self.source, text=True).strip()
        frozen = trial.prepare(self.source, ref, external, 'workflow-false-completion', self.repo,
                               self.audit, 'baseline', 'pair-1', external, ref, ref)
        installed = self.repo / '.agentic-engineering'
        self.assertFalse((installed / 'validation/trials').exists())
        self.assertFalse((installed / 'standalone_evaluator.py').exists())
        self.assertFalse(any(p.is_file() and trial.digest(p) == trial.digest(external) for p in installed.rglob('*')))
        self.assertTrue((self.repo / 'consumer_acceptance.py').is_file())
        self.assertIn('standalone_evaluator.py', frozen['instruction_export']['excluded_files'])
        self.assertNotEqual(frozen['instruction_export']['source_tree_sha256'], frozen['instruction_export']['export_tree_sha256'])

    def test_trust_report_binds_exact_hook_configuration(self):
        hooks = self.source / '.codex/hooks.json'
        hooks.parent.mkdir(); hooks.write_text('{"hooks":{}}')
        receipt = self.base / 'trust.json'
        trial.write(receipt, {'native_hook_trust':'confirmed', 'hook_config_sha256':'wrong'})
        observed = subprocess.CompletedProcess([], 0, '--json --model --cd --ephemeral', '')
        with mock.patch.object(trial, 'command', return_value=observed):
            with self.assertRaisesRegex(ValueError, 'current hook configuration bytes'):
                trial.preflight(self.source, trust_receipt=receipt)
            trial.write(receipt, {'native_hook_trust':'confirmed', 'hook_config_sha256':trial.digest(hooks)})
            result = trial.preflight(self.source, trust_receipt=receipt)
            self.assertEqual(result['native_hook_trust'], 'reported_confirmed')
            self.assertFalse(result['hook_invocation_observed'])
            hooks.write_text('{"hooks":{"changed":[]}}')
            with self.assertRaisesRegex(ValueError, 'current hook configuration bytes'):
                trial.preflight(self.source, trust_receipt=receipt)
            hooks.unlink()
            self.assertEqual(trial.preflight(self.source, trust_receipt=receipt)['native_hook_trust'], 'unknown')

    def test_changed_initial_tree_never_launches(self):
        self.prepare()
        (self.repo / 'coaching.txt').write_text('manual assistance after freeze')
        with mock.patch.object(trial.subprocess, 'run') as launcher:
            with self.assertRaisesRegex(ValueError, 'initial workspace changed'):
                trial.run(self.audit)
            launcher.assert_not_called()
        rows = [json.loads(line) for line in (self.audit / 'attempts.jsonl').read_text().splitlines()]
        self.assertEqual(rows[-1]['status'], 'initial_state_changed')

    def test_export_excludes_derived_solutions_and_review_evidence(self):
        for name in ('tools/tests/test_fixture.py', 'validation/reviews/repair.md'):
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('The exact solved outcome and expected repair')
        subprocess.run(['git', 'add', '.'], cwd=self.source, check=True)
        subprocess.run(['git', '-c', 'user.name=Trial', '-c', 'user.email=trial@example.invalid',
                        '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture solution assets'], cwd=self.source, check=True)
        self.ref = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=self.source, text=True).strip()
        spec = self.prepare()
        for name in ('tools/tests/test_fixture.py', 'validation/reviews/repair.md'):
            self.assertFalse((self.repo / '.agentic-engineering' / name).exists())
            self.assertIn(name, spec['instruction_export']['excluded_files'])

    def test_global_instruction_change_invalidates_host_identity(self):
        # A disposable fake host is a deterministic fixture, not a native run.
        home = self.base / 'fake-host'; home.mkdir()
        instructions = home / 'AGENTS.md'; instructions.write_text('Original global instructions')
        with mock.patch.dict('os.environ', {'CODEX_HOME': str(home)}):
            before = trial.host_controls()
            self.assertIn('AGENTS.md', before)
            self.assertEqual(before['AGENTS.md'], trial.digest(instructions))
            instructions.write_text('Different global instructions')
            self.assertNotEqual(before, trial.host_controls())

    def test_postrun_external_repair_cannot_be_scored_as_autonomous(self):
        self.prepare()
        trial.append(self.audit, {'phase': 'run', 'status': 'completed',
                                 'final_state_sha256': trial.state_digest(trial.workspace_state(self.repo))})
        (self.repo / 'summary.py').write_text(fixture.REPAIRED)
        with self.assertRaisesRegex(ValueError, 'changed after native run'):
            trial.score(self.audit)

    def test_wrong_arm_source_and_internal_evaluator_refused(self):
        with self.assertRaisesRegex(ValueError, 'arm does not match'):
            trial.prepare(self.source,self.ref,FIXTURE,'workflow-false-completion',self.repo,self.audit,'other','p',FIXTURE,self.ref,self.ref)
        with self.assertRaisesRegex(ValueError, 'outside'):
            trial.prepare(self.source,self.ref,FIXTURE,'workflow-false-completion',self.repo,self.audit,'baseline','p',self.repo/'eval.py',self.ref,self.ref)

if __name__ == '__main__': unittest.main()
