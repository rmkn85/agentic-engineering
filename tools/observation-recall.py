#!/usr/bin/env python3
"""Retrieve bounded, exact slices from a quiet-run observation bundle."""

import argparse
import base64
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


def artifact_from_manifest(manifest_path, artifact_id, expected_identity=None):
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
    if expected_identity is not None and expected_identity != expected:
        raise ValueError("continuation observation identity mismatch")
    if file_hash(path) != expected:
        raise ValueError("artifact hash mismatch")
    return path, expected


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


def recall_json(path, identity, args):
    """Report selection coverage separately from exact retained byte identity."""
    total = path.stat().st_size
    selection = {}
    extent = {}
    continuation = None
    search_complete = None
    whole_artifact_search = None
    if args.bytes is not None:
        start, count = parse_span(args.bytes, 0)
        if start > total:
            raise ValueError("byte start exceeds artifact size")
        limit = min(count, args.max_output_bytes)
        with path.open("rb") as source:
            source.seek(start)
            output = source.read(limit)
        end = start + len(output)
        selection = {"kind": "bytes", "start": start, "count": count}
        extent = {"byte_start": start, "byte_end_exclusive": end}
        complete = len(output) >= count or end == total
        whole = start == 0 and end == total
        if not complete:
            continuation = ["--bytes", "{}:{}".format(end, count - len(output))]
    else:
        selected = []
        size = 0
        returned_lines = []
        complete = True
        first_byte = None
        last_byte = None
        if args.lines is not None:
            start, count = parse_span(args.lines, 1)
            selection = {"kind": "lines", "start": start, "count": count}
            with path.open("rb") as source:
                number = 0
                while number < start + count - 1:
                    offset = source.tell()
                    line = source.readline(args.max_output_bytes + 1)
                    if not line:
                        break
                    # A bounded read cannot establish a line boundary on overflow.
                    if len(line) > args.max_output_bytes:
                        raise ValueError("line exceeds output limit; use --bytes or raise --max-output-bytes")
                    number += 1
                    if number >= start:
                        if size + len(line) > args.max_output_bytes:
                            complete = False
                            continuation = ["--lines", "{}:{}".format(number, start + count - number)]
                            break
                        selected.append(line)
                        returned_lines.append(number)
                        size += len(line)
                        if first_byte is None:
                            first_byte = offset
                        last_byte = source.tell()
            if start > number + 1:
                raise ValueError("line start exceeds artifact extent")
            output = b"".join(selected)
            whole = (first_byte == 0 and last_byte == total) or (start == 1 and total == 0)
        else:
            term = args.find.encode("utf-8")
            if not term:
                raise ValueError("search term must not be empty")
            start = args.start_line
            selection = {"kind": "find", "literal": args.find, "start_line": start,
                         "max_matches": args.max_matches}
            search_complete = True
            with path.open("rb") as source:
                number = 0
                while True:
                    offset = source.tell()
                    line = source.readline(args.max_output_bytes + 1)
                    if not line:
                        break
                    if len(line) > args.max_output_bytes:
                        raise ValueError("line exceeds output limit; use --bytes or raise --max-output-bytes")
                    number += 1
                    if number < start or term not in line:
                        continue
                    item = str(number).encode("ascii") + b":" + line
                    if len(selected) >= args.max_matches or size + len(item) > args.max_output_bytes:
                        if not selected:
                            raise ValueError("match exceeds output limit; use --bytes or raise --max-output-bytes")
                        search_complete = False
                        continuation = ["--find", args.find, "--start-line", str(number)]
                        break
                    selected.append(item)
                    returned_lines.append(number)
                    size += len(item)
                extent["searched_through_line"] = number if search_complete else number - 1
            if search_complete and start > number + 1:
                raise ValueError("search start exceeds artifact extent")
            complete = search_complete
            whole_artifact_search = start == 1 and search_complete
            whole = False  # Search results do not return nonmatching artifact bytes.
            output = b"".join(selected)
        extent.update({"line_numbers": returned_lines})
        if args.lines is not None:
            extent.update({"byte_start": first_byte, "byte_end_exclusive": last_byte})
    if continuation is not None:
        continuation = [str(args.manifest), "--artifact", args.artifact,
                        "--expect-sha256", identity, "--json",
                        "--max-output-bytes", str(args.max_output_bytes),
                        "--max-matches", str(args.max_matches)] + continuation
    return {
        "schema": "observation-recall-v1",
        "observation": {"id": "sha256:" + identity, "verified": True,
                        "artifact": args.artifact, "bytes": total},
        "selection": selection,
        "returned": dict(extent, bytes=len(output)),
        "coverage": {"selection": "complete" if complete else "partial",
                     "artifact": "complete" if whole else "partial",
                     "search_complete": search_complete,
                     "whole_artifact_search_complete": whole_artifact_search,
                     "substantive_verdict": "unassessed"},
        "continuation_argv": continuation,
        "output": {"encoding": "base64", "data": base64.b64encode(output).decode("ascii")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact", default="full-log")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--lines", metavar="START:COUNT", help="1-based line number and count")
    selector.add_argument("--bytes", metavar="START:COUNT", help="0-based byte offset and count")
    selector.add_argument("--find", metavar="LITERAL", help="literal text, with line numbers")
    parser.add_argument("--json", action="store_true", help="emit exact bytes and coverage receipt as JSON")
    parser.add_argument("--expect-sha256", help="require the same observation identity on continuation")
    parser.add_argument("--start-line", type=int, default=1, help="first search line (JSON find only)")
    parser.add_argument("--max-matches", type=int, default=20)
    parser.add_argument("--max-output-bytes", type=int, default=16384)
    args = parser.parse_args()
    try:
        if args.max_matches < 1 or args.max_output_bytes < 1:
            raise ValueError("output limits must be positive")
        if args.start_line < 1 or (args.start_line != 1 and (not args.json or args.find is None)):
            raise ValueError("--start-line requires JSON find and a positive line")
        path, identity = artifact_from_manifest(args.manifest, args.artifact, args.expect_sha256)
        if args.json:
            print(json.dumps(recall_json(path, identity, args), ensure_ascii=True))
        else:
            sys.stdout.buffer.write(recall(path, args))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        parser.exit(2, "observation-recall: {}\n".format(error))


if __name__ == "__main__":
    main()
