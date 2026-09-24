# References

This directory preserves the **research provenance, external framework notes, source links, experiments worth revisiting, and rejected/qualified ideas** behind Agentic Engineering.

It is intentionally **outside the normal agent reading path**.

Ordinary engineering agents should start with [`docs/agent-corpus/README.md`](../docs/agent-corpus/README.md) and load only the operational document needed for the decision at hand. Do not recursively read this directory unless the task is specifically to improve the methodology, audit evidence, compare external approaches, or revisit a design decision.

## Why this separation exists

Research depth and runtime context have opposite incentives:

- maintainers need rich history, competing ideas, citations, examples, and caveats so useful knowledge is not lost;
- execution agents need a small, high-signal working set so instructions do not crowd out the task, source code, diagnostics, and current evidence.

The operational docs should therefore contain the **current decision rule**. This directory should retain the **why, where it came from, competing approaches, limitations, and material that may become useful later**.

## Contents

- [`context-and-instruction-engineering-2026-09.md`](context-and-instruction-engineering-2026-09.md) — research behind the current instruction/context design, including OpenAI, Anthropic/Claude Code, Cursor, GitHub Copilot, LangChain, Promptfoo, DSPy, ACE, long-context research, BMAD, and Superpowers.
- [`agent-legible-code-history-2026-09.md`](agent-legible-code-history-2026-09.md) — historical and modern research behind code designed for cheap future agent localization, reasoning, refactoring, verification, and debugging: punch cards/batch systems, structured programming, Parnas, Cleanroom, JPL/NASA, MISRA, Ravenscar, cFS, Linux, Google testing/review, repository-level LLM research, and agent-first production experience.
- [`agent-semantic-understanding-2026-09.md`](agent-semantic-understanding-2026-09.md) — current evidence on LLM code-semantic reasoning (SemBench, LongCodeU, CodeGlance, CodeSense) and why bounded weak-reader mental-model construction is a better objective than any single complexity metric.
- [`airborne-and-realtime-assurance-2026-09.md`](airborne-and-realtime-assurance-2026-09.md) — FAA/DO-178 assurance, structural-coverage independence, Ravenscar analyzable concurrency, and the risk-scaled lesson of reducing state space before asking intelligence to reason about it.
- [`diagnostic-feedback-history-2026-09.md`](diagnostic-feedback-history-2026-09.md) — deep-space beacon/fault protection, syslog, minidumps/crash reports, Erlang supervision, crash-only/autonomic systems, delta debugging, Dapper/SRE/OpenTelemetry, Kubernetes, structured build/static-analysis protocols, Sentry and progressive diagnostic disclosure.
- [`postmortem-artifact-design-2026-09.md`](postmortem-artifact-design-2026-09.md) — offline crash-evidence design from systemd-coredump, JVM fatal reports, Apple `.ips` reports and Crashpad/minidumps; manifest-first navigation when the failed process cannot be queried.
- [`continuous-flight-recorder-evidence-2026-09.md`](continuous-flight-recorder-evidence-2026-09.md) — Java Flight Recorder and the bounded black-box pattern: continuously retain selected recent events cheaply, then freeze/dump the window when an incident occurs.
- [`diagnostic-escalation-2026-09.md`](diagnostic-escalation-2026-09.md) — deterministic record/replay (`rr`), persistent crash buffers (`pstore`), dynamic tracing/ftrace and the 2026 OpenTelemetry Profiles alpha as escalation mechanisms for hard incidents.
- [`repository-evolution-2026-09.md`](repository-evolution-2026-09.md) — what the repository's early live failures taught about routing checkpoints, proxy acceptance, instruction structure, and behavioral regression tests.
- [`delegation-adherence-2026-09.md`](delegation-adherence-2026-09.md) — archived delegation-specific regression cases and qualitative observations retained after the active protocol was generalized.

- [`agentic-efficiency-frontier-2026-09.md`](agentic-efficiency-frontier-2026-09.md) — September 2026 research on SoL-Pi, thin strong-root/cheap-worker orchestration, selective context management, prefix caching, pre-inference routing, bounded recovery, multi-agent token amplification, and workload-dependent KV serving.

## Promotion rule

A reference insight should move into operational guidance only when it produces a concrete decision rule or mechanism that is useful enough to justify its context/maintenance cost. Preserve the fuller source note here even after promotion.
