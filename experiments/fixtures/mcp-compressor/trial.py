import asyncio
import json
from pathlib import Path
import shutil
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


PYTHON = sys.executable
SERVER = str(Path(__file__).with_name("server.py"))
COMPRESSOR = shutil.which("mcp-compressor")


async def inspect(label: str, command: str, args: list[str]) -> dict:
    params = StdioServerParameters(command=command, args=args)
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as client:
            await client.initialize()
            listing = await client.list_tools()
            payload = listing.model_dump_json(exclude_none=True, by_alias=True)
            tool_names = [tool.name for tool in listing.tools]
            result = {"label": label, "tools": tool_names, "tool_list_bytes": len(payload.encode("utf-8"))}
            if label == "baseline":
                call = await client.call_tool("inspect_test", {"record_id": "R-42", "mode": "full"})
                result["call"] = call.model_dump(exclude_none=True)
            else:
                schema_tool = next(tool for tool in listing.tools if tool.name.endswith("get_tool_schema"))
                invoke_tool = next(tool for tool in listing.tools if tool.name.endswith("invoke_tool"))
                schema = await client.call_tool(schema_tool.name, {"tool_name": "inspect_test"})
                result["schema_response_bytes"] = len(schema.model_dump_json(exclude_none=True).encode("utf-8"))
                result["schema_has_required_id"] = "record_id" in schema.content[0].text
                call = await client.call_tool(invoke_tool.name, {"tool_name": "inspect_test", "tool_input": {"record_id": "R-42", "mode": "full"}})
                result["call"] = call.model_dump(exclude_none=True)
            return result


async def main() -> None:
    if COMPRESSOR is None:
        raise SystemExit("mcp-compressor is not on PATH")
    results = []
    results.append(await inspect("baseline", PYTHON, [SERVER]))
    for level in ("low", "medium", "high", "max"):
        results.append(await inspect(level, COMPRESSOR, ["-c", level, "--", PYTHON, SERVER]))
    baseline = results[0].pop("call")
    for result in results[1:]:
        result["same_result"] = result.pop("call") == baseline
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
