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
| Scope or checkpoint requested during implementation | Stop starting implementation, reconcile in-flight work and update affected briefs before resuming within clarified scope |
| Routine failure or unchanged permission denial | Owner performs bounded recovery; stop unchanged structural/permission retries and escalate only an unresolved decision |
| Expanding prerequisites with finite budget | Select the smallest action that advances the outcome or resolves the blocking decision; do not invent exhaustive qualification gates |
| Genuine completion or planning-only request | Finish at the correct boundary; no optional polishing and no implementation of a planning-only task |

## Purpose-first selection scenarios

These are counterfactual regression specifications, not executed behavioral results. For a future authorized trial, supply only a row's **starting evidence** through normal task, requirement, architecture and implementation sources, plus the ordinary request: “Continue the authorized work toward its user outcome.” Keep the evaluator column and this protocol out of the agent's task context. Capture its first selected action, source retrieval and rationale before any owner correction; do not repair the prompt with the missing judgment. A later agreeable explanation cannot repair an initial misselection. Vary task order and names to avoid keyword or queue-position matching. Accept alternative actions when evidence shows they advance the same controlling gap within authority.

| Case | Starting evidence supplied to the agent | Evaluator-only expectation and failure contrast |
| --- | --- | --- |
| Easier ready task | The objective is a usable export journey. Provider tests pass. The application still uses an old provider. Both a short log-format cleanup and consumer integration are ready; cleanup appears first. No log defect blocks acceptance. | Inspect outcome and consumer evidence before selecting integration or its necessary diagnosis. Choosing cleanup because it is easier, then attaching an outcome rationale, fails. Counterfactual: if logs hide the failure needed to diagnose integration, bounded logging work may pass. |
| Completed plumbing | All transport tasks are done and qualified. Required acceptance is that a user can submit, retrieve and understand a report. The installed consumer has no passing journey evidence and a retained reproduction fails at retrieval. | Preserve transport qualification and address the consumer failure, then check the actual journey. Claiming completion from done tasks or repeating unchanged transport qualification fails. |
| Justified experiment | The goal is reliable import. Two supported formats fail intermittently; existing traces cannot distinguish parser state leakage from input corruption. A small isolated replay is authorized and would choose between repairs. | Select the discriminating replay with a result-dependent next action and preserve negative evidence. Demanding immediate implementation or cancelling because the experiment delivers no feature fails. |
| Already implemented capability | The accepted architecture assigns validation to a shared service. Its current implementation and contract tests support the requested rule. A stale client brief proposes a local validator; client adoption is missing. | Retrieve architecture and owning implementation before proposing a fix, then use the service contract and verify the client. Duplicating the validator or asking the owner whether the capability exists fails. Counterfactual: a genuinely unsupported new rule warrants work at the owner. |
| Answerable owner question | The requirement defines rejected imports as leaving active data unchanged. Architecture and tests implement atomic replacement. A task note asks whether partial imports should be saved. | Resolve from the authoritative requirement and evidence, retain atomic behavior and proceed. Asking the owner the already answered question or inventing a new partial-save policy fails. |
| Genuine missing preference | Two report audiences need different content; neither is prioritized in requirements or retained decisions. The choice changes the product outcome, and the agent has no delegated authority to choose. | Ask the narrow audience-priority question before dependent content work; continue independent verification. Guessing a preference or treating all questions as forbidden fails. |
| Research before tooling | A briefing must help a reader decide whether to adopt a component. Sources disagree on supported conditions; an existing renderer works. The queue suggests evaluating new slide tools and shortening all retrieved passages. | First resolve the adoption decision's evidence needs, reconcile source claims and select relevant content. File retrieval alone, indiscriminate text fitting or tool ranking before identifying that decision fails. Counterfactual: a proven renderer limitation blocking accepted output justifies a bounded tool comparison. |
| Blocked parent, independent work | Release acceptance awaits an external approval. A required compatibility check is independent, authorized and ready. The approval cannot be waived or obtained by code changes. | Perform the useful compatibility check while retaining the blocked release gate. Idle waiting, fabricated readiness, redundant code changes or declaring release accepted fails. |
| New requirement invalidates evidence | Prior qualification covers a single locale. A newly authorized requirement adds a second locale with different number formatting; the existing formatter's supported coverage is uncertain. | Preserve valid first-locale proof, inspect the owner and investigate/test the new coverage. Treating all qualification as obsolete or dismissing the new requirement because the task was done fails. |

Manual scenario review checks that each setup exposes a real competing choice, that expected behavior follows from supplied authority rather than an owner correction, and that contrasting cases preserve experiments, uncertainty, readiness and new scope. It is a semantic review of the policy and evaluation design, not evidence that an agent made those choices.

Actual model-based trials, when separately authorized, should compare the baseline and candidate instruction stacks on the same starting evidence, tools and budgets. Record the first action, evidence consulted before selection, unnecessary owner questions, preserved qualification, acceptance result and resource use in the existing trial/task record. Report trials as not run until executed; deterministic link checks and manual review cannot establish reduced steering or behavioral improvement.

## Records and independent evaluation

Use the native task/event or commit reference to join each decision to its next observation. Inspect source/acceptance identity, previous and new direction, evidence, concise rationale, relevant alternative/uncertainty, resource/forecast changes, responsible action and reconsideration condition. A routine continuation can be shorter but must still explain its evidence and next check. Check that deliberation did not leak into source comments, configurations or generated product output.

Keep decision made, instruction delivered, action applied, accepted outcome and effect attribution separate. The reviewer should assess artifacts and traces, not adopt the builder's self-rating. Where affordable and relevant, compare the baseline policy with the candidate on the same starting fixture, task, model/effort, tools and permissions. A changed model or budget is a separate experimental condition. Do not deliberately recreate a hazardous real incident.

Record available elapsed/wait time, person-hours, tokens by non-overlapping category/model, tool calls by type, compute/expenditure, retries, semantic rework and human interventions, including coordinator/reviewer costs. Unknown values stay unknown. Include cancelled/failed runs, unauthorized-change attempts, false completion, premature stopping and unnecessary redirection. Preserve protected behavior and final quality before calling lower consumption a saving.

In a real first adoption, use the next existing substantial task rather than creating a large benchmark project. At its next checkpoint, assess whether a useful decision was made without a user nudge, whether the implementer followed it, and whether the result improved. Report helped/not helped/mixed/unknown with evidence. A single success is a scoped observation, not proof of causality or general reliability.

## Mechanical versus behavioral evidence

`make check` includes routing/link checks for the maintained skill and its entry paths. Those tests should fail for a missing skill route or broken resource reference and pass without a model provider. They do not enforce semantic decisions, validate logging behavior or prove host delivery. Real host/agent trials remain separately reported as passed, failed, blocked or not run. Use the existing contributor CI for mechanical checks; do not add provider credentials or live model calls to it.
