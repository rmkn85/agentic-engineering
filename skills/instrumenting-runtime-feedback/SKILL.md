---
name: instrumenting-runtime-feedback
description: Use when adding or changing logging, telemetry, health checks, crash reporting, diagnostics, self-monitoring, recovery reporting, build/test output, or other runtime feedback intended to help later diagnosis.
---

# Instrumenting runtime feedback

Goal: preserve diagnostic truth while giving the next agent the **smallest useful first view** and a cheap path to progressively deeper evidence.

1. **Name the diagnostic decisions.** Identify who/what consumes the signal and what decision it should support: healthy/degraded/failed, retry/stop, route traffic, localize a fault, compare environment, reproduce, or escalate.
2. **Assume the target may be dead.** If the failure can terminate/wedge/partition the program, design an offline postmortem bundle first. Live queries are optional acceleration, not the only diagnostic path.
3. **Make success boring.** Healthy/passing output should normally be a compact structured outcome plus artifact/run identity, not a transcript of routine work.
4. **Define a stable first-level capsule/manifest.** Include event/fingerprint, component/operation, release/environment identity, concise measured facts, remediation history and references to deeper artifacts. Do not encode speculative root cause as fact.
5. **Build a progressive evidence graph.** Prefer summary -> focused stack/events/environment delta/trace slice -> raw log/dump/profile. Record artifact kind, size/completeness and purpose so an agent can choose before opening it.
6. **Keep bounded pre-failure history when the failure needs history.** For rare timing/state/concurrency/performance failures, prefer a low-overhead rolling flight recorder of selected decision-bearing events with an explicit age/size bound. Freeze/reference the recent window on a trigger; do not replace it with unbounded DEBUG logs or every-function tracing.
7. **Correlate instead of concatenate.** Propagate trace/request/job/run/release IDs so metrics, events, traces, tests and artifacts can be joined without pasting them together.
8. **Choose the cheapest signal for each fact.** Metrics for aggregates; structured events for discrete decisions/state; traces for cross-boundary causality; profiles for population cost; dumps for state that ordinary signals cannot preserve.
9. **Capture environment comparably.** Prefer version/config/runtime/resource fingerprints and relevant deltas from a known-good baseline over full environment/process dumps. Exclude secrets and sensitive payloads before persistence.
10. **Bound self-healing and record it.** Retries/restarts/fallbacks/circuit breaking must have explicit budgets and emit trigger -> action -> attempt -> result -> resulting state. Preserve the original failure evidence.
11. **Survive the failure path.** Keep fatal/crash collection simple and bounded; use OS/runtime crash facilities, supervisors or helper processes when the target cannot reliably report itself. Mark partial/truncated collector output explicitly.
12. **Group and sample by decision value.** Collapse duplicate failures into fingerprint + count + representative event. Preserve errors/outliers more aggressively than routine healthy traffic without discarding the raw evidence needed for exceptional cases.
13. **Prefer structured tool protocols.** Consume/emit JUnit/JSON/SARIF/build-event/OTLP-style structured evidence when available instead of forcing agents to scrape terminal prose.
14. **Test diagnostics under failure.** Kill/crash/wedge the target or break the telemetry path in a safe fixture. Verify that a fresh agent can start from the manifest/capsule and follow a small number of references to the next correct diagnostic decision.

For offline bundle structure, read `docs/runtime/postmortem-bundles.md`. For the broader signal/recovery tradeoffs, read `docs/runtime/diagnostic-feedback.md` only when needed.
