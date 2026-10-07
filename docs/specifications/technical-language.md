# Precise technical language

Apply this guidance to engineering instructions, specifications, acceptance criteria, operational procedures, handoffs and decision-bearing comments. The objective is preserved meaning with less interpretation, not a particular tone in every conversation. Use it with the [specification contract](README.md).

## STE-informed by default

[ASD-STE100 Issue 9](https://www.asd-ste100.org/about_STE.html) combines controlled writing rules and vocabulary. Its [official FAQ](https://www.asd-ste100.org/STE_faq.html) also permits domain-specific technical nouns and verbs. This repository adopts STE-informed discipline, not a claim of full ASD-STE100 conformance.

Use consistent names for domain concepts, short direct sentences and explicit actors. Prefer a concrete condition and action over an ambiguous pronoun or passive instruction. Keep distinct obligations separately reviewable, while retaining conditions needed to interpret them. Define unfamiliar terms where they first matter or reuse the local glossary; do not invent synonyms for stylistic variety.

Preserve negation, quantifiers, units, thresholds, timing, scope, exceptions and requirement strength during rewriting. Keep API identifiers, commands, paths, error codes, externally defined terms and quoted source text exact. Do not rename a public interface or weaken a warning to satisfy a language preference. A shorter sentence is worse when it loses a constraint.

Put rationale, examples and proposed designs beside requirements without presenting them as additional obligations. Avoid words such as fast, robust, appropriate or user-friendly as the sole acceptance condition. Supply a relevant observable criterion from authority or evidence; do not invent a number merely to remove an adjective.

Full STE delivery requires the actual required edition, dictionary and review against its rules. Do not claim compliance from this summary, an agent's self-description or a generic readability checker. Do not copy the full standard/dictionary into a public repository without the necessary rights.

## Requirement strength

In this guidance and documents that adopt this convention, uppercase MUST, MUST NOT, SHOULD and MAY have their [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) meanings. MUST is mandatory; MUST NOT prohibits; SHOULD permits a justified exception after considering its implications; MAY grants an option. SHALL is the mandatory equivalent when a governing specification uses it. Prefer MUST in new local rules rather than mixing equivalent keywords arbitrarily.

Declare the convention in new normative specifications. Preserve a host project's existing convention or map it explicitly during an authorized migration. Do not mass-uppercase old text: ordinary imperatives and existing requirements still apply without these keywords. MAY for permission is not can for capability. SHOULD is not a convenient substitute for a mandatory acceptance condition. Uppercase wording creates no permission to exceed the actual authority of its source.

## EARS-adapted behavioral requirements

[EARS](https://alistairmavin.com/ears/) supplies patterns for event, state, unwanted and optional behavior. Its canonical examples use shall. The following local forms use MUST consistently; they are an adaptation, not a verbatim reproduction or a separate standard.

```text
The <system> MUST <response>.
WHEN <trigger>, the <system> MUST <response>.
WHILE <state>, the <system> MUST <response>.
IF <unwanted condition>, THEN the <system> MUST <response>.
WHERE <feature is included>, the <system> MUST <response>.
```

Combine clauses only when the triggering order and scope stay clear. An optional feature's WHERE condition does not make required behavior optional once the feature is present. Express a cross-event invariant as a property or state model when forcing it into a sentence would obscure it. Define timing, ordering or boundary conditions separately when needed. The template cannot determine what the product should do.

## Worked example and semantic review

Illustrative scope: an authorized user submits a configuration candidate. Validation rules already exist in the product contract.

```text
CFG-1: WHEN candidate validation fails, the configuration service MUST
       reject the candidate.
CFG-2: WHEN a candidate is rejected, the configuration service MUST
       preserve the active configuration.
CFG-3: WHEN a candidate is rejected, the configuration service MUST
       report the validation errors to the authorized caller.
```

The preserving mechanism might validate separate candidate state before publication. Independent checks submit invalid candidates and observe rejection, unchanged active state and the specified errors. Authorization, concurrent submissions, persistence failures and sensitive error details remain separate concerns; the fragment does not resolve them by implication.

Before accepting a rewrite, compare old and new actor, obligation strength, trigger/state, response, exceptions and protected values. Record a semantic change separately from language cleanup. For example, changing SHOULD retry to MUST retry strengthens behavior; changing before publication to after publication changes ordering. Neither is a formatting correction.

Use [NASA's public requirements checklist](https://www.nasa.gov/reference/appendix-c-how-to-write-a-good-requirement/) for additional review questions about necessity, consistency, assumptions and verifiability. Its terminology convention is not automatically this repository's BCP 14 convention.

For tests and migrations, retain the requirement source and dependent checks. Keep the canonical requirement in one place with links rather than manually synchronized prose copies. A project can adopt this discipline incrementally through [standards migration](../adoption/standards-migration.md).
