# Skills

Skills are on-demand workflows. Their discovery metadata should answer **when to load them**; their bodies contain the focused procedure. Do not load every skill for every task.

For adoption across hosts and repositories, use [portable skill routing](../docs/adoption/overlays.md#portable-skill-routing): preserve linked resources and verify availability, startup delivery and task behavior separately.

## Execution

- [`efficient-execution`](efficient-execution/SKILL.md) — long/repository-heavy/tool-heavy work where repeated model work, noisy context, fan-out, or broad validation may materially affect cost.
- [`recovering-interrupted-work`](recovering-interrupted-work/SKILL.md) — interrupted tasks, stale source, changed hosts or ambiguous writes; preserve existing task authority and work.
- [`improving-execution-guidance`](improving-execution-guidance/SKILL.md) — recurring execution friction; improve the smallest mechanism, generalize safely and verify behavior without changing the requested outcome.

For native setup/check/delivery bindings and cold/stale acceptance, see the [repository-only contributor contract](../docs/adoption/newcomer-contract.md).

## Agent-legible source work

Route by the **structural shape of the change**, not by programming-language syntax:

| Task shape | Skill |
| --- | --- |
| Create a new module/package/component/ownership boundary | [`designing-module-boundary`](designing-module-boundary/SKILL.md) |
| Add a new local function/class/method inside an existing boundary | [`adding-code-unit`](adding-code-unit/SKILL.md) |
| Modify/refactor an existing local function/class/method | [`changing-code-unit`](changing-code-unit/SKILL.md) |
| Restructure an existing module/package across units or its public/dependency boundary | [`refactoring-module`](refactoring-module/SKILL.md) |

Choose the smallest scope that contains the task. If work reveals that the real problem lives at a broader boundary, escalate once; do not stack all narrower skills.

This split is intentionally small. Add another specialized skill only when its trigger is cheap/unambiguous and its workflow differs enough that loading a general skill would repeatedly waste context or reduce adherence.

The shared invariant is defined in [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md): touched code should remain cheap for a fresh weaker coding model to mentally model from a bounded local context.

## Runtime feedback and diagnosis

These are orthogonal to the code-shape skills and should load only when the task actually concerns telemetry or failure diagnosis:

- [`instrumenting-runtime-feedback`](instrumenting-runtime-feedback/SKILL.md) — add/change logging, telemetry, health checks, crash reporting, self-monitoring, recovery reporting, or build/test diagnostic output so future agents get progressive structured evidence instead of raw-output floods.
- [`diagnosing-runtime-failure`](diagnosing-runtime-failure/SKILL.md) — diagnose crashes, exceptions, failing jobs/tests/builds, degraded services, dumps, traces or noisy logs by starting from the smallest trustworthy index and following evidence links only as needed.

A code-writing task that merely adds ordinary business logic should not load these skills. A crash/diagnosis task should not load all four source-structure skills unless it actually modifies source afterward.
