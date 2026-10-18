"""Offline producer-count and invalidation checks; no provider credentials."""
import argparse
import copy
import concurrent.futures
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("docs_result_cache", Path(__file__).parents[1] / "docs_result_cache.py")
cache = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cache)


class DocsResultCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.req = {"provider": "example-docs", "operation": "query-docs", "arguments": {"libraryId": "/org/lib/v2", "query": "routing", "language": "en"}, "namespace": "public-client-a", "source": "https://docs.example/v2"}
        self.request = self.root / "request.json"
        self.response = self.root / "response.json"
        self.response.write_text(json.dumps({"content": [{"type": "text", "text": "actual tool response"}]}))
        self.write_request()

    def write_request(self):
        self.request.write_text(json.dumps(self.req))

    def call(self, command, now=1000, **extra):
        args = dict(cache_dir=str(self.root / "cache"), command=command, request=str(self.request), max_age=100, response=str(self.response), kind="success", valid_for=200, retry_at=None, evidence="")
        args.update(extra)
        return cache.run(argparse.Namespace(**args), now=now)

    def test_fresh_duplicate_needs_no_additional_producer(self):
        calls = 0
        for _ in range(2):
            state = self.call("lookup")
            if state["status"] == "miss":
                calls += 1  # native MCP would run only here
                self.call("record")
                state = self.call("lookup")
            self.assertEqual(state["status"], "hit")
            self.assertEqual(state["response"], json.loads(self.response.read_text()))
        self.assertEqual(calls, 1)

    def test_identity_and_freshness(self):
        self.call("record")
        original = copy.deepcopy(self.req)
        for field, value in (("namespace", "client-b"), ("source", "https://docs.example/v3"), ("operation", "resolve-library-id")):
            with self.subTest(field=field):
                self.req = copy.deepcopy(original)
                self.req[field] = value
                self.write_request()
                self.assertEqual(self.call("lookup")["status"], "miss")
        for field, value in (("libraryId", "/org/lib/v3"), ("query", "different question"), ("language", "fr")):
            with self.subTest(field=field):
                self.req = copy.deepcopy(original)
                self.req["arguments"][field] = value
                self.write_request()
                self.assertEqual(self.call("lookup")["status"], "miss")
        self.req = original
        self.write_request()
        self.assertEqual(self.call("lookup", now=1101)["status"], "miss")
        self.assertEqual(self.call("lookup", now=1200, max_age=999)["status"], "miss")

    def test_canonical_argument_order_reuses(self):
        self.call("record")
        self.req["arguments"] = dict(reversed(list(self.req["arguments"].items())))
        self.write_request()
        self.assertEqual(self.call("lookup")["status"], "hit")

    def test_tamper_and_missing_response_invalidate(self):
        result = self.call("record")
        path = Path(result["record"])
        original = path.read_text()
        value = json.loads(original)
        value["body"]["response"] = "tampered"
        path.write_text(json.dumps(value))
        self.assertEqual(self.call("lookup")["status"], "miss")
        path.write_text(original)
        path.unlink()
        self.assertEqual(self.call("lookup")["status"], "miss")

    def test_wide_failure_blocks_different_queries_and_operations(self):
        for kind in sorted(cache.WIDE_FAILURES):
            with self.subTest(kind=kind):
                self.call("record", kind=kind, valid_for=None)
                self.req["operation"] = "resolve-library-id"
                self.req["arguments"] = {"libraryName": "another library " + kind}
                self.write_request()
                result = self.call("lookup")
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason"], kind)
                # Valid cached docs remain available without clearing the gate.
                self.call("record")
                self.assertEqual(self.call("lookup")["status"], "hit")
                self.req["arguments"]["libraryName"] = "yet another library"
                self.write_request()
                self.assertEqual(self.call("lookup")["status"], "blocked")
                self.call("release", evidence="provider status confirms service restored")

    def test_request_failure_is_not_docs_and_does_not_gate_other_queries(self):
        self.call("record", kind="request")
        self.assertEqual(self.call("lookup")["status"], "miss")
        self.req["arguments"]["query"] = "another question"
        self.write_request()
        self.assertEqual(self.call("lookup")["status"], "miss")
        self.call("record")
        self.assertEqual(self.call("lookup")["status"], "hit")

    def test_retry_boundary_and_explicit_changed_condition(self):
        self.call("record", kind="quota", retry_at="1970-01-01T00:20:00Z")
        self.assertEqual(self.call("lookup", now=1199)["status"], "blocked")
        self.assertEqual(self.call("lookup", now=1200)["status"], "miss")
        self.call("record", kind="auth", now=1201)
        with self.assertRaises(ValueError):
            self.call("release", evidence=" ")
        self.call("release", evidence="new authorized nonsecret credential namespace was verified")
        self.assertEqual(self.call("lookup")["status"], "miss")

    def test_concurrent_records_are_complete_and_recoverable(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.call("record"), range(16)))
        self.assertEqual(len({result["record"] for result in results}), 16)
        for result in results:
            envelope = json.loads(Path(result["record"]).read_text())
            self.assertEqual(cache.digest(envelope["body"]), result["sha256"])
        self.assertEqual(self.call("lookup")["status"], "hit")
        self.assertFalse(list((self.root / "cache").rglob(".write-*")))

    def test_symlink_cache_directory_rejected(self):
        target = self.root / "other"
        target.mkdir()
        (self.root / "cache").symlink_to(target, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.call("record")

    def test_unknown_quota_cannot_be_shortened_by_finite_outage(self):
        self.call("record", kind="quota")
        self.call("record", kind="outage", retry_at="1970-01-01T00:20:00Z")
        self.assertEqual(self.call("lookup", now=1201)["status"], "blocked")

    def test_later_boundary_cannot_be_shortened(self):
        self.call("record", kind="quota", retry_at="1970-01-01T00:30:00Z")
        self.call("record", kind="outage", retry_at="1970-01-01T00:20:00Z")
        self.assertEqual(self.call("lookup", now=1201)["status"], "blocked")
        self.assertEqual(self.call("lookup", now=1800)["status"], "miss")

    def test_concurrent_failures_preserve_all_unresolved_boundaries(self):
        def record(kind):
            return self.call("record", kind=kind, retry_at=None if kind == "quota" else "1970-01-01T00:20:00Z")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(record, ["quota", "outage", "auth", "spend"]))
        gate = next((self.root / "cache" / "gates").glob("*.json"))
        self.assertEqual(len(json.loads(gate.read_text())["records"]), 4)
        self.assertEqual(self.call("lookup", now=1201)["status"], "blocked")

    def test_pending_gate_mutation_blocks_only_new_producers(self):
        self.call("record")
        scope = cache.digest({"provider": self.req["provider"], "namespace": self.req["namespace"]})
        lock = self.root / "cache" / "gates" / (scope + ".lock")
        lock.parent.mkdir()
        lock.touch()
        self.assertEqual(self.call("lookup")["status"], "hit")
        self.req["arguments"]["query"] = "uncached question"
        self.write_request()
        self.assertEqual(self.call("lookup")["status"], "blocked")

    def test_error_envelope_cannot_be_success(self):
        self.response.write_text('{"isError": true, "content": []}')
        with self.assertRaises(ValueError):
            self.call("record")

    def test_corrupt_failure_state_fails_closed(self):
        result = self.call("record", kind="quota")
        Path(result["record"]).unlink()
        self.assertEqual(self.call("lookup")["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
