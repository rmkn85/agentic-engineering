import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('control_runtime', Path(__file__).parents[1] / 'control_runtime.py')
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class ObservationTests(unittest.TestCase):
    def test_fixed_baseline_cumulative_jitter_and_counts(self):
        spec = {'fields': ['load', 'status'], 'jitter': {'load': 1}}
        state, first = runtime.observe(spec, {'load': 10, 'status': 'run', 'timestamp': 1})
        state, quiet = runtime.observe(spec, {'status': 'run', 'load': 10.8, 'timestamp': 2}, state)
        self.assertFalse(quiet['wake'])
        state, drift = runtime.observe(spec, {'load': 11.2, 'status': 'run'}, state)
        self.assertTrue(drift['wake'])
        self.assertEqual((state['observations'], state['wakes'], state['suppressed']), (3, 2, 1))
        self.assertEqual(drift['changed'], ['load'])

    def test_each_critical_bypasses_and_missing_is_unknown(self):
        spec = {'fields': ['status']}
        state, _ = runtime.observe(spec, {'status': 'run'})
        for key in ('completion', 'failure', 'denial', 'exhaustion'):
            _, result = runtime.observe(spec, {'status': 'run', key: True}, state)
            self.assertTrue(result['wake'])
            self.assertEqual(result['critical'], [key])
        _, missing = runtime.observe(spec, {}, state)
        self.assertTrue(missing['wake'])
        self.assertEqual(missing['unknown'], ['status'])

    def test_persistent_failure_coalesces_and_reassertion_wakes(self):
        spec = {'fields': ['load'], 'jitter': {'load': 5}}
        state, _ = runtime.observe(spec, {'load': 10})
        state, asserted = runtime.observe(spec, {'load': 11, 'failure': True}, state)
        self.assertTrue(asserted['wake'])
        state, persistent = runtime.observe(spec, {'load': 12, 'failure': True}, state)
        self.assertFalse(persistent['wake'])
        self.assertEqual(persistent['critical'], ['failure'])
        self.assertEqual(persistent['newCritical'], [])
        state, cleared = runtime.observe(spec, {'load': 12, 'failure': False}, state)
        self.assertFalse(cleared['wake'])
        state, reasserted = runtime.observe(spec, {'load': 12, 'failure': True}, state)
        self.assertTrue(reasserted['wake'])
        self.assertEqual(reasserted['newCritical'], ['failure'])
        self.assertEqual((state['observations'], state['wakes'], state['suppressed']), (5, 3, 2))

    def test_persistent_unknown_coalesces_and_new_unknown_wakes(self):
        spec = {'fields': ['a', 'b']}
        state, first = runtime.observe(spec, {'b': 1})
        self.assertEqual(first['unknown'], ['a'])
        state, persistent = runtime.observe(spec, {'b': 1}, state)
        self.assertFalse(persistent['wake'])
        state, new = runtime.observe(spec, {}, state)
        self.assertTrue(new['wake'])
        self.assertEqual(new['newUnknown'], ['b'])
        _, quiet = runtime.observe(spec, {}, state)
        self.assertFalse(quiet['wake'])

    def test_json_bool_number_and_nested_values_are_distinct(self):
        pairs = [(False, 0), (True, 1), ({'a': [False]}, {'a': [0]}), ([{'n': True}], [{'n': 1}])]
        for old, new in pairs:
            for jitter in ({}, {'value': 5}):
                spec = {'fields': ['value'], 'jitter': jitter}
                state, _ = runtime.observe(spec, {'value': old})
                _, result = runtime.observe(spec, {'value': new}, state)
                self.assertTrue(result['wake'], (old, new, jitter))
                self.assertEqual(result['changed'], ['value'])
        spec = {'fields': ['value']}
        state, _ = runtime.observe(spec, {'value': {'a': 1, 'b': 2}})
        _, result = runtime.observe(spec, {'value': {'b': 2, 'a': 1}}, state)
        self.assertFalse(result['wake'])

    def test_disappearance_policy_and_reappearance(self):
        for actionable in (False, True):
            spec = {'fields': ['value'], 'missingActionable': actionable}
            state, _ = runtime.observe(spec, {'value': 4})
            state, missing = runtime.observe(spec, {}, state)
            self.assertEqual(missing['wake'], actionable)
            self.assertEqual(missing['changed'], ['value'] if actionable else [])
            state, repeated = runtime.observe(spec, {}, state)
            self.assertFalse(repeated['wake'])
            state, reappeared = runtime.observe(spec, {'value': 4}, state)
            self.assertEqual(reappeared['wake'], actionable)
            state, _ = runtime.observe(spec, {}, state)
            _, changed = runtime.observe(spec, {'value': 7}, state)
            self.assertTrue(changed['wake'])

    def test_nonactionable_missing_retains_fixed_baseline_across_other_wakes(self):
        spec = {'fields': ['value', 'status'], 'missingActionable': False, 'jitter': {'value': 1}}
        state, _ = runtime.observe(spec, {'value': 10, 'status': 'run'})
        state, result = runtime.observe(spec, {'status': 'waiting'}, state)
        self.assertTrue(result['wake'])
        state, result = runtime.observe(spec, {'value': 10.8, 'status': 'waiting'}, state)
        self.assertFalse(result['wake'])
        _, result = runtime.observe(spec, {'value': 11.2, 'status': 'waiting'}, state)
        self.assertTrue(result['wake'])
        self.assertEqual(result['changed'], ['value'])

    def test_missing_sentinel_is_not_confused_with_real_object(self):
        spec = {'fields': ['value']}
        state, _ = runtime.observe(spec, {'value': {'unknown': True}})
        state, result = runtime.observe(spec, {}, state)
        self.assertTrue(result['wake'])
        _, result = runtime.observe(spec, {'value': {'unknown': True}}, state)
        self.assertTrue(result['wake'])

    def test_malformed_config_and_state_fail_cleanly(self):
        for update in ({'missingActionable': 1}, {'missingActionable': 'false'}, {'jitter': []}):
            with self.assertRaises(ValueError):
                runtime.observe(dict({'fields': ['a']}, **update), {'a': 1})
        state, _ = runtime.observe({'fields': ['a']}, {'a': 1})
        for update in ({'observations': True}, {'wakes': -1}, {'suppressed': '0'}, {'observations': 20}, {'lastMissing': None}):
            with self.assertRaises(ValueError):
                runtime.observe({'fields': ['a']}, {'a': 1}, dict(state, **update))

    def test_cli_compare_and_swap_and_concurrent_lock(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            runtime.atomic(root / 'spec', {'fields': ['status']})
            runtime.atomic(root / 'obs', {'status': 'run'})
            args = ['observe', '--state', str(root / 'state'), '--spec', str(root / 'spec'), '--observation', str(root / 'obs'), '--expect', 'absent']
            self.assertEqual(runtime.main(args), 0)
            original = (root / 'state').read_bytes()
            self.assertEqual(runtime.main(args), 2)
            self.assertEqual((root / 'state').read_bytes(), original)
            with runtime.lock(root / 'state'):
                self.assertEqual(runtime.main(args), 2)

    def test_changed_spec_rejected(self):
        state, _ = runtime.observe({'fields': ['a']}, {'a': 1})
        with self.assertRaises(ValueError):
            runtime.observe({'fields': ['b']}, {'b': 1}, state)


class CapabilityTests(unittest.TestCase):
    def test_current_probe_and_explicit_denial_revocation(self):
        with tempfile.TemporaryDirectory() as name:
            request = {'scope': name, 'owned': True, 'authorization': 'allowed', 'authorizationRevision': 'r1'}
            result = runtime.capability(request)
            self.assertEqual(result['effective'], 'observed-writable')
            self.assertEqual(list(Path(name).iterdir()), [])
            request.update(authorization='denied', authorizationRevision='r2')
            with mock.patch.object(runtime.tempfile, 'TemporaryDirectory', side_effect=AssertionError('must not probe')):
                self.assertEqual(runtime.capability(request)['effective'], 'denied')
            request['authorization'] = 'unknown'
            self.assertEqual(runtime.capability(request)['probe'], 'unrun')

    def test_cli_bound_capability_receipt_and_denial(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            scope = root / 'owned'
            scope.mkdir()
            binding = {'authorityDigest': 'a' * 64, 'conditionsDigest': 'b' * 64, 'producer': 'native-filesystem'}
            request = dict(binding, scope=str(scope), owned=True, authorization='allowed', authorizationRevision='revision-3')
            for authorization in ('allowed', 'denied', 'unknown'):
                request['authorization'] = authorization
                runtime.atomic(root / 'request.json', request)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(runtime.main(['capability', '--request', str(root / 'request.json')]), 0)
                receipt = json.loads(output.getvalue())
                self.assertEqual({key: receipt[key] for key in binding}, binding)
                self.assertEqual(receipt['authorizationRevision'], 'revision-3')
                self.assertEqual(receipt['scope'], str(scope))
                if authorization == 'allowed':
                    self.assertEqual((receipt['probe'], receipt['effective']), ('passed', 'observed-writable'))
                else:
                    self.assertEqual(receipt['probe'], 'unrun')
                    self.assertEqual(receipt['effective'], authorization)

    def test_cli_rejects_partial_or_malformed_binding_metadata(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'request.json'
            base = {'scope': name, 'owned': True, 'authorization': 'allowed', 'authorizationRevision': 'r1'}
            binding = {'authorityDigest': 'a' * 64, 'conditionsDigest': 'b' * 64, 'producer': 'native'}
            invalid = [{'authorityDigest': 'a' * 64}, dict(binding, authorityDigest='A' * 64),
                       dict(binding, conditionsDigest='short'), dict(binding, producer='  '), dict(binding, producer=3)]
            for metadata in invalid:
                runtime.atomic(path, dict(base, **metadata))
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(runtime.main(['capability', '--request', str(path)]), 2)

    def test_native_permission_denial(self):
        with tempfile.TemporaryDirectory() as name:
            with mock.patch.object(runtime.tempfile, 'TemporaryDirectory', side_effect=PermissionError('denied')):
                result = runtime.capability({'scope': name, 'owned': True, 'authorization': 'allowed', 'authorizationRevision': 'r1'})
            self.assertEqual(result['effective'], 'denied')
            self.assertEqual(result['authorization'], 'allowed')


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.path = self.root / 'scratch'
        self.marker = runtime.init_resource({'resource': str(self.path), 'owner': 'task-a'})
        (self.path / 'unique.txt').write_text('unfinished work\n')
        (self.path / 'empty').mkdir()
        self.request = {'resource': str(self.path), 'owner': 'task-a', 'resourceId': self.marker['id'],
                        'checkpoint': str(self.root / 'durable'), 'shared': False, 'dependents': [],
                        'lease': {'state': 'released', 'revision': 'lease-2'}, 'retire': True}
        self.plan = runtime.plan_resource(self.request)

    def tearDown(self):
        self.temporary.cleanup()

    def test_preserve_remove_restore_real_bytes(self):
        self.assertEqual(runtime.preserve(self.plan, self.request)['status'], 'verified')
        receipt = runtime.apply(self.plan, self.request)
        self.assertEqual(receipt['status'], 'removed')
        self.assertFalse(self.path.exists())
        destination = self.root / 'resumed'
        marker = runtime.init_resource({'resource': str(destination), 'owner': 'task-a'})
        restore = {'destination': str(destination), 'owner': 'task-a', 'resourceId': marker['id']}
        self.assertEqual(runtime.restore(self.plan, restore)['status'], 'verified')
        self.assertEqual((destination / 'unique.txt').read_text(), 'unfinished work\n')
        self.assertTrue((destination / 'empty').is_dir())
        self.assertTrue((self.root / 'durable' / 'retirement.json').exists())
        with self.assertRaises(ValueError):
            runtime.restore(self.plan, restore)

    def test_executable_and_directory_modes_round_trip(self):
        script = self.path / 'run.sh'
        script.write_text('#!/bin/sh\nexit 0\n')
        script.chmod(0o750)
        (self.path / 'empty').chmod(0o750)
        self.path.chmod(0o750)
        plan = runtime.plan_resource(self.request)
        runtime.preserve(plan, self.request)
        runtime.apply(plan, self.request)
        destination = self.root / 'mode-resume'
        marker = runtime.init_resource({'resource': str(destination), 'owner': 'task-a'})
        runtime.restore(plan, {'destination': str(destination), 'owner': 'task-a', 'resourceId': marker['id']})
        self.assertEqual((destination / 'run.sh').stat().st_mode & 0o777, 0o750)
        self.assertEqual((destination / 'empty').stat().st_mode & 0o777, 0o750)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o750)

    def test_chmod_after_plan_blocks_retirement_and_special_modes_rejected(self):
        runtime.preserve(self.plan, self.request)
        for target in (self.path / 'unique.txt', self.path / 'empty', self.path):
            original = target.stat().st_mode & 0o777
            target.chmod(original ^ 0o010)
            with self.assertRaises(ValueError):
                runtime.apply(self.plan, self.request)
            self.assertTrue(self.path.exists())
            target.chmod(original)
        (self.path / 'unique.txt').chmod(0o4644)
        with self.assertRaises(ValueError):
            runtime.plan_resource(self.request)

    def test_unknown_active_shared_and_revoked_inputs_preserved(self):
        for update in ({'dependents': ['reader']}, {'shared': True}, {'shared': None},
                       {'lease': {'state': 'active'}}, {'lease': {}}, {'retire': False}, {'owner': 'other'}):
            request = dict(self.request, **update)
            with self.assertRaises(ValueError):
                runtime.plan_resource(request)
            self.assertTrue(self.path.exists())
        runtime.preserve(self.plan, self.request)
        with self.assertRaises(ValueError):
            runtime.apply(self.plan, dict(self.request, dependents=['new-reader']))
        self.assertTrue(self.path.exists())

    def test_changed_source_stale_plan_and_corrupt_checkpoint(self):
        runtime.preserve(self.plan, self.request)
        (self.path / 'unique.txt').write_text('new unique work')
        with self.assertRaises(ValueError):
            runtime.apply(self.plan, self.request)
        self.assertTrue(self.path.exists())
        (self.path / 'unique.txt').write_text('unfinished work\n')
        (self.root / 'durable' / 'data' / 'unique.txt').write_text('corrupt')
        with self.assertRaises(ValueError):
            runtime.apply(self.plan, self.request)
        self.assertTrue(self.path.exists())

    def test_failed_preservation_never_deletes_and_snapshot_once(self):
        with mock.patch.object(runtime.shutil, 'copytree', side_effect=OSError('full')):
            with self.assertRaises(OSError):
                runtime.preserve(self.plan, self.request)
        self.assertTrue(self.path.exists())
        self.assertFalse((self.root / 'durable').exists())
        with self.assertRaises(OSError):
            runtime.apply(self.plan, self.request)
        runtime.preserve(self.plan, self.request)
        with self.assertRaises(ValueError):
            runtime.preserve(self.plan, self.request)

    def test_symlink_hardlink_parent_and_checkpoint_guards(self):
        (self.path / 'link').symlink_to(self.root)
        with self.assertRaises(ValueError):
            runtime.plan_resource(self.request)
        (self.path / 'link').unlink()
        import os
        os.link(str(self.path / 'unique.txt'), str(self.root / 'shared'))
        with self.assertRaises(ValueError):
            runtime.plan_resource(self.request)
        for path in ('/', str(Path.cwd()), str(Path.cwd().parent)):
            with self.assertRaises(ValueError):
                runtime.resource_path(path)
        with self.assertRaises(ValueError):
            runtime.resource_inputs(dict(self.request, checkpoint=str(self.path / 'checkpoint')))

    def test_stale_plan_and_failed_removal_preserve_unique_checkpoint(self):
        changed = dict(self.plan, planDigest='0' * 64)
        with self.assertRaises(ValueError):
            runtime.preserve(changed, self.request)
        runtime.preserve(self.plan, self.request)
        with mock.patch.object(runtime.shutil, 'rmtree', side_effect=OSError('busy')):
            with self.assertRaises(OSError):
                runtime.apply(self.plan, self.request)
        self.assertTrue(self.path.exists())
        self.assertEqual(runtime.verify_checkpoint(self.plan)['status'], 'verified')

    def test_restore_nonempty_and_checkpoint_symlink_refused(self):
        runtime.preserve(self.plan, self.request)
        destination = self.root / 'resumed'
        marker = runtime.init_resource({'resource': str(destination), 'owner': 'task-a'})
        request = {'destination': str(destination), 'owner': 'task-a', 'resourceId': marker['id']}
        (destination / 'live').write_text('retain')
        with self.assertRaises(ValueError):
            runtime.restore(self.plan, request)
        self.assertEqual((destination / 'live').read_text(), 'retain')
        data = self.root / 'durable' / 'data'
        data.rename(self.root / 'moved-data')
        data.symlink_to(self.root / 'moved-data', target_is_directory=True)
        with self.assertRaises(ValueError):
            runtime.verify_checkpoint(self.plan)

    def test_marker_path_label_is_insufficient(self):
        runtime.atomic(self.path / runtime.MARKER, dict(self.marker, id='replacement'))
        with self.assertRaises(ValueError):
            runtime.apply(self.plan, self.request)


if __name__ == '__main__':
    unittest.main()
