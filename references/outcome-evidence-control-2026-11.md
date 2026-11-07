# Outcome and evidence control: research rationale

Reviewed 2026-11-07. This is methodology research, outside the normal execution
corpus. The operational owners are [direct delivery](../docs/execution/direct-delivery.md),
[bounded recovery](../docs/execution/bounded-recovery.md),
[observation economy](../docs/execution/observation-economy.md) and
[resource lifecycle](../docs/execution/resource-lifecycle.md).

## Human engineering management and coding agents

The [SPACE paper](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/)
(Forsgren et al., 2021) argues that developer productivity cannot be represented
by one activity measure or dimension. This supports preserving outcome, quality,
flow and human effort separately. It does not prescribe an agent status schema or
prove that this repository's controls improve productivity.

Google's [Eliminating Toil](https://sre.google/sre-book/eliminating-toil/)
(Rau, *Site Reliability Engineering*) distinguishes enduring engineering value
from recurring operational work. Our inference is to move repeated unchanged
observation and routine recovery into maintained deterministic routes, while
retaining human/agent judgment for decisions. Automation that produces more
maintenance than useful delivery fails that purpose; a temporary manual action
can remain the cheapest adequate choice.

The [2025 DORA report's official summary](https://dora.dev/research/2025/dora-report/)
describes AI as amplifying existing organizational strengths and weaknesses.
This supports examining selection, feedback and delivery organization alongside
the coding tool. That summary is not a controlled trial of the interventions
here and supplies no transferable effect size for them.

[Evaluating AGENTS.md](https://arxiv.org/abs/2602.11988v3)
(Gloaguen et al., v3, 2026-09-29) reports that repository context files did not
generally improve task success and increased inference cost in its evaluated
settings; non-standard conventions were a useful role for instructions. The
study covers particular agents, repositories and benchmark tasks. It does not
establish that all instructions are harmful or that long-running product work
needs no guidance. Our design inference is to keep the recurring core small,
place mechanical obligations in tools, and test behavior through the actual
instruction route before claiming improvement.

## Proposed mechanisms and competing explanations

| Failure | Intervention and expected benefit | Cost, counterexample and revision condition |
| --- | --- | --- |
| Ready work displaces the required journey | Select from the current outcome gap; test necessity before adding interfaces | Investigation has value too; retain a bounded experiment when it changes the decision |
| Local success becomes global completion | Independent applicable claims, native verdicts and actual consumer identity | Avoid imposing deployment on source-only work; revise if claims become duplicate bookkeeping |
| Partial or stale evidence becomes authority | Coverage/continuation and input-based invalidation | Reprobe mutable facts only when relevant conditions change; immutable evidence remains reusable |
| Recovery becomes abandonment or permission evasion | Classify the actual boundary; repair internal limits within real authority | A true denial or exhausted user ceiling remains binding |
| Resource retention depends on task closure | Preserve unique state, verify the checkpoint, retire owned disposable resources | Shared caches and active consumers can justify retention; failed preservation forbids deletion |
| Proxy speed hides slow delivery | Measure scoped feedback and accepted delivery intervals, including control overhead | Missing timing stays unknown; neither smaller logs nor a faster component proves a better outcome |

These are engineering hypotheses. The deterministic helpers can establish their
specified mechanics, and a synthetic release trial can establish a narrow
consumer result. Neither demonstrates sustained model adherence or portfolio
productivity. Alternative explanations include clearer tasks, model differences,
changed environments, easier samples and extra evaluator attention.

Use the [behavioral protocol](../experiments/outcome-evidence-control.md) and
[outcome scorecard](../docs/measurement/metrics.md#outcome-and-complete-operation-scorecard).
Preserve failed attempts and healthy contrasts; compare matched conditions where
practical. Adopt controls incrementally through the existing native owner, then
scope or retire them if they add rescue work or delay without compensating quality.
No percentage improvement or universal staffing/prompt ratio is established here.
