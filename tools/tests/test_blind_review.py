import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "blind_review.py"
GOAL = {"goal": "Exports are correct", "acceptance": [
    {"id": "t", "check": "export tests pass", "run": "check"},
    {"id": "o", "check": "owner accepts layout", "status": "pending"}]}
REPORT = """Findings below.
BEGIN FINDINGS
{"severity": "blocker", "target": "x.py:3", "problem": "export drops rows", "reproduction": "ran x; 2 of 3 rows"}
{"severity": "minor", "target": "y.py:9", "problem": "typo", "reproduction": "read y.py"}
END FINDINGS
"""


class BlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(TOOL), *args], input=stdin, cwd=self.root,
                              capture_output=True, text=True, check=False)

    def test_prompt_carries_goal_and_checks_but_no_reasoning(self):
        (self.root / "goal.json").write_text(json.dumps(GOAL))
        result = self.run_tool("prompt", "--goal", "goal.json", "--repo", "https://example.invalid/r",
                               "--branch", "topic")
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in ("GOAL: Exports are correct", "export tests pass (make check)",
                         "owner accepts layout (manual)", "do NOT read the pull request description",
                         "BEGIN FINDINGS", "END FINDINGS"):
            self.assertIn(expected, result.stdout)

    def test_ingest_appends_open_findings_with_new_ids(self):
        result = self.run_tool("ingest", "-", "--review", "blind-review-3", "--root", str(self.root), stdin=REPORT)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(l) for l in (self.root / "validation/findings.jsonl").read_text().splitlines()]
        self.assertEqual([r["id"] for r in rows], ["R3-01", "R3-02"])
        self.assertTrue(all(r["status"] == "open" for r in rows))
        again = self.run_tool("ingest", "-", "--review", "blind-review-3", "--root", str(self.root), stdin=REPORT)
        self.assertEqual(again.returncode, 0)
        ids = [json.loads(l)["id"] for l in (self.root / "validation/findings.jsonl").read_text().splitlines()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ingested_findings_satisfy_the_ledger_checker(self):
        self.run_tool("ingest", "-", "--review", "blind-review-3", "--root", str(self.root), stdin=REPORT)
        checker = Path(__file__).resolve().parents[1] / "check_findings.py"
        result = subprocess.run([sys.executable, str(checker), "--root", str(self.root)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 open", result.stdout)

    def test_report_without_block_or_with_incomplete_finding_is_rejected(self):
        self.assertEqual(self.run_tool("ingest", "-", "--review", "r", stdin="no markers").returncode, 1)
        bad = 'BEGIN FINDINGS\n{"severity": "blocker", "target": "x"}\nEND FINDINGS'
        self.assertEqual(self.run_tool("ingest", "-", "--review", "r", stdin=bad).returncode, 1)

    def test_empty_block_means_no_findings(self):
        result = self.run_tool("ingest", "-", "--review", "r9", "--root", str(self.root),
                               stdin="clean\nBEGIN FINDINGS\nEND FINDINGS\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("0 findings", result.stdout)


if __name__ == "__main__":
    unittest.main()
