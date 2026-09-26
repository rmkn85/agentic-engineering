# Defaults before overrides

The purpose of agentic engineering is not to maximize tuning. It is to accomplish the same work efficiently and reliably.

## Default-preserving rule

Treat current tool and model defaults as the starting prior, not as defects to be corrected.

A deviation is justified when all three are true:

1. **Mechanism** — there is a concrete reason the default is wasteful or unsuitable for this workload.
2. **Expected benefit** — the change plausibly improves a resource that matters (tokens, quota, wall time, deterministic compute, retries, or human effort) without weakening the required outcome.
3. **Reversibility** — the change can be removed when the underlying tool, model, or workload changes.

Do not add an override merely because a setting exists or because an older version of a tool benefited from it.

## Preserve properties by construction, not constant supervision

For an affected cross-cutting property, distinguish **enduring obligation**, **current change**, and **deferred refinement/evidence**. Recover these from current product authority, not just the latest task sentence. Deferring an expensive check changes confidence, not the obligation. Conversely, an explicitly scoped throwaway prototype or authorized product-scope change need not implement aspirational future features.

Before selecting tests, identify **property → preserving mechanism → real consumer → composition owner**. Prefer adequate native facilities and existing abstractions. A guide, dependency name or isolated demo is not integration. Components own their local allocations; the composition owns competing budgets, ordering and the complete user/system outcome. Individually valid parts can jointly fail.

Ask what happens under the next ordinary extension. Does another input, action, consumer or longer payload follow an existing policy, or force unrelated repairs? Use the smallest meaningful variation probe when this mechanism changes—not an exhaustive matrix on every edit. Preserve a good baseline rather than inventing a framework. See [agent-legible code](../code/agent-legible-code.md) for locality and dependency design.

## Unknown conditions require bounded strategies

| Uncertainty affecting this change | Proportionate response |
| --- | --- |
| Known operating envelope, uncertain instance | Preserve invariants across the range; probe boundaries and interactions, with justified margins rather than universal numbers. |
| Discoverable during execution | Make the condition observable, bound retries/resources, and use a documented fallback that preserves essential semantics. |
| Unobservable or delayed feedback | Reduce dependence on that assumption; contain faults and select a conservative, locally appropriate default. Missing evidence remains uncertainty. |
| Irreversible action or no later correction | Inspect exact delivered configuration/dependencies, exercise essential degraded behavior, retain recovery where possible, and require existing risk authority before proceeding. A future patch or absent reviewer is not a mitigation. |

Unknown does not mean every failure is predictable or that safe failure is always a halt. Choose the least harmful state for the actual system. Extra redundancy, watchdogs or independent review must have a named failure/decision to address; correlated copies may preserve the same blind spot.

Actively challenge one consequential assumption, not only declared happy-path claims. Depending on the boundary, use a property/metamorphic relation, fault injection, changed ordering/content/resource limit, differential consumer, or small combinatorial sample. Retain the seed/minimized reproducer and healthy control. Check that the oracle itself can fail correctly. Sampling is evidence about sampled conditions, not exhaustive assurance.

New observations can reveal a missing obligation. Reconcile the contract with product authority and keep the reason/change visible; do not freeze an incomplete checklist or silently weaken it. Respect unresolved critical risk instead of guessing permission. Return to the requested outcome once the uncertainty no longer changes the next decision.

**Basis:** this is a domain-neutral engineering synthesis, not a claim of aerospace certification or universal agent reliability. NASA's [design-solution process](https://www.nasa.gov/reference/4-4-design-solution-definition/) explicitly distinguishes design validation against stakeholder expectations from later product verification. NIST's [combinatorial coverage guidance](https://www.nist.gov/publications/combinatorial-coverage-measurement) describes interaction coverage rather than exhaustive correctness. Reviewed 2026-09-26. Their process scale and assurance levels are not imported here.

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
