# Execution surfaces and usage pools

Reviewed: 2026-09-15

Efficiency decisions should separate three different questions:

1. **Which model is capable enough?**
2. **Which execution surface best matches the work?**
3. **Which usage pool or billing meter will pay for it?**

These are related, but they are not the same decision. Using the same model through different surfaces can consume different user-facing allowances even when the underlying model capability is similar.

## Durable rule

Choose the cheapest capable combination that preserves the required outcome and quality bar.

Do not spend a scarce model or agentic allowance merely because it is available. Conversely, do not downgrade model quality or force work through an awkward surface solely to save quota when that creates retries, lost context, or lower-quality output.

## Route coupled synthesis separately from routine execution

Model capability is most valuable where one decision must reconcile several uncertain concerns at once. Examples include translating an experiential goal into architecture, preserving a product invariant through a cross-layer redesign, converging art direction, authored assets and runtime constraints, interpreting visual and runtime evidence together, or diagnosing a failure whose cause may cross state, timing, rendering and resource boundaries.

"Bounded" describes the assignment's ownership and context, not the model strength it requires. A bounded specialist may be stronger than the orchestrator coordinating it. Consider a stronger, scarcer model for a bounded synthesis or diagnosis pass when most of these are true:

- the desired outcome is clear enough to judge but the implementation route is materially ambiguous;
- several interacting boundaries must change coherently;
- local fixes are likely to move the problem or violate a distant constraint;
- evidence includes semantic or perceptual judgment that deterministic checks cannot resolve;
- a mistaken decision would create substantial rework, and a concise decision artifact can guide later execution.

Use judgment across the factors; they are not a numeric score or fixed threshold.

Use a sufficiently capable cheaper worker for bounded implementation when the contract, owned files, dependencies and acceptance checks are already explicit. This includes routine code changes and asset production after the reference, format, budgets and review criteria are settled. Use deterministic tools for exact inspection and repetition: state snapshots, counters, replay setup, captures, diffs, builds, tests and controlled measurements.

Select capability from the executors and models exposed by the current run. Do not route from a remembered model catalog. If the coordinator cannot judge or integrate the specialist's artifact, raise the integration decision to a capable executor too. Named models belong in dated examples and evidence only; operational routing should survive their renaming or removal.

A practical progression is:

```text
experience / invariant / failure
        ↓  capable synthesis or cross-boundary diagnosis when needed
explicit constraints + chosen boundary + observable acceptance
        ↓  bounded implementation
deterministic replay + state/counter checks + focused tests
        ↓  human or domain judgment at the required acceptance boundary
```

This is a handoff pattern, not a permanent model assignment. After the difficult decision has been expressed as contracts, references, fixtures, scenarios or tests, route routine implementation and verification down again. Escalate only when new evidence reopens the coupled decision, not whenever a check fails.

Do not reserve a strong model for high-volume mechanical work, unconstrained variant generation, repeated test execution, or broad repository reading that exact tooling or bounded workers can perform. Conversely, do not split a tightly coupled synthesis across independent workers merely to reduce per-worker cost; reconciliation can cost more than keeping the decision coherent.

These criteria are an **engineering hypothesis**, not a measured stronger-versus-cheaper-model saving. Validate consequential routing changes on representative accepted work, including retries and rework. OpenAI's [Building games with Astra](https://developers.openai.com/blog/how-to-build-games-with-astra), reviewed September 15, 2026, illustrates this approach through coupled visual/runtime diagnosis, editable asset production and repeatable comparisons. Its model name identifies the source, not a permanent routing target; the article does not establish comparative model savings. Approved references, an explicit authority boundary, a repeatable scenario and an ordinary-input journey make a specialist's decision testable by later executors.

## Execution surfaces

### Chat

Use Chat when the work is primarily semantic reasoning over a bounded amount of repository or document state and the available tools are sufficient to inspect and write the required artifacts.

Examples:

- architecture or taxonomy analysis
- large coherent document review
- independent audit of a completed change
- Git-backed work that needs relatively few mutation/verification iterations

The conversation is primary; repository operations are tools used by the conversation.

### Work

Use Work for general multi-step autonomous work spanning files, browser, apps, or other tools when the task is broader than software engineering.

Work follows the same agentic usage structure as Codex.

### Codex local

Use local Codex when repository state and the iterative engineering loop dominate:

- warm checkout and Git history
- installed dependencies
- build/test caches
- language servers and indexes
- local services
- repeated search/edit/build/test/diff cycles

The repository is primary. This is normally the most efficient execution surface for an established development environment because deterministic state can remain warm indefinitely.

### Codex cloud

Use cloud intentionally when the cloud environment itself creates value:

- genuinely independent substantial tasks that reduce the critical path
- clean-room verification from a fresh environment
- work that must continue without the local execution environment
- reproducible remote environments
- a deliberately independent executor or reviewer
- cloud-only capabilities

Do not choose cloud merely because a task is large. Local and cloud Codex draw from the same broad Work/Codex agentic allowance on ChatGPT plans; actual usage still varies with model, task, context, tools, reasoning, and where the task runs.

See [local-first execution](local-first.md).

## Usage pools are a resource too

For ChatGPT plans, ordinary Chat and agentic Work/Codex do not necessarily consume the same allowance.

As documented by OpenAI on the review date:

- regular Chat model limits are separate from Work/Codex allowances;
- Work and Codex share an agentic usage allowance and credit pool where supported;
- signing in to Codex with ChatGPT uses the ChatGPT plan allowance;
- using Codex with an API key uses API pricing instead;
- local and cloud Codex are both agentic Work/Codex usage, not separate subscription reservoirs.

Therefore, **pool selection can be part of efficient scheduling**. A semantic review that can be done well in Chat may preserve agentic allowance for repository-native execution. A repository mutation/test loop may justify Codex even if Chat has spare capacity.

## Example: Pro $200 on the review date

Current product limits are volatile. Treat this section as a dated example, not a permanent rule.

OpenAI currently documents:

- manually selected GPT-5.6 Sol Medium/High/Extra High uses a Chat reasoning allowance; the public help page does not publish one universal numeric Pro-$200 quota for that allowance;
- GPT-6 Pro Chat on Pro $200 has a published allowance of 200 messages per week;
- GPT-5.6 Sol Pro has a separate 170 messages per day, with GPT-6 Pro + Sol Pro also subject to a combined 200-message daily ceiling;
- GPT-6 Pro and Sol Pro Chat limits are separate from Work/Codex allowances;
- Work and Codex share the plan's agentic allowance.

The practical implication is not "always use Sol". It is:

> If ordinary Sol at the required reasoning level is already capable of the semantic task, do not automatically consume scarcer Astra Chat or Work/Codex capacity.

Reserve stronger or scarcer resources for cases where they materially improve success probability, quality, or total work required.

## A useful scheduling pattern

For mixed repository work:

```text
Chat / capable model
    deep planning, semantic analysis, independent audit
            ↓
Local Codex
    repository mutation, search, build/test/validation loop
            ↓
Chat
    independent result review when valuable
            ↓
Local Codex
    targeted fixes only
```

This is not mandatory orchestration. It is useful only when the phase boundaries are real and transferring the result is cheaper than keeping the entire job in one surface.

## Same model does not imply same cost experience

Holding model capability constant does not make the surfaces interchangeable.

The same model may encounter:

- different context/setup overhead;
- different persistent state and caches;
- different tool affordances;
- different user-facing meters;
- different opportunities for clean-room independence or parallelism.

Compare the full system, not only the model name.

## Do not game quotas at the expense of engineering

Usage pools are constraints to schedule intelligently, not targets to exhaust.

Bad optimization:

- splitting a coherent task only to consume two pools;
- moving an iterative build/test loop into Chat when Codex would avoid repeated state reconstruction;
- using a weaker model when retries erase the nominal saving;
- using cloud fan-out simply because cloud capacity exists.

Good optimization:

- use an abundant capable Chat model for a bounded semantic pass;
- preserve expensive agentic context for execution that actually needs repository-native state;
- choose cloud only when independence, elasticity, or remote persistence has measurable value;
- keep quality and acceptance fixed while reducing total resource use.

## Current authoritative sources

Because product limits change, re-check these before relying on numeric quotas:

- OpenAI Help: [GPT-5.6 and GPT-6 Pro in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt)
- OpenAI Help: [ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275)
- OpenAI Help: [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540)
- OpenAI Help: [Managing usage with GPT-6 Astra in Work and Codex](https://help.openai.com/en/articles/20001516)
