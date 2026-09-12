# Agentic Engineering

Practical, measurable techniques for accomplishing the **same agentic engineering task** with less model usage, less wall-clock time, less repeated computation, less human attention, and fewer retries.

This repository does **not** prescribe product architecture, project management, task decomposition, or what software should be built. The task, intended result, and quality bar are inputs. The subject here is how to execute that same work more efficiently.

## Optimization invariant

A claimed improvement is useful only if it preserves the required outcome and quality:

> same task + same success criteria + same quality bar → less total resource consumption

Resources include model input/output/reasoning tokens, cached-token ratio, quota/credits, tool-output context, model turns, wall time, local/cloud compute, repeated file reads/writes, repeated validation, retries, collisions, and human intervention.

## Core stance

Treat the model as the expensive probabilistic component inside a mostly deterministic engineering system.

- Spend model inference on judgment that actually requires it.
- Use deterministic local tools for exact search, indexing, hashing, moving, formatting, compilation, testing, filtering, and measurement.
- Cache semantic work and deterministic work independently.
- Keep model-visible output short; keep full evidence on disk and fetch it only when needed.
- Before substantial work, apply the [executor-routing checkpoint](docs/local-codex/subagents.md#executor-routing-checkpoint): choose exact tools, an authorized sufficiently capable smaller worker, or the orchestrator, and make that choice observable before the batch starts.
- Choose **model capability, execution surface, and usage pool independently**; the same model can have very different system economics in Chat, Work, local Codex, cloud Codex, or API use.
- Treat current platform defaults as a strong baseline; do not tune merely because a knob exists.
- Prefer mechanically favorable optimizations such as valid caching, warm deterministic state, concise model-visible logs, and exact local tools.
- Deviate from defaults only for a concrete reason; benchmark only when the tradeoff is non-obvious, consequential, or workload-dependent.
- Treat explicit large-scale orchestration and fan-out as costed choices, not signals of sophistication.

## Start here

The first concrete methodology is the [Local Codex Efficiency Stack](docs/local-codex/README.md), designed for Linux Mint + Cursor (including AppImage) but largely editor- and model-independent.

Before choosing that surface for a task, see [execution surfaces and usage pools](docs/execution/surface-and-pool-selection.md): Chat, Work, local Codex, cloud Codex, and API usage can offer similar model capability while differing substantially in repository state, tool affordances, and which allowance pays for the work.

The local stack includes:

- [workstation setup](docs/local-codex/linux-mint-cursor-appimage.md)
- [context and cache economics](docs/local-codex/context-caching.md)
- [deterministic repo tooling and concise logs](docs/local-codex/tooling.md)
- [prompt / AGENTS.md / skill discipline](docs/local-codex/prompts-skills-agents.md)
- [cost-aware delegation and subagent economics](docs/local-codex/subagents.md)
- [defaults before overrides](docs/principles/defaults-before-overrides.md)
- [measurement and benchmarking as decision aids](docs/local-codex/benchmarking.md)
- [optional experiment matrix](experiments/local-codex-efficiency-matrix.md)
- [sample Codex config](configs/codex/efficient-local.config.toml)
- [minimal global AGENTS.md](templates/global-AGENTS-efficient.md)
- [optional efficiency skill](skills/efficient-execution/SKILL.md)
- tools for [quiet command execution](tools/quiet-run), [repo inventory](tools/repo-index.py), and [Codex JSONL benchmark capture](tools/codex-bench.py)

## Repository map

- `docs/principles/` — durable concepts
- `docs/execution/` — execution mechanisms and surface/resource selection
- `docs/local-codex/` — concrete local Codex efficiency methodology
- `docs/collaboration/` — concurrency and ownership
- `docs/measurement/` — reusable metrics
- `docs/evidence/` — how observations become shared practices
- `experiments/` — controlled comparisons
- `configs/` — conservative configuration examples
- `templates/` — small reusable instruction templates
- `skills/` — optional on-demand workflows
- `tools/` — deterministic helpers that keep work out of the LLM

## Evidence rule

Guidance is categorized as one of:

1. **documented behavior** — supported by current vendor/tool documentation;
2. **measured result** — observed directly, with a controlled benchmark when one is useful;
3. **engineering hypothesis** — plausible and worth testing, but not yet proven.

Avoid turning a local anecdote into a universal rule. Measurement should resolve uncertainty, not become ceremony. If a current default already works well, leave it alone until there is a reason to change it.
