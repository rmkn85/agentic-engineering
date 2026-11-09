import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / "agent_hooks.py"
spec = importlib.util.spec_from_file_location("agent_hooks", TOOL)
hooks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hooks)


class AgentHooksTests(unittest.TestCase):
    def result(self, value, code=0):
        return subprocess.CompletedProcess([], code, json.dumps(value) if value is not None else "", "")

    def test_stop_normalizes_empty_success_for_codex(self):
        with patch.object(hooks, "invoke", return_value=self.result(None)):
            self.assertEqual(hooks.stop(Path("."), {}), {"continue": True})

    def test_stop_preserves_block_and_reason(self):
        response = {"decision": "block", "reason": "Consumer has not passed"}
        with patch.object(hooks, "invoke", return_value=self.result(response)):
            self.assertEqual(hooks.stop(Path("."), {}), response)

    def test_start_records_repetition_without_rerunning_acceptance(self):
        calls = []
        def invoke(name, root, *args, **kwargs):
            calls.append((name, args))
            return self.result({"focus": "Repair the consumer", "findings": [{"kind": "loop"}]})
        with tempfile.TemporaryDirectory() as temp, patch.object(hooks, "invoke", side_effect=invoke):
            result = hooks.start(Path(temp))
        self.assertIn("Repair the consumer", result["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(calls, [("work_audit.py", ("--json",)),
                                 ("finish_check.py", ("--trigger", "repetition"))])

    def test_start_inspects_stale_receipt_without_running_checks(self):
        calls = []
        def invoke(name, root, *args, **kwargs):
            calls.append((name, args))
            return self.result({"state": "stale"} if "--inspect" in args else {"focus": "Review goal"})
        with tempfile.TemporaryDirectory() as temp, patch.object(hooks, "invoke", side_effect=invoke):
            root = Path(temp)
            (root / ".agent").mkdir()
            for name in ("goal.json", "goal-status.json"):
                (root / ".agent" / name).write_text("{}")
            hooks.start(root)
        self.assertIn(("finish_check.py", ("--trigger", "stale-evidence")), calls)
        self.assertTrue(all("--hook" not in args for _, args in calls))

    def test_adapter_failure_ends_unverified_not_accepted(self):
        result = subprocess.run([sys.executable, str(TOOL), "--host", "codex", "--event", "stop"],
                                input="[]", text=True, capture_output=True)
        response = json.loads(result.stdout)
        self.assertFalse(response["continue"])
        self.assertIn("NOT verified", response["systemMessage"])

    def test_native_configs_use_same_adapter(self):
        root = TOOL.parents[1]
        codex = json.loads((root / ".codex/hooks.json").read_text())["hooks"]
        for event in ("SessionStart", "Stop"):
            self.assertIn("tools/agent_hooks.py", codex[event][0]["hooks"][0]["command"])

    def test_real_adapters_from_nested_cwd_keep_start_read_only_and_stop_outcome_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'nested').mkdir()
            (root / 'tools').symlink_to(TOOL.parent, target_is_directory=True)
            (root / '.gitignore').write_text('.agent/\n__pycache__/\n')
            (root / 'requirements').write_text('The consumer reads a working result')
            (root / 'source').write_text('working')
            (root / 'verify.py').write_text("from pathlib import Path\np=Path('.agent/count')\n"
                                           "p.write_text(str(int(p.read_text())+1) if p.exists() else '1')\n"
                                           "assert Path('source').read_text() == 'working'\n")
            (root / 'Makefile').write_text('consumer-check:\n\t@python3 verify.py\n')
            (root / '.agent').mkdir()
            goal = {'goal': 'Consumer reads working result', 'requirement_refs': ['requirements'],
                    'acceptance': [{'id': 'consumer', 'check': 'Consumer works', 'run': 'consumer-check'}]}
            def save():
                (root / '.agent/goal.json').write_text(json.dumps(goal))
            save()
            config = json.loads((TOOL.parents[1] / '.codex/hooks.json').read_text())['hooks']
            def invoke(event):
                # This exercises maintained commands with real subprocesses; it is
                # deliberately not a claim that a native host discovered the config.
                command = config[event][0]['hooks'][0]['command']
                result = subprocess.run(command, shell=True, cwd=root / 'nested', text=True,
                                        input=json.dumps({'cwd': str(root / 'nested'), 'session_id': 'fixture'}),
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            self.assertEqual(invoke('Stop'), {'continue': True})
            self.assertFalse((root / '.agent/reflection-state.json').exists())
            (root / 'source').write_text('regressed')
            count = (root / '.agent/count').read_text()
            start = invoke('SessionStart')
            self.assertIn('stale-evidence', start['hookSpecificOutput']['additionalContext'])
            self.assertEqual((root / '.agent/count').read_text(), count)
            self.assertEqual(invoke('Stop')['decision'], 'block')
            self.assertFalse(json.loads((root / '.agent/goal-status.json').read_text())['met'])
            (root / 'source').write_text('working')
            goal['reflection'] = {'interventions': [{'observation': 'The source had regressed after handoff',
                  'evidence': 'requirements', 'hypothesis': 'Restoring source repairs the consumer',
                  'expected_effect': 'The consumer will read working result', 'run': 'consumer-check'}]}
            save()
            self.assertEqual(invoke('Stop'), {'continue': True})
            self.assertTrue(json.loads((root / '.agent/goal-status.json').read_text())['met'])


if __name__ == "__main__":
    unittest.main()
