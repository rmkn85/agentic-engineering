# Postmortem diagnostic bundles

A failed program may no longer exist to answer questions. Agent-efficient diagnostics must therefore work **offline**.

The primary post-crash interface should be an immutable or append-only **diagnostic bundle** whose first file is a compact manifest/index and whose deeper files preserve progressively richer evidence.

The agent explores the bundle by following references, not by loading every artifact at once.

## Core shape

```text
failure-20260913T070000Z-7f2c/
  manifest.json                 # start here
  summary.md                    # optional concise human/agent rendering

  focused/
    application-stack.txt       # short symbolicated app-frame chain
    failure-excerpt.log         # bounded relevant log slice
    recent-events.jsonl         # bounded flight-recorder events
    environment-delta.json      # differences from known-good baseline
    failed-checks.json          # assertion/test/invariant failures
    trace-slice.json            # correlated failing request/job only
    minimized-input.json        # if automatic reduction succeeded

  state/
    last-checkpoint.json        # last durable/diagnostic state snapshot
    counters.json               # selected bounded runtime counters
    remediation.json            # retries/restarts/fallbacks already attempted

  raw/
    stdout-stderr.log
    trace.otlp.json
    profile.pb.gz
    minidump.dmp
    core.zst
    heap.hprof

  symbols/
    build-id.txt
    symbol-manifest.json
```

Projects should produce only the artifacts that help their failure modes. The directory above is a vocabulary, not a required checklist.

## `manifest.json` is the navigation interface

The manifest should be cheap to read and sufficient to choose the next artifact.

Example:

```json
{
  "schema": "agent-postmortem-v1",
  "bundle_id": "failure-20260913T070000Z-7f2c",
  "status": "CRASH",
  "event": "WORKER_SEGFAULT",
  "occurred_at": "2026-09-13T07:00:00Z",
  "component": "image-worker",
  "operation": "decode-frame",
  "release": "git:abc123",
  "environment": "linux-x86_64/config:9f20",
  "cause": {
    "type": "SIGSEGV",
    "application_frame": "decoder.cc:418"
  },
  "summary": "Worker terminated while decoding one frame",
  "evidence": [
    {
      "id": "app-stack",
      "kind": "stack",
      "ref": "focused/application-stack.txt",
      "bytes": 1842,
      "priority": 1,
      "use_when": "localize the crashing application path"
    },
    {
      "id": "recent-events",
      "kind": "events",
      "ref": "focused/recent-events.jsonl",
      "bytes": 9234,
      "priority": 2,
      "use_when": "reconstruct activity immediately before the crash"
    },
    {
      "id": "core",
      "kind": "core-dump",
      "ref": "raw/core.zst",
      "bytes": 734003200,
      "priority": 9,
      "use_when": "stack/events are insufficient and memory/process state is needed"
    }
  ]
}
```

Useful evidence metadata includes:

- `id` — stable within the bundle;
- `kind` / media or schema type;
- `ref` — relative path or immutable artifact URI;
- size before the agent opens it;
- checksum/content digest when integrity matters;
- whether it is complete, sampled, reduced, truncated or redacted;
- priority or expected diagnostic cost;
- `use_when` / short purpose description;
- sensitivity/access classification;
- parent/correlation relation when the bundle is a graph rather than a flat list.

The manifest should describe evidence, not guess a root cause beyond what the crash collector can establish reliably.

## A graph, not one giant report

Different evidence answers different questions. Keep references between artifacts explicit.

For example:

```text
manifest
  -> application stack
       -> source/build identity
  -> recent event ring
       -> trace ID
            -> trace slice
                 -> dependency event
  -> environment delta
       -> dependency/runtime versions
  -> minidump
       -> symbols
```

An agent can stop as soon as it has enough evidence for the next correct action.

Do not concatenate these files into `everything.txt`; that destroys the navigation advantage.

## Live querying is optional

When a process or service is still reachable, the manifest may include query handles:

```json
{"kind":"live-metrics","ref":"query://service/image-worker/metrics"}
```

But every critical post-failure path should assume the process may be dead, partitioned, wedged, or too damaged to respond.

The bundle is therefore the durable contract. Live inspection is an optimization layered on top.

## Capture before the failure destroys the evidence

Some state must be preserved **before** a crash:

- release/build/config fingerprints;
- bounded recent structured events in a ring buffer;
- current phase/state-machine state;
- operation/request/job correlation IDs;
- selected resource counters;
- active retry/fallback budget;
- reproducibility seed/input reference where safe;
- build/symbol identity.

Prefer bounded structures whose memory/storage cost is known.

A small in-memory flight recorder that keeps the last N decision-bearing events can be more useful than gigabytes of INFO logs after the process dies.

## Let a separate collector survive the target

A process handling its own catastrophic failure may be exactly the component least able to allocate memory, perform complex I/O or serialize rich state.

When consequence/value justifies it, use a simpler external mechanism:

- OS/core-dump facility;
- crash reporter/helper process;
- supervisor/sidecar;
- parent process;
- CI runner/build system;
- runtime-specific fatal-error reporter.

The application can publish small pre-crash context/checkpoints; the surviving collector can assemble/index the final bundle after termination.

This reduces common-mode failure between the application and its diagnostics.

## Crash-path code must itself be constrained

Do not put a sophisticated observability pipeline inside a signal/fatal-error path unless the runtime explicitly supports it.

Crash-path logic should normally be:

- minimal;
- bounded;
- low-allocation or preallocated where appropriate;
- careful about locks/reentrancy;
- tolerant of partially corrupted application state;
- able to fail without destroying already captured evidence.

Runtime/OS-specific crash-handler rules take precedence over generic guidance.

## Write artifacts atomically where practical

Avoid a crash bundle whose existence falsely implies completion.

Useful techniques include:

- write to a temporary path then rename/commit atomically;
- include `complete`, `truncated`, `collector_error` or equivalent status in the manifest;
- checksum important artifacts;
- write the small manifest skeleton early, then append/replace it with artifact status as collection progresses;
- keep raw artifacts even if later symbolication/reduction fails.

A partially captured bundle can still be useful if the agent knows which parts are incomplete.

## Precompute cheap views after the crash

The dead process cannot answer, but a surviving deterministic collector can often prepare cheap derived views before an LLM sees anything:

- symbolicate stack addresses;
- identify in-application frames;
- select recent events sharing the failed correlation ID;
- compute an environment fingerprint/delta;
- extract failed test/build/static-analysis records;
- generate heap/profile top-N summaries;
- count/group repeated exceptions;
- minimize a reproducible input;
- compress large raw artifacts.

Derived files should link back to the raw source artifact and record how they were produced.

## Preserve multiple resolutions

A strong bundle deliberately stores several resolutions because different failures stop at different depths.

Example stack hierarchy:

```text
stack-summary.json        # exception/signal + top relevant app frame
application-stack.txt     # only symbolicated in-project frames / causal exceptions
full-stack.txt            # all frames/threads if text-sized
minidump.dmp              # selected process snapshot
core.zst                  # full/large process memory state
```

The agent starts from the first and moves downward only when the current hypothesis requires information not represented there.

The same idea applies to logs, traces, profiles and build output.

## Keep artifact references stable

A diagnostic summary is far more useful when an agent can reliably reopen the referenced evidence later.

Prefer:

- relative paths within an immutable bundle;
- content-addressed objects;
- artifact-store IDs with retained metadata;
- explicit expiration/availability status;
- release/build IDs that resolve symbols/source.

Avoid transient terminal offsets or “see the log above” references that disappear across sessions.

## Privacy and secret handling must happen before persistence

Postmortem bundles are attractive places to accidentally preserve secrets, user data, environment variables, request payloads or memory.

Treat each artifact type according to its sensitivity:

- allowlist useful environment metadata rather than dumping all variables;
- redact credentials before structured event persistence;
- restrict/expire dumps with memory content;
- mark sensitivity/access requirements in the manifest;
- never send a raw sensitive artifact to a language model merely because it exists.

## Test the bundle under failure

A diagnostic design is incomplete until it has been exercised when the target is unavailable.

Useful tests include:

- forced language exception/unhandled rejection;
- abort/segmentation fault where appropriate;
- out-of-memory or disk-full simulation where safe;
- killed/wedged child worker;
- logging backend unavailable;
- crash while telemetry is being emitted;
- truncated/corrupted artifact;
- missing symbols;
- bundle persistence denied or out of space.

Acceptance is not “the logger printed something.” Verify that a fresh agent can start from the manifest, follow a small number of references, and obtain enough trustworthy evidence for the next diagnostic decision.

## Historical precedents

This pattern is already visible in mature crash infrastructure:

- `systemd-coredump` stores concise journal metadata/backtrace and can retain the large core externally for later retrieval;
- JVM fatal-error reporting writes a focused `hs_err_pid` report and can separately retain a core;
- Apple crash reports separate incident/environment/exception information from deeper thread/register/binary-image detail and use structured `.ips` JSON;
- minidump/crash-report systems preserve selected process state plus metadata rather than requiring the original process to remain queryable.

The agentic change is to make that hierarchy **explicitly navigable and cost-aware for model consumption**.

## Related material

- broader runtime feedback design: [`diagnostic-feedback.md`](diagnostic-feedback.md)
- diagnostic producer skill: [`../../skills/instrumenting-runtime-feedback/SKILL.md`](../../skills/instrumenting-runtime-feedback/SKILL.md)
- diagnostic consumer skill: [`../../skills/diagnosing-runtime-failure/SKILL.md`](../../skills/diagnosing-runtime-failure/SKILL.md)
- experiment: [`../../experiments/diagnostic-feedback.md`](../../experiments/diagnostic-feedback.md)
