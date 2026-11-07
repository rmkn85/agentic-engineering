import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1]
TOOL = TOOLS / "run_trial.py"
GIT = ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t"]


class RunTrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.root = base / "repo"
        (self.root / "tools" / "tests").mkdir(parents=True)
        shutil.copy(TOOLS / "check_guidance_budget.py", self.root / "tools")
        (self.root / "AGENTS.md").write_text("# AGENTS.md\n\nWrite a goal record first.\n")
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n\nClaude note.\n")
        scenarios = self.root / "validation" / "trials" / "scenarios"
        scenarios.mkdir(parents=True)
        (scenarios / "demo.json").write_text(json.dumps(
            {"id": "demo", "claim": "c", "task": "Add a rule.", "checks": ["goal-record", "added-test"]}))
        subprocess.run(GIT + ["init", "-q"], cwd=self.root, check=True)
        subprocess.run(GIT + ["add", "."], cwd=self.root, check=True)
        subprocess.run(GIT + ["commit", "-qm", "base"], cwd=self.root, check=True)
        self.out = base / "clone"

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              capture_output=True, text=True, check=False)

    def test_guided_prompt_carries_auto_loaded_instructions_and_task(self):
        result = self.run_tool("prepare", "demo", "--arm", "guided", "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Write a goal record first.", result.stdout)
        self.assertIn("Claude note.", result.stdout)
        self.assertIn("Task:\nAdd a rule.", result.stdout)
        self.assertIn(str(self.out), result.stdout)

    def test_unguided_arm_has_no_instructions_in_prompt_or_clone(self):
        result = self.run_tool("prepare", "demo", "--arm", "unguided", "--out", str(self.out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("goal record", result.stdout)
        self.assertNotIn("goal record", (self.out / "AGENTS.md").read_text())
        self.assertFalse((self.out / "CLAUDE.md").exists())

    def test_score_records_what_the_agent_actually_did(self):
        self.run_tool("prepare", "demo", "--arm", "guided", "--out", str(self.out))
        idle = json.loads(self.run_tool("score", str(self.out), "--agent", "none").stdout)
        self.assertEqual((idle["passed"], idle["total"]), (0, 2))
        (self.out / ".agent").mkdir()
        (self.out / ".agent" / "goal.json").write_text(json.dumps({"goal": "g", "acceptance": [{"id": "a"}]}))
        (self.out / "tools" / "tests").mkdir(parents=True, exist_ok=True)
        (self.out / "tools" / "tests" / "test_rule.py").write_text("def test_rule():\n    assert True\n")
        done = json.loads(self.run_tool("score", str(self.out), "--agent", "worker").stdout)
        self.assertEqual(done["checks"], {"goal-record": True, "added-test": True})
        rows = (self.root / "validation" / "trials" / "results.jsonl").read_text().splitlines()
        self.assertEqual([json.loads(r)["agent"] for r in rows], ["none", "worker"])

    def test_prose_only_change_is_not_an_added_test(self):
        self.run_tool("prepare", "demo", "--arm", "guided", "--out", str(self.out))
        (self.out / "AGENTS.md").write_text("# AGENTS.md\n\nNever commit large files. " * 20)
        (self.out / "tools" / "tests").mkdir(parents=True, exist_ok=True)
        (self.out / "tools" / "tests" / "notes.txt").write_text("remember the rule\n")
        result = json.loads(self.run_tool("score", str(self.out), "--agent", "prose").stdout)
        self.assertFalse(result["checks"]["added-test"])

    def test_suite_check_counts_only_new_failures(self):
        (self.root / "tools" / "tests" / "test_base.py").write_text(
            "import unittest\nclass B(unittest.TestCase):\n    def test_old(self):\n        self.fail('was broken')\n")
        scenario = self.root / "validation" / "trials" / "scenarios" / "demo.json"
        scenario.write_text(json.dumps({"id": "demo", "claim": "c", "task": "t", "checks": ["suite"]}))
        subprocess.run(GIT + ["add", "."], cwd=self.root, check=True)
        subprocess.run(GIT + ["commit", "-qm", "suite"], cwd=self.root, check=True)
        self.run_tool("prepare", "demo", "--arm", "guided", "--out", str(self.out))
        same = json.loads(self.run_tool("score", str(self.out), "--agent", "a").stdout)
        self.assertTrue(same["checks"]["suite"])  # the old failure is not the agent's
        (self.out / "tools" / "tests" / "test_new.py").write_text(
            "import unittest\nclass N(unittest.TestCase):\n    def test_new(self):\n        self.fail('agent broke it')\n")
        worse = json.loads(self.run_tool("score", str(self.out), "--agent", "b").stdout)
        self.assertFalse(worse["checks"]["suite"])

    def test_existing_directory_and_unknown_checks_are_refused(self):
        self.out.mkdir()
        self.assertEqual(self.run_tool("prepare", "demo", "--arm", "guided", "--out", str(self.out)).returncode, 1)
        scenario = self.root / "validation" / "trials" / "scenarios" / "demo.json"
        scenario.write_text(json.dumps({"id": "demo", "task": "t", "checks": ["rm -rf /"]}))
        result = self.run_tool("prepare", "demo", "--arm", "guided", "--out", str(self.out) + "2")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown", result.stderr)


if __name__ == "__main__":
    unittest.main()
