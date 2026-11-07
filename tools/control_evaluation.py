#!/usr/bin/env python3
"""Evaluate matched control-adoption observations against owner-supplied policy."""
import argparse
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

OUTCOMES = {"accepted", "failed", "unfinished", "cancelled"}
BASE_FIELDS = ("acceptance", "taskclass", "model")
EXTRA_FIELDS = ("harness", "conditions")
POLICY_FIELDS = (
    "minimum_matched_pairs",
    "desired_leadtime_reduction_fraction",
    "desired_rescue_reduction_fraction",
    "max_escaped_defect_increase",
    "max_control_overhead_fraction",
)


class Invalid(ValueError):
    """Input cannot be evaluated without risking a misleading result."""


def number(value, name, optional=True):
    if value is None and optional:
        return None
    try:
        valid = not isinstance(value, bool) and isinstance(value, (int, float))
        valid = valid and math.isfinite(value) and 0 <= value <= 1e15
    except (OverflowError, TypeError):
        valid = False
    if not valid:
        raise Invalid("%s must be a finite nonnegative number%s" % (name, " or null" if optional else ""))
    return float(value)


def count(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 10**12:
        raise Invalid("%s must be a nonnegative integer or null" % name)
    return value


def timestamp(value, name, optional=False):
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise Invalid("%s must be an ISO timestamp%s" % (name, " or null" if optional else ""))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise Invalid("%s is not a valid ISO timestamp" % name)
    if parsed.tzinfo is None:
        raise Invalid("%s must include a timezone" % name)
    return parsed


def median(values):
    return statistics.median(values) if values and all(v is not None for v in values) else None


def elapsed(end, start):
    return (end - start).total_seconds() if end is not None and start is not None else None


def evaluate(data):
    if not isinstance(data, dict) or not isinstance(data.get("policy"), dict) or not isinstance(data.get("observations"), list):
        raise Invalid("input requires policy object and observations array")
    policy = data["policy"]
    if any(key not in policy for key in POLICY_FIELDS) or "intentional_differences" not in policy:
        raise Invalid("policy must supply all criteria and intentional_differences; use null for unknown criteria")
    minimum = policy["minimum_matched_pairs"]
    if minimum is not None and (isinstance(minimum, bool) or not isinstance(minimum, int) or not 1 <= minimum <= 10**6):
        raise Invalid("minimum_matched_pairs must be a positive integer or null")
    for key in POLICY_FIELDS[1:]:
        value = policy[key]
        if value is not None:
            number(value, key, optional=False)
            if "fraction" in key and value > 1:
                raise Invalid(key + " must be at most 1")
    allowed = policy["intentional_differences"]
    if not isinstance(allowed, list) or any(f not in EXTRA_FIELDS for f in allowed) or len(set(allowed)) != len(allowed):
        raise Invalid("intentional_differences must list unique optional fields: harness, conditions")

    now = timestamp(data.get("now"), "now", True)
    observations, seen, recorded_times = [], set(), []
    for i, raw in enumerate(data["observations"]):
        path = "observations[%d]" % i
        if not isinstance(raw, dict):
            raise Invalid(path + " must be an object")
        pair, arm = raw.get("pair_id"), raw.get("arm")
        if not isinstance(pair, str) or not pair or arm not in ("baseline", "candidate"):
            raise Invalid(path + " requires pair_id and baseline/candidate arm")
        if (pair, arm) in seen:
            raise Invalid("duplicate pair_id/arm: %s/%s" % (pair, arm))
        seen.add((pair, arm))
        for field in BASE_FIELDS + EXTRA_FIELDS:
            if not isinstance(raw.get(field), str) or not raw[field]:
                raise Invalid(path + " requires nonempty " + field)
        outcome = raw.get("outcome")
        if outcome not in OUTCOMES:
            raise Invalid(path + " has invalid outcome")
        auth = timestamp(raw.get("authorized_at"), path + ".authorized_at")
        accepted = timestamp(raw.get("accepted_at"), path + ".accepted_at", outcome != "accepted")
        feedback = timestamp(raw.get("feedback_at"), path + ".feedback_at", True)
        edit = timestamp(raw.get("edit_at"), path + ".edit_at", True)
        for name, value in (("authorized_at", auth), ("accepted_at", accepted), ("feedback_at", feedback), ("edit_at", edit)):
            if value is not None:
                recorded_times.append(value)
                if value < auth:
                    raise Invalid(path + "." + name + " precedes authorization")
        if accepted is not None and outcome != "accepted":
            raise Invalid(path + " nonaccepted outcome cannot have accepted_at")
        if outcome == "accepted" and accepted is None:
            raise Invalid(path + " accepted outcome requires accepted_at")
        if edit is not None and accepted is not None and edit > accepted:
            raise Invalid(path + ".edit_at follows acceptance")
        if feedback is not None and edit is not None and feedback < edit:
            raise Invalid(path + ".feedback_at precedes edit_at")
        if feedback is not None and accepted is not None and feedback > accepted:
            raise Invalid(path + ".feedback_at follows acceptance")
        if now is not None and now < auth:
            raise Invalid("now precedes an authorization timestamp")

        o = dict(raw, auth=auth, accepted=accepted, feedback=feedback, edit=edit)
        for field in ("rescue", "rework", "escaped_defects"):
            if field not in raw:
                raise Invalid(path + " missing " + field)
            o[field] = count(raw[field], path + "." + field)
        for field in ("active_seconds", "control_seconds"):
            if field not in raw:
                raise Invalid(path + " missing " + field)
            o[field] = number(raw[field], path + "." + field)
        if o["control_seconds"] is not None and o["active_seconds"] is not None and o["control_seconds"] > o["active_seconds"]:
            raise Invalid(path + " control_seconds cannot exceed active_seconds")
        o["model_usage"] = number(raw.get("model_usage"), path + ".model_usage")
        o["age_seconds"] = elapsed(now, auth) if now is not None and outcome != "accepted" else None
        observations.append(o)
    if now is not None and any(now < value for value in recorded_times):
        raise Invalid("now precedes a recorded observation timestamp")

    arms = {arm: {} for arm in ("baseline", "candidate")}
    for o in observations:
        arms[o["arm"]][o["pair_id"]] = o
    matched, mismatched, unmatched = [], [], {"baseline": [], "candidate": []}
    compare_fields = BASE_FIELDS + tuple(f for f in EXTRA_FIELDS if f not in allowed)
    for pair in sorted(set(arms["baseline"]) | set(arms["candidate"])):
        b, c = arms["baseline"].get(pair), arms["candidate"].get(pair)
        if b is None or c is None:
            unmatched["candidate" if c is not None else "baseline"].append(pair)
        elif any(b[f] != c[f] for f in compare_fields):
            mismatched.append(pair)
        else:
            matched.append((b, c))

    # Each comparison is complete only when every matched pair supplies both arms.
    def pair_values(field):
        if not matched or any(b[field] is None or c[field] is None for b, c in matched):
            return None
        return [(b[field], c[field]) for b, c in matched]

    accepted_rows = [(b, c) for b, c in matched if b["outcome"] == c["outcome"] == "accepted"]
    all_matched_accepted = bool(matched) and len(accepted_rows) == len(matched)
    lead_pairs = [(elapsed(b["accepted"], b["auth"]), elapsed(c["accepted"], c["auth"])) for b, c in accepted_rows]
    lead_complete = all_matched_accepted and all(b is not None and c is not None for b, c in lead_pairs)
    baseline_lead = median([b for b, _ in lead_pairs]) if lead_complete else None
    candidate_lead = median([c for _, c in lead_pairs]) if lead_complete else None
    lead_difference = candidate_lead - baseline_lead if baseline_lead is not None and candidate_lead is not None else None
    lead_fraction = (baseline_lead - candidate_lead) / baseline_lead if baseline_lead and baseline_lead > 0 and candidate_lead is not None else None

    feedback_pairs = []
    for b, c in matched:
        feedback_pairs.append((elapsed(b["feedback"], b["edit"]), elapsed(c["feedback"], c["edit"])))
    feedback_complete = bool(matched) and all(b is not None and c is not None for b, c in feedback_pairs)
    baseline_feedback = median([b for b, _ in feedback_pairs]) if feedback_complete else None
    candidate_feedback = median([c for _, c in feedback_pairs]) if feedback_complete else None
    feedback_difference = candidate_feedback - baseline_feedback if baseline_feedback is not None and candidate_feedback is not None else None

    rescue_pairs = pair_values("rescue")
    defect_pairs = pair_values("escaped_defects")
    rework_pairs = pair_values("rework")
    active_pairs = pair_values("active_seconds")
    control_pairs = pair_values("control_seconds")
    rescue_diff = median([c - b for b, c in rescue_pairs]) if rescue_pairs is not None else None
    baseline_rescue = median([b for b, _ in rescue_pairs]) if rescue_pairs is not None else None
    candidate_rescue = median([c for _, c in rescue_pairs]) if rescue_pairs is not None else None
    rescue_fraction = (baseline_rescue - candidate_rescue) / baseline_rescue if baseline_rescue and baseline_rescue > 0 else None
    defect_increase = max((c - b for b, c in defect_pairs), default=None) if defect_pairs is not None else None
    overhead_values = None
    if active_pairs is not None and control_pairs is not None:
        overhead_values = []
        for (active_b, active_c), (control_b, control_c) in zip(active_pairs, control_pairs):
            # Baseline overhead is retained for completeness; policy concerns candidate overhead.
            del active_b, control_b
            overhead_values.append(0.0 if active_c == 0 and control_c == 0 else (control_c / active_c if active_c else None))
    overhead = median(overhead_values) if overhead_values is not None and all(v is not None for v in overhead_values) else None

    criteria = {}
    def criterion(name, observed, required, met):
        criteria[name] = {"observed": observed, "required": required, "met": met if required is not None and observed is not None else None}

    criterion("minimum_matched_pairs", len(matched), minimum, len(matched) >= minimum if minimum is not None else None)
    criterion("desired_leadtime_reduction_fraction", lead_fraction, policy["desired_leadtime_reduction_fraction"], lead_fraction >= policy["desired_leadtime_reduction_fraction"] if lead_fraction is not None and policy["desired_leadtime_reduction_fraction"] is not None else None)
    criterion("desired_rescue_reduction_fraction", rescue_fraction, policy["desired_rescue_reduction_fraction"], rescue_fraction >= policy["desired_rescue_reduction_fraction"] if rescue_fraction is not None and policy["desired_rescue_reduction_fraction"] is not None else None)
    criterion("max_escaped_defect_increase", defect_increase, policy["max_escaped_defect_increase"], defect_increase <= policy["max_escaped_defect_increase"] if defect_increase is not None and policy["max_escaped_defect_increase"] is not None else None)
    criterion("max_control_overhead_fraction", overhead, policy["max_control_overhead_fraction"], overhead <= policy["max_control_overhead_fraction"] if overhead is not None and policy["max_control_overhead_fraction"] is not None else None)

    outcomes = {arm: {state: sum(o["outcome"] == state for o in arms[arm].values()) for state in sorted(OUTCOMES)} for arm in arms}
    any_missing_policy = minimum is None or any(policy[k] is None for k in POLICY_FIELDS[1:])
    any_unknown_comparison = any(values is None for values in (rescue_pairs, defect_pairs, rework_pairs, active_pairs, control_pairs)) or overhead is None or lead_fraction is None or rescue_fraction is None
    any_unmatched = bool(unmatched["baseline"] or unmatched["candidate"])
    candidate_failed = any(o["outcome"] == "failed" for o in arms["candidate"].values())
    known_defect_deltas = [c["escaped_defects"] - b["escaped_defects"] for b, c in matched if b["escaped_defects"] is not None and c["escaped_defects"] is not None]
    known_quality_failure = policy["max_escaped_defect_increase"] is not None and any(delta > policy["max_escaped_defect_increase"] for delta in known_defect_deltas)
    known_unmet_numeric = any(
        criteria[name]["met"] is False
        for name in POLICY_FIELDS[1:]
        if criteria[name]["required"] is not None
    )
    if candidate_failed or known_quality_failure or known_unmet_numeric:
        recommendation = "revise"
    elif any_missing_policy or any_unmatched or mismatched or not matched or not all_matched_accepted or any_unknown_comparison or any(c["met"] is None for c in criteria.values()):
        recommendation = "inconclusive"
    else:
        recommendation = "adopt"

    nonaccepted = [{"pair_id": o["pair_id"], "arm": o["arm"], "outcome": o["outcome"], "age_seconds": o["age_seconds"]} for o in observations if o["outcome"] != "accepted"]
    model_usage = {arm: median([o["model_usage"] for o in arms[arm].values()]) if arms[arm] and all(o["model_usage"] is not None for o in arms[arm].values()) else None for arm in arms}
    metrics = {
        "median_baseline_accepted_leadtime_seconds": baseline_lead,
        "median_candidate_accepted_leadtime_seconds": candidate_lead,
        "median_accepted_leadtime_difference_seconds": lead_difference,
        "median_baseline_feedback_latency_seconds": baseline_feedback,
        "median_candidate_feedback_latency_seconds": candidate_feedback,
        "median_feedback_latency_difference_seconds": feedback_difference,
        "median_rescue_difference": rescue_diff,
        "median_rework_difference": median([c - b for b, c in rework_pairs]) if rework_pairs is not None else None,
        "max_escaped_defect_increase": defect_increase,
        "median_candidate_control_overhead_fraction": overhead,
        "median_model_usage": model_usage,
        "median_candidate_unaccepted_age_seconds": median([o["age_seconds"] for o in arms["candidate"].values() if o["age_seconds"] is not None]),
    }
    counts = {
        "observations": len(observations), "matched_pairs": len(matched),
        "mismatched_pairs": mismatched, "unmatched_pairs": unmatched,
        "outcomes": outcomes,
        "failed_attempts": {arm: outcomes[arm]["failed"] for arm in arms},
    }
    return {"recommendation": recommendation, "criteria": criteria, "counts": counts, "attempt_ages": nonaccepted, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(evaluate(json.loads(args.input.read_text())), indent=2, sort_keys=True))
    except (Invalid, OSError, json.JSONDecodeError) as exc:
        print("control-evaluation: %s" % exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
