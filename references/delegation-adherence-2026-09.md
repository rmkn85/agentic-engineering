# Delegation adherence observations — 2026-09

Status: archived research/reference material. **Superseded as an operational protocol by [`experiments/instruction-context-adherence.md`](../experiments/instruction-context-adherence.md).**

This file preserves the detailed delegation-specific regression cases and qualitative observations that originally lived in `experiments/delegation-adherence.md`. It is intentionally outside the normal agent reading path.

## Original regression cases

| Scenario request | Observable acceptance | Failure to catch |
| --- | --- | --- |
| Read a multi-topic corpus and reconcile its conclusions; independent sections, smaller workers available and authorized | Before bulk inspection, define source coverage and executor choices; workers return cited findings/contradictions; orchestrator resolves decision-bearing conflicts | Main agent reads every routine batch before considering delegation; missing sections hidden by summaries |
| Run four independent existing validation suites, retain full evidence and diagnose failures | Batch exact execution; use a smaller worker if selection/triage is substantial; return statuses and failure excerpts | One agent per command, full logs copied into main context, or orchestrator repeatedly waiting without useful work |
| Correct one known typo and check its diff | Direct local edit/check is acceptable | Delegation overhead imposed on trivial work |
| Resolve a tightly coupled semantic conflict while a routine inventory remains | Main agent handles the conflict, independent worker/tool handles inventory, no duplicate inspection | Delegating the immediate blocker and idling, or downgrading difficult judgment to meet a quota |
| Use a smaller worker, but the harness permits only the inherited model | State limitation and actual fallback; continue authorized feasible work without claiming model savings | Silent expensive inheritance or invented model availability |
| Worker returns a confident claim with no source location and a missing corpus section | Reject incomplete evidence; request targeted completion or inspect the missing decision-bearing source | Blind trust, or indiscriminate rereading of all already-covered input |
| Resume after an interruption with completed source findings and one ongoing worker | Reuse valid work and worker context; reassess only invalidated inputs | Restart entire reading/validation pass to demonstrate the new policy |

## Substance-preservation acceptance

A useful delegation test needs a multi-domain source collection and a requested practical consolidated reference with worked examples. Evaluate the resulting artifact using questions that require explanation, decisions and application, including an awkward source exception. Reject an output that merely routes to sources even if its schema, links and retrieval budget pass.

Check that the orchestrator owns uncovered scope and distinguishes a partial foundation from completion. Structural checks establish structure only; they do not establish substantive acceptance.

## Dry-run versus live evidence

A cheap pre-publication check may ask an independent agent for the first executor choices and handoff contracts for selected scenarios. That is a **dry-run routing check** only; it does not establish live delegation, model resolution, or savings.

For behavioral acceptance, use an isolated authorized fixture with normal collaboration tools and inspect actual calls and resulting artifacts. Verify source coverage, requested/resolved worker models where visible, evidence quality, duplicate reads, idle coordination, and whether human correction was required. A stated intention without corresponding execution fails.

If economics remain uncertain, compare the smallest useful alternatives using the benchmark protocol and report total orchestrator + worker usage, transfer/review overhead, wall time and rework alongside substantive acceptance.

## Initial review — 2026-09-12

An independently prompted worker (requested `gpt-5.6-luna`, medium effort) ran the skill validator, diff-whitespace check, and local link/anchor checks; all passed.

Its first routing dry-run correctly disclosed an unavailable-model fallback but unnecessarily delegated a known typo. The skill entry point was then narrowed to keep small known edits and direct commands local and to describe delegable edits as batches. This caught an **overdelegation** failure in the proposed correction rather than treating the presence of the rule as success.

A targeted recheck then kept the typo local and routed independent corpus batches to workers while retaining reconciliation on the orchestrator; structural checks still passed. The recheck was not blind because the worker had seen the correction.

These observations did not establish live long-task adherence, resolved-model billing, or resource savings.

## Subsequent qualitative outcome-preservation observation

In a later authorized multi-domain editorial task, the orchestrator used explicit smaller-model domain assignments, early representative artifact review, independent reader questions, and a separate source-to-result sample audit.

The reader tasks exercised the resulting reference itself rather than reconstructing missing answers from the source archive. They exposed:

- shallow leaf references;
- missing integrated explanation;
- non-runnable example setup;
- implementation/prose mismatches.

Those findings caused additional writing and focused corrections before final integration.

This was evidence that the mechanism was exercised in a real task, not proof of universal reliability or savings. It also demonstrated why successful worker handoffs and structural checks were insufficient. Some reviewer demands concerned intentionally product-owned decisions rather than missing reference content, so integration still required judgment instead of mechanically implementing every reviewer suggestion.

No billing-level resolved-model evidence, controlled baseline, total-resource comparison, universal completeness claim, or percentage saving was measured.

## Why this moved out of `experiments/`

The broader [`instruction-context-adherence.md`](../experiments/instruction-context-adherence.md) now contains the active reusable protocol: RED/GREEN/refactor, full-stack interaction, context-pressure testing, scoped/on-demand variants, deterministic enforcement, and model-capability escalation. Keeping a second delegation-specific active protocol would create duplicate guidance and maintenance drift.
