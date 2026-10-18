import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = Path(__file__).parents[1]
sys.path.insert(0, str(TOOLS))
import context7_cache_config as config_tool


class Context7ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "config.toml"
        self.original = b'model = "unchanged"\n[mcp_servers.context7]\ncommand = "npx"\nargs = ["-y", "@upstash/context7-mcp"]\nstartup_timeout_sec = 30\n[mcp_servers.context7.env]\nUNCHANGED = "private-placeholder"\n[mcp_servers.other]\ncommand = "other"\n'
        self.config.write_bytes(self.original)
        self.spec = self.root / "spec.json"
        self.value = {"config": str(self.config), "workspace": str(self.root / "workspace"), "repository": str(TOOLS.parent), "namespace": "fixture-client", "max_age": 3600, "valid_for": 3600}
        self.store = self.root / "plans"

    def plan(self):
        self.spec.write_text(json.dumps(self.value))
        return config_tool.plan(self.spec, self.store)

    def test_plan_apply_changes_only_context7_launch(self):
        plan = self.plan()
        self.assertEqual(self.config.read_bytes(), self.original)
        self.assertNotIn("private-placeholder", plan["diff"])
        config_tool.apply(plan["plan_sha256"], self.store)
        parsed = config_tool.tomllib.loads(self.config.read_text())
        self.assertEqual(parsed["model"], "unchanged")
        self.assertEqual(parsed["mcp_servers"]["other"], {"command": "other"})
        server = parsed["mcp_servers"]["context7"]
        self.assertEqual(server["env"], {"UNCHANGED": "private-placeholder"})
        self.assertIn(str(self.root / "workspace" / ".agent-cache" / "docs-results"), server["args"])
        self.assertIn("fixture-client", server["args"])
        self.assertNotIn("env_vars", server)

    def test_optional_name_forwarding_contains_no_key_value(self):
        self.value["forward_api_key"] = True
        plan = self.plan()
        config_tool.apply(plan["plan_sha256"], self.store)
        server = config_tool.tomllib.loads(self.config.read_text())["mcp_servers"]["context7"]
        self.assertEqual(server["env_vars"], ["CONTEXT7_API_KEY"])
        self.assertNotIn("private-placeholder", plan["diff"])

    def test_config_or_plan_change_rejected(self):
        plan = self.plan()
        self.config.write_bytes(self.original + b'# changed\n')
        with self.assertRaises(config_tool.Rejected):
            config_tool.apply(plan["plan_sha256"], self.store)
        self.config.write_bytes(self.original)
        body = json.loads(Path(plan["plan_file"]).read_text())
        body["candidate"] += "# changed\n"
        Path(plan["plan_file"]).write_text(json.dumps(body))
        with self.assertRaises(config_tool.Rejected):
            config_tool.apply(plan["plan_sha256"], self.store)

    def test_recomputed_malicious_plan_rejected(self):
        for change in ("command", "environment", "source_set", "spec"):
            with self.subTest(change=change):
                plan = self.plan()
                body = json.loads(Path(plan["plan_file"]).read_text())
                if change == "command":
                    body["candidate"] = body["candidate"].replace('context7_cache_stdio.py', 'arbitrary.py')
                elif change == "environment":
                    body["candidate"] = body["candidate"].replace('UNCHANGED = "private-placeholder"', 'UNCHANGED = "different"')
                elif change == "source_set":
                    body["sources"] = {}
                else:
                    body["spec"]["valid_for"] = -1
                body["candidate_sha256"] = config_tool.sha(body["candidate"].encode())
                identity = config_tool.sha(json.dumps(body, sort_keys=True).encode())
                (self.store / (identity + ".json")).write_text(json.dumps(body))
                with self.assertRaises(config_tool.Rejected):
                    config_tool.apply(identity, self.store)

    def test_duplicate_tables_and_noncanonical_host_target_rejected(self):
        self.config.write_bytes(self.original + b'\n[mcp_servers.context7]\ncommand="npx"\n')
        with self.assertRaises(ValueError):
            self.plan()
        with self.assertRaises(config_tool.Rejected):
            config_tool.host_identity(self.value)

    def test_private_plan_and_backup_modes(self):
        plan = self.plan()
        self.assertEqual(Path(plan["plan_file"]).stat().st_mode & 0o777, 0o600)
        result = config_tool.apply(plan["plan_sha256"], self.store)
        self.assertEqual(Path(result["backup"]).stat().st_mode & 0o777, 0o600)

    def test_unsafe_existing_store_or_parent_rejected(self):
        self.store.mkdir(mode=0o777)
        self.store.chmod(0o777)
        with self.assertRaises(config_tool.Rejected):
            self.plan()
        self.store.chmod(0o700)
        with mock.patch.object(config_tool.os, "getuid", return_value=self.store.stat().st_uid + 1):
            with self.assertRaises(config_tool.Rejected):
                self.plan()
        linked = self.root / "linked"
        linked.symlink_to(self.store, target_is_directory=True)
        with self.assertRaises(config_tool.Rejected):
            config_tool.private_store(linked / "nested")

    def stage_auth(self):
        self.config.chmod(0o600)
        base = Path(self.value["workspace"]) / ".agent-cache" / "context7-auth"
        base.mkdir(parents=True, mode=0o700)
        base.chmod(0o700)
        path = base / "fixture-stage" / ".codex" / "config.toml"
        path.parent.mkdir(parents=True, mode=0o700)
        key = "ctx7sk_" + "synthetic_not_a_credential"
        path.write_text('[mcp_servers.context7]\ncommand="npx"\nargs=' + json.dumps(["-y", "@upstash/context7-mcp", "--api-key", key]) + "\n")
        path.chmod(0o600)
        self.value["auth_config"] = str(path)
        self.value["namespace"] = "context7-stdio-cli-auth"
        return path, key

    def test_official_auth_adoption_is_fixed_redacted_and_preserving(self):
        path, key = self.stage_auth()
        plan = self.plan()
        self.assertNotIn(key, json.dumps(plan))
        self.assertIn("redacted", plan["diff"])
        config_tool.apply(plan["plan_sha256"], self.store)
        parsed = config_tool.tomllib.loads(self.config.read_text())
        self.assertEqual(parsed["mcp_servers"]["context7"]["env"], {"UNCHANGED": "private-placeholder", "CONTEXT7_API_KEY": key})
        self.assertEqual(parsed["mcp_servers"]["other"], {"command": "other"})
        self.assertNotIn(key, json.dumps(config_tool.launch_args(self.value)))

    def test_existing_fixed_key_updates_without_disclosing_either_value(self):
        path, key = self.stage_auth()
        previous = "ctx7sk_" + "older_synthetic_not_a_credential"
        self.config.write_text(self.original.decode().replace('UNCHANGED = "private-placeholder"', 'UNCHANGED = "private-placeholder"\nCONTEXT7_API_KEY = ' + json.dumps(previous) + ' # retained setting position'))
        plan = self.plan()
        self.assertNotIn(previous, json.dumps(plan))
        self.assertNotIn(key, json.dumps(plan))
        config_tool.apply(plan["plan_sha256"], self.store)
        env = config_tool.tomllib.loads(self.config.read_text())["mcp_servers"]["context7"]["env"]
        self.assertEqual(env, {"UNCHANGED": "private-placeholder", "CONTEXT7_API_KEY": key})

    def test_auth_input_drift_permissions_and_symlink_rejected(self):
        path, key = self.stage_auth()
        plan = self.plan()
        path.write_text(path.read_text().replace(key, key + "_changed"))
        with self.assertRaises(config_tool.Rejected):
            config_tool.apply(plan["plan_sha256"], self.store)
        path.chmod(0o644)
        with self.assertRaises(config_tool.Rejected):
            self.plan()
        path.chmod(0o600)
        linked = path.parent / "linked.toml"
        linked.symlink_to(path)
        self.value["auth_config"] = str(linked)
        with self.assertRaises(config_tool.Rejected):
            self.plan()

    def test_rehashed_auth_path_or_env_mutation_rejected(self):
        path, key = self.stage_auth()
        for change in ("path", "env"):
            with self.subTest(change=change):
                plan = self.plan()
                body = json.loads(Path(plan["plan_file"]).read_text())
                if change == "path":
                    body["spec"]["auth_config"] = str(self.root / ".codex" / "config.toml")
                else:
                    body["candidate"] = body["candidate"].replace('UNCHANGED = "private-placeholder"', 'UNCHANGED = "different"')
                body["candidate_sha256"] = config_tool.sha(body["candidate"].encode())
                identity = config_tool.sha(json.dumps(body, sort_keys=True).encode())
                (self.store / (identity + ".json")).write_text(json.dumps(body))
                with self.assertRaises(config_tool.Rejected):
                    config_tool.apply(identity, self.store)

    def test_unsupported_inline_env_or_key_shape_rejected(self):
        path, key = self.stage_auth()
        self.config.write_text('[mcp_servers.context7]\ncommand="npx"\nargs=["-y","@upstash/context7-mcp"]\nenv={UNCHANGED="value"}\n')
        with self.assertRaises(config_tool.Rejected):
            self.plan()
        self.config.write_bytes(self.original)
        path.write_text(path.read_text().replace(key, "invalid"))
        with self.assertRaises(config_tool.Rejected):
            self.plan()

    def test_remote_or_secret_arguments_not_accepted(self):
        self.config.write_text('[mcp_servers.context7]\nurl = "https://example.invalid/mcp"\n')
        with self.assertRaises(config_tool.Rejected):
            self.plan()
        self.config.write_text('[mcp_servers.context7]\ncommand = "npx"\nargs = ["-y", "@upstash/context7-mcp", "--api-key", "placeholder"]\n')
        with self.assertRaises(config_tool.Rejected):
            self.plan()


if __name__ == "__main__":
    unittest.main()
