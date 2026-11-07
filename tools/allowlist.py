#!/usr/bin/env python3
"""Render the host-neutral activity allowlist into each host's native format.

configs/allowed-activities.json is the single source. Hosts enforce it, so no
pattern-matching guard has to:

  render --host claude   permissions.allow entries for .claude/settings.json
  render --host codex    execpolicy prefix_rule lines for a Codex rules file
  check                  fail if .claude/settings.json differs from the source

Codex prefix rules cannot express "exact": an exact activity renders as a
prefix and the output says so. Install Codex rules through the reviewed
native-command-bindings route; this tool only prints them.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

SOURCE = Path("configs/allowed-activities.json")
CLAUDE = Path(".claude/settings.json")


def activities(root: Path) -> list[dict]:
    return json.loads((root / SOURCE).read_text(encoding="utf-8"))["activities"]


def claude(items: list[dict]) -> list[str]:
    return [f"Bash({' '.join(a['command'])}{':*' if a['match'] == 'prefix' else ''})" for a in items]


def codex(items: list[dict]) -> str:
    lines = ["# Rendered from configs/allowed-activities.json by tools/allowlist.py; do not edit."]
    for a in items:
        note = "  # exact in the source; Codex matches it as a prefix" if a["match"] == "exact" else ""
        lines.append(f"prefix_rule(pattern={json.dumps(a['command'])}, decision=\"allow\"){note}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=("render", "check"))
    parser.add_argument("--host", choices=("claude", "codex"))
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    items = activities(root)
    if args.action == "render":
        print(json.dumps(claude(items), indent=2) if args.host == "claude" else codex(items))
        return 0
    current = json.loads((root / CLAUDE).read_text(encoding="utf-8")).get("permissions", {}).get("allow", [])
    if current != claude(items):
        print(f"allowlist: FAIL: {CLAUDE} permissions.allow differs from {SOURCE}; "
              f"run: python3 tools/allowlist.py render --host claude", file=sys.stderr)
        return 1
    print(f"allowlist: {len(items)} activities; Claude adapter matches the source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
