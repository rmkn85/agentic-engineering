"""Independent positive and adversarial outcome-control scenarios."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('outcome_control', TOOLS / 'outcome_control.py')
oc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oc)
NOW = datetime(2026, 1, 2, tzinfo=timezone.utc)


def artifact(root, path, content):
    raw = content if isinstance(content, bytes) else json.dumps(content).encode()
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest()}


def fixture(root):
    source = artifact(root, 'src/result.txt', b'Observable result\n')
    task = {'schema': 'axioms-task/v1', 'id': 'RESULT-1', 'title': 'Deliver result', 'outcome': 'Consumer reads result',
            'status': 'in-progress', 'depends': [], 'acceptance': ['Exact result visible'], 'evidence': [],
            'current': {'summary': 'Candidate ready', 'nextAction': 'Verify consumer', 'blockers': []}}
    rules = {claim: {'applicable': claim in ('implemented', 'verified'), 'reason': 'Local file consumer' if claim in ('implemented', 'verified') else 'No separate boundary in this local example',
                     'scenario': 'local-result/' + claim, 'prerequisites': ['implemented'] if claim == 'verified' else [],
                     'classes': ['mechanical'], 'producers': ['native-check'], 'reviewers': ['owner'],
                     'loadedRequired': claim == 'verified'} for claim in oc.CLAIMS}
    task['control'] = {'schema': oc.SCHEMA, 'authorization': {'revision': '1', 'owner': 'owner', 'nonGoals': ['Publishing'],
                       'invariants': ['Preserve source'], 'decisionRights': list(oc.EVENTS), 'editScope': ['src'],
                       'deniedScope': ['src/protected'], 'requiredCapabilities': [], 'claims': rules},
                       'assignment': {}, 'source': [source], 'conditions': {'consumer': 'local-reader/v1'},
                       'claims': {c: {'state': 'open' if rules[c]['applicable'] else 'not-applicable', 'evidence': []} for c in oc.CLAIMS},
                       'decisions': [], 'wip': {'limits': {'changes': 2}, 'items': {k: [] for k in oc.WIP}, 'exceptions': [], 'history': [], 'overheadSeconds': None}}
    reassign(task)
    return task


def reassign(task):
    control = task['control']
    control['assignment'] = {'authorityDigest': oc.authority_digest(task), 'sourceDigest': oc.source_digest(control['source']),
                             'conditionsDigest': oc.digest(control['conditions']), 'actor': 'builder', 'rights': list(oc.EVENTS)}


def prove(root, task, claim='implemented', **overrides):
    source = oc.source_digest(task['control']['source'])
    proof = {'schema': 'outcome-evidence/v1', 'claim': claim, 'scenario': task['control']['authorization']['claims'][claim]['scenario'], 'authorityDigest': oc.authority_digest(task), 'sourceDigest': source,
             'conditions': task['control']['conditions'], 'class': 'mechanical', 'producer': 'native-check', 'reviewer': 'owner',
             'observedAt': '2026-01-01T12:00:00Z', 'status': 'passed',
             'native': {'completed': True, 'pass': True, 'errors': [], 'candidateDigest': source, 'loadedDigest': source}}
    proof.update(overrides)
    ref = artifact(root, 'proof/' + claim + '.json', proof)
    task['control']['claims'][claim] = {'state': 'satisfied', 'evidence': [ref]}
    return proof


class OutcomeControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.task = fixture(self.root)

    def valid(self):
        return oc.validate_control(self.task, self.root, NOW)

    def request(self, purpose='admission', paths=None):
        return {'authorityDigest': oc.authority_digest(self.task), 'actor': 'builder', 'purpose': purpose,
                'paths': paths or ['src/result.txt'], 'capabilities': [], 'wipAfter': copy.deepcopy(self.task['control']['wip']['items'])}

    def gate(self, event='pre-write', **kw):
        return oc.check_gate(self.task, self.root, event, self.request(**kw), NOW)

    def write_task(self):
        artifact(self.root, 'work/tasks/RESULT-1.json', self.task)

    def test_healthy_independent_claims(self):
        self.assertEqual(self.valid(), [])
        prove(self.root, self.task)
        self.assertEqual(self.valid(), [])
        self.assertTrue(self.gate('pre-completion'))
        prove(self.root, self.task, 'verified')
        self.task['status'] = 'done'
        self.assertEqual(self.valid(), [])
        self.assertEqual(self.gate('pre-completion'), [])

    def test_direct_done_bypass_and_native_reader(self):
        self.task['status'] = 'done'
        self.write_task()
        artifact(self.root, 'work/frontier.json', {'schema': 'axioms-frontier/v1', 'repository': 'sample/result',
                 'objective': 'Deliver result', 'mode': 'product', 'product': ['RESULT-1'], 'maintenance': [], 'parallel': []})
        result = subprocess.run([sys.executable, str(TOOLS / 'project_work.py'), '--root', str(self.root), 'validate'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('done requires every applicable claim', result.stdout)

    def test_missing_companion_fails_closed_but_legacy_still_works(self):
        reader = self.base / 'reader'
        reader.mkdir()
        (reader / 'project_work.py').write_bytes((TOOLS / 'project_work.py').read_bytes())
        self.write_task()
        artifact(self.root, 'work/frontier.json', {'schema': 'axioms-frontier/v1', 'repository': 'sample/result',
                 'objective': 'Deliver result', 'mode': 'product', 'product': ['RESULT-1'], 'maintenance': [], 'parallel': []})
        command = [sys.executable, str(reader / 'project_work.py'), '--root', str(self.root), 'validate']
        self.assertIn('requires outcome_control.py', subprocess.run(command, capture_output=True, text=True).stdout)
        (reader / 'outcome_control.py').write_text('invalid Python source !')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('validator unavailable', result.stdout)
        self.assertNotIn('Traceback', result.stderr)
        del self.task['control']
        self.write_task()
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)

    def test_native_policy_prevents_deleted_control_and_rejects_unknown_malformed(self):
        self.write_task()
        frontier = {'schema': 'axioms-frontier/v1', 'repository': 'sample/result',
                    'objective': 'Deliver result', 'mode': 'product', 'product': ['RESULT-1'], 'maintenance': [], 'parallel': [],
                    'controlPolicy': {'schema': 'outcome-policy/v1', 'requiredTasks': ['RESULT-1']}}
        def validate():
            artifact(self.root, 'work/frontier.json', frontier)
            return subprocess.run([sys.executable, str(TOOLS / 'project_work.py'), '--root', str(self.root), 'validate'], capture_output=True, text=True)
        self.assertEqual(validate().returncode, 0)
        del self.task['control']
        self.task['status'] = 'done'
        self.write_task()
        self.assertIn('required task lacks control', validate().stdout)
        frontier['controlPolicy']['requiredTasks'] = ['MISSING']
        self.assertIn('required task unavailable', validate().stdout)
        for policy in (None, {}, {'schema': 'outcome-policy/v1', 'requiredTasks': ['RESULT-1', 'RESULT-1']},
                       {'schema': 'outcome-policy/v1', 'requiredTasks': [None]}):
            frontier['controlPolicy'] = policy
            result = validate()
            self.assertEqual(result.returncode, 1)
            self.assertNotIn('Traceback', result.stderr)

    def test_stale_goal_same_revision_and_changed_acceptance(self):
        for field, value in [('outcome', 'Another result'), ('acceptance', ['Another test'])]:
            original = copy.deepcopy(self.task)
            self.task[field] = value
            self.assertIn('stale assignment authority', str(self.valid()))
            self.task = original

    def test_source_condition_assignment_and_evidence_binding(self):
        prove(self.root, self.task)
        self.task['control']['conditions']['consumer'] = 'another-reader'
        self.assertIn('assignment conditions', str(self.valid()))
        reassign(self.task)
        self.assertIn('condition mismatch', str(self.valid()))
        self.task['control']['source'] = [artifact(self.root, 'src/other.txt', b'Other source')]
        reassign(self.task)
        self.assertIn('wrong evidence source', str(self.valid()))

    def test_condition_identity_distinguishes_json_booleans_numbers_and_nested_values(self):
        for before, after in (({'enabled': False}, {'enabled': 0}),
                              ({'enabled': True}, {'enabled': 1}),
                              ({'nested': [{'enabled': False}]}, {'nested': [{'enabled': 0}]}),
                              ({'nested': {'enabled': True}}, {'nested': {'enabled': 1}})):
            with self.subTest(before=before, after=after):
                self.task = fixture(self.root)
                self.task['control']['conditions'] = before
                reassign(self.task)
                prove(self.root, self.task)
                prove(self.root, self.task, 'verified')
                self.task['status'] = 'done'
                self.assertEqual(self.valid(), [])
                self.task['control']['conditions'] = after
                reassign(self.task)  # Fresh assignment cannot refresh old proof.
                self.assertIn('evidence condition mismatch', str(self.valid()))
                prove(self.root, self.task)
                prove(self.root, self.task, 'verified')
                self.assertEqual(self.valid(), [])

    def test_reconcile_json_identity_preserves_extension_and_history_types(self):
        self.task['retainedExtension'] = {'nested': [False]}
        self.task['history'] = [{'enabled': False}]
        self.task['control']['wip']['history'] = [{'enabled': False}]
        self.write_task()
        current_path = self.root / 'work/tasks/RESULT-1.json'
        original = current_path.read_bytes()
        expected = hashlib.sha256(original).hexdigest()
        proposal = self.base / 'proposal.json'
        variants = []
        proposed = copy.deepcopy(self.task)
        proposed['retainedExtension']['nested'] = [0]
        variants.append(proposed)
        proposed = copy.deepcopy(self.task)
        proposed['history'] = [{'enabled': 0}]
        variants.append(proposed)
        proposed = copy.deepcopy(self.task)
        proposed['control']['wip']['history'] = [{'enabled': 0}]
        variants.append(proposed)
        for proposed in variants:
            proposal.write_text(json.dumps(proposed))
            with self.assertRaises(ValueError):
                oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)
            self.assertEqual(current_path.read_bytes(), original)

    def test_loaded_source_false_zero_exit_class_and_freshness(self):
        prove(self.root, self.task)
        good = prove(self.root, self.task, 'verified')
        mutations = [({'native': dict(good['native'], loadedDigest='0' * 64)}, 'loaded'),
                     ({'native': dict(good['native'], completed=False)}, 'completion'),
                     ({'native': dict(good['native'], errors=['semantic failure'])}, 'substantive'),
                     ({'class': 'human'}, 'class'), ({'status': 'unknown'}, 'not passed'),
                     ({'expiresAt': '2026-01-01T13:00:00Z'}, 'expired'),
                     ({'observedAt': '2026-01-01'}, 'timezone')]
        for mutation, expected in mutations:
            with self.subTest(expected=expected):
                prove(self.root, self.task, 'verified', **mutation)
                self.assertIn(expected, str(self.valid()))
        self.task['control']['authorization']['claims']['verified']['maxAgeSeconds'] = 10
        reassign(self.task)
        prove(self.root, self.task)
        prove(self.root, self.task, 'verified')
        self.assertIn('stale evidence age', str(self.valid()))

    def test_altered_bytes_symlinks_and_path_escape(self):
        prove(self.root, self.task)
        (self.root / 'proof/implemented.json').write_text('{}')
        self.assertIn('altered file', str(self.valid()))
        for path in ['../elsewhere', '/tmp/source', './src/result.txt', 'src/../result.txt']:
            self.task['control']['source'][0]['path'] = path
            self.assertTrue(self.valid())
        self.task = fixture(self.root)
        (self.root / 'src/result.txt').unlink()
        (self.root / 'src/result.txt').symlink_to(self.base / 'other')
        self.assertIn('symlink', str(self.valid()))

    def test_edit_denial_beats_probe_success(self):
        self.assertIn('explicit edit denial', str(self.gate(paths=['src/protected/result.txt'])))
        self.assertIn('outside authorized', str(self.gate(paths=['tools/new.py'])))
        request = self.request()
        request['capabilities'] = [{'name': 'write', 'status': 'available', 'evidence': self.capability()}]
        request['paths'] = ['src/protected/result.txt']
        self.assertIn('explicit edit denial', str(oc.check_gate(self.task, self.root, 'pre-write', request, NOW)))

    def capability(self, **overrides):
        c = self.task['control']
        receipt = {'schema': 'runtime-control/v1', 'type': 'capability', 'scope': str(self.root / 'src'),
                   'authorization': 'allowed', 'authorizationRevision': c['authorization']['revision'],
                   'observedAt': '2026-01-01T12:00:00Z', 'probe': 'passed', 'effective': 'observed-writable',
                   'authorityDigest': oc.authority_digest(self.task), 'conditionsDigest': oc.digest(c['conditions']), 'producer': 'runtime-probe'}
        receipt.update(overrides)
        return artifact(self.root, 'proof/capability.json', receipt)

    def test_capability_runtime_receipt_exact_binding(self):
        self.task['control']['authorization']['requiredCapabilities'] = [{'name': 'consumer', 'scope': 'src', 'producer': 'runtime-probe'}]
        reassign(self.task)
        request = self.request()
        request['capabilities'] = [{'name': 'consumer', 'status': 'available', 'evidence': self.capability()}]
        self.assertEqual(oc.check_gate(self.task, self.root, 'pre-write', request, NOW), [])
        for change in ({'authorityDigest': '0' * 64}, {'authorization': 'denied'}, {'probe': 'denied'}, {'effective': 'unknown'}, {'scope': str(self.root)}, {'producer': 'another-probe'}):
            request['capabilities'][0]['evidence'] = self.capability(**change)
            self.assertTrue(oc.check_gate(self.task, self.root, 'pre-write', request, NOW))

    def test_claim_scenario_reuse_cannot_upgrade_acceptance(self):
        auth = self.task['control']['authorization']
        auth['claims']['accepted']['applicable'] = True
        reassign(self.task)
        prove(self.root, self.task)
        prove(self.root, self.task, 'verified')
        self.task['control']['claims']['accepted'] = copy.deepcopy(self.task['control']['claims']['verified'])
        self.assertIn('claim/scenario mismatch', str(self.valid()))
        prove(self.root, self.task, 'accepted', scenario='another-scenario')
        self.assertIn('claim/scenario mismatch', str(self.valid()))

    def test_policy_limits_and_nonfinite_values(self):
        self.task['control']['wip']['limits']['changes'] = 3
        self.assertIn('stale assignment', str(self.valid()))
        reassign(self.task)
        self.task['control']['wip']['overheadSeconds'] = float('inf')
        self.assertTrue(self.valid())
        self.task['control']['wip']['overheadSeconds'] = None
        self.task['control']['authorization']['claims']['verified']['maxAgeSeconds'] = float('nan')
        self.assertTrue(self.valid())

    def test_required_capability_is_observed_not_assumed(self):
        self.task['control']['authorization']['requiredCapabilities'] = [{'name': 'consumer', 'scope': 'src', 'producer': 'runtime-probe'}]
        reassign(self.task)
        self.assertIn('missing', str(self.gate()))
        request = self.request()
        request['capabilities'] = [{'name': 'consumer', 'status': 'denied', 'evidence': {}}]
        self.assertIn('denied or unknown', str(oc.check_gate(self.task, self.root, 'pre-write', request, NOW)))

    def test_wip_limits_block_admission_allow_reduction_recovery(self):
        self.task['control']['wip']['items']['changes'] = ['change-1', 'change-2', 'change-3']
        self.assertIn('WIP admission', str(self.gate()))
        self.assertEqual(self.gate(purpose='reduction'), [])
        self.assertEqual(self.gate('resume', purpose='recovery'), [])
        self.task['control']['wip']['exceptions'] = [{'owner': 'owner', 'category': 'changes', 'limit': 4,
                'expiresAt': '2026-01-03T00:00:00Z', 'reason': 'Finish current integration'}]
        reassign(self.task)
        self.assertEqual(self.gate(), [])
        self.task['control']['wip']['exceptions'][0]['expiresAt'] = '2026-01-01T00:00:00Z'
        reassign(self.task)
        self.assertTrue(self.gate())

    def test_false_reduction_and_oversized_admission_rejected(self):
        request = self.request(purpose='reduction')
        request['wipAfter']['changes'] = ['new-change']
        self.assertIn('cannot admit WIP', str(oc.check_gate(self.task, self.root, 'pre-write', request, NOW)))
        request['purpose'] = 'admission'
        request['wipAfter']['changes'] = ['one', 'two', 'three']
        self.assertIn('WIP admission', str(oc.check_gate(self.task, self.root, 'pre-write', request, NOW)))

    def test_expected_observed_feedback_and_no_repeated_unreconciled_batch(self):
        decision = {'id': 'D1', 'owner': 'owner', 'authorityDigest': oc.authority_digest(self.task), 'sourceDigest': oc.source_digest(self.task['control']['source']), 'conditionsDigest': oc.digest(self.task['control']['conditions']), 'trigger': 'result', 'constraint': 'Consumer unproved', 'action': 'Read candidate',
                    'expected': 'Exact result observed', 'reconsider': 'Unexpected bytes', 'evidence': [], 'effect': None, 'state': 'continuation'}
        self.task['control']['decisions'] = [decision]
        self.assertEqual(self.valid(), [])
        self.assertIn('pending outcome', str(self.gate()))
        self.assertEqual(self.gate(purpose='reduction'), [])
        self.task['control']['decisions'].append(dict(decision, id='D2'))
        self.assertIn('reconcile pending', str(self.valid()))
        self.task['control']['decisions'].pop()
        decision['effect'] = {'decisionId': 'D1', 'observed': 'Read failed', 'matchesExpected': False, 'followUp': 'Investigate reader', 'evidence': [artifact(self.root, 'proof/failure.json', {'observation': 'Reader failed'})]}
        self.assertEqual(self.gate(), [])

    def test_feedback_identity_result_binding_and_stale_history(self):
        c = self.task['control']
        decision = {'id': 'D1', 'owner': 'owner', 'authorityDigest': oc.authority_digest(self.task),
                    'sourceDigest': oc.source_digest(c['source']), 'conditionsDigest': oc.digest(c['conditions']),
                    'trigger': 'result', 'constraint': 'Unknown reader', 'action': 'Read candidate', 'expected': 'Exact bytes',
                    'reconsider': 'Reader fails', 'evidence': [], 'state': 'continuation',
                    'effect': {'decisionId': 'D1', 'observed': 'Reader failed', 'matchesExpected': False,
                               'followUp': 'Investigate reader', 'evidence': [artifact(self.root, 'proof/failure.json', {'observation': 'Reader failed'})]}}
        c['decisions'] = [decision]
        self.assertEqual(self.valid(), [])
        decision['effect']['decisionId'] = 'another-decision'
        self.assertIn('effect decision mismatch', str(self.valid()))
        decision['effect']['decisionId'] = 'D1'
        evidence = decision['effect']['evidence']
        decision['effect']['evidence'] = []
        self.assertIn('observed result evidence', str(self.valid()))
        decision['effect']['evidence'] = evidence
        self.task['outcome'] = 'Changed goal'
        reassign(self.task)
        self.assertIn('latest decision has stale', str(self.valid()))
        c['decisions'].append(dict(decision, id='D2', authorityDigest=oc.authority_digest(self.task),
                                  effect=dict(decision['effect'], decisionId='D2')))
        self.assertEqual(self.valid(), [])  # Retain old-authority decision as history.

    def test_checkpoint_survives_source_loss_restore_no_overwrite_and_stale_resume(self):
        self.write_task()
        checkpoint = self.base / 'durable'
        identity = oc.checkpoint(self.root, 'work/tasks/RESULT-1.json', checkpoint)
        (self.root / 'src/result.txt').unlink()
        destination = self.base / 'recovery'
        self.assertEqual(oc.resume(self.root, 'work/tasks/RESULT-1.json', checkpoint, destination), identity)
        self.assertEqual((destination / 'restored/src/result.txt').read_bytes(), b'Observable result\n')
        with self.assertRaisesRegex(ValueError, 'no overwrite'):
            oc.resume(self.root, 'work/tasks/RESULT-1.json', checkpoint, destination)
        self.task['outcome'] = 'Changed but same revision'
        self.write_task()
        with self.assertRaisesRegex(ValueError, 'stale resume'):
            oc.resume(self.root, 'work/tasks/RESULT-1.json', checkpoint, self.base / 'other')

    def test_checkpoint_detects_concurrent_change_and_unexpected_restore_file(self):
        self.write_task()
        real_read = oc.read_bytes
        reads = {'source': 0}
        def changing_read(path):
            if path == self.root / 'src/result.txt':
                reads['source'] += 1
                if reads['source'] == 3:
                    path.write_bytes(b'Concurrent modification')
            return real_read(path)
        with patch.object(oc, 'read_bytes', side_effect=changing_read):
            with self.assertRaisesRegex(ValueError, 'changed during checkpoint'):
                oc.checkpoint(self.root, 'work/tasks/RESULT-1.json', self.base / 'changed')
        self.assertFalse((self.base / 'changed').exists())
        (self.root / 'src/result.txt').write_bytes(b'Observable result\n')
        checkpoint = self.base / 'durable'
        oc.checkpoint(self.root, 'work/tasks/RESULT-1.json', checkpoint)
        extra = artifact(checkpoint / 'snapshot/files', 'unrequested.txt', b'Injected')
        manifest = oc.read_json(checkpoint / 'snapshot/manifest.json')
        manifest['files'].append(extra)
        (checkpoint / 'snapshot/manifest.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'unexpected files'):
            oc.resume(self.root, 'work/tasks/RESULT-1.json', checkpoint, self.base / 'recovery')

    def test_interrupted_or_changed_checkpoint_is_never_published(self):
        self.write_task()
        with patch.object(oc.os, 'replace', side_effect=OSError('interrupted')):
            with self.assertRaisesRegex(OSError, 'interrupted'):
                oc.checkpoint(self.root, 'work/tasks/RESULT-1.json', self.base / 'broken')
        self.assertFalse((self.base / 'broken').exists())
        checkpoint = self.base / 'durable'
        oc.checkpoint(self.root, 'work/tasks/RESULT-1.json', checkpoint)
        (checkpoint / 'snapshot/files/src/result.txt').write_text('Changed')
        with self.assertRaisesRegex(ValueError, 'altered'):
            oc.resume(self.root, 'work/tasks/RESULT-1.json', checkpoint, self.base / 'recovery')
        with self.assertRaisesRegex(ValueError, 'exists'):
            oc.checkpoint(self.root, 'work/tasks/RESULT-1.json', checkpoint)

    def test_reconcile_atomic_source_refresh_and_cas(self):
        self.task['privateExtension'] = {'retained': True}
        self.task['history'] = ['Prior decision']
        self.write_task()
        current_path = self.root / 'work/tasks/RESULT-1.json'
        expected = hashlib.sha256(current_path.read_bytes()).hexdigest()
        proposed = copy.deepcopy(self.task)
        proposed['control']['source'] = [artifact(self.root, 'src/result.txt', b'New candidate')]
        reassign(proposed)
        proposal = self.base / 'proposal.json'
        proposal.write_text(json.dumps(proposed))
        self.assertTrue(self.valid())  # Stale source must not deadlock reconciliation.
        result = oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)
        self.assertEqual(result, hashlib.sha256(current_path.read_bytes()).hexdigest())
        self.assertEqual(json.loads(current_path.read_bytes())['privateExtension'], {'retained': True})
        with self.assertRaisesRegex(ValueError, 'stale expected'):
            oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)
        lock = current_path.with_name(current_path.name + '.outcome.lock')
        lock.write_text('Another writer')
        with self.assertRaises(FileExistsError):
            oc.reconcile(self.root, 'work/tasks/RESULT-1.json', result, proposal)
        self.assertEqual(lock.read_text(), 'Another writer')

    def test_unexpected_source_corruption_reconciles_truth_before_gated_repair(self):
        prove(self.root, self.task)
        prove(self.root, self.task, 'verified')
        self.task['status'] = 'done'
        self.write_task()
        current_path = self.root / 'work/tasks/RESULT-1.json'
        expected = hashlib.sha256(current_path.read_bytes()).hexdigest()
        corrupted = artifact(self.root, 'src/result.txt', b'Unexpected corruption')
        self.assertTrue(self.gate(purpose='recovery'))  # Never bypass stale evidence.
        proposed = copy.deepcopy(self.task)
        proposed['status'] = 'in-progress'
        proposed['control']['source'] = [corrupted]
        for claim in ('implemented', 'verified'):
            proposed['control']['claims'][claim]['state'] = 'open'
        reassign(proposed)
        proposal = self.base / 'recovery-proposal.json'
        proposal.write_text(json.dumps(proposed))
        reconciled = oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)
        self.task = proposed
        self.assertEqual(self.valid(), [])
        self.assertEqual(self.gate(purpose='recovery'), [])
        # The gate precedes actual repair, then CAS records the now-current source.
        repaired = copy.deepcopy(proposed)
        repaired['control']['source'] = [artifact(self.root, 'src/result.txt', b'Observable result\n')]
        reassign(repaired)
        proposal.write_text(json.dumps(repaired))
        oc.reconcile(self.root, 'work/tasks/RESULT-1.json', reconciled, proposal)
        self.task = repaired
        self.assertEqual(self.valid(), [])
        self.assertTrue(self.gate('pre-completion', purpose='recovery'))
        prove(self.root, self.task)
        prove(self.root, self.task, 'verified')
        self.assertEqual(self.gate('pre-completion', purpose='recovery'), [])

    def test_reconcile_rejects_authority_done_lost_extensions_and_history(self):
        self.task['retainedExtension'] = 'Keep'
        self.task['history'] = ['Prior decision']
        self.task['control']['wip']['history'] = ['Original WIP']
        self.write_task()
        current_path = self.root / 'work/tasks/RESULT-1.json'
        original = current_path.read_bytes()
        expected = hashlib.sha256(original).hexdigest()
        proposal = self.base / 'proposal.json'
        variants = []
        for key, value in [('outcome', 'Changed'), ('status', 'done'), ('id', 'ANOTHER'), ('history', [])]:
            proposed = copy.deepcopy(self.task)
            proposed[key] = value
            variants.append(proposed)
        proposed = copy.deepcopy(self.task)
        del proposed['retainedExtension']
        variants.append(proposed)
        proposed = copy.deepcopy(self.task)
        proposed['control']['wip']['limits']['changes'] = 100
        variants.append(proposed)
        proposed = copy.deepcopy(self.task)
        proposed['control']['wip']['history'] = []
        variants.append(proposed)
        for proposed in variants:
            proposal.write_text(json.dumps(proposed))
            with self.assertRaises(ValueError):
                oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)
            self.assertEqual(current_path.read_bytes(), original)
        proposal.write_text(json.dumps(self.task))
        with patch.object(oc.os, 'replace', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)
        self.assertEqual(current_path.read_bytes(), original)
        self.assertFalse(current_path.with_name(current_path.name + '.outcome.lock').exists())
        saved = self.base / 'saved-task.json'
        current_path.rename(saved)
        current_path.symlink_to(saved)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            oc.reconcile(self.root, 'work/tasks/RESULT-1.json', expected, proposal)

    def test_malformed_inputs_clean_nonzero(self):
        self.task['control']['source'] = None
        self.write_task()
        result = subprocess.run([sys.executable, str(TOOLS / 'outcome_control.py'), '--root', str(self.root), '--task', 'work/tasks/RESULT-1.json', 'validate'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
