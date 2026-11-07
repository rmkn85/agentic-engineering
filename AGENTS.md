# AGENTS.md

This public repository teaches coding agents to reach the **requested outcome** with less model usage, wall time, repeated work, retries and human effort. Your own work here follows the same method.

Read this file and [`docs/agent-corpus/README.md`](docs/agent-corpus/README.md); load deeper docs only for the decision at hand. Do not crawl `references/`: it holds research and rationale for methodology audits.

## Work backward from the goal

1. **State the goal and its evidence first.** For any multi-step task, write the user outcome and the checks that prove it in `.agent/goal.json` (format: `python3 tools/finish_check.py --help`). Preserve requirement authority and meaning under the [specification contract](docs/specifications/README.md); never invent requirements or weaken acceptance. Optimise execution, not scope: keep success criteria, source coverage, permissions and the quality bar. Human-facing work includes the [interface contract](docs/interfaces/accessible-interfaces.md).
2. **Choose the shortest path that closes the remaining gap.** Readiness, convenience or interesting side work is not priority. At checkpoints use [delivery steering](skills/steering-delivery/SKILL.md). Check execution feasibility before dependent preparation; keep external effects last and bind them to [reviewed native activities](docs/adoption/native-command-bindings.md#sandbox-first-external-activities).
3. **Execute with tools before inference.** Use deterministic tools for mechanical work, keep logs on disk, reuse valid results until an input changes, and select workers under the [routing policy](docs/local-codex/subagents.md#named-model-and-effort-policy) and [dispatch contract](docs/local-codex/subagents.md#launch-preflight). Fan out only for a concrete benefit. Platform defaults are the baseline; benchmark only consequential deviations. Record decision rationale in tasks or commit messages, not in source.
4. **Verify against the goal, not the steps.** Exit codes, green links, worker reports and passing unrelated tests do not prove the outcome. Validate narrowly while iterating and broadly at integration, preserving protected behaviour; use [bounded recovery](docs/execution/bounded-recovery.md) for faults. Report unrun checks and limitations instead of claiming conformance.
5. **Finish only through the gate.** Run `make finish-check` (Claude runs it as a Stop hook). If it fails, keep working. If a real external blocker remains, mark the item `blocked` with the blocker and fill the gap record it writes. Never present executable required work as "next steps" ([completion boundary](docs/agent-corpus/README.md#completion-boundary)).

## Changing guidance in this repository

A rule nothing enforces is a suggestion. A change to runtime guidance must do one of these:

- add or change a mechanism (tool, test, schema, hook or config) that fails on the observed failure before the change and passes after it;
- attach a behavioural trial result ([adherence protocol](experiments/instruction-context-adherence.md)); or
- delete at least as much runtime text as it adds.

`make guidance-delta` enforces this in CI, and `make check` holds the default reading under its word budget in `configs/guidance-budget.json`. Lower the budget when text shrinks; do not raise it to fit new prose. Prefer automated checks over sentences; repeated non-adherence calls for scoping or enforcement, not more prose. Forbid only new manual ceremony (forms, approvals, extra agents) without a measured failure.

Write runtime text as short imperatives under the [technical-language rules](docs/specifications/technical-language.md); keep evidence labels (documented, measured, hypothesis), rationale and research in `references/`. Adopt changes in active work through [standards migration](docs/adoption/standards-migration.md).

## Contribution rules

- Keep guidance domain-neutral. Project-specific formats and lessons stay with their project.
- Never copy private repository content, credentials, internal URLs or personal environment identifiers (usernames, hosts, addresses, workstation paths, hardware or OS inventory, personal config). Use neutral placeholders; keep only the capability or version a claim needs.
- Give vendor behaviour that may change a review date and an authoritative source.
- Do not generalise a local workaround without scope, a counterexample and evidence.

## Validation and adoption

`make check` runs the contributor regression suite with Python 3.9+ and Git, no external packages; CI runs it too. It proves tool behaviour, not model adherence or product delivery. To adopt these practices elsewhere, use the [newcomer contract](docs/adoption/newcomer-contract.md) and [native command bindings](docs/adoption/native-command-bindings.md); prefer executable routes over more always-loaded prose.
