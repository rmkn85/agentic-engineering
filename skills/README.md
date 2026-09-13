# Skills

Skills are on-demand workflows. Their discovery metadata should answer **when to load them**; their bodies contain the focused procedure. Do not load every skill for every task.

## Execution

- [`efficient-execution`](efficient-execution/SKILL.md) — long/repository-heavy/tool-heavy work where repeated model work, noisy context, fan-out, or broad validation may materially affect cost.

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
