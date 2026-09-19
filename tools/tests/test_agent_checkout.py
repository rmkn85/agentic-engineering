"""Offline acceptance fixtures. Real Git repositories; no user checkout or network."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("checkout_guard", Path(__file__).resolve().parents[1] / "agent-checkout.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


@unittest.skipUnless(shutil.which("git"), "Git is a prerequisite")
class CheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root / "remote.git"
        self.writer = self.root / "writer"
        self.checkout = self.root / "checkout"
        self.env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.run_git(self.root, "init", "--bare", "--initial-branch=main", str(self.remote))
        self.run_git(self.root, "clone", str(self.remote), str(self.writer))
        self.commit(self.writer, "base")
        self.run_git(self.writer, "push", "origin", "main")
        self.run_git(self.root, "clone", str(self.remote), str(self.checkout))
        normalizer = guard.repository_id
        # Only local fixture remotes are mapped; all Git operations are real.
        self.identity = mock.patch.object(guard, "repository_id", side_effect=lambda value:
            "example/project" if value == str(self.remote) else normalizer(value))
        self.identity.start()
        self.addCleanup(self.identity.stop)

    def run_git(self, root, *args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL, text=True).strip()

    def commit(self, root, name):
        (root / (name + ".txt")).write_text(name + "\n")
        self.run_git(root, "add", name + ".txt")
        self.run_git(root, "commit", "-m", name)
        return self.run_git(root, "rev-parse", "HEAD")

    def invoke(self, *extra, branch=True):
        output = io.StringIO()
        args = ["--path", str(self.checkout), "--expect", "example/project"]
        if branch:
            args += ["--branch", "main"]
        with contextlib.redirect_stdout(output):
            code = guard.main(args + list(extra))
        return code, json.loads(output.getvalue())

    def advance(self):
        head = self.commit(self.writer, "remote-change")
        self.run_git(self.writer, "push", "origin", "main")
        return head

    def test_cached_refs_never_claim_freshness(self):
        code, receipt = self.invoke()
        self.assertEqual((code, receipt["reason"]), (3, "remote_freshness_unverified"))

    def test_fetch_verifies_current_checkout(self):
        code, receipt = self.invoke("--fetch")
        self.assertEqual(code, 0)
        self.assertEqual(receipt["state"], "current_clean_checkout")
        self.assertFalse(receipt["mutated"])

    def test_fetch_does_not_move_a_stale_checkout(self):
        before = self.run_git(self.checkout, "rev-parse", "HEAD")
        self.advance()
        code, receipt = self.invoke("--fetch")
        self.assertEqual(receipt["reason"], "behind_remote")
        self.assertEqual(self.run_git(self.checkout, "rev-parse", "HEAD"), before)

    def test_fast_forward_is_idempotent(self):
        head = self.advance()
        code, receipt = self.invoke("--ff-only")
        self.assertEqual((code, receipt["head"], receipt["mutated"]), (0, head, True))
        code, receipt = self.invoke("--ff-only")
        self.assertEqual((code, receipt["mutated"]), (0, False))

    def test_tracked_edits_are_preserved(self):
        self.advance()
        (self.checkout / "base.txt").write_text("unsaved task\n")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "working_tree_not_clean")
        self.assertEqual((self.checkout / "base.txt").read_text(), "unsaved task\n")

    def test_untracked_files_are_preserved(self):
        (self.checkout / "new.txt").write_text("uncommitted work")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "working_tree_not_clean")

    def test_local_commits_are_not_pushed_or_reset(self):
        head = self.commit(self.checkout, "local-change")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "unpublished_local_commits")
        self.assertEqual(self.run_git(self.checkout, "rev-parse", "HEAD"), head)

    def test_divergence_is_not_auto_merged(self):
        head = self.commit(self.checkout, "local-change")
        self.advance()
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "diverged")
        self.assertEqual(self.run_git(self.checkout, "rev-parse", "HEAD"), head)

    def test_wrong_branch_is_not_switched(self):
        self.run_git(self.checkout, "switch", "-c", "other-task")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "wrong_or_detached_branch")
        self.assertEqual(self.run_git(self.checkout, "branch", "--show-current"), "other-task")

    def test_detached_candidate_has_separate_read_only_route(self):
        head = self.run_git(self.checkout, "rev-parse", "HEAD")
        self.run_git(self.checkout, "checkout", "--detach", head)
        code, receipt = self.invoke("--revision", head, branch=False)
        self.assertEqual((code, receipt["state"]), (0, "exact_candidate"))
        self.assertEqual(receipt["freshness"], "not_asserted")

    def test_wrong_candidate_fails(self):
        code, receipt = self.invoke("--revision", "0" * 40, branch=False)
        self.assertEqual(receipt["reason"], "candidate_revision_mismatch")

    def test_wrong_repository_fails_before_fetch(self):
        self.run_git(self.checkout, "remote", "set-url", "origin", "https://github.com/example/wrong.git")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "wrong_repository_or_push_destination")

    def test_wrong_push_destination_fails(self):
        self.run_git(self.checkout, "remote", "set-url", "--push", "origin", "https://github.com/example/wrong.git")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "wrong_repository_or_push_destination")

    def test_unfinished_git_operation_fails(self):
        head = self.run_git(self.checkout, "rev-parse", "HEAD")
        (self.checkout / ".git" / "CHERRY_PICK_HEAD").write_text(head)
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt["reason"], "git_operation_in_progress")

    def test_failed_fetch_does_not_claim_offline_success(self):
        shutil.rmtree(self.remote)
        code, receipt = self.invoke("--fetch")
        self.assertEqual(receipt["reason"], "git_fetch_failed")

    def test_subdirectory_resolves_same_repository(self):
        (self.checkout / "nested").mkdir()
        self.checkout = self.checkout / "nested"
        code, receipt = self.invoke("--fetch")
        self.assertEqual(code, 0)

    def test_multiple_push_destinations_are_not_ignored(self):
        self.run_git(self.checkout, "config", "--add", "remote.origin.pushurl", str(self.remote))
        self.run_git(self.checkout, "config", "--add", "remote.origin.pushurl", "https://github.com/example/wrong.git")
        code, receipt = self.invoke("--ff-only")
        self.assertEqual(receipt.get("reason"), "wrong_repository_or_push_destination")


class PrimitiveTests(unittest.TestCase):
    def test_url_normalization(self):
        for url in ("https://github.com/Example/Project.git", "git@github.com:Example/Project.git", "ssh://git@github.com/Example/Project.git"):
            self.assertEqual(guard.repository_id(url), "example/project")

    def test_untrusted_transport_is_not_normalized_as_github(self):
        for url in ("https://elsewhere.invalid/example/project", "https://github.com/example/project?token=secret", "file:///tmp/project"):
            with self.assertRaises(guard.Blocked):
                guard.repository_id(url)

    def test_timeout_has_bounded_non_sensitive_result(self):
        with mock.patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaisesRegex(guard.Blocked, "git_timeout"):
                guard.git(Path("."), "fetch", "origin")

    def test_missing_git_has_specific_result(self):
        with mock.patch.object(subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(guard.Blocked, "git_unavailable"):
                guard.git(Path("."), "status")


if __name__ == "__main__":
    unittest.main()
