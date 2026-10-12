# Checkpoint-driven delivery steering

Status: engineering policy and testable hypothesis. The [steering-delivery skill](../../skills/steering-delivery/SKILL.md) is the operational procedure. This guide supplies examples, traceability and adoption detail; ordinary agents need not load it at every checkpoint.

## Ownership without another management layer

The existing coordinator is the Technical Delivery Lead. It owns the next authorized engineering decision and its execution. [Efficient execution](../../skills/efficient-execution/SKILL.md) selects how to perform work economically; steering decides whether that work and approach still address the authorized outcome. [Direct delivery](direct-delivery.md) supplies the integrated result and acceptance path. [Bounded recovery](bounded-recovery.md) supplies safe local repair; a routine command failure does not justify a global replan.

The user delegates ordinary engineering choices, not authority to rewrite the user contract. The lead can reorder implementation, simplify a mechanism, assign suitable expertise, run a useful experiment and include necessary integration/repair without routine approval. Preserve requirements, priorities, quality, permissions, protected data and aggregate resource limits. A required outcome may need more supporting work than originally predicted; optional product expansion remains a separate decision. An updated estimate never renews an exhausted ceiling.

When evidence supports multiple materially different product outcomes or an action exceeds authority, identify that decision precisely and continue independent work. A role title, reviewer agreement or guessed answer from the user grants no additional permission.

## Distinguish consumption, progress and commitments

Use available native information in its original units. Do not combine tokens, commits and hours into a universal age or productivity score.

| Dimension | Relevant evidence |
| --- | --- |
| Elapsed and waiting | Wall time, queue/approval/dependency delays; distinguish active coordination from waiting for it |
| Human effort and continuity | Person-hours by available role/activity, scattered sessions, handoffs, context reconstruction and interventions; never infer effort from Git timestamps |
| Agent and infrastructure use | Available input/cached/output/reasoning tokens by model, calls by operation, retries, execution/CI/compute time and charges; avoid overlapping token categories |
| Economics | Attributable labor, API/compute/tool/contractor expenditure and committed future costs; identify shared allocation assumptions and opportunity cost separately, without double counting |
| Change and rework | Repeated edits to the same behavior, patch/revert loops, recurring failures, abandoned hypotheses and widening edit/dependency scope; exclude mechanical formatting/generated churn when interpreting semantics |
| Verified progress | Accepted behavior retained, blockers removed, reproducible findings and decisions changed; distinguish implemented, verified, integrated and delivered |
| New obligations | Required versus optional scope, maintenance/operational burdens, coupling and new failure modes |

Keep cumulative consumption and the delta since the previous checkpoint. Splitting a task, respawning or handing off cannot erase its history; avoid counting shared work twice. More parallel workers can change elapsed time without reducing total effort. Missing usage, cost or activity data is unknown, not zero.

Repeated changes can be sound test-driven development. Negative experiments can be valuable. The warning is repeated investment without a supported improvement or decision-relevant finding, especially when the same falsified premise survives and new obligations accumulate. Count the reviewer itself in the cost. Do not reward small diffs, cheap models, many commits or premature cancellation as substitutes for the required result.

Forecast the remaining work from the current state and relevant local experience. Separate the next useful experiment/milestone from total completion, active effort from waiting, and an uncertain forecast from an authorized allocation. Use ranges and explicit assumptions when justified; do not invent calibrated probabilities or apply a Pareto formula to arbitrary resource counters. No universal number of days, tokens or fixes determines whether to stop.

## Records belong to tasks or commit messages

Use the project's existing task history, including its established task/handoff file where that is the native record, or a meaningful implementation commit's message body. Select the available route once. Do not add a telemetry service, another task database, a per-checkpoint JSON file, source comments or configuration fields for managerial deliberation. Reusable policy and neutral examples belong in this methodology; project-specific decisions do not.

A record is a concise decision explanation, not an internal reasoning transcript. State what was observed, what it implies for the decision, the important alternative/tradeoff, uncertainty and the action. Link the exact candidate and decisive test/trace/task evidence. Record negative and unchanged decisions too. Routine CONTINUE decisions can be one line with an evidence reference, rationale and next check; material choices use the existing task fields or a compact body such as:

```text
Steering: <native task/event reference> | <event/time> | <source revision>
Previous direction: <what was going to happen>
Evidence: <verified gain, controlling gap, counterevidence; stable references>
Decision and rationale: <CONTINUE/STEER/BLOCKED/COMPLETE; why>
Alternative and uncertainty: <material competing choice; what is still unknown>
Investment/forecast: <observed delta and cumulative use when available;
                      revised remaining work; unchanged authority/ceiling>
Action: <old next action -> new action; owner; affected workers>
Next check: <expected result and observation that changes the decision>
Follow-up: <pending; later task entry/commit records adoption and actual effect>
```

Append the follow-up through normal task history or the next coherent commit, referencing the original decision. Preserve the original rationale rather than rewriting it with hindsight. Report adoption separately from effect: a worker may follow the instruction without improving the outcome. Use helped, not helped, mixed or unknown with evidence; one favorable sequence is not causal proof of general savings. Reassess or reverse an unhelpful steering decision instead of defending the overseer's own sunk cost.

If several checkpoint events share unchanged evidence, reference the same decision rather than copying it. A decision-record-only update does not trigger another review. Do not delay a needed recoverable checkpoint or manufacture empty/log-only commits to satisfy record cadence. If no authorized durable route is available, preserve the explanation in the current task response, state the persistence limitation and use it at the next available authorized checkpoint. Never claim a record was saved when it was not.

Keep private evidence with its actual owner. Redact secrets and unnecessary personal information, and retain raw diagnostics only through existing authorized evidence retention. Record filenames/commands are evidence references, not permission to fetch private resources or perform unrelated writes.

## Contrasting decisions

**STEER, not another patch.** A cancellation failure survives repeated retry-timing changes. The lead records that those patches did not address the publication invariant, preserves working code, and redirects the owner to trace cancellation/publication ownership and test the boundary. It does not assert an unobserved root cause. The follow-up records whether the trace ran and whether the requirement now passes.

**CONTINUE, not automatic cancellation.** Reproducible experiments eliminate distinct explanations and isolate the remaining uncertainty. Record the findings and authorize the next bounded step within existing limits, even when the original estimate was wrong. More active effort can be justified; expanded product scope does not follow automatically.

**BLOCKED, not invented busywork.** A validated change awaits external approval. Record the approval owner and outstanding gate, separate waiting from engineering effort, and continue independent authorized work. Do not modify correct code to appear active or silently waive approval.

**COMPLETE, not scope drift.** Required integrated acceptance holds. Record evidence and finish; do not introduce another refinement solely to keep the lead or worker busy.

## Activate in an existing task

Use [portable routing](../adoption/overlays.md#portable-skill-routing) and the existing reviewed-snapshot migration route. Preserve local adaptations, dirty work, active owners and the current task's resources. Bind the new skill beside efficient-execution; do not copy its full body into every startup layer or invent a host configuration key.

After an authorized reload, the coordinator should read the updated entry/corpus and skill, record the adopted revision in the existing task, reconcile the current goal/evidence, run one initial steering checkpoint and continue. Deliver material updates to already-running workers explicitly through supported controls; changing a file does not prove their contexts changed. If a host cannot refresh an active session, use its normal continuation/handoff path and report that boundary.

Where supported, use the existing iteration/continuation callbacks to invoke the review before the next batch. A Git hook alone cannot reliably inspect an agent's task context and does not cover uncommitted loops, pauses or resumptions. This repository introduces no background daemon or global hook. A skill is an instruction, not a runtime guarantee; distinguish available, delivered, loaded, applied and effective in adoption evidence.

## Evaluate the change

Run the [delivery-steering trials](../../experiments/delivery-steering.md) under the [normal instruction-adherence protocol](../../experiments/instruction-context-adherence.md). Compare accepted outcomes, repeated ineffective work, user corrections, unauthorized changes and total resource use including oversight. Navigation tests establish integration only. Keep or revise the policy based on actual delivery; remove duplicative guidance if supported behavior can be retained more cheaply. Do not make exhaustive telemetry or a statistical forecasting platform a prerequisite for trying one useful checkpoint.
