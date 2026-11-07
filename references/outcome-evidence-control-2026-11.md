# Outcome and evidence control: research rationale

Reviewed 2026-11-07. This is methodology research, outside the normal execution
corpus. Read it when evaluating delivery controls, repeated false completion,
context recovery or process overhead. The operational owners are
[direct delivery](../docs/execution/direct-delivery.md),
[bounded recovery](../docs/execution/bounded-recovery.md),
[observation economy](../docs/execution/observation-economy.md) and
[resource lifecycle](../docs/execution/resource-lifecycle.md).
The [source map](outcome-control-source-map.md) records primary sources,
source-specific limitations and unresolved provenance.

## Status and scope of the argument

A supplied research report motivated this synthesis. Its incidents are
unreproduced case observations, not a public dataset or causal experiment.
Private case identities, quotations, operational details and environment paths
are deliberately excluded. The report is research input, not authority to
change a project's requirements, permissions or acceptance.

The central engineering hypothesis is that some recurring failures arise when
an interpretation silently substitutes for an observed change: ready work
becomes priority, a proposed design becomes an approved interface, successful
process exit becomes successful behavior, or historical knowledge becomes
current authority. Separating those propositions may prevent specific errors.
It does not establish that a new management layer improves delivery overall.

Three kinds of support remain separate:

- **Documented practice:** a source describes a mechanism or recommendation.
- **Empirical finding:** a study reports observations within a specified setup;
  association, benchmark performance and randomized treatment effects differ.
- **Engineering hypothesis:** this repository's proposed transfer to sustained
  agent work, requiring local behavioral and outcome evaluation.

## What transfers from human software management

[SPACE](outcome-control-source-map.md#space) supports measuring productivity
across dimensions instead of using output counts or a single efficiency proxy.
[DORA](outcome-control-source-map.md#dora) directs attention to the surrounding
organizational system. Neither validates the particular controls below.
The resulting design hypothesis is to preserve accepted outcomes, quality,
flow, human intervention and computation as separate observations.

[Information hiding](outcome-control-source-map.md#parnas) offers a rationale
for assigning design decisions to component owners. A coordinator can state a
consumer problem and required behavior without prescribing a new public
interface for an owner's internal decision. An owner still needs freedom to
challenge an obsolete boundary through the project's actual decision process.

[Batch and WIP evidence](outcome-control-source-map.md#flow) supports testing
short feedback paths and limiting unresolved work, with important qualifications:
minimizing WIP is not demonstrated to maximize productivity, and splitting code
without integrating or obtaining feedback can merely relocate a queue.
For agents, candidate queues include untested assumptions, integration branches
and unverified claims; agent count alone is a weak substitute.

[SRE practice](outcome-control-source-map.md#sre) distinguishes recurring
operational toil from enduring improvement and uses explicit reliability policy
to balance competing goals. Our transfer is to automate unchanged observation
and known recovery where worthwhile, and to recognize genuine authority limits
separately from repairable implementation limits. This does not import another
organization's staffing percentages or error-budget policy.

## Five proposed mechanisms and their boundaries

These mechanisms should extend existing native task and delivery records.
They are not a requirement for five new services, files or review stages.

| Mechanism | Rationale and proposed benefit | Cost, limit and falsification |
| --- | --- | --- |
| Authorized outcome and decision rights | Preserve the controlling goal, acceptance, permissions, fixed interfaces and revisable assumptions across delegation. This may prevent a worker's preferred solution becoming authority. | Duplicating requirement stores creates drift. Link the authoritative record; revise if owners cannot recover it reliably or ordinary implementation waits for unnecessary approval. |
| Selection from the current outcome gap | Ask which observation or action can remove the present obstacle to the requested capability. This may reduce ready but irrelevant maintenance. | Discovery can be necessary before the obstacle is known. Keep justified experiments; reject selection rules that starve preventive work with a demonstrated acceptance or reliability dependency. |
| Separate applicable delivery claims | Record implementation, verification, integration, availability and acceptance as independent claims with their own evidence. This may prevent a local success from implying global completion. | A mandatory linear pipeline invents stages for source-only or research tasks and misrepresents partial success. Claims may be true, false, unknown or explicitly inapplicable with a reason; failure in one does not erase valid evidence for another. |
| Evidence tied to the claim | Bind decisive observations to source/build identity, runtime or consumer, native verdict, retrieval coverage and relevant conditions. This may prevent weak signals, partial retrieval and stale observations from carrying stronger meaning. | Metadata cannot prove subjective quality. Use independent observation and negative controls where warranted. Invalidate on changed inputs or conditions; elapsed time alone is not a universal reason to rerun immutable evidence. A time limit is appropriate only when time can change validity. |
| Resumable state and separate resource lifecycle | Preserve the current contract, uncertainty, evidence and next safe action outside ephemeral context; preserve unique work before retiring owned disposable resources. This may reduce restart loss and accumulation. | Extend the native task/checkpoint rather than create a parallel ledger. Shared caches and active consumers justify retention. Cleanup must respect ownership and verified preservation, even if a lease expires or a task closes. |

Agent-specific motivation comes from context reconstruction, tool semantics and
execution boundaries, rather than an assumption that human management transfers
unchanged. A process launch, test discovery, suite completion, native verdict,
consumer observation and experiential acceptance are distinct facts. Multiple
reviewers sharing the same untested premise do not provide independent evidence.
The [context study](outcome-control-source-map.md#context) cautions against
assuming more instruction text helps; the
[monitoring study](outcome-control-source-map.md#monitoring) supplies a concrete
selective-monitor design to test, not a reason to supervise every action.

## Causal failure classes and discriminating checks

The supplied report distinguishes nine classes. Keep them separate because a
single label such as goal drift would hide different interventions. The examples
below are neutral hypothetical failure modes, not published case evidence.

| Class | Causal hypothesis and candidate control | Observation that would revise it |
| --- | --- | --- |
| Task selection | Available internal work crowds out a blocked consumer journey; select from the current acceptance gap. | Given the same authoritative state, owners already select the necessary obstacle but fail during execution. Investigate execution instead. |
| Problem framing and architecture | A delegated design suggestion acquires unwarranted authority; preserve problem, boundary and decision owner separately. | Independent problem-first analysis and the interface owner support the same change. The architecture may need to change. |
| Evidence semantics | Exit success or a passing local check is mistaken for the claimed behavior; require the relevant native verdict and actual entry point. | False completion persists despite independently checked evidence semantics. Investigate acceptance interpretation or evidence fabrication rather than add another status field. |
| Acceptance layer | Mechanical checks miss usability, accessibility, perceptual quality or representative use; connect them to the actual journey and appropriate human judgment. | Representative checks predict acceptance reliably across the supported conditions. Narrow manual review where evidence justifies it. |
| Knowledge state | An unfinished retrieval or obsolete environment observation becomes current fact; expose continuation, coverage, observed conditions and invalidation inputs. | Complete retrieval and condition-aware revalidation do not reduce mistaken authority claims. Investigate interpretation, source reliability or missing authority. |
| Harness and environment | Inferred capabilities differ from effective permissions or runtime state; probe the actual boundary and use supported recovery. | Probes are accurate but execution still fails. Repair the actual service or respect a true denial; additional probing cannot grant permission. |
| Flow and resources | Preservation depends on task closure and narrow timing hides queues; separate resource ownership from completion and measure whole feedback intervals. | Resources converge but accepted delivery does not improve, or cleanup causes reconstruction and cache loss. Reconsider the bottleneck and retention policy. |
| Measurement and incentives | Activity proxies or model-based polling consume attention without a meaningful state change; use deterministic changed-state summaries and outcome measures. | Observation cost falls but missed changes, recovery latency or defects rise. Restore the necessary observation coverage. |
| Learning system | Each recurrence adds prose at the same ineffective layer; test the smallest scoped or mechanical intervention in the normal instruction stack. | Short instructions demonstrably prevent recurrence at lower total cost. Keep that successful control rather than mandate a tool rewrite. |

These are competing diagnoses, not labels that prove their own causes. A single
incident can involve several classes; retain the first failing boundary and
counterevidence rather than retrofitting every failure to the favored model.

## Alternatives and revision conditions

Instruction-only control is cheap to introduce and appropriate for unusual
conventions or decisions that cannot be mechanized. It becomes a poor bargain
when recurring text and repeated interpretation cost more than a maintained
native check. Gate-heavy pipelines and routine multi-agent review can catch
consequential mistakes, but can also delay delivery and reproduce a shared
premise. Add independent review where it changes available information,
expertise or judgment; no fixed agent ratio follows from this research.

A large new control platform is not the default response. Existing tasks,
commands and evidence artifacts may already encode the needed facts. Retire or
scope a proposed control if it duplicates those records, increases human rescue,
delays architecture decisions, loses useful caches, encourages evidence
administration instead of capability, or repeatedly needs exceptions for normal
work. A model, harness or task-distribution change may invalidate a prior local
comparison; preserve the evidence but qualify its applicability.

## Pilot design and unresolved acceptance

Use the [behavioral protocol](../experiments/outcome-evidence-control.md) and
[outcome scorecard](../docs/measurement/metrics.md#outcome-and-complete-operation-scorecard).
A tool regression verifies mechanics; a synthetic release verifies its narrow
scenario. Neither demonstrates sustained agent adherence or delivery improvement.

For a prospective pilot, preserve authorized scope, required source coverage,
permissions, quality and acceptance in both conditions. Start with existing logs
and a small matched or alternating-wave sample across comparable task classes.
Choose sample size after inspecting baseline variance and feasible observation;
no fixed item count is statistically justified by these sources. A behavioral
trial can test a failure channel before a portfolio comparison is possible.

Record authorization-to-acceptance elapsed time, including queueing, builds,
retries, external waits, review and handoffs. Separate active effort from elapsed
time, and do not double-count parallel execution. Also retain post-claim rework,
escaped defects, human rescue effort, complete edit-to-trustworthy-evidence
latency, repeated computation, model use and unresolved WIP. Measure **control
overhead** separately: planning, status extraction, orchestration, evidence
administration and review needed to operate the control. Useful validation can
cost time; classify consistently rather than hide it from total lead time.

Prespecify the comparison, acceptance checks, failure categories and any
owner-chosen adoption thresholds. Such thresholds are optional local decision
rules, not literature-derived effect sizes, mandatory quotas or permission to
weaken quality. Retain failed runs, healthy contrasts, incomplete items and
unavailable measurements; premature stops and exclusions can bias the result.

Control or record model and harness versions, context availability, task size and
difficulty, repository familiarity, evaluator attention, concurrent workloads,
cache state, service incidents and human participation. Historical-only before/
after comparisons cannot separate these confounds. Check selection and task
submission bias, and distinguish speed perceptions from measured intervals; the
[METR field study and follow-up](outcome-control-source-map.md#field-study)
illustrate why both matter. Benchmark horizons do not forecast a particular
project's safe autonomous duration; see
[evaluation limits](outcome-control-source-map.md#evaluation-limits).

Adopt incrementally only when the observed benefit justifies its full cost at the
same quality. If uncertainty remains, report it and continue independent product
work rather than declare the pilot successful or make an unavailable process
trial a blocker. No percentage improvement, vendor hierarchy or portfolio
productivity result is established by this synthesis.
