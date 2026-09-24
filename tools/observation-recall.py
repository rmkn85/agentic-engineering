#!/usr/bin/env python3
"""Retrieve bounded, exact slices from a quiet-run observation bundle."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_span(value, first_minimum):
    match = re.fullmatch(r"(\d+):(\d+)", value)
    if not match:
        raise ValueError("span must be START:COUNT")
    start, count = map(int, match.groups())
    if start < first_minimum or count < 1:
        raise ValueError("span start or count is out of range")
    return start, count


def artifact_from_manifest(manifest_path, artifact_id):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = [item for item in manifest["evidence"] if item.get("id") == artifact_id]
    if len(entries) != 1:
        raise ValueError("artifact id is missing or ambiguous")
    entry = entries[0]
    ref = entry["ref"]
    if Path(ref).name != ref or ref in (".", ".."):
        raise ValueError("artifact ref must be a file in the bundle")
    path = manifest_path.parent / ref
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact is missing or is a symlink")
    expected = entry.get("sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("artifact has no valid sha256 receipt")
    if file_hash(path) != expected:
        raise ValueError("artifact hash mismatch")
    return path


def recall(path, args):
    if args.bytes is not None:
        start, count = parse_span(args.bytes, 0)
        if count > args.max_output_bytes:
            raise ValueError("requested byte count exceeds output limit")
        with path.open("rb") as source:
            source.seek(start)
            return source.read(count)
    if args.lines is not None:
        start, count = parse_span(args.lines, 1)
        with path.open("rb") as source:
            selected = []
            size = 0
            for number, line in enumerate(source, 1):
                if number >= start + count:
                    break
                if number >= start:
                    selected.append(line)
                    size += len(line)
                    if size > args.max_output_bytes:
                        raise ValueError("selected output exceeds limit; request a narrower range or raise --max-output-bytes")
        output = b"".join(selected)
    else:
        term = args.find.encode("utf-8")
        if not term:
            raise ValueError("search term must not be empty")
        selected = []
        size = 0
        with path.open("rb") as source:
            for number, line in enumerate(source, 1):
                if term in line:
                    item = str(number).encode("ascii") + b":" + line
                    selected.append(item)
                    size += len(item)
                    if size > args.max_output_bytes:
                        raise ValueError("selected output exceeds limit; request a narrower range or raise --max-output-bytes")
                    if len(selected) >= args.max_matches:
                        break
        output = b"".join(selected)
    if len(output) > args.max_output_bytes:
        raise ValueError("selected output exceeds limit; request a narrower range or raise --max-output-bytes")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact", default="full-log")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--lines", metavar="START:COUNT", help="1-based line number and count")
    selector.add_argument("--bytes", metavar="START:COUNT", help="0-based byte offset and count")
    selector.add_argument("--find", metavar="LITERAL", help="literal text, with line numbers")
    parser.add_argument("--max-matches", type=int, default=20)
    parser.add_argument("--max-output-bytes", type=int, default=16384)
    args = parser.parse_args()
    try:
        if args.max_matches < 1 or args.max_output_bytes < 1:
            raise ValueError("output limits must be positive")
        path = artifact_from_manifest(args.manifest, args.artifact)
        sys.stdout.buffer.write(recall(path, args))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(2, "observation-recall: {}\n".format(error))


if __name__ == "__main__":
    main()
