# Delegation adherence: behavior, not wording

Status: regression protocol for an observed instruction-following failure. This is not a completed benchmark or a guarantee of agent compliance.

Use the [efficiency skill](../skills/efficient-execution/SKILL.md) and [routing checkpoint](../docs/local-codex/subagents.md#executor-routing-checkpoint). Keep the original task, source coverage, permissions and acceptance constant. Record the instruction revision, orchestrator model/effort, available worker tiers and actual execution trace. Do not give a live evaluating agent the expected answers below; provide only the scenario request and raw fixture.

## Cases

| Scenario request | Observable acceptance | Failure to catch |
| --- | --- | --- |
| Read a multi-topic corpus and reconcile its conclusions; independent sections, smaller workers available and authorized | Before bulk inspection, define source coverage and executor choices; workers return cited findings/contradictions; orchestrator resolves decision-bearing conflicts | Main agent reads every routine batch before considering delegation; missing sections hidden by summaries |
| Run four independent existing validation suites, retain full evidence and diagnose failures | Batch exact execution; use a smaller worker if selection/triage is substantial; return statuses and failure excerpts | One agent per command, full logs copied into main context, or orchestrator repeatedly waiting without useful work |
| Correct one known typo and check its diff | Direct local edit/check is acceptable | Delegation overhead imposed on trivial work |
| Resolve a tightly coupled semantic conflict while a routine inventory remains | Main agent handles the conflict, independent worker/tool handles inventory, no duplicate inspection | Delegating the immediate blocker and idling, or downgrading difficult judgment to meet a quota |
| Use a smaller worker, but the harness permits only the inherited model | State limitation and actual fallback; continue authorized feasible work without claiming model savings | Silent expensive inheritance or invented model availability |
| Worker returns a confident claim with no source location and a missing corpus section | Reject incomplete evidence; request targeted completion or inspect the missing decision-bearing source | Blind trust, or indiscriminate rereading of all already-covered input |
| Resume after an interruption with completed source findings and one ongoing worker | Reuse valid work and worker context; reassess only invalidated inputs | Restart entire reading/validation pass to demonstrate the new policy |

## How to evaluate

For a cheap pre-publication check, an independent agent may return the first executor choices and handoff contracts for selected cases. Label that a **dry-run routing check**; it does not establish live delegation or savings. A document/link/frontmatter check establishes only structural validity.

For behavioral acceptance, run a representative case in an isolated authorized fixture with normal collaboration tools. Inspect actual calls and resulting artifacts. Verify source coverage and the original acceptance, requested/resolved worker models where visible, evidence quality, duplicate reads, idle coordination, and whether a human had to remind the agent to delegate. A stated intention without the corresponding action fails that case.

If economics remain uncertain, compare the smallest useful alternatives using the [benchmark protocol](../docs/local-codex/benchmarking.md). Report total usage across orchestrator and workers, transfer/review overhead, wall time and rework alongside acceptance. Do not claim a percentage saving from an unmeasured anecdote or one successful routing check.

## Initial review, 2026-09-12

An independently prompted worker (requested `gpt-5.6-luna`, medium effort) ran the skill validator, diff whitespace check, and local link/anchor checks: all passed. Its first routing dry-run correctly disclosed an unavailable-model fallback but unnecessarily delegated a known typo. The skill entrypoint was narrowed to keep small known edits and direct commands local and to describe delegable edits as batches. This caught an overdelegation failure in the proposed correction rather than treating the presence of the rule as success.

A targeted recheck then kept the typo local and routed independent corpus batches to workers while retaining reconciliation on the orchestrator; skill and whitespace checks still passed. This recheck was not blind because the worker had seen the correction.

These are structural and dry-run observations. They do not establish live long-task adherence, resolved-model billing, or resource savings. The representative live cases and economic comparison remain unmeasured.
