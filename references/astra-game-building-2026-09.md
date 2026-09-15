# Astra game-building case — September 2026

Status: scoped source note based on OpenAI's public [Building games with Astra](https://developers.openai.com/blog/how-to-build-games-with-astra), reviewed 2026-09-15. **Not part of the normal agent reading corpus.** The case reports one author's workflow; it is not a comparative model benchmark.

Operational guidance: [execution surfaces and usage pools](../docs/execution/surface-and-pool-selection.md#route-coupled-synthesis-separately-from-routine-execution), [runtime E2E readiness](../docs/runtime/e2e-readiness.md), and [agent-efficient diagnostic feedback](../docs/runtime/diagnostic-feedback.md).

## Source-reported example

The author describes using Astra in Codex to turn desired player experiences and visual references into playable browser games. In the principal example, the work crossed navigation, multiple spatial scales, procedural terrain, controls, rendering and authored art. The workflow gave the agent repeatable named scenes, a small inspectable application-state interface, rendering and streaming counters, browser journeys, screenshots and deterministic tests. The human continued to judge appearance and control feel.

The source reports controlled comparisons for particular terrain and rendering changes. It carefully limits those results: software-rendered browser timings are not measurements of the author's GPU, scheduling counts are not frame rate, and browser play remains necessary for motion, uploads, shader compilation and feel. It also distinguishes loading a prepared scene from exercising the real control journey.

The article reports that Astra proposed and implemented architecture, investigated cross-layer problems, produced 3D assets from approved references and reran focused comparisons. It does **not** compare Astra with a smaller model, report token or monetary savings, establish that Astra is required for game development, or provide a hardware-performance benchmark.

## Engineering hypothesis derived from the case

The reusable lesson is domain-neutral: a costly capable model may earn its use when it must reconcile an intended experience or invariant across several coupled technical boundaries, especially when the evidence mixes runtime state with perceptual judgment. Its output becomes more economical when it crystallizes the decision into artifacts that cheaper executors and exact tools can follow.

Candidate artifacts include:

- an explicit boundary or architecture decision with preserved invariants;
- approved references and concrete acceptance criteria;
- repeatable scenarios that return the system to a decision-bearing state;
- a small stable state/diagnostic interface and bounded counters;
- deterministic contract tests plus a real journey through production controls;
- before/after measurements that isolate one policy while recording environment and limits.

This suggests a selective route: use strong synthesis for the coupled decision, bounded workers for well-specified implementation, deterministic machinery for replay and measurement, and human review where acceptance is experiential. The hypothesis should be revised if representative comparisons show that a cheaper model reaches the same accepted result with equal or less total retries, rework and human attention, or that the stronger model does not improve the coupled decision.

## Scope limits

- The specific games, architecture and measurements illustrate the author's public case; they are not universal prescriptions.
- Generated concepts, Blender assets, procedural art and code-drawn art are alternative production paths, not a required sequence.
- Instrumentation and prepared scenarios support agent diagnosis; they do not replace the shipped interaction journey or human experiential acceptance.
- The reported numeric improvements belong only to the named controlled comparisons in the source. This repository makes no derived savings or hardware-performance claim from them.
