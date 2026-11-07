#!/usr/bin/env python3
"""Refuse to finish a task while its declared goal is unmet.

Thin default for ordinary tasks. Programmes that need claims, decisions and
recovery use tools/outcome_control.py instead.

Goal record (default .agent/goal.json, untracked working state):

    {"goal": "Users can export a monthly report",
     "acceptance": [
       {"id": "tests", "check": "export tests pass", "run": "check"},
       {"id": "owner", "check": "owner accepts the layout",
        "status": "pass", "evidence": "approved in https://example.org/pr/12"}
     ]}

Rules:
- "run" names a Makefile target with a recipe; the item passes only when
  `make <target>` exits 0. Commands are never read from the record. Targets
  that call this gate are refused.
- An item without "run" passes only with "status": "pass" plus "evidence"
  citing a repository file or a URL. "status": "blocked" needs a "blocker"
  sentence naming what is missing.
- Anything else is unmet. A goal needs at least one passing "run" item:
  manual items alone cannot prove it. Recipes that cannot fail (true, :,
  echo) prove nothing.
- Ending with blocked items needs a "reflection" object in the record with
  first_divergence, guidance_followed and guidance_missing_or_misleading,
  each a real sentence.

Exit codes: 0 goal met (or no record, outside hook mode); 2 unmet, with a gap
record written under .agent/gaps/; 1 invalid record.

--hook acts as a Claude Code Stop hook. It blocks the stop while any item is
unmet, up to MAX_BLOCKS times per session, then lets the session end with a
visible warning and a not-met gap record (never an endless loop). With no goal
record and uncommitted changes it asks once per session for a goal record.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path

TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
STATUSES = {"pass", "blocked", "pending", "fail"}
GAP_FIELDS = ("first_divergence", "guidance_followed", "guidance_missing_or_misleading")
MAX_BLOCKS = 3
NO_RECIPE = re.compile(r"Nothing to be done for|is up to date")
CANNOT_FAIL = re.compile(r"^\s*(true|:|exit 0|echo(\s.*)?|printf(\s.*)?)\s*$")
URL = re.compile(r"https?://\S+")


def sentence(value) -> bool:
    """Real text, not a placeholder: at least three words with letters."""
    return text(value) and len(re.findall(r"[A-Za-z]{2,}", value)) >= 3


def cites(root: Path, evidence: str) -> bool:
    """Manual evidence must point at something checkable: a repository file or a URL."""
    if URL.search(evidence):
        return True
    for token in re.findall(r"[\w./-]+", evidence):
        candidate = (root / token).resolve()
        if len(token) > 2 and candidate.is_relative_to(root) and candidate.is_file():
            return True
    return False


class GoalError(ValueError):
    pass


def text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_goal(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoalError(f"cannot read goal record {path}: {exc}") from exc
    if not isinstance(data, dict) or not text(data.get("goal")):
        raise GoalError("goal record needs a non-empty string 'goal'")
    items = data.get("acceptance")
    if not isinstance(items, list) or not items:
        raise GoalError("goal record needs a non-empty 'acceptance' list")
    seen = set()
    for item in items:
        if not isinstance(item, dict) or not text(item.get("id")):
            raise GoalError("each acceptance item needs a string 'id'")
        name = item["id"]
        if name in seen:
            raise GoalError(f"duplicate acceptance id {name!r}")
        seen.add(name)
        if not text(item.get("check")):
            raise GoalError(f"item {name!r} needs a 'check' describing what must be true")
        run = item.get("run")
        if run is not None and not (isinstance(run, str) and TARGET.match(run)):
            raise GoalError(f"item {name!r}: 'run' must be a Makefile target name")
        status = item.get("status")
        if status is not None and not (isinstance(status, str) and status in STATUSES):
            raise GoalError(f"item {name!r}: status must be one of {sorted(STATUSES)}")
        for key in ("evidence", "blocker"):
            if key in item and not isinstance(item[key], str):
                raise GoalError(f"item {name!r}: {key} must be a string")
    return data


def run_target(root: Path, target: str, timeout: int) -> tuple[str, str | None]:
    make = ["make", "--no-print-directory"]
    try:
        dry = subprocess.run(make + ["-n", target], cwd=root, capture_output=True, text=True,
                             timeout=60, check=False)
        if dry.returncode == 0 and (NO_RECIPE.search(dry.stdout + dry.stderr) or not dry.stdout.strip()):
            return "unmet", f"make {target} has no recipe, so it proves nothing"
        if "finish_check" in dry.stdout:
            return "unmet", f"make {target} calls the finish gate itself"
        if all(CANNOT_FAIL.match(line) for line in dry.stdout.splitlines() if line.strip()):
            return "unmet", f"make {target} only runs commands that cannot fail, so it proves nothing"
        proc = subprocess.Popen(make + [target], cwd=root, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, start_new_session=True)
    except FileNotFoundError:
        return "unmet", "make is not installed"
    except subprocess.TimeoutExpired:
        return "unmet", f"make -n {target} timed out"
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)  # the whole tree, so nothing is orphaned
        proc.wait()
        return "unmet", f"make {target} timed out after {timeout}s"
    return ("met", None) if code == 0 else ("unmet", f"make {target} exited {code}")


def evaluate(goal: dict, root: Path, timeout: int) -> list[dict]:
    results, cache = [], {}
    for item in goal["acceptance"]:
        run = item.get("run")
        if run:
            if run not in cache:
                cache[run] = run_target(root, run, timeout)
            state, why = cache[run]
        elif item.get("status") == "pass" and text(item.get("evidence")) and cites(root, item["evidence"]):
            state, why = "met", None
        elif item.get("status") == "pass":
            state, why = "unmet", "status pass without evidence citing a repository file or URL"
        elif item.get("status") == "blocked" and sentence(item.get("blocker")):
            state, why = "blocked", item["blocker"]
        else:
            state, why = "unmet", f"status is {item.get('status', 'missing')}"
        results.append({"id": item["id"], "check": item["check"], "state": state, "why": why})
    machine = [r for item, r in zip(goal["acceptance"], results) if item.get("run")]
    if not any(r["state"] == "met" for r in machine):
        results.append({"id": "machine-check", "check": "at least one passing run check", "state": "unmet",
                        "why": "no passing run check: manual items alone cannot prove the goal"})
    return results


def write_gap(root: Path, goal: dict, results: list[dict], ended: bool = False) -> Path:
    gaps = root / ".agent" / "gaps"
    gaps.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    unmet = [r for r in results if r["state"] != "met"]
    record = {
        "schema": "finish-gap/v1",
        "recorded_at": stamp,
        "goal": goal["goal"],
        "status": "blocked" if all(r["state"] == "blocked" for r in unmet) else "not-met",
        "session_ended_unmet": ended,
        "unmet": unmet,
    }
    # Copied from the goal record's reflection; unknown stays null rather than invented.
    reflection = goal.get("reflection") if isinstance(goal.get("reflection"), dict) else {}
    record.update({field: reflection.get(field) if text(reflection.get(field)) else None for field in GAP_FIELDS})
    path = gaps / f"gap-{stamp}.json"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def summary(results: list[dict]) -> str:
    return "; ".join(f"{r['id']}: {r['why']}" for r in results if r["state"] != "met")


def bump(root: Path, session: str, key: str) -> int:
    """Count hook blocks per session so the hook can never loop forever."""
    path = root / ".agent" / "finish-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            state = {}
    except (OSError, ValueError):
        state = {}
    entry = f"{session}:{key}"
    state[entry] = int(state.get(entry, 0)) + 1 if isinstance(state.get(entry, 0), int) else 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state) + "\n", encoding="utf-8")
    return state[entry]


def changed(root: Path) -> bool:
    """Uncommitted changes, or commits not yet on the upstream or the default branch."""
    def run(*args):
        try:
            return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None
    status = run("status", "--porcelain", "--untracked-files=normal")
    if status is None or status.returncode != 0:
        return False
    if any(not line[3:].startswith(".agent/") for line in status.stdout.splitlines()):
        return True
    for upstream in ("@{u}", "origin/HEAD", "origin/main", "origin/master"):
        ahead = run("rev-list", "--count", f"{upstream}..HEAD")
        if ahead is not None and ahead.returncode == 0:
            return ahead.stdout.strip() not in ("", "0")
    return False


def reflected(goal: dict) -> bool:
    reflection = goal.get("reflection")
    return isinstance(reflection, dict) and all(sentence(reflection.get(field)) for field in GAP_FIELDS)


def remember(root: Path, session: str, goal: dict | None = None) -> dict | None:
    """Store this session's goal so deleting the record cannot end the session silently."""
    path = root / ".agent" / "finish-state.json"
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        state = state if isinstance(state, dict) else {}
    except (OSError, ValueError):
        state = {}
    key = f"goal:{session}"
    if goal is None:
        saved = state.get(key)
        return saved if isinstance(saved, dict) else None
    state[key] = goal
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state) + "\n", encoding="utf-8")
    return goal


def block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


def hook(root: Path, goal_path: Path, event: dict, timeout: int) -> int:
    session = str(event.get("session_id") or "unknown")
    if not goal_path.exists():
        saved = remember(root, session)
        if saved and text(saved.get("goal")):
            count = bump(root, session, "goal-removed")
            if count <= MAX_BLOCKS:
                return block("The goal record was removed before the goal was met. Restore .agent/goal.json "
                             f"and finish the work, or mark real blockers ({count}/{MAX_BLOCKS}).")
            gap = write_gap(root, saved, [{"id": "goal-record", "check": "goal record present", "state": "unmet",
                                           "why": "goal record removed"}], ended=True).relative_to(root)
            print(json.dumps({"systemMessage": f"finish-check: session ended after its goal record was removed; "
                                               f"goal NOT verified. Gap record: {gap}"}))
            return 0
        if changed(root) and bump(root, session, "no-goal") == 1:
            return block("You changed files without a goal record. Write .agent/goal.json with the goal and "
                         "the checks that prove it (see python3 tools/finish_check.py --help), then finish. "
                         "For a trivial change, one manual item with status pass and evidence is enough.")
        return 0
    try:
        goal = load_goal(goal_path)
    except GoalError as exc:
        if bump(root, session, "invalid") <= MAX_BLOCKS:
            return block(f"Fix the goal record before finishing: {exc}")
        print(json.dumps({"systemMessage": f"finish-check: goal record still invalid ({exc}); session ended unchecked."}))
        return 0
    remember(root, session, goal)
    results = evaluate(goal, root, timeout)
    if all(r["state"] == "met" for r in results):
        return 0
    key = "unmet:" + hashlib.sha256(goal["goal"].encode()).hexdigest()[:12]
    if all(r["state"] in ("met", "blocked") for r in results) and reflected(goal):
        write_gap(root, goal, results)
        return 0  # every remaining item names a real blocker and the process was reflected on
    if all(r["state"] in ("met", "blocked") for r in results):
        results = results + [{"id": "reflection", "check": "reflection filled", "state": "unmet",
                              "why": "fill reflection." + ", reflection.".join(GAP_FIELDS) + " in the goal record"}]
    count = bump(root, session, key)
    if count <= MAX_BLOCKS:
        gap = write_gap(root, goal, results).relative_to(root)
        return block(f"Goal not met ({count}/{MAX_BLOCKS}): {summary(results)}. Continue until each check "
                     f"passes. If a real blocker prevents it, mark the item blocked with the blocker and fill "
                     f"{', '.join(GAP_FIELDS)} in {gap}.")
    gap = write_gap(root, goal, results, ended=True).relative_to(root)
    print(json.dumps({"systemMessage": f"finish-check: session ended with the goal NOT met: {summary(results)}. "
                                       f"Gap record: {gap}"}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--goal", default=".agent/goal.json")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--hook", action="store_true", help="act as a Claude Code Stop hook")
    args = parser.parse_args(argv)

    event = {}
    if args.hook:
        try:
            event = json.loads(sys.stdin.read() or "{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            event = {}
        if not isinstance(event, dict):
            event = {}
    cwd = event.get("cwd") if isinstance(event.get("cwd"), str) else None
    root = Path(args.root if args.root != "." else cwd or ".").resolve()
    goal_path = root / args.goal
    if args.hook:
        return hook(root, goal_path, event, args.timeout)
    if not goal_path.exists():
        return 0
    try:
        goal = load_goal(goal_path)
    except GoalError as exc:
        print(f"finish-check: {exc}", file=sys.stderr)
        return 1
    results = evaluate(goal, root, args.timeout)
    if all(r["state"] == "met" for r in results):
        print(f"finish-check: goal met ({len(results)} checks)")
        return 0
    gap = write_gap(root, goal, results).relative_to(root)
    print(f"finish-check: goal not met: {summary(results)}; gap record {gap}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
