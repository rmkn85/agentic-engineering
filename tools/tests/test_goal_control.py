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
        self.correction('bad')
        results = self.run_gate()
        self.assertTrue(any(r['id'] == 'correction' for r in results))
        self.assertEqual(control.read(self.root / '.agent/reflection-receipt.json')['status'], 'refuted')
        self.assertFalse(control.read(self.root / '.agent/goal-status.json')['met'])
        self.correction()
        self.assertTrue(all(r['state'] == 'met' for r in self.run_gate()))
        control.require_correction(self.root, 'repetition', 'same failed approach three times')
        self.assertTrue(control.read(self.root / '.agent/reflection-state.json')['resolved'])

    def test_legacy_receipt_unverified_without_running_anything(self):
        control.write(self.root / '.agent/goal-status.json', {'goal': self.goal['goal'], 'met': True})
        self.assertEqual(control.receipt_state(self.root, self.goal)[0], 'unverified')
        self.assertEqual(work_audit.goal_open(self.root), self.goal['goal'])
