#!/usr/bin/env python3
"""Refuse to finish a task while its declared goal is unmet.

Thin default for ordinary tasks. Programmes that need claims, decisions and
recovery use tools/outcome_control.py instead.

Goal record (default .agent/goal.json, untracked working state):

    {"goal": "...",
     "acceptance": [
       {"id": "tests", "check": "what must be true", "run": "check"},
       {"id": "ux", "check": "human-judged result", "status": "pending"}
     ]}

An item with "run" names a Makefile target; it passes only when `make <target>`
exits 0. Commands are never read from the record. An item without "run" passes
only with "status": "pass"; "blocked" also needs a "blocker" naming what is
missing. Anything else is unmet.

Exit 0: all items met, or no goal record (not opted in).
Exit 2: unmet items; a gap record is written under .agent/gaps/.
Exit 1: invalid goal record.

--hook reads a Claude Code Stop hook event on stdin. On the first stop with
unmet items it prints a block decision so the agent continues; if the agent
stops again it allows the stop and keeps the gap record.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
STATUSES = {"pass", "blocked", "pending", "fail"}
GAP_FIELDS = ("first_divergence", "guidance_followed", "guidance_missing_or_misleading")


class GoalError(ValueError):
    pass


def load_goal(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GoalError(f"cannot read goal record {path}: {exc}") from exc
    if not isinstance(data, dict) or not str(data.get("goal", "")).strip():
        raise GoalError("goal record needs a non-empty 'goal'")
    items = data.get("acceptance")
    if not isinstance(items, list) or not items:
        raise GoalError("goal record needs a non-empty 'acceptance' list")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not str(item.get("id", "")).strip():
            raise GoalError("each acceptance item needs an 'id'")
        if item["id"] in seen:
            raise GoalError(f"duplicate acceptance id {item['id']!r}")
        seen.add(item["id"])
        if not str(item.get("check", "")).strip():
            raise GoalError(f"item {item['id']!r} needs a 'check' describing what must be true")
        run = item.get("run")
        if run is not None and not (isinstance(run, str) and TARGET.match(run)):
            raise GoalError(f"item {item['id']!r}: 'run' must be a Makefile target name")
        status = item.get("status")
        if status is not None and status not in STATUSES:
            raise GoalError(f"item {item['id']!r}: status must be one of {sorted(STATUSES)}")
    return data


def evaluate(goal: dict, root: Path, timeout: int) -> list[dict]:
    results, cache = [], {}
    for item in goal["acceptance"]:
        run = item.get("run")
        if run:
            if run not in cache:
                try:
                    proc = subprocess.run(["make", "--no-print-directory", run], cwd=root,
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                          timeout=timeout, check=False)
                    cache[run] = ("met", None) if proc.returncode == 0 else (
                        "unmet", f"make {run} exited {proc.returncode}")
                except subprocess.TimeoutExpired:
                    cache[run] = ("unmet", f"make {run} timed out after {timeout}s")
            state, why = cache[run]
        elif item.get("status") == "pass":
            state, why = "met", None
        elif item.get("status") == "blocked" and str(item.get("blocker", "")).strip():
            state, why = "blocked", item["blocker"]
        else:
            state, why = "unmet", f"status is {item.get('status', 'missing')}"
        results.append({"id": item["id"], "check": item["check"], "state": state, "why": why})
    return results


def write_gap(root: Path, goal: dict, results: list[dict]) -> Path:
    gaps = root / ".agent" / "gaps"
    gaps.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    record = {
        "schema": "finish-gap/v1",
        "recorded_at": stamp,
        "goal": goal["goal"],
        "status": "blocked" if all(r["state"] != "unmet" for r in results) else "not-met",
        "unmet": [r for r in results if r["state"] != "met"],
    }
    # Filled by the agent; unknown stays null rather than invented.
    record.update({field: None for field in GAP_FIELDS})
    path = gaps / f"gap-{stamp}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def summary(results: list[dict]) -> str:
    return "; ".join(f"{r['id']}: {r['why']}" for r in results if r["state"] != "met")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--goal", default=".agent/goal.json")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--hook", action="store_true", help="act as a Claude Code Stop hook")
    args = parser.parse_args(argv)

    event = {}
    if args.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError:
            event = {}
    root = Path(args.root if args.root != "." else event.get("cwd") or ".").resolve()
    goal_path = root / args.goal
    if not goal_path.exists():
        return 0
    try:
        goal = load_goal(goal_path)
    except GoalError as exc:
        if args.hook:
            if not event.get("stop_hook_active"):
                print(json.dumps({"decision": "block", "reason": f"Fix the goal record before finishing: {exc}"}))
            return 0
        print(f"finish-check: {exc}", file=sys.stderr)
        return 1

    results = evaluate(goal, root, args.timeout)
    if all(r["state"] == "met" for r in results):
        if not args.hook:
            print(f"finish-check: goal met ({len(results)} checks)")
        return 0

    gap = write_gap(root, goal, results)
    rel = gap.relative_to(root)
    if args.hook:
        if event.get("stop_hook_active"):
            return 0  # second stop: allow it; the gap record stays for review
        print(json.dumps({"decision": "block", "reason": (
            f"Goal not met: {summary(results)}. Continue until each check passes. "
            f"If a real blocker prevents it, mark the item blocked with the blocker and fill "
            f"{', '.join(GAP_FIELDS)} in {rel}.")}))
        return 0
    print(f"finish-check: goal not met: {summary(results)}; gap record {rel}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
