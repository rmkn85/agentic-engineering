import concurrent.futures
import json
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).parents[1]


class Context7BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.count = self.root / "producer.jsonl"

    def start(self, source="context7-mcp-4.4.2", valid_for=3600):
        process = subprocess.Popen([sys.executable, str(TOOLS / "context7_cache_stdio.py"), "--cache-dir", str(self.root / "cache"), "--namespace", "fixture-client", "--source", source, "--max-age", "3600", "--valid-for", str(valid_for), "--child", sys.executable, str(TOOLS / "tests" / "fixtures" / "context7_stdio.py"), str(self.count)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(self.stop, process)
        self.call(process, "initialize", {}, "init")
        return process

    def stop(self, process):
        if process.poll() is None:
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for stream in (process.stdout, process.stderr):
            stream.close()

    def call(self, process, method, params, identity=1):
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": identity, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        self.assertTrue(select.select([process.stdout], [], [], 8)[0], "bridge response deadline")
        return json.loads(process.stdout.readline())

    def docs(self, process, query="routing", identity=1, **extra):
        arguments = {"libraryId": "/example/library/v2", "query": query, **extra}
        return self.call(process, "tools/call", {"name": "query-docs", "arguments": arguments}, identity)

    def count_calls(self):
        return len(self.count.read_text().splitlines()) if self.count.exists() else 0

    def test_two_cold_native_clients_share_cache_without_reminder(self):
        first = self.start()
        response = self.docs(first, identity="first")
        self.stop(first)
        second = self.start()
        hit = self.docs(second, identity=97)
        self.assertEqual(response["result"]["content"], hit["result"]["content"])
        self.assertEqual(response["result"]["_meta"]["context7Cache"]["status"], "produced")
        self.assertEqual(hit["result"]["_meta"]["context7Cache"]["status"], "hit")
        self.assertEqual(hit["id"], 97)
        self.assertEqual(self.count_calls(), 1)

    def test_parallel_processes_do_not_duplicate_producer(self):
        first, second = self.start(), self.start()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda process: self.docs(process, query="delay"), (first, second)))
        self.assertEqual(results[0]["result"]["content"], results[1]["result"]["content"])
        self.assertEqual(self.count_calls(), 1)

    def test_observed_plain_quota_blocks_other_operation(self):
        first = self.start()
        self.docs(first, "quota")
        second = self.start()
        response = self.call(second, "tools/call", {"name": "resolve-library-id", "arguments": {"libraryName": "Example", "query": "other"}})
        self.assertTrue(response["result"]["isError"])
        self.assertIn("suppressed", response["result"]["content"][0]["text"])
        self.assertEqual(self.count_calls(), 1)

    def test_pinned_native_fallbacks_gate_other_queries(self):
        for query, kind in (("native-429", "quota"), ("native-503", "outage")):
            with self.subTest(query=query):
                # Separate cache scopes so the first provider failure cannot mask the second.
                self.root = self.root / query
                self.root.mkdir()
                self.count = self.root / "producer.jsonl"
                first = self.start()
                response = self.docs(first, query)
                self.assertEqual(response["result"]["_meta"]["context7Cache"]["status"], "failure:" + kind)
                other = self.docs(self.start(), "different question")
                self.assertEqual(other["result"]["_meta"]["context7Cache"]["status"], "blocked")
                self.assertEqual(self.count_calls(), 1)

    def test_params_source_and_unrecognized_text_do_not_false_hit(self):
        first = self.start()
        self.docs(first)
        self.docs(first, language="fr")
        self.docs(self.start(source="context7-mcp-next"))
        self.docs(first, "unknown")
        self.docs(first, "unknown")
        self.assertEqual(self.count_calls(), 5)

    def test_expired_or_tampered_record_requires_producer(self):
        first = self.start(valid_for=0.000001)
        self.docs(first)
        self.docs(first)
        self.assertEqual(self.count_calls(), 2)
        fresh = self.start()
        self.docs(fresh, "fresh")
        records = list((self.root / "cache" / "records").glob("*.json"))
        for path in records:
            value = json.loads(path.read_text())
            value["body"]["response"] = {"content": []}
            path.write_text(json.dumps(value))
        self.docs(fresh, "fresh")
        self.assertEqual(self.count_calls(), 4)

    def test_protocol_passthrough_and_child_failure(self):
        process = self.start()
        listing = self.call(process, "tools/list", {}, "list-id")
        self.assertEqual(listing["id"], "list-id")
        self.assertEqual(listing["result"]["tools"][0]["name"], "query-docs")
        echo = self.call(process, "fixture/echo", {"one": 1}, 42)
        self.assertEqual(echo["result"], {"echo": {"one": 1}})
        response = self.docs(process, "exit")
        self.assertTrue(response["result"]["isError"])
        self.assertIn("child exited", response["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
