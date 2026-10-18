#!/usr/bin/env python3
"""One hash-bound native Context7 acceptance activity; no configurable producer."""
import argparse
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import time
import uuid

import docs_result_cache as cache
import context7_cache_config as config

ARGUMENTS = {"libraryName": "Context7", "query": "How does the Context7 CLI configure stdio MCP authentication for Codex?"}
OPERATION = "resolve-library-id"


def validated_launch(raw, expected_sha, repository, workspace):
    if config.sha(raw) != expected_sha:
        raise config.Rejected("native config hash changed")
    parsed = config.tomllib.loads(raw.decode())
    server = parsed.get("mcp_servers", {}).get("context7", {})
    args = server.get("args", [])
    if not isinstance(args, list) or len(args) != 11:
        raise config.Rejected("unsupported bridge launch")
    spec = {"repository": str(repository), "workspace": str(workspace), "config": str(Path.home() / ".codex" / "config.toml"), "namespace": args[4], "max_age": int(args[8]), "valid_for": int(args[10])}
    config.validate_spec(spec)
    if server.get("command") != sys.executable or args != config.launch_args(spec) or spec["namespace"] != "context7-stdio-cli-auth":
        raise config.Rejected("requires the reviewed authenticated native bridge")
    env = server.get("env", {})
    if not isinstance(env, dict) or any(not isinstance(value, str) for value in env.values()) or not re.fullmatch(r"ctx7sk[A-Za-z0-9_-]+", env.get("CONTEXT7_API_KEY", "")):
        raise config.Rejected("native fixed-key configuration missing")
    request = {"provider": "context7", "operation": OPERATION, "arguments": ARGUMENTS, "namespace": spec["namespace"], "source": args[6]}
    return [server["command"]] + args, env, spec, request


class Client:
    def __init__(self, command, env, artifacts, label):
        self.buffer = b""
        self.stderr = (artifacts / (label + ".stderr")).open("wb")
        os.chmod(self.stderr.name, 0o600)
        self.transcript = (artifacts / (label + ".jsonl")).open("w")
        os.chmod(self.transcript.name, 0o600)
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, env={**os.environ, **env}, text=True, start_new_session=True)

    def call(self, identity, method, params, timeout):
        message = {"jsonrpc": "2.0", "id": identity, "method": method, "params": params}
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        while True:
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([self.process.stdout], [], [], max(0, remaining))[0]:
                    raise TimeoutError("native MCP deadline")
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError("native MCP child exited")
                self.buffer += chunk
                if len(self.buffer) > 1024 * 1024:
                    raise ValueError("native MCP line exceeds bounded size")
            line, self.buffer = self.buffer.split(b"\n", 1)
            result = json.loads(line)
            self.transcript.write(json.dumps(result) + "\n")
            self.transcript.flush()
            if result.get("id") == identity and "method" not in result:
                if "error" in result:
                    raise RuntimeError("native MCP protocol error")
                return result.get("result", {})
            if "method" in result and "id" in result:
                # No elicitation/auth flow is authorized by this acceptance activity.
                self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": result["id"], "error": {"code": -32601, "message": "Acceptance probe does not handle server requests"}}) + "\n")
                self.process.stdin.flush()

    def initialize(self):
        self.call(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "context7-cache-acceptance", "version": "1"}}, 90)
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.process.stdin.flush()
        listing = self.call(2, "tools/list", {}, 15)
        if OPERATION not in [tool.get("name") for tool in listing.get("tools", [])]:
            raise RuntimeError("required native tool missing")

    def close(self):
        # Descendants can outlive the bridge; teardown owns the whole new session.
        try:
            os.killpg(self.process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout):
            try:
                stream.close()
            except OSError:
                pass
        self.stderr.close()
        self.transcript.close()


def exercise(command, env, spec, request, artifacts, factory=Client):
    summary = {"status": "failed", "phase": "initialize", "artifacts": str(artifacts)}
    client = None
    try:
        client = factory(command, env, artifacts, "first")
        client.initialize()
        summary["phase"] = "first-tool-call"
        result = client.call(3, "tools/call", {"name": OPERATION, "arguments": ARGUMENTS}, 65)
        meta = result.get("_meta", {}).get("context7Cache", {})
        summary["first"] = meta.get("status", "unproved")
        if result.get("isError") or meta.get("status") not in {"hit", "produced"}:
            return summary
        client.close()
        client = None
        summary["phase"] = "offline-hit-verification"
        state = cache.run(argparse.Namespace(command="lookup", request=None, cache_dir=str(Path(spec["workspace"]) / ".agent-cache" / "docs-results"), max_age=spec["max_age"]), request_value=request)
        if state["status"] != "hit" or state["sha256"] != meta.get("sha256"):
            return summary  # Never launch a second producer without the identical valid hit.
        client = factory(command + ["--cache-only"], env, artifacts, "second")
        summary["phase"] = "second-initialize"
        client.initialize()
        summary["phase"] = "second-tool-call"
        second = client.call(3, "tools/call", {"name": OPERATION, "arguments": ARGUMENTS}, 5)
        second_meta = second.get("_meta", {}).get("context7Cache", {})
        summary["second"] = second_meta.get("status", "unproved")
        if second_meta.get("status") == "hit" and second_meta.get("sha256") == state["sha256"] and not second.get("isError"):
            summary.update(status="passed", phase="complete", response_sha256=state["sha256"])
        return summary
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, TimeoutError) as error:
        summary["error"] = type(error).__name__  # Never echo provider text or env values.
        return summary
    finally:
        if client is not None:
            client.close()


def main(arguments=None):
    try:
        values = sys.argv[1:] if arguments is None else arguments
        if len(values) != 2 or values[0] != "context7-cache-probe" or not re.fullmatch(r"CONFIG_SHA256=[0-9a-f]{64}", values[1]):
            raise config.Rejected("expected context7-cache-probe CONFIG_SHA256=<64hex>")
        repository = Path(__file__).resolve().parents[1]
        workspace = repository.parent
        native = Path.home() / ".codex" / "config.toml"
        raw, mode = config.read_regular(native)
        if mode != 0o600 or native.stat().st_uid != os.getuid():
            raise config.Rejected("native config must be owned mode0600")
        command, env, spec, request = validated_launch(raw, values[1].split("=", 1)[1], repository, workspace)
        config.host_identity(spec)
        root = workspace / ".agent-cache" / "context7-acceptance"
        config.private_store(root)
        artifacts = root / uuid.uuid4().hex
        artifacts.mkdir(mode=0o700)
        result = exercise(command, env, spec, request, artifacts)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "passed" else 1
    except (config.Rejected, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "refused", "error": type(error).__name__}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
