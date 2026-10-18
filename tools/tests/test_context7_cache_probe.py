import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

TOOLS = Path(__file__).parents[1]
sys.path.insert(0, str(TOOLS))
import context7_cache_probe as probe


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir(mode=0o700)
        self.spec = {"repository": str(TOOLS.parent), "workspace": str(self.root), "config": str(Path.home() / ".codex" / "config.toml"), "namespace": "context7-stdio-cli-auth", "max_age": 3600, "valid_for": 3600}
        self.key = "ctx7sk_" + "synthetic_not_a_credential"
        self.args = probe.config.launch_args(self.spec)
        self.raw = ('[mcp_servers.context7]\ncommand=' + json.dumps(sys.executable) + '\nargs=' + json.dumps(self.args) + '\n[mcp_servers.context7.env]\nCONTEXT7_API_KEY=' + json.dumps(self.key) + '\n').encode()
        self.request = {"provider": "context7", "operation": probe.OPERATION, "arguments": probe.ARGUMENTS, "namespace": self.spec["namespace"], "source": self.args[6]}

    def test_actual_protocol_cold_clients_share_one_producer(self):
        fixture = self.root / "stdio.py"
        source = (TOOLS / "tests" / "fixtures" / "context7_stdio.py").read_text()
        source = source.replace('result = {"tools": [{"name": "query-docs",', 'result = {"tools": [{"name": "resolve-library-id",')
        fixture.write_text(source)
        count = self.root / "calls.jsonl"
        command = [sys.executable] + self.args
        class FixtureClient(probe.Client):
            def __init__(inner, command, env, artifacts, label):
                super().__init__(command + ["--child", sys.executable, str(fixture), str(count)], env, artifacts, label)
        result = probe.exercise(command, {"CONTEXT7_API_KEY": self.key}, self.spec, self.request, self.artifacts, FixtureClient)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["first"], "produced")
        self.assertEqual(result["second"], "hit")
        self.assertEqual(len(count.read_text().splitlines()), 1)
        self.assertNotIn(self.key, json.dumps(result))
        for path in self.artifacts.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_hash_drift_and_out_of_scope_launch_rejected(self):
        with self.assertRaises(probe.config.Rejected):
            probe.validated_launch(b'not even valid TOML', '0' * 64, TOOLS.parent, self.root)
        changed = self.raw.replace(json.dumps(self.args).encode(), json.dumps(self.args + ["--child", "arbitrary"]).encode())
        with self.assertRaises(probe.config.Rejected):
            probe.validated_launch(changed, probe.config.sha(changed), TOOLS.parent, self.root)
        command, env, spec, request = probe.validated_launch(self.raw, probe.config.sha(self.raw), TOOLS.parent, self.root)
        self.assertEqual(command, [sys.executable] + self.args)
        self.assertEqual(env["CONTEXT7_API_KEY"], self.key)

    def test_no_second_client_without_offline_identical_hit(self):
        created = []
        class FakeClient:
            def __init__(inner, *args):
                created.append(1)
            def initialize(inner):
                pass
            def call(inner, *args):
                return {"_meta": {"context7Cache": {"status": "produced", "sha256": "not-a-cached-record"}}}
            def close(inner):
                pass
        result = probe.exercise([], {}, self.spec, self.request, self.artifacts, FakeClient)
        self.assertEqual(len(created), 1)
        self.assertEqual(result["phase"], "offline-hit-verification")
        self.assertEqual(result["status"], "failed")

    def test_second_client_cannot_produce_after_cache_deleted_during_startup(self):
        fixture = self.root / "stdio.py"
        source = (TOOLS / "tests" / "fixtures" / "context7_stdio.py").read_text()
        source = source.replace('result = {"tools": [{"name": "query-docs",', 'result = {"tools": [{"name": "resolve-library-id",')
        fixture.write_text(source)
        count = self.root / "calls.jsonl"
        command = [sys.executable] + self.args
        root = self.root
        class InvalidatingClient(probe.Client):
            def __init__(inner, command, env, artifacts, label):
                inner.label = label
                super().__init__(command + ["--child", sys.executable, str(fixture), str(count)], env, artifacts, label)
            def initialize(inner):
                super().initialize()
                if inner.label == "second":
                    for path in (root / ".agent-cache" / "docs-results" / "entries").glob("*.json"):
                        path.unlink()
        result = probe.exercise(command, {"CONTEXT7_API_KEY": self.key}, self.spec, self.request, self.artifacts, InvalidatingClient)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["phase"], "second-tool-call")
        self.assertEqual(len(count.read_text().splitlines()), 1)

    def test_partial_line_cannot_escape_deadline(self):
        client = probe.Client([sys.executable, "-c", "import sys,time;sys.stdout.write('{');sys.stdout.flush();time.sleep(60)"], {}, self.artifacts, "partial")
        started = time.monotonic()
        try:
            with self.assertRaises(TimeoutError):
                client.call(1, "initialize", {}, 0.1)
        finally:
            client.close()
        self.assertLess(time.monotonic() - started, 2)

    def test_timeout_tears_down_owned_child(self):
        client = probe.Client([sys.executable, "-c", "import time; time.sleep(60)"], {}, self.artifacts, "timeout")
        try:
            with self.assertRaises(TimeoutError):
                client.call(1, "initialize", {}, 0.01)
        finally:
            client.close()
        self.assertIsNotNone(client.process.poll())

    def test_failure_summary_never_echoes_exception_secret(self):
        secret = self.key
        class FailingClient:
            def __init__(inner, *args):
                pass
            def initialize(inner):
                raise RuntimeError(secret)
            def close(inner):
                pass
        result = probe.exercise([], {}, self.spec, self.request, self.artifacts, FailingClient)
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual(result["error"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
