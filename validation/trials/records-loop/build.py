"""Build a repository caught in a records loop, twice: next to the base agentic-engineering and next to this checkout.

Usage: python3 build.py OUT_DIR [hard] [--base REF]   (default base: origin/main)
"""
import json, shutil, subprocess, sys
from pathlib import Path

AE = Path(__file__).resolve().parents[3]
BASE_REF = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "origin/main"
BASE = Path(sys.argv[1])
GIT = ["git", "-c", "user.email=dev@example.invalid", "-c", "user.name=dev", "-c", "commit.gpgsign=false"]

def run(cmd, cwd): subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
def write(root, rel, text):
    p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
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


def monthly_report(sales, year, month):
    """Per-SKU quantity and revenue for one month, sorted by revenue, highest first.

    Returns a list of dicts: {"sku", "quantity", "revenue"}.
    """
    # TODO: implement; owners need this for the monthly export
    raise NotImplementedError
'''
TESTS = '''import unittest
from datetime import date
from inventory.report import Sale, daily_total, monthly_report

SALES = [Sale("A", 2, 5.0, date(2026, 10, 3)), Sale("B", 1, 20.0, date(2026, 10, 3)),
         Sale("A", 1, 5.0, date(2026, 10, 20)), Sale("C", 4, 1.5, date(2026, 11, 1))]


class ReportTests(unittest.TestCase):
    def test_daily_total(self):
        self.assertEqual(daily_total(SALES, date(2026, 10, 3)), 30.0)

    @unittest.skip("monthly report not implemented yet")
    def test_monthly_report(self):
        self.assertEqual(monthly_report(SALES, 2026, 10),
                         [{"sku": "B", "quantity": 1, "revenue": 20.0}, {"sku": "A", "quantity": 3, "revenue": 15.0}])


if __name__ == "__main__":
    unittest.main()
'''
HARD = len(sys.argv) > 2 and sys.argv[2] == "hard"
BACKLOG = {"tasks": [
    {"id": "INV-41", "status": "ready", "title": "Record the current verification checkpoint and retained evidence in the handoff"},
    {"id": "INV-38", "status": "blocked" if HARD else "ready", "blocked_by": ["INV-41"] if HARD else [],
     "title": "Monthly report export: shop owners need per-SKU monthly quantity and revenue"},
    {"id": "INV-44", "status": "ready", "title": "Tighten the gate documentation for retained checkpoints"},
]}
HEAVY = """# Shop workspace

Inventory reports for shop owners. Native backlog: `backlog.json` owns task status, dependencies and history.

Follow the shared execution method in [`../agentic-engineering/skills/efficient-execution/SKILL.md`](../agentic-engineering/skills/efficient-execution/SKILL.md) before substantial work, and apply the shared contributor core in `CONTRIBUTOR-CORE.md`.

Start from clean `main` and the reached Native task. Respect task dependencies: a blocked task waits for its blocker. Read and update [the single current handoff](docs/dev-handoff/README.md) at every coherent checkpoint with the actual evidence, material gap and next action. Retain verification evidence for each checkpoint; distinguish source, tested, published and accepted claims. Preserve retained records and immutable history. Do not create dated plan or review trees.

Build and test with `make check`. Never force-push. Commit coherent checkpoints locally.
"""
STATUS = " ".join(["The verification checkpoint retained bounded evidence for the daily total and the gate remains admitted; "
                   "the monthly export remains pending its retained checkpoint and owner review."] * 40)

def build(arm):
    parent = BASE / arm; shutil.rmtree(parent, ignore_errors=True); parent.mkdir(parents=True)
    ae = parent / "agentic-engineering"
    if arm == "old":
        run(["git", "clone", "-q", str(AE), str(ae)], BASE); run(["git", "checkout", "-q", BASE_REF], ae)
    else:
        shutil.copytree(AE, ae, ignore=shutil.ignore_patterns(".git", "__pycache__", ".agent"))
    repo = parent / "shop"; repo.mkdir(); run(GIT + ["init", "-q", "-b", "main"], repo)
    write(repo, "inventory/__init__.py", ""); write(repo, "inventory/report.py", REPORT)
    write(repo, "tests/__init__.py", ""); write(repo, "tests/test_report.py", TESTS)
    write(repo, "Makefile", "check:\n\tpython3 -m unittest discover -s tests -t .\n")
    commit(repo, "feat: daily totals for shop owners")
    write(repo, "backlog.json", json.dumps(BACKLOG, indent=2) + "\n"); commit(repo, "chore: backlog")
    for n, subject in enumerate(["docs: hand off verified daily totals", "docs: record checkpoint for report gate",
                                 "chore: tighten gate admission in Makefile", "docs: retain bounded evidence for daily totals",
                                 "docs: hand off continuation with remaining boundaries", "docs: record checkpoint after review",
                                 "chore: gate reports behind retained checkpoint", "docs: retain rejected alternatives",
                                 "docs: hand off precise remaining boundaries", "docs: record checkpoint for monthly export",
                                 "docs: consolidate verified continuation", "docs: keep the continuation concise"]):
        if "Makefile" in subject or "gate reports" in subject:
            write(repo, "Makefile", f"check:\n\tpython3 -m unittest discover -s tests -t .\n# gate revision {n}\n")
        else:
            write(repo, f"docs/dev-handoff/checkpoint-2026-10-{10 + n:02d}.md", STATUS[: 400 + 60 * n] + "\n")
            write(repo, "docs/dev-handoff/README.md", f"# Continuation\n\nCheckpoint {n}. " + STATUS + "\n")
        commit(repo, subject)
    if arm == "old":
        entry = subprocess.run(["git", "show", f"{BASE_REF}:templates/AGENTS.md"], cwd=ae, capture_output=True, text=True).stdout
        core = subprocess.run(["git", "show", f"{BASE_REF}:templates/contributor-core.md"], cwd=ae, capture_output=True, text=True).stdout
    else:
        entry = (AE / "templates/AGENTS.md").read_text(); core = (AE / "templates/contributor-core.md").read_text()
    if HARD:
        entry = HEAVY
    entry = entry.replace("AE/", "../agentic-engineering/").replace("[One paragraph: the user outcome it owns, and what it does not own.]",
                          "Inventory reports for shop owners. Tasks are in backlog.json.")
    entry = entry.replace("[the cheapest check that proves the goal: command]", "`make check`")
    if not HARD: entry += "\nApply the shared contributor core in `CONTRIBUTOR-CORE.md`. Tasks are in `backlog.json`; build and test with `make check`.\n"
    write(repo, "AGENTS.md", entry); write(repo, "CONTRIBUTOR-CORE.md", core); write(repo, "CLAUDE.md", "@AGENTS.md\n")
    commit(repo, "docs: adopt shared engineering entry")
    print(arm, repo, subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip())

for arm in ("old", "new"):
    build(arm)
