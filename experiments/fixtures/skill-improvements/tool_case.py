#!/usr/bin/env python3
"""Dependency-free tool catalogue for a progressive disclosure behavior trial."""

import argparse
import hashlib
import json
from pathlib import Path


SUBJECTS = ("build", "test", "docs", "release")
SOURCES = ("live", "archive", "snapshot")


def catalogue(seed):
    items = []
    for subject in SUBJECTS:
        for source in SOURCES:
            name = f"inspect_{subject}_{source}"
            items.append({
                "name": name,
                "summary": f"Inspect {source} {subject} records.",
                "description": (
                    f"Inspect the {source} {subject} record selected by record_id. "
                    "Use this when a local trial requests status and evidence for one record. "
                    "The mode argument selects summary or full evidence. The include_history "
                    "argument includes earlier states, and threshold selects a numeric cutoff. "
                    "This deterministic tool has no network access or side effects. "
                    f"Do not use it for other sources or subjects; this tool is for {source} {subject} records."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "record_id": {"type": "string", "description": "Record identifier"},
                        "mode": {"type": "string", "enum": ["summary", "full"], "default": "summary"},
                        "include_history": {"type": "boolean", "default": False},
                        "threshold": {"type": "number", "default": 0.5},
                    },
                    "required": ["record_id"],
                },
            })
    offset = seed % len(items)
    return items[offset:] + items[:offset]


def target(seed):
    return catalogue(seed)[(seed * 7 + 3) % 12]


def result(seed, name, record_id, mode):
    digest = hashlib.sha256(f"{seed}:{name}:{record_id}:{mode}".encode()).hexdigest()[:16]
    return {"tool": name, "record_id": record_id, "mode": mode, "status": "ready", "evidence_id": digest}


def append_trace(run_dir, event):
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "actions.jsonl").open("a", encoding="utf-8") as trace:
        trace.write(json.dumps(event, sort_keys=True) + "\n")


def check(seed, run_dir):
    answer = json.loads((run_dir / "answer.json").read_text(encoding="utf-8"))
    actions = [json.loads(line) for line in (run_dir / "actions.jsonl").read_text(encoding="utf-8").splitlines()]
    selected = target(seed)["name"]
    expected = result(seed, selected, "R-42", "full")
    if answer != expected:
        raise ValueError("answer differs from the selected tool result")
    if not any(item.get("action") == "call" and item.get("tool") == selected and item.get("result") == expected for item in actions):
        raise ValueError("the selected tool was not called")
    response_bytes = sum(item.get("response_bytes", 0) for item in actions)
    print(json.dumps({
        "accepted": True,
        "seed": seed,
        "selected_tool": selected,
        "actions": len(actions),
        "response_payload_bytes": response_bytes,
        "index_used": any(item.get("action") == "list_index" for item in actions),
        "schema_lookups": sum(item.get("action") == "schema" for item in actions),
        "wrong_calls": sum(item.get("action") == "call" and item.get("tool") != selected for item in actions),
    }))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("scenario", "list", "schema", "call", "check"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--detail", choices=("full", "index"), default="full")
    parser.add_argument("--name")
    parser.add_argument("--record-id", default="R-42")
    parser.add_argument("--mode", choices=("summary", "full"), default="full")
    args = parser.parse_args()
    tools = catalogue(args.seed)
    chosen = target(args.seed)
    if args.command == "scenario":
        print(f"Get the full status for {chosen['name'].split('_')[2]} {chosen['name'].split('_')[1]} record R-42. Return the exact JSON result from the appropriate tool as answer.json.")
        return
    if args.command == "check":
        try:
            check(args.seed, args.run_dir)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            parser.exit(2, f"tool case: {error}\n")
        return
    if args.command == "list":
        payload = tools if args.detail == "full" else [{"name": item["name"], "summary": item["summary"]} for item in tools]
        action = "list_full" if args.detail == "full" else "list_index"
    else:
        item = next((item for item in tools if item["name"] == args.name), None)
        if item is None:
            parser.error("unknown --name")
        if args.command == "schema":
            payload = item
            action = "schema"
        else:
            payload = result(args.seed, item["name"], args.record_id, args.mode)
            action = "call"
    output = json.dumps(payload, sort_keys=True)
    event = {"action": action, "response_bytes": len(output.encode("utf-8"))}
    if args.command in ("schema", "call"):
        event["tool"] = args.name
    if args.command == "call":
        event["result"] = payload
    append_trace(args.run_dir, event)
    print(output)


if __name__ == "__main__":
    main()
