import json
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

    def report(self, *args):
        result = subprocess.run([sys.executable, str(TOOL), "--root", str(self.root), "--json", *args],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def kinds(self, report):
        return [f["kind"] for f in report["findings"]]

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
        finding = next(f for f in self.report()["findings"] if f["kind"] == "unfinished")
        self.assertIn("2 unfinished markers", finding["problem"])
        self.assertIn("src/pay.py", finding["problem"] + finding["action"])

    def test_a_loop_with_unfinished_code_names_the_target_and_says_to_continue(self):
        self.commit("src/pay.py", "def pay():\n    raise NotImplementedError\n", "feat: payment stub")
        for n in range(6):
            self.commit(f"docs/n{n}.md", "x\n", f"docs: checkpoint {n} notes")
        focus = self.report()["focus"]
        self.assertIn("src/pay.py:2", focus)
        self.assertIn("does not end the session", focus)

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
