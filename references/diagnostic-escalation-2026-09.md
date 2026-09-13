# Diagnostic escalation research — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

Operational guidance: [`../docs/runtime/diagnostic-escalation.md`](../docs/runtime/diagnostic-escalation.md)

## Deterministic record/replay — `rr`

Source: https://rr-project.org/

`rr` records a program execution once and then replays that same execution deterministically under a debugger. Its project documentation emphasizes several properties relevant to agentic diagnosis:

- the failing execution is saved to disk;
- replay can be repeated as many times as needed;
- register/address-space/syscall state is the same on replay;
- reverse execution and data watchpoints help trace effects back to causes;
- recorded traces are durable and portable;
- the original motivation was intermittent failures that may disappear on rerun.

### Agentic lesson

Repeatedly rerunning a nondeterministic failure can invalidate observations and consume model/tool turns. A replay artifact can make diagnostic knowledge **monotonic**: once the agent learns an address, event order or state relation in the recorded failure, that knowledge remains valid on subsequent replay.

Record/replay is not a universal replacement for logs/traces. Platform support, workload overhead and recording size constrain applicability. Treat it as a deep escalation artifact for cases where reproducibility/nondeterminism dominates diagnosis cost.

---

## Linux persistent crash storage — pstore

Sources:

- Linux kernel, *Debugging Kernel Shutdown Hangs with pstore*: https://www.kernel.org/doc/html/latest/power/shutdown-debugging.html
- Linux kernel, pstore block panic/oops logger: https://kernel.org/doc/html/v5.12/admin-guide/pstore-blk.html

The Linux kernel's pstore subsystem can persist crash/hang console data across a reset so it can be retrieved on the next boot. This is an important failure-model lesson: the ordinary logger/process/filesystem path may not survive the incident.

### Agentic lesson

For sufficiently consequential systems, evidence collection should have a lower-level path that can survive the component/system it observes. On restart, a collector can ingest the preserved evidence into the normal postmortem bundle and index it rather than presenting it as raw boot/crash output.

---

## Dynamic ftrace / temporary probes

Source: Linux kernel, *ftrace — Function Tracer*: https://www.kernel.org/doc/html/latest/trace/ftrace.html

The kernel's dynamic ftrace machinery is designed so function tracing can have virtually no overhead while disabled, then be enabled for selected functions when needed.

### Agentic lesson

When a live incident lacks one specific observation, permanent verbose instrumentation is not the only option. A temporary targeted probe can answer the missing question and then expire.

The durable policy is:

- probe narrowly;
- state the hypothesis/question first;
- bound duration/events/overhead;
- correlate and persist the result;
- remove/expire the probe after the incident.

This does not mean agents should be granted arbitrary production tracing permissions. Security, safety and operational controls remain primary.

---

## OpenTelemetry Profiles public alpha (2026)

Source: https://opentelemetry.io/blog/2026/profiles-alpha/

On 2026-03-26 OpenTelemetry announced Profiles as a public-alpha signal, aiming to standardize low-overhead continuous production profiling alongside traces, metrics and logs. The work includes an efficient shared data representation, Collector integration, an eBPF-based reference profiler and ongoing cross-signal correlation work.

The announcement explicitly notes that the signal is still Alpha and should not yet be used for critical production workloads.

### Agentic lesson

Profiles can be another progressively addressable evidence type: the first model view should usually be a hotspot/query result, not the complete profile corpus. Cross-signal correlation allows an agent to ask questions such as which CPU/off-CPU behavior corresponds to a slow trace rather than independently reading two massive datasets.

The maturity caveat matters: operational guidance should treat OTel Profiles as an emerging standard, not a required default.

---

## Shared conclusion

Hard incidents benefit from **escalatable evidence mechanisms**, not permanently maximal telemetry:

```text
cheap normal evidence
    -> bounded recent recorder
    -> replay/persistent crash artifact
    -> temporary targeted probe
```

The next diagnostic level should be chosen because a specific fact is missing, not because “more data” feels safer.
