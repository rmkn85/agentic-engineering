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

--strict and --integration fail while any finding is open. Integration requires
a disposition (fixed, addressed or declined) with its normal evidence/reason.
--reopen ID --evidence PATH --reason TEXT retains the previous decision in
history, records new evidence, and makes a recurring finding open again.
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import date
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


def problems(root: Path, integration: bool = False) -> tuple[list[str], dict]:
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
        if integration and status == "open":
            errors.append(f"{name}: unresolved {row['severity']} finding needs a disposition before integration")
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



def reopen(root: Path, ident: str, evidence: Path, reason: str) -> None:
    """Reopen a decision without erasing its original status, proof or rationale."""
    if not sentence(reason):
        raise ValueError("reopening requires a reason explaining recurrence or changed assumptions")
    try:
        evidence_ref = evidence.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        raise ValueError("reopening evidence must be inside root; ledger stores a portable relative reference")
    data = evidence.read_bytes()
    if not data.strip():
        raise ValueError("reopening requires nonempty artifact evidence")
    ledger = root / LEDGER
    rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    matches = [row for row in rows if row.get("id") == ident]
    if len(matches) != 1:
        raise ValueError("reopening requires exactly one existing finding id")
    row = matches[0]
    if row.get("status") not in STATUSES - {"open"}:
        raise ValueError("finding is already open or has an unknown status")
    previous = {key: value for key, value in row.items() if key != "history"}
    event = {"date": date.today().isoformat(), "reason": reason,
             "evidence": {"path": evidence_ref, "sha256": hashlib.sha256(data).hexdigest()},
             "previous": previous}
    history = row.setdefault("history", [])
    if not isinstance(history, list):
        raise ValueError("finding history must be a list")
    history.append(event)
    row["status"] = "open"
    # Original note/tests/mutation stay intact; history retains each earlier decision too.
    temporary = ledger.with_suffix(".jsonl.tmp")
    with temporary.open("x", encoding="utf-8") as out:
        out.write("".join(json.dumps(item) + "\n" for item in rows))
    temporary.replace(ledger)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true", help="also fail while findings are open")
    parser.add_argument("--integration", action="store_true", help="fail all unresolved findings before integration")
    parser.add_argument("--reopen", metavar="ID", help="reopen a recurring or invalidated decision")
    parser.add_argument("--evidence", help="nonempty artifact documenting recurrence or changed assumptions")
    parser.add_argument("--reason", help="why the earlier decision must be reconsidered")
    args = parser.parse_args(argv)
    if args.reopen:
        try:
            if not args.evidence or not args.reason:
                raise ValueError("--reopen requires --evidence and --reason")
            reopen(Path(args.root).resolve(), args.reopen, Path(args.evidence), args.reason)
        except (OSError, ValueError, TypeError) as exc:
            print(f"findings: FAIL: {exc}", file=sys.stderr)
            return 1
    elif args.evidence or args.reason:
        parser.error("--evidence and --reason require --reopen")
    errors, counts = problems(Path(args.root).resolve(), integration=args.integration)
    for error in errors:
        print(f"findings: FAIL: {error}", file=sys.stderr)
    print(f"findings: {counts['fixed']} fixed ({counts['proven']} with a mutation proof), "
          f"{counts['addressed']} addressed without proof, {counts['declined']} declined, {counts['open']} open")
    return 1 if errors or (args.strict and counts["open"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
