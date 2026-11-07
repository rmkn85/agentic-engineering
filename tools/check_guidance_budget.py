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
skills and templates, and any file pulled in by an @path import from a
default-reading file. Path matching ignores case. Words are whitespace tokens.

Against a base, the config cannot be loosened: default-reading files and
runtime patterns are the union of base and current, evidence patterns their
intersection. Evidence must contain a test function or assertion (or, for
trial results, non-empty data); blank lines and empty files do not count.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
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


IMPORT = re.compile(r"(?:^|\s)@([A-Za-z0-9_./-]+)")


def reader(root: Path, ref: str | None):
    def read(rel: str) -> str | None:
        if ref is None:
            path = root / rel
            return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None
        result = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=root, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else None
    return read


def with_imports(read, files: list[str]) -> dict[str, str]:
    """Default-reading files plus everything they @import (outside code spans), recursively."""
    loaded, queue = {}, list(files)
    while queue:
        rel = posixpath.normpath(queue.pop(0))
        if rel in loaded or rel.startswith("..") or len(loaded) > 50:
            continue
        text = read(rel)
        if text is None:
            continue
        loaded[rel] = text
        plain = re.sub(r"`[^`]*`", "", re.sub(r"```.*?```", "", text, flags=re.S))
        for target in IMPORT.findall(plain):
            queue.append(posixpath.join(posixpath.dirname(rel), target))
    return loaded


def default_reading(root: Path, config: dict) -> int:
    return sum(words(text) for text in with_imports(reader(root, None), config["default_reading"]["files"]).values())


def runtime_words(root: Path, config: dict, ref: str | None) -> int:
    if ref is None:
        files = git(root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    else:
        files = git(root, "ls-tree", "-r", "--name-only", ref).splitlines()
    read = reader(root, ref)
    texts = {f: read(f) for f in files if matches(f, config["runtime"])}
    texts.update(with_imports(read, config["default_reading"]["files"]))
    return sum(words(t) for t in texts.values() if t is not None)


def effective(current: dict, base: dict | None) -> dict:
    if not base:
        return current
    merged = json.loads(json.dumps(current))
    merged["default_reading"]["files"] = sorted(set(current["default_reading"]["files"]) |
                                                set(base["default_reading"]["files"]))
    merged["runtime"] = sorted(set(current["runtime"]) | set(base["runtime"]))
    merged["evidence"] = sorted(set(current["evidence"]) & set(base["evidence"]))
    return merged


TEST_LINE = re.compile(r"^\s*(def test|async def test|assert\b|self\.assert)")


def substantive(root: Path, base: str, path: str) -> bool:
    """True when the change adds a test function or assertion, or non-empty trial data."""
    tracked = subprocess.run(["git", "cat-file", "-e", f"HEAD:{path}"], cwd=root, capture_output=True).returncode == 0 \
        or subprocess.run(["git", "ls-files", "--error-unmatch", path], cwd=root, capture_output=True).returncode == 0
    if tracked:
        added = [line[1:] for line in git(root, "diff", "--unified=0", base, "--", path).splitlines()
                 if line.startswith("+") and not line.startswith("+++")]
    else:
        file = root / path
        added = file.read_text(encoding="utf-8", errors="replace").splitlines() if file.is_file() else []
    if path.endswith(".py"):
        return any(TEST_LINE.match(line) for line in added)
    if path.endswith((".json", ".jsonl")):  # trial results and fixtures: real data, not notes
        text = "\n".join(added).strip()
        try:
            values = [json.loads(text)] if path.endswith(".json") else [json.loads(l) for l in added if l.strip()]
        except ValueError:
            return False
        return any(v not in ({}, [], None, "") for v in values)
    return False


def changed_paths(root: Path, base: str) -> list[str]:
    tracked = git(root, "diff", "--name-only", base, "--").splitlines()
    untracked = git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    return sorted(set(tracked) | set(untracked))


def base_config(root: Path, base: str) -> dict | None:
    try:
        data = json.loads(git(root, "show", f"{base}:{CONFIG.as_posix()}"))
        data["default_reading"]["max_words"]
        data.setdefault("evidence", data.get("mechanism", []))
        return data
    except (subprocess.CalledProcessError, ValueError, KeyError, TypeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--base", help="git ref to compare against")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    config = json.loads((root / CONFIG).read_text(encoding="utf-8"))
    base = base_config(root, args.base) if args.base else None
    limit = config["default_reading"]["max_words"]
    config = effective(config, base)
    failures = []

    used = default_reading(root, config)
    if used > limit:
        failures.append(f"default reading is {used} words, budget {limit}: cut text or move it on demand")
    else:
        print(f"guidance-budget: default reading {used}/{limit} words")

    if args.base:
        previous = base["default_reading"]["max_words"] if base else None
        if previous is not None and limit > previous:
            failures.append(f"budget raised from {previous} to {limit} words; budgets only go down")
        before = runtime_words(root, config, args.base)
        after = runtime_words(root, config, None)
        evidence = [p for p in changed_paths(root, args.base)
                    if matches(p, config["evidence"]) and substantive(root, args.base, p)]
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
