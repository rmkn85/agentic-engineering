# Offline postmortem artifact design — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

Operational guidance: [`../docs/runtime/postmortem-bundles.md`](../docs/runtime/postmortem-bundles.md)

## Research question

How should diagnostics work when the target program has already crashed, was killed, is wedged, or is otherwise impossible to query?

The key design correction is:

> **progressive diagnostic disclosure must work as persisted artifact navigation, not only as live querying.**

A postmortem system should leave a small durable index that links to multiple resolutions of evidence. A later agent follows only the references relevant to its hypothesis.

---

## systemd-coredump: metadata/summary separate from the large core

Sources:

- `systemd-coredump`: https://www.freedesktop.org/software/systemd/man/systemd-coredump.html
- `coredumpctl`: https://www.freedesktop.org/software/systemd/man/coredumpctl.html

`systemd-coredump` is a strong existing example of postmortem evidence layering. It can log a summary/backtrace and process metadata to the journal while storing the potentially large core dump externally. The journal entry records fields such as PID/UID/GID, terminating signal, executable, timestamp and a `COREDUMP_FILENAME` that points to the stored core when external storage is used.

`coredumpctl` then exposes increasingly deeper operations:

- `list` — compact crash inventory;
- `info` — detailed metadata;
- `dump` — retrieve the actual core;
- `debug` — hand the core to a debugger.

This is effectively an offline progressive evidence interface.

### Agentic lesson

Do not require a model to consume a core merely to learn that a specific executable died from `SIGSEGV` at a particular time. Keep crash identity/metadata cheap and let the agent retrieve the core only when memory/process state is actually needed.

Also note the lifecycle issue: journal metadata and core files can have different retention. An agent-facing manifest should therefore record artifact availability/expiry and not assume every reference remains valid forever.

---

## JVM fatal-error reports: focused crash report plus optional core

Sources:

- Oracle, *Fatal Error Log*: https://docs.oracle.com/en/java/javase/17/troubleshoot/location-fatal-error-log.html
- Oracle, *Fatal Error Reporting*: https://docs.oracle.com/en/java/javase/24/vm/error-reporting.html

On a fatal JVM error, HotSpot writes an `hs_err_pid*.log` report when possible. The report includes the fatal signal/exception, JVM/runtime/configuration information and a highlighted `Problematic frame`; the runtime can also produce a separate core dump.

Oracle's own example shows why layered evidence matters: the first lines can establish that the failure occurred in native code and identify the relevant native frame, while the core remains available for deeper analysis.

The documentation also notes that report generation itself can suffer secondary errors, which is a reminder that crash diagnostics must represent partial/incomplete capture explicitly.

### Agentic lesson

A useful postmortem bundle should keep:

1. a tiny crash identity/summary;
2. a focused application/runtime report;
3. deeper process-state artifacts separately.

The manifest should say when collection was truncated or failed rather than silently implying that absent data was healthy.

---

## Apple `.ips` crash reports: structured incident and crash data

Sources:

- Apple, *Examining the fields in a crash report*: https://developer.apple.com/documentation/xcode/examining-the-fields-in-a-crash-report
- Apple, *Interpreting the JSON format of a crash report*: https://developer.apple.com/documentation/xcode/interpreting-the-json-format-of-a-crash-report

Apple crash reports separate several information classes: incident/process/environment header, exception/termination information, diagnostic messages, crashed thread/backtraces, thread state/registers, binary images and other deeper detail.

Modern iOS/macOS `.ips` reports store structured JSON objects for incident metadata and crash data. That is directly useful for deterministic extraction before a language model is involved.

### Agentic lesson

Postmortem evidence does not need to be one giant textual stack dump. Keep stable typed crash identity/exception fields machine-readable and make thread/register/binary-image detail independently selectable.

---

## Crashpad/minidumps: selected process-state artifact plus report metadata

Sources:

- Crashpad minidump documentation: https://crashpad.chromium.org/doxygen/
- Crashpad report database types: https://crashpad.chromium.org/doxygen/classcrashpad_1_1CrashReportDatabase.html

Crashpad uses minidump structures that capture selected exception/process/system state and maintains crash-report metadata including report identity, path, creation time, upload state/attempts and total size.

### Agentic lesson

A crash artifact should have metadata that can be inspected **before opening the artifact itself**. Size, type, identity, availability and build/environment metadata are part of diagnostic navigation.

---

## The artifact graph should survive a dead process

The useful synthesis is not “ask the application for more logs.” It is:

```text
manifest / crash inventory
        |
        +--> focused stack
        |       +--> symbols/source identity
        |
        +--> recent event ring
        |       +--> trace/correlation slice
        |
        +--> environment delta
        |
        +--> minimized reproducer
        |
        +--> minidump
        |       +--> symbol files
        |
        +--> full log / full trace / core / heap
```

The target application need not exist at diagnosis time.

Live telemetry can be one referenced source while the process is still running, but postmortem correctness must not depend on it.

---

## Capture responsibilities before and after death

A robust design separates three stages.

### Before failure

Maintain bounded state that will matter after death:

- build/release/config identity;
- current operation/phase and correlation IDs;
- bounded recent event ring/flight recorder;
- selected resource counters;
- retry/recovery state;
- reproducibility seed/input reference where safe.

### At failure

Do the minimum reliable capture supported by the runtime/OS:

- crash identity/signal/exception;
- small state/checkpoint pointer;
- trigger external crash reporter/core/minidump facility;
- avoid complicated allocation/locks/formatting inside unsafe fatal paths.

### After failure

A surviving collector/supervisor/CI runner can create higher-value derived artifacts:

- symbolicated app-frame stack;
- relevant event slice;
- environment comparison;
- issue fingerprint/grouping;
- dump/profile summaries;
- compressed raw artifacts;
- integrity/availability metadata.

This is often safer and richer than trying to do everything inside the dying process.

---

## Partial evidence is a state, not an absence

Crash collection may itself fail because of:

- disk full;
- out of memory;
- permission failure;
- corrupted process state;
- missing symbols;
- collector crash;
- retention expiry;
- truncated core/dump size policy.

An agent-facing manifest should represent those facts explicitly:

```json
{
  "ref": "raw/core.zst",
  "status": "truncated",
  "expected": true,
  "available": true,
  "reason": "size_limit"
}
```

Without this, a missing artifact can be mistaken for evidence that the corresponding condition did not occur.

---

## Main operational conclusion

A diagnostic system for agent-maintained software should optimize the **postmortem traversal cost**:

- start with a tiny structured manifest;
- expose artifact size/kind/completeness/purpose before opening;
- preserve multiple evidence resolutions;
- use stable relative/content-addressed references;
- keep raw evidence immutable/retrievable;
- precompute cheap deterministic views after the crash;
- assume live querying may be impossible;
- test diagnosis with the target deliberately dead.

The goal is not fewer crash artifacts. It is **better indexed evidence**.
