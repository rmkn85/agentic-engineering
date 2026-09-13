---
name: adding-code-unit
description: Use when adding a new function, method, class, handler, or similarly local code unit inside an existing module without redefining the module boundary.
---

# Adding a code unit inside an existing module

Goal: extend the module while preserving its existing mental model instead of creating a second architecture inside it.

1. **Confirm the unit belongs here.** Identify the existing module responsibility and the new behavior's place in it. If the addition changes ownership or introduces a new independent lifecycle/contract, use `designing-module-boundary`.
2. **Reuse the module's vocabulary and interaction pattern.** Prefer existing stable types, naming, dependency direction, and error conventions unless those are the actual problem being changed.
3. **Keep the contract narrow.** Make parameters, result, errors, state effects, and important bounds explicit. Do not enlarge the public surface unless callers genuinely need it.
4. **Avoid hidden new dependencies.** Pass or locally declare what affects behavior; do not introduce ambient globals, registries, implicit configuration, or novel runtime wiring for convenience.
5. **Make the unit locally predictable.** Keep representative paths and state transformations easy to enumerate. Extract helpers only when they name a real concept or reduce the mental model; do not manufacture a wrapper chain.
6. **Keep effects visible.** When practical, separate deterministic decision/transformation logic from external I/O or other nondeterministic effects.
7. **Add independent behavioral evidence.** Test the new behavior/invariants at the narrowest stable boundary. Expected results should not duplicate the production algorithm.
8. **Check integration without rereading everything.** Run the cheapest tests/static checks that cover the addition, then broader module/integration acceptance only when the dependency/risk boundary requires it.
9. **Run the weak-reader check.** A fresh weaker model given the new unit and immediate contracts should be able to predict representative outputs, state/effects, failures, and dependencies.

If the task primarily changes an existing unit, use `changing-code-unit`. If the module itself needs ownership/public-surface/dependency restructuring, use `refactoring-module`.

For rationale and counterexamples, read `docs/code/agent-legible-code.md` only when needed.
