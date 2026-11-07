#!/usr/bin/env python3
"""Run blind reviews the same way every time, and keep what they find.

A blind reviewer is a fresh agent that gets only the goal, never the author's
reasoning, and tries to break the change. Two steps:

  prompt  print the reviewer prompt, built from the change's goal record
          (.agent/goal.json) plus repository, branch and base. Give it to a
          fresh agent session with no prior context (any host).
  ingest  read the reviewer's report, extract its FINDINGS block, and append
          each finding to validation/findings.jsonl as open, with a new id.

The report's FINDINGS block is JSON lines between the markers below, one
object per finding with severity, target, problem and reproduction.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

START, END = "BEGIN FINDINGS", "END FINDINGS"
SEVERITIES = {"blocker", "should-fix", "minor"}

PROMPT = """You are an independent reviewer. You have NOT seen how this change was made; judge it only against the goal.

Repository: {repo}. Branch under review: {branch}. Base: {base}.
Clone into a NEW directory of your own: git clone -q {repo} {workdir} && cd {workdir} && git checkout -q {branch}
Do not read or modify any other working directory, and do NOT read the pull request description or commit messages:
they carry the author's reasoning. Judge the diff (git diff origin/{base}...HEAD) and the behaviour.

GOAL: {goal}

The change claims these checks prove the goal:
{checks}

Run the project's own checks, then try hard to break each claim with real experiments: bypasses, malformed input,
false positives on everyday use, concurrency, anything the checks do not cover. Run them; do not speculate.
Do not fix or push anything. Pass dangerous commands you test only as data (for example from a Python
list) to the tool under test, never through a shell that could execute them.

Report, most severe first, under 800 words. End with one line per claim: met / partly met / not met, and why.
Then list every finding as JSON lines between these exact markers:
{start}
{{"severity": "blocker|should-fix|minor", "target": "path:line", "problem": "one sentence", "reproduction": "command run and its output"}}
{end}
Write an empty block if you found nothing."""


def checks_text(goal: dict) -> str:
    lines = []
    for item in goal.get("acceptance", []):
        how = f"(make {item['run']})" if item.get("run") else "(manual)"
        lines.append(f"- {item.get('check', '')} {how}")
    return "\n".join(lines) or "- (none declared)"


def render(goal: dict, repo: str, branch: str, base: str, workdir: str) -> str:
    return PROMPT.format(repo=repo, branch=branch, base=base, workdir=workdir, goal=goal.get("goal", ""),
                         checks=checks_text(goal), start=START, end=END)


def parse(report: str) -> list[dict]:
    match = re.search(re.escape(START) + r"(.*?)" + re.escape(END), report, re.S)
    if not match:
        raise ValueError(f"report has no {START} ... {END} block")
    findings = []
    for line in match.group(1).splitlines():
        line = line.strip().strip("`")
        if not line or line.startswith("{\"severity\": \"blocker|"):
            continue
        row = json.loads(line)
        if row.get("severity") not in SEVERITIES or not all(
                isinstance(row.get(k), str) and row[k].strip() for k in ("target", "problem", "reproduction")):
            raise ValueError(f"finding is incomplete: {line[:120]}")
        findings.append(row)
    return findings


def ingest(root: Path, report: str, review: str) -> list[str]:
    ledger = root / "validation" / "findings.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    existing = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if ledger.exists() else []
    prefix = "R" + re.sub(r"\D", "", review)[-3:] if re.search(r"\d", review) else "R"
    taken = {row["id"] for row in existing}
    added = []
    with ledger.open("a", encoding="utf-8") as out:
        for number, finding in enumerate(parse(report), 1):
            ident = f"{prefix}-{number:02d}"
            while ident in taken:
                number += 100
                ident = f"{prefix}-{number:02d}"
            taken.add(ident)
            row = {"id": ident, "review": review, "date": date.today().isoformat(), **{
                k: finding[k] for k in ("severity", "target", "problem", "reproduction")}, "status": "open", "tests": []}
            out.write(json.dumps(row) + "\n")
            added.append(ident)
    return added


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("--goal", default=".agent/goal.json")
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--base", default="main")
    p.add_argument("--workdir", default="/tmp/blind-review")
    i = sub.add_parser("ingest")
    i.add_argument("report", help="file with the reviewer's report, or - for stdin")
    i.add_argument("--review", required=True, help="name of this review, e.g. blind-review-3")
    i.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    if args.command == "prompt":
        goal = json.loads(Path(args.goal).read_text(encoding="utf-8"))
        print(render(goal, args.repo, args.branch, args.base, args.workdir))
        return 0
    report = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
    try:
        added = ingest(Path(args.root).resolve(), report, args.review)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"blind-review: {exc}", file=sys.stderr)
        return 1
    print(f"blind-review: {len(added)} findings added as open: {', '.join(added) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
