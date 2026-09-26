"""Offline adapter contracts; fake upstreams are not real tool/model trials."""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import external_practices as ep


class ExternalPractices(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        self.git("init", "-q")
        (self.repo / ".gitignore").write_text(".agent-cache/\n")
        (self.repo / "core.py").write_text("def double(x): return x * 2\n")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
        self.cache = self.repo / ".agent-cache" / "external-practices"
        self.pin = {"revision": "fixture", "skill": "skills/ponytail-review/SKILL.md"}
        self.source = self.cache / "upstream" / "fixture"
        self.source.mkdir(parents=True)
        self.bundle = self.cache / "runs" / "test"
        self.bundle.mkdir(parents=True)
        self.args = argparse.Namespace(repo=self.repo, scope=".", action="build", query=["double"])
        self.calls = []

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE)

    def fake_run(self, argv, env):
        self.calls.append(argv)
        if "extract" in argv:
            out = Path(env["GRAPHIFY_OUT"])
            out.mkdir(exist_ok=True)
            (out / "graph.json").write_text(json.dumps({"nodes": [{"id": "double"}], "edges": []}))

    def graph(self, run=None):
        usage = {}
        with patch.object(ep, "verified_source"), patch.object(ep, "interpreter", return_value=Path(sys.executable)):
            (self.source / ".installed.json").write_text(json.dumps(self.pin))
            ep.graphify(self.args, self.pin, self.source, self.cache, self.bundle, {}, run or self.fake_run, usage)
        return usage

    def test_working_tree_identity_includes_untracked_modified_and_deleted(self):
        original = ep.fingerprint(self.repo, ".", self.cache)
        (self.repo / "new.py").write_text("pass\n")
        added = ep.fingerprint(self.repo, ".", self.cache)
        self.assertNotEqual(original, added)
        (self.repo / "core.py").write_text("def double(x): return x + 2\n")
        changed = ep.fingerprint(self.repo, ".", self.cache)
        self.assertNotEqual(added, changed)
        (self.repo / "core.py").unlink()
        self.assertNotEqual(changed, ep.fingerprint(self.repo, ".", self.cache))

    def test_cache_does_not_invalidate_inputs(self):
        original = ep.fingerprint(self.repo, ".", self.cache)
        (self.cache / "evidence.log").write_text("private retained output\n")
        self.assertEqual(original, ep.fingerprint(self.repo, ".", self.cache))

    @unittest.skipIf(os.name == "nt", "symlink permissions vary on Windows")
    def test_symlinks_rejected(self):
        (self.repo / "alias.py").symlink_to(self.repo / "core.py")
        with self.assertRaisesRegex(ValueError, "symlink"):
            ep.fingerprint(self.repo, ".", self.cache)

    def test_build_query_reuse_and_stale_rejection(self):
        self.graph()
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.graph()["cache_hit"])
        self.assertEqual(len(self.calls), 1)
        self.args.action = "query"
        self.graph()
        self.assertEqual(len(self.calls), 2)
        (self.repo / "new.py").write_text("def extra(): pass\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            self.graph()
        self.assertEqual(len(self.calls), 2)

    def test_graph_tamper_is_not_silently_reused(self):
        usage = self.graph()
        (self.cache / usage["graph"]).write_text("{}")
        self.args.action = "query"
        with self.assertRaisesRegex(ValueError, "stale"):
            self.graph()

    def test_scope_escape_and_flag_injection_rejected(self):
        self.args.scope = ".."
        with self.assertRaisesRegex(ValueError, "within"):
            self.graph()
        self.args.scope = "."
        self.graph()
        self.args.action, self.args.query = "query", ["--backend=openai"]
        with self.assertRaisesRegex(ValueError, "flags"):
            self.graph()

    def test_changed_inputs_during_build_do_not_publish_freshness(self):
        def change(argv, env):
            self.fake_run(argv, env)
            (self.repo / "core.py").write_text("# concurrent edit\n")
        with self.assertRaisesRegex(ValueError, "changed during"):
            self.graph(change)
        self.assertFalse(list((self.cache / "graphs").glob("*.json")))

    def test_subprocess_success_failure_timeout_retained(self):
        calls = []
        ep.command([sys.executable, "-c", "print('hello')"], self.repo, self.bundle, os.environ.copy(), 5, calls)
        self.assertEqual(calls[-1]["exit_code"], 0)
        with self.assertRaises(RuntimeError):
            ep.command([sys.executable, "-c", "raise SystemExit(7)"], self.repo, self.bundle, os.environ.copy(), 5, calls)
        self.assertEqual(calls[-1]["exit_code"], 7)
        with self.assertRaises(RuntimeError):
            ep.command([sys.executable, "-c", "import time; time.sleep(5)"], self.repo, self.bundle, os.environ.copy(), .05, calls)
        self.assertEqual(calls[-1]["exit_code"], 124)
        self.assertEqual(len(list(self.bundle.glob("command-*.log"))), 3)

    def execute(self, action="load"):
        lock = self.repo / "fixture-lock.json"
        lock.write_text(json.dumps({"ponytail": self.pin}))
        skill = self.source / self.pin["skill"]
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("Fixture review instruction, not the upstream skill.\n")
        args = argparse.Namespace(repo=self.repo, cache=self.cache, tool="ponytail", action=action,
                                  task="adapter-fixture", why="test receipt mechanics", scope=".",
                                  timeout=5, kind="fixture")
        output = io.StringIO()
        with patch.object(ep, "LOCK", lock), patch.object(ep, "checkout", return_value=self.source), \
                patch.object(ep, "verified_source"), contextlib.redirect_stdout(output):
            result = ep.execute(args)
        receipt = next(self.cache.glob("runs/*/practice-feedback.json"))
        return result, receipt, output.getvalue()

    def test_loaded_is_not_applied_and_tokens_unknown(self):
        result, path, output = self.execute()
        raw = ep.load_record(path)
        self.assertEqual(result, 0)
        self.assertEqual(raw["practices"][0]["stage"], "loaded")
        self.assertEqual(raw["outcome"]["status"], "unverified")
        self.assertIsNone(raw["measurements"]["tokens"])
        self.assertGreater(raw["measurements"]["instruction_bytes"], 0)
        self.assertIn("Fixture review", output)
        self.assertTrue(ep.analyze(raw, self.cache)["outcome_evidence_resolved"])

    def test_skip_does_not_claim_applied(self):
        _, path, _ = self.execute("skip")
        self.assertEqual(ep.load_record(path)["practices"][0]["stage"], "not_used")

    def test_assessment_requires_evidence_and_is_immutable(self):
        _, path, _ = self.execute()
        before = path.read_bytes()
        args = argparse.Namespace(repo=self.repo, cache=self.cache, run=path.parent.name,
                                  status="accepted", effect="Fixture only", evidence=[], baseline=None)
        with self.assertRaisesRegex(ValueError, "evidence"):
            ep.assess(args)
        proof = self.repo / "fixture-check.log"
        proof.write_text("Fixture acceptance record; not a live model trial.\n")
        args.evidence = [proof.name]
        with contextlib.redirect_stdout(io.StringIO()):
            ep.assess(args)
        self.assertEqual(path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, "already exists"):
            ep.assess(args)

    def test_report_preserves_fixture_unknowns_and_evidence_mismatch(self):
        _, path, _ = self.execute()
        (path.parent / "upstream-skill.md").write_text("changed")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            ep.report(argparse.Namespace(cache=self.cache, json=True))
        report = json.loads(output.getvalue())
        self.assertEqual(report["rows"][0]["kind"], "fixture")
        self.assertIsNone(report["rows"][0]["assessment"])
        self.assertFalse(report["rows"][0]["evidence_resolved"])
        self.assertIn("absence is not zero use", report["coverage"])

    def test_revision_and_dirty_checkout_rejected(self):
        pin = {"revision": "wrong"}
        with self.assertRaisesRegex(ValueError, "revision"):
            ep.verified_source(self.repo, pin)
        pin["revision"] = self.git("rev-parse", "HEAD").decode().strip()
        (self.repo / "core.py").write_text("# modified\n")
        with self.assertRaisesRegex(ValueError, "dirty"):
            ep.verified_source(self.repo, pin)


if __name__ == "__main__":
    unittest.main()
