#!/usr/bin/env python3
"""Native lifecycle adapters for the repository's existing audit and finish gate.

Scope: cooperative local agents, reviewed host hooks and maintained Make targets.
Discovery and hook trust belong to the host. A configured file or this program's
own receipt is not proof that a host invoked it. No model or network calls occur.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TOOLS = Path(__file__).resolve().parent


def invoke(name: str, root: Path, *args: str, event: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / name), "--root", str(root), *args],
                          input=json.dumps(event) if event is not None else None,
                          capture_output=True, text=True, timeout=600, check=False)


def record(root: Path, host: str, event: str, payload: dict, response: dict) -> None:
    folder = root / ".agent"
    folder.mkdir(exist_ok=True)
    row = {"schema": "agent-hook-event/v1", "host": host, "event": event,
           "session": payload.get("session_id"), "turn": payload.get("turn_id"),
           "time": dt.datetime.now(dt.timezone.utc).isoformat(),
           "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "decision": response.get("decision", "continue")}
    with (folder / "hook-events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True) + "\n")


def start(root: Path) -> dict:
    result = invoke("work_audit.py", root, "--json")
    if result.returncode:
        raise ValueError("work audit failed: " + result.stderr[-1000:])
    report = json.loads(result.stdout)
    triggers = []
    if any(f.get("kind") in {"loop", "repeat"} for f in report.get("findings", [])):
        triggers.append("repetition")
    if (root / ".agent/goal.json").exists() and (root / ".agent/goal-status.json").exists():
        inspected = invoke("finish_check.py", root, "--inspect")
        if json.loads(inspected.stdout).get("state") != "verified":
            triggers.append("stale-evidence")
    for trigger in triggers:
        marked = invoke("finish_check.py", root, "--trigger", trigger)
        if marked.returncode:
            raise ValueError("cannot record correction trigger: " + marked.stderr[-1000:])
    focus = report.get("focus", "Inspect the current task and acceptance.")
    context = "Work audit: " + focus
    if triggers:
        context += " A corrective obligation is recorded: " + ", ".join(triggers) + "."
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}


def stop(root: Path, event: dict) -> dict:
    result = invoke("finish_check.py", root, "--hook", event=event)
    if result.returncode:
        raise ValueError("finish gate failed: " + (result.stderr or result.stdout)[-1000:])
    response = json.loads(result.stdout) if result.stdout.strip() else {"continue": True}
    if not isinstance(response, dict):
        raise ValueError("finish gate returned no object")
    return response


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("codex", "claude"), required=True)
    parser.add_argument("--event", choices=("start", "stop"), required=True)
    parser.add_argument("--root")
    args = parser.parse_args(argv)
    try:
        event = json.loads(sys.stdin.read() or "{}")
        if not isinstance(event, dict):
            raise ValueError("hook input must be an object")
        cwd = args.root or event.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            raise ValueError("hook input must identify its working directory")
        location = Path(cwd).resolve(strict=True)
        repository = subprocess.run(['git', '-C', str(location), 'rev-parse', '--show-toplevel'],
                                    capture_output=True, text=True, timeout=30, check=False)
        if repository.returncode:
            raise ValueError('hook working directory must belong to a repository')
        root = Path(repository.stdout.strip()).resolve(strict=True)
        response = start(root) if args.event == "start" else stop(root, event)
        record(root, args.host, args.event, event, response)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        # End unchecked on adapter failure; never convert it to goal acceptance or
        # loop on a broken hook. The host shows the exact failure for recovery.
        response = {"continue": False, "stopReason": "Outcome controls unavailable: " + str(error),
                    "systemMessage": "Goal NOT verified; repair the native hook before relying on its result."}
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
