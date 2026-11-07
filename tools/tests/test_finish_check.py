import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "finish_check.py"
MAKEFILE = "ok:\n\t@true\nbad:\n\t@false\n"


class FinishCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "Makefile").write_text(MAKEFILE)

    def goal(self, *items, text="Users can export a report"):
        (self.root / ".agent").mkdir(exist_ok=True)
        (self.root / ".agent" / "goal.json").write_text(
            json.dumps({"goal": text, "acceptance": list(items)}))

    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              input=stdin, capture_output=True, text=True, check=False)

    def gaps(self):
        return sorted((self.root / ".agent" / "gaps").glob("gap-*.json"))

    def test_without_goal_record_it_does_not_interfere(self):
        result = self.run_tool()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_met_goal_allows_finish(self):
        self.goal({"id": "t", "check": "tests pass", "run": "ok"},
                  {"id": "h", "check": "owner accepted", "status": "pass"})
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
        self.assertEqual(record["unmet"][0]["id"], "t")
        self.assertIsNone(record["first_divergence"])

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
        result = self.run_tool()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(self.gaps()[-1].read_text())["status"], "blocked")

    def test_commands_cannot_come_from_the_record(self):
        for run in ("bad; rm -rf x", "../x", "-f /tmp/m"):
            self.goal({"id": "t", "check": "c", "run": run})
            result = self.run_tool()
            self.assertEqual(result.returncode, 1, run)
            self.assertIn("Makefile target", result.stderr)

    def test_invalid_records_are_rejected(self):
        for data in ({"goal": "", "acceptance": [{"id": "a", "check": "c"}]},
                     {"goal": "g", "acceptance": []},
                     {"goal": "g", "acceptance": [{"id": "a"}]},
                     {"goal": "g", "acceptance": [{"id": "a", "check": "c"}, {"id": "a", "check": "c"}]}):
            (self.root / ".agent").mkdir(exist_ok=True)
            (self.root / ".agent" / "goal.json").write_text(json.dumps(data))
            self.assertEqual(self.run_tool().returncode, 1, data)

    def test_hook_blocks_first_stop_then_allows_second(self):
        self.goal({"id": "t", "check": "tests pass", "run": "bad"})
        event = {"cwd": str(self.root), "stop_hook_active": False}
        first = self.run_tool("--hook", stdin=json.dumps(event))
        self.assertEqual(first.returncode, 0)
        decision = json.loads(first.stdout)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("Goal not met", decision["reason"])
        second = self.run_tool("--hook", stdin=json.dumps({**event, "stop_hook_active": True}))
        self.assertEqual((second.returncode, second.stdout), (0, ""))
        self.assertEqual(len(self.gaps()), 2)

    def test_hook_never_loops_on_an_invalid_record(self):
        (self.root / ".agent").mkdir()
        (self.root / ".agent" / "goal.json").write_text("{not json")
        first = self.run_tool("--hook", stdin=json.dumps({"stop_hook_active": False}))
        self.assertEqual(json.loads(first.stdout)["decision"], "block")
        second = self.run_tool("--hook", stdin=json.dumps({"stop_hook_active": True}))
        self.assertEqual((second.returncode, second.stdout), (0, ""))

    def test_hook_is_silent_when_goal_met(self):
        self.goal({"id": "t", "check": "tests pass", "run": "ok"})
        result = self.run_tool("--hook", stdin=json.dumps({"cwd": str(self.root)}))
        self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
