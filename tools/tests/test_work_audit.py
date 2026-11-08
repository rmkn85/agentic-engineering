import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "work_audit.py"
GIT = ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t", "-c", "commit.gpgsign=false"]


class WorkAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(GIT + ["init", "-q", "-b", "main"], cwd=self.root, check=True)
        self.commit("src/app.py", "def run():\n    return 1\n", "feat: first product behaviour")

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def commit(self, rel, text, subject):
        self.write(rel, text)
        subprocess.run(GIT + ["add", "-A"], cwd=self.root, check=True)
        subprocess.run(GIT + ["commit", "-qm", subject], cwd=self.root, check=True)

    def report(self, *args):  # noqa: D401
        result = subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), "--json", *args],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def kinds(self, report):
        return [f["kind"] for f in report["findings"]]

    def finding(self, report, kind):
        self.assertIn(kind, self.kinds(report))
        return next(f for f in report["findings"] if f["kind"] == kind)

    def test_records_only_history_is_a_loop_and_focus_asks_for_product_change(self):
        for n in range(6):
            self.commit(f"docs/handoff-notes-{n}.md", f"note {n}\n", f"docs: record checkpoint {n}")
        report = self.report()
        self.assertEqual(report["mix"].get("records"), 6)
        self.assertIn("loop", self.kinds(report))
        self.assertIn("change product behaviour", report["focus"])

    def test_a_recent_product_commit_ends_the_loop_finding(self):
        for n in range(6):
            self.commit(f"docs/notes-{n}.md", f"note {n}\n", f"docs: record checkpoint {n}")
        self.commit("src/app.py", "def run():\n    return 9\n", "feat: real change")
        self.commit("docs/handoff.md", "short\n", "docs: replace handoff")
        self.assertNotIn("loop", self.kinds(self.report()))

    def test_a_goal_the_finish_gate_found_met_is_not_open(self):
        self.write(".agent/goal.json", json.dumps({"goal": "Exports work", "acceptance": []}))
        self.assertIn("goal", self.kinds(self.report()))
        self.write(".agent/goal-status.json", json.dumps({"goal": "Exports work", "met": True}))
        self.assertNotIn("goal", self.kinds(self.report()))
        self.write(".agent/goal-status.json", json.dumps({"goal": "Other goal", "met": True}))
        self.assertIn("goal", self.kinds(self.report()))

    def test_product_history_is_not_a_loop(self):
        for n in range(6):
            self.commit("src/app.py", f"def run():\n    return {n}\n", f"feat: behaviour step {n}")
        self.assertNotIn("loop", self.kinds(self.report()))

    def test_process_files_count_as_support_not_product(self):
        for n, rel in enumerate(("Makefile", ".github/workflows/ci.yml", "AGENTS.md", "scripts/gate.sh")):
            self.commit(rel, f"x{n}\n", f"chore: tighten gate {n}")
        report = self.report()
        self.assertEqual(report["mix"].get("process"), 4)
        self.assertIn("loop", self.kinds(report))

    def test_a_commit_touching_product_counts_as_product(self):
        self.write("docs/a.md", "doc\n")
        self.commit("src/app.py", "def run():\n    return 2\n", "feat: change with its doc")
        self.assertEqual(self.report()["mix"], {"product": 2})

    def test_repeating_subjects_are_reported(self):
        for n in range(3):
            self.commit("src/app.py", f"def run():\n    return {n + 5}\n", f"fix: retry gateway startup {n}")
        self.assertIn("repeat", self.kinds(self.report()))

    def test_old_repeats_followed_by_different_work_are_not_reported(self):
        for n in range(3):
            self.commit("src/app.py", f"def run():\n    return {n + 5}\n", f"fix: retry gateway startup {n}")
        for n, subject in enumerate(("feat: export monthly totals", "fix: round revenue to cents",
                                     "feat: sort rows by revenue")):
            self.commit("src/app.py", f"def run():\n    return {n + 50}\n", subject)
        self.assertNotIn("repeat", self.kinds(self.report()))

    def test_unfinished_code_is_found_in_product_not_in_docs(self):
        self.commit("src/pay.py", "def pay():\n    raise NotImplementedError\n", "feat: payment stub")
        self.commit("tests/test_pay.py", "import unittest\n@unittest.skip('later')\ndef test_pay():\n    pass\n",
                    "test: payment")
        self.commit("tests/test_env.py", "import unittest, shutil\n"
                    "@unittest.skipUnless(shutil.which('git'), 'needs git')\ndef test_env():\n    pass\n", "test: env")
        self.commit("docs/plan.md", "TODO: write the plan\n", "docs: plan")
        self.commit("src/lint.py", '"""Find markers.\n\nTODO and FIXME lines are reported.\n"""\n'
                    "PATTERN = 'TODO|FIXME'\nSAMPLE = \"raise NotImplementedError\"\n", "feat: lint")
        self.commit("src/lint.js", "const PATTERN = \"TODO|FIXME\";\n", "feat: lint js")
        finding = self.finding(self.report(), "unfinished")
        self.assertIn("2 stubs or skipped tests", finding["problem"])
        self.assertNotIn("todo-notes", self.kinds(self.report()))  # marker words inside strings are data
        self.assertIn("src/pay.py", finding["problem"] + finding["action"])

    def test_a_loop_with_unfinished_code_names_the_target_and_says_to_continue(self):
        self.commit("src/pay.py", "def pay():\n    raise NotImplementedError\n", "feat: payment stub")
        for n in range(6):
            self.commit(f"docs/n{n}.md", "x\n", f"docs: checkpoint {n} notes")
        focus = self.report()["focus"]
        self.assertIn("src/pay.py:2", focus)
        self.assertIn("does not end the session", focus)

    def test_inconsistent_task_list_is_reported_and_comes_before_handoff(self):
        self.commit("backlog.json", json.dumps({"tasks": [
            {"id": "T1", "status": "done", "title": "Record checkpoint"},
            {"id": "T2", "status": "blocked", "blocked_by": ["T1"], "title": "Monthly export"},
            {"id": "T3", "status": "open", "blocked_by": ["T9"], "title": "Export CSV"},
            {"id": "T4", "status": "in_progress", "updated_at": "2020-01-01T00:00:00Z", "title": "Fix rounding"},
            {"id": "T5", "status": "open", "title": "Fix  rounding!"},
        ]}), "chore: backlog")
        self.commit("docs/dev-handoff/README.md", "current\n", "docs: handoff")
        self.commit("docs/dev-handoff/old.md", "older\n", "docs: handoff history")
        report = self.report()
        finding = self.finding(report, "tasks")
        for expected in ("T2 is blocked only by finished T1", "T3 depends on missing T9",
                         "T4 claimed in progress", "duplicate open tasks T4, T5"):
            self.assertIn(expected, finding["problem"])
        self.assertLess(self.kinds(report).index("tasks"), self.kinds(report).index("handoff"))
        self.assertIn("fix: remove T9 from its blockers", finding["action"])
        self.assertIn("not owner decisions", finding["action"])
        handoff = self.finding(report, "handoff")["action"]
        self.assertIn("Rewrite docs/dev-handoff/README.md", handoff)
        self.assertIn("delete docs/dev-handoff/old.md", handoff)

    def test_odd_task_shapes_do_not_crash_or_split(self):
        self.commit("backlog.json", json.dumps({"tasks": [
            {"id": "A", "status": "done", "title": "a"},
            {"id": "B", "status": "blocked", "blocked_by": "A", "title": "b"},
            {"id": "C", "status": "open", "blocked_by": 7, "title": "c"},
            {"id": "D", "status": "open", "dependencies": "A", "title": "d"},
        ]}), "chore: backlog")
        problem = self.finding(self.report(), "tasks")["problem"]
        self.assertIn("B is blocked only by finished A", problem)
        self.assertIn("C depends on missing 7", problem)

    def test_abstract_methods_and_site_root_links_are_not_findings(self):
        self.commit("src/base.py", "import abc\n\nclass Base(abc.ABC):\n    @abc.abstractmethod\n"
                    "    def run(self):\n        raise NotImplementedError\n", "feat: base")
        self.commit("docs/my guide.md", "x\n", "docs: guide")
        self.commit("AGENTS.md", "See [g](/docs/my%20guide.md) and [h](docs/my%20guide.md).\n", "chore: entry")
        kinds = self.kinds(self.report())
        self.assertNotIn("unfinished", kinds)
        self.assertNotIn("stale-references", kinds)

    def test_beads_issues_are_read(self):
        rows = [{"id": "bd-1", "title": "a", "status": "closed"},
                {"id": "bd-2", "title": "b", "status": "blocked",
                 "dependencies": [{"depends_on_id": "bd-1", "type": "blocks"}]}]
        self.commit(".beads/issues.jsonl", "".join(json.dumps(r) + "\n" for r in rows), "chore: beads")
        finding = self.finding(self.report(), "tasks")
        self.assertIn("bd-2 is blocked only by finished bd-1", finding["problem"])

    def test_tasks_can_come_from_a_configured_tracker_command(self):
        rows = [{"id": "bd-7", "title": "x", "status": "done"},
                {"id": "bd-8", "title": "y", "status": "blocked", "blocked_by": ["bd-7"]}]
        bin_dir = self.root / ".fakebin"
        bin_dir.mkdir()
        (bin_dir / "bd").write_text("#!%s\nimport json\nfor r in %r:\n    print(json.dumps(r))\n" % (sys.executable, rows))
        (bin_dir / "bd").chmod(0o755)
        self.write(".agent/audit.json", json.dumps({"tasks_command": ["bd", "list", "--json"]}))
        env = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
        result = subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), "--json"],
                                capture_output=True, text=True, check=True, env=env)
        problem = self.finding(json.loads(result.stdout), "tasks")["problem"]
        self.assertIn("bd-8 is blocked only by finished bd-7", problem)

    def test_a_repository_cannot_make_the_audit_run_arbitrary_commands(self):
        self.write(".agent/audit.json", json.dumps(
            {"tasks_command": [sys.executable, "-c", "open('PWNED', 'w').write('x')"]}))
        report = self.report()
        self.assertFalse((self.root / "PWNED").exists())
        self.assertIn("ignored tasks_command", " ".join(report["notes"]))
        self.write(".agent/audit.json", json.dumps({"tasks_command": ["bd", "delete", "bd-1"]}))
        self.assertIn("ignored tasks_command", " ".join(self.report()["notes"]))

    def test_code_named_handoff_is_never_a_handoff_to_delete(self):
        self.commit("src/handoff.py", "def handoff():\n    return 1\n", "feat: handoff api")
        self.commit("tests/test_handoff.py", "def test_handoff():\n    assert True\n", "test: handoff")
        self.commit("docs/dev-handoff/README.md", "current\n", "docs: handoff")
        self.commit("docs/dev-handoff/old.md", "old\n", "docs: old handoff")
        action = self.finding(self.report(), "handoff")["action"]
        self.assertNotIn("handoff.py", action)
        self.assertIn("delete docs/dev-handoff/old.md", action)

    def test_scattered_and_repeated_instructions_are_reported(self):
        rule = "Always run the full verification suite before you publish any change to the shared branch."
        for rel in ("AGENTS.md", "CLAUDE.md", ".cursor/rules/a.mdc", ".devin/agents/b.md", ".github/copilot-instructions.md"):
            self.commit(rel, "\n\n".join(f"{rule} Rule {n} applies to every task in this repository today."
                                          for n in range(5)) + "\n", f"chore: {rel}")
        finding = self.finding(self.report(), "instructions")
        self.assertIn("5 agent instruction files", finding["problem"])
        self.assertIn("Delete the repeated text from .cursor/rules/a.mdc", finding["action"])
        self.assertIn("Make CLAUDE.md a pointer: @AGENTS.md", finding["action"])
        self.assertIn("needs no owner decision", finding["action"])

    def test_one_short_instruction_file_is_not_a_finding(self):
        self.commit("AGENTS.md", "Run make check before you commit any change to this repository.\n", "chore: entry")
        self.assertNotIn("instructions", self.kinds(self.report()))

    def test_oversized_code_is_reported_but_never_the_focus(self):
        self.commit("configs/allowed-activities.json", "{}\n", "chore: allowlist")
        body = "".join(f"    x{n} = {n}\n" for n in range(130))
        self.commit("src/big.py", "def huge():\n" + body + "    return 1\n", "feat: big")
        report = self.report()
        finding = self.finding(report, "size")
        self.assertIn("function huge", finding["problem"])
        self.assertEqual(self.kinds(report), ["size"])
        self.assertNotIn("split", report["focus"])

    def test_tests_that_assert_nothing_are_reported(self):
        self.commit("tests/test_a.py", "def check(x):\n    assert x\n\ndef test_ok():\n    check(1)\n\n"
                    "def test_empty():\n    run = 1\n", "test: a")
        problem = self.finding(self.report(), "vacuous-tests")["problem"]
        self.assertIn("test_empty", problem)
        self.assertNotIn("test_ok", problem)

    def test_checks_that_cannot_fail_are_reported_but_tolerated_setup_is_not(self):
        self.commit(".github/workflows/ci.yml", "steps:\n  - run: git fetch origin main || true\n", "ci: fetch")
        self.assertNotIn("cannot-fail", self.kinds(self.report()))
        self.commit(".github/workflows/ci.yml", "steps:\n  - run: pytest -q || true\n", "ci: tests")
        self.assertIn("pytest -q || true", self.finding(self.report(), "cannot-fail")["problem"])
        self.commit("Makefile", "lint:\n\truff check . --exit-zero\n", "build: lint")
        self.assertIn("Makefile:2", self.finding(self.report(), "cannot-fail")["problem"])

    def test_links_to_missing_files_in_instructions_are_reported(self):
        self.commit("docs/guide.md", "guide\n", "docs: guide")
        self.commit("AGENTS.md", "See [guide](docs/guide.md) and [old](docs/removed.md).\n", "chore: entry")
        problem = self.finding(self.report(), "stale-references")["problem"]
        self.assertIn("docs/removed.md", problem)
        self.assertNotIn("docs/guide.md", problem)

    def test_instruction_growth_within_the_window_is_reported(self):
        self.commit("AGENTS.md", "Run make check.\n", "chore: entry")
        for n in range(4):
            self.commit("AGENTS.md", "Run make check.\n" + "Also remember this rule. " * (120 * (n + 1)),
                        f"docs: add rule {n}")
        self.assertIn("instruction-growth", self.kinds(self.report("--commits", "4")))

    def test_too_much_work_in_progress_is_reported(self):
        for n in range(12):
            subprocess.run(GIT + ["switch", "-q", "-c", f"wip-{n}", "main"], cwd=self.root, check=True)
            self.commit(f"src/wip{n}.py", "x = 1\n", f"feat: wip {n}")
        subprocess.run(GIT + ["switch", "-q", "main"], cwd=self.root, check=True)
        self.assertIn("12 unmerged branches", self.finding(self.report(), "wip")["problem"])

    def test_large_tracked_files_and_missing_allowlist_are_reported(self):
        self.commit("assets/blob.bin", "x" * 5_100_000, "chore: blob")
        report = self.report()
        self.assertIn("assets/blob.bin", self.finding(report, "large-files")["problem"])
        self.assertIn("allowlist", self.kinds(report))
        self.commit("configs/allowed-activities.json", "{}\n", "chore: allowlist")
        self.assertNotIn("allowlist", self.kinds(self.report()))

    def test_every_finding_names_its_area(self):
        for n in range(6):
            self.commit(f"docs/n{n}.md", "x\n", f"docs: note {n}")
        report = self.report()
        self.assertTrue(report["findings"])
        self.assertTrue(all(f["area"] in ("direction", "evidence", "knowledge", "instructions", "flow", "harness",
                                          "code") for f in report["findings"]))

    def test_validator_style_tests_are_real_tests(self):
        self.commit("tests/test_contract.py", "from src.app import run\n\ndef test_contract_validates():\n"
                    "    run()\n\ndef test_placeholder():\n    pass\n", "test: contract")
        problem = self.finding(self.report(), "vacuous-tests")["problem"]
        self.assertIn("test_placeholder", problem)
        self.assertNotIn("test_contract_validates", problem)

    def test_interfaces_vendored_code_and_notes_do_not_become_the_focus(self):
        self.commit("src/base.py", "class Store:\n    def save(self, item):\n        raise NotImplementedError\n",
                    "feat: store interface")
        self.commit("vendor/lib/x.py", "def f():\n    raise NotImplementedError\n", "chore: vendor")
        self.commit("src/notes.py", "def g():\n    return 1  # TODO: cache this\n", "feat: g")
        self.commit("configs/allowed-activities.json", "{}\n", "chore: allowlist")
        report = self.report()
        self.assertNotIn("unfinished", self.kinds(report))
        self.assertIn("src/notes.py", self.finding(report, "todo-notes")["problem"])
        self.assertTrue(report["focus"].startswith("No waste signal"), report["focus"])
        self.commit("src/pay.py", "def pay():\n    raise NotImplementedError\n", "feat: pay stub")
        self.assertIn("src/pay.py:2", self.finding(self.report(), "unfinished")["action"])

    def test_verified_false_positives_can_be_recorded_with_a_reason(self):
        self.commit("src/pay.py", "def pay():\n    raise NotImplementedError\n", "feat: pay stub")
        self.commit(".agent/audit.json", json.dumps({"ignore": [
            {"kind": "unfinished", "path": "src/pay.py", "reason": "payment is intentionally disabled in this edition"},
            {"kind": "allowlist", "reason": "too short"}]}), "chore: audit config")
        report = self.report()
        self.assertNotIn("unfinished", self.kinds(report))
        self.assertIn("allowlist", self.kinds(report))
        self.assertTrue(any("invalid ignore rule" in note for note in report["notes"]))

    def test_handoff_that_grew_into_a_history_is_reported(self):
        self.commit("docs/dev-handoff/README.md", "current\n", "docs: handoff")
        self.commit("docs/dev-handoff/2026-11-01.md", "older\n", "docs: handoff history")
        self.assertIn("handoff", self.kinds(self.report()))

    def test_long_entry_and_required_reading_are_reported_but_on_demand_links_are_not(self):
        self.commit("guide/deep.md", "word " * 7000, "feat: big guide")
        self.commit("AGENTS.md", "Use [the guide](guide/deep.md) when deploying.\n", "chore: entry")
        self.assertNotIn("entry", self.kinds(self.report()))
        self.commit("AGENTS.md", "Read [the guide](guide/deep.md) before any task.\n", "chore: entry")
        self.assertIn("entry", self.kinds(self.report()))

    def test_open_goal_record_comes_first(self):
        for n in range(6):
            self.commit(f"docs/n{n}.md", "x\n", f"docs: note {n}")
        self.write(".agent/goal.json", json.dumps({"goal": "Exports work", "acceptance": []}))
        report = self.report()
        self.assertEqual(self.kinds(report)[0], "goal")
        self.assertIn("goal.json", report["focus"])

    def test_product_paths_can_be_declared(self):
        for n in range(4):
            self.commit(f"scripts/engine{n}.sh", "echo\n", f"feat: engine part {n}")
        self.assertIn("loop", self.kinds(self.report()))
        self.write(".agent/audit.json", json.dumps({"product": ["scripts/*"]}))
        self.assertNotIn("loop", self.kinds(self.report()))

    def test_audit_is_read_only_and_strict_mode_fails_on_findings(self):
        for name in "abcd":
            self.commit(f"docs/{name}.md", "x\n", f"docs: {name}")
        before = subprocess.run(["git", "status", "--porcelain"], cwd=self.root, capture_output=True, text=True).stdout
        strict = subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), "--strict"],
                                capture_output=True, text=True, check=False)
        self.assertEqual(strict.returncode, 1)
        self.assertIn("FOCUS:", strict.stdout)
        after = subprocess.run(["git", "status", "--porcelain"], cwd=self.root, capture_output=True, text=True).stdout
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
