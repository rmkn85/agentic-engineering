import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "prove_guards.py"
RULE = "def allowed(x):\n    return x != 'bad'\n"
GOOD_TEST = ("import unittest\nfrom rule import allowed\n"
             "class T(unittest.TestCase):\n    def test_bad_refused(self):\n        self.assertFalse(allowed('bad'))\n")
WEAK_TEST = ("import unittest\nfrom rule import allowed\n"
             "class T(unittest.TestCase):\n    def test_good_allowed(self):\n        self.assertTrue(allowed('ok'))\n")


class ProveGuardsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel, text in (("rule.py", RULE), ("test_good.py", GOOD_TEST), ("test_weak.py", WEAK_TEST)):
            (self.root / rel).write_text(text)
        (self.root / "validation" / "mutations").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def mutation(self, name, tests, find="return x != 'bad'"):
        (self.root / "validation" / "mutations" / f"{name}.json").write_text(json.dumps(
            {"id": name, "rule": "bad is refused", "file": "rule.py", "find": find,
             "replace": "return True", "tests": tests}))

    def run_tool(self):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root)],
                              capture_output=True, text=True, check=False)

    def test_guarding_test_catches_the_mutation(self):
        self.mutation("m", ["test_good.T.test_bad_refused"])
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("caught", result.stdout)

    def test_test_that_does_not_guard_the_rule_is_reported(self):
        self.mutation("m", ["test_weak.T.test_good_allowed"])
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("survived", result.stdout)

    def test_stale_mutation_is_reported(self):
        self.mutation("m", ["test_good.T.test_bad_refused"], find="text that is gone")
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("stale", result.stdout)

    def test_missing_test_name_is_not_a_catch(self):
        self.mutation("m", ["test_good.T.test_renamed_away"])
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("broken", result.stdout)

    def test_syntax_breaking_mutation_is_not_a_catch(self):
        self.mutation("m", ["test_good.T.test_bad_refused"])
        path = self.root / "validation" / "mutations" / "m.json"
        data = json.loads(path.read_text())
        data["replace"] = "return = = True"
        path.write_text(json.dumps(data))
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("breaks the code", result.stdout)

    def test_error_only_failure_is_not_a_catch(self):
        self.mutation("m", ["test_good.T.test_bad_refused"])
        path = self.root / "validation" / "mutations" / "m.json"
        data = json.loads(path.read_text())
        data["replace"] = "return undefined_name"
        path.write_text(json.dumps(data))
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("only errored", result.stdout)

    def test_original_repository_is_never_modified(self):
        self.mutation("m", ["test_good.T.test_bad_refused"])
        self.run_tool()
        self.assertEqual((self.root / "rule.py").read_text(), RULE)


if __name__ == "__main__":
    unittest.main()
