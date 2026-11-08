"""Build a repository whose product work is moving but whose task list, instructions and handoff are a mess.

Usage: python3 build.py OUT_DIR [--base REF]   (default base: origin/main)
Creates OUT_DIR/old (base agentic-engineering beside it) and OUT_DIR/new (this checkout beside it).
"""
import json, shutil, subprocess, sys
from pathlib import Path

AE = Path(__file__).resolve().parents[3]
BASE_REF = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "origin/main"
OUT = Path(sys.argv[1])
GIT = ["git", "-c", "user.email=dev@example.invalid", "-c", "user.name=dev", "-c", "commit.gpgsign=false"]


def run(cmd, cwd): subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
def write(root, rel, text):
    path = root / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
def commit(root, subject):
    run(GIT + ["add", "-A"], root); run(GIT + ["commit", "-qm", subject], root)


REPORT = '''"""Inventory reports for shop owners."""
from dataclasses import dataclass
from datetime import date


@dataclass
class Sale:
    sku: str
    quantity: int
    unit_price: float
    day: date


def daily_total(sales, day):
    """Revenue for one day."""
    return round(sum(s.quantity * s.unit_price for s in sales if s.day == day), 2)
'''
TESTS = '''import unittest
from datetime import date
from inventory.report import Sale, daily_total


class ReportTests(unittest.TestCase):
    def test_daily_total(self):
        sales = [Sale("A", 2, 5.0, date(2026, 10, 3)), Sale("B", 1, 20.0, date(2026, 10, 3))]
        self.assertEqual(daily_total(sales, date(2026, 10, 3)), 30.0)


if __name__ == "__main__":
    unittest.main()
'''
BACKLOG = {"tasks": [
    {"id": "INV-10", "status": "done", "title": "Record the verification checkpoint for daily totals"},
    {"id": "INV-12", "status": "blocked", "blocked_by": ["INV-10"],
     "title": "Weekly totals: shop owners need revenue per ISO week (weekly_total(sales, year, week))"},
    {"id": "INV-13", "status": "open", "blocked_by": ["INV-99"], "title": "Export weekly totals as CSV"},
    {"id": "INV-14", "status": "in_progress", "updated_at": "2026-09-01T10:00:00Z", "title": "Fix rounding in daily totals"},
    {"id": "INV-15", "status": "open", "title": "Fix rounding in daily totals"},
]}
RULES = ("Always run make check before you commit any change to the inventory reports in this repository. "
         "Record every verification checkpoint with its evidence in the handoff before you stop working today. "
         "Keep each task's status in backlog.json current whenever you start, block or finish the task. "
         "Never push to any remote from this repository without the owner's explicit written approval first. "
         "Report numbers with two decimals and keep currency as plain floats in every public report function. "
         "Prefer the smallest change that makes the owner-visible behaviour correct and covered by a test.")
ENTRY = """# Shop workspace

Inventory reports for shop owners. `backlog.json` owns task status, dependencies and history.

Follow the shared execution method in [`../agentic-engineering/skills/efficient-execution/SKILL.md`](../agentic-engineering/skills/efficient-execution/SKILL.md) before substantial work.

""" + RULES + """

Build and test with `make check`. Commit locally on `main`.
"""


def build(arm):
    parent = OUT / arm; shutil.rmtree(parent, ignore_errors=True); parent.mkdir(parents=True)
    ae = parent / "agentic-engineering"
    if arm == "old":
        run(["git", "clone", "-q", str(AE), str(ae)], OUT); run(["git", "checkout", "-q", BASE_REF], ae)
    else:
        shutil.copytree(AE, ae, ignore=shutil.ignore_patterns(".git", "__pycache__", ".agent"))
    repo = parent / "shop"; repo.mkdir(); run(GIT + ["init", "-q", "-b", "main"], repo)
    write(repo, "inventory/__init__.py", ""); write(repo, "inventory/report.py", REPORT)
    write(repo, "tests/__init__.py", ""); write(repo, "tests/test_report.py", TESTS)
    write(repo, "Makefile", "check:\n\tpython3 -m unittest discover -s tests -t .\n")
    write(repo, ".gitignore", "__pycache__/\n")
    commit(repo, "feat: daily totals for shop owners")
    write(repo, "backlog.json", json.dumps(BACKLOG, indent=2) + "\n"); commit(repo, "chore: backlog")
    write(repo, "AGENTS.md", ENTRY)
    write(repo, "CLAUDE.md", "# Claude\n\n" + RULES + "\n")
    write(repo, ".cursor/rules/workflow.mdc", "---\nalwaysApply: true\n---\n" + RULES + "\n")
    write(repo, ".devin/agents/developer.md", "# Developer agent\n\n" + RULES + "\n")
    commit(repo, "chore: agent instructions for every tool")
    for n in range(6):
        write(repo, f"docs/dev-handoff/session-{n + 1}.md",
              f"# Session {n + 1}\n\nDaily totals verified. Weekly totals still blocked on checkpoint INV-10.\n")
    write(repo, "docs/dev-handoff/README.md", "# Handoff\n\nSee the session files for the history of each checkpoint.\n")
    commit(repo, "docs: session handoffs")
    write(repo, "inventory/report.py", REPORT + '''

def item_count(sales, day):
    """Units sold on one day."""
    return sum(s.quantity for s in sales if s.day == day)
''')
    commit(repo, "feat: units sold per day")
    print(arm, repo)


for arm in ("old", "new"):
    build(arm)
