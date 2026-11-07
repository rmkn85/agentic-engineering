#!/usr/bin/env python3
"""Behavioural trials: does an agent actually follow the guidance, and does it help?

A scenario (validation/trials/scenarios/<id>.json) gives a realistic task and
the deterministic checks that show the guided behaviour happened:

    {"id": "research-intake", "claim": "what the guidance should cause",
     "task": "the task text given to the agent", "checks": ["goal-record", ...]}

  prepare  make a fresh local clone for one arm and print the agent prompt.
           Arm "guided" prepends the repository instructions a host would
           auto-load (AGENTS.md, CLAUDE.md); arm "unguided" replaces them with
           a one-line stub. Give the prompt to a fresh agent session.
  score    run the scenario's checks in that clone and append the result to
           validation/trials/results.jsonl.

Checks come from a fixed registry below; scenarios cannot run commands.
A trial shows what one agent did once; compare arms over repeated runs before
claiming an effect.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

STATE = ".trial.json"
STUB = "# AGENTS.md\n\nPublic repository of guidance for coding agents.\n"


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def make(cwd: Path, *args: str, timeout: int = 900) -> bool:
    try:
        return subprocess.run(["make", "--no-print-directory", *args], cwd=cwd, capture_output=True,
                              text=True, timeout=timeout, check=False).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def changed(clone: Path, start: str) -> list[str]:
    tracked = git(clone, "diff", "--name-only", start, "--").stdout.splitlines()
    untracked = git(clone, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted(set(tracked) | set(untracked))


def check_goal_record(clone: Path, start: str) -> bool:
    path = clone / ".agent" / "goal.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(data, dict) and bool(data.get("goal")) and bool(data.get("acceptance"))


def check_added_test(clone: Path, start: str) -> bool:
    sys.path.insert(0, str(clone / "tools"))
    try:
        from check_guidance_budget import substantive  # the repository's own definition of evidence
    except ImportError:
        return False
    finally:
        sys.path.pop(0)
    return any(p.startswith("tools/tests/") and substantive(clone, start, p) for p in changed(clone, start))


def check_no_unpaid_prose(clone: Path, start: str) -> bool:
    return make(clone, "guidance-delta", f"BASE={start}")


def failing_tests(clone: Path) -> list[str] | None:
    try:
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tools/tests"], cwd=clone,
                                capture_output=True, text=True, timeout=900, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return sorted(set(re.findall(r"^(?:FAIL|ERROR): (\S+ \([^)]*\))", result.stderr, re.M)))


def check_suite(clone: Path, start: str) -> bool:
    """No test fails that did not already fail before the agent started (arms differ in setup)."""
    state = json.loads((clone / STATE).read_text(encoding="utf-8"))
    before, after = state.get("failing_before"), failing_tests(clone)
    if before is None or after is None:
        return False
    return set(after) <= set(before)


def check_finish_gate(clone: Path, start: str) -> bool:
    return (clone / ".agent" / "goal.json").exists() and make(clone, "finish-check")


def check_proofs(clone: Path, start: str) -> bool:
    return make(clone, "prove")


CHECKS = {
    "goal-record": check_goal_record,
    "added-test": check_added_test,
    "no-unpaid-prose": check_no_unpaid_prose,
    "suite": check_suite,
    "finish-gate": check_finish_gate,
    "proofs": check_proofs,
}


def load(root: Path, scenario: str) -> dict:
    data = json.loads((root / "validation" / "trials" / "scenarios" / f"{scenario}.json").read_text(encoding="utf-8"))
    unknown = [c for c in data.get("checks", []) if c not in CHECKS]
    if unknown or not data.get("task") or not data.get("checks"):
        raise ValueError(f"scenario {scenario}: needs task and known checks (unknown: {unknown})")
    return data


def prepare(root: Path, scenario: str, arm: str, out: Path) -> str:
    data = load(root, scenario)
    if out.exists():
        raise ValueError(f"{out} exists; trials need a fresh directory")
    result = git(root, "clone", "-q", "--no-hardlinks", str(root), str(out))
    if result.returncode != 0:
        raise ValueError(result.stderr.strip())
    start = git(out, "rev-parse", "HEAD").stdout.strip()
    instructions = ""
    if arm == "guided":
        for name in ("AGENTS.md", "CLAUDE.md"):
            if (out / name).exists():
                text = (out / name).read_text(encoding="utf-8")
                if name == "CLAUDE.md":
                    text = text.replace("@AGENTS.md", "")
                instructions += f"\n--- {name} (auto-loaded by your host) ---\n{text.strip()}\n"
    else:
        (out / "AGENTS.md").write_text(STUB, encoding="utf-8")
        if (out / "CLAUDE.md").exists():
            (out / "CLAUDE.md").unlink()
        git(out, "-c", "user.email=trial@example.invalid", "-c", "user.name=trial", "commit", "-qam", "unguided arm")
        start = git(out, "rev-parse", "HEAD").stdout.strip()
    baseline = failing_tests(out) if "suite" in data["checks"] else []
    (out / STATE).write_text(json.dumps({"scenario": scenario, "arm": arm, "start": start,
                                         "failing_before": baseline}) + "\n", encoding="utf-8")
    exclude = out / ".git" / "info" / "exclude"
    exclude.write_text(exclude.read_text(encoding="utf-8") + f"\n{STATE}\n", encoding="utf-8")
    prompt = (f"You are a coding agent working in the git repository at {out}. "
              "Work only inside that directory; do not push or open pull requests.\n")
    if instructions:
        prompt += "\nRepository instructions:" + instructions
    return prompt + f"\nTask:\n{data['task']}\n"


def score(root: Path, clone: Path, label: str) -> dict:
    state = json.loads((clone / STATE).read_text(encoding="utf-8"))
    data = load(root, state["scenario"])
    results = {name: CHECKS[name](clone, state["start"]) for name in data["checks"]}
    record = {"scenario": state["scenario"], "arm": state["arm"], "agent": label,
              "date": dt.date.today().isoformat(), "checks": results,
              "passed": sum(results.values()), "total": len(results),
              "changed_files": changed(clone, state["start"])}
    ledger = root / "validation" / "trials" / "results.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as out:
        out.write(json.dumps(record) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("scenario")
    p.add_argument("--arm", choices=("guided", "unguided"), required=True)
    p.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("clone")
    s.add_argument("--agent", required=True, help="label of the agent and settings that ran the trial")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        if args.command == "prepare":
            print(prepare(root, args.scenario, args.arm, Path(args.out).resolve()))
        else:
            record = score(root, Path(args.clone).resolve(), args.agent)
            print(json.dumps({k: record[k] for k in ("scenario", "arm", "agent", "checks", "passed", "total")}))
    except (OSError, ValueError, KeyError) as exc:
        print(f"trial: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
