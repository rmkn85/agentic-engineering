#!/usr/bin/env python3
"""Route a seeded request through the direct or compressed MCP catalogue."""

import argparse
import asyncio
import json
from pathlib import Path
import shutil
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


DOMAINS = ("build", "test", "deploy", "docs", "security", "metrics", "release", "review")
SERVER = Path(__file__).resolve().parents[1] / "mcp-compressor" / "server.py"


def target(seed):
    return f"inspect_{DOMAINS[seed % len(DOMAINS)]}"


def append_trace(run_dir, event):
    run_dir.mkdir(parents=True, exist_ok=True)
    with (run_dir / "actions.jsonl").open("a", encoding="utf-8") as trace:
        trace.write(json.dumps(event, sort_keys=True) + "\n")


async def request(args):
    args.run_dir.mkdir(parents=True, exist_ok=True)
    if args.variant == "compressed":
        compressor = shutil.which("mcp-compressor")
        if not compressor:
            raise ValueError("mcp-compressor is not on PATH")
        params = StdioServerParameters(command=compressor, args=["-c", "medium", "--", sys.executable, str(SERVER)])
    else:
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    errlog = (args.run_dir / "mcp-stderr.log").open("a", encoding="utf-8")
    async with stdio_client(params, errlog=errlog) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            listing = await client.list_tools()
            if args.command == "list":
                payload = json.loads(listing.model_dump_json(exclude_none=True, by_alias=True))
            elif args.command == "schema":
                if args.variant != "compressed":
                    raise ValueError("schema lookup is only available in compressed variant")
                schema_tool = next(tool for tool in listing.tools if tool.name.endswith("get_tool_schema"))
                schema = await client.call_tool(schema_tool.name, {"tool_name": args.name})
                payload = json.loads(schema.model_dump_json(exclude_none=True, by_alias=True))
            else:
                if args.variant == "compressed":
                    invoke_tool = next(tool for tool in listing.tools if tool.name.endswith("invoke_tool"))
                    response = await client.call_tool(invoke_tool.name, {"tool_name": args.name, "tool_input": {"record_id": "R-42", "mode": "full"}})
                else:
                    response = await client.call_tool(args.name, {"record_id": "R-42", "mode": "full"})
                payload = {"tool": args.name, "text": [item.text for item in response.content if item.type == "text"], "is_error": response.isError}
    errlog.close()
    output = json.dumps(payload, sort_keys=True)
    event = {"variant": args.variant, "action": args.command, "response_payload_bytes": len(output.encode())}
    if args.command in ("schema", "call"):
        event["tool"] = args.name
    if args.command == "call":
        event["result"] = payload
    append_trace(args.run_dir, event)
    print(output)


def check(args):
    answer = json.loads((args.run_dir / "answer.json").read_text(encoding="utf-8"))
    actions = [json.loads(line) for line in (args.run_dir / "actions.jsonl").read_text(encoding="utf-8").splitlines()]
    chosen = target(args.seed)
    expected = {"tool": chosen, "text": [f"{chosen.removeprefix('inspect_')}:R-42:full:False:0.5"], "is_error": False}
    if answer != expected:
        raise ValueError("answer does not match the selected tool result")
    if not any(item.get("action") == "call" and item.get("tool") == chosen and item.get("result") == expected for item in actions):
        raise ValueError("selected tool was not invoked")
    if {item.get("variant") for item in actions} != {args.variant}:
        raise ValueError("mixed direct/compressed actions")
    correct_calls = [index for index, item in enumerate(actions) if item.get("action") == "call" and item.get("tool") == chosen]
    schema_before_call = any(
        item.get("action") == "schema" and item.get("tool") == chosen and index < correct_calls[0]
        for index, item in enumerate(actions)
    )
    print(json.dumps({
        "accepted": True,
        "seed": args.seed,
        "variant": args.variant,
        "actions": len(actions),
        "response_payload_bytes": sum(item.get("response_payload_bytes", 0) for item in actions),
        "schema_lookups": sum(item.get("action") == "schema" for item in actions),
        "listed_catalogue": any(item.get("action") == "list" for item in actions),
        "schema_before_call": schema_before_call,
        "wrong_calls": sum(item.get("action") == "call" and item.get("tool") != chosen for item in actions),
    }))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("scenario", "list", "schema", "call", "check"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--variant", choices=("direct", "compressed"), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--name")
    args = parser.parse_args()
    if args.command == "scenario":
        print(f"Get the full status for synthetic {DOMAINS[args.seed % len(DOMAINS)]} record R-42. Save the exact JSON call result as answer.json.")
    elif args.command == "check":
        try:
            check(args)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            parser.exit(2, f"mcp route: {error}\n")
    else:
        if args.command in ("schema", "call") and not args.name:
            parser.error("schema/call requires --name")
        try:
            asyncio.run(request(args))
        except (OSError, ValueError, StopIteration) as error:
            parser.exit(2, f"mcp route: {error}\n")


if __name__ == "__main__":
    main()
