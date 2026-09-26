#!/usr/bin/env python3
"""Offline, engine/agent-neutral practice feedback. Never executes evidence or sends it anywhere."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

STAGES = {"not_used", "selected", "loaded", "applied"}
BASES = {"self_report", "tool_trace", "independent_review"}
OUTCOMES = {"accepted", "rejected", "blocked", "unverified"}
COUNTS = ("preventable_corrections", "creative_changes", "structural_regressions", "rework_cycles")
MEASURES = ("wall_seconds", "tokens", "instruction_bytes", "first_actionable_failure_seconds")
LIMIT = 1024 * 1024  # Bounded receipts, not a limit on retained native logs.


def require(ok, message):
    if not ok:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def load_record(path):
    path = Path(path)
    require(path.stat().st_size <= LIMIT, "receipt exceeds 1 MiB")
    def invalid_constant(value):
        raise ValueError("nonfinite JSON number: " + value)
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=invalid_constant,
                      object_pairs_hook=unique_object)


def check_reference(ref, root):
    """Resolve only relative files within an explicitly authorized evidence root."""
    require(isinstance(ref, dict), "evidence reference must be an object")
    require(text(ref.get("path")), "evidence path required")
    path = Path(ref["path"])
    require(not path.is_absolute() and ".." not in path.parts, "evidence path must stay inside its root")
    require(re.fullmatch(r"[0-9a-f]{64}", ref.get("sha256", "")) is not None, "sha256 required")
    lines = ref.get("lines")
    if lines is not None:
        require(isinstance(lines, list) and len(lines) == 2 and
                all(type(n) is int and n > 0 for n in lines) and lines[0] <= lines[1], "invalid line range")
    if root is None:
        return {"path": ref["path"], "state": "unchecked"}
    root = Path(root).resolve()
    target = (root / path).resolve()
    require(target.is_relative_to(root), "evidence symlink escapes its root")
    if not target.is_file():
        return {"path": ref["path"], "state": "missing"}
    digest = hashlib.sha256()
    found_end = lines is None
    with target.open("rb") as stream:
        if lines is None:
            for block in iter(lambda: stream.read(65536), b""):
                digest.update(block)
        else:
            for index, line in enumerate(stream, 1):
                if index >= lines[0]:
                    digest.update(line)
                if index == lines[1]:
                    found_end = True
                    break
    state = "matched" if found_end and digest.hexdigest() == ref["sha256"] else "mismatch"
    return {"path": ref["path"], "state": state}


def references(refs, root):
    require(isinstance(refs, list), "evidence must be an array")
    require(len(refs) <= 100, "too many evidence references; retain a focused receipt")
    result = [check_reference(ref, root) for ref in refs]
    return result, bool(result) and all(ref["state"] == "matched" for ref in result)


def analyze(record, root=None):
    require(isinstance(record, dict) and record.get("schema") == "practice-feedback/v1", "invalid feedback schema")
    for key in ("run_id", "source", "task_class"):
        require(text(record.get(key)), key + " required")
    require(record.get("record_kind") in {"agent_run", "manual_review", "fixture"}, "record_kind required")
    practices = record.get("practices")
    require(isinstance(practices, list) and len(practices) <= 100, "bounded practices array required")
    rows, seen = [], set()
    for practice in practices:
        require(isinstance(practice, dict), "practice must be an object")
        for key in ("id", "revision", "trigger", "decision"):
            require(text(practice.get(key)), "practice " + key + " required")
        key = (practice["id"], practice["revision"])
        require(key not in seen, "duplicate practice/revision; combine its evidence")
        seen.add(key)
        require(practice.get("stage") in STAGES and practice.get("basis") in BASES, "invalid stage/basis")
        refs, matched = references(practice.get("evidence"), root)
        rows.append({key: practice[key] for key in ("id", "revision", "stage", "basis", "trigger", "decision")})
        rows[-1].update(evidence=refs, evidence_resolved=matched)
    outcome = record.get("outcome")
    require(isinstance(outcome, dict) and outcome.get("status") in OUTCOMES, "invalid outcome")
    refs, matched = references(outcome.get("evidence"), root)
    counts = {}
    for key in COUNTS:
        value = outcome.get(key)
        require(value is None or type(value) is int and value >= 0, "invalid count: " + key)
        counts[key] = value
    measurements = record.get("measurements", {})
    require(isinstance(measurements, dict), "measurements must be an object")
    for key, value in measurements.items():
        require(key in MEASURES, "unknown measurement: " + key)
        require(value is None or type(value) in (int, float) and math.isfinite(value) and value >= 0,
                "invalid measurement: " + key)
    return {"run_id": record["run_id"], "source": record["source"], "task_class": record["task_class"],
            "record_kind": record["record_kind"], "practices": rows,
            "outcome_reported": outcome["status"], "outcome_evidence_resolved": matched,
            "outcome_evidence": refs, "counts": counts,
            "measurements": {key: measurements.get(key) for key in MEASURES}}


def summarize(results):
    require(bool(results), "no feedback records")
    ids = [result["run_id"] for result in results]
    require(len(set(ids)) == len(ids), "duplicate run_id; retries need separate attempt identities")
    cohorts = {}
    for result in results:
        key = (result["record_kind"], result["task_class"])
        cohorts.setdefault(key, []).append(result)
    groups = []
    for (kind, task), runs in sorted(cohorts.items()):
        meters = {}
        for field in COUNTS + MEASURES:
            values = [run["counts" if field in COUNTS else "measurements"][field] for run in runs]
            known = [value for value in values if value is not None]
            meters[field] = {"known": len(known), "total_runs": len(runs),
                             "observed_sum": sum(known) if known else None,
                             "mean_known": sum(known) / len(known) if known else None}
        practices = Counter((p["id"], p["revision"], p["stage"], p["basis"], p["evidence_resolved"])
                            for run in runs for p in run["practices"])
        groups.append({"record_kind": kind, "task_class": task, "runs": len(runs),
                       "reported_outcomes": dict(Counter(run["outcome_reported"] for run in runs)),
                       "outcomes_with_resolved_evidence": sum(run["outcome_evidence_resolved"] for run in runs),
                       "measurements": meters,
                       "practices": [{"id": k[0], "revision": k[1], "stage": k[2], "basis": k[3],
                                      "evidence_resolved": k[4], "runs": n} for k, n in sorted(practices.items())]})
    return {"schema": "practice-feedback-summary/v1", "runs": len(results), "cohorts": groups,
            "limitation": "Digest matches prove artifact identity, not truthful attribution, independent review, completeness, or causal improvement."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", nargs="+")
    parser.add_argument("--evidence-root", type=Path, help="explicit authorized root; omitted references remain unchecked")
    parser.add_argument("--output", type=Path, help="retain detailed report privately; stdout stays compact")
    args = parser.parse_args()
    try:
        results = [analyze(load_record(path), args.evidence_root) for path in args.records]
        report = summarize(results)
        if args.output:
            require(args.output.resolve() not in {Path(p).resolve() for p in args.records}, "output would overwrite a receipt")
            # A diagnostic summarizer never overwrites an existing artifact.
            with args.output.open("x", encoding="utf-8") as stream:
                json.dump({**report, "details": results}, stream, indent=2, allow_nan=False)
                stream.write("\n")
        print(json.dumps(report, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(json.dumps({"schema": "practice-feedback-summary/v1", "state": "INVALID", "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
