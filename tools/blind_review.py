#!/usr/bin/env python3
"""Run blind reviews the same way every time, and keep what they find.

Two-phase reviews derive criteria from the original request and failure evidence
before exposing the builder goal or implementation. Receipts bind bytes and
artifact references; they do not prove reviewer independence or semantic truth.

The original prompt/ingest route remains a labeled legacy goal-based review:

  prompt  print the reviewer prompt, built from the change's goal record
          (.agent/goal.json) plus repository, branch and base. Give it to a
          fresh agent session with no prior context (any host).
  ingest  read the reviewer's report, extract its FINDINGS block, and append
          each finding to validation/findings.jsonl as open, with a new id.

The report's FINDINGS block is JSON lines between the markers below, one
object per finding with severity, target, problem and reproduction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

START, END = "BEGIN FINDINGS", "END FINDINGS"
SEVERITIES = {"blocker", "should-fix", "minor"}

PROMPT = """You are an independent reviewer. You have NOT seen how this change was made; judge it only against the goal.

Repository: {repo}. Branch under review: {branch}. Base: {base}.
Clone into a NEW directory of your own: git clone -q {repo} {workdir} && cd {workdir} && git checkout -q {branch}
Do not read or modify any other working directory, and do NOT read the pull request description or commit messages:
they carry the author's reasoning. Judge the diff (git diff origin/{base}...HEAD) and the behaviour.

GOAL: {goal}

The change claims these checks prove the goal:
{checks}

Run the project's own checks, then try hard to break each claim with real experiments: bypasses, malformed input,
false positives on everyday use, concurrency, anything the checks do not cover. Run them; do not speculate.
Each tool states its scope in a "Scope:" paragraph of its --help. Test against that scope first. Report a finding
outside it only if you think the scope itself is wrong, and add "scope": "out" to that finding.
Do not fix or push anything. Pass dangerous commands you test only as data (for example from a Python
list) to the tool under test, never through a shell that could execute them.

Report, most severe first, under 800 words. End with one line per claim: met / partly met / not met, and why.
Then list every finding as JSON lines between these exact markers:
{start}
{{"severity": "blocker|should-fix|minor", "target": "path:line", "problem": "one sentence", "reproduction": "command run and its output", "scope": "in|out"}}
{end}
Write an empty block if you found nothing."""



def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def payload_hash(payload: dict) -> str:
    return digest(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_criteria(criteria: dict) -> None:
    if not isinstance(criteria, dict) or set(criteria) != {"criteria", "discrepancies"}:
        raise ValueError("frame requires exactly criteria and discrepancies")
    rows = criteria["criteria"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("frame criteria must be a nonempty list")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "requirement", "check"} or not all(
                nonempty(row[k]) for k in ("id", "requirement", "check")):
            raise ValueError("each criterion requires id, requirement and independent check")
        if row["id"] in seen:
            raise ValueError("duplicate criterion id")
        seen.add(row["id"])
    if not isinstance(criteria["discrepancies"], list):
        raise ValueError("discrepancies must be a list")
    seen = set()
    for row in criteria["discrepancies"]:
        if not isinstance(row, dict) or set(row) != {"id", "problem", "resolution", "evidence"} or not all(
                nonempty(row[k]) for k in ("id", "problem", "resolution")):
            raise ValueError("every discrepancy needs an explicit resolution and artifact evidence")
        if row["id"] in seen:
            raise ValueError("duplicate discrepancy id")
        seen.add(row["id"])
        if not isinstance(row["evidence"], list) or not row["evidence"]:
            raise ValueError("discrepancy resolution needs artifact evidence")
        for item in row["evidence"]:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"} or not nonempty(item["path"]):
                raise ValueError("artifact evidence requires path and sha256")
            data = Path(item["path"]).read_bytes()
            if not data.strip() or digest(data) != item["sha256"]:
                raise ValueError("artifact evidence is empty or hash mismatch")


def seal_frame(request: Path, failure: Path, criteria_path: Path, output: Path) -> dict:
    criteria = json.loads(criteria_path.read_text(encoding="utf-8"))
    # Evidence paths in submitted criteria are relative to that file, never the caller's cwd.
    for row in criteria.get("discrepancies", []):
        for item in row.get("evidence", []):
            if isinstance(item, dict) and nonempty(item.get("path")):
                item["path"] = str((criteria_path.parent / item["path"]).resolve())
    validate_criteria(criteria)
    payload = {"schema": 1, "request_sha256": digest(request.read_bytes()),
               "failure_sha256": digest(failure.read_bytes()), "frame": criteria}
    if not request.read_bytes().strip() or not failure.read_bytes().strip():
        raise ValueError("original request and failure evidence must be nonempty")
    receipt = {"payload": payload, "sha256": payload_hash(payload)}
    # Exclusive creation prevents replacing an earlier framing decision in place.
    with output.open("x", encoding="utf-8") as out:
        json.dump(receipt, out, indent=2)
        out.write("\n")
    return receipt


def validate_frame(path: Path, request: Path, failure: Path) -> dict:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict) or set(receipt) != {"payload", "sha256"}:
        raise ValueError("invalid framing receipt")
    payload = receipt["payload"]
    if not isinstance(payload, dict) or set(payload) != {"schema", "request_sha256", "failure_sha256", "frame"}:
        raise ValueError("invalid framing payload")
    if payload["schema"] != 1 or payload_hash(payload) != receipt["sha256"]:
        raise ValueError("framing receipt hash mismatch")
    if digest(request.read_bytes()) != payload["request_sha256"] or digest(failure.read_bytes()) != payload["failure_sha256"]:
        raise ValueError("request or failure evidence changed since framing")
    validate_criteria(payload["frame"])
    return receipt


def validate_goal_framing(root: Path, goal: dict) -> list[str]:
    """Validate declared review controls; callers decide when review is required.

    This checks artifact binding and completion, never semantic quality or whether
    a contribution was correctly classified as methodology/control work.
    """
    review = goal.get("review")
    if review is None:
        return ["methodology/control goal requires a review declaration"] if goal.get("kind") in {"methodology", "control"} else []
    if not isinstance(review, dict) or review.get("kind") not in {"ordinary", "methodology", "control"}:
        return ["review requires kind ordinary, methodology or control"]
    if review["kind"] == "ordinary":
        return ["methodology/control goal cannot use ordinary review"] if goal.get("kind") in {"methodology", "control"} else []
    fields = ("framing", "request", "failure_evidence")
    if not all(nonempty(review.get(key)) for key in fields):
        return ["methodology/control review requires framing, request and failure_evidence paths"]
    try:
        receipt = validate_frame(root / review["framing"], root / review["request"], root / review["failure_evidence"])
        if "framing_sha256" in review and review["framing_sha256"] != receipt["sha256"]:
            return ["framing receipt differs from the independently retained hash"]
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return [f"invalid review framing: {exc}"]
    return []


def frame_prompt(request: str, failure: str) -> str:
    return ("Independent framing phase: derive the requested outcome and independent falsifiable checks "
            "from the original request and observed failure. Do not read the builder goal, plan, diff, "
            "commit messages or implementation yet. Challenge the frame itself, including missing "
            "capability and success criteria. Preserve original authority; do not invent requirements.\n"
            "ORIGINAL REQUEST:\n" + request + "\nFAILURE EVIDENCE:\n" + failure +
            '\nReturn JSON with exactly criteria and discrepancies. criteria is a nonempty list of '
            '{"id":"C1","requirement":"requested behavior","check":"independent falsifiable check"}. '
            'discrepancies is a list of {"id":"D1","problem":"gap","resolution":"explicit resolution",'
            '"evidence":[{"path":"artifact path","sha256":"artifact SHA256"}]}; resolve every discrepancy '
            'with artifact evidence before sealing, or leave the review blocked. An empty list means none identified. '
            'Do not claim JSON proves semantic correctness or independence.\n')

def checks_text(goal: dict) -> str:
    lines = []
    for item in goal.get("acceptance", []):
        how = f"(make {item['run']})" if item.get("run") else "(manual)"
        lines.append(f"- {item.get('check', '')} {how}")
    return "\n".join(lines) or "- (none declared)"


def render(goal: dict, repo: str, branch: str, base: str, workdir: str) -> str:
    return "LEGACY GOAL-BASED REVIEW (not independent framing)\n" + PROMPT.format(repo=repo, branch=branch, base=base, workdir=workdir, goal=goal.get("goal", ""),
                         checks=checks_text(goal), start=START, end=END)


def parse(report: str) -> list[dict]:
    # Markers count only on their own line, and the last block wins: prose may mention the markers.
    blocks = re.findall(rf"^[ \t`]*{re.escape(START)}[ \t`]*$(.*?)^[ \t`]*{re.escape(END)}[ \t`]*$", report, re.S | re.M)
    if not blocks:
        raise ValueError(f"report has no {START} ... {END} block")
    findings = []
    for line in blocks[-1].splitlines():
        line = line.strip().strip("`")
        if not line or line.startswith("{\"severity\": \"blocker|"):
            continue
        row = json.loads(line)
        if row.get("severity") not in SEVERITIES or not all(
                isinstance(row.get(k), str) and row[k].strip() for k in ("target", "problem", "reproduction")):
            raise ValueError(f"finding is incomplete: {line[:120]}")
        findings.append(row)
    return findings


def ingest(root: Path, report: str, review: str, framing_sha256: str | None = None) -> list[str]:
    ledger = root / "validation" / "findings.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    existing = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if ledger.exists() else []
    prefix = "R" + re.sub(r"\D", "", review)[-3:] if re.search(r"\d", review) else "R"
    taken = {row["id"] for row in existing}
    added = []
    with ledger.open("a", encoding="utf-8") as out:
        for number, finding in enumerate(parse(report), 1):
            ident = f"{prefix}-{number:02d}"
            while ident in taken:
                number += 100
                ident = f"{prefix}-{number:02d}"
            taken.add(ident)
            row = {"id": ident, "review": review, "date": date.today().isoformat(), **{
                k: finding[k] for k in ("severity", "target", "problem", "reproduction")}, "status": "open", "tests": []}
            if framing_sha256:
                row["framing_sha256"] = framing_sha256
            else:
                row["review_mode"] = "legacy-goal-based"
            if finding.get("scope") == "out":
                row["scope"] = "out"
            out.write(json.dumps(row) + "\n")
            added.append(ident)
    return added


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("--goal", default=".agent/goal.json")
    p.add_argument("--repo", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--base", default="main")
    p.add_argument("--workdir", default="/tmp/blind-review")
    i = sub.add_parser("ingest")
    i.add_argument("report", help="file with the reviewer's report, or - for stdin")
    i.add_argument("--review", required=True, help="name of this review, e.g. blind-review-3")
    i.add_argument("--root", default=".")
    for command in (p, i):
        command.add_argument("--review-kind", choices=("ordinary", "methodology", "control"), default="ordinary")
        command.add_argument("--framing")
        command.add_argument("--request")
        command.add_argument("--failure-evidence")
    for name in ("frame-prompt", "seal-frame", "validate-frame", "implementation-prompt"):
        phase = sub.add_parser(name)
        phase.add_argument("--request", required=True)
        phase.add_argument("--failure-evidence", required=True)
        if name == "seal-frame":
            phase.add_argument("--criteria", required=True)
            phase.add_argument("--output", required=True)
        elif name != "frame-prompt":
            phase.add_argument("--framing", required=True)
        if name == "implementation-prompt":
            phase.add_argument("--goal", default=".agent/goal.json")
            phase.add_argument("--repo", required=True)
            phase.add_argument("--branch", required=True)
            phase.add_argument("--base", default="main")
            phase.add_argument("--workdir", default="/tmp/blind-review")
    gate = sub.add_parser("validate-goal")
    gate.add_argument("--goal", default=".agent/goal.json")
    gate.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    try:
        return execute(args)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(f"blind-review: {exc}", file=sys.stderr)
        return 1


def execute(args) -> int:
    if args.command == "validate-goal":
        root = Path(args.root).resolve()
        error = validate_goal_framing(root, json.loads((root / args.goal).read_text(encoding="utf-8")))
        if error:
            raise ValueError("; ".join(error))
        print("blind-review: declared goal framing controls valid (structural binding only)")
        return 0
    if args.command == "frame-prompt":
        print(frame_prompt(Path(args.request).read_text(), Path(args.failure_evidence).read_text()))
        return 0
    if args.command == "seal-frame":
        seal_frame(Path(args.request), Path(args.failure_evidence), Path(args.criteria), Path(args.output))
        print("blind-review: framing receipt sealed (structural binding only)")
        return 0
    receipt = None
    if args.command in ("implementation-prompt", "validate-frame") or args.review_kind != "ordinary":
        if not args.framing or not args.request or not args.failure_evidence:
            raise ValueError("methodology/control review requires framing receipt, original request and failure evidence")
        receipt = validate_frame(Path(args.framing), Path(args.request), Path(args.failure_evidence))
    if args.command == "validate-frame":
        print("blind-review: framing complete; discrepancies have hash-bound artifact evidence (not semantic proof)")
        return 0
    if args.command in ("prompt", "implementation-prompt"):
        goal = json.loads(Path(args.goal).read_text(encoding="utf-8"))
        prompt = render(goal, args.repo, args.branch, args.base, args.workdir)
        if receipt:
            prompt = ("IMPLEMENTATION REVIEW: judge goal and diff against the prior independent framing. "
                      "Treat goal and declared checks as claims, not requirement authority.\nFRAMING RECEIPT: " +
                      receipt["sha256"] + "\n" + json.dumps(receipt["payload"]["frame"], indent=2) +
                      "\n" + prompt.split("\n", 1)[1].replace("judge it only against the goal", "judge it against the independent frame"))
        print(prompt)
        return 0
    report = sys.stdin.read() if args.report == "-" else Path(args.report).read_text(encoding="utf-8")
    added = ingest(Path(args.root).resolve(), report, args.review, receipt["sha256"] if receipt else None)
    print(f"blind-review: {len(added)} findings added as open: {', '.join(added) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
