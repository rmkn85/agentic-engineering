# Bounded recovery before model replanning

Make important properties survive supported faults through construction and native checks, not a longer prompt or a permanent agent committee. This is local engineering policy, not a claim of universal fault tolerance. Use the [specification contract](../specifications/README.md) and the existing task record; do not create a second requirements system.

## Supported conditions and useful service

Before changing a consequential boundary, identify **protected properties, minimum useful service, supported conditions/budgets, allowed degradation and the recovery boundary**. Reuse existing requirements. Resolve consequential missing limits rather than inventing them. Staying online is insufficient; rejecting every task also fails when useful service is required. Beyond supported conditions, preserve safety and expose the limitation instead of silently claiming success.

First remove fragile dependencies. Rebuild disposable caches; keep unique state and checkpoints at the required durability boundary. Reduce round trips and repeated work; use bounded queues, explicit ownership and established transactions. Drop optional work under pressure before protected behavior. Label stale, pending and unknown results. Slow hardware may reduce throughput, not silently weaken correctness, access or security. Desktop throttling is not proof of embedded-target timing or behavior.

## Recovery loop

```text
execute -> check outcome -> continue
failure -> classify -> known authorized recovery within budget -> verify
unknown, unsafe or exhausted -> diagnose / revise the authorized approach
```

Recovery is bounded, observable and verification-gated. **Escalation is not task termination.** Continue independent work and use the [completion boundary](../agent-corpus/README.md#completion-boundary). Do not reset an exhausted budget through respawning or a new operation name.

## Starter taxonomy

| Failure signal | First response | Escalate when |
| --- | --- | --- |
| Timeout / transient network failure | Reconcile uncertain effects; retry only when safe, with bounded backoff | Duplicate-effect safety is unknown or budget is exhausted |
| Rate limit | Obey retry-after / wait policy | Deadline or quota makes completion infeasible |
| Missing command | Inspect declared toolchain/environment | Dependency cannot be located safely |
| Parser / syntax error | Return exact location to the responsible editor | Ownership or intended source is ambiguous |
| Approved formatter/lint fix | Run the known fixer once | It changes semantics/scope or remains failing |
| Stale generated output | Run the declared generator | It is ambiguous, destructive or fails |
| Test assertion failure | Inspect the assertion and minimum decisive evidence | Semantic diagnosis is required |
| Tool/schema argument error | Repair only an unambiguous mismatch | Valid interpretations differ |
| Write/merge collision | Refresh authoritative state and serialize ownership | Semantic reconciliation is required |
| Ambiguous regression | Preserve evidence; do not guess a repair | Immediately |

## Recovery budget

Declare finite attempt, elapsed-time and resource limits, backoff, retry/duplicate-effect policy, post-recovery checks and conditions forbidding recovery. Propagate cancellation and remaining budgets across layers; do not multiply retries across callers. A timeout is not proof that a remote effect did not occur. Reconcile state before repeating an uncertain consequential operation.

## Local repair before global replan

Repair an argument, regenerate one stale artifact or run an approved fixer before replanning the product. Replan when evidence invalidates a material assumption, not merely because a command returned nonzero. Put consequential limits in types, validated boundaries, permissions and runtime guards where feasible; do not rely solely on model memory. Guards and fallback paths need their own tests and failure policy.

## Verification is separate from recovery

HTTP success still needs payload/state checks; a completed generator needs artifact checks; a fixer needs relevant syntax/type/behavior checks. Recovery does not prove acceptance. Keep product failure, unavailable capability, unknown outcome and missing evidence distinct. Use the [E2E evidence rules](../runtime/e2e-readiness.md); do not hide a primary failure when diagnostic storage also fails.

## Controlled disturbances

Exercise the real task with an independent expected result, then disturb one relevant assumption. Verify that the injection reached its intended boundary and check both protected properties and useful service, including recovery. Start with attributable single faults; add plausible combinations and timing sequences when interactions matter. Retain baseline, candidate, inputs, parameters, actual fault schedule and outcome. Seeds help controlled simulations but do not make external services or models deterministic.

| Affected boundary | Relevant disturbance | Required observation |
| --- | --- | --- |
| Process / network | Termination, outage, delay, duplicate or reordered messages | Valid state, bounded recovery and the declared duplicate-effect behavior |
| Storage | Lost scratch state, full disk, failed write, interrupted publication | Rebuildable scratch, protected committed state, honest evidence availability |
| Resources | Restricted CPU, memory, bandwidth, concurrency or execution budget | Minimum useful service within the profile; explicit overload and cancellation behavior |
| Visual meaning | Smaller image, blur, noise, skew, rotation or color reduction | Declared distinctions survive; use the [visual/novice checks](../interfaces/accessible-interfaces.md#comprehension-under-degradation) |
| Agent context | Compression, fresh session, missing background or stale/conflicting material | Recover authority and unfinished state, not invented knowledge; use [context trials](../../experiments/specification-integrity.md#fault-and-context-controls) |
| Decisions | Plausible wrong proposal, reviewer disagreement or incorrect majority | Independent evidence decides; confidence and vote count do not override a violated contract |

Use three controls: a meaning-preserving transformation should preserve the relevant answer; a meaningful change should change it; loss of essential information should produce retrieval or scoped uncertainty. Do not demand successful guessing after information destruction. Inject a known defect in a disposable fixture to check that the oracle rejects it. A detector that never rejects or an injector that never activates provides no assurance.

## Independent decisions

Default to one builder plus appropriate independent checks. Invoke a bounded independent reviewer for consequential ambiguity, conflicting evidence or required assurance, not for every routine edit. Give the reviewer the relevant authoritative sources and artifact, without anchoring it on the builder's explanation. For novice visual checks, provide only the intended user's background. Keep evaluator and human-usability evidence separate.

Resolve disagreement with a discriminating check or the authorized decision owner. A valid counterexample blocks the affected claim even against a majority. Do not assume repeated calls, different model names or role labels create independent errors. Reviewers cannot change acceptance, approve their own exceptions or exceed the [worker policy](../local-codex/subagents.md#launch-preflight). Budget review depth; escalate only the unresolved decision and return routine work to the cheaper adequate path.

## Safety and ownership

Run fault injection in explicitly scoped, disposable environments by default. Bind targets, credentials, process ownership, duration, affected scope, stop conditions and teardown before execution. Teardown touches only resources the experiment owns. Never fill a shared disk, kill unrelated processes or corrupt a contributor checkout to demonstrate resilience. Test the injector/cleanup limits too.

Production experiments require separate applicable authorization, monitoring, containment and recovery readiness. A request for resilience is not permission to attack live dependencies. Neither recovery nor testing authorizes deleting unrelated work, force-pushing, disabling checks, widening permissions, installing undeclared dependencies or choosing a different migration. A rollback claim must account for irreversible external effects; unavailable restore prerequisites block the dependent action.

## Telemetry

Keep the record small: source/task, protected property, supported profile, original operation, fault/class, recovery action, attempts/resources, verification result, evidence location and unresolved boundary. If evidence storage fails, retain the original known result through an available channel and mark delivery failure; do not rerun side effects merely to recreate a log. No channel can report after all reporting paths are lost.

## Adoption and automation

At first adoption or an affected change, bind the relevant checks to the project's existing native test commands and CI. Keep cheap regressions on ordinary changes; run broader fault sequences and sampled context/visual trials at the existing integration or approved scheduled boundary. Identify command, trigger, finite budget and evidence destination in the existing entry/task record. A prose promise or absent test tool is not an installed check. Reuse fixtures and test adapters, not a mandatory chaos platform, universal command or parallel orchestrator.

Use [incremental migration](../adoption/standards-migration.md): preserve work, select one representative journey and its consequential weak assumption, test it safely, repair the smallest boundary and retain the regression. Missing host, human or target-hardware trials stay explicit. New projects start this way; untouched legacy is not a blanket rewrite target. Refresh active instruction contexts and continue the original assignment.

## Promotion rule

Promote recovery rules only when classification and safe outcomes have evidence. Compare normal and stressed tasks under comparable permissions and budgets: useful completion, violations, false success, recovery time, resource cost and human correction. Select the smallest adequate configuration; remove duplicated prose when a verified mechanism replaces it. Reject changes that hide failures or simply shift cost into mandatory committees. Do not claim general reliability or token savings from navigation tests or a few successful trials.

## Source scope

Reviewed 2026-10-08. [Chaos Engineering](https://principlesofchaos.org/) supports outcome-based experiments and containment; its production preference does not grant local authorization. [FoundationDB](https://apple.github.io/foundationdb/testing.html) documents deterministic simulation alongside separate performance and hardware tests. [SQLite](https://www.sqlite.org/testing.html) documents fault, compound-failure and mutation testing. [Google SRE](https://sre.google/sre-book/handling-overload/) discusses overload and graceful degradation.

[NASA runtime-assurance work](https://ntrs.nasa.gov/citations/20240007986) separates an advanced controller, monitor and trusted fallback under explicit assumptions. Borrowing that separation does not give agents spacecraft guarantees or make a model committee equivalent to hardware redundancy. The visual/context adaptations and review policy here are engineering proposals requiring the scoped trials above.
