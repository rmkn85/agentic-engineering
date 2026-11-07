import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "check_guidance_budget.py"
CONFIG = {
    "default_reading": {"files": ["AGENTS.md"], "max_words": 5},
    "runtime": ["AGENTS.md", "docs/*.md"],
    "mechanism": ["tools/*"],
}


class GuidanceBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "configs").mkdir()
        (self.root / "configs" / "guidance-budget.json").write_text(json.dumps(CONFIG))
        (self.root / "docs").mkdir()
        self.write("AGENTS.md", "one two three")
        self.write("docs/guide.md", "alpha beta")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "base")

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

    def test_prose_growth_without_mechanism_fails(self):
        self.write("docs/guide.md", "alpha beta gamma delta")
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("grew by 2 words", result.stderr)

    def test_prose_growth_with_mechanism_passes(self):
        self.write("docs/guide.md", "alpha beta gamma delta")
        self.write("tools/check.py", "print('enforced')")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)

    def test_shrinking_prose_passes_without_mechanism(self):
        self.write("docs/guide.md", "alpha")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)

    def test_nested_runtime_docs_count(self):
        self.write("docs/deep/rule.md", "new rule text")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 1)


if __name__ == "__main__":
    unittest.main()
