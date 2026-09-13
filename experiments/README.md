# Experiments

This directory is for reproducible comparisons of agent-development techniques. Experiments are decision aids, not a requirement to benchmark every obvious optimization.

Useful dimensions include:

- model choice at fixed operation mode;
- local vs cloud at fixed model and task;
- reasoning level;
- single agent vs delegated workers;
- cold vs warm dependency/build caches;
- raw tool output vs reduced diagnostics;
- semantic index vs ad-hoc repeated search;
- read-once/invalidation workflow vs repeated global review;
- instruction present vs absent/scoped/on-demand;
- instruction rule alone vs normal complete stack;
- representative vs high legitimate context pressure;
- thin vs stronger orchestrator for instruction/control reliability.

An experiment should define workload, environment, success criteria, model/settings, measured resources, substantive quality checks, and limitations. Change the smallest number of variables needed to answer the decision.

## Current protocols

- [`instruction-context-adherence.md`](instruction-context-adherence.md) — RED/GREEN/refactor, ablation, instruction interference, context pressure, delegation/routing adherence, and escalation.
- [`local-codex-efficiency-matrix.md`](local-codex-efficiency-matrix.md) — optional broader local Codex comparisons.

Historical observations that no longer need to be active protocols belong under [`../references/`](../references/), not here.

Do not report resource savings from an instruction/model/delegation variant unless the required outcome remains non-inferior.
