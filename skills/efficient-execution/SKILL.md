---
name: efficient-execution
description: Execute long, repository-heavy or tool-heavy engineering tasks with minimal redundant model work, noisy context, repeated validation, and unnecessary agent fan-out while preserving the requested result and quality.
---

1. Establish the required outcome and acceptance checks; do not reduce them to save tokens.
2. Before a substantial reading, implementation, or validation batch, choose its executor: deterministic tool, bounded worker, or orchestrator. Use exact tools for mechanical work. A small known edit or direct command stays local; do not spawn a worker merely to satisfy this checkpoint. When delegation is available and authorized, assign independent extraction, straightforward edit batches, and validation/triage to a sufficiently capable smaller model where permitted; keep synthesis, ambiguous decisions, and integration with the orchestrator. Record the choice and concrete reason in the existing plan or a short update, not a new ledger. Do this before consuming the batch, not after a user notices under-delegation.
3. Keep full logs/evidence on disk and expose terse summaries to model context; inspect detailed excerpts only when needed.
4. Treat completed semantic work as cached until an input that can affect it changes. Record enough state to know what is valid or dirty.
5. Use targeted validation after local changes; perform broader validation at integration boundaries and final completion, not reflexively after every edit.
6. Delegate an outcome-sized batch, not every file read or shell command. Give each worker a bounded question/write scope, acceptance checks, and a compact evidence return contract (findings, file/line or artifact references, failures, uncertainty). Select and record the model/effort when permitted: an inherited orchestrator model is not a cheaper-model optimization. If a requested tier is unavailable, disclose the fallback. Continue useful non-overlapping work instead of waiting or duplicating the worker's inspection. Review decision-bearing evidence and spot-check routine results; do not routinely reread the entire worker input. Reassess routing at integration boundaries or on actual cost, quality, or coordination failures; do not impose a fixed fan-out or benchmark every obvious assignment.
7. Prefer stable instructions/context and on-demand references. Do not repeat large task descriptions or repo summaries already available in files.
8. For repeatable work, capture `codex exec --json` metrics and compare against the applicable baseline.

For delegation tradeoffs, exception cases, and behavioral acceptance, use [cost-aware delegation](../../docs/local-codex/subagents.md). Direct reads required by higher-priority instructions remain the orchestrator's responsibility. Smaller workers must not weaken source coverage, privacy boundaries, permissions, or acceptance; escalate ambiguity rather than guessing.
