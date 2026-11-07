import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "check_findings.py"
BASE = {"review": "blind-review-1", "date": "2026-11-07", "severity": "blocker", "target": "x.py",
        "problem": "p", "reproduction": "r"}


class CheckFindingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "tools" / "tests").mkdir(parents=True)
        (self.root / "tools" / "tests" / "test_x.py").write_text(
            "import unittest\nclass XTests(unittest.TestCase):\n    def test_guarded(self):\n        pass\n")
        (self.root / "validation" / "mutations").mkdir(parents=True)
        (self.root / "validation" / "mutations" / "m1.json").write_text(
            json.dumps({"tests": ["tools.tests.test_x.XTests.test_guarded"]}))
        (self.root / "validation" / "mutations" / "other.json").write_text(
            json.dumps({"tests": ["tools.tests.test_x.XTests.test_unrelated"]}))

    def ledger(self, *rows):
        (self.root / "validation" / "findings.jsonl").write_text(
            "".join(json.dumps({**BASE, **row}) + "\n" for row in rows))

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              capture_output=True, text=True, check=False)

    def test_fixed_with_existing_test_and_mutation_passes(self):
        self.ledger({"id": "F1", "status": "fixed", "tests": ["tools.tests.test_x.XTests.test_guarded"],
                     "mutation": "m1"})
        result = self.run_tool("--strict")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 fixed (1 with a mutation proof)", result.stdout)

    def test_fixed_without_test_or_with_missing_references_fails(self):
        for row in ({"id": "F1", "status": "fixed"},
                    {"id": "F1", "status": "fixed", "tests": ["tools.tests.test_x.XTests.test_gone"]},
                    {"id": "F1", "status": "fixed", "tests": ["tools.tests.test_x.XTests.test_guarded"],
                     "mutation": "gone"}):
            self.ledger(row)
            self.assertEqual(self.run_tool().returncode, 1, row)

    def test_fixed_findings_cite_test_methods_not_classes(self):
        self.ledger({"id": "F1", "status": "fixed", "severity": "minor", "tests": ["tools.tests.test_x.XTests"]})
        self.assertEqual(self.run_tool().returncode, 1)
        self.ledger({"id": "F1", "status": "fixed", "severity": "minor",
                     "tests": ["tools.tests.test_x.XTests.test_guarded"]})
        self.assertEqual(self.run_tool().returncode, 0)

    def test_fixed_blocker_needs_a_mutation_or_a_reason(self):
        row = {"id": "F1", "status": "fixed", "tests": ["tools.tests.test_x.XTests.test_guarded"]}
        self.ledger(row)
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("needs a mutation proof", result.stderr)
        self.ledger({**row, "note": "the fix deletes a code path, so there is nothing to mutate"})
        self.assertEqual(self.run_tool().returncode, 0)

    def test_addressed_and_declined_need_a_note(self):
        for status in ("addressed", "declined"):
            self.ledger({"id": "F1", "status": status})
            self.assertEqual(self.run_tool().returncode, 1, status)
            self.ledger({"id": "F1", "status": status, "note": "."})
            self.assertEqual(self.run_tool().returncode, 1, status)
            self.ledger({"id": "F1", "status": status, "note": "kept on purpose for compatibility"})
            self.assertEqual(self.run_tool().returncode, 0, status)

    def test_borrowed_mutation_does_not_prove_a_finding(self):
        self.ledger({"id": "F1", "status": "fixed", "tests": ["tools.tests.test_x.XTests.test_guarded"],
                     "mutation": "other"})
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertIn("proves other tests", result.stderr)

    def test_open_findings_fail_only_in_strict_mode(self):
        self.ledger({"id": "F1", "status": "open"})
        self.assertEqual(self.run_tool().returncode, 0)
        self.assertEqual(self.run_tool("--strict").returncode, 1)

    def test_malformed_rows_and_duplicates_fail(self):
        (self.root / "validation" / "findings.jsonl").write_text("not json\n")
        self.assertEqual(self.run_tool().returncode, 1)
        self.ledger({"id": "F1", "status": "open"}, {"id": "F1", "status": "open"})
        self.assertIn("duplicate", self.run_tool().stderr)
        self.ledger({"id": "F1", "status": "maybe"})
        self.assertEqual(self.run_tool().returncode, 1)


if __name__ == "__main__":
    unittest.main()
