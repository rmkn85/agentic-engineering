import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


QUIET_RUN = Path(__file__).resolve().parents[1] / "quiet-run"


class QuietRunTests(unittest.TestCase):
    def test_process_success_does_not_accept_defective_product(self):
        for exit_code, output in [(0, "PRODUCT FAILED"), (0, "PRODUCT PASSED"), (7, "PRODUCT PASSED")]:
            with self.subTest(exit_code=exit_code, output=output), tempfile.TemporaryDirectory() as root:
                result = subprocess.run(
                    [str(QUIET_RUN), "--", sys.executable, "-c",
                     "import sys; print(sys.argv[1]); sys.exit(int(sys.argv[2]))", output, str(exit_code)],
                    env={**os.environ, "QUIET_RUN_LOG_DIR": root}, capture_output=True, text=True,
                    check=False)
                self.assertEqual(result.returncode, exit_code, result.stderr)
                status = "PASS" if exit_code == 0 else "FAIL"
                self.assertTrue(result.stdout.startswith(status + " code="))
                self.assertIn("scope=process-exit substantive_verdict=unassessed", result.stdout)
                path = next(Path(root).glob("*/manifest.json"))
                manifest = json.loads(path.read_text())
                self.assertEqual(manifest["status"], status)
                self.assertEqual(manifest["status_scope"], "process-exit")
                self.assertEqual(manifest["substantive_verdict"], "unassessed")
                log = path.parent / "full.log"
                self.assertEqual(log.read_text(), output + "\n")
                self.assertEqual(manifest["evidence"][-1]["sha256"], hashlib.sha256(log.read_bytes()).hexdigest())
                self.assertEqual((path.parent / "failure-excerpt.log").exists(), exit_code != 0)


if __name__ == "__main__":
    unittest.main()
