"""The host-neutral allowlist names reviewed activities only, and host adapters match it."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "allowlist.py"
SOURCE = json.loads((ROOT / "configs" / "allowed-activities.json").read_text(encoding="utf-8"))
MAKE_TARGETS = set(re.findall(r"^([a-z][a-z0-9_-]*):", (ROOT / "Makefile").read_text(encoding="utf-8"), re.M))
# External effects stay with per-use approval: they are never allowlisted.
EXTERNAL = {"push", "gh", "curl", "wget", "sudo", "rm", "reset", "clean", "apply"}


class AllowlistTests(unittest.TestCase):
    def test_activities_are_specific_local_and_real(self):
        for activity in SOURCE["activities"]:
            command = activity["command"]
            with self.subTest(command=command):
                self.assertIn(activity["match"], ("exact", "prefix"))
                self.assertGreaterEqual(len(command), 2, "a bare program name is blanket access")
                parts = {piece for word in command for piece in re.split(r"[-_/.]", word)}
                self.assertFalse(EXTERNAL & parts, "external effects need per-use approval")
                self.assertFalse(any("*" in w for w in command), "no wildcards inside an activity")
                if command[0] == "make":
                    self.assertEqual(activity["match"], "exact", "make takes extra goals: list exact targets")
                    self.assertIn(command[1], MAKE_TARGETS)
                if command[0] == "python3" and command[1] != "-m":
                    self.assertTrue((ROOT / command[1]).is_file(), command[1])

    def test_claude_adapter_matches_the_source(self):
        result = subprocess.run([sys.executable, str(TOOL), "check", "--root", str(ROOT)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_drifted_claude_adapter_is_reported(self):
        import shutil, tempfile
        with tempfile.TemporaryDirectory() as temp:
            for rel in ("configs/allowed-activities.json", ".claude/settings.json"):
                (Path(temp) / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / rel, Path(temp) / rel)
            settings = json.loads((Path(temp) / ".claude/settings.json").read_text())
            settings["permissions"]["allow"].append("Bash(git push:*)")
            (Path(temp) / ".claude/settings.json").write_text(json.dumps(settings))
            result = subprocess.run([sys.executable, str(TOOL), "check", "--root", temp],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1)
            self.assertIn("differs", result.stderr)

    def test_codex_rendering_is_one_rule_per_activity(self):
        result = subprocess.run([sys.executable, str(TOOL), "render", "--host", "codex", "--root", str(ROOT)],
                                capture_output=True, text=True, check=True)
        rules = [l for l in result.stdout.splitlines() if l.startswith("prefix_rule(")]
        self.assertEqual(len(rules), len(SOURCE["activities"]))
        self.assertTrue(all('decision="allow"' in rule for rule in rules))


if __name__ == "__main__":
    unittest.main()
