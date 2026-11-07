#!/usr/bin/env python3
"""Keep runtime guidance from growing as unenforced prose.

Two checks, configured in configs/guidance-budget.json:

1. Default reading (files loaded on every task) stays within max_words.
   Lower the number when the text shrinks; never raise it to fit new prose.
2. With --base REF: if runtime guidance gained words since REF, the same change
   must touch a mechanism path (tool, test, schema, config, hook, trial result).
   Otherwise the added rule has nothing that enforces or measures it.

Words are whitespace-separated tokens of the Markdown source.
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
    return subprocess.run(["git", *args], cwd=root, check=True,
                          capture_output=True, text=True).stdout


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def default_reading(root: Path, config: dict) -> tuple[int, int]:
    total = sum(words((root / f).read_text(encoding="utf-8")) for f in config["default_reading"]["files"])
    return total, config["default_reading"]["max_words"]


def runtime_words(root: Path, config: dict, ref: str | None) -> int:
    if ref is None:
        files = git(root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
        return sum(words((root / f).read_text(encoding="utf-8"))
                   for f in files if matches(f, config["runtime"]) and (root / f).exists())
    files = git(root, "ls-tree", "-r", "--name-only", ref).splitlines()
    return sum(words(git(root, "show", f"{ref}:{f}")) for f in files if matches(f, config["runtime"]))


def changed_paths(root: Path, base: str) -> list[str]:
    tracked = git(root, "diff", "--name-only", base, "--").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked) | set(untracked))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", help="git ref to compare runtime guidance against")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    failures = []

    used, limit = default_reading(root, config)
    if used > limit:
        failures.append(f"default reading is {used} words, budget {limit}: cut text or move it on demand")
    else:
        print(f"guidance-budget: default reading {used}/{limit} words")

    if args.base:
        before = runtime_words(root, config, args.base)
        after = runtime_words(root, config, None)
        paths = changed_paths(root, args.base)
        mechanisms = [p for p in paths if matches(p, config["mechanism"])]
        if after > before and not mechanisms:
            failures.append(
                f"runtime guidance grew by {after - before} words since {args.base} with no change to a "
                "mechanism path; enforce the rule with a tool, test or hook, attach a trial result, or delete "
                "an equal amount of text")
        else:
            print(f"guidance-budget: runtime guidance {before} -> {after} words; "
                  f"mechanism paths changed: {len(mechanisms)}")

    for failure in failures:
        print(f"guidance-budget: FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
