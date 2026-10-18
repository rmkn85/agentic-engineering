"""Offline contract tests; the optional activity needs stdlib tomllib."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('codex_settings', Path(__file__).resolve().parents[1] / 'codex_settings.py')
settings = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(settings)

CONFIG = b'''# private original\nmodel = "saved-model" # retain\nmodel_reasoning_effort = "high"\nmodel_auto_compact_token_limit = 180000 # keep this comment\napproval_policy = "on-request"\nsandbox_mode = "workspace-write"\n[features]\nunrelated = true\n[features.multi_agent_v2]\nmulti_agent_mode_hint_text = "old hint" # retain hint comment\n[profiles.review]\nmodel = "another saved model"\n'''


@unittest.skipIf(settings.tomllib is None, 'optional settings activity requires Python 3.11+ tomllib')
class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.config = self.root / 'config.toml'
        self.config.write_bytes(CONFIG)
        self.config.chmod(0o640)
        self.hint = self.root / 'hint.txt'
        self.hint.write_text('New literal hint\n$(touch NEVER) `echo never` "quoted"', encoding='utf-8')
        self.hint.chmod(0o600)
        self.cache = self.root / 'cache'

    def plan(self):
        return settings.plan(self.config, self.hint, self.cache)['plan_sha256']

    def test_exact_scope_and_text_preservation(self):
        hint = self.hint.read_text()
        result = settings.transform(CONFIG, hint)
        expected = CONFIG.replace(b'model_auto_compact_token_limit = 180000 ', b'')
        expected = expected.replace(b'"old hint"', json.dumps(hint, ensure_ascii=False).encode())
        self.assertEqual(result, expected)
        parsed = settings.tomllib.loads(result.decode())
        self.assertEqual(parsed['model'], 'saved-model')
        self.assertEqual(parsed['model_reasoning_effort'], 'high')
        self.assertEqual(parsed['sandbox_mode'], 'workspace-write')
        self.assertEqual(parsed['profiles']['review']['model'], 'another saved model')
        self.assertNotIn('model_auto_compact_token_limit', parsed)
        self.assertEqual(parsed['features']['multi_agent_v2']['multi_agent_mode_hint_text'], hint)

    def test_multiline_hint_and_crlf(self):
        original = CONFIG.replace(b'"old hint"', b'"""old\nhint"""').replace(b'\n', b'\r\n')
        result = settings.transform(original, 'replacement')
        self.assertIn(b'"replacement" # retain hint comment\r\n', result)
        self.assertEqual(result.count(b'\r\n'), original.count(b'\r\n') - 1)

    def test_backup_mode_atomic_replace_and_repeat(self):
        receipt = self.plan()
        with patch.object(settings.os, 'replace', wraps=os.replace) as replace:
            status = settings.apply(self.config, receipt, self.cache)
        self.assertEqual(status['status'], 'applied')
        replace.assert_called_once()
        self.assertEqual(stat.S_IMODE(self.config.stat().st_mode), 0o640)
        backup = self.cache / (settings.digest(CONFIG) + '.backup')
        self.assertEqual(backup.read_bytes(), CONFIG)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o600)
        self.assertEqual(settings.apply(self.config, receipt, self.cache)['status'], 'already_applied')
        self.assertEqual(list(self.root.glob('.codex-settings-*')), [])

    def test_plan_has_only_allowed_payload_and_digests(self):
        receipt = self.plan()
        payload = json.loads((self.cache / (receipt + '.json')).read_bytes())
        self.assertEqual(set(payload), {'schema', 'original_sha256', 'result_sha256', 'remove_top_level', 'replace_hint'})
        self.assertNotIn('saved-model', json.dumps(payload))
        self.assertNotIn('approval_policy', json.dumps(payload))
        self.assertEqual(stat.S_IMODE(self.cache.stat().st_mode), 0o700)

    def test_config_drift_refused(self):
        receipt = self.plan()
        self.config.write_bytes(CONFIG + b'# external edit\n')
        with self.assertRaises(settings.Rejected):
            settings.apply(self.config, receipt, self.cache)
        self.assertFalse(list(self.cache.glob('*.backup')))

    def test_plan_drift_refused(self):
        receipt = self.plan()
        path = self.cache / (receipt + '.json')
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaises(settings.Rejected):
            settings.apply(self.config, receipt, self.cache)
        self.assertEqual(self.config.read_bytes(), CONFIG)

    def test_extra_effects_even_with_rehashed_plan_refused(self):
        receipt = self.plan()
        payload = json.loads((self.cache / (receipt + '.json')).read_bytes())
        for key, value in [('model', 'attacker'), ('approval_policy', 'never'), ('destination', '/elsewhere')]:
            altered = dict(payload, **{key: value})
            data = json.dumps(altered).encode()
            forged = settings.digest(data)
            path = self.cache / (forged + '.json')
            path.write_bytes(data)
            path.chmod(0o600)
            with self.assertRaises(settings.Rejected):
                settings.apply(self.config, forged, self.cache)
        self.assertEqual(self.config.read_bytes(), CONFIG)

    def test_symlink_destination_cache_plan_and_parent_refused(self):
        real = self.root / 'real.toml'
        real.write_bytes(CONFIG)
        self.config.unlink()
        self.config.symlink_to(real)
        with self.assertRaises(settings.Rejected):
            self.plan()
        self.config.unlink()
        self.config.write_bytes(CONFIG)
        other = self.root / 'other'
        other.mkdir(mode=0o700)
        self.cache.symlink_to(other, target_is_directory=True)
        with self.assertRaises(settings.Rejected):
            self.plan()
        self.cache.unlink()
        receipt = self.plan()
        path = self.cache / (receipt + '.json')
        data = path.read_bytes()
        path.unlink()
        saved = self.root / 'saved'
        saved.write_bytes(data)
        path.symlink_to(saved)
        with self.assertRaises(settings.Rejected):
            settings.apply(self.config, receipt, self.cache)
        parent = self.root / 'linked'
        parent.symlink_to(other, target_is_directory=True)
        with self.assertRaises(settings.Rejected):
            settings.checked_path(parent / 'child')

    def test_unprivate_hint_and_cache_refused(self):
        self.hint.chmod(0o644)
        with self.assertRaises(settings.Rejected):
            self.plan()
        self.hint.chmod(0o600)
        self.cache.mkdir(mode=0o755)
        with self.assertRaises(settings.Rejected):
            self.plan()

    def test_unsupported_spelling_or_missing_key_refused(self):
        for data in [CONFIG.replace(b'model_auto_compact_token_limit', b'other'),
                     CONFIG.replace(b'[features.multi_agent_v2]', b'[features."multi_agent_v2"]'),
                     CONFIG.replace(b'180000', b'"180000"'),
                     CONFIG + b'\nmodel = "duplicate"\n']:
            with self.subTest(data=data):
                with self.assertRaises((settings.Rejected, ValueError)):
                    settings.transform(data, 'new')

    def test_failed_replace_leaves_original_and_backup(self):
        receipt = self.plan()
        with patch.object(settings.os, 'replace', side_effect=OSError('injected')):
            with self.assertRaises(OSError):
                settings.apply(self.config, receipt, self.cache)
        self.assertEqual(self.config.read_bytes(), CONFIG)
        self.assertTrue(list(self.cache.glob('*.backup')))
        self.assertEqual(list(self.root.glob('.codex-settings-*')), [])

    def test_final_drift_check(self):
        receipt = self.plan()
        reader = settings.read_regular
        count = 0
        def changing(path):
            nonlocal count
            if Path(path) == self.config:
                count += 1
                if count == 2:
                    self.config.write_bytes(CONFIG + b'# racing writer\n')
            return reader(path)
        with patch.object(settings, 'read_regular', side_effect=changing):
            with self.assertRaises(settings.Rejected):
                settings.apply(self.config, receipt, self.cache)
        self.assertTrue(self.config.read_bytes().endswith(b'# racing writer\n'))


class ParserTests(unittest.TestCase):
    def test_only_exact_activities_and_arguments(self):
        self.assertEqual(settings.parse_activity(['codex-settings-plan', 'HINT_FILE=a b;$(never)']),
                         ('codex-settings-plan', 'a b;$(never)'))
        for args in [[], ['--help'], ['-f', 'evil'], ['codex-settings-plan', 'HINT_FILE=a', 'check'],
                     ['codex-settings-plan', 'HINT_FILE=a', 'SHELL=evil'],
                     ['codex-settings-plan', '--eval=evil'], ['check', 'HINT_FILE=a'],
                     ['codex-settings-apply', 'PLAN_SHA256=' + 'A' * 64],
                     ['codex-settings-plan', 'DESTINATION=x'], ['codex-settings-plan', 'HINT_FILE=']]:
            with self.subTest(args=args), self.assertRaises(settings.Rejected):
                settings.parse_activity(args)

    def test_wrapper_never_executes_make_options_or_shell_data(self):
        wrapper = Path(__file__).resolve().parents[1] / 'make'
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'executed'
            result = subprocess.run([str(wrapper), '--eval=touch ' + str(marker)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(marker.exists())
            result = subprocess.run([str(wrapper), 'codex-settings-plan', 'HINT_FILE=$(touch ' + str(marker) + ')'],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(marker.exists())
            self.assertNotIn(str(marker), result.stderr)

    def test_clear_dependency_failure_without_install(self):
        with patch.object(settings, 'tomllib', None):
            with self.assertRaisesRegex(settings.Rejected, 'Python 3.11'):
                settings.transform(b'', 'hint')
