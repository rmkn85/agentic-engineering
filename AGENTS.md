# AGENTS.md

This repository is a public professional knowledge base about making agentic engineering execution more efficient while preserving the task, required result, and quality bar.

## Scope invariant

Do not prescribe project goals, product architecture, backlog structure, or domain methodology here. Optimize *how the same authorized engineering work is executed*: model usage, context, tools, caching, validation, concurrency, wall time, compute, retries, and human effort.

## Contribution rules

- Keep guidance domain-neutral unless a section is explicitly a case study.
- Never copy private repository content, proprietary code, credentials, internal URLs, or confidential project details into this public repository.
- Distinguish documented behavior, measured evidence, and engineering hypotheses.
- Prefer mechanisms and decision rules over vendor-specific prompt folklore.
- When documenting vendor/model behavior that may change, include the review date and authoritative source where practical.
- Do not turn a local workaround into a universal rule without scope and counterexamples.
- Treat current platform/tool defaults as the baseline. Any override should state the concrete inefficiency it addresses and why the change is expected to help.
- Use measurement or benchmarking when a tradeoff is non-obvious, consequential, or workload-dependent; do not turn benchmarking into ceremony.
- Keep always-loaded guidance concise. Optional procedures belong in skills or referenced docs.
- Apply the [executor-routing checkpoint](docs/local-codex/subagents.md#executor-routing-checkpoint) before substantial batches: exact tools first, sufficiently capable smaller workers for authorized independent work, orchestrator for synthesis/integration. Make the executor/model choice explicit in existing work context; merely reading efficiency guidance is not applying it. Preserve platform permissions and justify both extra fan-out and keeping a large routine batch on the orchestrator.

## Quality bar for a practice

Efficiency preserves substantive scope. For broad delegated transformations, require owned coverage and inspect representative deliverables against the original user outcome; worker counts, compact handoffs and structural tests are not substitutes for content acceptance. See [outcome-preserving delegation](docs/local-codex/subagents.md#outcome-preserving-delegation).

A useful entry should answer most of:

1. What resource inefficiency does this address?
2. What mechanism causes the inefficiency?
3. What change is proposed?
4. What can it save and what can it cost?
5. When should it not be used?
6. How can the same outcome/quality be verified?
7. Which metrics demonstrate the improvement?
8. What evidence supports it?
9. What result would invalidate or revise it?
