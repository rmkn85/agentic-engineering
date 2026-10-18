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
                patch.object(ep, "verified_source"), \
                patch.object(ep, "verified_skill", return_value=(self.pin["skill"], skill.read_bytes(), ep.digest(skill))), \
                contextlib.redirect_stdout(output):
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

    def committed_skill(self, name="caveman-review"):
        relative = ep.SKILLS[name][1]
        skill = self.repo / relative
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text("Fixture skill only.\n")
        self.git("add", relative)
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "skill")
        pin = {"revision": self.git("rev-parse", "HEAD").decode().strip(),
               "skills": {name: {"path": relative, "sha256": ep.digest(skill)}}}
        return skill, pin

    def test_reviewed_skills_are_exact_pinned_bytes(self):
        for name in ("caveman-review", "caveman-commit"):
            skill, pin = self.committed_skill(name)
            relative, content, sha256 = ep.verified_skill(self.repo, pin, name)
            self.assertEqual(relative, ep.SKILLS[name][1])
            self.assertEqual(content, skill.read_bytes())
            self.assertEqual(sha256, pin["skills"][name]["sha256"])

    def test_skill_tamper_is_rejected_even_when_git_status_is_clean(self):
        skill, pin = self.committed_skill()
        self.git("update-index", "--assume-unchanged", str(skill.relative_to(self.repo)))
        skill.write_text("Changed instruction.\n")
        ep.verified_source(self.repo, pin)
        with self.assertRaisesRegex(ValueError, "pinned Git blob"):
            ep.verified_skill(self.repo, pin, "caveman-review")

    def test_skill_paths_capabilities_and_review_digest_are_bounded(self):
        _, pin = self.committed_skill()
        for name in ("../SKILL.md", "caveman", "caveman-learn", "cavecrew"):
            with self.assertRaisesRegex(ValueError, "unsupported skill"):
                ep.verified_skill(self.repo, pin, name)
        pin["skills"]["caveman-review"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "reviewed sha256"):
            ep.verified_skill(self.repo, pin, "caveman-review")
        pin["skills"]["caveman-review"]["path"] = "../SKILL.md"
        with self.assertRaisesRegex(ValueError, "allowlist"):
            ep.verified_skill(self.repo, pin, "caveman-review")

    def test_cli_load_routes_only_explicit_named_skills(self):
        for name, tool in ((None, "ponytail"), ("caveman-review", "caveman"),
                           ("caveman-commit", "caveman")):
            argv = ["external_practices.py", "load", "--task", "fixture", "--why", "bounded draft"]
            if name:
                argv += ["--skill", name]
            with patch.object(sys, "argv", argv), patch.object(ep, "execute", return_value=0) as execute:
                self.assertEqual(ep.main(), 0)
                args = execute.call_args.args[0]
                self.assertEqual(args.tool, tool)
                self.assertEqual(args.skill, name or "ponytail-review")
        for name in ("../SKILL.md", "caveman-learn", "cavecrew"):
            argv = ["external_practices.py", "load", "--skill", name, "--task", "fixture", "--why", "reject"]
            with patch.object(sys, "argv", argv), contextlib.redirect_stderr(io.StringIO()), \
                    patch.object(ep, "execute") as execute, self.assertRaises(SystemExit):
                ep.main()
            execute.assert_not_called()

    @unittest.skipIf(os.name == "nt", "symlink permissions vary on Windows")
    def test_skill_symlink_is_rejected(self):
        skill, pin = self.committed_skill()
        original = self.repo / "original.md"
        skill.rename(original)
        skill.symlink_to(original)
        with self.assertRaisesRegex(ValueError, "symlink"):
            ep.verified_skill(self.repo, pin, "caveman-review")


if __name__ == "__main__":
    unittest.main()
