# Runtime feedback

Runtime diagnostics are part of Agentic Engineering because every emitted byte may later become fresh model context.

The governing pattern is **progressive diagnostic disclosure**:

```text
compact outcome / beacon
        ↓
structured diagnostic capsule or postmortem manifest
        ↓
focused correlated evidence
        ↓
retained raw artifact
```

The target may be alive, dead, wedged or unreachable. A robust design therefore treats persisted evidence as the durable contract; live querying is optional.

## Guidance

- [`diagnostic-feedback.md`](diagnostic-feedback.md) — logging, metrics, traces, profiles, health checks, self-healing, grouping/sampling, CI/build/test diagnostics and general evidence economics.
- [`postmortem-bundles.md`](postmortem-bundles.md) — crash-safe/offline evidence bundles whose small manifest links to progressively deeper files such as stack slices, recent events, environment deltas, minidumps, cores and full logs.
- [`diagnostic-escalation.md`](diagnostic-escalation.md) — only for harder cases: bounded flight recorders, deterministic record/replay, lower-level persistent crash buffers and temporary dynamic probes.

## Skills

- [`../../skills/instrumenting-runtime-feedback/SKILL.md`](../../skills/instrumenting-runtime-feedback/SKILL.md) — design or change the feedback producer.
- [`../../skills/diagnosing-runtime-failure/SKILL.md`](../../skills/diagnosing-runtime-failure/SKILL.md) — consume failure evidence progressively.

## Evaluation

- [`../../experiments/diagnostic-feedback.md`](../../experiments/diagnostic-feedback.md) — compare raw-first diagnostics with progressive evidence at the same underlying diagnostic fidelity.

Historical research and source notes live under [`../../references/`](../../references/README.md) and are not part of normal runtime context.
