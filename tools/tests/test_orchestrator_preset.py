"""Static preset regression only; no claim about agent behavior or live settings."""
from pathlib import Path
import unittest

try:
    import tomllib
except ImportError:
    tomllib = None

ROOT = Path(__file__).resolve().parents[2]
PRESET = ROOT / "configs" / "codex" / "efficient-local.config.toml"


@unittest.skipIf(tomllib is None, "TOML parsing requires Python 3.11+")
class OrchestratorPresetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with PRESET.open("rb") as stream:
            cls.config = tomllib.load(stream)

    def test_root_has_explicit_policy_baseline(self):
        self.assertEqual(self.config["model"], "gpt-6.1-sol")
        self.assertEqual(self.config["model_reasoning_effort"], "medium")

    def test_worker_fallback_does_not_inherit_root_effort(self):
        agents = self.config["agents"]
        self.assertEqual(agents["default_subagent_model"], "gpt-6-luna")
        self.assertEqual(agents["default_subagent_reasoning_effort"], "medium")

    def test_explicit_worker_routing_remains_available_in_preset(self):
        self.assertTrue(self.config["agents"]["enabled"])
        native = self.config["features"]["multi_agent_v2"]
        self.assertTrue(native["enabled"])
        self.assertTrue(native["expose_spawn_agent_model_overrides"])
        self.assertIsInstance(native["multi_agent_mode_hint_text"], str)

    def test_effort_preset_does_not_install_permission_overrides(self):
        for key in ("approval_policy", "sandbox_mode"):
            self.assertNotIn(key, self.config)
        self.assertEqual(self.config["service_tier"], "default")


if __name__ == "__main__":
    unittest.main()
