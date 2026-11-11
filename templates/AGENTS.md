# AGENTS.md template

Copy this into a repository and fill the bracketed parts. Keep it under about
400 words: a map, not a manual. `AE` below is the path to an agentic-engineering
checkout, for example `../agentic-engineering`.

## What this repository delivers
[One paragraph: the user outcome it owns, and what it does not own.]

## Shared method and native bindings

Apply [the shared contributor core](contributor-core.md), including preservation
of architectural decisions. Copy it beside this entry or update this link to
the reviewed local snapshot. Keep product authority and native commands local.

- Audit: `python3 AE/tools/work_audit.py --root .`.
- Goal: `.agent/goal.json` (`python3 AE/tools/finish_check.py --help`).
- Prove: [the cheapest check that proves the goal: command].
- Finish: `python3 AE/tools/finish_check.py --root .`; a real blocker needs its
  reason and reflection in the goal record.

## Commands
[Build, test and run commands. List the local ones agents may run without
approval in `configs/allowed-activities.json`; everything else needs approval.]

## Hard limits
[Only the few things that must never happen here, each with its reason.]

## Handoff
One file, under 800 words: goal, last proven state, next action. History is in Git.

For source-code subtrees, prefer a small nested instruction such as
[`source-AGENTS-agent-legible.md`](source-AGENTS-agent-legible.md). Link deeper
procedures; do not inline them.
