# Machine contracts across independent delivery

Use this practice when a machine-facing boundary is shared by independently delivered components. The purpose is a stable observable outcome that a consumer can implement and verify without waiting for the provider. The [specification contract](../specifications/README.md) and local product authority still govern the outcome; this practice adds no board, gate or parallel ledger.

## Define the boundary before implementation

Identify the consumer, provider, observable outcome and public contract. Reuse the semantic owner's definitions and canonical schema authority; link to them rather than maintaining competing meanings or schema copies. The owner specifies inputs and outputs, types and units, identity, ordering, state transitions, authorization, errors, retry and idempotency behavior where relevant. State supported conditions and consequential failure behavior. Keep unresolved semantics explicitly draft and resolve them through their owner before promising them as stable.

Classify the actual public surface before choosing its representation: an HTTP API, tool protocol, library, command, stream, user-interface package or retained artifact has its own lifecycle and consumer expectations. A process or deployment may expose several surfaces, and one contract may have multiple bindings. Treat bindings as interchangeable only after their observable behavior is verified. Give each independently consumed surface a compatibility identity; keep that distinct from package, provider build, protocol, deployment and data-instance identities. Grouping operations for navigation does not itself create another versioned contract.

Write representative examples and behavior acceptance from the authoritative outcome before implementation. Include normal behavior, boundary and failure cases, and expected results independent of the implementation. Contract tests, fixtures and mocks let consumers and providers develop independently against the same published revision. A successful mock or consumer test demonstrates only its tested contract assumptions; it does not establish provider integration, QA acceptance or the user's end-to-end outcome. Run the relevant provider and integrated checks separately and record their actual results.

## Publish and evolve

Publish identifiable, immutable contract revisions with their schemas, examples and compatibility expectations. Reuse the existing release and ownership routes. A published revision describes a promise; distinguish its **maturity** (such as draft or stable), each implementation's **support** for it, and actual **availability** to a consumer. A schema's existence alone proves neither implementation nor availability.

Compare the normative meaning and referenced schema closure of the affected surface, including defaults, units, authorization and behavior. Preserve an independent digest for contract content and for the complete published artifact, so a packaging or editorial change does not imply a changed promise. When the owner requires explicit contract approval, prepare the exact candidate, change description and compatibility evidence first; bind the decision to that candidate. Unchanged contracts and independently delivered products continue through their established routes.

For each change, state which previous revisions and consumer/provider combinations remain compatible and why, including historical data or replay where applicable. Preserve exact historical semantics and revision identity; do not reinterpret old records using today's meaning. Test additive changes against representative strict readers as well as tolerant readers: an added field, enum value or response can break a consumer that rejects unknown values. When compatibility cannot be preserved, publish a distinct revision and migration path rather than silently replacing the old contract.

Retire a revision based on observed consumer adoption and the owner's support commitments. Identify affected consumers, migration and evidence of readiness before retirement; a calendar date or a new version alone does not prove adoption. Keep the old revision and its interpretation available for supported historical use.

## Select a protocol profile

For HTTP APIs, a useful reference profile is [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) with [JSON Schema 2020-12](https://json-schema.org/draft/2020-12), [HTTP semantics (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html), [problem details (RFC 9457)](https://www.rfc-editor.org/rfc/rfc9457.html), [timestamps (RFC 3339)](https://www.rfc-editor.org/rfc/rfc3339.html), [Trace Context](https://www.w3.org/TR/trace-context/) and [AIP-180 compatibility guidance](https://google.aip.dev/180). Select the parts applicable to the boundary and pin the adopted editions. These references inform local decisions; they do not establish certification or impose a universal toolchain.

For packages, events, files, commands or other protocols, use the surface's native typed, package or protocol contract and its established compatibility rules. Do not introduce HTTP or an API solely to apply this profile. Consider relevant quality characteristics using [ISO/IEC 25010](https://www.iso.org/standard/78176.html) as a quality reference, not a source of invented thresholds.

The expected benefit is fewer incompatible assumptions and less serial waiting. Maintaining examples, compatibility evidence and supported revisions costs effort; use the smallest shared contract justified by the boundary. Local private implementation details need not become public contracts. Revisit the practice if actual delivery evidence shows that it adds maintenance without preventing ambiguity or incompatible change.
