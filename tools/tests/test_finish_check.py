import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "finish_check.py"
MAKEFILE = "ok:\n\t@true\nbad:\n\t@false\n"
OWNER_OK = {"id": "h", "check": "owner accepted", "status": "pass", "evidence": "approved in review"}


class FinishCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "Makefile").write_text(MAKEFILE)
        (self.root / "README").write_text("a file, not a target\n")

    def goal(self, *items, text="Users can export a report"):
        (self.root / ".agent").mkdir(exist_ok=True)
        (self.root / ".agent" / "goal.json").write_text(
            json.dumps({"goal": text, "acceptance": list(items)}))

    def run_tool(self, *args, stdin=None, env=None):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              input=stdin, capture_output=True, text=True, check=False, env=env)

    def hook(self, session="s1"):
        return self.run_tool("--hook", stdin=json.dumps({"session_id": session, "stop_hook_active": True}))

    def gaps(self):
        return sorted((self.root / ".agent" / "gaps").glob("gap-*.json"))

    def test_without_goal_record_cli_does_not_interfere(self):
        result = self.run_tool()
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_met_goal_allows_finish(self):
        self.goal({"id": "t", "check": "tests pass", "run": "ok"}, OWNER_OK)
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.gaps(), [])

    def test_failing_check_blocks_and_records_gap_with_unknown_reflection(self):
        self.goal({"id": "t", "check": "tests pass", "run": "bad"})
        result = self.run_tool()
        self.assertEqual(result.returncode, 2)
        self.assertIn("make bad exited", result.stdout)
        record = json.loads(self.gaps()[0].read_text())
        self.assertEqual(record["status"], "not-met")
        self.assertIsNone(record["first_divergence"])

    def test_self_declared_pass_needs_evidence(self):
        self.goal({"id": "h", "check": "owner accepted", "status": "pass"})
        result = self.run_tool()
        self.assertEqual(result.returncode, 2)
        self.assertIn("without evidence", result.stdout)

    def test_target_without_recipe_proves_nothing(self):
        for run in ("README", "Makefile"):
            self.goal({"id": "t", "check": "c", "run": run})
            result = self.run_tool()
            self.assertEqual(result.returncode, 2, run)
            self.assertIn("no recipe", result.stdout)

    def test_unverified_manual_item_is_unmet(self):
        for status in (None, "pending", "fail"):
            item = {"id": "h", "check": "human judged"}
            if status:
                item["status"] = status
            self.goal(item)
            self.assertEqual(self.run_tool().returncode, 2, status)

    def test_blocked_needs_a_named_blocker(self):
        self.goal({"id": "h", "check": "deployed", "status": "blocked"})
        self.assertIn("status is blocked", self.run_tool().stdout)
        self.goal({"id": "h", "check": "deployed", "status": "blocked", "blocker": "no deploy credentials"})
        self.assertEqual(self.run_tool().returncode, 2)
        self.assertEqual(json.loads(self.gaps()[-1].read_text())["status"], "blocked")

    def test_commands_cannot_come_from_the_record(self):
        for run in ("bad; rm -rf x", "../x", "-f /tmp/m"):
            self.goal({"id": "t", "check": "c", "run": run})
            result = self.run_tool()
            self.assertEqual(result.returncode, 1, run)
            self.assertIn("Makefile target", result.stderr)

    def test_invalid_records_are_rejected_without_crashing(self):
        for data in ({"goal": "", "acceptance": [{"id": "a", "check": "c"}]},
                     {"goal": "g", "acceptance": []},
                     {"goal": "g", "acceptance": [{"id": "a"}]},
                     {"goal": "g", "acceptance": [{"id": 3, "check": "c"}]},
                     {"goal": "g", "acceptance": [{"id": [], "check": "c"}]},
                     {"goal": "g", "acceptance": [{"id": "a", "check": "c", "status": ["pass"]}]},
                     {"goal": "g", "acceptance": [{"id": "a", "check": "c"}, {"id": "a", "check": "c"}]},
                     ["not", "an", "object"]):
            (self.root / ".agent").mkdir(exist_ok=True)
            (self.root / ".agent" / "goal.json").write_text(json.dumps(data))
            result = self.run_tool()
            self.assertEqual(result.returncode, 1, data)
            self.assertNotIn("Traceback", result.stderr)

    def test_missing_make_is_an_unmet_check_not_a_crash(self):
        self.goal({"id": "t", "check": "tests pass", "run": "ok"})
        result = self.run_tool(env={**os.environ, "PATH": str(self.root)})
        self.assertEqual(result.returncode, 2)
        self.assertIn("make is not installed", result.stdout)

    def test_hook_keeps_blocking_unmet_goal_then_ends_loudly(self):
        self.goal({"id": "t", "check": "tests pass", "run": "bad"})
        for attempt in range(1, 4):
            decision = json.loads(self.hook().stdout)
            self.assertEqual(decision["decision"], "block", attempt)
            self.assertIn(f"({attempt}/3)", decision["reason"])
        final = self.hook()
        self.assertEqual(final.returncode, 0)
        self.assertIn("NOT met", json.loads(final.stdout)["systemMessage"])
        self.assertTrue(json.loads(self.gaps()[-1].read_text())["session_ended_unmet"])
        self.assertEqual(json.loads(self.hook("s2").stdout)["decision"], "block")  # new session starts over

    def test_hook_allows_finish_when_only_named_blockers_remain(self):
        self.goal({"id": "t", "check": "tests pass", "run": "ok"},
                  {"id": "d", "check": "deployed", "status": "blocked", "blocker": "no credentials"})
        self.assertEqual((self.hook().returncode, self.hook().stdout), (0, ""))
        self.assertEqual(json.loads(self.gaps()[-1].read_text())["status"], "blocked")

    def test_hook_asks_once_for_a_goal_record_when_files_changed(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        first = json.loads(self.hook().stdout)
        self.assertIn("without a goal record", first["reason"])
        self.assertEqual(self.hook().stdout, "")

    def test_hook_is_silent_without_changes_or_record(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "commit", "-qm", "x"],
                       cwd=self.root, check=True)
        self.assertEqual(self.hook().stdout, "")

    def test_hook_survives_malformed_events(self):
        for stdin in ("[]", "not json", json.dumps({"cwd": 5, "session_id": []})):
            result = self.run_tool("--hook", stdin=stdin)
            self.assertEqual(result.returncode, 0, stdin)
            self.assertNotIn("Traceback", result.stderr)

    def test_help_shows_the_record_format(self):
        self.assertIn('"acceptance"', self.run_tool("--help").stdout)


if __name__ == "__main__":
    unittest.main()
