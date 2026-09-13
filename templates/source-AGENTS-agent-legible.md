# Source-code legibility

Apply these rules when writing, modifying, refactoring, or reviewing source in this subtree.

- **Bounded mental model:** leave each touched unit understandable from the unit plus a small explicit contract/dependency context. A fresh weaker coding model should be able to predict representative paths, state changes, results, side effects, and failures without repository archaeology.
- **Semantic locality over size:** prefer cohesive units and direct control/data flow. Split real decisions, not arbitrary line counts; do not replace one large unit with a maze of tiny wrappers.
- **Make hidden inputs visible:** dependencies, state, errors, timeouts/retries, resource bounds, and important invariants should be explicit or mechanically discoverable.
- **Abstract only when it shrinks future reasoning/change radius:** avoid speculative interfaces/factories/indirection that add possible implementations without isolating real volatility.
- **Tests are independent contracts:** test behavior/invariants with an oracle independent from the implementation; avoid tests that mirror internals and break on behavior-preserving refactors.
- **Comments carry non-recoverable information:** explain rationale, constraints, and invariants, not obvious syntax or a second prose implementation.
- **Prefer boring machine-checkable consistency:** standard formatter, types/static checks, dependency rules, and low-noise lints over style instructions the model must remember.
- **Every touch:** do not make touched code harder for the next weak/fresh reader to model. Make obvious low-risk local simplifications when they reduce hidden state, branching, or navigation; do not expand scope into unrelated cleanup.

For rationale, counterexamples, and measurement, load `docs/code/agent-legible-code.md` only when needed.
