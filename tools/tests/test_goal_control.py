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
        (self.root / 'source').write_text('broken')
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'stale')
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])
        self.assertTrue(any(r['id'] == 'correction' for r in self.run_gate()))
        self.correction()
        self.assertTrue(all(r['state'] == 'met' for r in self.run_gate()))

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
