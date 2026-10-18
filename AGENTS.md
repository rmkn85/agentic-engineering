# AGENTS.md

This repository is a public knowledge base about executing the **same authorized engineering work** with less model usage, wall time, repeated computation, retries, and human effort while preserving the requested result and quality.

## Normal reading boundary

For ordinary work, use this file plus [`docs/agent-corpus/README.md`](docs/agent-corpus/README.md) as the default operating corpus. Load deeper operational docs only when the current decision needs them.

**Do not recursively crawl `references/`.** It preserves external research, provenance, competing ideas, and historical rationale for maintainers improving this methodology. Read it only for methodology research/audit work.

## Execution invariants

- Preserve the task, success criteria, source coverage, permissions, and quality bar; optimize execution, not scope. A milestone is not completion: apply the corpus's [completion boundary](docs/agent-corpus/README.md#completion-boundary) before any final response. For substantial iterative work, use [delivery steering](skills/steering-delivery/SKILL.md) at checkpoints: revise and execute the justified in-scope next action, and retain decision rationale and observed effect in tasks or commit messages, never source/configuration.
- Apply the [specification contract](docs/specifications/README.md): preserve requirement authority and meaning, connect construction to independent evidence, and never invent requirements or weaken acceptance. Use [incremental migration](docs/adoption/standards-migration.md) for existing or active work; preserve local rules and unfinished work.
- Apply the [interface contract](docs/interfaces/accessible-interfaces.md) by default: accessible operation, rendered human comprehension and machine semantics are independent obligations. New barriers are not polish; expose limitations and unrun checks rather than claiming conformance.
- Use deterministic tools for mechanical work. Keep logs on disk; workers return status, decisions, and evidence paths. The coordinator reads only decision-critical excerpts: consumed logs keep taxing later context.
- Complete sandboxed preparation first. Bind necessary external effects to [reviewed parameterized native activities](docs/adoption/native-command-bindings.md#sandbox-first-external-activities), approve/allowlist each bounded activity once, and reject ad-hoc inline command escalation rather than seeking equivalent access through another surface.
- Apply the [named routing policy](docs/local-codex/subagents.md#named-model-and-effort-policy) to each phase and review: tools/Luna for routine operations, maintenance and monitoring; Sol 6.1/Medium for sustained engineering; Astra/Medium or High for extremely creative or complex decisions. Ultra requires a current explicit owner instruction to exhaust allowance before reset; exhaustion, reset or the owner deadline ends that exception. Explicitly select model/effort, appropriate context and finite budgets under the [dispatch contract](docs/local-codex/subagents.md#launch-preflight); reusing an agent does not preserve an expired exception. Do not force model ratios or create fan-out without a concrete benefit.
- Treat context as a working set. Keep always-loaded guidance small; prefer path-scoped rules, on-demand skills, isolated worker context, and retrievable references when they are sufficient.
- Reuse valid semantic and deterministic work until an input that can affect it changes; reusing a worker still requires its configuration and remaining budget to comply.
- Build for supported conditions; use [controlled stress checks and bounded recovery](docs/execution/bounded-recovery.md). Preserve protected behavior and minimum useful service, not just uptime. Validate narrowly while iterating and broadly at integration; structural checks, worker votes and green links do not prove the requested outcome.
- Treat platform defaults as the baseline for unconstrained choices, never as an override of explicit worker selection or owner ceilings. Benchmark consequential or workload-dependent deviations; do not turn benchmarking into ceremony.

## Instruction discipline

A persistent instruction is recurring context. Before adding one, ask what observed failure it addresses, whether it matters to nearly every task, and whether code/config/test/path scoping/on-demand loading can solve it more cheaply.

For important behavior changes, establish the baseline when practical, add the smallest intervention, then test the behavior inside the normal instruction stack. Repeated non-adherence should trigger better scoping, deterministic enforcement, or a more capable authorized coordinator before unlimited prompt growth; it does not itself authorize a worker above its ceiling. See [`experiments/instruction-context-adherence.md`](experiments/instruction-context-adherence.md).

Use the [technical-language rules](docs/specifications/technical-language.md), including STE-informed writing and declared requirement strength. Preserve authority, conditions, exceptions and checks during rewrites; capitalization does not erase plain-language obligations.

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

## Native validation and adoption

From this repository root, `make check` runs the contributor-tool regression suite with Python 3.9+ and Git, without external packages or an installed project ecosystem. CI uses that same command. Tool tests do not replace semantic review, public-corpus privacy review, or a real host/model/delivery trial.

When adopting these practices in another repository, use the [newcomer contract](docs/adoption/newcomer-contract.md) and [native command bindings](docs/adoption/native-command-bindings.md). Apply protections by process needs, preserve local authority, and prefer executable native routes over additional always-loaded prose.
