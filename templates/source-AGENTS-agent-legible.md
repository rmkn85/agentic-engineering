# Source-code legibility

When writing, modifying, refactoring, or reviewing source in this subtree, preserve one invariant:

> A fresh weaker coding model should be able to predict representative behavior from the touched unit plus a small explicit contract/dependency context.

Choose **one** focused skill from the task's structural scope:

- new module/package/component/boundary -> `designing-module-boundary`
- new function/class/method inside an existing module -> `adding-code-unit`
- modify/refactor an existing local function/class/method -> `changing-code-unit`
- restructure an existing module/package across units or its public/dependency boundary -> `refactoring-module`

Use the **smallest structural scope that actually contains the task**. If a local task discovers a boundary-level problem, escalate once to the broader skill; do not stack every narrower skill underneath it.

Do not make touched code harder for the next weak/fresh reader to model. Avoid expanding scope into unrelated cleanup.

Load `docs/code/agent-legible-code.md` only when a decision needs rationale, counterexamples, or measurement guidance.
