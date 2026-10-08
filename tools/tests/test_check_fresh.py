"""Real local-Git trials of native commands, not file-presence checks."""
import errno
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("fresh", Path(__file__).resolve().parents[1] / "check-fresh.py")
fresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fresh)


@unittest.skipUnless(shutil.which("git"), "Git is required")
class FreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        self.env = fresh.environment(self.base / "setup-home")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        (self.source / "value.txt").write_text("old\n")
        self.commit()
        (self.source / "value.txt").write_text("new\n")
        self.commit()

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.source), *args],
                                       env=self.env, stderr=subprocess.DEVNULL, text=True).strip()

    def commit(self):
        self.git("add", "--all")
        self.git("commit", "-m", "test: change fixture")

    def exercise(self, code=None, timeout=10):
        output = Path(tempfile.mkdtemp(dir=self.base))
        if code is None:
            code = "from pathlib import Path; assert Path('value.txt').read_text() == 'new\\n'"
        return fresh.exercise(self.source, [sys.executable, "-c", code], output, timeout)

    def test_cold_and_stale_check_actual_new_candidate_without_siblings(self):
        result = self.exercise()
        self.assertEqual(result["state"], "passed", result)
        self.assertEqual(result["candidate"], self.git("rev-parse", "HEAD"))
        self.assertEqual([r["retained_local_files"] for r in result["scenarios"]], [0, 2])
        self.assertNotEqual(result["candidate"], result["stale_base"])
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_warm_home_dependency_is_exposed_not_inherited(self):
        home = self.base / "warm-home"
        home.mkdir()
        (home / "hidden-config").write_text("installed only on maintainer host")
        code = "import os; from pathlib import Path; assert (Path(os.environ['HOME']) / 'hidden-config').exists()"
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)
            result = self.exercise(code)
        self.assertEqual(result["reason"], "command_exit_1")
        self.assertEqual(len(result["scenarios"]), 1)

    def test_uncommitted_feature_cannot_receive_a_pass_for_old_HEAD(self):
        (self.source / "value.txt").write_text("uncommitted change")
        result = self.exercise()
        self.assertEqual(result["reason"], "source_has_uncommitted_work")
        self.assertEqual(result["scenarios"], [])
        self.assertEqual((self.source / "value.txt").read_text(), "uncommitted change")

    def test_untracked_work_is_not_omitted_silently(self):
        (self.source / "new-feature.txt").write_text("new")
        self.assertEqual(self.exercise()["reason"], "source_has_uncommitted_work")

    def test_missing_history_is_not_a_stale_test_pass(self):
        self.git("checkout", "--orphan", "single")
        self.commit()
        result = self.exercise()
        self.assertEqual(result["reason"], "source_identity_or_history_unavailable")
        self.assertEqual(result["scenarios"], [])

    def test_failure_stops_before_next_scenario_and_retains_detail(self):
        result = self.exercise("print('original diagnostic'); raise SystemExit(7)")
        self.assertEqual(result["reason"], "command_exit_7")
        self.assertEqual(len(result["scenarios"]), 1)
        log = Path(result["scenarios"][0]["log"])
        self.assertIn("original diagnostic", log.read_text())
        self.assertIn("original diagnostic", result["failure_excerpt"])

    def test_timeout_is_failure(self):
        result = self.exercise("import time; time.sleep(60)", timeout=1)
        self.assertEqual(result["reason"], "command_timeout")

    def test_native_check_cannot_rewrite_tracked_feature_to_manufacture_pass(self):
        result = self.exercise("from pathlib import Path; Path('value.txt').write_text('changed')")
        self.assertEqual(result["reason"], "native_check_changed_tracked_source")
        self.assertEqual((self.source / "value.txt").read_text(), "new\n")

    def test_native_check_cannot_change_candidate(self):
        result = self.exercise("import subprocess; subprocess.run(['git','checkout','--detach','HEAD^'], check=True)")
        self.assertEqual(result["reason"], "native_check_changed_candidate")

    def test_stale_check_cannot_destroy_unrelated_files(self):
        code = "from pathlib import Path; [p.unlink() for p in Path('.').glob('.contributor-trial-*')]"
        result = self.exercise(code)
        self.assertEqual(result["reason"], "native_check_damaged_local_work")
        self.assertEqual(result["scenarios"][0]["state"], "passed")

    def test_ci_clone_has_its_own_exact_candidate(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_SHA": "wrong", "GITHUB_WORKSPACE": "wrong"}):
            result = self.exercise("import os, subprocess; from pathlib import Path; assert Path(os.environ['GITHUB_WORKSPACE']) == Path.cwd(); assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==os.environ['GITHUB_SHA']")
        self.assertEqual(result["state"], "passed", result)

    def test_sentinel_path_must_not_be_owned_by_candidate(self):
        (self.source / ".contributor-trial-ignored").write_text("real project content")
        self.commit()
        self.assertEqual(self.exercise()["reason"], "trial_sentinel_collides_with_source")

    def test_inherited_secrets_and_import_paths_are_not_passed(self):
        with mock.patch.dict(os.environ, {"GITHUB_TOKEN": "fixture-only", "PYTHONPATH": "fixture-only", "VIRTUAL_ENV": "fixture-only", "NPM_TOKEN": "fixture-only"}):
            result = self.exercise("import os; assert not any(k in os.environ for k in ['GITHUB_TOKEN','NPM_TOKEN','PYTHONPATH','VIRTUAL_ENV'])")
        self.assertEqual(result["state"], "passed", result)

    def test_noisy_success_is_stored_not_returned_as_context(self):
        result = self.exercise("print('x' * 20000)")
        self.assertEqual(result["state"], "passed", result)
        self.assertLess(len(json.dumps(result)), 2000)
        self.assertGreater(Path(result["scenarios"][0]["log"]).stat().st_size, 20000)

    def test_native_make_entry_is_exercised_not_reimplemented(self):
        if not shutil.which("make"):
            self.skipTest("Make not present")
        # Use a separate explicit check script to avoid make/shell escaping policy.
        (self.source / "check.py").write_text("from pathlib import Path\nassert Path('value.txt').read_text() == 'new\\n'\n")
        (self.source / "Makefile").write_text("check:\n\t@" + sys.executable + " check.py\n")
        self.commit()
        output = Path(tempfile.mkdtemp(dir=self.base))
        result = fresh.exercise(self.source, ["make", "check"], output, 10)
        self.assertEqual(result["state"], "passed", result)


    def test_control_storage_failure_returns_nonpassing_receipt(self):
        # Deterministic ENOSPC injection, not filling the host disk.
        with mock.patch.object(fresh, "environment", side_effect=OSError(errno.ENOSPC, "fixture disk full")):
            result = self.exercise()
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["reason"], "trial_io_failure")
        self.assertEqual(result["scenarios"], [])
        self.assertEqual((self.source / "value.txt").read_text(), "new\n")

    def test_log_read_failure_preserves_original_command_failure(self):
        original_open = Path.open
        reached = []

        def fail_diagnostic_read(path, mode="r", *args, **kwargs):
            if path.name == "cold-native.log" and mode == "rb":
                reached.append(path)
                raise OSError(errno.EIO, "fixture diagnostic read failed")
            return original_open(path, mode, *args, **kwargs)

        with mock.patch.object(Path, "open", fail_diagnostic_read):
            result = self.exercise("raise SystemExit(7)")
        self.assertTrue(reached, "Fault must reach the diagnostic boundary")
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["reason"], "command_exit_7")
        self.assertEqual(result["evidence_error"], "failure_log_unavailable")
        self.assertNotIn("failure_excerpt", result)
        self.assertEqual(len(result["scenarios"]), 1)

    def test_temp_directory_failure_does_not_start_checks(self):
        output = io.StringIO()
        with mock.patch.object(fresh.tempfile, "mkdtemp", side_effect=OSError(errno.ENOSPC, "fixture disk full")), \
                mock.patch.object(fresh, "exercise") as execute, \
                mock.patch("sys.stdout", output):
            code = fresh.main(["--source", str(self.source), "--", sys.executable, "-c", "pass"])
        execute.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["state"], "failed")
        self.assertEqual(result["reason"], "trial_storage_unavailable")
        self.assertEqual(result["scenarios"], [])
        self.assertNotIn("evidence_directory", result)

    def test_receipt_write_failure_preserves_check_outcome_and_fails_delivery(self):
        original_write = Path.write_text
        reached = []

        def fail_receipt_write(path, *args, **kwargs):
            if path.name == "receipt.json":
                reached.append(path)
                raise OSError(errno.ENOSPC, "fixture disk full")
            return original_write(path, *args, **kwargs)

        for native_code, check_state, reason in (
                ("pass", "passed", "receipt_write_failed"),
                ("raise SystemExit(7)", "failed", "command_exit_7")):
            with self.subTest(check_state=check_state):
                trial_dir = Path(tempfile.mkdtemp(dir=self.base))
                output = io.StringIO()
                with mock.patch.object(fresh.tempfile, "mkdtemp", return_value=str(trial_dir)), \
                        mock.patch.object(Path, "write_text", fail_receipt_write), \
                        mock.patch("sys.stdout", output):
                    code = fresh.main(["--source", str(self.source), "--", sys.executable, "-c", native_code])
                result = json.loads(output.getvalue())
                self.assertEqual(code, 1)
                self.assertEqual(result["state"], "failed")
                self.assertEqual(result["check_state"], check_state)
                self.assertEqual(result["reason"], reason)
                self.assertEqual(result["evidence_error"], "receipt_write_failed")
                self.assertEqual(result["candidate"], self.git("rev-parse", "HEAD"))
                self.assertEqual((self.source / "value.txt").read_text(), "new\n")
        self.assertEqual(len(reached), 2, "Both receipt-write injections must execute")

    def test_cli_positive_control_persists_matching_receipt(self):
        trial_dir = Path(tempfile.mkdtemp(dir=self.base))
        output = io.StringIO()
        with mock.patch.object(fresh.tempfile, "mkdtemp", return_value=str(trial_dir)), \
                mock.patch("sys.stdout", output):
            code = fresh.main(["--source", str(self.source), "--", sys.executable, "-c", "pass"])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["state"], "passed")
        self.assertEqual(result, json.loads((trial_dir / "receipt.json").read_text()))
        self.assertEqual(len(result["scenarios"]), 2)
        self.assertEqual(self.git("status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
