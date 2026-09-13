# Documentation

The repository is organized around execution efficiency rather than project methodology.

## Default agent reading path

Agents doing ordinary engineering work should start with the focused [`agent-corpus/README.md`](agent-corpus/README.md), then open only the deeper document needed for the current decision.

Do **not** treat the documentation tree as a startup checklist. In particular, [`../references/`](../references/README.md) is a research/provenance archive for methodology work, not normal execution context.

## Quick adoption

- [Quick wins without major refactoring](adoption/quick-wins.md)
- [Local overlays](adoption/overlays.md)

## Concrete methodologies

- [Local Codex Efficiency Stack](local-codex/README.md) — local-first Codex setup, context/cache discipline, deterministic tooling, instruction/skill benchmarking, bounded delegation, and metrics.

## General principles

- [Context economics](principles/context-economics.md) — context residency, instruction cost, progressive disclosure, context pressure, and lower-bound footprint auditing.
- [Metering units and amortization](principles/metering-units-and-amortization.md) — distinguish token-, message-, task-, invocation-, and other meters; maximize useful accepted work per scarce accounting unit.
- [Defaults before overrides](principles/defaults-before-overrides.md) — preserve good upstream behavior; justify tuning.

## Execution mechanisms

- [Execution surfaces and usage pools](execution/surface-and-pool-selection.md)
- [Caching and prefetching](execution/caching-and-prefetching.md)
- [Local-first execution](execution/local-first.md)
- [Read-once/write-once and invalidation](execution/read-once-write-once.md)

## Collaboration, measurement, and evidence

- [Collisions as signals](collaboration/collisions-as-signals.md)
- [Metrics](measurement/metrics.md)
- [Practice lifecycle](evidence/practice-lifecycle.md)

## Behavioral experiments

- [Instruction and context adherence](../experiments/instruction-context-adherence.md)
- [Delegation adherence](../experiments/delegation-adherence.md)
- [Local Codex efficiency matrix](../experiments/local-codex-efficiency-matrix.md)
