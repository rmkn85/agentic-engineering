# AGENTS.md template

Copy this into a repository and fill the bracketed parts. Keep it under about
400 words: a map, not a manual. `AE` below is the path to an agentic-engineering
checkout, for example `../agentic-engineering`.

## What this repository delivers
[One paragraph: the user outcome it owns, and what it does not own.]

## Every task, in this order
1. **Focus.** Run `python3 AE/tools/work_audit.py --root .` and do its FOCUS line
   first, unless the user names a different task. It reads this
   repository's history, so it works the same for every agent.
2. **Goal.** Write the outcome and the checks that prove it in
   `.agent/goal.json` (`python3 AE/tools/finish_check.py --help`).
3. **Change behaviour.** Progress is changed behaviour that a check proves.
   Records, handoffs and process changes support it: replace them instead of
   appending, and keep them a small share of commits.
4. **Prove.** Run [the cheapest check that proves the goal: command]. Fix what
   fails; a skipped test is unfinished work.
5. **Finish.** Run `python3 AE/tools/finish_check.py --root .`. If a real
   blocker remains, mark the item blocked with the reason and the reflection.
   Do executable work now; "next steps" are only for work you cannot do.

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
