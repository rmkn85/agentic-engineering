#!/usr/bin/env python3
"""Create a cheap deterministic inventory of Git-tracked files.

No model calls. The index is intentionally shallow: use ctags/LSP/language-native
metadata for richer symbol and dependency graphs.
"""
from __future__ import annotations
import argparse, json, os, subprocess
from pathlib import Path


def run(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--output", default=".agent-cache/repo-index.jsonl")
    ns = ap.parse_args()
    repo = Path(ns.repo).resolve()
    out = (repo / ns.output).resolve() if not Path(ns.output).is_absolute() else Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    # mode SP blob SP stage TAB path NUL
    raw = run(repo, "ls-files", "-s", "-z")
    rows = []
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, path_b = rec.split(b"\t", 1)
        mode_b, blob_b, stage_b = meta.split(b" ", 2)
        rel = os.fsdecode(path_b)
        p = repo / rel
        size = p.stat().st_size if p.exists() else None
        ext = p.suffix.lower()
        binary = False
        lines = None
        if p.is_file():
            try:
                data = p.read_bytes()
                binary = b"\0" in data[:8192]
                if not binary:
                    lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
            except OSError:
                pass
        rows.append({
            "path": rel,
            "git_blob": blob_b.decode(),
            "mode": mode_b.decode(),
            "stage": int(stage_b),
            "bytes": size,
            "lines": lines,
            "extension": ext,
            "binary": binary,
        })

    with out.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    total_bytes = sum(r["bytes"] or 0 for r in rows)
    print(f"INDEX files={len(rows)} bytes={total_bytes} output={out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
