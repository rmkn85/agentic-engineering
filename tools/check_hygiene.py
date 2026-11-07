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
PROCESS_WORD = r"(plans?|reviews?|handoffs?|status|retros?)"
SCRATCH = re.compile(r"(^|/)(\.tmp|tmp|\.cache|\.agent-cache|node_modules|__pycache__)/|\.log$")
KEEP_FILES = {".keep", ".gitkeep"}


def process_record(path: str) -> bool:
    """A dated file in a plans/reviews/handoffs/status directory, or named after one."""
    *dirs, name = path.split("/")
    in_process_dir = any(re.fullmatch(PROCESS_WORD, d, re.I) for d in dirs)
    named = re.match(PROCESS_WORD + r"[-_.]", name, re.I)
    return bool(DATED.search(path) and (in_process_dir or named))


def scratch(path: str) -> bool:
    parts = path.split("/")
    if parts[-1] in KEEP_FILES or "fixtures" in parts:
        return False
    return bool(SCRATCH.search(path))


def default_base(root: Path) -> str | None:
    for ref in ("refs/remotes/origin/HEAD",):
        try:
            return git(root, "symbolic-ref", "--short", ref)[0]
        except subprocess.CalledProcessError:
            pass
    for name in ("main", "master", "trunk"):
        if exists(root, name):
            return name
    return None


def exists(root: Path, ref: str) -> bool:
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], cwd=root,
                          capture_output=True).returncode == 0


def git(root: Path, *args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout
    return [line for line in out.splitlines() if line.strip()]


def findings(root: Path, base: str | None) -> list[str]:
    found = []
    base = base or default_base(root)
    if base and not exists(root, base):
        found.append(f"base {base} does not exist; branch check skipped (pass --base)")
        base = None
    if base:
        current = git(root, "rev-parse", "--abbrev-ref", "HEAD")[0]
        base_tip = git(root, "rev-parse", base)[0]
        for line in git(root, "branch", "--format=%(refname:short) %(objectname)", "--merged", base):
            branch, tip = line.rsplit(" ", 1)
            if branch in (base, current) or base.endswith("/" + branch) or tip == base_tip:
                continue  # trunk itself, or a branch not yet started
            found.append(f"merged branch not deleted: {branch} (git branch -d {branch})")
    worktrees = [line.split(" ", 1)[1] for line in git(root, "worktree", "list", "--porcelain")
                 if line.startswith("worktree ")]
    for extra in worktrees[1:]:
        found.append(f"extra worktree still registered: {extra} (harvest, then git worktree remove)")
    for path in git(root, "ls-files"):
        if process_record(path):
            found.append(f"dated process record: {path} (keep one current handoff; history is in Git)")
        elif scratch(path):
            found.append(f"tracked scratch or cache: {path}")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", help="trunk to compare branches with (default: origin HEAD, main, master)")
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
