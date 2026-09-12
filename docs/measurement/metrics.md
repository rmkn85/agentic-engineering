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
- deterministic acceptance result
- commands/tool calls
- retries/failures
- number of agents/subagents
- changed-file/diff statistics

For repository-heavy workflows, additionally measure repeated file reads, write amplification, repeated tests, and raw log size versus model-visible log size where tooling can expose them.

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

Use the metric that matches the scarce resource. A message-metered Chat surface and a token-metered Codex surface should not be compared using tokens alone.

See [`../local-codex/benchmarking.md`](../local-codex/benchmarking.md) for the concrete Codex protocol, [`../principles/metering-units-and-amortization.md`](../principles/metering-units-and-amortization.md) for metering granularity, [`../execution/surface-and-pool-selection.md`](../execution/surface-and-pool-selection.md) for cross-surface resource selection, and [`../../tools/codex-bench.py`](../../tools/codex-bench.py) for capture tooling.
