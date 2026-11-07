# AGENTS.md

This public repository teaches coding agents to reach the **requested outcome** with less model usage, wall time, repeated work, retries and human effort. Your own work here follows the same method.

Read this file and [`docs/agent-corpus/README.md`](docs/agent-corpus/README.md); load deeper docs only for the decision at hand. Do not crawl `references/`: it holds research and rationale for methodology audits.

## Work backward from the goal

1. **State the goal and its evidence first.** For any multi-step task, write the user outcome and the checks that prove it in `.agent/goal.json` (format: `python3 tools/finish_check.py --help`). Under the [specification contract](docs/specifications/README.md), preserve requirement authority and meaning, connect construction to independent evidence, and never invent requirements or weaken acceptance. Optimise execution, not scope: keep success criteria, source coverage, permissions and the quality bar. Human-facing work follows the [interface contract](docs/interfaces/accessible-interfaces.md): accessible operation, rendered comprehension and machine semantics are separate obligations; a new barrier is a defect, not polish.
2. **Choose the shortest path that closes the remaining gap.** Readiness, convenience or interesting side work is not priority. At checkpoints use [delivery steering](skills/steering-delivery/SKILL.md). Check feasibility before dependent preparation. Keep preparation sandboxed and external effects last; bind them to [reviewed native activities](docs/adoption/native-command-bindings.md#sandbox-first-external-activities), allowlist each bounded activity once, and never seek equivalent access through an ad-hoc command or another surface.
3. **Execute with tools before inference.** Use deterministic tools for mechanical work. Keep logs on disk: workers return status, decisions and evidence paths, and the coordinator reads only decision-critical excerpts. Reuse valid results until an input changes. Select role, lifetime, model, effort and context explicitly under the [routing policy](docs/local-codex/subagents.md#named-model-and-effort-policy) and [dispatch contract](docs/local-codex/subagents.md#launch-preflight); reuse never preserves an unsuitable selection or an expired exception. Epic owners continue through accepted delivery (estimates prompt steering, never invented stop budgets); short workers return a bounded result. Fan out only for a concrete benefit; no forced model ratios. Platform defaults are the baseline for unconstrained choices and never override explicit selection or owner ceilings; benchmark only consequential deviations. Record decision rationale in tasks or commit messages, not in source.
4. **Verify against the goal, not the steps.** Exit codes, green links, worker reports and passing unrelated tests do not prove the outcome. Validate narrowly while iterating and broadly at integration. Build for supported conditions with [controlled stress checks and bounded recovery](docs/execution/bounded-recovery.md), preserving protected behaviour and minimum useful service. Report unrun checks and limitations instead of claiming conformance.
5. **Finish only through the gate.** Run `make finish-check` (Claude runs it as a Stop hook). If it fails, keep working. If a real external blocker remains, mark the item `blocked` with the blocker and fill the gap record it writes. Never present executable required work as "next steps" ([completion boundary](docs/agent-corpus/README.md#completion-boundary)).

## Changing guidance in this repository

A rule nothing checks is a suggestion. A change that adds runtime guidance must also:

- add or change a test that fails on the observed failure without the change and passes with it; or
- attach a behavioural trial result ([adherence protocol](experiments/instruction-context-adherence.md)); or
- delete at least as much runtime text as it adds.

`make guidance-delta` enforces this in CI, and `make check` holds the default reading under `configs/guidance-budget.json`. Budgets only go down. Prefer automated checks over sentences; repeated non-adherence calls for scoping or enforcement, never more prose and never a worker above its ceiling. Forbid only new manual ceremony (forms, approvals, extra agents) without a measured failure.

A practice states the failure it addresses, its mechanism, what it saves and costs, when not to use it, how the same outcome is verified, and the evidence that would revise it. Label claims as documented behaviour, measured result or engineering hypothesis. Prefer mechanisms and decision rules over vendor prompt folklore.

Write runtime text as short imperatives under the [technical-language rules](docs/specifications/technical-language.md): declare requirement strength, and preserve authority, conditions, exceptions and checks in every rewrite; capitalisation does not erase an obligation. Move rationale and research out of runtime text into `references/`; do not delete it. Adopt changes in active work through [standards migration](docs/adoption/standards-migration.md), preserving local rules and unfinished work.

## Contribution rules

- Keep guidance domain-neutral unless it is explicitly a case study. Project-specific formats and lessons stay with their project.
- Never copy private repository content, proprietary code, credentials, internal URLs, confidential project details or personal environment identifiers (usernames, account URLs, hosts, addresses, workstation paths, hardware or OS inventory, personal config). Use neutral placeholders; keep only the capability or version a claim needs.
- Give vendor behaviour that may change a review date and an authoritative source.
- Do not generalise a local workaround without scope, a counterexample and evidence.

## Validation and adoption

`make check` runs the contributor regression suite with Python 3.9+ and Git, no external packages; CI runs it too. It proves tool behaviour, not model adherence, product delivery, semantic correctness or public-corpus privacy; those need review or a trial. To adopt these practices elsewhere, use the [newcomer contract](docs/adoption/newcomer-contract.md) and [native command bindings](docs/adoption/native-command-bindings.md): apply protections by process need, preserve local authority, and prefer executable routes over more always-loaded prose.
