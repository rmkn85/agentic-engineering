# Instruction and context adherence

Status: regression and experiment protocol. The goal is to discover the **smallest reliably sufficient instruction/context configuration**, not the shortest prompt and not the most comprehensive manual.

Use this when an instruction changes important behavior, when a lightweight agent appears to ignore guidance, when the instruction stack is growing, or when context pressure/interference is a plausible cause of failures.

## Principle

A written rule is not evidence that the agent will execute it. A concise rule is not automatically better either. Evaluate the behavior produced by the **real instruction stack under representative context pressure**.

### Launch delivery is a separate variable

Observed failure class: a worker started in a parent directory containing multiple repositories can miss the child repository's instructions. The child instruction text may be present on disk, and a coached worker read may succeed, while automatic startup delivery was absent. A stale parent session can create the same misleading appearance: changing the cwd or editing instructions does not prove that an already-built session chain changed. The current documented discovery behavior is a per-run walk from project root to cwd, with no child-directory traversal; verify the [official source](https://learn.chatgpt.com/docs/agent-configuration/agents-md) (reviewed 2026-09-13) when platform behavior matters.

Add a launch-delivery check to the smallest relevant experiment: capture the actual launch cwd and the instruction sources delivered before work begins. If child guidance is absent, test concise shared discovery instructions at the workspace root, an actual launch from the child root, or the runtime's supported instruction-loading mechanism. A fresh, uncoached behavioral acceptance case must then exercise the rule and retain the actual trace plus acceptance result. Include at least one stale-session or parent-cwd case, unfamiliar questions, and a negative case where the child rule should not apply. A coached file read is a diagnostic condition, not startup-delivery evidence.

Separate retrieval/output tokens used by the run from the total-token budget (including supplied context and any runtime accounting). Report both when available; do not call either a measured saving without a non-inferior outcome and comparable runs. Do not claim universal guaranteed model compliance or measured savings from this protocol alone.

## RED → GREEN → REFACTOR for instructions

1. **RED — establish the failure.** Run the representative task without the proposed new instruction or with the current baseline. Record the actual execution trace and acceptance result. If the behavior already works reliably, first question whether another persistent rule is needed.
2. **GREEN — smallest intervention.** Add the smallest instruction, scoping change, skill, or deterministic mechanism expected to fix the observed failure. Repeat the same scenario.
3. **REFACTOR — reduce recurring cost.** Try moving explanation/reference depth out of the always-loaded layer, removing redundancy, or replacing prose with deterministic enforcement. Keep the behavior green.

Do not manufacture a failing baseline when the task is unsafe or costly merely to satisfy the protocol. Existing observed failures can serve as the baseline when recorded clearly.

## Core matrix

For a consequential rule or instruction group, select the smallest subset of these cases that resolves the decision:

| Variant | Question |
| --- | --- |
| Rule absent | Was the rule needed? |
| Rule alone | Can the model understand/apply it in isolation? |
| Normal full stack | Does it survive interaction with the real instructions? |
| Scoped/on-demand | Can the same behavior be achieved without permanent residency? |
| Deterministic enforcement | Can model context be removed entirely for this constraint? |
| Normal task pressure | Does it work in a realistic repository/task? |
| High context pressure | Does adherence collapse when files, diagnostics, tools, or history grow? |
| Thinner model | What is the cheapest tier that remains sufficiently capable and compliant? |
| Stronger model | Is the failure instruction/context design or control capacity? |

Do **not** run the full Cartesian product by default. Stop once the operating decision is clear.

## Pressure scenarios

A useful pressure test combines legitimate competing incentives rather than asking the model to repeat a rule.

Example: executor routing

> Reconcile a corpus with several independent source groups while an immediate tightly coupled semantic conflict also needs resolution. Exact inventory can be scripted. Smaller workers are available. Preserve all requested substance and finish efficiently.

Acceptance should inspect the execution trace:

- exact inventory uses deterministic tooling;
- independent extraction is considered before the orchestrator consumes all of it;
- tightly coupled conflict/integration remains with an adequate orchestrator;
- worker results contain evidence locations and uncertainty;
- no ritual fan-out for tiny commands;
- the original substantive outcome still passes.

A response that merely says “I will delegate efficiently” but then reads every routine source itself fails.

### Portable routing and handoff check

On a fresh host/task, try one representative evidence-producing assignment through the normal router, without pasting the skill body into the prompt. Check that the agent finds the actual skill path, reads applicable repository instructions and retains detailed evidence outside its return message. The return must identify tested scope/revision, verdict, checks, limitations and retrievable evidence. Give the orchestrator a real unresolved claim: it should inspect the relevant evidence or request a targeted follow-up, while leaving unrelated logs unopened. A missing visual/input check must remain incomplete even if a command exited successfully.

Also check one small task that should not activate the workflow, and an absent optional skill checkout. Keep startup delivery, behavior and resource measurements separate. After compaction, verify that a continuation uses the recorded next action and preserves unfinished acceptance rather than restarting completed work or declaring success. Run this subset when portability or retention is the uncertainty; it is not a required matrix for every wording edit.

## Context-pressure levels

Use workload-specific fixtures rather than arbitrary token counts:

### Low

- core instruction only;
- small task;
- few tools/files.

Purpose: verify the rule is understandable.

### Representative

- normal global + repository instructions;
- expected skills/tool set;
- realistic task files and diagnostics.

Purpose: estimate production behavior.

### High

- same required outcome;
- larger but still legitimate source/tool working set;
- multiple relevant instructions with potential tension.

Purpose: detect instruction interference, attention dilution, or model-tier limits before the nominal context window is exhausted.

Do not pad context with irrelevant junk merely to create a dramatic failure. Pressure should resemble real work.

## What to record

### Outcome

- substantive acceptance pass/fail;
- structural checks separately;
- omitted scope, contradictions, or regressions;
- human correction required.

### Behavior

- first meaningful executor/model choices;
- relevant instruction violations or justified deviations;
- duplicate reads/retries;
- unnecessary narration/planning/approvals;
- unnecessary fan-out or failure to split independent work;
- whether a worker inherited an expensive model unexpectedly;
- whether the orchestrator replayed worker input and erased context savings.

### Resources

Where the harness exposes them:

- total input tokens;
- cached input tokens;
- fresh input tokens;
- output/reasoning tokens;
- turns;
- tool/model calls;
- wall time;
- retries and rework;
- human intervention.

Only claim a resource saving when outcome/quality is non-inferior.

## Instruction ablation

When the always-loaded stack grows, test groups rather than arguing from prose quality.

Example groups:

```text
A outcome/quality invariant
B executor routing
C context/log discipline
D cache/invalidation discipline
E validation discipline
F explanatory rationale/examples
```

Useful comparisons might be `ABCDEF` vs `ABCDE`, then remove or scope another group only if the first result leaves uncertainty. Avoid exhaustive combinatorial testing unless the interaction itself is the research question.

For every permanently resident group, ask:

> What observable behavior or outcome becomes worse when this is absent?

If representative runs show no benefit, demote it to scoped/on-demand/reference material or remove it. Lack of measured benefit is not proof of zero value; record uncertainty rather than claiming uselessness.

## Instruction interference

Test important rules inside the **normal complete stack**. Individually sensible instructions can combine into an unintended policy.

Example tension:

- use smaller workers for suitable independent work;
- avoid unnecessary delegation;
- prefer local execution;
- minimize coordination overhead.

A thin model may resolve the stack as “keep everything local.” Fix the ambiguity at the decision rule or routing boundary rather than piling on synonyms for the original instruction.

## Context footprint

File size is only a lower-bound proxy for runtime context. Harnesses can also inject system prompts, memory, skill metadata/bodies, tool/MCP metadata, schemas, output styles, and other state.

Use native inspection when available. The repository's deterministic [`tools/instruction-footprint.py`](../tools/instruction-footprint.py) inventories common file-based sources but cannot see hidden/runtime context by itself.

Track the **controllable recurring context** separately from task-specific working data. Prompt caching may reduce billing/latency for repeated prefixes, but cached tokens still occupy model input and therefore do not eliminate instruction interference or attention cost.

## Escalation ladder

Repeated non-adherence should not automatically grow `AGENTS.md`:

1. platform/default behavior;
2. minimal explicit instruction;
3. better placement/trigger/scoping;
4. behavioral regression test;
5. deterministic harness enforcement when feasible;
6. more capable orchestrator when the workload exceeds the thinner model's reliable control capacity.

The correct endpoint may be removing an instruction because upstream/default behavior improved.

## Relationship to delegation adherence

Historical executor/model-routing observations are retained in [`references/delegation-adherence-2026-09.md`](../references/delegation-adherence-2026-09.md). This document is the active protocol for testing delegation and other persistent instruction/context decisions.
