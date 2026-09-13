# Continuous flight-recorder evidence — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

Operational guidance: [`../docs/runtime/diagnostic-feedback.md`](../docs/runtime/diagnostic-feedback.md) and [`../docs/runtime/postmortem-bundles.md`](../docs/runtime/postmortem-bundles.md)

## Research question

How can a program preserve enough **pre-failure history** for diagnosis without continuously emitting or retaining unbounded verbose logs?

The useful pattern is a bounded continuous recorder: capture selected structured events cheaply, keep only a limited recent window, and freeze/dump that window when a failure or diagnostic trigger occurs.

---

## Java Flight Recorder (JFR)

Sources:

- Oracle, *Diagnostic Tools — Flight Recorder*: https://docs.oracle.com/en/java/javase/24/troubleshoot/diagnostic-tools.html
- Oracle, *Flight Recorder Configurations*: https://docs.oracle.com/en/java/javase/17/jfapi/flight-recorder-configurations.html
- Oracle JMC documentation, *Using JDK Flight Recorder*: https://docs.oracle.com/en/java/java-components/jdk-mission-control/8/user-guide/using-jdk-flight-recorder.html

Oracle describes JFR as a profiling/event collection framework designed to preserve detailed runtime information for after-the-fact incident analysis while operating with low overhead.

Current documentation distinguishes:

- **continuous recordings** — always on, bounded by maximum age/size and suitable for low-overhead production use;
- **profiling recordings** — more detailed and more expensive, enabled when the deeper information is worth the cost.

For continuous recordings, events accumulate in bounded buffers/storage; oldest data is discarded as limits are reached. The current buffer/window can be dumped manually or by a trigger when an incident occurs.

The default JFR configuration is specifically intended to balance useful data with low overhead; more expensive event classes can be enabled selectively for deeper profiling.

### Agent-era translation

A system can keep a bounded diagnostic **flight recorder** that is richer than ordinary logs but cheaper than always-on full tracing/debug logging:

- selected state transitions;
- boundary-call durations/results;
- retry/fallback decisions;
- queue/resource pressure;
- allocation/lock/scheduling samples when relevant;
- correlation IDs;
- runtime/environment transitions.

When an error/invariant/latency/resource trigger fires:

1. freeze or retain the relevant pre-failure window;
2. write/reference it from the postmortem manifest;
3. derive a small focused recent-event slice;
4. let the agent open the full recording only if needed.

This avoids the impossible requirement to know in advance exactly which single log line will explain a rare failure.

---

## Bounded recency is often more valuable than unbounded history

For many failures, the most valuable evidence is **what immediately preceded the symptom**.

A ring/circular buffer or age/size bounded repository provides predictable resource use:

```text
record selected events continuously
          ↓
oldest evidence expires at known bound
          ↓
failure trigger freezes/references recent window
          ↓
collector writes focused summary + retained recording
```

The exact window is workload-specific. Do not adopt a universal “last N minutes” rule.

Long-horizon forensic/audit needs are a separate storage requirement and may justify durable telemetry aggregation outside the process.

---

## Record decisions, not every instruction

A flight recorder should optimize diagnostic value per event.

High-value candidates tend to be:

- state-machine transitions;
- external boundary start/end/error with duration;
- retry/fallback/circuit decisions;
- resource/saturation threshold crossings;
- configuration/feature-flag changes;
- important cache/leader/ownership transitions;
- invariant failures;
- sampled concurrency/lock/latency events.

Low-value defaults often include:

- every function entry/exit;
- repeated static configuration;
- high-frequency success events already represented by aggregate metrics;
- giant payload serialization;
- duplicated logs emitted by every layer for the same event.

---

## Recorder loss must be explicit

Bounded recorders necessarily drop/overwrite data. That is fine when the policy is intentional, but it must not masquerade as complete history.

Useful metadata includes:

- recording start/end/window;
- configured max age/size;
- dropped/overwritten event counts where available;
- event classes enabled;
- trigger that caused the dump;
- collector/truncation errors.

This allows the next agent to distinguish “nothing happened” from “the recorder did not retain that interval/class.”

---

## Main conclusion

For rare/runtime-dependent failures, the best agent-facing evidence may come from a **bounded black-box recorder**, not from either extreme:

```text
no runtime history
vs
unbounded verbose logs
```

Use a low-overhead bounded recorder for selected decision-bearing events, then integrate the frozen window into the same progressive postmortem artifact graph used for stacks, traces, environment deltas, dumps and full logs.
