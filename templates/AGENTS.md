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
Project-owned path: [HANDOFF.md]. Keep goal, last proven state and next action
under 800 words; preserve unfinished work and local record authority. Declare
shared/dependency trees in `.agent/audit.json` as `external_scopes` (root-relative
directories); see [ownership adoption](../docs/adoption/newcomer-contract.md#selective-local-inheritance).
Keep project handoffs and tasks outside those trees.

For source-code subtrees, prefer a small nested instruction such as
[`source-AGENTS-agent-legible.md`](source-AGENTS-agent-legible.md). Link deeper
procedures; do not inline them.
