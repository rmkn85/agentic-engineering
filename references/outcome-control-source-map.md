# Outcome-control source map

Reviewed 2026-11-07. On-demand research provenance for
[outcome and evidence control](outcome-evidence-control-2026-11.md), not ordinary
agent instructions. This scoped map verifies ten source groups supporting the
mechanisms and evaluation design. It is not an exhaustive literature review.
Links lead to the actual source; findings below are paraphrases.

## SPACE

**Source:** Forsgren et al., *The SPACE of Developer Productivity*, 2021,
[author institution publication record](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/).

**Verified support:** The framework argues that individual activity and system
efficiency alone do not represent productivity; measurement needs multiple
dimensions. **Type:** research framework, not a controlled intervention trial.
**Transfer:** keep accepted outcomes, quality, flow and human effort visible.
**Limit:** does not validate this repository's metrics or agent controls.

## DORA

**Source:** DORA, *State of AI-assisted Software Development 2025*,
[official report summary](https://dora.dev/research/2025/dora-report/).

**Verified support:** The official summary characterizes AI as amplifying an
organization's existing strengths and weaknesses, with returns depending on the
surrounding system. **Type:** report summary of organizational research.
**Transfer:** evaluate selection, feedback and delivery alongside tool use.
**Limit:** the inspected summary supplies neither a causal estimate for this
control model nor evidence that any one proposed mechanism is necessary.

## Parnas

**Source:** D. L. Parnas, *On the Criteria To Be Used in Decomposing Systems into
Modules*, Communications of the ACM 15(12), 1972,
[DOI](https://doi.org/10.1145/361598.361623),
[full paper hosted by a university](https://john.cs.olemiss.edu/~hcc/csci555/notes/localcopy/Parnas_Criteria_Decomposing.pdf).

**Verified support:** The paper compares decompositions, treats modules as
responsibility assignments, and favors hiding changeable design decisions over
mirroring processing steps. **Type:** conceptual argument with a worked design.
**Transfer:** protect internal decision ownership when delegating a consumer
problem. **Limit:** this is not an empirical study of team or agent organization;
information hiding does not make interfaces permanently unchangeable. The ACM
endpoint denied retrieval; the full original paper was inspected at the
university copy. A separate institutional deposit dates its record to 1995;
that metadata is not the original publication year.

## Flow

**Sources:** *An empirical study of WIP in kanban teams*, ESEM 2018,
[author institution abstract and bibliographic record](https://www.sintef.no/en/publications/publication/0198cc68f9da-52d0d8f1-3d82-461c-970c-21d8229b9ac3/),
[DOI](https://doi.org/10.1145/3239235.3239238);
DORA, [Working in small batches](https://dora.dev/capabilities/working-in-small-batches/),
page updated 2025-12-08.

**Verified support:** The Kanban abstract describes more than 8,000 items across
five teams over four years: lower WIP correlated with shorter lead time, but
productivity relationships did not support simple WIP minimization. Quality
information was insufficient and the authors call for replication. DORA describes
small independently testable batches and warns against regrouping them before
downstream feedback. **Type:** observational case study plus documented delivery
practice. **Transfer:** test WIP and complete feedback paths locally.
**Limit:** no universal WIP limit or agent-concurrency target follows. The supplied
report's attribution to “Santos et al.” conflicts with the inspected SINTEF
record, which lists Dag Sjøberg; retain title/DOI rather than repeat that attribution
without the full proceedings metadata.

## SRE

**Sources:** Vivek Rau, [Eliminating Toil](https://sre.google/sre-book/eliminating-toil/),
*Site Reliability Engineering*; Steven Thurgood,
[Example Error Budget Policy](https://sre.google/workbook/error-budget-policy/),
*The Site Reliability Workbook*, policy dated 2018-02-19.

**Verified support:** Toil is recurring, automatable operational work without
enduring value; administrative overhead is distinguished from toil. The example
error-budget policy balances customer reliability and feature work using an
explicit SLO and exceptions. **Type:** documented organizational practice.
**Transfer:** reduce repeated observation/recovery where worthwhile, measure
management overhead separately, and make real stop conditions explicit.
**Limit:** neither text authorizes bypassing permissions or establishes an agent
management quota. Their numeric policies are contextual examples.

## Context

**Source:** Gloaguen et al., *Evaluating AGENTS.md: Are Repository-Level Context
Files Helpful for Coding Agents?*,
[arXiv v3, 2026-09-29](https://arxiv.org/html/2602.11988v3).

**Verified support:** The study evaluates generated and developer-provided
context files on SWE-bench and Python CTXbench tasks. It reports no general
significant task-success benefit and increased inference work; developer files
perform better than generated ones. Its ablations do not establish file length
as the causal factor. **Type:** empirical benchmark study, preprint.
**Transfer:** test useful nonstandard instructions in the actual stack instead of
assuming more prose helps. **Limit:** Python task resolution does not establish
effects on long-running ownership, security, all toolchains or all instructions.
Do not infer that shortening a file alone improves outcomes.

## Monitoring

**Source:** Liu et al., *Online Monitoring and Corrective Steering of Programming
Agents*, [arXiv v1, 2026-08-07](https://arxiv.org/html/2608.06701v1).

**Verified support:** LivePlan separates deterministic trajectory signals from
advice, consulting an advisor when a signal fires. The paper evaluates the design
with SWE-agent, three executors, two advisors, SWE-bench Verified and Pro, including
ablations and a bounded check of run nondeterminism. **Type:** empirical benchmark
study, preprint. **Transfer:** test changed-state detection and selective advice.
**Limit:** benchmark resolution is not accepted multi-day product delivery;
phase-based signals may misclassify valid exploration. Deterministic rules can
still encode a bad proxy. No intervention effect size is transferred here.
The primary paper replaces the supplied report's secondary research-record link.

## Field study

**Sources:** Becker et al., METR,
[Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/),
2025-07-10; [experiment-design update](https://metr.org/blog/2026-02-24-uplift-update/),
2026-02-24.

**Verified support:** The original RCT randomized AI availability for real tasks
submitted by experienced developers in familiar repositories. Perceived speed
and measured task time disagreed. The later update explicitly describes
participation/task selection, changed compensation and concurrent-agent timing
as obstacles to estimating a current effect. **Type:** randomized field study
plus follow-up methodological observations. **Transfer:** fix task definitions,
measure whole intervals and examine selection/confounding. **Limit:** neither
historical results nor biased follow-up estimates establish current agent
productivity or an intervention effect for this repository.

## Evaluation limits

**Source:** METR,
[Task-Completion Time Horizons](https://metr.org/time-horizons/),
last updated 2026-09-08; methodology linked there.

**Verified support:** A horizon estimates success probability against human-expert
task duration, not how long an agent should run. Tasks are chiefly self-contained,
well-specified software, ML and security tasks with automatic evaluation. Human
timing, task distribution and extrapolation beyond the suite limit interpretation;
the page says it is no longer actively maintained. **Type:** empirical evaluation
methodology and measurements. **Transfer:** evaluate reliability at the task and
acceptance actually required. **Limit:** benchmark horizons do not establish safe
multi-day autonomy, experiential quality or a universal stopping deadline.

## Evolution benchmarks

**Sources:** Deng et al.,
[SWE-Bench Pro v2, 2025-11-14](https://arxiv.org/abs/2509.16941v2);
Le et al., [SWE-EVO v6, 2026-05-22](https://arxiv.org/abs/2512.18470v6).

**Verified support:** Pro targets more complex multi-file issues than the
original SWE-bench; EVO builds evolution tasks from release notes of seven
mature Python projects and evaluates against test suites. These broaden the
construction of coding evaluations beyond a narrow issue sample.
**Type:** benchmark construction and empirical evaluation papers; abstract-level
verification here. **Transfer:** test cumulative changes and preserved behavior,
not only isolated patches. **Limit:** different models, scaffolds, tasks and
versions prevent treating cross-benchmark score gaps as a controlled causal
comparison. Neither suite recreates evolving real users, permissions, deployment
state and subjective acceptance. No vendor performance hierarchy is inferred.

## Provenance exclusions and open checks

The supplied report contains session-local citation tokens and file citations;
these are not independently retrievable public references. They were not copied
or treated as evidence. Its private case observations were not reproduced or
published here. The mechanism proposals remain hypotheses even where a related
public source is verified.

The report also invokes a systematic mapping study, requirements-failure
research, high-reliability practice and trajectory/verification studies without
enough bibliographic detail in the supplied bibliography to resolve each exact
claim in this bounded pass. Those claims remain **unverified and unused** here;
missing verification is not evidence of fabrication. Its platform implementation
claims and current vendor-documentation descriptions were not needed for this
synthesis and remain unaudited. A documentation capability alone would not prove
that a host adopted it correctly or that it improved outcomes.

The shared-workspace coordination DOI in the supplied bibliography resolves to a
[primary publisher record](https://doi.org/10.4230/LIPIcs.ESEM.2026.18) matching the
stated title and authors. Metadata was verified; the detailed concurrency claims
were not audited and are not used to prescribe shared writing or agent counts.
SWE-Lancer is outside the selected mechanism evidence; its quantitative results
were not rechecked or reused. Omission here means scoped exclusion, not rejection.

Future revisions should inspect full methods when a decision depends on a
specific study effect, resolve the WIP author discrepancy before an author-level
citation, and update changing agent evidence when the tested model, harness or
workload changes. Do not make these research checks prerequisites for independent
authorized product work.
