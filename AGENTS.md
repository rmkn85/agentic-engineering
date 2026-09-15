# AGENTS.md

This repository is a public knowledge base about executing the **same authorized engineering work** with less model usage, wall time, repeated computation, retries, and human effort while preserving the requested result and quality.

## Normal reading boundary

For ordinary work, use this file plus [`docs/agent-corpus/README.md`](docs/agent-corpus/README.md) as the default operating corpus. Load deeper operational docs only when the current decision needs them.

**Do not recursively crawl `references/`.** It preserves external research, provenance, competing ideas, and historical rationale for maintainers improving this methodology. Read it only for methodology research/audit work.

## Execution invariants

- Preserve the task, success criteria, source coverage, permissions, and quality bar; optimize execution, not scope.
- Use deterministic tools for mechanical work. Keep logs on disk; workers return status, decisions, and evidence paths. The coordinator reads only decision-critical excerpts: consumed logs keep taxing later context.
- Before a substantial batch, choose the cheapest adequate executor: exact tool, bounded worker, orchestrator, or capability-selected specialist. The coordinator need not be the strongest model: it may route one bounded, coupled decision to a stronger available specialist, then resume cheaper execution. Do not add fan-out without a concrete benefit.
- Treat context as a working set. Keep always-loaded guidance small; prefer path-scoped rules, on-demand skills, isolated worker context, and retrievable references when they are sufficient.
- Reuse valid semantic and deterministic work until an input that can affect it changes.
- Use targeted validation while iterating and broader acceptance at integration/final boundaries. Structural checks, worker completion, and green links/tests are not substitutes for the requested substantive outcome.
- Treat platform defaults as the baseline. Benchmark consequential or workload-dependent deviations; do not turn benchmarking into ceremony.

## Instruction discipline

A persistent instruction is recurring context. Before adding one, ask what observed failure it addresses, whether it matters to nearly every task, and whether code/config/test/path scoping/on-demand loading can solve it more cheaply.

For important behavior changes, establish the baseline when practical, add the smallest intervention, then test the behavior inside the normal instruction stack. Repeated non-adherence should trigger better scoping, deterministic enforcement, or a more capable orchestrator before unlimited prompt growth. See [`experiments/instruction-context-adherence.md`](experiments/instruction-context-adherence.md).

## Contribution rules

- Keep guidance domain-neutral unless explicitly a case study.
- Never copy private repository content, proprietary code, credentials, internal URLs, or confidential project details here.
- Do not publish personal environment identifiers or configuration: personal usernames or account URLs unrelated to public project/source identity, host/runner names, private addresses, workstation paths, hardware inventory, operating-system installation details, driver inventory, or copied personal config. Preserve only the minimum capability, dependency version, and evidence limitation needed to support a claim, using neutral placeholders where concrete values are unnecessary.
- Distinguish **documented behavior**, **measured result**, and **engineering hypothesis**.
- Prefer mechanisms and decision rules over vendor-specific prompt folklore.
- For vendor/model behavior that may change, include a review date and authoritative source where practical.
- Do not turn a local workaround or anecdote into a universal rule without scope, counterexamples, and appropriate evidence.
- Keep runtime guidance concise; preserve deeper research and rationale under `references/` instead of deleting it.

## Quality bar for a practice

A useful practice should make clear:

1. what inefficiency/failure it addresses;
2. the mechanism and proposed change;
3. what it may save and what it may cost;
4. when not to use it;
5. how the same outcome/quality is verified;
6. what evidence supports it and what would revise it.
