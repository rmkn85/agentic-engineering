---
name: diagnosing-runtime-failure
description: Use when diagnosing a runtime crash, exception, failing job/test/build, degraded service, noisy logs, dump, trace, or other failure evidence where reading all available output would be expensive or distracting.
---

# Diagnosing runtime failure

Goal: reach the next correct hypothesis/fix with the least fresh evidence context while preserving access to the original artifacts.

1. **Start from the smallest trustworthy index.** Read the failure capsule, manifest, failed target/test identity, crash header, or equivalent before opening full logs/stacks/dumps.
2. **Decide live vs postmortem.** Do not assume the target still exists. If it crashed or is unreachable, follow artifact references only. If live queries are available, use them as additional evidence, not as a substitute for durable crash artifacts.
3. **Establish identity first.** Confirm release/build/commit, runtime, environment/config fingerprint, operation and correlation IDs. A wrong binary/environment assumption can invalidate every later inference.
4. **Classify facts, not causes.** Record what is directly known: exit/signal/error code, failed boundary, phase, attempts, resource state and automatic remediation. Keep hypotheses explicitly separate.
5. **Follow one evidence edge that answers one question.** Open the application-frame stack to localize code; recent correlated events to reconstruct preceding activity; environment delta to test environmental change; trace slice for cross-service causality; dump/profile only when earlier levels lack the required state.
6. **Prefer targeted extraction over whole-artifact ingestion.** Search/filter/index raw logs, traces, dumps and build/test artifacts deterministically and give the model only the relevant slice plus a reference to the source artifact.
7. **Collapse repetition.** Work from failure fingerprint + counts + representative examples. Do not reread thousands of identical stacks/events unless variation itself is the question.
8. **Inspect recovery history before repeating actions.** Know which retries, reconnects, restarts, fallbacks or cache rebuilds already ran and what happened.
9. **Compare with known-good state.** Prefer explicit environment/config/runtime/resource deltas over speculative “code bug vs environment” arguments.
10. **Escalate evidence depth deliberately.** State the unanswered question before opening a larger artifact. For hard intermittent/timing failures, consider an already-captured bounded flight recorder or deterministic replay artifact before generating more prose logs. If the target is still alive and the missing fact was never instrumented, a temporary targeted probe may be cheaper than permanently broad instrumentation. See `docs/runtime/diagnostic-escalation.md` only when needed.
11. **Minimize a reproducible failure when practical.** Shrink failing input/event sequence, isolate a regression range, or reduce the correlated trace/log set while retaining the original evidence.
12. **Validate the diagnosis independently.** Reproduce, run a targeted test, check an invariant, or use an independent signal before claiming root cause. A plausible narrative is not sufficient.
13. **Return a compact evidence-backed result.** Include observed failure, supported hypothesis/root cause if established, relevant evidence references, the proposed/implemented action, and unresolved uncertainty.

For bundle navigation conventions, read `docs/runtime/postmortem-bundles.md`. For instrumentation/recovery design, use `instrumenting-runtime-feedback` rather than expanding this diagnosis task into a telemetry redesign.
