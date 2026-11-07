import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "check_guidance_budget.py"
CONFIG = {
    "default_reading": {"files": ["AGENTS.md", "CLAUDE.md"], "max_words": 5},
    "runtime": ["AGENTS.md", "CLAUDE.md", ".claude/*.md", "docs/*.md"],
    "evidence": ["tools/tests/*", "experiments/*.json"],
}


class GuidanceBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config(CONFIG)
        self.write("AGENTS.md", "one two three")
        self.write("docs/guide.md", "alpha beta")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "base")

    def config(self, data):
        self.write("configs/guidance-budget.json", json.dumps(data))

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              capture_output=True, text=True, check=False)

    def test_within_budget_passes(self):
        self.assertEqual(self.run_tool().returncode, 0)

    def test_default_reading_over_budget_fails(self):
        self.write("AGENTS.md", "one two three four five six")
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("budget 5", result.stderr)

    def test_always_loaded_host_file_counts_toward_default_reading(self):
        self.write("CLAUDE.md", "a b c")
        self.assertEqual(self.run_tool().returncode, 1)

    def test_raising_the_budget_fails_against_base(self):
        raised = json.loads(json.dumps(CONFIG))
        raised["default_reading"]["max_words"] = 500
        self.config(raised)
        self.write("AGENTS.md", "one two three " + "more " * 200)
        self.write("tools/tests/test_x.py", "")
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("budgets only go down", result.stderr)

    def test_prose_growth_without_evidence_fails(self):
        self.write("docs/guide.md", "alpha beta gamma delta")
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("grew by 2 words", result.stderr)

    def test_a_tool_or_config_change_is_not_evidence(self):
        self.write("docs/guide.md", "alpha beta gamma delta")
        self.write("tools/x.py", "")
        self.write("configs/other.json", "{}")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 1)

    def test_prose_growth_with_a_changed_test_passes(self):
        self.write("docs/guide.md", "alpha beta gamma delta")
        self.write("tools/tests/test_rule.py", "def test_rule(): pass")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)

    def test_shrinking_prose_passes_without_evidence(self):
        self.write("docs/guide.md", "alpha")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)

    def test_new_untracked_nested_and_host_rule_files_count(self):
        for rel in ("docs/deep/rule.md", ".claude/rules/rule.md", "DOCS/Upper.MD"):
            with self.subTest(rel=rel):
                self.write(rel, "new rule text")
                self.assertEqual(self.run_tool("--base", "HEAD").returncode, 1)
                (self.root / rel).unlink()


if __name__ == "__main__":
    unittest.main()
