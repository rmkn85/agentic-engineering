# Local Codex Efficiency Stack

This methodology optimizes **execution efficiency**, not project methodology.

The task itself is held constant. We change the execution environment, instructions, tools, caching, validation strategy, and delegation policy, then measure whether the same required result was obtained with fewer resources.

## Reference environment

- Linux Mint / Ubuntu-family Linux
- Cursor desktop, including AppImage
- Codex CLI authenticated with ChatGPT or API
- Git repository already cloned locally
- dependencies/build products kept warm where safe

Cursor is the editor. Codex CLI provides a useful **measurable execution substrate** because `codex exec --json` emits machine-readable events including per-turn token usage. Measurement is a helper when a choice is uncertain; routine work does not need to become a benchmark.

Start from current Codex defaults. This methodology adds mechanisms around them and proposes overrides only when a concrete workload shows a reason. See [defaults before overrides](../principles/defaults-before-overrides.md).

## Efficiency stack

1. **Warm local environment** — repo, dependencies, compiler caches, services, and tools already available.
2. **Stable model context** — small durable global instructions; dynamic task data late and on demand.
3. **Progressive disclosure** — `AGENTS.md` for universal operating rules; skills for workflows only when selected; source/logs only when required.
4. **Deterministic indexing** — Git, ripgrep, ctags/LSP/language-native dependency tools before model-driven rediscovery.
5. **Quiet tools** — full output saved to disk; model receives a terse success summary or only the relevant failure excerpts.
6. **Incremental invalidation** — do not repeat expensive semantic work unless inputs affecting that result changed.
7. **Targeted validation** — cheapest relevant checks first; broaden only when justified; one final integration pass.
8. **Cost-aware delegation** — respect sensible platform defaults; explicitly increase or constrain fan-out only for a concrete workload reason.
9. **Proportionate instrumentation** — capture useful operational metrics cheaply; add deeper tracing only when investigating an inefficiency.
10. **A/B evaluation when needed** — use controlled comparisons to resolve non-obvious or consequential choices, not as a prerequisite for every practice.

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
- human interventions
- final acceptance result

See [benchmarking.md](benchmarking.md).
