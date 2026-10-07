# Interface standards: applicability, not a checklist of badges

Reviewed **2026-10-07**. Use this map with the [interface contract](accessible-interfaces.md). Select standards by surface, users, task and risk; preserve stricter product/contract/legal requirements. Publication does not itself establish legal applicability. These are sources for local engineering policy, not certification.

## Human-facing baseline

| Reference | Scope and application |
| --- | --- |
| [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | All applicable Level A and AA web criteria, not merely scanner-detectable issues. |
| [W3C COGA](https://www.w3.org/TR/coga-usable/) | Cognitive usability: hierarchy, clear labels, manageable content, focus, feedback and recovery. Supplemental guidance beyond WCAG conformance. |
| [ISO 9241-125:2017](https://www.iso.org/standard/64839.html) and [ISO 9241-112:2025](https://www.iso.org/standard/87518.html) | Visual presentation and information presentation across modalities. Not a universal graphic grammar or complete chart-design specification. |
| [ISO 9241-110:2020](https://www.iso.org/standard/75258.html), [ISO 9241-210:2019](https://www.iso.org/standard/77520.html) and [ISO 9241-11:2018](https://www.iso.org/standard/63500.html) | Interaction principles, human-centred design and usability in context. Apply proportionately; screenshots alone do not establish usability. |

ISO scope/edition statements were checked against official public summaries, not complete licensed standards. Do not invent clause-level obligations or claim ISO conformance from these summaries. Obtain authorized access to the specified edition when formal conformance is required. Normative specifications, informative notes, platform guidance and this repository's policy have different authority.

## Conditional extensions

| Surface or need | Reference | Application and boundary |
| --- | --- | --- |
| Custom web widgets | [WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/) | Prefer native controls; implement keyboard/focus behavior as well as semantics. APG is guidance, not certification. |
| Native software/non-web documents | [WCAG2ICT](https://www.w3.org/TR/wcag2ict-22/) | Informative mapping plus native platform accessibility APIs; do not equate it with web certification. |
| Games | [Xbox Accessibility Guidelines](https://learn.microsoft.com/en-us/xbox/accessibility/guidelines) | Game-specific barriers in controls, text, audio and other interactions; useful beyond web scanners, not a universal game standard. |
| Authoring/generation tools | [ATAG 2.0](https://www.w3.org/TR/ATAG20/) | Both accessible authoring UI and support for accessible output. |
| PDF output | [ISO 14289-2:2024 / PDF/UA-2](https://www.iso.org/standard/82278.html) | Accessible PDF 2.0 structure; select the PDF/UA edition supported by the actual format/toolchain. Verify content and reading order too. |
| User-facing language | [ISO 24495-1:2023](https://www.iso.org/standard/78907.html) and COGA | Audience-appropriate plain language. Controlled technical English is a separate domain choice, not a substitute for interaction design. |
| Multiple languages/locales | [W3C internationalization guidance](https://www.w3.org/International/quicktips/) | Unicode, language metadata, directionality, local formats and text expansion; test intended RTL/LTR layouts. |
| HTTP APIs | [OpenAPI](https://spec.openapis.org/oas/latest.html) and [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) | Explicit operations/schemas and structured errors where applicable. Use the actual protocol for other tools. Interoperability is not human accessibility. |
| Application security | [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) | Risk-appropriate verification of authorization, authentication and other boundaries. Accessible alternatives must preserve security. Do not impose an unrelated full audit on every visual edit. |
| Regulated/procured ICT | Applicable jurisdictional/product rules, including EN 301 549 where required | Verify scope, edition and legal/contractual applicability. [AccessibleEU's September 2026 notice](https://accessible-eu-centre.ec.europa.eu/content-corner/news/european-accessibility-standard-en-301-549-has-been-updated-2026-09-07_en) distinguishes a new edition from legal citation. |

Safety-critical, medical, aviation and industrial-control systems need separately scoped domain standards and qualified review. This list does not replace them. Resolve moving specifications to the edition actually used; do not require every agent to download all sources or add a new compliance framework.

[WCAG 3's September 2026 publication remains a Working Draft](https://www.w3.org/standards/history/wcag-3.0/), not the conformance baseline. [WAI evaluation guidance](https://www.w3.org/WAI/test-evaluate/) explains why automated checks require human evaluation too. A standards reference is neither measured adherence nor proof of an accessible product.
