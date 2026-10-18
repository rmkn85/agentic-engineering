#!/usr/bin/env python3
"""Narrow newline-JSON MCP bridge: Context7 docs cache; no authentication layer."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading

import docs_result_cache as cache

OPERATIONS = {"resolve-library-id", "query-docs"}
PINNED_CHILD = ["npx", "-y", "@upstash/context7-mcp@4.4.2"]


def classify(operation, message):
    """Recognize inspected Context7 formats; unknown prose is never cached docs."""
    result = message.get("result", {})
    content = result.get("content", []) if isinstance(result, dict) else []
    text = "\n".join(item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text")
    lowered = text.strip().lower()
    for prefixes, kind in [(("monthly quota exceeded", "rate limit exceeded", "rate limited or quota exceeded", "too many requests"), "quota"),
                           (("unauthorized", "authentication failed", "invalid api key", "api key required"), "auth"),
                           (("spending limit", "payment required", "credits exhausted"), "spend"),
                           (("service unavailable", "upstream unavailable"), "outage")]:
        if lowered.startswith(prefixes):
            return kind
    if re.fullmatch(r"request failed with status 5[0-9]{2}\. please try again later\.", lowered):
        return "outage"
    if "error" in message or not isinstance(result, dict) or result.get("isError"):
        return "request"
    if operation == "resolve-library-id" and text.startswith("Available Libraries:\n") and "Context7-compatible library ID:" in text:
        return "success"
    if operation == "query-docs" and re.search(r"(?m)^Source: https?://\S+", text) and ("```" in text or "### " in text):
        return "success"
    return "request"


def error_result(request_id, text):
    return {"jsonrpc": "2.0", "id": request_id, "result": {"isError": True, "content": [{"type": "text", "text": text}]}}


class Bridge:
    def __init__(self, args):
        self.args = args
        self.output_lock = threading.Lock()
        self.child_lock = threading.Lock()
        self.pending_lock = threading.Lock()
        self.pending = {}
        self.child = subprocess.Popen(args.child or PINNED_CHILD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=True, bufsize=1)
        threading.Thread(target=self.read_child, daemon=True).start()
        self.worker = ThreadPoolExecutor(max_workers=1)

    def send(self, message):
        with self.output_lock:
            sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    def send_tool(self, message, status, state=None):
        result = message.get("result")
        if isinstance(result, dict):
            result = dict(result)
            meta = dict(result.get("_meta", {}))
            meta["context7Cache"] = {"status": status, "sha256": (state or {}).get("sha256"), "source": self.args.source}
            result["_meta"] = meta
            message = dict(message, result=result)
        self.send(message)

    def forward(self, message):
        with self.child_lock:
            self.child.stdin.write(json.dumps(message, ensure_ascii=False) + "\n")
            self.child.stdin.flush()

    def read_child(self):
        try:
            for line in self.child.stdout:
                message = json.loads(line)
                key = json.dumps(message.get("id"))
                with self.pending_lock:
                    pending = self.pending.pop(key, None) if "method" not in message else None
                if pending is None:
                    self.send(message)
                else:
                    pending.put(message)
        except (ValueError, OSError) as error:
            print("context7-cache: child protocol failure: " + type(error).__name__, file=sys.stderr)
        finally:
            with self.pending_lock:
                for pending in self.pending.values():
                    pending.put(None)
                self.pending.clear()

    def cached_call(self, message):
        request_id = message["id"]
        params = message["params"]
        request = {"provider": "context7", "operation": params["name"], "arguments": params.get("arguments", {}), "namespace": self.args.namespace, "source": self.args.source}
        scope = cache.digest({"provider": "context7", "namespace": self.args.namespace})
        root = Path(self.args.cache_dir)
        options = argparse.Namespace(cache_dir=str(root), command="lookup", request=None, max_age=self.args.max_age)
        try:
            # Covers lookup -> producer -> record across independent bridge processes.
            with cache.gate_lock(root / "producers" / (scope + ".json")):
                state = cache.run(options, request_value=request)
                if state["status"] == "hit":
                    self.send_tool({"jsonrpc": "2.0", "id": request_id, "result": state["response"]}, "hit", state)
                    return
                if self.args.cache_only or state["status"] == "blocked":
                    self.send_tool(error_result(request_id, "Context7 producer suppressed by cache preflight: " + json.dumps(state)), "blocked", state)
                    return
                response_queue = queue.Queue()
                key = json.dumps(request_id)
                with self.pending_lock:
                    self.pending[key] = response_queue
                try:
                    self.forward(message)
                    response = response_queue.get(timeout=self.args.timeout)
                except queue.Empty:
                    self.child.terminate()  # prevent a late duplicate response for this ID
                    raise ValueError("child response deadline exceeded; no automatic retry")
                finally:
                    with self.pending_lock:
                        self.pending.pop(key, None)
                if response is None:
                    raise ValueError("child exited before completing call")
                kind = classify(params["name"], response)
                options.command = "record"
                options.kind = kind
                options.valid_for = self.args.valid_for if kind == "success" else None
                options.retry_at = None  # Never infer metadata absent from actual tool result.
                options.response = None
                raw = response["result"] if "result" in response else response
                recorded = cache.run(options, request_value=request, response_value=raw)
                self.send_tool(response, "produced" if kind == "success" else "failure:" + kind, recorded)
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.send_tool(error_result(request_id, "Context7 cache bridge stopped call: " + str(error)), "stopped")

    def run(self):
        try:
            for line in sys.stdin:
                message = json.loads(line)
                params = message.get("params", {})
                if message.get("method") == "tools/call" and params.get("name") in OPERATIONS and "id" in message:
                    self.worker.submit(self.cached_call, message)
                else:
                    self.forward(message)
            self.worker.shutdown(wait=True)
        finally:
            if self.child.poll() is None:
                self.child.terminate()
                try:
                    self.child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.child.kill()
                    self.child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--max-age", required=True, type=float)
    parser.add_argument("--valid-for", required=True, type=float)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--cache-only", action="store_true", help="never produce docs on a miss; bounded acceptance only")
    parser.add_argument("--child", nargs=argparse.REMAINDER, help="explicit fixture or supported stdio child command")
    args = parser.parse_args()
    if (not Path(args.cache_dir).is_absolute() or not all(math.isfinite(value) for value in (args.timeout, args.max_age, args.valid_for)) or args.timeout <= 0 or args.max_age < 0 or args.valid_for <= 0):
        parser.error("absolute shared cache and finite positive deadline/validity (nonnegative freshness) required")
    try:
        Bridge(args).run()
    except (OSError, ValueError) as error:
        print("context7-cache: stopped: " + type(error).__name__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
