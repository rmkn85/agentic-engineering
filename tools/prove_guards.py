#!/usr/bin/env python3
"""Prove that tests guard the rules they claim to guard.

Each validation/mutations/*.json disables one rule in a disposable copy of the
repository (an exact text replacement) and names the tests that must then
fail. If those tests still pass, they do not protect the rule; if the
replacement text is missing, the mutation is stale; if the tests fail even
without the mutation, or the mutated code does not compile, or the tests only
error instead of failing an assertion, the proof is broken. Any of these fails
the proof.

    {"id": "short-name", "rule": "what must hold", "file": "tools/x.py",
     "find": "exact text", "replace": "text that disables the rule",
     "tests": ["tools.tests.test_x.Class.test_name"]}

Usage: python3 tools/prove_guards.py [--only ID ...] [--root DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def load(root: Path) -> list[dict]:
    mutations = []
    for path in sorted((root / "validation" / "mutations").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("id", "rule", "file", "find", "replace", "tests"):
            if key not in data:
                raise ValueError(f"{path.name}: missing {key}")
        if not isinstance(data["tests"], list) or not data["tests"]:
            raise ValueError(f"{path.name}: tests must be a non-empty list")
        mutations.append(data)
    return mutations


def copy_tracked(root: Path, destination: Path) -> None:
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    for rel in files:
        source = root / rel
        if source.is_file():
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def prove(root: Path, mutation: dict, timeout: int) -> tuple[str, str]:
    with tempfile.TemporaryDirectory(prefix="prove-") as temp:
        copy = Path(temp)
        copy_tracked(root, copy)
        run = [sys.executable, "-m", "unittest", *mutation["tests"]]
        try:
            baseline = subprocess.run(run, cwd=copy, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return "broken", "tests time out even without the mutation"
        if baseline.returncode != 0:
            lines = (baseline.stderr or baseline.stdout).strip().splitlines()
            return "broken", "tests fail without the mutation: " + (lines[-1] if lines else "no output")
        target = copy / mutation["file"]
        text = target.read_text(encoding="utf-8") if target.exists() else ""
        count = text.count(mutation["find"])
        if count != 1:
            return "stale", f"find text occurs {count} times in {mutation['file']}"
        target.write_text(text.replace(mutation["find"], mutation["replace"]), encoding="utf-8")
        if target.suffix == ".py":
            compiled = subprocess.run([sys.executable, "-m", "py_compile", str(target)], capture_output=True, text=True)
            if compiled.returncode != 0:
                return "broken", "the mutation breaks the code instead of disabling the rule"
        try:
            result = subprocess.run(run, cwd=copy, capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            return "caught", "tests timed out under the mutation"
        if result.returncode == 0:
            return "survived", "tests still pass with the rule disabled"
        if not re.search(r"^FAIL: ", result.stderr, re.M):
            return "broken", "tests only errored; a catch needs an assertion to fail on the disabled rule"
        return "caught", "tests pass as written and fail with the rule disabled"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--only", nargs="*", default=None)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    mutations = [m for m in load(root) if args.only is None or m["id"] in args.only]
    bad = 0
    for mutation in mutations:
        outcome, detail = prove(root, mutation, args.timeout)
        bad += outcome != "caught"
        print(f"prove: {outcome:8} {mutation['id']}: {detail}")
    print(f"prove: {len(mutations) - bad}/{len(mutations)} rules guarded by tests that fail without them")
    return 1 if bad or not mutations else 0


if __name__ == "__main__":
    raise SystemExit(main())
