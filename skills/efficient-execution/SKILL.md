---
name: efficient-execution
description: Use when executing long, repository-heavy or tool-heavy engineering work where repeated model work, noisy context, unnecessary fan-out, or broad revalidation may materially increase cost or wall time.
---

# Efficient execution

1. **Preserve the outcome.** Keep the requested scope, acceptance, evidence, permissions, and quality. For broad transformations, map the requested scope to owned deliverables; structural success is not substantive acceptance.

2. **Route substantial batches before consuming them.** Choose the cheapest adequate executor: deterministic tool, bounded worker, orchestrator, or capability-selected specialist. The coordinator need not be the strongest model. Keep small work local; use exact tools for exact work. Route a bounded coupled decision to a stronger available specialist when it is likely to prevent material rework, then return explicit implementation and verification to cheaper executors.

3. **Keep context lean.** Retain verbose logs, tool output and captures with the executor; expose status and decisive excerpts or artifact paths first. If a large MCP catalogue repeatedly dominates input, compare direct tools with [progressive schema disclosure](../../docs/local-codex/tooling.md#tool-schema-disclosure), including schema lookups, cache effects, latency and accepted results. Load procedures and evidence only for the current decision. At phase boundaries, update existing task notes with outcomes, decisions, owned changes, evidence paths, blockers and the next action so runtime compaction can preserve continuity. Notes do not themselves remove earlier context.

4. **Reuse valid work.** Treat completed semantic work and deterministic artifacts as cached until an input that can affect them changes. Do not reread, regenerate, or revalidate merely to demonstrate activity.

5. **Validate proportionally.** Run targeted checks after local changes and broader acceptance at integration/final boundaries. Before scaling a repeated assignment, inspect one representative result against the user's actual outcome.

6. **Delegate outcome-sized work, not commands.** Define the outcome and artifact, owned scope, constraints and permissions, authoritative inputs, time/token/variant budget, acceptance surfaces, and stop conditions. Require a compact return: result, scope/revision tested, changed files, checks and status, evidence paths, failures, uncertainty, and remaining acceptance. Keep substantive deliverables complete; handoff brevity must not hide exceptions. Inspect decision-critical evidence and spot-check routine work; reopen or repeat more only for changed inputs, conflicts, unreliable results or required acceptance. Check live model/tool availability before selecting a named tier and record requested/resolved capability when visible; inherited orchestrator models are not evidence of cheaper delegation.

7. **Treat instructions as a costed resource.** If this skill conflicts with other persistent guidance or repeatedly fails under realistic context, fix placement/decision boundaries or escalate enforcement/model capability instead of adding unlimited prose.

8. **Measure only when the decision is uncertain.** For repeatable material tradeoffs, capture `codex exec --json` (or equivalent) usage plus substantive acceptance. Do not claim savings from worker counts, prompt length, or one anecdote.

For routing exceptions and outcome-preserving delegation, read [`docs/local-codex/subagents.md`](../../docs/local-codex/subagents.md). For instruction/context placement and adherence tests, read [`docs/local-codex/prompts-skills-agents.md`](../../docs/local-codex/prompts-skills-agents.md) and [`experiments/instruction-context-adherence.md`](../../experiments/instruction-context-adherence.md) only when that decision is relevant.
