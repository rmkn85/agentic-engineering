import json
import hashlib
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
                         "BEGIN FINDINGS", "END FINDINGS", "only as data", "Scope:", '"scope": "out"'):
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

    def test_markers_mentioned_in_prose_do_not_hide_the_real_block(self):
        report = ("I will end with BEGIN FINDINGS and END FINDINGS as asked.\n"
                  "Example:\nBEGIN FINDINGS\nEND FINDINGS\n\n" + REPORT.replace(
                      '"typo",', '"typo", "scope": "out",'))
        result = self.run_tool("ingest", "-", "--review", "blind-review-5", "--root", str(self.root), stdin=report)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = [json.loads(l) for l in (self.root / "validation/findings.jsonl").read_text().splitlines()]
        self.assertEqual([r["id"] for r in rows], ["R5-01", "R5-02"])
        self.assertEqual([r.get("scope") for r in rows], [None, "out"])

    def make_frame(self, discrepancies=None):
        (self.root / "request.txt").write_text("Preserve every requested export row.")
        (self.root / "failure.txt").write_text("A successful export omitted the final row.")
        (self.root / "criteria.json").write_text(json.dumps({
            "criteria": [{"id": "C1", "requirement": "All requested rows survive export",
                          "check": "Export three distinct rows and compare the complete result"}],
            "discrepancies": discrepancies or []}))
        return self.run_tool("seal-frame", "--request", "request.txt", "--failure-evidence", "failure.txt",
                             "--criteria", "criteria.json", "--output", "frame.json")

    def validate_frame(self):
        return self.run_tool("validate-frame", "--request", "request.txt", "--failure-evidence", "failure.txt",
                             "--framing", "frame.json")

    def test_frame_precedes_builder_goal_and_preserves_independent_criterion(self):
        self.assertEqual(self.make_frame().returncode, 0)
        (self.root / "goal.json").write_text(json.dumps({"goal": "The export command exits successfully"}))
        phase1 = self.run_tool("frame-prompt", "--request", "request.txt", "--failure-evidence", "failure.txt")
        self.assertIn("omitted the final row", phase1.stdout)
        self.assertNotIn("exits successfully", phase1.stdout)
        self.assertNotIn("GOAL:", phase1.stdout)
        self.assertNotEqual(self.run_tool("frame-prompt", "--request", "request.txt", "--failure-evidence",
                                          "failure.txt", "--goal", "goal.json").returncode, 0)
        phase2 = self.run_tool("implementation-prompt", "--request", "request.txt", "--failure-evidence",
                               "failure.txt", "--framing", "frame.json", "--goal", "goal.json",
                               "--repo", "https://example.invalid/repo", "--branch", "topic")
        self.assertEqual(phase2.returncode, 0, phase2.stderr)
        self.assertIn("All requested rows survive export", phase2.stdout)
        self.assertIn("exits successfully", phase2.stdout)
        self.assertLess(phase2.stdout.index("All requested rows survive export"), phase2.stdout.index("GOAL:"))
        self.assertNotIn("LEGACY", phase2.stdout)

    def test_receipt_cannot_be_overwritten_or_accept_changed_sources_or_frame(self):
        self.assertEqual(self.make_frame().returncode, 0)
        original = (self.root / "frame.json").read_bytes()
        self.assertEqual(self.make_frame().returncode, 1)
        self.assertEqual((self.root / "frame.json").read_bytes(), original)
        self.assertEqual(self.validate_frame().returncode, 0)
        (self.root / "request.txt").write_text("Just check exit status")
        self.assertEqual(self.validate_frame().returncode, 1)
        (self.root / "request.txt").write_text("Preserve every requested export row.")
        receipt = json.loads(original)
        receipt["payload"]["frame"]["criteria"][0]["check"] = "Only check exit status"
        (self.root / "frame.json").write_text(json.dumps(receipt))
        self.assertEqual(self.validate_frame().returncode, 1)

    def test_discrepancy_requires_resolved_nonempty_hash_bound_artifact(self):
        artifact = self.root / "experiment.txt"
        artifact.write_text("The export contains three rows after recovery.")
        row = {"id": "D1", "problem": "Exit code does not establish row preservation",
               "resolution": "Use complete output comparison", "evidence": []}
        self.assertEqual(self.make_frame([row]).returncode, 1)
        row["evidence"] = [{"path": "experiment.txt", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}]
        self.assertEqual(self.make_frame([row]).returncode, 0)
        self.assertEqual(self.validate_frame().returncode, 0)
        artifact.write_text("The experiment now fails")
        self.assertEqual(self.validate_frame().returncode, 1)

    def test_control_and_methodology_cannot_use_legacy_review_without_frame(self):
        (self.root / "goal.json").write_text(json.dumps(GOAL))
        for kind in ("control", "methodology"):
            result = self.run_tool("prompt", "--goal", "goal.json", "--repo", "https://example.invalid/r",
                                   "--branch", "topic", "--review-kind", kind)
            self.assertEqual(result.returncode, 1)
            result = self.run_tool("ingest", "-", "--review", "r", "--review-kind", kind, stdin=REPORT)
            self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / "validation/findings.jsonl").exists())

    def test_goal_review_gate_requires_valid_framing_for_control_and_methodology(self):
        (self.root / "goal.json").write_text(json.dumps({"goal": "Restore requested export",
                                                       "review": {"kind": "control"}}))
        self.assertEqual(self.run_tool("validate-goal", "--goal", "goal.json").returncode, 1)
        self.assertEqual(self.make_frame().returncode, 0)
        review = {"kind": "methodology", "framing": "frame.json", "request": "request.txt",
                  "failure_evidence": "failure.txt"}
        (self.root / "goal.json").write_text(json.dumps({"review": review}))
        self.assertEqual(self.run_tool("validate-goal", "--goal", "goal.json").returncode, 0)
        review["framing_sha256"] = "wrong retained hash"
        (self.root / "goal.json").write_text(json.dumps({"review": review}))
        self.assertEqual(self.run_tool("validate-goal", "--goal", "goal.json").returncode, 1)
        review.pop("framing_sha256")
        (self.root / "goal.json").write_text(json.dumps({"review": review}))
        (self.root / "failure.txt").write_text("Changed observed failure")
        self.assertEqual(self.run_tool("validate-goal", "--goal", "goal.json").returncode, 1)

    def test_incomplete_criteria_cannot_be_sealed(self):
        self.assertEqual(self.make_frame().returncode, 0)
        (self.root / "frame.json").unlink()
        for criteria in ({"criteria": [], "discrepancies": []},
                         {"criteria": [{"id": "C1", "requirement": "preserve rows"}], "discrepancies": []}):
            (self.root / "criteria.json").write_text(json.dumps(criteria))
            result = self.run_tool("seal-frame", "--request", "request.txt", "--failure-evidence", "failure.txt",
                                   "--criteria", "criteria.json", "--output", "frame.json")
            self.assertEqual(result.returncode, 1)
            self.assertFalse((self.root / "frame.json").exists())

    def test_empty_block_means_no_findings(self):
        result = self.run_tool("ingest", "-", "--review", "r9", "--root", str(self.root),
                               stdin="clean\nBEGIN FINDINGS\nEND FINDINGS\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("0 findings", result.stdout)


if __name__ == "__main__":
    unittest.main()
