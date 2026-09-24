"""Missing benchmark evidence must remain visibly unavailable."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
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
                "response_count": 2, "median_input_tokens": 200.0,
                "peak_input_tokens": 300, "peak_cached_input_tokens": 200})


if __name__ == "__main__":
    unittest.main()
