import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


TOOL = Path(__file__).resolve().parents[1] / "check_hygiene.py"


class HygieneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.commit("README.md", "hello")

    def git(self, *args):
        subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", *args],
                       cwd=self.root, check=True, capture_output=True)

    def commit(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git("add", "-f", rel)
        self.git("commit", "-qm", rel)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              capture_output=True, text=True, check=False)

    def test_clean_repository(self):
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 0)
        self.assertIn("clean", result.stdout)

    def test_merged_branch_and_extra_worktree(self):
        self.git("checkout", "-q", "-b", "done-topic")
        self.commit("feature.txt", "x")
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--no-ff", "-m", "merge", "done-topic")
        self.git("branch", "just-started")  # no commits of its own yet: not a leftover
        self.git("worktree", "add", "-q", str(Path(self.temp.name) / "wt"), "-b", "live")
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 1)
        self.assertIn("merged branch not deleted: done-topic", result.stdout)
        self.assertNotIn("worktree", result.stdout)  # one fresh worktree is active parallel work
        self.assertNotIn("just-started", result.stdout)

    def add_worktree(self, name):
        path = Path(self.temp.name) / name
        self.git("worktree", "add", "-q", str(path), "-b", name)
        return path

    def test_worktree_older_than_a_day_fails(self):
        path = self.add_worktree("stale")
        admin = Path(self.temp.name) / "repo" / ".git" / "worktrees" / "stale" / "commondir"
        old = time.time() - 30 * 3600
        os.utime(admin, (old, old))
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"extra worktree {path} is 30h old", result.stdout)
        self.assertEqual(self.run_tool("--strict", "--max-worktree-hours", "48").returncode, 0)

    def test_more_worktrees_than_the_cap_fail(self):
        for n in range(3):
            self.add_worktree(f"lane{n}")
        self.assertEqual(self.run_tool("--strict").returncode, 0)
        self.add_worktree("lane3")
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 1)
        self.assertIn("4 extra worktrees exceed the cap of 3", result.stdout)

    def test_dated_process_records_and_tracked_scratch(self):
        self.commit("docs/plans/2026-10-28-rollout.md", "x")
        self.commit("docs/reviews/review-2026-11-01.md", "x")
        self.commit("handoff-20261101.md", "x")
        self.commit("docs/notes/2026-11-07-plan.md", "x")
        self.commit("docs/2026-11-07 review.md", "x")
        self.commit(".tmp/run/out.txt", "x")
        self.commit("build.log", "x")
        result = self.run_tool()
        self.assertEqual(result.returncode, 0)  # report mode never fails
        for expected in ("docs/plans/2026-10-28-rollout.md", "handoff-20261101.md", ".tmp/run/out.txt", "build.log",
                         "docs/notes/2026-11-07-plan.md", "docs/2026-11-07 review.md"):
            self.assertIn(expected, result.stdout)

    def test_more_scratch_and_dated_plan_spellings(self):
        for path in ("scratch/try.py", "out.tmp", "docs/plan-2026.11.07.md", "docs/plans/2026-11-07.json"):
            self.commit(path, "x")
        result = self.run_tool()
        for expected in ("scratch/try.py", "out.tmp", "docs/plan-2026.11.07.md", "docs/plans/2026-11-07.json"):
            self.assertIn(expected, result.stdout)

    def test_fast_forward_merged_branch_is_reported(self):
        self.git("checkout", "-q", "-b", "feat")
        self.commit("feat.txt", "x")
        self.git("checkout", "-q", "main")
        self.git("merge", "-q", "--ff-only", "feat")
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 1)
        self.assertIn("merged branch not deleted: feat", result.stdout)

    def test_local_trunk_is_not_flagged_against_its_remote(self):
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-q", "-b", "topic")
        self.assertIn("clean", self.run_tool("--strict", "--base", "origin/main").stdout)

    def test_ordinary_dated_and_fixture_files_are_not_flagged(self):
        self.commit("references/research-2026-09/README.md", "x")
        self.commit("experiments/2026-09-20-trial.md", "x")
        self.commit("db/migrate/20240101120000_add_status_to_users.rb", "x")
        self.commit("tmp/.keep", "")
        self.commit("test/fixtures/sample.log", "x")
        self.commit("src/status/20200101_migration.sql", "x")
        self.assertIn("clean", self.run_tool("--strict").stdout)


class HygieneWithoutMainTests(unittest.TestCase):
    def test_master_trunk_and_missing_base_do_not_crash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run = lambda *a: subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", *a],
                                            cwd=root, check=True, capture_output=True)
            run("init", "-q", "-b", "master")
            (root / "a.txt").write_text("x")
            run("add", ".")
            run("commit", "-qm", "a")
            for args in ([], ["--base", "main"]):
                result = subprocess.run([sys.executable, str(TOOL), "--root", temp, *args],
                                        capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
