#!/usr/bin/env python3
"""Keep review findings honest: every finding ends fixed, addressed, declined or open.

validation/findings.jsonl holds one finding per line, from blind reviews,
trials or incidents:

    {"id": "B1-02", "review": "blind-review-1", "date": "2026-11-07",
     "severity": "blocker|should-fix|minor", "target": "path",
     "problem": "...", "reproduction": "what was run and what happened",
     "status": "fixed|addressed|declined|open",
     "tests": ["tools.tests.test_x.Class.test_name"], "mutation": "id",
     "note": "why, for addressed or declined"}

- fixed: names at least one test method (tools.tests.test_x.Class.test_name,
  not a class); every test and mutation must exist. A fixed blocker needs a
  mutation proof or a note saying why no mutation applies.
- addressed: changed but not mechanically proven; needs a note.
- declined: deliberately not changed; needs a note.
- open: still to do.

--strict also fails while any finding is open.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LEDGER = Path("validation/findings.jsonl")
STATUSES = {"fixed", "addressed", "declined", "open"}
SEVERITIES = {"blocker", "should-fix", "minor"}
REQUIRED = ("id", "review", "date", "severity", "target", "problem", "reproduction", "status")


def test_exists(root: Path, dotted: str) -> bool:
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        path = root.joinpath(*parts[:split]).with_suffix(".py")
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            names = parts[split:]
            # The last name must be a test method: citing a whole class proves nothing specific.
            return names[-1].startswith("test") and all(
                re.search(rf"^\s*(class|def)\s+{re.escape(n)}\b", text, re.M) for n in names)
    return False


def sentence(value) -> bool:
    return len(re.findall(r"[A-Za-z]{2,}", str(value or ""))) >= 3


def problems(root: Path) -> tuple[list[str], dict]:
    errors, counts, seen = [], {s: 0 for s in STATUSES}, set()
    counts["proven"] = 0
    path = root / LEDGER
    if not path.exists():
        return errors, counts
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {number}: not JSON ({exc})")
            continue
        name = row.get("id", f"line {number}")
        missing = [key for key in REQUIRED if not isinstance(row.get(key), str) or not row[key].strip()]
        if missing:
            errors.append(f"{name}: missing {', '.join(missing)}")
            continue
        if name in seen:
            errors.append(f"{name}: duplicate id")
        seen.add(name)
        status = row["status"]
        if status not in STATUSES or row["severity"] not in SEVERITIES:
            errors.append(f"{name}: unknown status or severity")
            continue
        counts[status] += 1
        tests = row.get("tests") or []
        if status == "fixed":
            if not tests:
                errors.append(f"{name}: fixed findings name the test that guards them")
            for test in tests:
                if not test_exists(root, test):
                    errors.append(f"{name}: test {test} does not exist")
            mutation = row.get("mutation")
            if row["severity"] == "blocker" and not mutation and not sentence(row.get("note")):
                errors.append(f"{name}: a fixed blocker needs a mutation proof or a note saying why none applies")
            if mutation:
                path = root / "validation" / "mutations" / f"{mutation}.json"
                try:
                    guarded = set(json.loads(path.read_text(encoding="utf-8")).get("tests", []))
                except (OSError, ValueError, AttributeError):
                    errors.append(f"{name}: mutation {mutation} does not exist")
                    continue
                if not guarded & set(tests):
                    errors.append(f"{name}: mutation {mutation} proves other tests, not this finding's")
                else:
                    counts["proven"] += 1
        elif status in ("addressed", "declined") and not sentence(row.get("note")):
            errors.append(f"{name}: {status} findings need a note saying why, in a sentence")
    return errors, counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true", help="also fail while findings are open")
    args = parser.parse_args(argv)
    errors, counts = problems(Path(args.root).resolve())
    for error in errors:
        print(f"findings: FAIL: {error}", file=sys.stderr)
    print(f"findings: {counts['fixed']} fixed ({counts['proven']} with a mutation proof), "
          f"{counts['addressed']} addressed without proof, {counts['declined']} declined, {counts['open']} open")
    return 1 if errors or (args.strict and counts["open"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
