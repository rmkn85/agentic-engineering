# Defaults before overrides

The purpose of agentic engineering is not to maximize tuning. It is to accomplish the same work efficiently and reliably.

## Default-preserving rule

Treat current tool and model defaults as the starting prior, not as defects to be corrected.

A deviation is justified when all three are true:

1. **Mechanism** — there is a concrete reason the default is wasteful or unsuitable for this workload.
2. **Expected benefit** — the change plausibly improves a resource that matters (tokens, quota, wall time, deterministic compute, retries, or human effort) without weakening the required outcome.
3. **Reversibility** — the change can be removed when the underlying tool, model, or workload changes.

Do not add an override merely because a setting exists or because an older version of a tool benefited from it.

## Three classes of optimization

### 1. Mechanically favorable practices

These generally need little or no repeated benchmarking once correctness is established because the mechanism is direct and monotonic:

- reuse a valid cache instead of recomputing the same deterministic result;
- keep dependencies/build artifacts warm when inputs are unchanged;
- preserve full logs on disk while showing the model only the relevant summary/excerpt;
- use exact deterministic tools for exact operations instead of asking an LLM to rediscover the result;
- avoid rereading or regenerating unchanged material when prior semantic work remains valid;
- keep stable prompt/context prefixes stable when the platform can cache them.

Even here, correctness conditions matter. A stale cache, over-aggressive log truncation, or incorrect invalidation policy is not an optimization.

### 2. Workload-dependent choices

These are plausible but not universally better:

- explicit subagent counts or concurrency caps;
- local vs cloud execution;
- custom model/reasoning effort;
- custom `AGENTS.md` instructions;
- skills and prompt templates;
- context-size limits;
- test-selection heuristics;
- compaction timing;
- custom tool-output limits.

Start with the platform default. Deviate only for a specific reason. Measure when the consequence is material or the direction of improvement is uncertain.

### 3. Speculative tuning

Avoid changes whose only rationale is that they *might* save resources. Every extra instruction, skill, wrapper, index, cache layer, and orchestration rule has maintenance and context cost.

If the mechanism is unclear, do not add it until a real problem appears.

## Benchmarking is a helper

Benchmarks answer questions; they are not the objective.

Use a benchmark when it helps decide between plausible alternatives, validate a consequential override, or detect a regression after a tool/model change. Do not benchmark a cache hit against deliberately recomputing an identical deterministic artifact merely to prove that caching exists.

The final goal is a simpler operational rule, not a permanent experiment suite.

## Deletion is an optimization

When a newer Codex/model/tool default subsumes a local workaround, delete the workaround. Fewer instructions and overrides mean less configuration drift, less prompt/context overhead, and fewer ways to fight improvements in the upstream system.
