#!/usr/bin/env python3
"""Report repository state that agents leave behind instead of cleaning up.

- merged branches that were never deleted (local branches fully merged into BASE)
- extra worktrees still registered
- dated plan, review, handoff or status trees (one current handoff is enough;
  history lives in Git)
- tracked scratch, cache or log files

Read-only: it never deletes. With --strict, findings exit 1 so the check can
be a finish-gate item or CI step.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

DATED = re.compile(r"(19|20)\d{2}-?\d{2}-?\d{2}")
PROCESS_WORDS = re.compile(r"(^|[/_.-])(plans?|reviews?|handoffs?|status|retros?)([/_.-]|$)", re.I)
SCRATCH = re.compile(r"(^|/)(\.tmp|tmp|\.cache|\.agent-cache|node_modules|__pycache__)/|\.log$")


def git(root: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def findings(root: Path, base: str) -> list[str]:
    found = []
    current = git(root, "rev-parse", "--abbrev-ref", "HEAD")[0]
    for branch in git(root, "branch", "--format=%(refname:short)", "--merged", base):
        if branch not in (base, current) and not base.endswith("/" + branch):
            found.append(f"merged branch not deleted: {branch} (git branch -d {branch})")
    worktrees = [line.split(" ", 1)[1] for line in git(root, "worktree", "list", "--porcelain")
                 if line.startswith("worktree ")]
    for extra in worktrees[1:]:
        found.append(f"extra worktree still registered: {extra} (harvest, then git worktree remove)")
    for path in git(root, "ls-files"):
        if DATED.search(path) and PROCESS_WORDS.search(path):
            found.append(f"dated process record: {path} (keep one current handoff; history is in Git)")
        elif SCRATCH.search(path):
            found.append(f"tracked scratch or cache: {path}")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", default="main")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    found = findings(Path(args.root).resolve(), args.base)
    for line in found:
        print(f"hygiene: {line}")
    if not found:
        print("hygiene: clean")
    return 1 if found and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
