"""Discriminating safety tests using disposable local repositories, never user data."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location('preservation_guard', Path(__file__).resolve().parents[1] / 'agent-checkout.py')
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class PreservationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.remote, self.writer, self.local = [self.root / name for name in ('remote.git', 'writer', 'local')]
        settings = mock.patch.dict(os.environ, {
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
            'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
        })
        settings.start()
        self.addCleanup(settings.stop)
        self.git(self.root, 'init', '--bare', '--initial-branch=main', str(self.remote))
        self.git(self.root, 'clone', str(self.remote), str(self.writer))
        (self.writer / '.gitignore').write_text('local-settings.txt\n')
        self.git(self.writer, 'add', '.gitignore')
        self.git(self.writer, 'commit', '-m', 'base')
        self.git(self.writer, 'push', 'origin', 'main')
        self.git(self.root, 'clone', str(self.remote), str(self.local))
        normal = guard.repository_id
        identity = mock.patch.object(guard, 'repository_id', side_effect=lambda value:
            'example/project' if value == str(self.remote) else normal(value))
        identity.start()
        self.addCleanup(identity.stop)

    def git(self, root, *args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.DEVNULL, timeout=10).strip()

    def publish(self, name):
        (self.writer / name).write_text('upstream content\n')
        self.git(self.writer, 'add', '-f', name)
        self.git(self.writer, 'commit', '-m', 'advance')
        self.git(self.writer, 'push', 'origin', 'main')
        return self.git(self.writer, 'rev-parse', 'HEAD')

    def invoke(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = guard.main(['--path', str(self.local), '--expect', 'example/project', '--branch', 'main', '--ff-only'])
        return code, json.loads(output.getvalue())

    def test_ignored_collision_preserves_local_bytes_and_head(self):
        before = self.git(self.local, 'rev-parse', 'HEAD')
        (self.local / 'local-settings.txt').write_text('unpublished local settings\n')
        self.publish('local-settings.txt')
        code, _ = self.invoke()
        self.assertEqual((self.local / 'local-settings.txt').read_text(), 'unpublished local settings\n')
        self.assertEqual(self.git(self.local, 'rev-parse', 'HEAD'), before)
        self.assertEqual(code, 3)

    def test_unrelated_ignored_file_does_not_block_safe_fast_forward(self):
        (self.local / 'local-settings.txt').write_text('preserve me\n')
        target = self.publish('feature.txt')
        code, receipt = self.invoke()
        self.assertEqual((code, receipt['head']), (0, target))
        self.assertEqual((self.local / 'local-settings.txt').read_text(), 'preserve me\n')
        self.assertFalse(self.invoke()[1]['mutated'])

    def test_branch_switch_during_fetch_is_not_silently_updated(self):
        before = self.git(self.local, 'rev-parse', 'HEAD')
        self.publish('feature.txt')
        original_git = guard.git
        def changing_git(root, *args):
            result = original_git(root, *args)
            if args[0] == 'fetch':
                self.git(self.local, 'switch', '-c', 'another-task')
            return result
        with mock.patch.object(guard, 'git', side_effect=changing_git):
            code, _ = self.invoke()
        self.assertEqual(code, 3)
        self.assertEqual(self.git(self.local, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.git(self.local, 'branch', '--show-current'), 'another-task')

    def test_dirty_edit_is_preserved_even_when_autostash_is_enabled(self):
        self.git(self.local, 'config', 'merge.autostash', 'true')
        (self.local / '.gitignore').write_text('owned unfinished edit\n')
        self.publish('feature.txt')
        code, receipt = self.invoke()
        self.assertEqual((code, receipt['reason']), (3, 'working_tree_not_clean'))
        self.assertEqual((self.local / '.gitignore').read_text(), 'owned unfinished edit\n')


if __name__ == '__main__':
    unittest.main()
