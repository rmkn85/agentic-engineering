from pathlib import Path
import subprocess
import sys
import tempfile
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
        self.git("branch", "done-topic")
        self.git("worktree", "add", "-q", str(Path(self.temp.name) / "wt"), "-b", "live")
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 1)
        self.assertIn("merged branch not deleted: done-topic", result.stdout)
        self.assertIn("extra worktree", result.stdout)

    def test_dated_process_records_and_tracked_scratch(self):
        self.commit("docs/plans/2026-10-28-rollout.md", "x")
        self.commit("handoff-20261101.md", "x")
        self.commit(".tmp/run/out.txt", "x")
        self.commit("build.log", "x")
        result = self.run_tool()
        self.assertEqual(result.returncode, 0)  # report mode never fails
        for expected in ("docs/plans/2026-10-28-rollout.md", "handoff-20261101.md", ".tmp/run/out.txt", "build.log"):
            self.assertIn(expected, result.stdout)

    def test_local_trunk_is_not_flagged_against_its_remote(self):
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        self.git("checkout", "-q", "-b", "topic")
        self.assertIn("clean", self.run_tool("--strict", "--base", "origin/main").stdout)

    def test_dated_research_and_evidence_are_not_process_records(self):
        self.commit("references/research-2026-09/README.md", "x")
        self.commit("experiments/2026-09-20-trial.md", "x")
        self.assertIn("clean", self.run_tool("--strict").stdout)


if __name__ == "__main__":
    unittest.main()
