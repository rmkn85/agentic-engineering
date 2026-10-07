# Specification, implementation and evidence

Use this contract for new or changed engineering instructions, requirements, code and acceptance criteria. It extends the [operating corpus](../agent-corpus/README.md), not the product scope. For existing systems or active tasks, also use [standards migration](../adoption/standards-migration.md).

These are local engineering rules informed by the [standards map](standards.md), not certification requirements. Uppercase MUST, MUST NOT, SHOULD and MAY use the meanings of [BCP 14](technical-language.md#requirement-strength). Existing plain-language obligations remain binding; capitalization is not an escape from them.

## Start with the smallest adequate contract

1. **Establish authority and purpose.** Read the current task, applicable repository instructions and relevant source specifications. Identify the user outcome, constraints, affected consumers and existing acceptance. Challenge unnecessary requirements or premature solution choices before optimizing them. Do not substitute a different outcome without authority.
2. **Separate facts from choices.** Distinguish authoritative requirements, observed behavior, assumptions, experiments and design decisions. Existing code is evidence of behavior, not automatic authority for desired behavior. A new document or model-generated summary is not automatically authoritative either.
3. **Select applicable quality obligations.** Reuse the project's approved standards profile. Identify failure, security/privacy, accessibility, compatibility, resource and recovery concerns that the change actually affects. A feature request need not repeat these inherited obligations. Load additional standards only for a relevant decision.
4. **State decisive behavior before coding it.** Use the [technical-language rules](technical-language.md). Identify actor, trigger/state, response, protected state and observable outcome. Define relevant units, limits, ordering, failure and cancellation semantics. Preserve an existing adequate specification instead of retranscribing it.
5. **Choose construction and verification together.** For each material obligation, identify what in the implementation preserves it and what independent evidence can contradict it. Then implement the smallest coherent change through the existing native commands.

A small change can satisfy this in its existing issue, test or commit rationale. Do not create a specification file, requirements database, new framework or approval ceremony for every function. A broader cross-component change needs a durable shared contract, not a larger private mental model.

## Resolve uncertainty without inventing requirements

Retrieve missing information from existing sources first. Use an established default for a reversible implementation choice that does not change the accepted outcome. State a material assumption and its scope; do not silently promote it to a user requirement.

An agent MUST NOT invent a latency target, retry count, retention period, permission or destructive-action policy to make an incomplete specification look precise. Resolve a consequential conflict through the existing owner/decision route before the dependent risky action. Continue independent authorized work. Do not ask for approval merely to select an ordinary in-scope implementation.

For empirical or exploratory tasks, define the hypothesis, safe experiment boundary, measurement and decision rule instead of pretending the desired result is known. Separate experiments from production acceptance and preserve negative results.

## Make the implementation preserve the contract

Use the [agent-legible code rules](../code/agent-legible-code.md). In particular:

- Put contracts in the smallest useful boundary: types/schemas, validated inputs, explicit state transitions, resource ownership and pre/postconditions. Reuse established language and platform mechanisms. Do not add a contract library just to cite Design by Contract.
- Validate untrusted inputs and authorization at trust boundaries. Internal caller obligations do not justify trusting network input. Assertions that can be disabled MUST NOT be the only protection for authorization, destructive effects or untrusted data.
- Distinguish success, rejection, pending and unknown outcome. A timeout does not by itself prove that a remote effect did not occur. For retries or concurrent writers, specify relevant identity, duplicate-effect policy, ownership and conflict behavior; do not promise exactly-once effects without a preserving mechanism and stated assumptions.
- Make consequential effects explicit. Identify what can change, what must remain unchanged and what recovery is possible. Use transactional or staged publication where the contract needs it. A dry run or backup claim requires evidence appropriate to the action, not a reassuring label.
- Make exceptional paths legible: propagated errors, cancellation, cleanup, capacity limits and exhaustion behavior. Bound external work where feasible; long-lived services still need resource policies and shutdown/recovery contracts, not an arbitrary requirement that every loop terminates.

The design record should explain non-obvious mechanisms and tradeoffs, not duplicate code. Keep API/schema and compatibility obligations with their actual owners. For human-facing output, the [accessible interface contract](../interfaces/accessible-interfaces.md) remains independently required.

## Verify the requirement, not the implementation's story

Verification asks whether the candidate meets the contract. Validation asks whether that contract and resulting behavior meet the user's need in context. Neither substitutes for the other.

Derive expected results from authoritative requirements or an independent oracle. Cover the decisive normal case, relevant boundaries and at least one consequential failure or counterexample. Add property, contract, integration, fault-injection, security or model checks when their scope warrants them. Prefer existing test tools. Given-When-Then can organize a scenario without mandating Gherkin or Cucumber.

A scenario is not executed evidence until its real setup, action and assertions run. A test that copies the production algorithm can agree with the same defect. Inspect implementation structure for important behavior missing from the requirements/tests too. Coverage counts, lint, file presence and copied standards names do not prove the requested outcome.

Keep a lightweight trace in existing records: **requirement/source -> preserving mechanism -> check/oracle -> candidate and result**. Use stable IDs or anchors for obligations that cross files, teams or revisions; do not number every sentence. Requirements, mechanisms and checks can have many-to-many relationships. Reassess dependent evidence when a relevant requirement, implementation, fixture, environment or oracle changes.

Use the existing [E2E evidence distinctions](../runtime/e2e-readiness.md). Record passed, failed, blocked or not run for each required check; not applicable needs a scope reason. Preserve source/build identity and evidence paths. Changes to tests or thresholds MUST NOT merely redefine a defective candidate as successful. A legitimate acceptance change needs its actual rationale and authority, separate from the fix.

## Scale rigor by risk

| Change | Adequate starting point | Escalate when |
| --- | --- | --- |
| Local, reversible behavior | Existing requirement, focused test, native static checks and review of the changed boundary | Ambiguity or coupling prevents a bounded explanation |
| Persistent state, public contract, permissions or external effects | Explicit failure/compatibility contract, representative consumer tests and recovery evidence | Partial failures, mixed versions or concurrency threaten the invariant |
| Consequential concurrent/distributed behavior | State/transition model, safety properties, progress assumptions and fault scenarios | Examples cannot adequately expose ordering or recovery errors; consider TLA+/PlusCal or another suitable method |
| Regulated or safety-critical system | Applicable domain profile, required authority and qualified assurance process | Required assurance cannot be obtained through the ordinary project route |

This table is a local routing rule, not an ISO assurance level. Model checking supports only the modeled properties under its stated assumptions and explored scope; it is not proof the implementation matches the model. Do not impose aerospace restrictions on unrelated software or replace qualified domain review with a generic checklist.

## Completion

An agent MUST NOT claim a required property was verified without evidence for that property. Surface unresolved material assumptions, failed checks, accepted deviations and unrun acceptance honestly. A scoped implementation can be complete while a separately required external review remains blocked; name that boundary rather than claiming full product acceptance.

A known new violation of an inherited contract is not optional cleanup. Repair it before claiming completion. Handle unrelated existing debt through [bounded migration](../adoption/standards-migration.md), without silently expanding or abandoning the assigned outcome.

The expected benefit is fewer ambiguous changes, misleading tests and repeated clarification loops. The cost is relevant specification and validation work. [Behavioral probes](../../experiments/specification-integrity.md) test that hypothesis; navigation tests alone establish routing, not agent reliability or standard conformance.
