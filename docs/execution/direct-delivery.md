# Direct delivery of an integrated outcome

Use this method for multi-component product work, especially when repeated local
fixes have not made the requested user journey work. It applies the existing
[specification contract](../specifications/README.md); it adds no tracker,
approval ceremony or mandatory research phase.

## One direction, one current record

Keep the current outcome, constraints, decisive acceptance scenarios, owned lanes
and next action in the existing task/handoff. Use its existing fields to describe
the user outcome, a representative scenario, the next connected deliverable,
the existing implementation/interfaces and the observable finish. Reuse an
adequate specification.
Record a material user correction there before the next dependent change, and
reconcile any stale goal, scheduled prompt or worker brief through its supported
controls. If those controls cannot edit it, explicitly mark the stale text
superseded in the continuation. A generated continuation never overrides the
latest user instruction. Do not silently reset consumed budgets.

Execute the accepted plan with ordinary implementation judgment. Reopen a settled
decision when new evidence establishes infeasibility, a requirement conflict,
material risk or an acceptance failure. Record that evidence and make the smallest
necessary revision within authority; an optional alternative alone is not a reason
to redesign. A checkpoint can confirm the current approach. Preserve necessary
diagnosis, independent checks and the complete acceptance contract. Follow the
[routing rules](../local-codex/subagents.md#choose-effort-for-the-unresolved-decision)
when a reopened decision needs different capability or effort.

Replace superseded next actions rather than appending a new competing plan.
Keep receipts and detailed chronology in native task history, logs and version
control. A current handoff needs current state and enough evidence to resume;
it should not become an archive the next agent must reread.

## Focus on the journey people commonly use

Choose work by its contribution to the controlling user outcome and explicit
priorities. A ready task is eligible work, not automatically the next priority.
Establish that a proposed mechanism is needed before delegating its construction
([kernel 7](../agent-corpus/README.md#execution-kernel)). Use **80/20** as a
qualitative guide: concentrate on common scenarios while covering less common
scenarios where requirements or consequences make them necessary. Within that
focus, use **70/30** to favor features and use cases over the enabling work that
makes them possible. These nested ratios express judgment, not time allocations,
quotas, task counts or acceptance exemptions. A consequential boundary can warrant
immediate work; complete required scope even when its proportions differ.

Keep coordination, plan upkeep and CI/merge/deployment boilerplate in the smallest
supporting corner. Run the required delivery operations as part of finishing the
journey. Choose enabling work because it removes a concrete obstruction to that
journey, then resume the connected deliverable. Extend an existing owner or
published contract when it supplies the capability. Complete the next missing
connection, run relevant checks, publish through the authorized route and
demonstrate the result in its consumer.

Write instructions as desired actions with precise invariants: state the behavior
to produce, the boundary to preserve and the observation that proves it. For
example, "route every entrypoint through the existing owner and preserve its
refusal semantics" gives an implementation direction and a checkable invariant.
Preserve binding safety, permission, stop and approval conditions with their full
meaning; affirmative wording is not permission to weaken them. Lead progress and
completion reports with the usable capability and remaining journey gap, followed
by the evidence and supporting delivery state.

## Keep context close to the current decision

Use three layers: a small enduring core for stable authority and invariants; a
current record for outcome, progress and next action; and task-specific evidence
retrieved when relevant. Keep detailed sources, diagnostics and history
retrievable through their existing owners. Load the implementation/interface or
evidence needed for the next decision and refresh it when relevant inputs change.
This keeps the current journey visible while retaining access to the complete
contract and required evidence.

## Work in this order

1. **Define the observable result.** State what the user must be able to do and
   understand through the actual entrypoint. Identify the required normal case,
   meaningful contrast and consequential failure/boundary, beginning with the
   common journey that makes the capability useful. Preserve the complete
   scope; a representative scenario is an early checkpoint, not a smaller finish
   line. Mark assumptions and proposed targets separately from requirements.
2. **Trace the existing path once.** Follow that action through its current
   owners, contracts and renderer. Use one real source-bound example and the
   existing tools. Identify the defect or unknown preventing the result. Avoid
   a broad inventory of unrelated systems or a replacement implementation.
3. **Choose the preserving mechanism.** Identify the semantic owner before adding
   an interface. Check whether an internal repair or existing contract supplies
   the needed behavior; a stale result alone does not establish a need for a new
   public refresh API. Add a public surface only for a required caller, authority
   or trust boundary, preserving ownership and refusal semantics. Settle the few
   cross-boundary decisions
   that control correctness before coding: semantics, dates/units, state memory,
   missingness, ownership and the consumer contract where relevant. Resolve an
   uncertainty with the smallest observation that can change the decision.
4. **Make one complete path work.** Implement and inspect the connected result
   early through the real entrypoint. Use focused regressions for changed logic
   and installed/rendered proof for claims that depend on composition. Check
   human comprehension separately from pixel layout and data correctness. Repair
   the path before multiplying variants or optional features; independent lanes
   may proceed once their shared contract and integration case are clear.
5. **Extend and finish.** Exercise required contrasts, failure/recovery cases
   and supported scope, preserving accepted behavior. Run the normal integration
   checks once the coherent candidate is ready. Efficient unit and integration
   tests are part of delivery; use QA/product review for approval where required.
   Do not invent exhaustive qualification gates at delivery or release.
   Publish a recoverable checkpoint
   and continue remaining authorized work; report completion only for proven scope.

Progress means a required scenario works, a concrete obstruction was removed, or
evidence changed the next decision. Test totals, commits and reports support that
claim; they are not substitute outcomes. At checkpoints, apply
[delivery steering](../../skills/steering-delivery/SKILL.md): assess the current
trajectory and previous intervention, then execute the justified next action.
If successive increments leave the same primary gap unchanged, reconsider the
mechanism and work ordering before another similar patch. Keep the working parts;
do not restart discovery wholesale. Record the evidence-backed rationale and
subsequent effect in the task or commit message, not in source/configuration.

## Scope delivery claims independently

Use the existing task or receipt to distinguish these claims where applicable;
they are neither a new task-status enum nor a universal linear pipeline.

| Claim | Evidence it needs |
| --- | --- |
| Implemented | The required mechanism exists in the identified candidate |
| Verified | An independent check supports the specified behavior and scope |
| Integrated | The actual consumer composes and invokes that candidate correctly |
| Available | The intended user can reach the capability in the stated environment now |
| Accepted | The authorized acceptance conditions and required judgment are satisfied |

Select applicability with the work's contract, before a failed check invites an
exemption. A documentation edit need not acquire a deployment prerequisite.
Use unknown when proof is missing and not applicable with a scope reason.
Acceptance can remain valid for a version while its availability later regresses;
state the affected version/environment rather than collapsing every claim.

For consequential claims, retain source/candidate identity and actual loaded,
installed or served artifact identity, scenario/entrypoint, relevant environment,
substantive result/errors, coverage and invalidation condition in existing
receipts. Source equality does not prove the runtime loaded it. Keep a comparison
control's actual identity too; an old test against a different artifact is not a
valid control for the candidate. Process exit describes execution, not substantive
completion: use native producers' completion/error verdicts and propagate failures
through actual callers and CI. A successful generic command remains useful
process evidence without product qualification. Do not infer a universal verdict
from a printed success token or arbitrary log regex.

For human-facing work, inspect representative ordinary composed output through
the actual primary interaction. A diagnostic fixture, hidden action, isolated
component render or numerical proxy cannot establish ordinary readability,
visual quality or comprehension. Use the intended user's context and applicable
product judgment independently of data correctness and machine accessibility.
Retain unrun human/visual checks instead of claiming acceptance from test totals.

Detection and containment are not remediation completion. When repair is required,
verify the corrected result or obtain an authorized irreparable disposition with
usable investigation and explicit limitations. Do not silently close the outcome
at a provenance report.

## Performance work must change the user's wait

Measure the complete relevant operation before selecting a component optimization:
for example cold load, warm load, in-buffer interaction and a boundary request.
Keep those categories separate. Attribute the dominant cost using existing timing
or profiling; preserve waiting, transfer/serialization and rendering costs where
they are on the path. Instrumentation overhead is not an unqualified baseline.

Estimate the maximum plausible end-to-end benefit before building a benchmark or
candidate. A large percentage of a tiny component can leave the reported delay
unchanged. Choose work whose expected benefit addresses the complaint within the
existing resource limits. Do not invent a user latency target or silently turn a
candidate-selection heuristic into acceptance. When no numeric requirement exists,
state the baseline, proposed improvement and actual result honestly.

For a chosen change, preserve semantic parity, source/time identity and relevant
state/caching/invalidation behavior. Measure the same operation after integration.
Reject a failed candidate, retain its finding and move to a materially different
cause; do not repeat it under a new name. A faster fixture or one warm request
does not prove cold-load speed, tail latency or universal performance.

## Keep the process smaller than the work

Use native commands and observed paths. Classify setup failures once; retry only
after a specific correction. Apply resource and sample gates to their actual
operation and authority: build-tool memory, analytical runtime and experimental
data limits are not interchangeable. Do not add staged sample counts, approval
steps, independent reviews or full-suite reruns to every reversible edit unless
the existing contract or the changed risk requires them.

During edits, use the maintained ownership selector and focused source checks.
For the coherent candidate, run the owning product's build, relevant unit checks
and focused integration checks through its normal delivery path; documentation-only
updates use their applicable checks. Resolve unknown ownership or ambiguous impact
to select the meaningful checks, widening them when shared validation changes or
the affected behavior requires it. Verify package and dependency integrity at build
and consumption, and obtain QA/product approval where required. Preserve required
release acceptance; a development check or smoke result proves only its tested
boundary. Measure setup separately from execution and compare the same operation
before claiming improvement.

Keep short exact operations and tightly coupled judgment local. Delegate when
context isolation, domain continuity or independent progress repays coordination,
under the existing [dispatch contract](../local-codex/subagents.md#launch-preflight).
Sustained domain owners and co-developers retain relevant context through feedback
and validation; they do not duplicate the coordinator's investigation. Each owner
advances implementation, checks and routine recovery locally against declared
interfaces and artifacts. Coordinate decisions that cross ownership boundaries,
serialize shared-contract changes and final integration, and keep one current
acceptance contract across lanes. When composing from source rather than consuming
a published artifact, declare that mode, the exact source identities and the
consumer boundary; verify the resulting composition at that boundary.

This method is a response to a failure pattern, not a guarantee of first-attempt
correctness or measured savings. Small isolated fixes need only their existing
focused check. Exploratory work may legitimately end in a negative result when
that experiment is the authorized outcome. Judge this process on subsequent
integrated delivery, repeated user corrections and total rework—not document length.
