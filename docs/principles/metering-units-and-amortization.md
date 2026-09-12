# Metering units and amortization

Reviewed: 2026-09-12

Token count is only one possible accounting unit. Agentic systems can be constrained by messages, research tasks, model tokens, credits, tool/API invocations, concurrent workers, compute windows, wall time, files or bytes processed, and human turns. An efficiency strategy that ignores the actual scarce unit can optimize the wrong thing.

## The accounting unit is part of the execution surface

For every surface, identify both:

1. the **physical work** performed: model tokens, searches, file reads, commands, tests, browser actions, subagents, compute; and
2. the **user-facing meter** that depletes: message allowance, research-task allowance, Work/Codex credits, API dollars, external-tool quota, rate-limit window, or another counter.

These need not be proportional.

A single top-level operation may contain a large amount of nested work. Conversely, a small top-level operation may consume the same quota unit as a much more substantial one.

## Fixed-quantum versus variable meters

### Message-metered surfaces

When a plan publishes a quota in messages, the scarce subscription unit is the user message, not the number of underlying tokens exposed to the user.

For example, on the review date OpenAI documents GPT-6 Pro Chat on Pro $200 as 200 messages per week. A coherent user request that causes a long, complex answer still occupies one published Chat message unit, subject to the product's context, response, tool, safety and runtime limits.

Therefore, when quality is preserved, **amortizing substantial coherent work into one message can be more quota-efficient than fragmenting the same work across many conversational turns**.

This is not a recommendation to create oversized prompts. A task should remain coherent and reviewable; packing unrelated work together can reduce quality, exceed context/runtime limits, or make failures expensive to recover.

### Task/use-metered surfaces

Some features are metered in top-level tasks or uses rather than every internal operation.

Chat Deep Research is an important example. OpenAI describes its Chat allowance in research **tasks** and exposes a remaining-task counter. One research task may perform many searches, page reads and synthesis steps internally; those underlying searches are not each a separate Chat Deep Research task from that allowance.

Deep Research in Work or Codex is different: it uses the existing Work/Codex allowance or credits rather than the separate Chat Deep Research task allowance.

This creates a real amortization boundary: use one research task for one coherent research outcome rather than unnecessarily splitting a single question into many separately metered research tasks.

### Token/credit-metered surfaces

Work, Codex and direct API usage are much closer to variable-cost meters. More model context, reasoning, output, tool-result text and subagent work can consume more allowance or credits even if the user initiated it with one instruction.

Here, combining work into one top-level request does not make the nested model work free. Stable context, caching, concise tools, incremental validation and avoiding duplicated agents remain important.

### Invocation-metered tools

External tools and services may impose their own per-call, per-search, per-file, per-minute or per-request limits. These meters can sit underneath a message- or task-metered parent operation.

Do not assume that because the parent surface charges one message or one task, every nested service is unmetered.

## Hierarchical metering

Treat an agentic run as a tree of meters rather than one scalar cost:

```text
one top-level message / task
        |
        +-- model inference tokens
        +-- web/search/browser operations
        +-- file reads and writes
        +-- shell/tool calls
        +-- subagents
        |      +-- their own model tokens and tools
        +-- deterministic compute
        +-- human follow-up turns
```

The top-level quota and the nested resource costs can both matter. Optimize at the level that is actually scarce while preserving the required outcome.

## Amortization metrics

Useful derived metrics include:

- **accepted work per message** — useful accepted outcome divided by user messages consumed;
- **accepted research per research task** — useful research outcome divided by top-level research uses;
- **accepted work per agentic credit** — useful accepted outcome divided by Work/Codex credits;
- **accepted work per API dollar** — for direct API workflows;
- **human-turn efficiency** — useful progress per required user intervention;
- **invocation amplification** — nested model/tool/subagent invocations per top-level task;
- **context amplification** — total model input across all workers divided by unique task-relevant information;
- **compute amplification** — repeated deterministic work divided by the minimum necessary deterministic work.

The numerator must include quality. A huge amount of incorrect work per message is not efficient.

## Scheduling implication

The router should know not only which model and surface are capable, but also the **marginal accounting unit** of the next action.

Examples:

- If GPT-6 Pro Chat is message-metered, prefer one well-scoped complete semantic job over a chain of tiny prompts when the single job can be completed reliably.
- If Chat Deep Research is task-metered, ask one coherent research question with all necessary dimensions rather than spending several tasks on artificial fragments.
- If Codex is token/credit-metered, reducing repeated context and unnecessary subagents matters even when everything happens under one user request.
- If an external API is per-call metered, batch or cache deterministic calls when its semantics allow it.

## Do not optimize the meter by damaging the task

Meter-aware execution is not quota gaming.

Bad examples:

- combining unrelated work merely because one message is cheaper;
- refusing useful clarification when ambiguity would make a long run fail;
- forcing a huge research problem into one task when independent validation requires separate runs;
- hiding failures to avoid another message;
- choosing a surface with a favorable top-level quota but poor repository state, causing more total work.

Good examples:

- provide all relevant constraints and desired outputs in the first coherent request;
- let one expensive message or research task do substantial internally coherent work;
- use deterministic local computation freely when it does not consume the scarce model meter;
- preserve intermediate state so a necessary follow-up does not replay the whole job;
- compare both top-level quota depletion and nested resource amplification.

## Current OpenAI examples

These are dated examples, not permanent product rules.

- GPT-6 Pro Chat on Pro $200 is currently documented as 200 messages per week; Work and Codex have separate allowances.
- Chat Deep Research has a plan-dependent task allowance with an in-product remaining-task counter.
- Deep Research in Work/Codex consumes the Work/Codex allowance or credits instead of the Chat Deep Research task allowance.
- Codex usage depends on model, execution location, complexity, context, reasoning, speed and tools; a long-running task can consume substantially more than a short request.

Authoritative sources:

- OpenAI Help: [GPT-5.6 and GPT-6 Pro in ChatGPT](https://help.openai.com/en/articles/20001354)
- OpenAI Help: [Deep research in ChatGPT](https://help.openai.com/en/articles/10500283)
- OpenAI Help: [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540)
