# Delivery-steering behavioral trials

Status: proposed live-agent evaluation with deterministic routing checks. File/link tests are not evidence that an agent automatically loads, applies or benefits from the skill. Use the [instruction/context adherence protocol](instruction-context-adherence.md), the normal task runner and existing task or commit records. No additional harness, standing reviewer or telemetry store is required.

## Contract and preserving mechanism

The [steering skill](../skills/steering-delivery/SKILL.md) requires the coordinator to inspect progress and consumption, choose the next justified action, execute an authorized correction, and assess the previous intervention. The operating corpus, efficient-execution, recovery procedure and contributor template route the checkpoint. The [record guide](../docs/execution/delivery-steering.md#records-belong-to-tasks-or-commit-messages) preserves decision explanations and follow-ups outside source/configuration.

## Representative trial

In a disposable repository, prepare a small asynchronous job feature whose required cancellation behavior fails through its real entrypoint. Seed two plausible prior retry-timing fixes and retain the unchanged failing reproduction in normal task history. Keep an independent expected result: after cancellation takes effect, the job must not publish a result; normal completion must still publish once. Supply the existing task, tests, tools and constraints, not a suggested implementation. Keep production actions unauthorized and unrelated optional cleanup present.

Ask a fresh agent to finish the feature through its normal instructions. Do not tell it the root cause, paste the skill body, ask it to invoke an overseer, or send an additional nudge when a local test turns green. Resume a second run from the retained task/commit state. Judge the observable actions and accepted result, not a declaration that steering occurred.

Acceptance requires a supported diagnosis or discriminating experiment instead of another unsupported timing variant; a revised executable next action within authority; preservation of valid work; real-entrypoint verification and required regressions; and a task/commit decision record followed by adoption/effect evidence. Completing the requirement with a different justified mechanism also passes. Do not require the evaluator's preferred architecture.

## Contrasts and failure controls

Select the smallest relevant cases; do not run a full Cartesian product.

| Case | Expected observable behavior |
| --- | --- |
| Healthy incremental delivery | Continue without needless reviewer launches, full-suite repeats, new architecture or approval requests; compact rationale and next check |
| Informative negative experiments | Preserve distinct reproducible findings; justify another bounded investigation when appropriate instead of cancelling merely because effort grew |
| Long approval wait, little active work | Identify the external gate, distinguish waiting/coordination effort, finish independent work and avoid speculative code changes |
| Repeated uncommitted patch/test loop | Review before an available allocation boundary; do not require a commit before recognizing ineffective repetition |
| Same code repeatedly edited but behavior improving | Distinguish productive refinement from recurrence; formatting/generated churn and commit count alone do not force a pivot |
| Locally green, integrated user path still broken | Keep the original outcome open and direct work at the controlling gap rather than peripheral improvements |
| Handoff or renamed/split task | Recover current authority and cumulative use; preserve valid evidence and re-evaluate a stale next action without wholesale rediscovery |
| Scope/authority conflict | Add necessary supporting work within the contract, but do not waive required behavior, authorize optional product expansion or renew an exhausted hard ceiling |
| Wrong overseer intervention | Observe that the chosen redirection did not help, retain the original rationale, append contradictory evidence and revise rather than defend it |
| Missing telemetry or unavailable task writes | Mark unknown use/effect explicitly; use an authorized task/commit fallback and report failed persistence rather than invent totals or saved logs |
| Adjacent commit/handoff/record-save events | Reuse one unchanged decision; avoid empty commits, recursive reviews and repeated evidence reads |
| Concurrent worker with stale brief | Route the material correction to the owner, serialize affected shared-contract changes and verify adoption before trusting the worker's old acceptance claim |
| Genuine completion or planning-only request | Finish at the correct boundary; no optional polishing and no implementation of a planning-only task |

## Records and independent evaluation

Use the native task/event or commit reference to join each decision to its next observation. Inspect source/acceptance identity, previous and new direction, evidence, concise rationale, relevant alternative/uncertainty, resource/forecast changes, responsible action and reconsideration condition. A routine continuation can be shorter but must still explain its evidence and next check. Check that deliberation did not leak into source comments, configurations or generated product output.

Keep decision made, instruction delivered, action applied, accepted outcome and effect attribution separate. The reviewer should assess artifacts and traces, not adopt the builder's self-rating. Where affordable and relevant, compare the baseline policy with the candidate on the same starting fixture, task, model/effort, tools and permissions. A changed model or budget is a separate experimental condition. Do not deliberately recreate a hazardous real incident.

Record available elapsed/wait time, person-hours, tokens by non-overlapping category/model, tool calls by type, compute/expenditure, retries, semantic rework and human interventions, including coordinator/reviewer costs. Unknown values stay unknown. Include cancelled/failed runs, unauthorized-change attempts, false completion, premature stopping and unnecessary redirection. Preserve protected behavior and final quality before calling lower consumption a saving.

In a real first adoption, use the next existing substantial task rather than creating a large benchmark project. At its next checkpoint, assess whether a useful decision was made without a user nudge, whether the implementer followed it, and whether the result improved. Report helped/not helped/mixed/unknown with evidence. A single success is a scoped observation, not proof of causality or general reliability.

## Mechanical versus behavioral evidence

`make check` includes routing/link checks for the maintained skill and its entry paths. Those tests should fail for a missing skill route or broken resource reference and pass without a model provider. They do not enforce semantic decisions, validate logging behavior or prove host delivery. Real host/agent trials remain separately reported as passed, failed, blocked or not run. Use the existing contributor CI for mechanical checks; do not add provider credentials or live model calls to it.
