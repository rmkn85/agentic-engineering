import hashlib
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1]
RECALL = TOOLS / "observation-recall.py"
QUIET_RUN = TOOLS / "quiet-run"


class ObservationRecallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        result = subprocess.run(
            [str(QUIET_RUN), "--", sys.executable, "-c", "import sys; print('alpha'); print('target'); print('omega'); sys.exit(7)"],
            env={**os.environ, "QUIET_RUN_LOG_DIR": str(self.root)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 7, result.stderr)
        self.manifest_path = next(self.root.glob("*/manifest.json"))
        self.manifest = json.loads(self.manifest_path.read_text())

    def run_recall(self, *args):
        return subprocess.run(
            [sys.executable, str(RECALL), str(self.manifest_path), *args],
            capture_output=True,
            check=False,
        )

    def test_receipts_and_exact_bounded_recall(self):
        entries = {item["id"]: item for item in self.manifest["evidence"]}
        for item in entries.values():
            self.assertEqual(item["sha256"], hashlib.sha256((self.manifest_path.parent / item["ref"]).read_bytes()).hexdigest())
        self.assertEqual(self.run_recall("--lines", "2:1").stdout, b"target\n")
        self.assertEqual(self.run_recall("--bytes", "6:6").stdout, b"target")
        self.assertEqual(self.run_recall("--find", "target").stdout, b"2:target\n")
        self.assertEqual(self.run_recall("--artifact", "failure-excerpt", "--lines", "2:1").stdout, b"target\n")

    def test_tampered_evidence_is_rejected(self):
        (self.manifest_path.parent / "full.log").write_text("changed\n")
        result = self.run_recall("--lines", "1:1")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"hash mismatch", result.stderr)
        self.assertFalse(result.stdout)

    def test_success_bundle_has_verifiable_receipt(self):
        result = subprocess.run(
            [str(QUIET_RUN), "--", sys.executable, "-c", "print('passed')"],
            env={**os.environ, "QUIET_RUN_LOG_DIR": str(self.root / "success")},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = next((self.root / "success").glob("*/manifest.json"))
        recalled = subprocess.run(
            [sys.executable, str(RECALL), str(manifest), "--lines", "1:1"],
            capture_output=True,
            check=False,
        )
        self.assertEqual(recalled.returncode, 0, recalled.stderr)
        self.assertEqual(recalled.stdout, b"passed\n")

    def test_escape_and_unbounded_output_are_rejected(self):
        self.manifest["evidence"][-1]["ref"] = "../other.log"
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.assertIn(b"must be a file in the bundle", self.run_recall("--lines", "1:1").stderr)
        self.manifest["evidence"][-1]["ref"] = "full.log"
        self.manifest_path.write_text(json.dumps(self.manifest))
        result = self.run_recall("--lines", "1:3", "--max-output-bytes", "4")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)

    def replace_log(self, data):
        (self.manifest_path.parent / "full.log").write_bytes(data)
        entry = self.manifest["evidence"][-1]
        entry["sha256"] = hashlib.sha256(data).hexdigest()
        self.manifest_path.write_text(json.dumps(self.manifest))

    def receipt(self, *args):
        result = self.run_recall("--json", *args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_json_find_exact_limit_and_later_match(self):
        self.replace_log(b"hit\nmiss\nhit\n")
        exact = self.receipt("--find", "hit", "--max-matches", "2")
        self.assertTrue(exact["coverage"]["whole_artifact_search_complete"])
        self.assertIsNone(exact["continuation_argv"])
        self.assertEqual(exact["coverage"]["artifact"], "partial")
        self.replace_log(b"hit\nmiss\nhit\nhit\n")
        first = self.receipt("--find", "hit", "--max-matches", "2")
        self.assertFalse(first["coverage"]["search_complete"])
        self.assertEqual(first["returned"]["line_numbers"], [1, 3])
        second = subprocess.run([sys.executable, str(RECALL), *first["continuation_argv"]],
                                capture_output=True, check=False)
        self.assertEqual(second.returncode, 0, second.stderr)
        receipt = json.loads(second.stdout)
        self.assertEqual(base64.b64decode(receipt["output"]["data"]), b"4:hit\n")
        self.assertTrue(receipt["coverage"]["search_complete"])
        self.assertFalse(receipt["coverage"]["whole_artifact_search_complete"])
        self.assertEqual(self.run_recall("--find", "hit", "--max-matches", "2").stdout,
                         b"1:hit\n3:hit\n")

    def test_json_absence_scope_and_continuation_identity(self):
        absent = self.receipt("--find", "missing")
        self.assertTrue(absent["coverage"]["whole_artifact_search_complete"])
        partial = self.receipt("--find", "alpha", "--start-line", "2")
        self.assertFalse(partial["coverage"]["whole_artifact_search_complete"])
        self.assertEqual(base64.b64decode(partial["output"]["data"]), b"")
        self.assertEqual(self.run_recall("--json", "--find", "alpha", "--start-line", "99").returncode, 2)
        self.assertEqual(self.run_recall("--json", "--bytes", "99:1").returncode, 2)
        self.assertEqual(self.run_recall("--json", "--lines", "99:1").returncode, 2)
        self.replace_log(b"hit\nhit\n")
        first = self.receipt("--find", "hit", "--max-matches", "1")
        self.replace_log(b"changed\n")
        result = subprocess.run([sys.executable, str(RECALL), *first["continuation_argv"]],
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"identity mismatch", result.stderr)
        self.assertFalse(result.stdout)

    def test_json_search_byte_limit_and_bounded_long_line(self):
        self.replace_log(b"hit\nhit\n")
        exact = self.receipt("--find", "hit", "--max-output-bytes", "12")
        self.assertEqual(exact["coverage"]["selection"], "complete")
        capped = self.receipt("--find", "hit", "--max-output-bytes", "6")
        self.assertEqual(capped["coverage"]["selection"], "partial")
        self.assertEqual(base64.b64decode(capped["output"]["data"]), b"1:hit\n")
        self.replace_log(b"x" * 100 + b"\nhit\n")
        result = self.run_recall("--json", "--find", "absent", "--max-output-bytes", "8")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(result.stdout)
        self.assertIn(b"use --bytes", result.stderr)

    def test_json_empty_artifact_and_unterminated_line(self):
        self.replace_log(b"")
        self.assertEqual(self.receipt("--lines", "1:1")["coverage"]["artifact"], "complete")
        self.assertTrue(self.receipt("--find", "absent")["coverage"]["whole_artifact_search_complete"])
        self.replace_log("猫".encode("utf-8"))
        found = self.receipt("--find", "猫", "--max-matches", "1")
        self.assertEqual(base64.b64decode(found["output"]["data"]), "1:猫".encode("utf-8"))
        self.assertTrue(found["coverage"]["whole_artifact_search_complete"])
        self.assertEqual(self.receipt("--lines", "1:1")["coverage"]["artifact"], "complete")

    def test_json_byte_caps_preserve_multibyte_and_continue(self):
        data = "é猫z".encode("utf-8")
        self.replace_log(data)
        first = self.receipt("--bytes", "0:20", "--max-output-bytes", "3")
        self.assertEqual(base64.b64decode(first["output"]["data"]), data[:3])
        self.assertEqual(first["coverage"]["selection"], "partial")
        result = subprocess.run([sys.executable, str(RECALL), *first["continuation_argv"]],
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        second = json.loads(result.stdout)
        self.assertEqual(base64.b64decode(second["output"]["data"]), data[3:])
        self.assertEqual(second["coverage"]["selection"], "complete")
        self.assertIsNone(second["continuation_argv"])
        self.assertIsNone(second["coverage"]["search_complete"])
        self.assertEqual(self.run_recall("--bytes", "0:20", "--max-output-bytes", "3").returncode, 2)
        whole = self.receipt("--bytes", "0:20")
        self.assertEqual(whole["coverage"]["artifact"], "complete")

    def test_json_line_output_cap_and_symlink_rejection(self):
        self.replace_log(b"one\ntwo\nthree\n")
        first = self.receipt("--lines", "1:3", "--max-output-bytes", "8")
        self.assertEqual(base64.b64decode(first["output"]["data"]), b"one\ntwo\n")
        self.assertEqual(first["coverage"]["selection"], "partial")
        result = subprocess.run([sys.executable, str(RECALL), *first["continuation_argv"]],
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(base64.b64decode(json.loads(result.stdout)["output"]["data"]), b"three\n")
        artifact = self.manifest_path.parent / "full.log"
        target = self.root / "target"
        artifact.rename(target)
        artifact.symlink_to(target)
        result = self.run_recall("--json", "--lines", "1:1")
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"symlink", result.stderr)

    def test_buried_failure_remains_retrievable_beyond_tail(self):
        result = subprocess.run(
            [str(QUIET_RUN), "--", sys.executable, "-c",
             "import sys; print('FAIL exact_id=CASE-079 retry=false latency=125 ms; cause uncertain unless cache warm'); "
             "print('no measurements supplied'); print('measured_count=0; delta=-2 ms'); "
             "print('unit=PASS; render=UNRUN; device=UNRUN; integration=UNRUN'); "
             "[print('routine progress') for _ in range(300)]; sys.exit(7)"],
            env={**os.environ, "QUIET_RUN_LOG_DIR": str(self.root / "buried")},
            capture_output=True, check=False)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.manifest_path = next((self.root / "buried").glob("*/manifest.json"))
        excerpt = self.manifest_path.parent / "failure-excerpt.log"
        self.assertNotIn(b"CASE-079", excerpt.read_bytes())
        recalled = self.run_recall("--find", "CASE-079")
        self.assertEqual(recalled.returncode, 0, recalled.stderr)
        self.assertEqual(recalled.stdout,
                         b"1:FAIL exact_id=CASE-079 retry=false latency=125 ms; cause uncertain unless cache warm\n")
        self.assertEqual(self.run_recall("--lines", "2:3").stdout,
                         b"no measurements supplied\nmeasured_count=0; delta=-2 ms\n"
                         b"unit=PASS; render=UNRUN; device=UNRUN; integration=UNRUN\n")


if __name__ == "__main__":
    unittest.main()
