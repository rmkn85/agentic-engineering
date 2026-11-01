# Reasoning effort, settled plans and proportional sampling

Reviewed **2026-11-01**. Status: external research synthesis and repository operating
choices; no repository-specific causal efficiency result or historical audit.

## Problem and mechanism

Treating higher effort as a general quality upgrade can spend reasoning on decisions
already resolved. Instructions demanding alternatives or certainty can independently
increase work. Model capability, effort, exploration instructions, scope authority
and worker lifetime are separate controls. A passing result can still contain
unnecessary redesign or repeated verification, so acceptance alone cannot identify
all process waste.

The operational rule lives in the [canonical routing policy](../docs/local-codex/subagents.md#choose-effort-for-the-unresolved-decision):
spend reasoning on remaining uncertainty, execute adequate accepted decisions,
diagnose before escalating, and return resolved work to its execution owner.
Necessary diagnosis and complete acceptance remain part of the task.

## Primary sources and limits

### Effort economics

[Sun et al., *What Effort Level Should I Choose? On the Economics of Reasoning Effort
in LLM Agents*, arXiv:2610.34491v1, 2026-10-25](https://arxiv.org/html/2610.34491v1),
especially §§2–3.4 and appendices H–J:

- **Measured:** increased effort can change strategy and verification behavior,
  and spend more on tasks lower effort already solves. Aggregate improvement does
  not guarantee that every individual run improves.
- **Limit:** most agentic conditions have one run per task. Repeated-run analysis
  cautions that observed reversals do not establish systematic decreases in
  task-specific success probability. GPT-6.1 Sol and approved-plan adherence were
  not tested.
- **Limit:** reference-fix access affected the original coding benchmark; use the
  corrected environment when interpreting results. The extreme cost ratio is not
  a forecast for this repository or its current models.
- **Proposed policy studied:** lowest reasoning-enabled effort followed by a fresh
  highest-effort attempt after external failure verification. This is not evidence
  for a mandatory one-step Low → Medium → High staircase, and verifier availability
  limits applicability.

### Prompt-induced exploration

[*Prompt-Induced Waste in Coding Agents: Reasoning, Effort, Harness Design, and
End-to-End Cost*, arXiv:2608.01347v4](https://arxiv.org/html/2608.01347v4),
especially §§2–4, 8 and 10:

- **Measured:** under matched task/model/harness conditions, multiple-approach
  instructions increased reasoning and discarded branches without a credible
  overall success benefit on the tested bounded tasks.
- **Limit:** architecture-heavy work is underrepresented. Prompt effects and effort
  effects are separate comparisons; these results do not establish that High
  generally harms engineering or that exploration is unnecessary for open decisions.
- **Boundary:** premature stopping can hurt ambiguous tasks. Preserve necessary
  investigation and independent checks when adopting concise execution wording.

### Current platform guidance

[OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)
documents Medium as GPT-6.1 Sol's default.
[OpenAI reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning)
describes the effort tradeoff in reasoning allocation, latency and token use.
These support an intentional baseline, not proof that Medium is optimal for every
task. Model support and defaults can change; recheck them when changing routing.

## Repository choices and tradeoffs

These are **engineering operating choices**, not experimental findings:

- Retain the existing named pairs, Sol 6.1/Medium root and Luna/Medium child
  fallback. Use deterministic tools and explicit dispatch for actual assignments.
- Reopen settled choices on evidence of infeasibility, requirement conflict,
  material risk or acceptance failure; revise only what the evidence requires.
- Diagnose failures. Change effort or capability for a specific reasoning
  bottleneck, including a known difficult decision before any failed attempt.
- Use a representative sample only when it can inform selection for substantial
  remaining work and plausibly repay sample, review, reconstruction and integration
  costs. Prefer useful production output and reuse valid accepted results. Use
  defaults when likely benefit is unclear.

Expected benefit: less unnecessary branching, unchanged verification and expensive
worker reuse. Possible cost: underestimating uncertainty can cause rework; an overly
rigid reading can suppress justified replanning. Preserve direct High selection,
ordinary judgment, current authority and complete acceptance to limit that risk.
Existing scoped authorization requirements for xhigh/max and Ultra remain intact.

The supplied research brief also proposed an automatic escalation helper, telemetry
schema, benchmark profiles, campaigns and canary thresholds. Those are proposals,
not source evidence or instructions to implement them. This update adds none of
those mechanisms: their overhead has not been justified for ordinary routing.

## What would revise the practice

Use existing delivery evidence and the [adherence scenarios](../experiments/instruction-context-adherence.md#reasoning-effort-and-settled-plan-cases).
Repeated substantive failures attributable to inadequate reasoning would favor a
stronger route for that task class. Repeated unjustified reopening or redundant
checks would favor better instruction placement or clearer task authority. Compare
accepted outcomes, rework, human effort, elapsed time and available usage when a
consequential decision warrants a trial; keep missing attribution unknown.

To isolate wording, hold model and effort fixed. To isolate effort, hold task,
instructions, tools and permissions fixed. Judge whole accepted outcomes, including
sampling and integration overhead. Do not promote a historical anecdote, one
successful run, static checks or a coached policy review into measured savings.
