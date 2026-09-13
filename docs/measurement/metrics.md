# Efficiency metrics

The governing comparison is **same required outcome, lower total resource use**.

Do not optimize a single metric in isolation. A task that uses 30% fewer tokens but fails acceptance is not an efficiency improvement.

## Minimum common metrics

- input tokens
- cached input tokens
- output tokens
- reasoning output tokens where exposed
- model turns
- wall-clock duration
- deterministic and substantive acceptance result
- commands/tool calls
- retries/failures
- number of agents/subagents
- changed-file/diff statistics

For repository-heavy workflows, additionally measure repeated file reads, write amplification, repeated tests, and raw log size versus model-visible log size where tooling can expose them.

## Instruction/context metrics

When prompts, `AGENTS.md`, skills, rules, tools, or memory are part of the experiment, also record where available:

- always-loaded / recurring controllable context;
- runtime context breakdown from the harness (system/instructions, memory, skills, tools/MCP, files, conversation);
- file-based instruction footprint as a lower-bound proxy;
- instruction/adherence failures visible in the execution trace;
- human corrections caused by non-adherence;
- retries or discarded work caused by context/instruction failure;
- behavior under representative and high legitimate context pressure.

Do not treat a nominal context-window size as a measure of effective instruction capacity. Do not treat cached input as absent context: caching can change billing/latency while the cached tokens still remain model input.

[`../../tools/instruction-footprint.py`](../../tools/instruction-footprint.py) inventories common file-based instruction sources. Its character-based token estimate is only a stable comparison proxy; prefer native harness context accounting when available.

## Code-maintenance / agent-legibility metrics

When code structure itself is the optimization, measure the **future maintenance task**, not just static code style.

Useful observations include:

- files/symbols opened before the correct change location is identified;
- unique source context loaded before/through the accepted edit;
- search/index/LSP calls and dependency hops followed;
- wrong candidate implementations inspected;
- files/modules changed for one conceptual change (**edit radius**);
- unrelated files changed because of coupling;
- model turns/tool calls before a passing edit;
- tests rewritten by a behavior-preserving refactor;
- validation wall time and breadth;
- retries/reverts/human corrections;
- time/context required to diagnose a seeded or real failure.

Static measures such as cyclomatic/cognitive complexity, dependency cycles/fan-out, public surface size, function/module size, global mutable state, and duplication can help explain results. They are proxies, not the objective: extracting ten tiny helpers can improve line-count metrics while making agent navigation worse.

See [`../../experiments/agent-legibility.md`](../../experiments/agent-legibility.md) for the comparison protocol and [`../code/agent-legible-code.md`](../code/agent-legible-code.md) for operational guidance.

## Cross-surface metrics

For cross-surface comparisons, also record:

- model and reasoning level
- execution surface: Chat, Work, Codex local, Codex cloud, Deep Research, or direct API
- authentication/billing path when relevant
- **metering unit**: tokens, credits, user messages, research tasks/uses, API calls, compute/time windows, or another surfaced unit
- which usage allowance or credit pool was consumed
- reported credits/messages/tasks/allowance depletion where the product exposes it
- local versus cloud setup/warm-state assumptions
- nested invocation counts where relevant: searches, tools, subagents, file operations, or external API calls

A token count alone can be misleading when two surfaces draw from different included allowances. Conversely, a superficially cheap message or task is not efficient if the surface reconstructs state repeatedly or produces lower-quality work.

## Derived comparisons

Useful decision aids include:

- cache-hit ratio
- fresh-input estimate
- token saving relative to baseline
- wall-clock speedup
- fan-out token amplification
- speedup per token-amplification factor
- allowance depletion per accepted task, where measurable
- accepted work per metered message/task/use
- invocation amplification: nested invocations per top-level metered unit
- context amplification: total worker context divided by unique task-relevant information
- human-turn efficiency: accepted progress per required user intervention

For instruction experiments, a useful qualitative/quantitative pair is:

```text
incremental recurring context
vs
change in accepted behavior / human correction rate
```

For source-structure experiments, useful workload-specific ratios include localization context, edit radius, turns, and validation/recovery effort relative to the baseline. Do not combine them into a universal “agent legibility score” unless the workload provides defensible weights.

Do not collapse instruction dimensions into a universal “instruction value score” either. A 40-token rule that prevents an expensive recurring failure may be extremely valuable; a 700-token explanation that changes nothing may belong in a reference instead.

## Recovery cost

A cheaper initial model/run can be more expensive after non-adherence:

```text
effective workflow cost =
  initial run
  + duplicated/repeated work
  + retries
  + corrective human turns
  + stronger-model recovery
  + discarded worker work
```

Use actual surfaced units where possible; otherwise report the components rather than inventing a currency conversion.

See [`../local-codex/benchmarking.md`](../local-codex/benchmarking.md) for the concrete Codex protocol, [`../../experiments/instruction-context-adherence.md`](../../experiments/instruction-context-adherence.md) for behavioral instruction testing, [`../../experiments/agent-legibility.md`](../../experiments/agent-legibility.md) for code-structure comparisons, [`../principles/metering-units-and-amortization.md`](../principles/metering-units-and-amortization.md) for metering granularity, [`../execution/surface-and-pool-selection.md`](../execution/surface-and-pool-selection.md) for cross-surface resource selection, and [`../../tools/codex-bench.py`](../../tools/codex-bench.py) for capture tooling.
