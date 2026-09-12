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

## Derived comparisons

- cache-hit ratio
- fresh-input estimate
- token saving relative to baseline
- wall-clock speedup
- fan-out token amplification
- speedup per token-amplification factor

See [`../local-codex/benchmarking.md`](../local-codex/benchmarking.md) for the concrete Codex protocol and [`../../tools/codex-bench.py`](../../tools/codex-bench.py) for capture tooling.
