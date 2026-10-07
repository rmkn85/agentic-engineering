# Engineering standards and methods: applicability map

Reviewed **2026-10-07** against the primary sources linked below. Use this map with the [specification contract](README.md), [technical-language rules](technical-language.md) and [migration procedure](../adoption/standards-migration.md). This is a source map and local adoption profile, not an assertion that every project conforms to every named standard.

## Core profile

| Reference | Use in this repository | Boundary |
| --- | --- | --- |
| [ASD-STE100 Issue 9](https://www.asd-ste100.org/about_STE.html), [official FAQ](https://www.asd-ste100.org/STE_faq.html) | Consistent technical terminology and clear operational writing | STE-informed local rules; full compliance needs the actual rules/dictionary and appropriate review. Technical nouns and verbs remain permitted. |
| [BCP 14 / RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) | Distinguish mandatory, recommended and optional obligations | Declare the convention; uppercase terms do not erase plain-language requirements or override source authority. |
| [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) | Requirements engineering and requirements-related information across the lifecycle | Apply requirements review, traceability and change-impact discipline proportionately. The public scope does not authorize clause-level conformance claims. |
| [EARS](https://alistairmavin.com/ears/) | Explicit trigger, state and required response in behavioral requirements | Engineering method, not an ISO standard. Local MUST patterns are an adaptation of canonical shall forms. |
| [ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) | Consider relevant product-quality requirements, not only requested functionality | Quality model, not a universal set of performance thresholds or a score proving quality. |
| [Design by Contract](https://www.eiffel.org/doc/eiffel/ET-_Design_by_Contract_%28tm%29%2C_Assertions_and_Exceptions) | Preconditions, postconditions and invariants at useful implementation boundaries | Method, not a mandate to use Eiffel or assertions everywhere. Untrusted inputs still need runtime validation. |
| [ISO/IEC/IEEE 29119-2:2021](https://www.iso.org/standard/79428.html) | Risk-appropriate test planning, execution and evidence | Process standard; use existing tests/CI and do not confuse test records with correctness. |

The [NASA requirements checklist](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/) is an accessible review aid for requirement quality. [Gherkin](https://cucumber.io/docs/gherkin/reference/) can express executable scenarios when backed by actual step implementations and assertions. Neither requires a new toolchain for ordinary prose or native tests.

## Conditional extensions

| Trigger | Reference | Decision it should change |
| --- | --- | --- |
| Lifecycle ownership, operation, maintenance or retirement | [ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html) | Include relevant delivery, support, migration and retirement obligations; do not prescribe a replacement development methodology. |
| Consequential architecture shared across components or teams | [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) | Describe concerns, decisions and relevant views with the existing architecture record. It specifies architecture description, not which architecture to choose. |
| Secure development and supply-chain concerns | [NIST SP 800-218 / SSDF 1.1](https://csrc.nist.gov/pubs/sp/800/218/final) | Integrate applicable security practices into the existing lifecycle and dependency/release controls. |
| Security-sensitive implementation | [SEI CERT coding standards](https://insights.sei.cmu.edu/library/sei-cert-coding-standards-wiki/) and the project's language/toolchain guidance | Select applicable rules and low-noise static checks; do not impose C-specific restrictions on unrelated languages. |
| Application security verification | [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) | Choose risk-appropriate requirements for actual trust boundaries; preserve authorization, privacy and secure alternatives. |
| Difficult concurrency, coordination or recovery | [TLA+/PlusCal](https://lamport.azurewebsites.net/tla/high-level-view.html) or another suitable formal method | Model relevant states, safety properties and progress assumptions before implementing an uncertain design. Record model scope and the separate implementation correspondence checks. |
| Human-facing interfaces and generated output | [Interface standards map](../interfaces/standards.md) and [interface contract](../interfaces/accessible-interfaces.md) | Preserve WCAG/COGA and relevant ISO 9241-informed obligations, plus platform/document/game requirements where applicable. |
| Public machine contracts | The project's protocol/schema standard, including [OpenAPI](https://spec.openapis.org/oas/latest.html) or [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) where applicable | Make operations, errors, compatibility and permissions explicit; do not invent a separate API merely to claim coverage. |
| Safety-critical or regulated software | The domain's required assurance and coding profile | Obtain the applicable edition, evidence and qualified review. Aerospace-inspired restrictions such as Power of Ten are not a blanket profile for every application. |

The existing [agent-legible code guidance](../code/agent-legible-code.md) already adopts bounded reasoning surfaces, explicit state and independent checks. Keep those mechanisms; do not add new abstractions or rewrite an architecture solely to attach a standard's name.

## Edition, authority and evidence rules

ISO references here were checked against official public scope/edition pages, not the full licensed texts. The STE summary is based on official public material, not a full dictionary audit. Formal conformance requires the actual specified edition, applicable clauses, scope and appropriate evidence. Do not copy restricted source material into the repository.

At this review, ISO lists 29148:2018 as published while a replacement is in development; 12207:2026 is published. NIST lists [SSDF 1.2 / SP 800-218r1](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd) as an initial public draft. This profile uses SSDF 1.1 as its published reference, not the draft as a mandatory replacement. Verify status again when making an edition-dependent decision.

A newer publication does not automatically change a contract, legal obligation or pinned project profile. Record edition and source status when adopting; use [migration triggers](../adoption/standards-migration.md#when-to-adopt-or-migrate) for updates. A standard, informative guide, research method and local policy have different authority. Name deviations honestly; do not turn selected guidance into a false certification claim.

The baseline is relevant engineering behavior, not reading this entire table on every task. Every added reference must affect an actual decision, construction mechanism or verification check. Keep detailed background out of the normal operating context.
