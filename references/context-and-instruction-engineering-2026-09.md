# Context and instruction engineering research — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

This note preserves the external research and design reasoning that led to the current Agentic Engineering guidance on instruction adherence, context economics, progressive disclosure, and behavioral evaluation. Operational conclusions belong in `docs/`; this file keeps the deeper evidence and competing ideas so future maintainers do not have to rediscover them.

Reviewed: 2026-09-13.

## Research question

Two recurring failures motivated this work:

1. a thin/fast agent is economically attractive, but it can ignore execution-efficiency instructions and erase the saving through duplicated work, poor routing, retries, or human correction;
2. attempts to fix that failure by adding more persistent instructions can themselves make the agent worse by consuming context and creating instruction interference.

The target is therefore not the shortest prompt or the most comprehensive prompt. It is the **smallest reliably sufficient working context for the behavior and outcome required by the current task**.

## Main synthesis

Across otherwise different systems, several patterns recur:

- Treat context as a scarce working set, not an archive.
- Keep always-loaded instructions to broadly applicable invariants.
- Scope specialized rules to paths/tasks or load them on demand.
- Keep large rationale/examples/reference material outside the always-loaded layer.
- Prefer deterministic enforcement when a constraint can be checked mechanically.
- Isolate temporary high-volume work in separate contexts/subagents when only the result is needed upstream.
- Inspect what actually enters context rather than assuming configuration equals runtime behavior.
- Evaluate prompts/instructions as executable behavior: baseline, change, pressure scenario, measured outcome.
- Avoid optimizing purely for brevity: compression can discard useful exceptions and domain knowledge.
- Large nominal context windows do not imply equal effective use of every token.

These convergences justify the operational placement ladder and the instruction/context adherence experiment in this repository. They do **not** imply that one framework's workflow should be copied wholesale.

---

## OpenAI — Harness engineering

Source: https://openai.com/index/harness-engineering/

Relevant observation: OpenAI describes an early attempt to use one large `AGENTS.md` as a comprehensive manual. They report predictable failure modes: the file competed with task/code context, too much guidance diluted prioritization, monolithic guidance became stale, and a blob of prose was hard to verify mechanically. Their corrective pattern is to give agents a compact map into repository knowledge rather than loading the whole manual up front.

### What this suggests here

Adopt:

- make the root instruction file a map + invariants, not the research corpus;
- keep deeper docs structured and navigable;
- make operational knowledge verifiable where possible;
- separate provenance/reference depth from execution context.

Do not over-generalize:

- a large file is not bad merely because it is large; the question is whether it is automatically resident and whether the task needs it;
- this is evidence from one production environment, not a universal line-count threshold.

---

## Anthropic — Effective context engineering for AI agents

Source: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

Anthropic frames context engineering as choosing the configuration of tokens most likely to produce the desired behavior. The important shift is from wordsmithing a prompt toward curating the whole model-visible state. Context is finite and should contain the information necessary for the current decision, rather than everything that might possibly be useful.

### What this suggests here

Adopt:

- optimize token **utility**, not prompt length in isolation;
- distinguish information that must be resident from information that merely must be retrievable;
- treat instructions, retrieved files, tool output, memory, schemas, and conversation history as one competing working set.

Counterweight:

- “minimal” should mean minimal **while preserving the required behavior and knowledge**, not aggressively terse.

---

## Claude Code — explicit context accounting and progressive disclosure

Sources:

- https://code.claude.com/docs/en/features-overview
- https://code.claude.com/docs/en/context-window
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/debug-your-config
- https://code.claude.com/docs/en/costs

Claude Code currently exposes unusually explicit documentation of what consumes context. Its docs describe project instructions, memory, skill descriptions, MCP/tool metadata, files, outputs, and conversation as competing users of the same working window. `/context` shows the actual breakdown in a running session.

Important design patterns:

- `CLAUDE.md` is always-loaded context; the docs recommend keeping it focused (currently suggesting roughly under 200 lines) because longer persistent instructions can reduce adherence.
- path-scoped rules load when matching files are relevant;
- skills provide progressive disclosure: descriptions are discoverable first and bodies load when used;
- large supporting references can remain separate from `SKILL.md` and be read only when needed;
- subagents provide context isolation: heavy intermediate reads/tool calls can remain outside the main context and only a result comes back;
- hooks can enforce deterministic behavior without asking the model to remember another prose rule;
- the tooling provides diagnostics (`/context`, `/memory`, `/mcp`) to verify what actually loaded.

The skills documentation also warns that once a skill body is loaded it remains a recurring context cost for the session. Progressive disclosure delays the cost; it does not make loaded content free.

### What this suggests here

Adopt as general mechanisms, not Claude-specific requirements:

1. **inspect residency** — know what is loaded before adding more;
2. **scope by relevance** — path/task specific guidance should not be global;
3. **use on-demand modules** for workflows/reference material;
4. **quarantine high-volume intermediate context** when only conclusions are needed upstream;
5. **move enforceable constraints into code/hooks/tests** where practical;
6. distinguish discovery metadata cost from full-body cost.

Do not adopt the 200-line recommendation as a universal law. Different harnesses load files differently; behavioral evaluation matters more than a fixed length.

---

## Cursor Rules — make context residency an explicit policy

Sources:

- https://docs.cursor.com/context/rules
- https://prod.cursor.com/docs/rules

Cursor exposes several rule-loading modes: always included, automatically attached by matching files, agent-selected based on a description, and manual inclusion. Nested rules can scope knowledge to repository subtrees.

### What this suggests here

The important insight is not the `.mdc` format. It is the **residency model**:

- always;
- deterministic/path-triggered;
- relevance-triggered;
- explicitly/manual on demand.

Agentic Engineering should teach users to decide which residency class an instruction deserves before polishing its wording.

---

## GitHub Copilot — repository vs path-specific vs interaction-specific context

Sources:

- https://docs.github.com/en/copilot/concepts/prompting/response-customization
- https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions
- https://docs.github.com/en/copilot/reference/custom-instructions-support

GitHub distinguishes repository-wide instructions, path-specific instructions, agent instruction files, and reusable prompt files. Its documentation explicitly presents path-specific instructions as a way to avoid overloading repository-wide guidance with information that only applies to some files.

### What this suggests here

Adopt the general decision rule:

- repository/global instructions only for cross-cutting invariants;
- deterministic file/directory relevance should trigger scoped guidance;
- one-off workflow/task material belongs in an invoked prompt/skill rather than permanent global context.

Also note GitHub's explicit caveat that probabilistic agents may not follow custom instructions identically on every run. Configuration presence is therefore not a sufficient acceptance test.

---

## LangChain / Deep Agents — context includes tools and lifecycle state

Sources:

- https://docs.langchain.com/oss/python/concepts/context
- https://docs.langchain.com/oss/python/langchain/context-engineering
- https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
- https://docs.langchain.com/oss/python/deepagents/context-engineering

LangChain's current context-engineering material usefully broadens the object being optimized. Model context includes instructions, messages, tools, model choice, and response format; lifecycle mechanisms can summarize or filter state between calls. The docs also state that exposing too many tools can overload context and increase errors, motivating dynamic tool selection. Subagents are described partly as context isolation: intermediate tool activity stays in a separate window.

### What this suggests here

Add to Agentic Engineering's context accounting:

- tool names/descriptions/schemas are part of the context budget;
- MCP/plugin proliferation can therefore have an instruction-like tax even if the human prompt is tiny;
- context policy may need to select tools dynamically, not merely shorten prose;
- summarization/offloading and subagent isolation are context mechanisms, not automatically cost wins — model-call overhead and lost detail still need consideration.

---

## Promptfoo — treat prompts/instructions as testable artifacts

Sources:

- https://www.promptfoo.dev/docs/configuration/guide/
- https://www.promptfoo.dev/docs/usage/prompt-optimization/

Promptfoo's useful contribution here is methodological: define test cases and assertions, establish a baseline, evaluate candidate prompt variants, and compare measured behavior rather than relying on prompt aesthetics. Its prompt optimizer builds candidate revisions from observed failures and re-evaluates them against the same tests.

### What this suggests here

Agentic Engineering does not need Promptfoo as a dependency. It should copy the discipline:

- fixed task fixture;
- fixed model/settings where possible;
- acceptance assertions;
- multiple stochastic runs when variance matters;
- prompt/instruction variant as the independent variable;
- tokens, latency, retries, and human correction reported only alongside quality.

This supports instruction ablation and context-pressure testing.

---

## DSPy — optimize instructions against a metric rather than folklore

Source: https://dspy.ai/

DSPy treats LM behavior as a program that can be optimized against an explicit metric and training/examples rather than endlessly hand-tuning prompt text. Current DSPy optimizers generate and evaluate instruction/demonstration variants against the metric.

### What this suggests here

The transferable lesson is modest but important:

- human-written instructions are candidate implementations, not sacred artifacts;
- once a behavioral metric exists, automated or semi-automated search over instruction variants becomes possible;
- optimization must keep acceptance/quality as the objective constraint, otherwise it can cheaply optimize the wrong behavior.

Agentic Engineering should first make behavioral fixtures reproducible; automated prompt search can remain optional/later.

---

## ACE — Agentic Context Engineering

Source: https://arxiv.org/abs/2510.04618

ACE treats context as an evolving playbook and calls out two failure modes of naive compression: **brevity bias**, where useful domain insights disappear because shorter summaries are preferred, and **context collapse**, where repeated rewriting gradually erodes detail. Its approach incrementally updates structured context rather than repeatedly replacing everything with an increasingly compressed summary.

### What this suggests here

This is an important counterweight to instruction minimization:

- do not optimize for smallest byte count;
- preserve exceptions, failure modes, and decision-bearing evidence outside the always-loaded layer;
- prefer moving depth into retrievable references over deleting it;
- version or incrementally curate durable knowledge rather than repeatedly summarizing a summary.

This directly motivates the `references/` split: remove research from runtime context **without destroying the research**.

---

## Long-context research — nominal capacity is not usable attention

Primary source:

- Liu et al., *Lost in the Middle: How Language Models Use Long Contexts*: https://arxiv.org/abs/2307.03172

The paper shows that long-context models can perform differently depending on where relevant information appears; relevant material in the middle of long inputs can be used less reliably than material near the ends. The precise effect varies by model/task, but the durable lesson is that “fits in the context window” is weaker than “will be used reliably.”

### What this suggests here

- track effective behavior under context pressure rather than only maximum supported tokens;
- place high-priority invariants in concise, salient structures rather than burying them in large manuals;
- test rules with the **normal full instruction stack**, because isolated-rule success can hide interference;
- include a high-context pressure variant in adherence regression tests.

---

## BMAD Method — right-sized process and durable handoff artifacts

Repository: https://github.com/bmad-code-org/BMAD-METHOD

Reviewed README: https://github.com/bmad-code-org/BMAD-METHOD/blob/main/README.md

BMAD's current top-level framing emphasizes right-sizing the process to the work: small changes can go directly to build, while complex initiatives get deeper planning. It also emphasizes explicit durable context passed from planning to implementation rather than repeatedly reconstructing decisions in chat.

### Useful insight for this repo

- process depth should be workload-dependent;
- durable artifacts can prevent repeated re-explanation;
- decision trees are useful when they choose **how much process/context is warranted**, not when they impose ceremony on every task.

### What not to copy

Agentic Engineering is intentionally narrower than BMAD. It should not absorb product planning, backlog methodology, architecture process, or a full software-delivery lifecycle. BMAD is evidence for **adaptive depth**, not a template for this repository's scope.

---

## Superpowers — skill discovery, pressure testing, and documentation TDD

Repository: https://github.com/obra/superpowers

Reviewed:

- https://github.com/obra/superpowers/blob/main/README.md
- https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md

Superpowers is organized as composable skills plus bootstrap instructions that cause agents to consider those skills. The most relevant material is its `writing-skills` guidance, which treats process documentation similarly to test-driven development:

- establish a behaviorally failing baseline;
- add the smallest skill/rule intended to address it;
- rerun pressure scenarios;
- refine against concrete rationalizations/failures;
- automate mechanical constraints instead of documenting them as judgment rules.

It also makes a useful discovery distinction: skill metadata should primarily answer **when to load the skill**, rather than duplicating the procedure. Their reported reason is behavioral: a description that summarized the workflow could become a shortcut the agent followed instead of loading the actual skill.

The skill authoring guide is also aggressively sensitive to token costs for frequently loaded material and recommends moving heavy reference information out of the main skill body.

### What this suggests here

Adopt:

- behavioral RED/GREEN style evaluation for new instructions;
- pressure scenarios, not only comprehension questions;
- minimal discovery metadata that triggers the right deeper material;
- separation of heavy reference material from frequently loaded skill bodies;
- mechanical enforcement for mechanical constraints.

Qualify:

- Superpowers uses strong mandatory workflow policies (for example its development/TDD process). Agentic Engineering should not inherit these as universal engineering rules because its scope is execution efficiency with the user's task and quality bar held fixed.
- its concrete word-count targets are useful design heuristics inside that project, not universal thresholds.

---

## Instruction interaction is a first-class failure mode

A key conclusion from combining the sources above with this repository's observed routing failure is that an agent can “follow” individual rules yet still behave incorrectly when rules interact.

Example:

- use cheaper bounded workers for independent work;
- avoid unnecessary delegation;
- prefer local execution;
- reduce coordination overhead.

Each rule is plausible. A lightweight model can synthesize the stack into “do everything myself,” especially under context pressure. That is not necessarily failure to read a specific sentence; it is an **integration bug in the instruction set**.

Therefore instruction evaluation should include:

1. rule alone;
2. rule inside the real complete stack;
3. removal/ablation;
4. realistic task context;
5. high context pressure;
6. thinner model tier where relevant.

---

## Context tax and recovery cost

Two useful accounting ideas emerged from this research.

### Context tax

A lower-bound inventory of recurring controllable context can include:

- global/repository instruction files;
- unscoped rules;
- skill discovery metadata;
- tool/MCP names, descriptions, and schemas depending on harness loading behavior;
- persistent memory/context;
- injected templates or output styles.

The exact runtime tax is harness-specific, so file byte counts are only a proxy. Prefer native context inspection where available.

### Instruction recovery cost

A “cheap” model that ignores instructions may be expensive after recovery:

```text
total effective cost =
  initial run
  + duplicated work
  + retries
  + corrective human turns
  + stronger-model recovery
  + discarded worker work
```

Therefore model routing should target the cheapest model that is sufficiently capable **and sufficiently reliable at the control policy for this workload**. Worker capability and orchestrator instruction reliability are separate selection problems.

---

## Candidate experimental protocol

For a representative task and fixed model/settings where possible:

1. baseline platform defaults;
2. add concise task outcome/acceptance only;
3. add minimal global operating invariants;
4. add optional skill/procedure;
5. add/remove one instruction group at a time when the decision remains unclear.

Record:

- substantive acceptance pass/fail;
- policy/adherence observations from the execution trace;
- human corrections;
- total and fresh input tokens where exposed;
- cached input tokens where exposed;
- output/reasoning tokens where exposed;
- model turns and tool calls;
- wall time;
- retries/rework;
- resolved model/tier for workers where visible.

Run pressure variants with increasing task/context load. Do not claim token/cost savings unless the outcome is non-inferior.

Useful ablation question:

> If this instruction group disappears, what observable behavior or outcome gets worse?

If nothing changes across representative runs, the instruction has not demonstrated a right to permanent residency. It may still belong in a scoped skill/reference.

---

## Current design decisions for Agentic Engineering

Based on the research above and this repository's own live failures:

1. Keep a **small agent operating corpus** for normal work.
2. Keep research/provenance in a separate **`references/` archive** that normal agents should not crawl.
3. Treat instruction placement as a cost hierarchy: deterministic enforcement → always-loaded invariant → path-scoped rule → on-demand skill → retrievable reference.
4. Treat instructions as behavior-affecting code: baseline, regression scenario, pressure test, ablation when useful.
5. Measure the real stack, not a rule in isolation.
6. Escalate repeated non-adherence to enforcement or a more capable orchestrator rather than adding unlimited prose.
7. Preserve research depth and exceptions instead of deleting them in the name of concision.
8. Keep framework-specific guidance in references/adapters unless it changes a general operational decision.

These decisions should be revised when measured behavior contradicts them.
