# Agent operating corpus

Read this **default operating corpus**, then load deeper guidance only for the current decision.

Do **not** recursively crawl the repository. `references/` is methodology research/provenance, not ordinary runtime context.

## Execution kernel

1. **Preserve the outcome and inherited constraints.** Separate the change from deferred checks/refinement. Narrower verification is not permission to remove a product invariant; an explicit product-scope change is different.
2. **Route substantial batches before consuming them.** Choose the cheapest adequate executor: deterministic tool, bounded worker, orchestrator, or capability-selected specialist. A low-cost coordinator may route one bounded coupled decision to a stronger available specialist, then return implementation and verification to cheaper executors. Do not create fan-out without a concrete benefit.
3. **Treat context as a working set, not an archive.** Keep always-loaded instructions small. Load path-specific rules, skills, references, source files, logs, and tool schemas only when they become relevant.
4. **Use deterministic machinery for deterministic work.** Search, inventory, hashing, formatting, compilation, test execution, filtering, moving, and measurement usually do not need model reasoning.
5. **Reuse valid work.** Cache semantic findings and deterministic artifacts until an input that can affect them changes. Do not reread or revalidate merely to demonstrate activity.
6. **Keep logs out of coordinator context.** Retain evidence on disk; workers/tools return status, decisions, and paths. Inspect only decision-critical excerpts; consumed logs burden later turns.
7. **Construct, then challenge.** Identify what preserves the affected property in the real consumer and the next ordinary change. Probe one consequential assumption outside the happy path; use targeted checks now and appropriate integration later. Tests do not supply the preserving mechanism.
8. **Measure uncertainty, not everything.** Keep good defaults. For consequential decisions retain the practice/revision, trigger, action and native evidence in the existing run record. Separate reported use from observed behavior; leave unknown measurements unknown.
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

Judge instructions by behavior in the normal stack.

Identify the failure, preserve a practical baseline, and make the smallest intervention. Test actual behavior under normal instructions and relevant context pressure. Remove, scope or demote recurring prose without demonstrated benefit. Repeated failure calls for better placement, deterministic enforcement or adequate capability—not more synonyms.

See [instruction/context adherence experiments](../../experiments/instruction-context-adherence.md) when this tradeoff is material.

## Load deeper guidance only when needed

| Decision | Read |
| --- | --- |
| Narrow scope, structural preservation, uncertain or irreversible conditions | [`../principles/defaults-before-overrides.md`](../principles/defaults-before-overrides.md) |
| Writing/refactoring source for cheap future agent maintenance | [`../code/agent-legible-code.md`](../code/agent-legible-code.md) |
| Bounded complexity review, cross-file relationship discovery, or external-tool usage/effect evidence | [`../../skills/using-external-practices/SKILL.md`](../../skills/using-external-practices/SKILL.md) |
| Designing logging/telemetry/crash evidence/self-monitoring | [`../runtime/diagnostic-feedback.md`](../runtime/diagnostic-feedback.md) and, for dead-target evidence, [`../runtime/postmortem-bundles.md`](../runtime/postmortem-bundles.md) |
| Establishing browser/native E2E test capability or choosing proof surfaces | [`../runtime/e2e-readiness.md`](../runtime/e2e-readiness.md) |
| Diagnosing a crash/failure/noisy runtime artifact | use [`../../skills/diagnosing-runtime-failure/SKILL.md`](../../skills/diagnosing-runtime-failure/SKILL.md) and follow the smallest diagnostic artifact first |
| Context, prompt, `AGENTS.md`, skills, instruction placement | [`../local-codex/prompts-skills-agents.md`](../local-codex/prompts-skills-agents.md) and [`../principles/context-economics.md`](../principles/context-economics.md) |
| Delegation, workers, model routing, fan-out | [`../local-codex/subagents.md`](../local-codex/subagents.md) |
| Benchmarks and resource comparisons | [`../local-codex/benchmarking.md`](../local-codex/benchmarking.md) |
| Exact local tooling and quiet outputs | [`../local-codex/tooling.md`](../local-codex/tooling.md) |
| Reuse/invalidation | [`../execution/read-once-write-once.md`](../execution/read-once-write-once.md) and [`../execution/caching-and-prefetching.md`](../execution/caching-and-prefetching.md) |
| Model/surface/pool choice, including costly coupled synthesis versus bounded execution | [`../execution/surface-and-pool-selection.md`](../execution/surface-and-pool-selection.md) |
| Evidence maturity and claims | [`../evidence/practice-lifecycle.md`](../evidence/practice-lifecycle.md) |

## References boundary

Read `references/` only when the task is to improve Agentic Engineering itself, audit provenance, compare external frameworks, revisit a design decision, or investigate a behavior not explained by the operational docs. Those files preserve research depth without taxing ordinary agent runs.
