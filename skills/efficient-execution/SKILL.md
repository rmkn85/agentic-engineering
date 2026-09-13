---
name: efficient-execution
description: Use when executing long, repository-heavy or tool-heavy engineering work where repeated model work, noisy context, unnecessary fan-out, or broad revalidation may materially increase cost or wall time.
---

# Efficient execution

1. **Preserve the outcome.** Keep the requested scope, acceptance, evidence, permissions, and quality. For broad transformations, map the requested scope to owned deliverables; structural success is not substantive acceptance.

2. **Route substantial batches before consuming them.** Choose the cheapest adequate executor: deterministic tool, bounded worker, or orchestrator. Keep small/tightly coupled work local. Use exact tools for exact work; use smaller workers only where authorized, supported, and sufficiently capable; keep ambiguous synthesis/integration on an adequate orchestrator.

3. **Keep context lean.** Store full logs/evidence outside model context and expose terse status/failure excerpts first. Do not load large procedures/reference material until relevant. A worker can isolate a large temporary working set when the orchestrator only needs its evidence-backed result.

4. **Reuse valid work.** Treat completed semantic work and deterministic artifacts as cached until an input that can affect them changes. Do not reread, regenerate, or revalidate merely to demonstrate activity.

5. **Validate proportionally.** Run targeted checks after local changes and broader acceptance at integration/final boundaries. Before scaling a repeated assignment, inspect one representative result against the user's actual outcome.

6. **Delegate outcome-sized work, not commands.** Give workers bounded scope, acceptance, and a compact return contract: result, source/artifact locations, validation, failures, uncertainty. Do not routinely reread all worker inputs. Record requested/resolved worker tier when visible; inherited orchestrator models are not evidence of cheaper delegation.

7. **Treat instructions as a costed resource.** If this skill conflicts with other persistent guidance or repeatedly fails under realistic context, fix placement/decision boundaries or escalate enforcement/model capability instead of adding unlimited prose.

8. **Measure only when the decision is uncertain.** For repeatable material tradeoffs, capture `codex exec --json` (or equivalent) usage plus substantive acceptance. Do not claim savings from worker counts, prompt length, or one anecdote.

For routing exceptions and outcome-preserving delegation, read [`docs/local-codex/subagents.md`](../../docs/local-codex/subagents.md). For instruction/context placement and adherence tests, read [`docs/local-codex/prompts-skills-agents.md`](../../docs/local-codex/prompts-skills-agents.md) and [`experiments/instruction-context-adherence.md`](../../experiments/instruction-context-adherence.md) only when that decision is relevant.
