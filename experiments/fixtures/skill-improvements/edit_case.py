#!/usr/bin/env python3
"""Set up and independently check a small Python edit with a known test command."""

import argparse
import importlib.util
import json
from pathlib import Path
import sys


def setup(seed, run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    alias = f"soft-{seed % 11}"
    (run_dir / "status_map.py").write_text(
        '"""Normalize statuses received from small text feeds."""\n\n'
        f'ALIASES = {{"ok": "ready", "{alias}": "warning", "failed": "error"}}\n\n'
        'def canonical_status(value):\n'
        '    """Return a canonical status, or unknown for unsupported input."""\n'
        '    if not isinstance(value, str):\n'
        '        return "unknown"\n'
        '    return ALIASES.get(value.lower(), "unknown")\n',
        encoding="utf-8",
    )
    (run_dir / "test_status_map.py").write_text(
        'import unittest\nfrom status_map import canonical_status\n\n'
        'class StatusTests(unittest.TestCase):\n'
        '    def test_trimmed_case_insensitive_input(self):\n'
        '        self.assertEqual(canonical_status("  OK  "), "ready")\n'
        f'        self.assertEqual(canonical_status("  {alias.upper()}  "), "warning")\n'
        '    def test_unknown(self):\n'
        '        self.assertEqual(canonical_status("missing"), "unknown")\n',
        encoding="utf-8",
    )
    (run_dir / "task.txt").write_text(
        "Fix canonical_status so it ignores leading/trailing whitespace and casing "
        "when matching the existing ALIASES. Non-string and unmapped values return "
        '"unknown". Run `python3 -m unittest -q` from this directory.\n',
        encoding="utf-8",
    )
    print(json.dumps({"run_dir": str(run_dir), "task": str(run_dir / "task.txt"), "validation": "python3 -m unittest -q"}))


def check(seed, run_dir):
    source = run_dir / "status_map.py"
    spec = importlib.util.spec_from_file_location("trial_status_map", source)
    if spec is None or spec.loader is None:
        raise ValueError("status_map.py is missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    alias = f"soft-{seed % 11}"
    cases = [
        ("OK", "ready"), ("  oK\t", "ready"),
        (f"\t{alias.upper()}  ", "warning"), (" Failed ", "error"),
        ("none", "unknown"), ("   ", "unknown"), (None, "unknown"), (17, "unknown"),
    ]
    for value, expected in cases:
        if module.canonical_status(value) != expected:
            raise ValueError(f"incorrect result for {value!r}")
    print(json.dumps({"accepted": True, "seed": seed, "checks": len(cases)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "check"))
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "setup":
        setup(args.seed, args.run_dir)
    else:
        try:
            check(args.seed, args.run_dir)
        except (OSError, ValueError, AttributeError) as error:
            parser.exit(2, f"edit case: {error}\n")


if __name__ == "__main__":
    main()
