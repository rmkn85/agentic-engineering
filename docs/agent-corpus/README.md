# Agent operating corpus

This is the **small default corpus** for agents applying Agentic Engineering during ordinary engineering work. It is deliberately compact. Read this page, then load deeper guidance only when the current decision needs it.

Do **not** recursively crawl the repository before starting work. In particular, `references/` is research provenance for maintainers improving this methodology; it is not normal runtime context.

## Execution kernel

1. **Preserve the requested outcome.** Optimize execution, not scope, acceptance criteria, evidence, or quality.
2. **Route substantial batches before consuming them.** Choose the cheapest adequate executor: deterministic tool, bounded worker, or orchestrator. Keep tightly coupled judgment and integration with the orchestrator; do not create fan-out without a concrete benefit.
3. **Treat context as a working set, not an archive.** Keep always-loaded instructions small. Load path-specific rules, skills, references, source files, logs, and tool schemas only when they become relevant.
4. **Use deterministic machinery for deterministic work.** Search, inventory, hashing, formatting, compilation, test execution, filtering, moving, and measurement usually do not need model reasoning.
5. **Reuse valid work.** Cache semantic findings and deterministic artifacts until an input that can affect them changes. Do not reread or revalidate merely to demonstrate activity.
6. **Keep evidence larger than model context.** Persist full logs and source evidence outside the conversation; expose terse status/failure excerpts first and expand only when needed.
7. **Validate at the cheapest useful boundary.** Use targeted checks while iterating and broader acceptance at integration/final boundaries. Structural success is not substantive acceptance.
8. **Measure uncertainty, not everything.** Platform defaults are the baseline. Benchmark consequential or workload-dependent deviations; leave obvious wins and already-good defaults alone.
9. **Leave touched code cheap to model.** A fresh weaker coding model should be able to predict a touched unit's representative behavior from the unit plus a small explicit contract/dependency context. Do not trade local simplicity for hidden coupling or abstraction mazes.

## Context placement rule

Before adding persistent guidance, place it at the lowest-cost layer that can reliably enforce the behavior:

```text
Can deterministic code/config/test enforce it?
  yes -> enforce mechanically; do not spend model context
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
Background, examples, rationale, source material?
  -> searchable documentation/reference loaded on demand
```

Use a separate worker/context when a subtask needs a large temporary working set whose intermediate detail is not useful to the orchestrator.

## Instruction changes are code changes

A rule is useful only if it changes behavior under realistic conditions.

When adding or strengthening an instruction:

- identify the observed failure or uncertainty it addresses;
- establish the baseline behavior when practical;
- add the smallest intervention likely to fix it;
- test the behavior with the normal instruction stack, not only in isolation;
- test under realistic context pressure when overload/interference is plausible;
- remove, scope, or demote instructions that add recurring context without measurable behavioral value;
- escalate to deterministic enforcement or a more capable orchestrator when repeated failures show that more prose is not the answer.

See [instruction/context adherence experiments](../../experiments/instruction-context-adherence.md) when this tradeoff is material.

## Load deeper guidance only when needed

| Decision | Read |
| --- | --- |
| Writing/refactoring source for cheap future agent maintenance | [`../code/agent-legible-code.md`](../code/agent-legible-code.md) |
| Context, prompt, `AGENTS.md`, skills, instruction placement | [`../local-codex/prompts-skills-agents.md`](../local-codex/prompts-skills-agents.md) and [`../principles/context-economics.md`](../principles/context-economics.md) |
| Delegation, workers, model routing, fan-out | [`../local-codex/subagents.md`](../local-codex/subagents.md) |
| Benchmarks and resource comparisons | [`../local-codex/benchmarking.md`](../local-codex/benchmarking.md) |
| Exact local tooling and quiet outputs | [`../local-codex/tooling.md`](../local-codex/tooling.md) |
| Reuse/invalidation | [`../execution/read-once-write-once.md`](../execution/read-once-write-once.md) and [`../execution/caching-and-prefetching.md`](../execution/caching-and-prefetching.md) |
| Model/surface/pool choice | [`../execution/surface-and-pool-selection.md`](../execution/surface-and-pool-selection.md) |
| Evidence maturity and claims | [`../evidence/practice-lifecycle.md`](../evidence/practice-lifecycle.md) |

## References boundary

Read `references/` only when the task is to improve Agentic Engineering itself, audit provenance, compare external frameworks, revisit a design decision, or investigate a behavior not explained by the operational docs. Those files preserve research depth without taxing ordinary agent runs.
