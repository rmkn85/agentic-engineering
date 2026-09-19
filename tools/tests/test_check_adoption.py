import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("adoption", Path(__file__).resolve().parents[1] / "check-adoption.py")
adoption = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adoption)


class AdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "core.md").write_text("Core\n")
        self.manifest = {"schema": 1, "upstream": {"repository": "rmkn85/agentic-engineering", "revision": "a" * 40}, "files": [{"path": "core.md", "sha256": hashlib.sha256(b"Core\n").hexdigest()}], "entrypoints": ["core.md"]}
        patch = mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false"})
        patch.start()
        self.addCleanup(patch.stop)

    def test_malformed_manifest_is_a_bounded_failure(self):
        for value in (None, [], {"schema": 1, "upstream": []}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                adoption.validate(self.root, value)

    def test_valid_snapshot_needs_no_upstream_checkout(self):
        self.assertEqual(adoption.validate(self.root, self.manifest)["files"], 1)

    def test_drift_fails(self):
        (self.root / "core.md").write_text("Changed\n")
        with self.assertRaisesRegex(ValueError, "drift"):
            adoption.validate(self.root, self.manifest)

    def test_missing_file_fails(self):
        (self.root / "core.md").unlink()
        with self.assertRaises(ValueError):
            adoption.validate(self.root, self.manifest)

    def test_path_traversal_and_absolute_paths_fail(self):
        for name in ("../core.md", "/core.md", "a/../core.md", "a\\core.md", "a//core.md", "C:/core.md"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                adoption.local_file(self.root, name)

    def test_symlink_fails(self):
        try:
            (self.root / "alias.md").symlink_to(self.root / "core.md")
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            adoption.local_file(self.root, "alias.md")

    def test_duplicate_path_fails(self):
        self.manifest["files"] *= 2
        with self.assertRaises(ValueError):
            adoption.validate(self.root, self.manifest)

    def test_mutable_upstream_ref_fails(self):
        self.manifest["upstream"]["revision"] = "main"
        with self.assertRaises(ValueError):
            adoption.validate(self.root, self.manifest)

    def test_missing_entrypoint_fails(self):
        self.manifest["entrypoints"] = ["AGENTS.md"]
        with self.assertRaises(ValueError):
            adoption.validate(self.root, self.manifest)

    def test_wrong_ci_candidate_fails(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_SHA": "b" * 40}), mock.patch.object(adoption.subprocess, "check_output", return_value="c" * 40):
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                adoption.validate(self.root, self.manifest)

    def test_ci_candidate_is_recorded_not_latest_inferred(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_SHA": "b" * 40}), mock.patch.object(adoption.subprocess, "check_output", return_value="b" * 40):
            self.assertEqual(adoption.validate(self.root, self.manifest)["candidate"], "b" * 40)


if __name__ == "__main__":
    unittest.main()
