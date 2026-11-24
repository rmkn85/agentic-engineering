#!/usr/bin/env python3
"""Detect drifted reusable workflow refs and mismatched input pins across repositories."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

SKIP_DIRS = frozenset(("node_modules", "vendor", "dist", "build", "__pycache__"))
USES_RE = re.compile(
    r"^(\s*)(?:-\s*)?uses:\s*['\"]?"
    r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/\.github/workflows/[^@\s'\"]+)@([^\s'\"#]+)"
    r"['\"]?\s*$"
)
WITH_RE = re.compile(r"^(\s*)with:\s*$")
KV_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*:\s*['\"]?([^\s'\"#]+)['\"]?\s*$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")


def strip_comment(line: str) -> str:
    """Remove an unquoted YAML # comment from a single line."""
    quote = ""
    escaped = False
    for idx, ch in enumerate(line):
        if escaped:
            escaped = False
            continue
        if quote == '"' and ch == "\\":
            escaped = True
            continue
        if quote:
            if ch == quote:
                quote = ""
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "#" and (idx == 0 or line[idx - 1].isspace()):
            return line[:idx].rstrip()
    return line.rstrip("\r\n")


def discover_repos(paths: list[str], discover: bool) -> list[Path]:
    """Return sorted unique repository roots containing .github/workflows."""
    found: dict[Path, None] = {}
    for raw in paths:
        target = Path(raw).resolve()
        if not target.exists():
            raise FileNotFoundError(f"path does not exist: {raw}")
        has_workflows = (target / ".github" / "workflows").is_dir()
        if has_workflows:
            found[target] = None
        if discover or not has_workflows:
            for child in sorted(target.iterdir()) if target.is_dir() else ():
                if not child.is_dir() or child.name.startswith(".") or child.name in SKIP_DIRS:
                    continue
                if (child / ".github" / "workflows").is_dir():
                    found[child] = None
    return list(found)


def parse_workflow_file(repo: Path, wf_path: Path, input_keys: set[str]) -> list[dict]:
    """Extract reusable workflow calls and tracked with-inputs from one workflow file."""
    rel = wf_path.relative_to(repo).as_posix()
    lines = wf_path.read_text(encoding="utf-8", errors="replace").splitlines()
    refs: list[dict] = []
    idx = 0
    while idx < len(lines):
        cleaned = strip_comment(lines[idx])
        match = USES_RE.match(cleaned)
        if not match:
            idx += 1
            continue
        entry, idx = _consume_call_block(repo.name, rel, lines, idx, match, input_keys)
        refs.append(entry)
    return refs


def _consume_call_block(
    repo_name: str,
    rel: str,
    lines: list[str],
    start_idx: int,
    match: re.Match[str],
    input_keys: set[str],
) -> tuple[dict, int]:
    """Read any subsequent with: block at the same job level after a uses: line."""
    uses_indent = len(match.group(1))
    inputs: dict[str, str] = {}
    in_with = False
    with_indent = -1
    idx = start_idx + 1
    while idx < len(lines):
        cleaned = strip_comment(lines[idx])
        if not cleaned.strip():
            idx += 1
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        if indent < uses_indent or (indent == uses_indent and USES_RE.match(cleaned)):
            break
        if in_with:
            if indent <= with_indent:
                in_with = False
            else:
                kv = KV_RE.match(cleaned)
                if kv and kv.group(1) in input_keys:
                    inputs[kv.group(1)] = kv.group(2)
                idx += 1
                continue
        with_match = WITH_RE.match(cleaned)
        if with_match and indent == uses_indent:
            in_with = True
            with_indent = indent
        idx += 1
    entry = {
        "repo": repo_name,
        "file": rel,
        "line": start_idx + 1,
        "workflow": match.group(2),
        "ref": match.group(3),
        "inputs": inputs,
    }
    return entry, idx


def caller_label(entry: dict) -> str:
    return f"{entry['repo']}:{entry['file']}:{entry['line']}"


def sha_compatible(left: str, right: str) -> bool:
    a, b = left.lower(), right.lower()
    return a.startswith(b) or b.startswith(a)


def check_references(
    refs: list[dict],
    expected_refs: list[tuple[str, str]],
    match_ref: bool,
) -> list[dict]:
    """Evaluate drift, ref/input mismatch, and expected-ref policy findings."""
    findings: list[dict] = []
    by_wf_ref: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    by_wf_input: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    for entry in refs:
        wf, ref, caller = entry["workflow"], entry["ref"], caller_label(entry)
        by_wf_ref[wf][ref].append(caller)
        for key, val in entry["inputs"].items():
            if val:
                by_wf_input[(wf, key)][val].append(caller)
                both_sha = bool(SHA_RE.match(ref) and SHA_RE.match(val))
                mismatch = (not sha_compatible(ref, val)) if both_sha else (match_ref and val != ref)
                if mismatch:
                    findings.append({
                        "kind": "ref-input-mismatch",
                        "workflow": wf,
                        "caller": caller,
                        "message": f"{caller} calls {wf}@{ref} with {key}={val}",
                    })
        for pattern, expected in expected_refs:
            if (wf == pattern or wf.endswith("/" + pattern) or wf.endswith(pattern)) and ref != expected:
                findings.append({
                    "kind": "expected-ref-mismatch",
                    "workflow": wf,
                    "caller": caller,
                    "message": f"{caller} calls {wf}@{ref} (expected @{expected})",
                })

    for wf, ref_map in sorted(by_wf_ref.items()):
        if len(ref_map) > 1:
            detail = ", ".join(f"@{r} ({len(c)}: {', '.join(c)})" for r, c in sorted(ref_map.items()))
            findings.append({
                "kind": "workflow-ref-drift",
                "workflow": wf,
                "message": f"{wf} uses {len(ref_map)} refs: {detail}",
            })

    for (wf, key), val_map in sorted(by_wf_input.items()):
        if len(val_map) > 1:
            detail = ", ".join(f"{v} ({len(c)}: {', '.join(c)})" for v, c in sorted(val_map.items()))
            findings.append({
                "kind": "input-pin-drift",
                "workflow": wf,
                "key": key,
                "message": f"{wf} input '{key}' has {len(val_map)} values: {detail}",
            })
    return findings


def parse_expected(raw_items: list[str]) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for item in raw_items:
        wf, sep, ref = item.partition("=")
        if not sep or not wf or not ref:
            raise ValueError(f"--expected-ref must be WORKFLOW=REF, got: {item!r}")
        parsed.append((wf, ref))
    return parsed


def scan_paths(
    paths: list[str],
    discover: bool,
    input_keys: list[str],
    expected_refs: list[tuple[str, str]],
    match_ref: bool,
) -> dict:
    """Discover repositories, parse workflow calls, and compute drift findings."""
    repos = discover_repos(paths, discover)
    refs: list[dict] = []
    tracked = set(input_keys)
    for repo in repos:
        wf_dir = repo / ".github" / "workflows"
        for wf_file in sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))):
            refs.extend(parse_workflow_file(repo, wf_file, tracked))
    findings = check_references(refs, expected_refs, match_ref)
    return {
        "repos_scanned": [r.name for r in repos],
        "references": refs,
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["."], help="Repository or parent directories to scan.")
    parser.add_argument("--discover", action="store_true", help="Scan immediate child directories as repositories.")
    parser.add_argument("--input-key", action="append", dest="input_keys", default=[],
                        help="Reusable workflow input key to track (default: tooling_revision).")
    parser.add_argument("--expected-ref", action="append", default=[],
                        help="Require callers of WORKFLOW (full name or suffix) to use REF (WORKFLOW=REF).")
    parser.add_argument("--match-ref", action="store_true",
                        help="Require tracked input values to match the workflow @ref.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Emit JSON output.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any finding is reported.")
    args = parser.parse_args(argv)

    input_keys = args.input_keys or ["tooling_revision"]
    try:
        expected_refs = parse_expected(args.expected_ref)
        report = scan_paths(args.paths, args.discover, input_keys, expected_refs, args.match_ref)
    except (OSError, ValueError) as exc:
        print(f"check-workflow-pins: error: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report, indent=2))
    elif not report["findings"]:
        print(
            f"check-workflow-pins: clean ({len(report['repos_scanned'])} repos, "
            f"{len(report['references'])} reusable workflow calls)"
        )
    else:
        for item in report["findings"]:
            print(f"[{item['kind']}] {item['message']}")
    return 1 if (args.strict and report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
