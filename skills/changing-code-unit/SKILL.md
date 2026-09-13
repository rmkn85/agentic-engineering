---
name: changing-code-unit
description: Use when modifying or refactoring an existing function, method, class, handler, or similarly local code unit while keeping the surrounding module boundary substantially intact.
---

# Changing an existing code unit

Goal: make the requested change while leaving the unit no harder for a fresh weaker coding model to understand than before.

1. **State whether behavior changes.** Separate a behavior-preserving refactor from an intentional contract/behavior change. Do not let cleanup silently redefine the outcome.
2. **Capture the current contract before editing.** Identify callers, inputs, outputs, errors, state/effects, and the cheapest tests/invariants that protect the behavior. Add a characterization test first when important current behavior is uncertain.
3. **Find the real reasoning burden.** Look for interacting branches, hidden state/dependencies, duplicated decisions, long semantic-hop chains, mixed effects/logic, or ambiguous names. Do not refactor merely to hit a line-count metric.
4. **Simplify one conceptual decision at a time.** Prefer direct flow, explicit intermediate state, guard clauses where useful, and helpers that name actual concepts. Do not move complexity behind factories/wrappers and declare victory.
5. **Keep the external surface stable unless the task requires change.** If callers, ownership, or dependency direction need coordinated restructuring, escalate to `refactoring-module`.
6. **Keep tests independent of internals.** Preserve/extend behavioral or invariant evidence. A behavior-preserving refactor should not require broad test rewrites merely because private structure moved.
7. **Validate locally first.** Run the focused checks that cover the changed unit, then broaden only where the affected dependency boundary/risk requires it.
8. **Run the weak-reader check.** Given the changed unit and immediate declared contracts/dependencies, can a fresh weaker model predict representative paths, results, state/effects, failures, and bounds with no more context/reasoning than before?

If a local refactor reveals that the real problem is the module's public surface, ownership, cycles, or dependency graph, stop widening the local patch and use `refactoring-module`.

For rationale and counterexamples, read `docs/code/agent-legible-code.md` only when needed.
