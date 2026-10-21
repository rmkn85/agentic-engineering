---
name: designing-module-boundary
description: Use when creating a new module, package, component, service boundary, or other new source-code ownership boundary.
---

# Designing a module boundary

Goal: create a boundary whose representative behavior and dependencies a fresh weaker coding model can understand without opening unrelated repository areas.

1. **Name one owned responsibility and its authority.** Every functionality path must pass through the single authority that owns that behavior. Locate an existing authority before creating a new one. State what the module owns and what remains outside it. If the responsibility needs repeated “and”, reconsider the boundary.
2. **Design the smallest useful public contract first.** Make inputs, outputs, errors, invariants, and lifecycle explicit. Do not expose internals merely because they exist.
3. **Choose dependency direction deliberately.** List required outbound dependencies and keep them conventional/statically discoverable. Entry points, adapters, jobs, compatibility paths and fallbacks must delegate owned decisions and mutations through the authority's public contract. They may translate representation but must not duplicate policy, manufacture an accepted result or override refusal. Restrict access to private decision and mutation interfaces. Avoid hidden registries, service locators, callbacks, or runtime wiring unless the problem requires them.
4. **Place state and side effects.** Make ownership of mutable state clear. Keep I/O, time, randomness, network/storage, and other effects near explicit boundaries when practical.
5. **Prefer direct implementation until volatility earns abstraction.** Do not create interfaces/factories/adapters for hypothetical future implementations. Add a seam when it isolates a real changing decision or external boundary.
6. **Make representative flows mentally enumerable.** A weak reader should be able to follow normal and important error paths with few semantic hops. Split real decisions, not arbitrary line counts.
7. **Create independent contract evidence.** Enumerate the supported entry paths and enforce their delegation with native type, dependency or architecture checks. Exercise a deliberate bypass to prove the check rejects it. Test the authority's behavior, input coverage and calculations against independent expectations; shared implementation is not an independent oracle. State unverified paths explicitly rather than inferring universal enforcement from one adapter.
8. **Check runtime uncertainty.** If the boundary introduces external I/O, long-running/concurrent state, retries/fallbacks, process/service boundaries, resource limits, or another failure mode that will be hard to reconstruct after the fact, decide whether runtime feedback is sufficient. Load `instrumenting-runtime-feedback` only when this is material; do not instrument pure/local logic by default.
9. **Run the weak-reader check.** Given the public contract plus the key implementation unit, can a fresh weaker model predict representative results, state/effects, failures, and influencing dependencies without repository archaeology?

If the new code clearly belongs inside an existing boundary without changing that boundary's responsibility, use `adding-code-unit` instead.

For rationale and counterexamples, read `docs/code/agent-legible-code.md` only when needed.
