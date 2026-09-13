# Diagnostic feedback research and historical lineage — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

Operational guidance distilled from this research lives in [`../docs/runtime/diagnostic-feedback.md`](../docs/runtime/diagnostic-feedback.md).

## Research question

How should software expose runtime, build, test and failure evidence so that a coding agent can diagnose the next problem with the least fresh model context and repeated exploration, while preserving enough original evidence to avoid misleading compression?

The question includes ordinary logging/telemetry as well as self-checking, self-monitoring, bounded recovery, crash artifacts, CI/build protocols and automatic failure reduction.

The governing tension is:

```text
more evidence can improve diagnosis
but
more raw evidence can consume model context, attention, latency and money
```

The durable answer across several generations of engineering is not simply “log less.” It is **hierarchical/progressive evidence**: cheap coarse state first, stable identifiers for correlation, richer evidence retained behind it, and automatic local handling only where the policy is safe and bounded.

---

## 1. Deep Space 1 Beacon Monitor: onboard summarization before expensive contact

Primary sources:

- JPL, *Deep Space 1 — Beacon Monitor*: https://www.jpl.nasa.gov/nmp/ds1/tech/beacon.html
- NASA/JPL NTRS, *Lessons Learned During Implementation and Early Operations of the DS1 Beacon Monitor Experiment*: https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20000056912.pdf
- NASA, *Basics of Space Flight — Telecom / Beacons*: https://science.nasa.gov/learn/basics-of-space-flight/chapter10-1/

Deep Space 1 demonstrated a strikingly relevant idea. Instead of routinely downlinking full engineering telemetry for ground staff to process, onboard software summarized spacecraft health and selected one of four easily detectable tones indicating how urgently full contact was needed.

The NTRS paper explicitly frames the technology as reducing the frequency/volume of engineering telemetry downlink and reducing routine ground telemetry processing/analysis. The spacecraft performs a first-stage health assessment locally; expensive bandwidth and operator attention are consumed only when the beacon indicates that deeper contact is warranted.

### Agent-era translation

This is the core analogy for agent-facing diagnostics:

```text
runtime does cheap local summarization
        ↓
beacon / compact structured state
        ↓ only if needed
correlated focused evidence
        ↓ only if needed
full raw telemetry / dump / trace
```

The lesson is **not** that four states are universally correct. It is that the system closest to the evidence can often cheaply compress routine state into a decision-bearing representation while retaining a path to deeper data.

### What not to copy blindly

A spacecraft beacon is optimized for extreme communication scarcity and delayed intervention. Ordinary software can afford much richer local storage and interactive querying. Therefore preserve raw evidence locally/cloud-side and make it addressable rather than throwing it away.

---

## 2. Spacecraft fault protection and safing: local mitigation before round-trip human control

Source:

- NASA, *Basics of Space Flight — Onboard Systems*: https://science.nasa.gov/learn/basics-of-space-flight/chapter11-1/

NASA notes that light-time and constrained tracking schedules mean robotic spacecraft cannot depend on immediate ground response. Fault-protection algorithms monitor conditions and can request actions such as safing: shutting down/reconfiguring components to prevent damage and restore contact capability.

### Agent-era translation

Some faults should be handled locally before escalation when the response is well understood and safer than waiting:

- bounded retry of a classified transient operation;
- restart of an isolated supervised/crash-only worker;
- circuit-break/stop traffic to an unhealthy dependency;
- safe-mode/read-only/degraded operation;
- rebuild of disposable derived state.

The important constraint is **bounded and observable autonomy**. A recovery action should preserve the original failure evidence and report what was tried. Infinite retries or silent fallbacks make later diagnosis harder.

---

## 3. Syslog: severity and structured data as early compression/routing primitives

Primary source:

- RFC 5424, *The Syslog Protocol*: https://www.rfc-editor.org/info/rfc5424/

Syslog standardizes event notification transport with severity levels and structured-data elements. RFC 5424 defines severity values from Emergency through Debug and provides structured name/value data rather than relying only on free text.

### Durable lesson

Long before modern observability stacks, systems needed two things that remain valuable to agents:

1. a cheap way to distinguish urgency/importance;
2. machine-parseable fields for filtering/routing without understanding prose.

Severity alone is not enough — projects often misuse INFO/WARN/ERROR — but a stable event schema plus severity/impact class lets deterministic tooling remove large amounts of irrelevant text before any LLM sees it.

---

## 4. Minidumps: preserve the useful subset before reaching for the full state image

Current sources:

- Microsoft, *Minidump Files*: https://learn.microsoft.com/en-us/windows/win32/debug/minidump-files
- Microsoft, *User-mode Dump Files*: https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/user-mode-dump-files

Microsoft describes minidumps as a useful subset of full crash state that can be created quickly and efficiently and transmitted more easily. Different minidump options allow deliberate control over which threads/modules/memory are included.

### Agent-era translation

Crash state should be **tiered evidence**:

- start with exception/error identity + in-application frames + build/symbol identity;
- attach/select a minidump when stack/log evidence is insufficient;
- keep larger/full dump capability for cases that actually need memory/handle/heap state.

Do not paste binary/full dump-derived text into the model by default. Query/symbolicate/extract a focused view first and retain the artifact handle.

---

## 5. Erlang/OTP supervision: make recovery structure explicit

Sources:

- Erlang/OTP Design Principles — Supervision Trees: https://www.erlang.org/doc/system/design_principles.html
- Erlang supervisor reference: https://www.erlang.org/doc/apps/stdlib/supervisor.html

OTP structures fault-tolerant applications around workers and supervisors. Supervisors monitor children and restart them according to explicit strategies.

### Agent-era translation

Fault handling becomes cheaper to reason about when ownership/recovery policy is structural rather than duplicated across arbitrary catch/retry blocks.

Useful general ideas:

- isolate failure domains;
- centralize restart policy;
- make retry/restart intensity explicit;
- keep worker logic focused on work, not improvised self-resurrection;
- surface supervisor/restart history as diagnostic evidence.

Do not interpret “let it crash” as “ignore errors.” It depends on containment, restartability and observable supervision.

---

## 6. Crash-only software: simplify stop/recovery paths

Primary source:

- Candea & Fox, *Crash-Only Software* (HotOS IX, 2003): https://www.usenix.org/conference/hotos-ix/crash-only-software

Crash-only software proposes components that stop by crashing and start by recovery, reducing the number of distinct shutdown/startup paths and encouraging fast component-level recovery.

### Agent-era translation

A component can be easier to diagnose and recover when there are fewer lifecycle modes and recovery is idempotent/tested. This can reduce both runtime state space and agent reasoning.

Qualify heavily: many systems require graceful transactional shutdown, data durability or external protocol cleanup. Use the principle only where crash/restart semantics are safe.

---

## 7. IBM autonomic computing: monitor → analyze → plan → execute with knowledge

Primary sources:

- IBM Research, *An architectural approach to autonomic computing* (ICAC 2004): https://research.ibm.com/publications/an-architectural-approach-to-autonomic-computing
- IBM Research, *Autonomic computing: Architectural approach and prototype*: https://research.ibm.com/publications/autonomic-computing-architectural-approach-and-prototype

IBM's autonomic-computing work sought self-configuration, self-optimization, self-healing and self-protection through explicit interfaces/behavioral requirements and feedback loops commonly summarized as MAPE-K (Monitor, Analyze, Plan, Execute over Knowledge).

### Agent-era translation

Self-healing should not be an ad-hoc catch block. Separate:

- observation;
- classification/analysis;
- policy/decision;
- action;
- retained state/knowledge.

For ordinary software the loop can be very small. The key is that automatic recovery has an explicit policy and leaves a trace of the trigger/action/result for later diagnosis.

---

## 8. Delta Debugging: automatically shrink evidence while preserving the failure predicate

Primary source:

- Andreas Zeller & Ralf Hildebrandt, *Simplifying and Isolating Failure-Inducing Input*: https://www.st.cs.uni-saarland.de/papers/tse2002/

Delta Debugging automatically reduces failing inputs/sequences to smaller cases that still reproduce the failure. The classic Mozilla case reduced 95 user actions to 3 and hundreds of HTML lines to a single failure-inducing line.

### Agent-era translation

Failure minimization is literally context minimization with a correctness predicate.

When a deterministic reproducer exists, agents/tools should consider:

- minimizing fuzz/property-test counterexamples;
- shrinking request/event sequences;
- reducing fixtures;
- isolating a change/regression range (`git bisect` family of techniques);
- retaining both original and minimized artifacts.

This is often far more valuable than asking a model to reason through the original huge input.

---

## 9. Google Dapper: ubiquitous tracing made affordable through small instrumentation surface and sampling

Primary source:

- Google, *Dapper, a Large-Scale Distributed Systems Tracing Infrastructure* (2010): https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/

Dapper's design goals included low overhead, application transparency and ubiquitous deployment. Google highlights sampling and instrumentation concentrated in a small number of common libraries as key design choices.

### Agent-era translation

Do not sprinkle bespoke trace/log logic across every function.

Prefer:

- instrumentation at shared boundaries/framework layers;
- propagated correlation IDs;
- sampling policies that preserve useful outliers/errors;
- stable semantic conventions across languages/components.

This makes runtime evidence both cheaper to collect and easier for agents to query consistently.

---

## 10. Google SRE / Prometheus: aggregate symptoms first, causes on demand

Sources:

- Google SRE, *Monitoring Distributed Systems*: https://sre.google/sre-book/monitoring-distributed-systems/
- Prometheus, *Alerting*: https://prometheus.io/docs/practices/alerting/
- Prometheus, *The Zen of Prometheus*: https://prometheus.io/docs/practices/the_zen/

Google's SRE book popularized the four golden signals: latency, traffic, errors and saturation. Prometheus guidance recommends keeping alerts simple, alerting primarily on symptoms associated with user impact, minimizing non-actionable alerts, and using richer consoles/diagnostics to find causes.

### Agent-era translation

An agent should not be awakened by every internal anomaly.

Use a hierarchy:

- symptom/contract failure decides **whether intervention is needed**;
- causal telemetry decides **what to inspect/fix**.

This reduces noise and prevents alert definitions from encoding a brittle guess about the root cause.

Metamonitoring is also important: the telemetry/alert path itself must be checked, otherwise silence can be mistaken for health.

---

## 11. OpenTelemetry: one correlated model across logs, traces, metrics and profiles

Current sources (reviewed 2026-09-13):

- Logs data model: https://opentelemetry.io/docs/specs/otel/logs/data-model/
- Logs concepts: https://opentelemetry.io/docs/concepts/signals/logs/
- Semantic conventions: https://opentelemetry.io/docs/concepts/semantic-conventions/
- Metrics/exemplars: https://opentelemetry.io/docs/specs/otel/metrics/data-model/
- Collector processors: https://opentelemetry.io/docs/collector/components/processor/
- Tail sampling example: https://opentelemetry.io/docs/demo/sample-configurations/tail-sampling-service-criticality/

OpenTelemetry now provides a stable log data model, trace-context fields on logs, semantic conventions across logs/traces/metrics/profiles/resources, and exemplars that link aggregate metric values to specific traces. Collector processors can filter, transform, redact, sample and prune telemetry.

The current tail-sampling examples preserve errors and selected slow/critical traces while sampling ordinary traffic more aggressively.

### Important detail: JSON is not automatically structured

OpenTelemetry explicitly distinguishes structured logs from merely JSON-encoded logs. Stable schema/typed semantics are what make downstream deterministic processing reliable.

### Agent-era translation

A strong default architecture is:

```text
aggregate metric / health summary
       ↓ exemplar/correlation ID
representative trace
       ↓ event IDs
structured logs / exceptions
       ↓ artifact ref if needed
full logs/profile/dump
```

This is progressive disclosure applied to observability.

### Caveats

Tail sampling and processing are not free. Tail samplers retain state and can become a scaling concern. Filtering/sampling policies can remove evidence if misconfigured. Instrumentation must have an explicit cost/error budget.

---

## 12. Kubernetes probes and self-healing: distinguish kinds of health and beware destructive diagnostics

Current sources:

- Kubernetes, *Liveness, Readiness, and Startup Probes*: https://kubernetes.io/docs/concepts/workloads/pods/probes/
- Kubernetes, *Self-Healing*: https://kubernetes.io/docs/concepts/architecture/self-healing/

Kubernetes distinguishes startup, liveness and readiness because they imply different actions. A liveness failure may restart the container; readiness failure removes it from traffic without killing it. The docs explicitly caution that misconfigured liveness probes can create cascading failures.

### Agent-era translation

Avoid one ambiguous `healthy=false` bit.

The diagnostic should communicate **what decision the state supports**:

- cannot make progress → restart may help;
- temporarily cannot serve → drain traffic but keep state/process;
- operation contract failed → report error but process may be fine;
- degraded safe mode → keep running with reduced service;
- health check unknown → do not treat as proof of failure.

Automatic remediation must match the state, not just the severity label.

---

## 13. Build Event Protocol: programmatic build evidence instead of scraping terminal text

Sources:

- Bazel Build Event Protocol: https://bazel.build/remote/bep
- Bazel source docs: https://bazel.googlesource.com/bazel/+/master/site/en/remote/bep.md

Bazel's Build Event Protocol exposes build/test progress/results as structured protocol-buffer events and explicitly aims to make parsing command-line output unnecessary.

### Agent-era translation

CI/build integration should prefer structured native output whenever available.

Instead of giving an LLM thousands of lines of compiler/build chatter, query the event stream for:

- failed targets/tests;
- aborted phases;
- exit/status codes;
- relevant configuration;
- produced artifacts;
- links to retained stdout/stderr.

---

## 14. SARIF: standard structured interchange for static-analysis findings

Primary source:

- OASIS, *Static Analysis Results Interchange Format (SARIF) v2.1.0*: https://www.oasis-open.org/standard/sarifv2-1-os/

SARIF exists because developers use many analysis tools and aggregation is harder when every tool emits a different format. It standardizes machine-readable findings and location/rule metadata.

### Agent-era translation

Agents should consume structured findings (`rule`, `severity`, `location`, `message`, fix metadata where available) rather than reparsing formatted linter output. Combine/deduplicate findings before model ingestion and retain raw reports as artifacts.

---

## 15. Sentry: failure grouping, aggregate metadata and explicit LLM-ready representations

Current sources (reviewed 2026-09-13):

- issue grouping hashes: https://docs.sentry.io/api/events/list-an-issues-hashes/
- retrieve issue event with `llmFormat`: https://docs.sentry.io/api/events/retrieve-an-issue-event/
- trace metadata: https://docs.sentry.io/api/discover/retrieve-trace-metadata/
- Seer issue fix API: https://docs.sentry.io/api/seer/start-seer-issue-fix/

Sentry groups repeated events into issues using grouping signatures/fingerprints, exposes aggregate trace metadata separately from full trace/event bodies, and its current APIs can render issue events directly in JSON/Markdown/XML formats for LLM consumption. Its Seer issue-fix workflow can perform root-cause analysis, propose a solution, generate code changes and hand work to coding agents.

### Why this is important evidence

This is no longer a theoretical “LLM-friendly logs” idea. Production observability products are explicitly adding **machine/LLM consumption surfaces distinct from the raw event body**.

The transferable mechanism is:

- group repetitions;
- expose aggregate metadata;
- select a representative event;
- render a stable compact representation for the reasoning system;
- preserve full event/trace data behind references.

Do not adopt a vendor-specific schema as a universal standard; adopt the layering.

---

## 16. Independent diagnostics and common-mode failure

Diagnostics should not depend on the exact same assumptions as the subsystem they observe.

Examples across domains include:

- external/black-box checks alongside internal metrics;
- simple supervisors watching more complex workers;
- crash reporters designed to operate in damaged process conditions;
- behavioral tests derived from contracts instead of reproducing implementation logic;
- watchdogs/safing logic with small, constrained responsibilities.

### Agent-era translation

If telemetry is produced only by the code path that is currently broken, absence/malformed telemetry can mislead the agent. Where the consequence warrants it, preserve an independent signal that the telemetry source itself is alive and trustworthy.

---

## Main synthesis: progressive diagnostic disclosure

The recurring architecture across spacecraft, operating systems, observability and modern AI debugging is:

```text
cheap stable state/urgency
        ↓
structured diagnostic capsule
        ↓
correlated focused evidence
        ↓
raw retained artifact
```

This gives the next agent a bounded first view while preserving evidence fidelity.

The system should optimize **expected diagnostic work**, not raw telemetry volume in isolation.

A useful conceptual objective is:

```text
diagnostic efficiency =
  accepted root-cause/fix quality
  -----------------------------------------------
  fresh evidence tokens + probes + retries + time
```

Do not turn this into a universal scalar without workload-specific weights.

---

## Anti-patterns to avoid

### Raw-output dumping

Every failure automatically pastes the full stack, all logs and environment dump into the agent context.

### Evidence deletion disguised as compression

Only a one-line summary is kept, so the agent cannot challenge the summarizer or inspect an exceptional case.

### Text scraping when a protocol exists

The agent regexes terminal output even though the tool exposes JSON/SARIF/BEP/JUnit/OTLP/etc.

### Retry amnesia

The runtime retries/restarts/falls back but does not report what it already attempted, so the agent repeats the same action.

### Duplicate-event amplification

The same stack occurs 50,000 times and is presented 50,000 times rather than grouped with frequency/representative examples.

### Uncorrelated observability

Logs, metrics and traces exist but cannot be joined by request/job/release/environment identity.

### Health-action confusion

A dependency outage causes a liveness restart storm because `healthy=false` was used for every failure state.

### Speculative diagnostics presented as fact

The runtime prints a guessed root cause instead of the measured facts that support the next probe.

### Environment firehose

Every incident dumps all environment variables/packages/process state instead of a baseline fingerprint and relevant deltas — often leaking secrets in the process.

### Instrumentation everywhere

Pure local functions emit verbose traces/logs even though their behavior is already covered by deterministic tests/callers.

---

## Research-backed design rules promoted to operational guidance

1. **Beacon first:** give a stable outcome/urgency state before detailed evidence.
2. **Structure facts:** event codes, IDs, state and measurements should not require prose parsing.
3. **Correlate signals:** IDs connect metrics → trace → events → artifacts.
4. **Preserve raw evidence:** compact first view must be reversible through references.
5. **Group repetition:** report issue/fingerprint + count + representative event.
6. **Sample by decision value:** errors/outliers retain richer evidence than ordinary success paths.
7. **Make environment comparable:** fingerprint + delta beats full machine dump.
8. **Record recovery history:** automatic actions are evidence.
9. **Separate health decisions:** liveness/readiness/correctness/degradation are not interchangeable.
10. **Prefer machine protocols:** structured build/test/static-analysis outputs before terminal parsing.
11. **Automate reduction:** minimize reproducible failures before asking a model to reason over huge inputs.
12. **Instrument selectively:** observability has runtime/context/privacy cost.
13. **Keep diagnostics independent enough to survive the failure they report.**
14. **Treat LLM rendering as a view over evidence, not the evidence itself.**

