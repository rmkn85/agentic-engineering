import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "finish_check.py"
MAKEFILE = ("ok:\n\t@test -f Makefile\nbad:\n\t@false\nnoop:\n\t@true\nsay:\n\t@echo done\nhelp:\n\t@echo help\nloop:\n\t@python3 tools/finish_check.py\n"
            "slow:\n\t@sleep {marker} & sleep {marker}\n"
            "bintrue:\n\t@/bin/true\ncomment:\n\t@true # done\ntest1:\n\t@test 1\nfiletest:\n\t@test -f README\n")
REFLECTION = {"first_divergence": "the deploy step needs credentials",
              "guidance_followed": "wrote the goal record first",
              "guidance_missing_or_misleading": "no deploy route is documented here"}
OWNER_OK = {"id": "h", "check": "owner accepted", "status": "pass", "evidence": "approved in https://example.invalid/pr/12"}


class FinishCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        # A per-instance sleep duration, so parallel suites never see each other's processes.
        self.marker = f"{40000 + (os.getpid() * 7 + id(self)) % 50000}.{os.getpid()}"
        (self.root / "Makefile").write_text(MAKEFILE.replace("{marker}", self.marker))
        (self.root / "README").write_text("a file, not a target\n")

    def fresh(self):
        # Independent table cases are separate tasks, not contract revisions.
        for name in ('goal-contract.json', 'goal-status.json', 'reflection-state.json'):
            (self.root / '.agent' / name).unlink(missing_ok=True)

    def authorize_revision(self):
        path = self.root / '.agent' / 'goal.json'
        record = json.loads(path.read_text())
        previous = json.loads((self.root / '.agent/goal-contract.json').read_text())
        record['supersedes'] = {'goal': previous['contract']['goal'], 'digest': previous['digest'],
                                'reason': 'the owner approved this revision', 'authority': 'see README'}
        record['reflection'] = {'interventions': [{'observation': 'the prior check failed',
                'evidence': 'see README', 'hypothesis': 'the revised scope resolves failure',
                'expected_effect': 'the maintained checks should pass', 'run': 'ok'}]}
        path.write_text(json.dumps(record))

    def goal(self, *items, text="Users can export a report", reflection=None):
        (self.root / ".agent").mkdir(exist_ok=True)
        record = {"goal": text, "acceptance": list(items)}
        if reflection:
            record["reflection"] = reflection
        (self.root / ".agent" / "goal.json").write_text(json.dumps(record))

    def run_tool(self, *args, stdin=None, env=None):
        return subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), *args],
                              input=stdin, capture_output=True, text=True, check=False, env=env)

    def hook(self, session="s1"):
        return self.run_tool("--hook", stdin=json.dumps({"session_id": session, "stop_hook_active": True}))

    def decision(self, result):
        self.assertTrue(result.stdout.strip(), "the hook allowed the stop")
        return json.loads(result.stdout)

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
        self.assertEqual((self.root / ".agent" / ".gitignore").read_text(), "*\n!.gitignore\n!audit.json\n")
        status = json.loads((self.root / ".agent" / "goal-status.json").read_text())
        self.assertEqual((status["goal"], status["met"], status["schema"]), ("Users can export a report", True, "goal-receipt/v2"))

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

    def test_manual_items_alone_cannot_prove_a_goal(self):
        self.goal(OWNER_OK)
        result = self.run_tool()
        self.assertEqual(result.returncode, 2)
        self.assertIn("no passing run check", result.stdout)

    def test_manual_evidence_must_cite_a_file_or_url(self):
        for evidence, met in (("x", False), ("it works", False), ("see Makefile", True),
                              ("https://example.invalid/run/1", True)):
            self.fresh()
            self.goal({"id": "t", "check": "tests pass", "run": "ok"},
                      {"id": "h", "check": "owner", "status": "pass", "evidence": evidence})
            self.assertEqual(self.run_tool().returncode == 0, met, evidence)

    def test_recipes_that_cannot_fail_prove_nothing(self):
        for run in ("noop", "say"):
            self.fresh()
            self.goal({"id": "t", "check": "c", "run": run})
            self.assertIn("cannot fail", self.run_tool().stdout)

    def test_common_no_op_spellings_prove_nothing(self):
        for run in ("bintrue", "comment", "test1"):
            self.fresh()
            self.goal({"id": "t", "check": "c", "run": run})
            self.assertIn("cannot fail", self.run_tool().stdout, run)
        self.fresh()
        self.goal({"id": "t", "check": "c", "run": "filetest"})
        self.assertEqual(self.run_tool().returncode, 0)

    def test_swapping_an_unmet_goal_needs_a_stated_reason(self):
        self.goal({"id": "t", "check": "export tests pass", "run": "bad"}, text="Users can export a monthly report")
        self.decision(self.hook())
        self.goal({"id": "t", "check": "c", "run": "ok"}, text="Make a small edit")
        for attempt in range(1, 4):
            self.assertIn("contract changed", self.decision(self.hook()).get("reason", ""), attempt)
        self.assertIn("NOT met", self.decision(self.hook())["systemMessage"])

    def test_a_reasoned_goal_change_is_allowed_and_recorded(self):
        self.goal({"id": "t", "check": "export tests pass", "run": "bad"}, text="Users can export a monthly report")
        self.decision(self.hook())
        record = {"goal": "Make a small edit", "acceptance": [{"id": "t", "check": "c", "run": "ok"}],
                  "supersedes": {"goal": "Users can export a monthly report",
                                 "reason": "the owner moved export to the next release"}}
        (self.root / ".agent" / "goal.json").write_text(json.dumps(record))
        self.authorize_revision()
        self.assertEqual(self.hook().stdout, "")
        gap = json.loads(self.gaps()[-1].read_text())
        self.assertEqual(gap["superseded_goal"]["goal"], "Users can export a monthly report")

    def test_a_met_goal_may_be_followed_by_another(self):
        self.goal({"id": "t", "check": "c", "run": "ok"}, text="first goal")
        self.assertEqual(self.hook().stdout, "")
        self.goal({"id": "t", "check": "c", "run": "ok"}, text="second goal")
        self.authorize_revision()
        self.assertEqual(self.hook().stdout, "")

    def test_a_goal_blocked_on_its_only_machine_check_can_end_blocked(self):
        item = {"id": "e2e", "check": "end-to-end run passes", "run": "bad", "status": "blocked",
                "blocker": "the staging database is offline for maintenance"}
        self.goal(item)
        reason = self.decision(self.hook())["reason"]
        self.assertIn("reflection.first_divergence", reason)
        self.assertIn("goal.json", reason)
        self.goal(item, reflection=REFLECTION)
        self.assertEqual(self.hook().stdout, "")
        self.assertEqual(json.loads(self.gaps()[-1].read_text())["status"], "blocked")
        self.assertEqual(self.run_tool().returncode, 2)  # blocked is never reported as met

    def test_placeholder_blockers_and_reflection_do_not_end_the_session(self):
        self.goal({"id": "t", "check": "tests pass", "run": "ok"},
                  {"id": "d", "check": "deployed", "status": "blocked", "blocker": "-"},
                  reflection={field: "-" for field in REFLECTION})
        self.assertEqual(self.decision(self.hook()).get("decision"), "block")

    def test_removing_the_goal_record_does_not_end_the_session_silently(self):
        self.goal({"id": "t", "check": "tests pass", "run": "bad"})
        self.decision(self.hook())
        (self.root / ".agent" / "goal.json").unlink()
        for _ in range(3):
            self.assertIn("goal record was removed", self.decision(self.hook()).get("reason", ""))
        final = self.decision(self.hook())
        self.assertIn("NOT verified", final["systemMessage"])

    def test_target_without_recipe_proves_nothing(self):
        for run in ("README", "Makefile"):
            self.fresh()
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
        self.fresh()
        self.goal({"id": "t", "check": "tests pass", "run": "ok"},
                  {"id": "h", "check": "deployed", "status": "blocked", "blocker": "no deploy credentials in this sandbox"})
        self.assertEqual(self.run_tool().returncode, 2)
        self.assertEqual(json.loads(self.gaps()[-1].read_text())["status"], "blocked")

    def test_commands_cannot_come_from_the_record(self):
        for run in ("bad; rm -rf x", "../x", "-f /tmp/m"):
            self.fresh()
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
        import shutil
        (self.root / "git").symlink_to(shutil.which("git"))
        result = self.run_tool(env={**os.environ, "PATH": str(self.root)})
        self.assertEqual(result.returncode, 2)
        self.assertIn("make is not installed", result.stdout)

    def test_hook_keeps_blocking_unmet_goal_then_ends_loudly(self):
        self.goal({"id": "t", "check": "tests pass", "run": "bad"})
        for attempt in range(1, 4):
            decision = self.decision(self.hook())
            self.assertEqual(decision.get("decision"), "block", attempt)
            self.assertIn(f"({attempt}/3)", decision["reason"])
        final = self.hook()
        self.assertEqual(final.returncode, 0)
        self.assertIn("NOT met", self.decision(final)["systemMessage"])
        self.assertTrue(json.loads(self.gaps()[-1].read_text())["session_ended_unmet"])
        self.assertEqual(self.decision(self.hook("s2")).get("decision"), "block")  # new session starts over

    def test_hook_allows_finish_with_named_blockers_only_after_reflection(self):
        items = ({"id": "t", "check": "tests pass", "run": "ok"},
                 {"id": "d", "check": "deployed", "status": "blocked", "blocker": "no deploy credentials in this sandbox"})
        self.goal(*items)
        self.assertIn("reflection.first_divergence", self.decision(self.hook())["reason"])
        self.goal(*items, reflection=REFLECTION)
        self.assertEqual(self.hook().stdout, "")
        record = json.loads(self.gaps()[-1].read_text())
        self.assertEqual((record["status"], record["first_divergence"]), ("blocked", REFLECTION["first_divergence"]))

    def test_targets_that_prove_nothing_or_call_the_gate_are_refused(self):
        (self.root / "tools").mkdir()
        (self.root / "tools" / "finish_check.py").write_text("")
        for run, why in (("help", "cannot fail"), ("loop", "calls the finish gate")):
            self.fresh()
            self.goal({"id": "t", "check": "c", "run": run})
            self.assertIn(why, self.run_tool().stdout)

    def test_timeout_kills_the_whole_process_tree(self):
        self.addCleanup(subprocess.run, ["pkill", "-f", f"sleep {self.marker}"], capture_output=True)
        self.goal({"id": "t", "check": "c", "run": "slow"})
        result = self.run_tool("--timeout", "1")
        self.assertIn("timed out", result.stdout)
        left = subprocess.run(["pgrep", "-f", f"sleep {self.marker}"], capture_output=True, text=True).stdout.split()
        self.assertEqual(left, [])

    def test_unpushed_commits_count_as_changes_without_a_goal(self):
        git = ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t"]
        subprocess.run(git + ["init", "-q"], cwd=self.root, check=True)
        subprocess.run(git + ["add", "."], cwd=self.root, check=True)
        subprocess.run(git + ["commit", "-qm", "base"], cwd=self.root, check=True)
        subprocess.run(git + ["update-ref", "refs/remotes/origin/main", "HEAD"], cwd=self.root, check=True)
        (self.root / "work.txt").write_text("x")
        subprocess.run(git + ["add", "."], cwd=self.root, check=True)
        subprocess.run(git + ["commit", "-qm", "work"], cwd=self.root, check=True)
        self.assertIn("without a goal record", self.decision(self.hook())["reason"])

    def test_a_new_goal_in_the_same_session_is_enforced_again(self):
        self.goal({"id": "t", "check": "c", "run": "bad"}, text="first goal")
        for _ in range(4):
            self.hook()
        record = {"goal": "second goal", "acceptance": [{"id": "t", "check": "c", "run": "bad"}],
                  "supersedes": {"goal": "first goal", "reason": "the owner replaced the first goal"}}
        (self.root / ".agent" / "goal.json").write_text(json.dumps(record))
        decision = self.decision(self.hook())
        self.assertEqual(decision.get("decision"), "block")
        self.assertIn("(1/3)", decision["reason"])

    def test_hook_asks_once_for_a_goal_record_when_files_changed(self):
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        first = self.decision(self.hook())
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
