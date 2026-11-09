import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native_boundary as boundary


class NativeBoundaryTests(unittest.TestCase):
    def observe(self, **changes):
        values = dict(root=os.ST_RDONLY, mask=os.ST_RDONLY, mode=stat.S_IFDIR,
                      owner=os.geteuid(), status='NoNewPrivs:\t1\nSeccomp:\t2\n', profile='test-profile')
        values.update(changes)
        with mock.patch.object(boundary.sys, 'platform', 'linux'), \
             mock.patch.object(boundary.os, 'statvfs', side_effect=[SimpleNamespace(f_flag=values['root']), SimpleNamespace(f_flag=values['mask'])]) as statvfs, \
             mock.patch.object(boundary.Path, 'lstat', return_value=SimpleNamespace(st_mode=values['mode'], st_uid=values['owner'])), \
             mock.patch.object(boundary.Path, 'read_text', return_value=values['status']), \
             mock.patch.object(boundary.os, 'readlink', return_value='mnt:[observation]'), \
             mock.patch.dict(os.environ, {'CODEX_PERMISSION_PROFILE': values['profile']}):
            observed = boundary.observe('outer-codex-sandbox')
            self.assertEqual(statvfs.call_args_list[1].args[0], Path('/tmp') / ('codex-daemon-' + str(os.geteuid())))
            return observed

    def test_guard_requires_every_independent_observation(self):
        self.assertEqual(self.observe()['status'], 'verified')
        for changed in ({'root': 0}, {'mask': 0}, {'mode': stat.S_IFDIR | 0o700},
                        {'mode': stat.S_IFLNK}, {'owner': os.geteuid() + 1}, {'profile': ''},
                        {'status': 'NoNewPrivs: 0\nSeccomp: 2'}, {'status': 'NoNewPrivs: 1\nSeccomp: 0'}):
            with self.subTest(changed=changed):
                self.assertEqual(self.observe(**changed)['status'], 'failed')
        with mock.patch.object(boundary.os, 'statvfs', side_effect=OSError):
            self.assertEqual(boundary.observe('outer-codex-sandbox')['status'], 'failed')

    def test_non_linux_fails_closed_before_linux_observations(self):
        with mock.patch.object(boundary.sys, 'platform', 'unsupported'), \
             mock.patch.object(boundary.os, 'statvfs') as observation:
            result = boundary.observe('outer-codex-sandbox')
            observation.assert_not_called()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['checks'], {'linux': False})

    def test_signature_binds_profile_but_not_namespace_observation(self):
        frozen = self.observe()
        current = dict(frozen, mount_namespace='mnt:[different-normal-tool-call]')
        self.assertTrue(boundary.matches(frozen, current))
        self.assertFalse(boundary.matches(frozen, self.observe(profile='different-profile')))
        self.assertFalse(boundary.matches(frozen, {'status': 'failed'}))
        self.assertEqual(boundary.observe('native')['status'], 'not_applicable')
        with self.assertRaises(ValueError): boundary.observe('unknown')
