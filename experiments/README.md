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
- thin vs stronger orchestrator for instruction/control reliability;
- one broad skill vs several cheaply routed focused skills;
- code structure before/after a targeted legibility refactor at fixed behavior/acceptance;
- raw-first failure evidence vs progressively linked diagnostic artifacts at the same retained diagnostic fidelity.

An experiment should define workload, environment, success criteria, model/settings, measured resources, substantive quality checks, and limitations. Change the smallest number of variables needed to answer the decision.

## Current protocols

- [`instruction-context-adherence.md`](instruction-context-adherence.md) — RED/GREEN/refactor, ablation, instruction interference, context pressure, delegation/routing adherence, and escalation.
- [`skill-routing.md`](skill-routing.md) — determine when focused skills save more context/reasoning than their discovery and routing overhead.
- [`agent-legibility.md`](agent-legibility.md) — compare source structures by weak-reader semantic accuracy, localization context, edit radius, validation/recovery effort, and accepted outcome.
- [`diagnostic-feedback.md`](diagnostic-feedback.md) — compare raw-first diagnostics with compact manifests/capsules and progressively deeper retained evidence, including dead-target cases.
- [`local-codex-efficiency-matrix.md`](local-codex-efficiency-matrix.md) — optional broader local Codex comparisons.

## Bounded tool trials

- [`harness-tool-trials-2026-09-24.md`](harness-tool-trials-2026-09-24.md) — verified observation recall and an isolated MCP schema-compression fixture, with explicit limits on what the trials establish.
- [`fixtures/coordination-replay/README.md`](fixtures/coordination-replay/README.md) — synthetic cross-component release repair with retained logs and independent source/package/install/consumer acceptance; suitable for paired coordinator-context trials.

Historical observations that no longer need to be active protocols belong under [`../references/`](../references/), not here.

Do not report resource savings from an instruction/model/delegation/skill/code-structure/diagnostic variant unless the required outcome remains non-inferior.
