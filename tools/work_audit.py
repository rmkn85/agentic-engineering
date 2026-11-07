#!/usr/bin/env python3
"""Tell an agent what to focus on in this repository, from its own history.

Read-only and host-neutral: any agent, any model, any reasoning level runs
the same command and gets the same answer.

    python3 tools/work_audit.py [--root DIR] [--commits N] [--json] [--strict]

It prints one FOCUS line (the first thing to do) and ranked findings, each
with the action that fixes it:

- goal:     an open .agent/goal.json is the current work; finish it first
- loop:     most recent commits changed only records or process, not product
- repeat:   the same commit subject keeps coming back
- unfinished: TODO/FIXME/not-implemented/skipped tests in product code
- handoff:  handoff or continuation text that grew into a history
- entry:    always-loaded instructions too long to act on
- hygiene:  merged branches, extra worktrees, dated plans, tracked scratch

A commit counts as product when it changes any product path. Records are
docs, handoffs, evidence and notes; process is CI, build files, agent
configuration and instruction files; tests are tests and fixtures. Override
the product paths in .agent/audit.json: {"product": ["tools/*.py"]}.
Unmatched paths are product.

Scope: a heuristic over history and text. It points at likely waste and
unfinished work; it does not judge whether a change was right.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

INSTRUCTIONS = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md")
RECORDS = re.compile(r"(^|/)(docs?|handoffs?|dev-handoff|evidence|receipts?|records?|reports?|research|references|"
                     r"notes|plans?|retros?|reviews?|adr|decisions?|status|journal|changelog)(/|$)|"
                     r"\.(md|markdown|rst|txt|adoc|org)$|(^|/)(CHANGELOG|HISTORY|NOTES)[^/]*$", re.I)
PROCESS = re.compile(r"(^|/)(\.github|\.gitlab|\.circleci|\.claude|\.cursor|\.codex|\.agents?|\.devin|\.gemini|"
                     r"\.vscode|\.idea|\.devcontainer|ci|scripts)(/|$)|(^|/)(Makefile|GNUmakefile|[^/]*\.mk|"
                     r"\.gitlab-ci\.yml|\.pre-commit-config\.yaml|Procfile|process-compose\.yaml|"
                     r"AGENTS[^/]*\.md|CLAUDE\.md|GEMINI\.md)$", re.I)
TESTS = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?|testdata)(/|$)|(^|/)(test_[^/]*|[^/]*_test\.\w+|"
                   r"[^/]*\.(test|spec)\.\w+)$", re.I)
UNFINISHED = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b|NotImplementedError|not implemented|unimplemented!|todo!\(|"
                        r"@unittest\.skip\(|pytest\.mark\.(skip|xfail)\b(?!if)|\b(it|describe|test)\.skip\(|@Disabled\b|"
                        r"\bt\.Skip\(", re.I)
HANDOFF = re.compile(r"(handoff|hand-off|continuation|dev-handoff)", re.I)
CODE = re.compile(r"\.(py|js|jsx|ts|tsx|go|rs|java|kt|cs|cpp|cc|c|h|hpp|rb|php|swift|scala|gd|lua|sh)$", re.I)
ENTRY_WORDS = 1500       # always-loaded instructions an agent can still act on
LINKED_WORDS = 6000      # entry plus the documents it tells every newcomer to read
REQUIRED = re.compile(r"\b(read|start (with|from|here)|apply|follow)\b", re.I)
HANDOFF_WORDS = 800      # a current handoff, not a history
SUPPORT_SHARE = 0.5      # records + process above this share of recent commits is a loop
RECENT = 3               # ...unless one of the latest commits already changes product


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def config(root: Path) -> dict:
    try:
        data = json.loads((root / ".agent" / "audit.json").read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def kind(path: str, product: list[str]) -> str:
    if any(fnmatch.fnmatch(path, pattern) for pattern in product):
        return "product"
    if TESTS.search(path):
        return "test"
    if PROCESS.search(path):
        return "process"
    if RECORDS.search(path):
        return "records"
    return "product"


def commit_mix(root: Path, count: int, product: list[str]) -> list[dict]:
    log = git(root, "log", f"-{count}", "--no-merges", "--name-only", "--format=\x1e%h\x1f%s")
    commits = []
    for block in log.split("\x1e")[1:]:
        head, _, body = block.partition("\n")
        sha, _, subject = head.partition("\x1f")
        paths = [p for p in body.splitlines() if p.strip()]
        kinds = {kind(p, product) for p in paths}
        main = next((k for k in ("product", "test", "process", "records") if k in kinds), "records")
        commits.append({"sha": sha, "subject": subject, "kind": main, "paths": len(paths)})
    return commits


def words(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").split())
    except OSError:
        return 0


def entry_reading(root: Path) -> tuple[int, int, list[str]]:
    """Words always loaded, and words in the local documents the entry tells every agent to read."""
    loaded = [root / name for name in INSTRUCTIONS if (root / name).is_file()]
    for path in list(loaded):  # @imports load too
        for target in re.findall(r"(?m)^\s*@(\S+)", path.read_text(encoding="utf-8", errors="replace")):
            candidate = (path.parent / target).resolve()
            if candidate.is_file() and candidate not in loaded:
                loaded.append(candidate)
    linked = []
    for path in loaded:
        text = path.read_text(encoding="utf-8", errors="replace")
        required = " ".join(s for s in re.split(r"(?<=[.!?])\s+|\n\s*\n", text) if REQUIRED.search(s))
        for target in re.findall(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", required):
            candidate = (path.parent / target).resolve()
            if candidate.is_file() and candidate not in loaded and candidate not in linked:
                linked.append(candidate)
    always = sum(words(p) for p in loaded)
    return always, always + sum(words(p) for p in linked), [str(p.relative_to(root)) for p in loaded
                                                             if p.is_relative_to(root)]


def tracked(root: Path) -> list[str]:
    return [p for p in git(root, "ls-files").splitlines() if p]


def unfinished(root: Path, files: list[str], product: list[str]) -> list[tuple[str, int, str]]:
    found = []
    for rel in files:
        if not CODE.search(rel) or kind(rel, product) not in ("product", "test"):
            continue
        try:
            lines = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            if UNFINISHED.search(line) and not re.search(r"UNFINISHED|re\.compile", line):
                found.append((rel, number, line.strip()[:100]))
    return found


def handoffs(root: Path, files: list[str]) -> tuple[int, int]:
    chosen = [p for p in files if HANDOFF.search(p)]
    return len(chosen), sum(words(root / p) for p in chosen if p.endswith((".md", ".txt", ".rst")))


def goal_open(root: Path) -> str | None:
    """The recorded goal, unless the finish gate's last verdict on this same goal was "met"."""
    path, status = root / ".agent" / "goal.json", root / ".agent" / "goal-status.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    goal = data.get("goal") if isinstance(data, dict) and isinstance(data.get("goal"), str) else None
    try:
        verdict = json.loads(status.read_text(encoding="utf-8"))
        if (verdict.get("goal") == goal and verdict.get("met") is True
                and status.stat().st_mtime >= path.stat().st_mtime):
            return None
    except (OSError, ValueError, AttributeError):
        pass
    return goal


def hygiene(root: Path) -> list[str]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from check_hygiene import findings  # same directory, optional
        return findings(root, None)
    except Exception:  # hygiene is advisory here; a failure must not hide the rest
        return []


def audit(root: Path, count: int) -> dict:
    cfg = config(root)
    product = [p for p in cfg.get("product", []) if isinstance(p, str)]
    commits = commit_mix(root, count, product)
    files = tracked(root)
    found = []

    goal = goal_open(root)
    if goal:
        found.append({"kind": "goal", "problem": f"open goal record: {goal!r}",
                      "action": "Finish this goal first: make each check in .agent/goal.json pass "
                                "(python3 tools/finish_check.py shows what is unmet)."})

    mix = Counter(c["kind"] for c in commits)
    if commits:
        support = mix["records"] + mix["process"]
        share = support / len(commits)
        recent_product = any(c["kind"] == "product" for c in commits[:RECENT])
        if share > SUPPORT_SHARE and not recent_product:
            examples = "; ".join(c["subject"][:60] for c in commits if c["kind"] in ("records", "process"))[:240]
            found.append({"kind": "loop",
                          "problem": f"{support}/{len(commits)} recent commits changed only records or process "
                                     f"({share:.0%}), e.g. {examples}",
                          "action": "Make the next commit change product behaviour and prove it with a check. "
                                    "Add a record only when someone will act on it; replace the old one."})
        opening = lambda c: " ".join(c["subject"].lower().split()[:3])
        openings = Counter(opening(c) for c in commits)
        latest = {opening(c) for c in commits[:RECENT]}  # history an agent cannot change is not a finding
        repeated = [(text, n) for text, n in openings.most_common(3)
                    if n >= 3 and len(text.split()) == 3 and text in latest]
        if repeated:
            found.append({"kind": "repeat",
                          "problem": "repeating commit subjects: " + ", ".join(f"'{t}' x{n}" for t, n in repeated),
                          "action": "Stop repeating the step. Name what each repeat failed to achieve and "
                                    "change the approach, or mark the item blocked with the reason."})

    gaps = unfinished(root, files, product)
    if gaps:
        top = Counter(rel for rel, _, _ in gaps).most_common(5)
        first = gaps[0]
        found.append({"kind": "unfinished",
                      "problem": f"{len(gaps)} unfinished markers in code; most in "
                                 + ", ".join(f"{rel} ({n})" for rel, n in top),
                      "action": f"Finish or delete the incomplete code, starting with {first[0]}:{first[1]} "
                                f"({first[2]}). A skipped test is unfinished work, not a pass."})

    count_handoff, handoff_words = handoffs(root, files)
    if count_handoff > 1 or handoff_words > HANDOFF_WORDS:
        found.append({"kind": "handoff",
                      "problem": f"{count_handoff} handoff/continuation files, {handoff_words} words",
                      "action": "Keep one current handoff under "
                                f"{HANDOFF_WORDS} words: goal, last proven state, next action. History is in Git."})

    always, linked, loaded = entry_reading(root)
    if always > ENTRY_WORDS or linked > LINKED_WORDS:
        found.append({"kind": "entry",
                      "problem": f"entry reading is {always} words always loaded ({', '.join(loaded)}) and "
                                 f"{linked} words with the documents it tells every agent to read",
                      "action": "Shorten the entry to the loop and the hard limits; move the rest behind "
                                "on-demand links. Delete rules that no check or trial supports."})

    for line in hygiene(root):
        found.append({"kind": "hygiene", "problem": line,
                      "action": "Clean it up: delete merged branches and finished worktrees through Git; "
                                "keep one current plan or handoff."})

    order = ["goal", "loop", "repeat", "unfinished", "handoff", "entry", "hygiene"]
    found.sort(key=lambda f: order.index(f["kind"]))
    kinds = [f["kind"] for f in found]
    if gaps and kinds[:1] in (["loop"], ["repeat"]):
        # A loop with known unfinished code: name the target, so any model can act on it.
        rel, number, text = gaps[0]
        focus = (f"This is the next task: finish {rel}:{number} ({text}) and prove it with a check, in "
                 "this session. If a records-only task blocks it, close that in one short commit, then "
                 "continue here; the records task does not end the session.")
    elif found:
        focus = found[0]["action"]
    else:
        focus = ("No waste signal found. Take the highest-priority ready task, change product behaviour, "
                 "and prove it with a check.")
    return {"root": str(root), "commits": len(commits), "mix": dict(mix), "focus": focus, "findings": found}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--commits", type=int, default=50)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="exit 1 when any finding is present")
    args = parser.parse_args(argv)
    report = audit(Path(args.root).resolve(), args.commits)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        mix = ", ".join(f"{k} {v}" for k, v in sorted(report["mix"].items())) or "no history"
        print(f"work-audit: last {report['commits']} commits: {mix}")
        print(f"FOCUS: {report['focus']}")
        for number, finding in enumerate(report["findings"], 1):
            print(f"{number}. [{finding['kind']}] {finding['problem']}\n   -> {finding['action']}")
    return 1 if args.strict and report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
