#!/usr/bin/env python3
"""Inventory common file-based agent instructions without loading them into an LLM.

This is deliberately a lower-bound proxy. A real harness may also inject system
prompts, memories, skill metadata, tool/MCP schemas, output styles, and other
runtime context. Prefer the harness's native context inspector when available.
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


IGNORED_DIRS = {
    ".git",
    ".agent-bench",
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}


@dataclass(frozen=True)
class Entry:
    path: str
    kind: str
    residency: str
    bytes: int
    lines: int
    words: int
    approx_tokens: int


def classify(path: Path, root: Path) -> tuple[str, str] | None:
    rel = path.relative_to(root)
    name = path.name
    parts = rel.parts
    rel_posix = rel.as_posix()

    if name == "AGENTS.md":
        return "agent-instructions", "scope/harness-dependent"
    if name in {"CLAUDE.md", "GEMINI.md"}:
        return "agent-instructions", "usually-always-loaded-in-scope"
    if rel_posix == ".github/copilot-instructions.md":
        return "copilot-repo-instructions", "always-loaded-in-repo-scope"
    if len(parts) >= 3 and parts[0:2] == (".github", "instructions") and name.endswith(".instructions.md"):
        return "copilot-path-instructions", "path-scoped-capable"
    if ".cursor" in parts and "rules" in parts and path.suffix == ".mdc":
        return "cursor-rule", "rule-metadata-dependent"
    if ".claude" in parts and "rules" in parts and path.suffix in {".md", ".mdc"}:
        return "claude-rule", "path-scoped-capable"
    if name == "SKILL.md":
        return "skill-body", "on-demand-capable"
    return None


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        if classify(path, root) is not None:
            yield path


def inspect(path: Path, root: Path) -> Entry:
    kind, residency = classify(path, root) or ("unknown", "unknown")
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    # Character/4 is only a stable dependency-free comparison proxy. It is not
    # tokenizer-accurate and must not be reported as actual model usage.
    approx_tokens = math.ceil(len(text) / 4)
    return Entry(
        path=path.relative_to(root).as_posix(),
        kind=kind,
        residency=residency,
        bytes=len(raw),
        lines=len(text.splitlines()),
        words=len(text.split()),
        approx_tokens=approx_tokens,
    )


def totals(entries: list[Entry]) -> dict[str, object]:
    by_residency: dict[str, dict[str, int]] = {}
    for entry in entries:
        bucket = by_residency.setdefault(
            entry.residency,
            {"files": 0, "bytes": 0, "lines": 0, "words": 0, "approx_tokens": 0},
        )
        bucket["files"] += 1
        bucket["bytes"] += entry.bytes
        bucket["lines"] += entry.lines
        bucket["words"] += entry.words
        bucket["approx_tokens"] += entry.approx_tokens
    return {
        "files": len(entries),
        "bytes": sum(e.bytes for e in entries),
        "lines": sum(e.lines for e in entries),
        "words": sum(e.words for e in entries),
        "approx_tokens": sum(e.approx_tokens for e in entries),
        "by_residency": by_residency,
    }


def print_table(entries: list[Entry]) -> None:
    if not entries:
        print("No recognized instruction files found.")
        return
    headers = ("Path", "Kind", "Residency", "Lines", "Words", "~Tokens")
    rows = [
        (
            e.path,
            e.kind,
            e.residency,
            str(e.lines),
            str(e.words),
            str(e.approx_tokens),
        )
        for e in entries
    ]
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    print("  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        print("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory common file-based agent instruction/context sources."
    )
    parser.add_argument("root", nargs="?", default=".", help="repository root")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    entries = sorted((inspect(path, root) for path in iter_files(root)), key=lambda e: e.path)
    result = {
        "schema": 1,
        "root": str(root),
        "warning": (
            "Lower-bound file inventory only; runtime/system/tool context is not visible here. "
            "approx_tokens is characters/4, not tokenizer usage."
        ),
        "entries": [asdict(e) for e in entries],
        "totals": totals(entries),
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_table(entries)
        t = result["totals"]
        print()
        print(
            f"Recognized: {t['files']} files, {t['lines']} lines, {t['words']} words, "
            f"~{t['approx_tokens']} proxy tokens"
        )
        print(result["warning"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
