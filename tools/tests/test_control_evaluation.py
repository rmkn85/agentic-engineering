import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from control_evaluation import Invalid, evaluate


POLICY = {
    "minimum_matched_pairs": 1,
    "desired_leadtime_reduction_fraction": 0.2,
    "desired_rescue_reduction_fraction": 0.5,
    "max_escaped_defect_increase": 0,
    "max_control_overhead_fraction": 0.2,
    "intentional_differences": [],
}


def obs(pair, arm, outcome="accepted", auth="2026-01-01T00:00:00Z", accepted=None, rescue=2, defect=0, active=100, control=0, acceptance="same", feedback=None):
    if accepted is None and outcome == "accepted":
        accepted = "2026-01-01T00:00:10Z" if arm == "candidate" else "2026-01-01T00:00:20Z"
    return {"pair_id": pair, "arm": arm, "acceptance": acceptance, "taskclass": "change", "model": "model-x", "harness": "harness-v1", "conditions": "condition-set-a", "outcome": outcome, "authorized_at": auth, "accepted_at": accepted, "feedback_at": feedback, "edit_at": None, "rescue": rescue, "rework": 0, "escaped_defects": defect, "active_seconds": active, "control_seconds": control, "model_usage": None}


def data(rows, policy=None, now="2026-01-03T00:00:00Z"):
    return {"policy": POLICY if policy is None else policy, "observations": rows, "now": now}


class EvaluationTests(unittest.TestCase):
    def test_good_match_adopts_and_keeps_full_timing(self):
        result = evaluate(data([obs("p", "baseline", rescue=4), obs("p", "candidate", rescue=0, control=10)]))
        self.assertEqual("adopt", result["recommendation"])
        self.assertEqual(20, result["metrics"]["median_baseline_accepted_leadtime_seconds"])
        self.assertEqual(10, result["metrics"]["median_candidate_accepted_leadtime_seconds"])

    def test_slower_or_quality_degradation_revises(self):
        rows = [obs("p", "baseline", rescue=4), obs("p", "candidate", rescue=4, accepted="2026-01-01T00:00:30Z")]
        self.assertEqual("revise", evaluate(data(rows))["recommendation"])
        rows[1]["escaped_defects"] = 1
        self.assertEqual("revise", evaluate(data(rows))["recommendation"])

    def test_known_failed_criterion_precedes_another_unknown_metric(self):
        rows = [obs("p", "baseline", rescue=4), obs("p", "candidate", rescue=None, accepted="2026-01-01T00:00:30Z")]
        result = evaluate(data(rows))
        self.assertFalse(result["criteria"]["desired_leadtime_reduction_fraction"]["met"])
        self.assertIsNone(result["criteria"]["desired_rescue_reduction_fraction"]["met"])
        self.assertEqual("revise", result["recommendation"])

    def test_unmatched_and_acceptance_mismatch_are_inconclusive(self):
        r = evaluate(data([obs("p", "candidate", rescue=0)]))
        self.assertEqual("inconclusive", r["recommendation"])
        self.assertEqual(["p"], r["counts"]["unmatched_pairs"]["candidate"])
        rows = [obs("p", "baseline"), obs("p", "candidate", acceptance="different", rescue=0)]
        r = evaluate(data(rows))
        self.assertEqual("inconclusive", r["recommendation"])
        self.assertEqual(["p"], r["counts"]["mismatched_pairs"])

    def test_missing_criteria_and_unknown_metrics_inconclusive(self):
        policy = dict(POLICY, desired_rescue_reduction_fraction=None)
        self.assertEqual("inconclusive", evaluate(data([obs("p", "baseline"), obs("p", "candidate", rescue=0)], policy))["recommendation"])
        rows = [obs("p", "baseline", feedback=None), obs("p", "candidate", rescue=0, feedback=None)]
        self.assertIsNone(evaluate(data(rows))["metrics"]["median_candidate_feedback_latency_seconds"])

    def test_control_overhead_and_zero_denominator(self):
        rows = [obs("p", "baseline", rescue=4), obs("p", "candidate", rescue=0, active=0, control=0)]
        self.assertEqual(0, evaluate(data(rows))["metrics"]["median_candidate_control_overhead_fraction"])
        rows[1]["control_seconds"] = 1
        with self.assertRaises(Invalid):
            evaluate(data(rows))

    def test_failed_and_unfinished_retained_with_age(self):
        rows = [obs("p", "baseline", rescue=4), obs("p", "candidate", "unfinished", accepted=None, rescue=0)]
        r = evaluate(data(rows))
        self.assertEqual("inconclusive", r["recommendation"])
        self.assertEqual(1, r["counts"]["outcomes"]["candidate"]["unfinished"])
        self.assertEqual(172800, r["metrics"]["median_candidate_unaccepted_age_seconds"])
        self.assertEqual(172800, r["attempt_ages"][0]["age_seconds"])
        rows[1]["outcome"] = "failed"
        self.assertEqual("revise", evaluate(data(rows))["recommendation"])


    def test_null_defect_and_overhead_thresholds_are_inconclusive(self):
        policy = dict(POLICY, max_escaped_defect_increase=None, max_control_overhead_fraction=None)
        result = evaluate(data([obs("p", "baseline"), obs("p", "candidate", rescue=0)], policy))
        self.assertEqual("inconclusive", result["recommendation"])
        self.assertIsNone(result["criteria"]["max_escaped_defect_increase"]["met"])
        self.assertIsNone(result["criteria"]["max_control_overhead_fraction"]["met"])

    def test_unknown_counts_or_seconds_invalidate_whole_metric(self):
        for field, metric in (("rescue", "desired_rescue_reduction_fraction"), ("escaped_defects", "max_escaped_defect_increase"), ("active_seconds", "max_control_overhead_fraction"), ("control_seconds", "max_control_overhead_fraction"), ("rework", None)):
            rows = [obs("p", "baseline"), obs("p", "candidate", rescue=0)]
            rows[1][field] = None
            result = evaluate(data(rows))
            self.assertEqual("inconclusive", result["recommendation"], field)
            if metric:
                self.assertIsNone(result["criteria"][metric]["met"], field)
            if field == "rework":
                self.assertIsNone(result["metrics"]["median_rework_difference"])

    def test_feedback_latency_is_edit_to_feedback_and_order_is_checked(self):
        rows = [obs("p", "baseline", feedback="2026-01-01T00:00:18Z"), obs("p", "candidate", rescue=0, feedback="2026-01-01T00:00:09Z")]
        rows[0]["edit_at"] = "2026-01-01T00:00:10Z"
        rows[1]["edit_at"] = "2026-01-01T00:00:05Z"
        result = evaluate(data(rows))
        self.assertEqual(8, result["metrics"]["median_baseline_feedback_latency_seconds"])
        self.assertEqual(4, result["metrics"]["median_candidate_feedback_latency_seconds"])
        self.assertEqual(-4, result["metrics"]["median_feedback_latency_difference_seconds"])
        rows[1]["feedback_at"] = "2026-01-01T00:00:04Z"
        with self.assertRaises(Invalid):
            evaluate(data(rows))

    def test_control_bound_counts_and_now_validation(self):
        rows = [obs("p", "baseline"), obs("p", "candidate", rescue=0)]
        rows[1]["control_seconds"] = 101
        with self.assertRaises(Invalid):
            evaluate(data(rows))
        rows[1]["control_seconds"] = 1
        rows[1]["rescue"] = 1.5
        with self.assertRaises(Invalid):
            evaluate(data(rows))
        rows[1]["rescue"] = 0
        with self.assertRaises(Invalid):
            evaluate(data(rows, now="2026-01-01T00:00:00Z"))
        rows[1]["active_seconds"] = 10**1000
        with self.assertRaises(Invalid):
            evaluate(data(rows))

    def test_baseline_failure_and_unfinished_cannot_inflate_accepted_subset(self):
        rows = [obs("p1", "baseline", outcome="failed", accepted=None), obs("p1", "candidate", rescue=0), obs("p2", "baseline", rescue=4), obs("p2", "candidate", rescue=0)]
        result = evaluate(data(rows))
        self.assertEqual("inconclusive", result["recommendation"])
        self.assertIsNone(result["metrics"]["median_baseline_accepted_leadtime_seconds"])
        rows[0]["outcome"] = "unfinished"
        result = evaluate(data(rows))
        self.assertEqual("inconclusive", result["recommendation"])
        self.assertEqual(1, result["counts"]["outcomes"]["baseline"]["unfinished"])

    def test_harness_and_conditions_must_match_or_be_declared(self):
        rows = [obs("p", "baseline"), obs("p", "candidate", rescue=0)]
        rows[1]["harness"] = "harness-v2"
        result = evaluate(data(rows))
        self.assertEqual("inconclusive", result["recommendation"])
        self.assertEqual(["p"], result["counts"]["mismatched_pairs"])
        result = evaluate(data(rows, dict(POLICY, intentional_differences=["harness"])))
        self.assertEqual("adopt", result["recommendation"])
        rows[1]["conditions"] = "other"
        self.assertEqual("inconclusive", evaluate(data(rows, dict(POLICY, intentional_differences=["harness"]))) ["recommendation"])

    def test_known_quality_failure_still_revises_with_other_unknown_pairs(self):
        rows = [obs("p1", "baseline"), obs("p1", "candidate", defect=1, rescue=0), obs("p2", "baseline"), obs("p2", "candidate", defect=None, rescue=0)]
        result = evaluate(data(rows))
        self.assertEqual("revise", result["recommendation"])
        self.assertIsNone(result["criteria"]["max_escaped_defect_increase"]["met"])

    def test_baseline_unmatched_and_candidate_failure_remain_visible(self):
        result = evaluate(data([obs("only-baseline", "baseline")]))
        self.assertEqual("inconclusive", result["recommendation"])
        self.assertEqual(["only-baseline"], result["counts"]["unmatched_pairs"]["baseline"])
        result = evaluate(data([obs("p", "baseline"), obs("p", "candidate", outcome="failed", accepted=None)]))
        self.assertEqual("revise", result["recommendation"])

    def test_invalid_numeric_and_time_inputs_rejected(self):
        rows = [obs("p", "baseline"), obs("p", "candidate", rescue=0)]
        rows[1]["active_seconds"] = float("nan")
        with self.assertRaises(Invalid):
            evaluate(data(rows))
        rows[1]["active_seconds"] = True
        with self.assertRaises(Invalid):
            evaluate(data(rows))
        rows[1]["active_seconds"] = 1
        rows[1]["accepted_at"] = "2025-12-31T23:59:59Z"
        with self.assertRaises(Invalid):
            evaluate(data(rows))


if __name__ == "__main__":
    unittest.main()
