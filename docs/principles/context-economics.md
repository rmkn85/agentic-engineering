# Context economics

Model context is a **working set, not an archive**. Information can be valuable and still be harmful when it is permanently resident in every model call.

Optimize for the **smallest reliably sufficient working context** for the required behavior and outcome — not the shortest prompt and not the largest context that fits.

## Context has two costs

A token can impose both:

1. **resource cost** — input usage, latency, cache/storage transfer, compaction pressure;
2. **attention/behavior cost** — competition with the current task, source code, evidence, tools, and other instructions.

A large nominal context window does not prove that every resident instruction will be used reliably. Test important behavior under representative context pressure.

## Residency before wording

Before polishing an instruction, decide whether it should be resident at all.

Use the lowest-cost reliable layer:

```text
Can deterministic code/config/test enforce it?
  yes -> enforce mechanically
  no
   |
Needed for nearly every task?
  yes -> concise always-loaded instruction
  no
   |
Predictably tied to files/directories?
  yes -> path-scoped/nested instruction
  no
   |
Reusable workflow needed only sometimes?
  yes -> skill/on-demand procedure
  no
   |
Background/rationale/examples/provenance?
  -> searchable reference loaded on demand
```

If a subtask needs a large temporary working set but the orchestrator only needs the conclusion, a separate worker/context can quarantine the intermediate detail. Account for the extra model call and coordination cost; isolation is not automatically cheaper.

## Stable before volatile

For context that really belongs in the same working set, keep durable material conceptually ahead of changing task state:

1. system and repository invariants;
2. architecture and stable constraints;
3. stable repository metadata;
4. current task and acceptance;
5. current files, diagnostics, and transient evidence.

Stable prefixes can improve cache reuse, but prompt caching is an **accounting/latency optimization**, not an attention optimization: cached tokens still enter model context.

## Instructions must earn recurring residency

A persistent rule is recurring input. Ask:

- What observed failure or decision does it address?
- How often is that decision relevant?
- What observable behavior changes when the rule is present?
- Does it still work inside the normal complete instruction stack?
- Could the same behavior be scoped, retrieved, or enforced mechanically?
- What happens under realistic context pressure?

Individually sensible rules can interfere. For example, “use smaller workers for independent work,” “avoid unnecessary delegation,” “prefer local execution,” and “minimize coordination overhead” can combine into an unintended “do everything yourself” policy for a thin model. Resolve the decision rule rather than adding synonyms.

Use [`experiments/instruction-context-adherence.md`](../../experiments/instruction-context-adherence.md) when the tradeoff is material.

## Compress semantics, not truth

After a unit has been fully inspected, later work often needs only compact state such as:

- content hash/version;
- ownership/destination;
- public symbols or interface facts;
- dependencies;
- transformation decision;
- validation result;
- invalidation state.

Keep the authoritative source available and reopen it when invalidated or contradicted. Do not repeatedly summarize summaries until useful exceptions disappear. Move depth out of the hot working set instead of deleting it.

This repository applies the same rule to its own knowledge: normal agents use the focused [`docs/agent-corpus/`](../agent-corpus/README.md), while external research/provenance lives under [`references/`](../../references/README.md).

## Tool output is context too

Logs stored on disk are cheap compared with logs copied into model context. Prefer terse status and failure excerpts, then targeted expansion only when needed.

Tool definitions can also consume context. Depending on the harness, tool/MCP names, descriptions, schemas, skill metadata, memory, output styles, and other injected state may be present before the user provides any task. A tiny `AGENTS.md` does not imply a tiny startup context.

Use native harness context inspection when available. [`tools/instruction-footprint.py`](../../tools/instruction-footprint.py) inventories common file-based instruction sources, but it is deliberately only a lower-bound proxy for runtime context.

## Why a delegated task can still grow

Worker isolation only saves the intermediate material that stays outside the parent's context. The parent still carries its startup instructions/tool definitions, its own reads and browser actions, worker messages, integration checks and the ongoing conversation. Do not attribute a large context number to worker transcripts without inspecting what the host actually returns. Context occupancy and total usage across agents are different measurements; do not invent a per-category breakdown when the runtime does not expose one.

Keep complete logs and captures with their executor and use the [compact handoff contract](../local-codex/subagents.md#handoff-and-retained-context). Saving a log after already printing it does not undo the context cost. Nor does producing a shorter summary remove prior messages by itself.

At a phase boundary, refresh the task's existing continuation notes and use host-supported compaction when available. Preserve scope, decisions, tested revision/environment, evidence references, blockers and the next action. After compaction, distinguish retained summaries from original evidence; reread exact source when the next decision requires it. Compaction changes the available context, not the files or the acceptance state. Keep the full substantive deliverable outside the compressed working summary.

## Output can dominate

When a workflow requires a model to regenerate large amounts of source, output may dominate cost. Avoid regenerating unchanged bytes merely to prove they were considered. If intentional preservation is required, record an explicit retain/move decision and use deterministic movement when possible.

## Audit loop

When context appears too large or adherence degrades:

1. inspect what actually loads;
2. identify always-resident material;
3. remove duplication;
4. move scoped procedures/references out of the global layer;
5. test important rules with the normal stack;
6. run an ablation or pressure test only where the value remains uncertain;
7. escalate repeated non-adherence to deterministic enforcement or a more capable orchestrator instead of growing instructions indefinitely.

The target is not a universal token budget. The target is **high behavioral value per recurring context token while preserving the required result**.
