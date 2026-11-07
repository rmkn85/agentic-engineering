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
        self.write("tools/tests/test_rule.py", "def test_rule():\n    assert True\n")
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


class GuidanceBudgetTamperingTests(GuidanceBudgetTests):
    def test_loosening_the_config_does_not_hide_growth(self):
        loose = {"default_reading": {"files": [], "max_words": 5}, "runtime": [], "evidence": ["docs/*"]}
        self.config(loose)
        self.write("AGENTS.md", "one two three " + "more " * 300)
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("budget 5", result.stderr)

    def test_imported_files_count_as_default_reading(self):
        self.write("CLAUDE.md", "@rules/extra.txt")
        self.write("rules/extra.txt", "w " * 50)
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("default reading", result.stderr)

    def test_code_span_mentions_are_not_imports(self):
        self.write("CLAUDE.md", "see `@rules/extra.txt`")
        self.write("rules/extra.txt", "w " * 50)
        self.assertNotIn("default reading is", self.run_tool().stderr)

    def test_vacuous_evidence_does_not_count(self):
        self.write("docs/guide.md", "alpha beta " + "rule " * 50)
        self.write("tools/tests/test_existing.py", "def test_old(): pass\n")
        self.git("add", ".")
        self.git("-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "test")
        self.write("docs/guide.md", "alpha beta " + "rule " * 80)
        with open(self.root / "tools/tests/test_existing.py", "a") as handle:
            handle.write("\n\n")
        self.write("tools/tests/empty.txt", "")
        self.write("tools/tests/notes.txt", "remember the rule\n")
        self.write("experiments/result.json", "{}")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 1)
        with open(self.root / "tools/tests/test_existing.py", "a") as handle:
            handle.write("def test_rule():\n    assert True\n")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)


class GuidanceBudgetProportionTests(unittest.TestCase):
    setUp = GuidanceBudgetTests.setUp
    config, git, write, run_tool = (GuidanceBudgetTests.config, GuidanceBudgetTests.git,
                                    GuidanceBudgetTests.write, GuidanceBudgetTests.run_tool)

    def test_one_trivial_test_cannot_pay_for_a_large_rule_text(self):
        self.write("docs/guide.md", "alpha beta " + "rule " * 2400)
        self.write("tools/tests/test_trivial.py", "def test_trivial():\n    assert True\n")
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("pay for 150", result.stderr)

    def test_proportionate_growth_passes(self):
        self.write("docs/guide.md", "alpha beta " + "rule " * 100)
        self.write("tools/tests/test_rule.py", "def test_rule():\n    assert True\n")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)

    def test_test_functions_that_assert_nothing_pay_nothing(self):
        self.write("docs/guide.md", "alpha beta " + "rule " * 100)
        self.write("tools/tests/test_noop.py", "def test_noop():\n    pass\n")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 1)
        self.write("tools/tests/test_noop.py", "def check(x):\n    assert x\n\ndef test_helper():\n    check(1)\n")
        self.assertEqual(self.run_tool("--base", "HEAD").returncode, 0)

    def test_raising_the_price_per_test_does_not_pay_for_prose(self):
        priced = json.loads(json.dumps(CONFIG))
        priced["words_per_evidence"] = 100000
        self.config(priced)
        self.write("docs/guide.md", "alpha beta " + "rule " * 2400)
        self.write("tools/tests/test_rule.py", "def test_rule():\n    assert True\n")
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("pay for 150", result.stderr)

    def test_narrowing_what_is_measured_fails(self):
        narrowed = json.loads(json.dumps(CONFIG))
        narrowed["runtime"] = ["AGENTS.md", "CLAUDE.md", ".claude/*.md"]
        self.config(narrowed)
        result = self.run_tool("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("narrows what is measured", result.stderr)


if __name__ == "__main__":
    unittest.main()
