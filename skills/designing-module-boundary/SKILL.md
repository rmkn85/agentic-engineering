---
name: designing-module-boundary
description: Use when creating a new module, package, component, service boundary, or other new source-code ownership boundary.
---

# Designing a module boundary

Goal: create a boundary whose representative behavior and dependencies a fresh weaker coding model can understand without opening unrelated repository areas.

1. **Name one owned responsibility and its authority.** Route every path through the single owning authority. Locate existing authorities before adding one; state what stays inside and outside. Repeated "and"s signal a split boundary.
2. **Keep shared libraries boring (change-locality test).** Shared contract packages hold only stable primitives, envelopes, errors, and auth scopes. Keep feature DTOs, views, and endpoints in the owning product behind prefix- or scope-routed gateways so routine features land in one repo without multi-repo release syncs.
3. **Justify any new public contract.** Treat a new interface as a hypothesis: name the caller or trust boundary requiring it and why existing contracts cannot serve it. Make inputs, outputs, errors, invariants, and lifecycle explicit; do not expose internals.
4. **Choose dependency direction deliberately.** Keep outbound dependencies statically discoverable. Adapters, jobs, and fallbacks delegate owned decisions and mutations; they translate representation without duplicating policy or overriding refusal. Avoid hidden registries or callbacks unless required.
5. **Place state and side effects.** Isolate mutable state; push I/O, time, randomness, and storage to explicit boundaries.
6. **Prefer direct code until volatility earns abstraction.** Avoid speculative interfaces or factories; add seams only around real changing decisions or external boundaries.
7. **Keep flows mentally enumerable.** Keep normal and error paths flat with few semantic hops; split real decisions, not arbitrary line counts.
8. **Prove the boundary independently.** Enforce delegation via type/dependency checks and prove bypasses fail. Test against independent expectations rather than shared code; name any unverified path.
9. **Check runtime uncertainty.** Only when adding external I/O, concurrency, retries, or resource limits that tests cannot explain, load `instrumenting-runtime-feedback`.
10. **Run the weak-reader check.** From the public contract and key implementation unit alone, a weaker model should predict results, state/effects, failures, and dependencies without repository archaeology.

If code belongs inside an existing boundary without changing responsibility, use `adding-code-unit`. Rationale: `docs/code/agent-legible-code.md`.
