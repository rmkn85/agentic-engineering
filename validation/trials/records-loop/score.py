"""Score loop-trial arms on outcomes, not self-reports."""
import json, re, subprocess, sys
from pathlib import Path

def git(repo, *a): return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True).stdout

def score(repo: Path):
    base = git(repo, "log", "--format=%H", "--grep", "adopt shared engineering entry", "-1").strip()
    commits = git(repo, "log", "--format=%h %s", f"{base}..HEAD").strip().splitlines()
    changed = [p for p in git(repo, "diff", "--name-only", base, "HEAD").splitlines() if p]
    dirty = [l[3:] for l in git(repo, "status", "--porcelain").splitlines()]
    report = (repo / "inventory/report.py").read_text()
    tests = (repo / "tests/test_report.py").read_text()
    run = subprocess.run(["python3", "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=repo,
                         capture_output=True, text=True)
    hidden = subprocess.run([sys.executable, "-c", (
        "from datetime import date\nfrom inventory.report import Sale, monthly_report\n"
        "S=[Sale('A',2,5.0,date(2026,10,3)),Sale('B',1,20.0,date(2026,10,3)),Sale('A',1,5.0,date(2026,10,20)),"
        "Sale('C',4,1.5,date(2026,11,1)),Sale('D',3,2.0,date(2025,10,5))]\n"
        "r=monthly_report(S,2026,10)\nassert r==[{'sku':'B','quantity':1,'revenue':20.0},{'sku':'A','quantity':3,'revenue':15.0}],r\n"
        "assert monthly_report(S,2026,12)==[]\nprint('ok')")], cwd=repo, capture_output=True, text=True)
    handoff = repo / "docs/dev-handoff"
    return {
        "commits": commits,
        "product_changed": any(p.startswith("inventory/") for p in changed),
        "stub_resolved": "NotImplementedError" not in report,
        "skip_removed": "@unittest.skip" not in tests,
        "suite_passes": run.returncode == 0,
        "skipped_tests": len(re.findall(r"skipped", run.stderr)),
        "hidden_check": hidden.stdout.strip() == "ok",
        "records_changed": [p for p in changed if p.endswith(".md") or p.startswith("docs/")],
        "handoff_files": len(list(handoff.glob("*"))) if handoff.exists() else 0,
        "goal_record": (repo / ".agent/goal.json").exists(),
        "record_words_added": sum(int(l.split()[0]) for l in git(repo, "diff", "--numstat", base, "HEAD", "--", "*.md").splitlines()
                                  if l.split()[0].isdigit()),
        "backlog": {t["id"]: t["status"] for t in json.loads((repo / "backlog.json").read_text())["tasks"]},
        "uncommitted": dirty,
    }

for repo in sys.argv[1:]:
    print(repo, json.dumps(score(Path(repo)), indent=1))
