"""Offline newline-JSON MCP provider fixture, not a live Context7 service."""
import json
import os
from pathlib import Path
import sys
import time

count = Path(sys.argv[1])
for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    method = message.get("method")
    if method == "tools/call":
        with count.open("a") as stream:
            stream.write(json.dumps(message["params"]) + "\n")
        args = message["params"].get("arguments", {})
        query = args.get("query", "")
        if query == "exit":
            os._exit(3)
        if query == "delay":
            time.sleep(0.2)
        if query == "quota":
            text = "Monthly quota exceeded. Create a free API key at https://context7.com/dashboard for more requests."
        elif query == "native-429":
            text = "Rate limited or quota exceeded. Create a free API key at https://context7.com/dashboard for higher limits."
        elif query == "native-503":
            text = "Request failed with status 503. Please try again later."
        elif query == "unknown":
            text = "A novel failure that does not match the known messages."
        elif message["params"]["name"] == "resolve-library-id":
            text = "Available Libraries:\n\n- Title: Example\n- Context7-compatible library ID: /example/library"
        else:
            text = "### Example\nSource: https://docs.example/v2\n```python\nprint('fixture')\n```"
        result = {"content": [{"type": "text", "text": text}]}
    elif method == "initialize":
        result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "offline-fixture", "version": "1"}}
    elif method == "tools/list":
        result = {"tools": [{"name": "query-docs", "inputSchema": {"type": "object"}}]}
    else:
        result = {"echo": message.get("params")}
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
