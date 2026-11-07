#!/usr/bin/env python3
"""Keep runtime guidance from growing as unenforced prose.

Configured in configs/guidance-budget.json:

1. Default reading (files every agent loads on every task, for any host)
   stays within max_words. Lower the number when text shrinks.
2. With --base REF:
   - max_words may not rise above its value at REF;
   - if runtime guidance gained words since REF, the same change must touch an
     evidence path: a test or a trial result. Editing the budget, a config or
     an empty tool does not count. Otherwise the added rule has nothing that
     checks it.

Runtime guidance includes instruction files read by any agent host (AGENTS.md,
CLAUDE.md, GEMINI.md, Copilot and Cursor rules, .claude/**/*.md) plus docs,
skills and templates. Path matching ignores case. Words are whitespace tokens.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

CONFIG = Path("configs/guidance-budget.json")


def words(text: str) -> int:
    return len(text.split())


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def matches(path: str, patterns: list[str]) -> bool:
    lowered = path.lower()
    return any(fnmatch.fnmatch(lowered, p.lower()) for p in patterns)


def default_reading(root: Path, config: dict) -> int:
    return sum(words((root / f).read_text(encoding="utf-8"))
               for f in config["default_reading"]["files"] if (root / f).exists())


def runtime_words(root: Path, config: dict, ref: str | None) -> int:
    if ref is None:
        files = git(root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
        return sum(words((root / f).read_text(encoding="utf-8", errors="replace"))
                   for f in files if matches(f, config["runtime"]) and (root / f).is_file())
    files = git(root, "ls-tree", "-r", "--name-only", ref).splitlines()
    return sum(words(git(root, "show", f"{ref}:{f}")) for f in files if matches(f, config["runtime"]))


def changed_paths(root: Path, base: str) -> list[str]:
    tracked = git(root, "diff", "--name-only", base, "--").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked) | set(untracked))


def base_budget(root: Path, base: str) -> int | None:
    try:
        return json.loads(git(root, "show", f"{base}:{CONFIG.as_posix()}"))["default_reading"]["max_words"]
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", help="git ref to compare against")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    limit = config["default_reading"]["max_words"]
    failures = []

    used = default_reading(root, config)
    if used > limit:
        failures.append(f"default reading is {used} words, budget {limit}: cut text or move it on demand")
    else:
        print(f"guidance-budget: default reading {used}/{limit} words")

    if args.base:
        previous = base_budget(root, args.base)
        if previous is not None and limit > previous:
            failures.append(f"budget raised from {previous} to {limit} words; budgets only go down")
        before = runtime_words(root, config, args.base)
        after = runtime_words(root, config, None)
        evidence = [p for p in changed_paths(root, args.base) if matches(p, config["evidence"])]
        if after > before and not evidence:
            failures.append(
                f"runtime guidance grew by {after - before} words since {args.base} without a changed test or "
                "trial result; add the check that fails without the rule, attach a trial, or delete an equal "
                "amount of text")
        else:
            print(f"guidance-budget: runtime guidance {before} -> {after} words; evidence paths changed: "
                  f"{len(evidence)}")

    for failure in failures:
        print(f"guidance-budget: FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
