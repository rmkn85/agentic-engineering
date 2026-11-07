"""Missing benchmark evidence must remain visibly unavailable."""
import contextlib
import io
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from decimal import Decimal
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), TOOLS / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bench = load_script("codex-bench.py")
compare = load_script("bench-compare.py")


class BenchReportingTests(unittest.TestCase):
    def test_missing_and_partial_turn_usage_is_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(json.dumps({"type": "error"}) + "\n")
            usage, turns, counts = bench.summarize_events(events)
            self.assertEqual(usage, dict.fromkeys(bench.USAGE_FIELDS))
            self.assertEqual(turns, [])
            self.assertEqual(counts["errors"], 1)

            records = [
                {"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 0,
                                                      "output_tokens": 0, "reasoning_output_tokens": 0}},
                {"type": "turn.completed", "usage": {"input_tokens": 20, "output_tokens": 5,
                                                      "reasoning_output_tokens": 0}},
                {"type": "item.completed", "item": {"type": "command_execution"}},
            ]
            events.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            usage, turns, counts = bench.summarize_events(events)
            self.assertEqual(usage, {"input_tokens": 30, "cached_input_tokens": None,
                                     "output_tokens": 5, "reasoning_output_tokens": 0})
            self.assertEqual(counts["turns"], 2)
            self.assertEqual(counts["commands"], 1)

    def test_legacy_zero_fill_does_not_hide_missing_usage(self):
        old = {"usage": dict.fromkeys(bench.USAGE_FIELDS, 0), "per_turn_usage": [{}]}
        self.assertEqual(compare.tok(old), (None, None, None, None))
        measured_zero = {"usage": dict.fromkeys(bench.USAGE_FIELDS, 0),
                         "per_turn_usage": [dict.fromkeys(bench.USAGE_FIELDS, 0)]}
        self.assertEqual(compare.tok(measured_zero), (0, 0, 0, 0))

    def test_comparison_requires_independent_acceptance(self):
        base = {"label": "no-eval", "codex_exit_code": 0, "eval_command": None,
                "eval_exit_code": None, "wall_seconds": 1.0,
                "usage": dict.fromkeys(bench.USAGE_FIELDS, 0), "per_turn_usage": [],
                "counts": {"turns": 0, "commands": 0}, "git": {"changed_files": 0}}
        evaluated = {**base, "label": "evaluated", "eval_command": "make test", "eval_exit_code": 0,
                     "per_turn_usage": [dict.fromkeys(bench.USAGE_FIELDS, 0)]}
        failed = {**evaluated, "label": "failed", "eval_exit_code": 1}
        invalid = {**base, "label": "missing-command", "eval_exit_code": 0}
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for row in (base, evaluated, failed, invalid):
                path = Path(tmp) / f"{row['label']}.json"
                path.write_text(json.dumps(row))
                paths.append(str(path))
            result = subprocess.run([sys.executable, str(TOOLS / "bench-compare.py"), *paths],
                                    check=True, capture_output=True, text=True)
        lines = result.stdout.splitlines()
        self.assertIn("| no-eval | UNVERIFIED | 1.0 | unavailable | unavailable | unavailable |", lines[2])
        self.assertIn("| evaluated | PASS | 1.0 | 0 | 0 | unavailable |", lines[3])
        self.assertIn("| failed | FAIL |", lines[4])
        self.assertIn("| missing-command | UNVERIFIED |", lines[5])

    def test_observed_loop_requires_valid_measured_durations_and_passing_eval(self):
        base = {"codex_exit_code": 0, "eval_command": "make test", "eval_exit_code": 0,
                "wall_seconds": 2, "eval_wall_seconds": 3, "loop_wall_seconds": 7}
        self.assertEqual(compare.timings(base), (2, 3, 7))
        for field in ("wall_seconds", "eval_wall_seconds", "loop_wall_seconds"):
            for value in (None, True, False, -1, float("inf"), float("nan"), "3"):
                with self.subTest(field=field, value=value):
                    self.assertIsNone(compare.timings({**base, field: value})[2])
        for change in ({"loop_wall_seconds": 4}, {"eval_command": None},
                       {"eval_exit_code": 1}, {"eval_exit_code": False},
                       {"codex_exit_code": True}, {"codex_exit_code": None}):
            self.assertIsNone(compare.timings({**base, **change})[2])
        legacy = {key: value for key, value in base.items() if key != "loop_wall_seconds"}
        self.assertEqual(compare.timings(legacy), (2, 3, None))

    def test_optional_cost_uses_uncached_and_cached_rates_once(self):
        tokens=(1_000_000,500_000,2_000_000,100_000)
        rates=(Decimal("2"),Decimal("0.5"),Decimal("8"))
        self.assertEqual(compare.estimate_cost(tokens,rates),Decimal("17.25"))
        self.assertIsNone(compare.estimate_cost((None,0,0,0),rates))
        self.assertIsNone(compare.estimate_cost((10,11,0,0),rates))

    def test_root_response_profile_uses_local_session_usage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            events.write_text(json.dumps({"type": "thread.started", "thread_id": "trial-1"}) + "\n")
            session_dir = root / "sessions" / "2026" / "09" / "24"
            session_dir.mkdir(parents=True)
            session = session_dir / "rollout-trial-1.jsonl"
            records = []
            for response_id, input_count, cached_count in (("a", 100, 20), ("b", 300, 200), ("b", 300, 200)):
                records.append({"type": "token_usage_record", "payload": {
                    "response_id": response_id, "usage": {"input_tokens": input_count,
                    "cached_input_tokens": cached_count, "output_tokens": 5,
                    "reasoning_output_tokens": 1}}})
            session.write_text("\n".join(json.dumps(record) for record in records) + "\n")
            self.assertEqual(bench.summarize_root_responses(events, root), {
                "response_count": 2, "compaction_count": 0, "median_input_tokens": 200.0,
                "peak_input_tokens": 300, "peak_cached_input_tokens": 200})


class WorktreePreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        bench.git(self.repo, "init")
        bench.git(self.repo, "config", "user.name", "Benchmark test")
        bench.git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "tracked").write_text("base\n")
        (self.repo / ".gitignore").write_text("ignored\n")
        bench.git(self.repo, "add", ".")
        bench.git(self.repo, "commit", "-m", "base")
        self.base = bench.git(self.repo, "rev-parse", "HEAD")
        self.worktree = self.root / "worktree"
        bench.git(self.repo, "worktree", "add", "--detach", str(self.worktree), self.base)

    def retire(self, keep=False):
        return bench.retire_worktree(self.repo, self.worktree, self.base, keep)

    def test_clean_unchanged_worktree_is_removed_without_force(self):
        original = bench.git
        with mock.patch.object(bench, "git", wraps=original) as calls:
            receipt = self.retire()
        self.assertEqual(receipt["state"], "removed")
        self.assertFalse(self.worktree.exists())
        self.assertIn(mock.call(self.repo, "worktree", "remove", str(self.worktree)), calls.call_args_list)
        self.assertFalse(any("--force" in call.args for call in calls.call_args_list))

    def test_dirty_untracked_and_ignored_files_are_preserved(self):
        for filename in ("tracked", "untracked", "ignored"):
            with self.subTest(filename=filename):
                path = self.worktree / filename
                path.write_text("unique result\n")
                receipt = self.retire()
                self.assertEqual(receipt["state"], "retained")
                self.assertEqual(receipt["reason"], "tracked_untracked_or_ignored_changes")
                self.assertEqual(path.read_text(), "unique result\n")
                if filename == "tracked":
                    bench.git(self.worktree, "restore", filename)
                else:
                    path.unlink()

    def test_detached_commit_and_explicit_keep_are_preserved(self):
        self.assertEqual(self.retire(keep=True)["reason"], "explicit_keep")
        (self.worktree / "tracked").write_text("committed result\n")
        bench.git(self.worktree, "add", "tracked")
        bench.git(self.worktree, "commit", "-m", "unique result")
        head = bench.git(self.worktree, "rev-parse", "HEAD")
        receipt = self.retire()
        self.assertEqual(receipt["reason"], "head_differs_from_base")
        self.assertEqual(receipt["head_commit"], head)
        self.assertEqual(bench.git(self.worktree, "rev-parse", "HEAD"), head)

    def test_index_flags_cannot_hide_unique_tracked_content(self):
        for flag in ("assume-unchanged", "skip-worktree"):
            with self.subTest(flag=flag):
                bench.git(self.worktree, "update-index", "--" + flag, "tracked")
                path = self.worktree / "tracked"
                path.write_text("hidden unique result\n")
                self.assertEqual(bench.git(self.worktree, "status", "--porcelain"), "")
                receipt = self.retire()
                self.assertEqual(receipt["reason"], "index_flags_can_hide_changes")
                self.assertEqual(path.read_text(), "hidden unique result\n")
                bench.git(self.worktree, "update-index", "--no-" + flag, "tracked")
                bench.git(self.worktree, "restore", "tracked")

    def test_reset_detached_commit_is_preserved_in_worktree_head_reflog(self):
        (self.worktree / "tracked").write_text("detached unique result\n")
        bench.git(self.worktree, "add", "tracked")
        bench.git(self.worktree, "commit", "-m", "detached result")
        unique = bench.git(self.worktree, "rev-parse", "HEAD")
        bench.git(self.worktree, "reset", "--hard", self.base)
        self.assertEqual(bench.git(self.worktree, "status", "--porcelain"), "")
        receipt = self.retire()
        self.assertEqual(receipt["reason"], "head_reflog_contains_unique_commit")
        self.assertEqual(receipt["head_commit"], unique)
        self.assertTrue(self.worktree.exists())
        self.assertEqual(bench.git(self.worktree, "show", unique + ":tracked"), "detached unique result")

    def test_retirement_failure_is_reported_and_preserves_data(self):
        original = bench.git
        def fail_remove(repo, *args, **kwargs):
            if args[:2] == ("worktree", "remove"):
                raise subprocess.CalledProcessError(1, ["git", *args])
            return original(repo, *args, **kwargs)
        with mock.patch.object(bench, "git", side_effect=fail_remove):
            receipt = self.retire()
        self.assertEqual(receipt["reason"], "retirement_failed")
        self.assertTrue(self.worktree.exists())
        self.assertEqual(receipt["path"], str(self.worktree))

    def test_main_records_setup_to_eval_timing_and_retirement_receipt(self):
        original = subprocess.run
        def fake_worker(command, **kwargs):
            if isinstance(command, list) and command[0] == "codex":
                kwargs["stdout"].write('{"type":"turn.completed","usage":{}}\n')
                return subprocess.CompletedProcess(command, 0)
            if kwargs.get("shell"):
                return subprocess.CompletedProcess(command, 0)
            return original(command, **kwargs)
        args = ["codex-bench.py", "--repo", str(self.repo), "--label", "test",
                "--prompt", "test", "--eval-command", "chosen-check", "--runs-dir", str(self.root / "runs")]
        with mock.patch.object(sys, "argv", args), \
             mock.patch.object(bench.subprocess, "run", side_effect=fake_worker), \
             mock.patch.object(bench.time, "monotonic", side_effect=[10, 11, 13, 14, 15, 18, 20]), \
             mock.patch.object(bench, "collect_practice_feedback", return_value={"state": "not_recorded"}), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(bench.main(), 0)
        metrics = json.loads(next((self.root / "runs").glob("*/metrics.json")).read_text())
        self.assertEqual(metrics["wall_seconds"], 2)
        self.assertEqual(metrics["eval_wall_seconds"], 3)
        self.assertEqual(metrics["loop_wall_seconds"], 10)
        self.assertEqual(metrics["worktree_lifecycle"]["state"], "removed")
        self.assertIn("chosen evaluation", metrics["timing_scope"]["loop_wall_seconds"])


if __name__ == "__main__":
    unittest.main()
