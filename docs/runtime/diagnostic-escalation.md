# Diagnostic escalation: recorder, replay, and dynamic probes

Use this only when ordinary structured diagnostics and postmortem bundles are insufficient. These mechanisms deliberately spend more runtime/storage/engineering cost to avoid far larger exploratory model/debugging cost on difficult failures.

The escalation order is generally:

```text
normal capsule / postmortem manifest
        ↓ insufficient
bounded pre-failure flight recorder
        ↓ insufficient and failure reproducible/recordable
record/replay artifact
        ↓ target still alive and missing evidence can be observed safely
dynamic targeted probe
```

This is not a strict universal sequence. Choose the cheapest mechanism that can preserve the missing fact.

## Bounded flight recorder

Use when the failure depends on **what happened before the symptom** and ordinary logs are either too sparse or too expensive to keep verbose continuously.

Keep a bounded rolling window of selected structured events, for example:

- state transitions;
- external-boundary start/result/duration;
- retry/fallback decisions;
- queue/resource threshold crossings;
- ownership/leader/config transitions;
- sampled scheduling/lock/allocation events where relevant;
- correlation identifiers.

Bound by age, size, event count, or another explicit resource budget. On an incident trigger, freeze/dump the relevant window into the postmortem bundle and record the retention policy/dropped-data status.

This is a **black-box recorder**, not `DEBUG` logging forever.

## Record/replay

For intermittent or nondeterministic failures, preserving the execution itself can be more valuable than producing more textual telemetry.

Where runtime/platform tooling supports it, record enough nondeterministic inputs/state to replay the same failing execution repeatedly under a debugger or analyzer.

A replay artifact is especially useful when:

- the bug is timing-sensitive or intermittent;
- rerunning produces materially different state;
- repeated probes would otherwise invalidate earlier observations;
- reverse execution/data watchpoints can trace an effect back to its cause;
- a portable recording can move diagnosis away from the failing environment.

Treat the replay recording as a deep evidence artifact in the postmortem manifest. The first agent-facing view should still be small; open/replay it only when shallower evidence cannot answer the question.

Record/replay can have platform, performance, storage and compatibility constraints. Do not require it universally.

## Persistent crash buffers below the application

Some failures destroy not only the process but ordinary logging/storage paths. Where the platform provides it, use a lower-level persistent crash buffer or OS/runtime crash facility that survives restart/reboot.

Examples include kernel panic/oops persistence, OS core-dump facilities and external crash collectors.

The agent-facing bundle should ingest/index the surviving evidence after restart rather than depending on the failed application to have flushed its normal logs.

## Dynamic targeted probes

When the system is still alive and the missing fact was not instrumented ahead of time, prefer a **targeted temporary probe** over permanently enabling high-volume diagnostics everywhere.

Possible mechanisms include:

- runtime diagnostic commands;
- dynamic tracing/eBPF/ftrace/DTrace-style probes;
- temporary trace/sampling policy changes;
- targeted profiler activation;
- feature-gated diagnostic events.

A dynamic probe should have:

- a narrow target/question;
- an explicit duration/event/resource budget;
- stable correlation with the incident;
- automatic rollback/expiry where practical;
- a persisted output artifact;
- a privacy/security review appropriate to the captured data.

Do not let an agent install arbitrary high-overhead probes merely because the first evidence layer was inconclusive.

## Escalation must say what information is missing

Before opening or enabling a more expensive evidence source, state the unanswered question.

Good:

```text
Known: request fails in decoder after frame allocation.
Missing: which writer last changed buffer length.
Escalate: replay trace + data watchpoint.
```

Bad:

```text
Need more information; enable all debug logs and attach the core.
```

This keeps diagnostic expansion hypothesis-driven rather than evidence-hoarding.

## Keep the evidence graph intact

All escalation artifacts should link back to the same incident/bundle identity and record how they were created.

Example:

```text
manifest.json
  -> focused/recent-events.jsonl
  -> raw/minidump.dmp
  -> replay/rr-trace/
  -> probes/lock-contention-20260913.otlp.json
```

A later agent should be able to understand which artifacts existed at failure time and which were generated during follow-up diagnosis.

## Completion test

An escalation mechanism earns its cost when it materially reduces one or more of:

- repeated failed reproductions;
- fresh model evidence tokens;
- exploratory queries/probes;
- hypotheses investigated before root cause;
- human intervention;
- time to a verified fix;

while preserving diagnostic correctness, runtime safety and privacy.

Related guidance:

- [`diagnostic-feedback.md`](diagnostic-feedback.md)
- [`postmortem-bundles.md`](postmortem-bundles.md)
- [`../../skills/diagnosing-runtime-failure/SKILL.md`](../../skills/diagnosing-runtime-failure/SKILL.md)
