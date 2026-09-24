#!/usr/bin/env python3
"""Seeded, interleaved diagnostic log with an independent answer checker.

The checker regenerates the log; no expected answer is stored beside a run.
"""

import argparse
import hashlib
import json
from pathlib import Path
import random
import sys


KINDS = ("cache-index", "input-schema", "artifact-store", "worker-lease", "config-parse")


def make_case(seed):
    rng = random.Random(seed)
    incidents = [f"job-{number:02d}" for number in range(1, 15)]
    failed = set(rng.sample(incidents, 5))
    starts = rng.sample(range(140, 4350, 290), len(incidents))
    events = {}
    expected = []
    for incident, start in zip(incidents, starts):
        cause = rng.choice(KINDS)
        code = f"{cause.upper().replace('-', '_')}_{rng.randrange(101, 999)}"
        block = (
            f"phase=prepare job={incident} state=blocked code={code} "
            f"resource={hashlib.blake2s((incident + str(seed)).encode(), digest_size=4).hexdigest()}"
        )
        result_line = start + rng.randrange(30, 95)
        outcome = "failed" if incident in failed else "recovered"
        result = f"phase=complete job={incident} status={outcome} attempts=2"
        events[start] = block
        events[result_line] = result
        if outcome == "failed":
            expected.append({
                "job": incident,
                "code": code,
                "cause_line": start,
                "cause_text": block,
                "failure_line": result_line,
            })
    expected.sort(key=lambda item: item["failure_line"])
    lines = []
    for number in range(1, 4501):
        event = events.get(number)
        if event is None:
            trace_id = hashlib.blake2s(f"{seed}:{number}".encode(), digest_size=5).hexdigest()
            event = f"phase=work trace={trace_id} state=ok detail=" + "x" * 96
        lines.append(f"{number:04d} {event}\n")
    return "".join(lines).encode(), expected


def check(seed, run_dir):
    expected_log, expected_failures = make_case(seed)
    answer = json.loads((run_dir / "answer.json").read_text(encoding="utf-8"))
    manifests = list((run_dir / "logs").glob("*/manifest.json"))
    if len(manifests) != 1:
        raise ValueError("expected exactly one quiet-run manifest")
    manifest_path = manifests[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = (manifest_path.parent / "full.log").read_bytes()
    digest = hashlib.sha256(expected_log).hexdigest()
    if raw != expected_log or manifest.get("status") != "PASS":
        raise ValueError("retained log differs from the seeded fixture")
    evidence = [item for item in manifest.get("evidence", []) if item.get("id") == "full-log"]
    if len(evidence) != 1 or evidence[0].get("sha256") != digest:
        raise ValueError("quiet-run receipt does not match the fixture")
    if answer != {"sha256": digest, "failures": expected_failures}:
        raise ValueError("answer does not identify every failed job and its exact cause")
    print(json.dumps({"accepted": True, "seed": seed, "failures": len(expected_failures), "raw_bytes": len(raw), "sha256": digest}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("emit", "check"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-dir", type=Path)
    args = parser.parse_args()
    if args.command == "emit":
        sys.stdout.buffer.write(make_case(args.seed)[0])
    else:
        if args.run_dir is None:
            parser.error("check requires --run-dir")
        try:
            check(args.seed, args.run_dir)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            parser.exit(2, f"log case: {error}\n")


if __name__ == "__main__":
    main()
