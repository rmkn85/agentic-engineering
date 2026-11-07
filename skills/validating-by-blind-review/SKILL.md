---
name: validating-by-blind-review
description: Before merging a consequential change to rules, tools, gates or shared behaviour, have a fresh agent that sees only the goal try to break it, then turn every finding into a test or a recorded decision.
---

# Validate by blind review

Use for changes whose failure would mislead other agents or users: guards, gates, checks, instructions, shared tools. Skip for small local edits that the normal suite already covers.

1. Write the goal record first (`.agent/goal.json`). The reviewer sees only the goal and the checks you claim prove it.
2. Push the branch. Run `python3 tools/blind_review.py prompt --repo URL --branch BRANCH > prompt.txt`.
3. Give the prompt to a **fresh** session with no prior context: a subagent that does not inherit your conversation, `claude -p`, `codex exec`, or another host. Never a fork of yourself, and never with your reasoning attached.
4. Save the report and run `python3 tools/blind_review.py ingest report.md --review blind-review-N`. Findings enter `validation/findings.jsonl` as open.
5. For each finding: write the failing test from its reproduction, fix, and set the status to `fixed` with the test name. Where the finding is a rule, add a mutation in `validation/mutations/` and run `make prove`. Otherwise mark it `addressed` or `declined` with a note.
6. Repeat with a new fresh reviewer until a review finds no blocker. `make findings` stays red while anything is open.

Do not argue a finding away in prose. Either a test shows it is wrong, or it is a finding.
