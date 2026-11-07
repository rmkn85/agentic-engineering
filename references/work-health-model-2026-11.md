# Work health model: what degrades coding-agent work, and how it is detected (2026-11)

`tools/work_audit.py` checks a repository against this model and prints one
FOCUS line plus ranked findings. This note records where each part comes from,
so findings can be argued with and revised. Labels: **measured** (counted in a
real repository or trial), **documented** (vendor or research source),
**hypothesis** (our inference).

## Sources

- *Managing Long-Running Software Development by Coding Agents: A Thin
  Outcome-Control Model* (supplied research, 2026-11): sixteen failure patterns
  in two multi-repository programmes, grouped into nine causal classes. Central
  diagnosis: semantic transitions (backlog item → priority, zero exit →
  success, old observation → current fact) happen in model interpretation
  without proof that real state changed. Supports selective deterministic
  control over more prose (documented, with cited studies).
- *Engineering standards* reports for two game repositories (supplied
  research, 2026-11): acceptance must end in the real user-facing scenario;
  handoffs read as acceptance matrices, not feature lists (documented).
- *Minimal delivery telemetry* report (supplied research, 2026-11): agents
  need small typed receipts with reason codes, not prose from logs; phases,
  completed-vs-selected tests, and delivery state kept separate (documented).
- Lab publications reviewed in [allowlists-and-positive-direction-2026-11](allowlists-and-positive-direction-2026-11.md):
  sandbox and allowlist over per-command prompts and deny-lists; AGENTS.md as
  a map, not a manual; mechanical enforcement; error messages that teach;
  rules are prompts, not enforcement (documented).
- Repository state, counted from history and files (measured, 2026-11-07):
  - 53–58% of commits in three downstream repositories only recorded,
    retained, handed off, checkpointed or gated;
  - one repository carries 52 agent instruction files (23,420 words) with 39
    sentences repeated across them, and about 100 registered worktrees;
  - a "single current handoff" directory of about 2,000 files;
  - entry reading of about 8,000 words before any task.
- Records-loop trial ([validation/trials/records-loop](../validation/trials/records-loop/)):
  a named FOCUS target moved a small model from 0/2 to 3/3 delivering the
  blocked product change; capable models delivered either way (measured).
- Cleanup trial ([validation/trials/cleanup](../validation/trials/cleanup/)),
  small model, "pick up the next task" in each session (measured):
  - base: task list left inconsistent and handoff grown, 2/2 runs;
  - generic actions ("reconcile the task list"): task list fixed, handoff
    still grown; agents deferred "fix the missing blocker" and "merge the
    duplicate" as owner decisions;
  - named fixes (each edit listed, "bookkeeping, not owner decisions"):
    task list and handoff clean after one session in 2/2 lineages;
    instruction duplication declined as "the owner's rules" until the
    finding said that moving text changes no rule; then 0 repeated
    sentences after session 3 in 2/2 lineages;
  - every session in every arm also shipped a product change with a test;
  - permissions (an allowlist) were left to the owner, as they should be.

  Lesson: a weak model acts on a finding when it names the exact edits and
  says whose decision it is. General instructions lose to its caution.

## The model

The loop is goal → select → change → prove → finish. Each area below breaks
one part of it. "Signal" is what the audit computes without judgement.

| Area | Failure | Signal | Action the audit prints |
| --- | --- | --- | --- |
| Direction | Available or internal work chosen over the user-blocking constraint | open goal record; records/process share of recent commits; repeated subjects including the latest commits; task list blocked by finished or missing tasks, stale claims, duplicates; many unmerged branches | Finish the goal; change product behaviour next (naming the unfinished target); change approach instead of repeating; reconcile the task list |
| Evidence | Weak signals read as success | unfinished markers and skipped tests in code (strings excluded); tests that assert nothing; check commands that cannot fail | Finish or delete; give tests assertions; let checks fail |
| Knowledge | Stale or incomplete facts carried forward | handoff files beyond one, or over 800 words; links in instructions/handoffs to missing files | One current handoff; fix or delete broken references |
| Instructions | Corrections added as prose at the failing layer | instruction files beyond 8, or 5+ repeated sentences; instruction growth within the window; required entry reading over limits | One source, thin host pointers, delete repeats; replace prose with checks; shorten the entry |
| Flow | Work and resources outlive their purpose | merged branches, extra worktrees, dated plans, tracked scratch; large tracked binaries | Merge, close or delete; move artefacts out of Git |
| Harness | Capability inferred from prose; deny-lists invite workarounds | no machine-readable allowlist | List the activities agents may run without approval |
| Code | Changes get riskier as code grows | product files over 1,000 lines, Python functions over 120 | Split the part a task changes; never the FOCUS on its own |

## Ordering and balance

Findings are ranked direction → evidence → knowledge → instructions → flow →
harness → code, because a wrong next step wastes everything after it, and
false evidence hides that the step was wrong. Each session does the FOCUS line,
so the list is worked through over sessions. Cleanup commits count as records
or process: when they dominate, the loop finding puts product work first
again. That balance is a hypothesis to watch in practice, not a measured
result.

## Not detected (judgement stays with the agent and owner)

- **Problem framing and architecture**: a proposed solution becoming a new
  contract instead of using the existing owner. The loop's "route every caller
  through the single owner" and the specification contract cover it; no
  reliable textual signal exists.
- **Experiential acceptance**: visual quality, motion, readability. The goal
  record keeps these as manual items with evidence; the audit cannot judge them.
- **Measurement noise and slow feedback loops**: these need run telemetry
  (see the delivery-telemetry report), not repository text.

## What would revise this

- Findings that agents act on but that do not change delivery or rework in
  practice: lower their rank or delete them.
- Thresholds that flag healthy repositories: raise them, with the example.
- Recurring failures with no signal here: add a detector only with a test, a
  mutation proof and a downstream example.
