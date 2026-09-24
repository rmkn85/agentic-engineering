import hashlib
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


if __name__ == "__main__":
    unittest.main()
