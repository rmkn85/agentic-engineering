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
- Treat **instruction/context residency** as a resource decision: always-loaded rules must earn their recurring context cost; use scoped rules, on-demand skills, isolated worker context, or retrievable references when they are sufficient.
- Treat **source code as future agent context**: a fresh weaker coding model should be able to build a useful bounded mental model of touched code from the unit plus a small explicit contract/dependency context.
- Treat **runtime/build/test evidence as future agent context**: emit compact structured diagnostic state first, preserve deeper evidence behind stable references, and support offline postmortem navigation when the target is dead.
- Choose **model capability, execution surface, and usage pool independently**; the same model can have very different system economics in Chat, Work, local Codex, cloud Codex, or API use.
- Treat current platform defaults as a strong baseline; do not tune merely because a knob exists.
- Prefer mechanically favorable optimizations such as valid caching, warm deterministic state, concise model-visible logs, and exact local tools.
- Deviate from defaults only for a concrete reason; benchmark only when the tradeoff is non-obvious, consequential, or workload-dependent.
- Treat explicit large-scale orchestration and fan-out as costed choices, not signals of sophistication.

## Code is persistent context

For coding/refactoring tasks, see [`docs/code/agent-legible-code.md`](docs/code/agent-legible-code.md). It distills practices that make future work cheaper to localize, mentally model, modify, validate, and debug without turning “AI-friendly code” into another style religion.

The primary target is **bounded mental-model construction**, not smallest LOC and not formal proof. A weak/fresh coding model should be able to predict representative paths, state changes, results, side effects, failures, and important dependencies without repository archaeology or a large reasoning budget.

That usually favors semantic locality, cohesive functions/modules, information-hiding boundaries, explicit dependency direction and state, mentally enumerable control flow, resilient behavior-level tests, useful diagnostics, and conventional machine-enforced formatting. Excessive micro-functions, speculative interfaces, reflection, hidden dependency injection, brittle mocks, duplicated comments, and long semantic-hop chains can do the opposite.

Use [`templates/source-AGENTS-agent-legible.md`](templates/source-AGENTS-agent-legible.md) as a compact source-tree rule set when the harness supports scoped/nested instructions. The deeper research remains out of the normal runtime path.

Claims about agent savings should be tested on representative maintenance work. [`experiments/agent-legibility.md`](experiments/agent-legibility.md) includes a weak-reader semantic test plus localization context, dependency hops, edit radius, turns/tools, validation/recovery effort, and the same outcome gate.

## Runtime evidence is persistent context too

Even correct code runs inside changing environments and eventually emits failures, warnings, build/test output, traces, profiles and crash artifacts that another agent must inspect.

The runtime-feedback methodology in [`docs/runtime/`](docs/runtime/README.md) applies the same context economics to that evidence:

```text
compact outcome / beacon
        ↓
structured diagnostic capsule or postmortem manifest
        ↓
focused correlated evidence
        ↓
retained raw artifact
```

Do not delete raw evidence merely to save tokens. Make it **progressively addressable** so an agent opens only what the current hypothesis needs.

A crashed target is a first-class case. [`docs/runtime/postmortem-bundles.md`](docs/runtime/postmortem-bundles.md) defines an offline evidence bundle whose manifest links to progressively deeper files such as application-stack slices, recent structured events, environment deltas, traces, minidumps, cores, heap dumps and full logs. Live queries can help when available but are never assumed.

Use [`skills/instrumenting-runtime-feedback/SKILL.md`](skills/instrumenting-runtime-feedback/SKILL.md) when designing the producer and [`skills/diagnosing-runtime-failure/SKILL.md`](skills/diagnosing-runtime-failure/SKILL.md) when consuming failure evidence. [`experiments/diagnostic-feedback.md`](experiments/diagnostic-feedback.md) compares raw-first and progressive evidence at the same diagnostic quality bar.

## Two knowledge layers

The repository deliberately separates **what execution agents should normally read** from **what maintainers may need when improving the methodology**.

### Operational corpus

Start with [`docs/agent-corpus/README.md`](docs/agent-corpus/README.md). It contains the small execution kernel and points to deeper operational guidance only when a decision needs it.

This avoids turning the repository itself into the failure mode it warns about: a giant instruction manual that crowds out the task.

### Research/reference archive

[`references/`](references/README.md) preserves external framework notes, source links, competing approaches, historical rationale, and research depth. Ordinary execution agents should **not** recursively crawl it. It exists so concision does not destroy useful research.

## Quick adoption

For teams that want immediate improvements without changing their architecture or agent framework, use [`docs/adoption/quick-wins.md`](docs/adoption/quick-wins.md).

The first steps are intentionally boring: inspect instruction footprint, quiet noisy tool output, route exact work to exact tools, stop rereading unchanged state, keep validation proportional, and benchmark only the uncertain choices.

## Start here

The first concrete methodology is the [Local Codex Efficiency Stack](docs/local-codex/README.md), designed for Linux Mint + Cursor (including AppImage) but largely editor- and model-independent.

Before choosing that surface for a task, see [execution surfaces and usage pools](docs/execution/surface-and-pool-selection.md): Chat, Work, local Codex, cloud Codex, and API usage can offer similar model capability while differing substantially in repository state, tool affordances, and which allowance pays for the work.

The local stack includes:

- [workstation setup](docs/local-codex/linux-mint-cursor-appimage.md)
- [context and cache economics](docs/local-codex/context-caching.md)
- [deterministic repo tooling and concise logs](docs/local-codex/tooling.md)
- [prompt / AGENTS.md / rule / skill discipline](docs/local-codex/prompts-skills-agents.md)
- [portable skill adoption across repositories and hosts](docs/adoption/overlays.md#portable-skill-routing)
- [cost-aware delegation and subagent economics](docs/local-codex/subagents.md)
- [agent-legible code](docs/code/agent-legible-code.md)
- [runtime diagnostic feedback](docs/runtime/README.md)
- [runtime E2E readiness and evidence boundaries](docs/runtime/e2e-readiness.md)
- [defaults before overrides](docs/principles/defaults-before-overrides.md)
- [measurement and benchmarking as decision aids](docs/local-codex/benchmarking.md)
- [instruction/context adherence protocol](experiments/instruction-context-adherence.md)
- [agent-legibility comparison protocol](experiments/agent-legibility.md)
- [diagnostic-feedback comparison protocol](experiments/diagnostic-feedback.md)
- [optional experiment matrix](experiments/local-codex-efficiency-matrix.md)
- [sample Codex config](configs/codex/efficient-local.config.toml)
- [minimal global AGENTS.md](templates/global-AGENTS-efficient.md)
- [source-scoped agent-legibility template](templates/source-AGENTS-agent-legible.md)
- [optional efficiency skill](skills/efficient-execution/SKILL.md)
- tools for [quiet command execution](tools/quiet-run), [repo inventory](tools/repo-index.py), [instruction-footprint inventory](tools/instruction-footprint.py), and [Codex JSONL benchmark capture](tools/codex-bench.py)

## Repository map

- `docs/agent-corpus/` — small default reading corpus for execution agents
- `docs/code/` — source-structure guidance for cheap future agent maintenance
- `docs/runtime/` — runtime/build/test diagnostic feedback and offline postmortem evidence
- `docs/principles/` — durable concepts
- `docs/execution/` — execution mechanisms and surface/resource selection
- `docs/local-codex/` — concrete local Codex efficiency methodology
- `docs/collaboration/` — concurrency and ownership
- `docs/measurement/` — reusable metrics
- `docs/evidence/` — how observations become shared practices
- `docs/adoption/` — low-friction adoption and local overlays
- `experiments/` — behavioral and economic comparisons
- `configs/` — conservative configuration examples
- `templates/` — small reusable instruction templates, including source-scoped code guidance
- `skills/` — optional on-demand workflows
- `tools/` — deterministic helpers that keep work out of the LLM
- `references/` — external research/provenance; not normal runtime context

## Evidence rule

Guidance is categorized as one of:

1. **documented behavior** — supported by current vendor/tool documentation;
2. **measured result** — observed directly, with a controlled benchmark when one is useful;
3. **engineering hypothesis** — plausible and worth testing, but not yet proven.

Avoid turning a local anecdote into a universal rule. Measurement should resolve uncertainty, not become ceremony. If a current default already works well, leave it alone until there is a reason to change it.
