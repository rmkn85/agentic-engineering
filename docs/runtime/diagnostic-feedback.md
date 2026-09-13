# Agent-efficient diagnostic feedback

Runtime evidence is future agent context. The system should preserve enough truth to diagnose failures while making the **first diagnostic representation small, structured, correlated, and actionable**.

The optimization target is:

> **same diagnostic fidelity + same recovery quality -> less fresh model context, fewer probes, fewer repeated reads, and faster localization**

Do not optimize by deleting evidence. Optimize by making evidence progressively addressable.

## Primary invariant: beacon first, evidence behind it

A healthy execution path should normally emit a compact status. A failure should first expose a **diagnostic capsule** that tells the next agent what failed, where, under which runtime identity/environment, what the system already tried, and where deeper evidence lives.

Keep richer evidence out-of-band until the diagnosis needs it.

A useful hierarchy is:

```text
LEVEL 0  beacon / outcome
         OK | DEGRADED | FAIL | UNKNOWN
         + stable event/fingerprint + urgency/action class

LEVEL 1  diagnostic capsule
         component, operation, cause class, app frame,
         correlation IDs, release/env fingerprint,
         bounded state/counters, remediation history,
         evidence references

LEVEL 2  focused evidence
         correlated log slice, failed assertion/test,
         selected spans, relevant metric window,
         symbolicated stack subset, minimized input

LEVEL 3  retained raw artifact
         complete logs, full trace, dump/minidump,
         profile, build event stream, test artifacts
```

An agent should not start at Level 3 merely because Level 3 exists.

## A diagnostic capsule

Use a stable machine-readable schema appropriate to the project. Not every field belongs in every system, but the capsule should usually answer most of these questions without parsing a prose log:

```json
{
  "schema": "agent-diagnostic-v1",
  "status": "FAIL",
  "event": "ORDER_STORE_TIMEOUT",
  "fingerprint": "order-store/postgres/timeout",
  "component": "order-store",
  "operation": "persist-order",
  "occurred_at": "2026-09-13T07:00:00Z",
  "release": "git:abc123",
  "environment": "prod-eu/config:9f20...",
  "trace_id": "...",
  "summary": "Postgres write timed out after bounded retries",
  "cause": {
    "type": "TimeoutError",
    "code": "ETIMEDOUT",
    "boundary": "postgres",
    "application_frame": "order_store.py:184"
  },
  "state": {
    "phase": "commit",
    "attempt": 3,
    "elapsed_ms": 15007
  },
  "impact": {
    "failed": 1,
    "window_total": 187,
    "window_seconds": 60
  },
  "environment_delta": {
    "db_latency_p95_ms": {"current": 4800, "baseline": 42}
  },
  "remediation": [
    {"action": "retry", "count": 2, "result": "failed"}
  ],
  "reproduce": {
    "input_ref": "artifact://failures/.../input.json",
    "seed": 18431
  },
  "evidence": [
    {"kind": "log-slice", "ref": "artifact://.../relevant.log"},
    {"kind": "trace", "ref": "trace://..."},
    {"kind": "full-log", "ref": "artifact://.../stdout-stderr.log"}
  ]
}
```

The exact schema is less important than **stable semantics**. A JSON blob whose keys and meanings change on every call is not structured telemetry; it is prose with braces.

## Structure before prose

Prefer stable typed fields over messages that require language-model parsing.

Useful stable identities include:

- event/error code;
- component and operation;
- build/release/commit;
- runtime/config/environment fingerprint;
- trace/request/job/correlation ID;
- failure fingerprint/grouping key;
- test/target name;
- phase/state-transition name;
- remediation action/result.

Human-readable messages remain useful, but should supplement rather than replace fields the tooling can consume exactly.

## Correlate instead of concatenate

A log line, trace span, metric point, profile sample, test failure and crash dump become much more valuable when they share stable identifiers.

Prefer:

- trace/span IDs on request-scoped events;
- job/run/build IDs for asynchronous work;
- release/commit IDs everywhere diagnostics may cross deployments;
- error/event fingerprints for grouping repeated failures;
- artifact digests or immutable references for retained evidence.

Do not solve correlation by dumping every related artifact into one model prompt.

## Use the right signal for the question

### Metrics: cheap aggregate state

Use metrics for rates, distributions, saturation, capacity, health trends and alert predicates. Metrics answer **how much/how often/how bad** cheaply.

Avoid high-cardinality identifiers as ordinary metric labels. Link exceptional individual cases through exemplars or correlation IDs instead.

### Structured events/logs: discrete facts

Use structured events for important state transitions, decisions, boundary failures, remediation actions and facts that need exact attributes.

Do not log every function entry/exit merely because it is possible. Normal high-volume behavior is often better represented by counters/histograms plus sampled traces.

### Traces: causal path across boundaries

Use traces when the question is **where did this request/job spend time or fail across components?** Keep trace context consistent across services and correlate errors/logs back to the trace.

Sampling is an engineering decision. Preserve error/slow/otherwise interesting traces at higher rates while sampling ordinary healthy paths when full capture is too expensive.

### Profiles: population-level execution cost

Use profiles when the question concerns CPU/allocation/lock/time distribution across many executions. Prefer a query/top-hotspot representation before sending raw profile data to a model.

### Dumps: state snapshot when ordinary signals are insufficient

A crash dump or heap dump is evidence, not a default prompt attachment. Prefer the smallest dump that preserves the required debugging state, retain symbols/build identity, and escalate to a larger dump only when the smaller artifact cannot answer the question.

## Success should be boring

Passing/healthy output should be tiny unless the caller explicitly asks for detail.

Good:

```text
PASS tests=812 duration=41.2s warnings=0 artifacts=.agent-artifacts/run-184/
```

Bad:

```text
812 passing test names + every INFO log + dependency setup chatter + progress bars
```

The full evidence can still be retained on disk or in the CI artifact store.

## Failure should be selective, not silent

Do not replace a 5,000-line failure with `FAILED`.

A useful first failure report should identify:

1. **what operation failed**;
2. **the stable error/event identity**;
3. **the most local decision-bearing frame/boundary**;
4. **the causal/root error class when known without speculation**;
5. **important state and bounds** (attempt, phase, timeout, queue depth, etc.);
6. **release/environment identity**;
7. **what automatic recovery already happened**;
8. **where targeted and raw evidence can be fetched**.

A full stack trace should usually be retained as evidence but not automatically pasted into every agent turn. A compact symbolicated application-frame chain is often a better first representation.

## Group repetitions before reporting them

Repeated identical failures should normally become one issue/fingerprint plus counts and representative examples, not N copies of the same stack.

Useful grouping fields include:

- exception/error type and stable code;
- normalized in-application stack frames;
- operation/component;
- relevant protocol/status code;
- explicit project-specific fingerprint when the default groups badly.

Report first/last seen, frequency, affected release/environment and representative event. Preserve individual events for drill-down.

## Environment is part of the failure state

Code that passed yesterday can fail today with no source change. Capture enough environmental identity to compare the failure against a known-good execution without dumping the entire host into context.

Useful dimensions, depending on the system:

- application release/commit/build;
- runtime/compiler/interpreter version;
- dependency/lockfile image digest;
- OS/kernel/container image;
- configuration/feature-flag digest;
- locale/timezone/clock assumptions;
- permissions/identity;
- CPU/memory/disk/file-descriptor pressure;
- queue/cache/database/backend status;
- network/DNS/TLS endpoint identity;
- hardware/accelerator/driver version.

Prefer an **environment fingerprint + relevant deltas from baseline** over a raw `env`, package list, `/proc`, or system dump.

Never expose secrets, tokens, credentials or sensitive user data to the diagnostic path merely because an agent may need context. Redact or omit at the source.

## Record remediation, do not hide it

Self-healing is useful only when it remains bounded and observable.

Safe local remediation may include, when appropriate to the system:

- idempotent retry for a classified transient failure;
- reconnect/reinitialize an isolated client;
- restart an isolated crash-only/supervised worker;
- trip a circuit breaker or stop sending work to an unhealthy dependency;
- mark a replica not-ready while preserving liveness;
- fall back to a documented safe mode;
- rebuild an invalid disposable cache.

Every automatic action should record:

```text
trigger -> action -> attempt/budget -> result -> resulting state
```

Do not silently retry forever, continuously restart a persistently broken component, or erase the original failure evidence. Recovery loops need explicit budgets/backoff and an escalation state.

## Distinguish health from readiness from correctness

One bit called `healthy` often hides different operational decisions.

Separate questions such as:

- **live?** can this process make progress, or should it be restarted?
- **ready?** should new work/traffic be sent here?
- **correct?** did this operation satisfy its contract?
- **degraded?** can the service safely continue with reduced capability?
- **unknown?** did the diagnostic mechanism itself fail?

A bad health check can cause more damage than the original fault. Never auto-restart merely because a downstream dependency is temporarily slow if the local process is otherwise healthy.

## Symptoms first, causes behind them

For paging/urgent escalation, prefer high-level symptoms that imply real impact. Keep cause-specific diagnostics available for investigation.

This prevents every low-level anomaly from waking an agent/human and avoids coupling alerts to one guessed failure mechanism.

A useful split is:

```text
BEACON: user/job/system outcome is degraded or failed
       -> decide whether intervention is needed

DIAGNOSTICS: correlated causal evidence
       -> determine why and what to change
```

## Sample deliberately

If telemetry volume is high, reduce it with policies that preserve decision-bearing events.

Useful patterns include:

- keep all errors and rare invariant violations;
- keep slow/outlier traces at a higher rate;
- probabilistically sample routine healthy traffic;
- retain exemplars that bridge aggregate metrics to individual traces;
- rate-limit duplicate events while preserving counts;
- dynamically increase detail for a component while an incident is active, then return to normal.

Sampling policy is part of system behavior and should be versioned/tested. An over-aggressive filter that removes the only failing path is not an optimization.

## Build, CI, tests and static analysis should emit machine-readable evidence

Do not make agents parse colorful terminal output if the tool can emit a structured protocol.

Prefer, where available:

- structured test result files;
- compiler JSON diagnostics;
- SARIF for static-analysis findings;
- build event protocols/services rather than scraping build stdout;
- stable failed target/test identifiers;
- artifact references for full logs, coverage, reports and dumps.

The model-facing summary should usually contain counts, failed identities, the shortest useful failure reason, and artifact references. Passing target/test inventories belong in artifacts, not the prompt.

## Automatically minimize failure evidence when the reducer is trustworthy

Some failures can be turned into much cheaper reproductions automatically:

- delta-debug/minimize a failing input;
- `git bisect` or equivalent to isolate a regression range;
- reduce a property/fuzz failure to a minimal counterexample;
- minimize a sequence of operations while preserving the failure;
- select only trace/log events correlated to the failing request and time window.

Keep the original artifact. A reducer can accidentally remove a second relevant symptom even while preserving one failure predicate.

## Design diagnostics as an independent subsystem

Diagnostics that share the exact same assumptions as the failing code can fail with it.

Where consequence justifies the cost:

- keep health checks/simple sentinels simpler than the subsystem they observe;
- verify the telemetry path itself (metamonitoring);
- use independent black-box checks for externally visible behavior;
- keep crash/error reporting robust to partial application failure;
- avoid allocating huge amounts of memory while reporting an out-of-memory failure.

## Diagnostic code has a budget too

Instrumentation costs CPU, I/O, memory, storage, network, privacy surface and developer/agent attention.

Do not add traces/logs to pure deterministic local code merely because observability is fashionable. Instrument where the runtime has meaningful uncertainty or external state:

- process/service boundaries;
- network/storage/API calls;
- long-running/background jobs;
- queues/concurrency/state machines;
- resource limits/backpressure;
- retries/fallbacks/recovery paths;
- expensive or operationally important phases;
- security/trust boundaries;
- code whose failures have historically been difficult to localize.

Keep ordinary internal transforms quiet when their callers/tests already expose enough evidence.

## Diagnostic output should guide the next probe, not pretend to know the root cause

A runtime component can safely report deterministic facts such as:

- `dependency=postgres`
- `attempts_exhausted=3`
- `timeout_ms=5000`
- `db_latency_p95_ms=4800`
- `known_good_p95_ms=42`

It should be cautious about emitting speculative prose such as “root cause is network congestion” unless that conclusion is produced by an independently validated diagnostic mechanism.

Prefer evidence that lets the agent cheaply choose the next query.

## Completion check for diagnostic design

When adding or changing runtime feedback, ask:

1. Can the normal healthy path be understood without verbose logs?
2. Does one failure capsule identify the operation, stable failure class, runtime identity and evidence handles?
3. Can repeated failures be grouped instead of replayed?
4. Can an agent retrieve one correlated slice before the full artifact?
5. Is the original raw evidence retained?
6. Are environmental differences visible without dumping the whole machine?
7. Are automatic recovery actions bounded, observable and non-destructive?
8. Can the monitoring/diagnostic path itself fail visibly?
9. Are secrets and sensitive payloads excluded before storage/model access?
10. Does the telemetry cost match the operational value?

## Related material

- focused skill for adding/changing telemetry and self-checks: [`../../skills/instrumenting-runtime-feedback/SKILL.md`](../../skills/instrumenting-runtime-feedback/SKILL.md)
- focused skill for consuming noisy failure evidence: [`../../skills/diagnosing-runtime-failure/SKILL.md`](../../skills/diagnosing-runtime-failure/SKILL.md)
- experiment protocol: [`../../experiments/diagnostic-feedback.md`](../../experiments/diagnostic-feedback.md)
- research/provenance: [`../../references/diagnostic-feedback-history-2026-09.md`](../../references/diagnostic-feedback-history-2026-09.md)
