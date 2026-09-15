# Local Codex Efficiency Stack

This methodology optimizes **execution efficiency**, not project methodology.

The task itself is held constant. We change the execution environment, instructions, tools, caching, validation strategy, and delegation policy, then measure whether the same required result was obtained with fewer resources.

## Required capabilities

- a supported Codex CLI authenticated through the intended account or API route
- a local Git checkout
- the project's required dependency and tool versions
- persistent build/index/package caches where safe
- an editor or terminal that exposes the same required CLI environment

Codex CLI provides a useful **measurable execution substrate** because `codex exec --json` emits machine-readable events including per-turn token usage. The editor is optional and replaceable. Measurement is a helper when a choice is uncertain; routine work does not need to become a benchmark.

Start from current Codex defaults. This methodology adds mechanisms around them and proposes overrides only when a concrete workload shows a reason. See [defaults before overrides](../principles/defaults-before-overrides.md).

## Efficiency stack

1. **Warm local environment** — repo, dependencies, compiler caches, services, and tools already available.
2. **Small resident context** — keep cross-cutting instructions compact; inspect what actually loads and do not confuse “fits in the context window” with “is useful to keep resident.”
3. **Progressive disclosure** — use scoped rules, skills, source files, diagnostics, and reference material only when the task needs them. Moving text to another file is not a saving if the harness still force-loads it.
4. **Deterministic indexing** — Git, ripgrep, ctags/LSP/language-native dependency tools before model-driven rediscovery.
5. **Quiet tools** — full output saved to disk; model receives a terse success summary or only the relevant failure excerpts.
6. **Incremental invalidation** — do not repeat expensive semantic work unless inputs affecting that result changed.
7. **Targeted validation** — cheapest relevant checks first; broaden only when justified; one final integration pass.
8. **Observable executor routing** — before a substantial batch, choose exact tooling, a bounded worker, or the orchestrator. Model selection is separate from spawning; inherited orchestrator models are not automatically cheaper workers.
9. **Instruction behavior checks** — when a persistent rule materially affects execution, test the actual behavior under the normal instruction stack and realistic context pressure rather than checking only that the rule exists.
10. **Proportionate instrumentation** — capture useful operational metrics cheaply; add deeper tracing or A/B comparisons only when investigating an uncertain/consequential tradeoff.

For the compact default policy, start with the [agent operating corpus](../agent-corpus/README.md). For instruction placement and evaluation, see [prompts-skills-agents.md](prompts-skills-agents.md) and the [instruction/context adherence protocol](../../experiments/instruction-context-adherence.md).

## What “efficient” means

Do not optimize token count by silently reducing quality. A run is eligible to win only after its acceptance checks are non-inferior to the baseline.

Among qualifying runs, compare:

- total input tokens
- cached input tokens and cache-hit ratio
- output + reasoning output tokens
- model turns
- tool calls and model-visible tool-output volume
- unique vs repeated source reads
- write amplification
- validation duplication
- agent/subagent count
- wall-clock duration
- human interventions/corrections
- final substantive acceptance result

See [benchmarking.md](benchmarking.md).
