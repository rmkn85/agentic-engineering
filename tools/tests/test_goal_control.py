"""Behavioral regressions for authority, evidence freshness and corrective checks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import finish_check as gate
import goal_control as control
import outcome_control
import work_audit


class GoalControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.agent/\nignored\n')
        (self.root / 'source').write_text('working')
        (self.root / 'requirements').write_text('consumer must work')
        (self.root / 'Makefile').write_text('ok:\n\t@test -f source\nbad:\n\t@false\nchange:\n\t@touch new-source\n')
        self.goal = {'goal': 'Deliver working consumer', 'requirement_refs': ['requirements'],
                     'acceptance': [{'id': 'consumer', 'check': 'consumer works', 'run': 'ok'}]}
        self.save()

    def save(self):
        control.write(self.root / '.agent/goal.json', self.goal)

    def run_gate(self):
        self.save()
        results = gate.evaluate(self.goal, self.root, 5)
        gate.record_status(self.root, self.goal, results)
        return results

    def correction(self, run='ok'):
        self.goal['reflection'] = {'interventions': [{'observation': 'the previous evidence became stale',
             'evidence': 'see requirements', 'hypothesis': 'the correction restores consumer behavior',
             'expected_effect': 'the consumer check should pass', 'run': run, 'status': 'supported'}]}

    def test_shared_canonical_primitive_parity(self):
        self.assertIs(control.digest, outcome_control.digest)
        self.assertIs(control.canonical, outcome_control.canonical)
        self.assertNotEqual(control.digest({'v': True}), control.digest({'v': 1}))

    def test_removed_consumer_cannot_hide_behind_same_goal_text_across_sessions(self):
        self.goal['acceptance'].append({'id': 'failing-consumer', 'check': 'consumer integration', 'run': 'bad'})
        self.run_gate()
        self.goal['acceptance'].pop()
        results = self.run_gate()
        self.assertTrue(any(r['id'] == 'contract' for r in results))
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])

    def test_requirement_content_check_run_and_declared_inputs_are_authority(self):
        original = control.digest(control.contract(self.goal, self.root))
        for field, value in [('check', 'syntax only'), ('run', 'bad'), ('id', 'different')]:
            changed = copy.deepcopy(self.goal)
            changed['acceptance'][0][field] = value
            self.assertNotEqual(original, control.digest(control.contract(changed, self.root)))
        (self.root / 'requirements').write_text('different authority')
        self.assertNotEqual(original, control.digest(control.contract(self.goal, self.root)))

    def test_progress_is_mutable_but_receipt_not_authority_after_source_change(self):
        self.run_gate()
        self.assertIsNone(work_audit.goal_open(self.root))
        self.goal['acceptance'][0]['status'] = 'pass'
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        (self.root / 'source').unlink()
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])
        self.assertTrue(any(r['id'] == 'correction' for r in self.run_gate()))
        (self.root / 'source').write_text('repaired')
        self.assertTrue(any(r['id'] == 'correction' for r in self.run_gate()))
        self.correction()
        self.assertTrue(all(r['state'] == 'met' for r in self.run_gate()))

    def test_healthy_source_change_refreshes_without_authored_intervention(self):
        (self.root / '.gitignore').write_text('.agent/\nignored\n__pycache__/\n')
        (self.root / 'utility.py').write_text('def value(): return 7\n')
        (self.root / 'test_utility.py').write_text('import unittest\nfrom utility import value\nclass UtilityTests(unittest.TestCase):\n    def test_value(self): self.assertEqual(value(), 7)\n')
        (self.root / 'Makefile').write_text('ok:\n\t@' + sys.executable + ' -m unittest discover\n')
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
        old = control.read(self.root / '.agent/goal-status.json')
        original_goal = (self.root / '.agent/goal.json').read_bytes()
        (self.root / 'utility.py').write_text('# Return the stable documented value.\ndef value(): return 7\n')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        before = (self.root / '.agent/goal-status.json').read_bytes()
        self.assertIsNotNone(work_audit.goal_open(self.root))
        inspect = subprocess.run([sys.executable, gate.__file__, '--root', str(self.root), '--inspect'],
                                 capture_output=True, text=True, check=False)
        self.assertEqual(inspect.returncode, 2)
        self.assertEqual((self.root / '.agent/goal-status.json').read_bytes(), before)
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
        self.assertEqual((self.root / '.agent/goal.json').read_bytes(), original_goal)
        self.assertNotIn('reflection', self.goal)
        receipt = control.read(self.root / '.agent/reflection-receipt.json')
        self.assertEqual(receipt['kind'], 'freshness-verification')
        self.assertEqual(receipt['before']['snapshot_digest'], control.digest(old['snapshot']))
        self.assertEqual(receipt['after'], control.observation_identity(self.root, self.goal))
        self.assertNotEqual(receipt['before'], receipt['after'])
        self.assertTrue(all(item['state'] == 'met' for item in receipt['checks']))
        state = control.read(self.root / '.agent/reflection-state.json')
        self.assertTrue(state['resolved'])
        self.assertEqual(state['obligations'][0]['trigger'], 'stale-evidence')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        receipt_bytes = (self.root / '.agent/reflection-receipt.json').read_bytes()
        from unittest.mock import patch
        with patch.object(gate, 'run_target', wraps=gate.run_target) as runner:
            self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
            runner.assert_called_once_with(self.root, 'ok', 5)
        self.assertEqual((self.root / '.agent/reflection-receipt.json').read_bytes(), receipt_bytes)
        (self.root / 'utility.py').write_text('# Preserve the documented value.\ndef value(): return 7\n')
        self.run_gate()
        refreshed = control.read(self.root / '.agent/reflection-receipt.json')
        self.assertEqual(refreshed['history'][0], {k: v for k, v in receipt.items() if k != 'history'})

    def test_declared_input_refresh_and_explicit_stale_trigger_execute_acceptance(self):
        self.goal['inputs'] = ['ignored']
        (self.root / 'ignored').write_text('first supported input')
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
        (self.root / 'ignored').write_text('second supported input')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
        control.require_correction(self.root, 'stale-evidence', 'explicit freshness verification requested')
        from unittest.mock import patch
        with patch.object(gate, 'run_target', wraps=gate.run_target) as runner:
            self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
            runner.assert_called_once_with(self.root, 'ok', 5)
        self.assertNotIn('reflection', self.goal)
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')

    def test_stale_only_failed_refresh_still_requires_verified_correction(self):
        (self.root / 'Makefile').write_text('ok:\n\t@test "$$(cat source)" = working\n')
        self.run_gate()
        (self.root / 'source').write_text('regression')
        failed = self.run_gate()
        self.assertTrue(any(item['id'] == 'correction' for item in failed))
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])
        (self.root / 'source').write_text('working')
        self.assertTrue(any(item['id'] == 'correction' for item in self.run_gate()))
        self.correction()
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))

    def test_stale_with_substantive_obligations_cannot_auto_resolve(self):
        for trigger in ('repetition', 'methodology', 'acceptance-revision', 'concurrent-change'):
            with self.subTest(trigger=trigger):
                control.write(self.root / '.agent/reflection-state.json', {})
                control.require_correction(self.root, 'stale-evidence', 'changed source identity')
                control.require_correction(self.root, trigger, 'independent substantive discrepancy')
                results = self.run_gate()
                self.assertTrue(any(item['id'] == 'correction' for item in results))
                self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])

    def test_stale_refresh_cannot_accept_changed_inputs_during_check(self):
        self.goal['inputs'] = ['ignored']
        (self.root / 'ignored').write_text('first')
        (self.root / 'Makefile').write_text('ok:\n\t@test -f source\n')
        self.run_gate()
        (self.root / 'source').write_text('valid new source')
        (self.root / 'mutate.py').write_text('from pathlib import Path\nwith Path("ignored").open("a") as stream: stream.write("changed")\n')
        (self.root / 'Makefile').write_text('ok:\n\t@' + sys.executable + ' mutate.py\n')
        results = self.run_gate()
        self.assertTrue(any(item['id'] == 'concurrent-change' for item in results))
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])
        self.assertFalse((self.root / '.agent/reflection-receipt.json').exists())

    def test_stale_refresh_requires_every_current_check_to_pass(self):
        self.run_gate()
        (self.root / 'source').write_text('new supported input')
        control.require_correction(self.root, 'stale-evidence', 'old receipt predates current input')
        current = control.snapshot(self.root, self.goal)
        results = [{'id': 'consumer', 'state': 'met'}, {'id': 'integration', 'state': 'unmet'}]
        self.assertFalse(control.refresh_stale_evidence(self.root, self.goal, results, current,
                         control.digest(control.contract(self.goal, self.root))))
        self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])
        self.assertFalse((self.root / '.agent/reflection-receipt.json').exists())

    def test_legacy_valid_success_requires_explicit_current_verification(self):
        control.write(self.root / '.agent/goal-status.json', {'met': True, 'goal': self.goal['goal']})
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'unverified')
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        receipt = control.read(self.root / '.agent/goal-status.json')
        self.assertEqual(receipt['schema'], 'goal-receipt/v2')
        self.assertEqual(receipt['snapshot'], control.snapshot(self.root, self.goal))
        self.assertNotIn('reflection', self.goal)

    def test_legacy_success_requires_real_fresh_verification(self):
        control.write(self.root / '.agent/goal-status.json', {'met': True, 'goal': self.goal['goal']})
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'unverified')
        self.assertIsNotNone(work_audit.goal_open(self.root))
        (self.root / 'Makefile').write_text('ok:\n\t@test -f missing-consumer\n')
        self.assertFalse(all(item['state'] == 'met' for item in self.run_gate()))
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        (self.root / 'missing-consumer').write_text('consumer restored')
        self.assertTrue(any(item['id'] == 'correction' for item in self.run_gate()))
        self.correction()
        self.assertTrue(all(item['state'] == 'met' for item in self.run_gate()))
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')

    def test_revision_preserves_previous_contract_and_requires_authority_pointer(self):
        self.run_gate()
        old = control.read(self.root / '.agent/goal-contract.json')['digest']
        self.goal['acceptance'][0]['check'] = 'new authorized outcome'
        self.goal['supersedes'] = {'digest': old, 'reason': 'the owner changed requirements', 'authority': 'assertion only'}
        with self.assertRaises(control.ContractError):
            control.pin_contract(self.root, self.goal)
        self.goal['supersedes']['authority'] = 'see requirements'
        control.pin_contract(self.root, self.goal)
        saved = control.read(self.root / '.agent/goal-contract.json')
        self.assertEqual(saved['history'][0]['digest'], old)

    def test_concurrent_source_change_rejects_success(self):
        self.goal['acceptance'][0]['run'] = 'change'
        self.assertTrue(any(r['id'] == 'concurrent-change' for r in self.run_gate()))

    def test_ignored_external_and_agent_dependencies_are_bound_outputs_are_not(self):
        (self.root / 'ignored').write_text('input')
        control.write(self.root / '.agent/requirement.json', {'contract': 1})
        self.goal['inputs'] = ['ignored', '.agent/requirement.json']
        self.run_gate()
        control.write(self.root / '.agent/hook-events.jsonl', {'event': 'later'})
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        (self.root / 'ignored').write_text('modified')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')

    def test_manual_agent_evidence_dependency_is_bound(self):
        evidence = self.root / '.agent/proof.txt'
        evidence.write_text('accepted')
        self.goal['acceptance'].append({'id': 'review', 'check': 'review accepted', 'status': 'pass', 'evidence': '.agent/proof.txt'})
        self.run_gate()
        evidence.write_text('withdrawn')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')

    def test_self_label_and_prose_cannot_resolve_failed_intervention(self):
        control.require_correction(self.root, 'repetition', 'same failed approach three times')
        self.goal['acceptance'][0]['run'] = 'bad'
        self.correction('bad')
        results = self.run_gate()
        self.assertTrue(any(r['id'] == 'correction' for r in results))
        self.assertEqual(control.read(self.root / '.agent/reflection-receipt.json')['status'], 'refuted')
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        (self.root / 'Makefile').write_text((self.root / 'Makefile').read_text().replace('@false', '@test -f source'))
        self.correction('bad')
        self.assertTrue(all(r['state'] == 'met' for r in self.run_gate()))
        history = control.read(self.root / '.agent/reflection-receipt.json')['history']
        self.assertEqual(history[0]['status'], 'refuted')
        control.require_correction(self.root, 'repetition', 'same failed approach three times')
        state = control.read(self.root / '.agent/reflection-state.json')
        self.assertFalse(state['resolved'])  # same words with changed observations reopen
        count = len(state['obligations'])
        control.require_correction(self.root, 'repetition', 'same failed approach three times')
        self.assertEqual(len(control.read(self.root / '.agent/reflection-state.json')['obligations']), count)

    def test_legacy_receipt_unverified_without_running_anything(self):
        control.write(self.root / '.agent/goal-status.json', {'goal': self.goal['goal'], 'met': True})
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'unverified')
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])

    def test_publication_cannot_bind_old_acceptance_to_new_source(self):
        results = gate.evaluate(self.goal, self.root, 5)
        self.assertTrue(all(r['state'] == 'met' for r in results))
        (self.root / 'source').write_text('changed after checks')
        gate.record_status(self.root, self.goal, results)
        receipt = control.read(self.root / '.agent/goal-status.json')
        self.assertFalse(receipt['met'])
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        self.assertTrue(any(r['id'] == 'publication-change' for r in results))
        self.assertTrue(any(r['id'] == 'correction' for r in self.run_gate()))
        self.correction()
        self.assertTrue(all(r['state'] == 'met' for r in self.run_gate()))

    def test_intervention_input_change_invalidates_earlier_acceptance(self):
        script = self.root / 'check.py'
        script.write_text("from pathlib import Path\np=Path('.agent/count')\n"
                          "n=int(p.read_text()) if p.exists() else 0\np.write_text(str(n+1))\n"
                          "if n: Path('source').write_text('changed during reflection')\n")
        (self.root / 'Makefile').write_text('ok:\n\t@' + sys.executable + ' check.py\n')
        control.require_correction(self.root, 'repetition', 'repeated check failed earlier')
        self.correction()
        results = self.run_gate()
        self.assertTrue(any(r['id'] == 'concurrent-change' for r in results))
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        self.assertEqual(control.read(self.root / '.agent/reflection-receipt.json')['status'], 'inconclusive')

    def test_unrelated_passing_target_cannot_resolve_obligation(self):
        control.require_correction(self.root, 'repetition', 'the repeated approach failed')
        self.correction('change')
        results = self.run_gate()
        self.assertTrue(any(r['id'] == 'correction' and 'current acceptance target' in r['why'] for r in results))
        self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])

    def test_resolution_reopens_after_observation_or_contract_change(self):
        control.require_correction(self.root, 'repetition', 'the repeated approach failed')
        self.correction()
        self.run_gate()
        self.assertTrue(control.read(self.root / '.agent/reflection-state.json')['resolved'])
        (self.root / 'source').write_text('new observation')
        self.goal.pop('reflection')
        self.assertIsNotNone(control.reflection_check(self.goal, self.root, 5, gate.run_target))
        self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])
        self.correction()
        self.run_gate()
        self.goal['goal'] = 'New authorized outcome'
        self.goal.pop('reflection')
        self.assertIsNotNone(control.reflection_check(self.goal, self.root, 5, gate.run_target))

    def test_revision_without_old_success_receipt_still_needs_impact_check(self):
        old = control.pin_contract(self.root, self.goal)
        self.goal['acceptance'][0]['check'] = 'new acceptance authorized'
        self.goal['supersedes'] = {'digest': old, 'reason': 'the owner approved revision', 'authority': 'requirements'}
        self.save()
        control.pin_contract(self.root, self.goal)
        self.assertFalse((self.root / '.agent/goal-status.json').exists())
        state = control.read(self.root / '.agent/reflection-state.json')
        self.assertTrue(any(o['trigger'] == 'acceptance-revision' for o in state.get('obligations', [])))
        self.assertTrue(any(r['id'] == 'correction' for r in self.run_gate()))

    def test_missing_declared_input_at_publication_is_unverified(self):
        self.goal['inputs'] = ['source']
        self.save()
        results = gate.evaluate(self.goal, self.root, 5)
        (self.root / 'source').unlink()
        gate.record_status(self.root, self.goal, results)
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        self.assertTrue(any(r['id'] == 'publication-change' for r in results))

    def test_new_obligation_invalidates_prior_success_without_rerunning(self):
        self.run_gate()
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        control.require_correction(self.root, 'repetition', 'new repeated failure observed')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'unverified')
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])

    def test_trigger_records_obligation_without_running_acceptance(self):
        (self.root / 'Makefile').write_text('ok:\n\t@touch acceptance-ran\n')
        for trigger in ('stale-evidence', 'repetition', 'methodology'):
            proc = subprocess.run([sys.executable, gate.__file__, '--root', str(self.root),
                                   '--trigger', trigger], capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), {'trigger': trigger, 'recorded': True})
            self.assertFalse((self.root / 'acceptance-ran').exists())
            self.assertFalse((self.root / '.agent/goal-status.json').exists())
        state = control.read(self.root / '.agent/reflection-state.json')
        self.assertEqual({o['trigger'] for o in state['obligations']},
                         {'stale-evidence', 'repetition', 'methodology'})

    def test_disappearing_declared_input_during_acceptance_is_unmet_not_crash(self):
        self.goal['inputs'] = ['source']
        self.save()
        (self.root / 'Makefile').write_text('ok:\n\t@rm source\n')
        proc = subprocess.run([sys.executable, gate.__file__, '--root', str(self.root)],
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertNotIn('Traceback', proc.stderr)
        self.assertIn('inputs-unavailable', proc.stdout)
        receipt = control.read(self.root / '.agent/goal-status.json')
        self.assertFalse(receipt['met'])
        self.assertTrue(any(r['id'] == 'inputs-unavailable' for r in receipt['results']))

    def test_changed_ignored_corrective_evidence_reopens_supported_resolution(self):
        evidence = self.root / '.agent/failure.txt'
        evidence.write_text('original consumer failure')
        self.correction()
        self.goal['reflection']['interventions'][0]['evidence'] = '.agent/failure.txt'
        self.save()
        control.require_correction(self.root, 'repetition', 'the consumer failure repeated')
        self.run_gate()
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        evidence.write_text('new contradictory consumer failure')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        self.assertIsNotNone(control.reflection_check(self.goal, self.root, 5,
                              lambda root, target, timeout: ('unmet', 'new evidence requires repair')))
        self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])

    def test_intervention_specification_is_bound_but_status_labels_are_not(self):
        self.correction()
        self.save()
        control.require_correction(self.root, 'repetition', 'the consumer failure repeated')
        self.run_gate()
        original = copy.deepcopy(self.goal)
        for field, changed in [('hypothesis', 'a different proposed mechanism'),
                               ('expected_effect', 'a different predicted consumer effect'), ('run', 'bad')]:
            with self.subTest(field=field):
                revised = copy.deepcopy(original)
                revised['reflection']['interventions'][0][field] = changed
                self.assertEqual(control.receipt_state(self.root, revised)[0], 'stale')
                from unittest.mock import Mock
                runner = Mock(return_value=('unmet', 'changed prediction has not passed'))
                self.assertIsNotNone(control.reflection_check(revised, self.root, 5, runner))
                self.assertFalse(control.read(self.root / '.agent/reflection-state.json')['resolved'])
                if field != 'run':
                    runner.assert_called_once()
        self.goal['reflection']['interventions'][0]['status'] = 'refuted'
        # A self-label cannot revoke or manufacture the tool's observed result.
        self.assertEqual(control.snapshot(self.root, self.goal), control.snapshot(self.root, original))

    def paired_evidence(self):
        from tools.tests import test_outcome_control as richer
        task = richer.fixture(self.root)
        self.goal['acceptance'][0]['check'] = 'consumer reads exact observable result'
        (self.root / 'Makefile').write_text('ok:\n\t@' + sys.executable +
            ' -c \'from pathlib import Path; assert Path("src/result.txt").read_text() == "Observable result\\n"\'\n')
        richer.prove(self.root, task)
        richer.prove(self.root, task, 'verified')
        task['status'] = 'done'
        self.run_gate()
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
        self.assertEqual(richer.oc.validate_control(task, self.root, richer.NOW), [])
        return richer, task

    def test_shared_source_regression_invalidates_both_control_routes(self):
        richer, task = self.paired_evidence()
        (self.root / 'src/result.txt').write_text('consumer source regressed')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        self.assertIn('altered file', str(richer.oc.validate_control(task, self.root, richer.NOW)))

    def test_shared_acceptance_substitution_invalidates_both_control_routes(self):
        richer, task = self.paired_evidence()
        self.goal['acceptance'][0]['check'] = 'substituted weaker acceptance'
        task['acceptance'] = ['Substituted weaker acceptance']
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        with self.assertRaises(control.ContractError):
            control.pin_contract(self.root, self.goal)
        self.assertIn('stale assignment authority', str(richer.oc.validate_control(task, self.root, richer.NOW)))

    def test_shared_unchanged_evidence_reuse_needs_no_native_execution(self):
        from unittest.mock import patch
        richer, task = self.paired_evidence()
        ordinary_before = (self.root / '.agent/goal-status.json').read_bytes()
        richer_before = (self.root / 'proof/verified.json').read_bytes()
        with patch.object(gate, 'run_target', side_effect=AssertionError('unexpected native execution')):
            for _ in range(2):
                self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'verified')
                self.assertEqual(richer.oc.validate_control(task, self.root, richer.NOW), [])
        self.assertEqual((self.root / '.agent/goal-status.json').read_bytes(), ordinary_before)
        self.assertEqual((self.root / 'proof/verified.json').read_bytes(), richer_before)

    def test_removed_unmet_goal_survives_new_session_and_audit_without_execution(self):
        self.goal['acceptance'][0]['run'] = 'bad'
        self.run_gate()
        (self.root / '.agent/goal.json').unlink()
        before = (self.root / '.agent/goal-status.json').read_bytes()
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])
        self.assertEqual((self.root / '.agent/goal-status.json').read_bytes(), before)
        command = [sys.executable, gate.__file__, '--root', str(self.root)]
        cli = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(cli.returncode, 2, cli.stdout + cli.stderr)
        self.assertIn('retained goal unverified', cli.stdout)
        event = json.dumps({'session_id': 'new-session-after-deletion'})
        for _ in range(gate.MAX_BLOCKS):
            proc = subprocess.run(command + ['--hook'], input=event, capture_output=True, text=True, check=False)
            self.assertEqual(json.loads(proc.stdout)['decision'], 'block')
        final = subprocess.run(command + ['--hook'], input=event, capture_output=True, text=True, check=False)
        self.assertIn('NOT verified', json.loads(final.stdout)['systemMessage'])
        self.assertEqual((self.root / '.agent/goal-status.json').read_bytes(), before)
        self.assertNotIn('status', control.retained_goal(self.root)['acceptance'][0])

    def test_removed_completed_goal_requires_current_evidence(self):
        self.run_gate()
        (self.root / '.agent/goal.json').unlink()
        command = [sys.executable, gate.__file__, '--root', str(self.root)]
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIsNone(work_audit.goal_open(self.root))
        (self.root / 'source').write_text('changed after completion')
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])

    def test_no_goal_and_no_retained_contract_remains_unaffected(self):
        (self.root / '.agent/goal.json').unlink()
        proc = subprocess.run([sys.executable, gate.__file__, '--root', str(self.root)],
                              capture_output=True, text=True, check=False)
        self.assertEqual((proc.returncode, proc.stdout), (0, ''))
        self.assertIsNone(work_audit.goal_open(self.root))
