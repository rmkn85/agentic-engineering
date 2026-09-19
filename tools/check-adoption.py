#!/usr/bin/env python3
"""Validate a local engineering snapshot, offline; no upstream dependency."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess


def local_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError("invalid adopted path")
    parts = name.split("/")
    if any(part in ("", ".", "..") for part in parts) or PurePosixPath(name).is_absolute():
        raise ValueError("invalid adopted path")
    target = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlink in adopted path")
    if not target.is_file() or not target.resolve().is_relative_to(root):
        raise ValueError("adopted file missing or outside repository")
    return target


def validate(root: Path, manifest: dict) -> dict:
    if not isinstance(manifest, dict) or manifest.get("schema") != 1:
        raise ValueError("unsupported adoption schema")
    upstream = manifest.get("upstream", {})
    if not isinstance(upstream, dict):
        raise ValueError("invalid upstream identity")
    if upstream.get("repository") != "rmkn85/agentic-engineering" or not re.fullmatch(r"[0-9a-f]{40}", upstream.get("revision", "")):
        raise ValueError("missing immutable upstream identity")
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("no adopted files")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            raise ValueError("invalid adopted file entry")
        name = entry["path"]
        if name in seen or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]):
            raise ValueError("duplicate path or invalid digest")
        seen.add(name)
        if hashlib.sha256(local_file(root, name).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("adopted content drift: " + name)
    entrypoints = manifest.get("entrypoints", [])
    if not isinstance(entrypoints, list):
        raise ValueError("invalid contributor entrypoints")
    for name in entrypoints:
        if not local_file(root, name).read_text(encoding="utf-8").strip():
            raise ValueError("empty contributor entry")
    result = {"schema": 1, "state": "adoption_valid", "files": len(seen), "upstream_revision": upstream["revision"]}
    # A dependency checkout inherits its caller's CI environment. Only the
    # primary checkout may compare HEAD with that workflow's GITHUB_SHA;
    # dependency pins belong to the native composition verifier.
    workspace = os.environ.get("GITHUB_WORKSPACE")
    if os.environ.get("GITHUB_ACTIONS") == "true" and (
        not workspace or Path(workspace).resolve() != root
    ):
        result["ci_identity_scope"] = "not_primary_checkout"
    elif os.environ.get("GITHUB_ACTIONS") == "true":
        expected = os.environ.get("GITHUB_SHA", "")
        if not re.fullmatch(r"[0-9a-f]{40}", expected):
            raise ValueError("CI candidate identity missing")
        actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL, timeout=15).strip()
        if actual != expected:
            raise ValueError("CI candidate identity mismatch")
        result["candidate"] = actual
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest", default=".agents/engineering/ORIGIN.json")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).resolve()
        manifest = json.loads(local_file(root, args.manifest).read_text(encoding="utf-8"))
        result = validate(root, manifest)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        # Do not expose raw subprocess output or absolute host paths.
        reason = str(error) if type(error) is ValueError else "adoption_input_or_git_failure"
        print(json.dumps({"schema": 1, "state": "blocked", "reason": reason}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
