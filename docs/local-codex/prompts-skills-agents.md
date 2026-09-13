# Prompts, AGENTS.md, rules, and skills

The first question is not “how should this instruction be worded?” It is **“why should this information be in the model's working context at this point?”**

A longer prompt is not automatically better. A shorter prompt is not automatically better. A global rule is recurring model input, and a skill that is always loaded is no longer progressive disclosure.

For the compact cross-framework decision rule, start with the [agent operating corpus](../agent-corpus/README.md).

## Choose placement before prose

Use the least-resident mechanism that reliably produces the required behavior.

| Information / constraint | Preferred placement |
| --- | --- |
| Exact/mechanical constraint | Script, config, hook, linter, test, policy gate |
| Cross-repository invariant needed almost every run | Minimal global instructions |
| Repository-wide fact needed frequently | Repository `AGENTS.md` / equivalent |
| File/directory/language-specific rule | Nested/path-scoped instructions when supported |
| Reusable procedure needed only for some tasks | Skill / invoked workflow |
| Large examples, rationale, API docs, research | Supporting/reference file loaded on demand |
| High-volume temporary research whose details are not needed upstream | Separate worker/context with compact evidence return |

Moving a paragraph into an imported file does **not** save context if the harness eagerly imports that file. Verify loading semantics rather than inferring them from directory structure.

## Responsibility split

### Task prompt

Contains what changes for this run:

- desired outcome;
- success criteria;
- task-specific constraints;
- relevant starting point.

Keep it outcome-first. Do not prescribe deterministic micro-steps unless the path itself is part of the requirement.

### Global instructions

Contain only cross-repository operating invariants that should affect nearly every task.

Examples:

- preserve requested outcome/quality while optimizing execution;
- prefer exact tools for exact work;
- keep noisy output out of model context;
- reuse valid work until invalidated;
- choose tool / bounded worker / orchestrator before a substantial batch.

Keep this deliberately small. See [`templates/global-AGENTS-efficient.md`](../../templates/global-AGENTS-efficient.md).

### Repository `AGENTS.md`

Contains repo-specific invariants and a **map** to deeper knowledge, not the full repository handbook. Canonical build/test commands and truly cross-cutting local constraints belong here; large procedures and research do not.

Nested instruction files can be useful when the harness supports scope inheritance. Keep the rule close to the files it governs rather than making every task pay for it.

### Skills / on-demand procedures

Use a skill for a reusable workflow relevant to only a subset of tasks. Prefer short discovery metadata that answers **when this skill is needed** and load the full procedure only when selected.

Keep heavy examples/reference material in supporting files when the harness can retrieve them on demand. Once a skill body loads, many harnesses retain it for some or all of the session; progressive disclosure delays context cost but does not make loaded content free.

### Research/reference archive

Reference material should preserve depth without becoming runtime instructions. In this repository, external research and framework comparisons live under [`references/`](../../references/README.md), which ordinary execution agents should not crawl.

## Instructions are behavior-changing code

A new rule should address a concrete failure, uncertainty, or expensive repeated correction. Do not add a persistent instruction merely because the sentence sounds wise.

Use a lightweight RED → GREEN → REFACTOR loop:

1. **RED:** capture the current failure or baseline behavior;
2. **GREEN:** add the smallest intervention expected to fix it;
3. **REFACTOR:** remove redundancy, scope the rule, or replace it with deterministic enforcement while keeping behavior correct.

For discipline/enforcement rules, use pressure scenarios that create realistic competing incentives. A comprehension question proves only that the model can restate the rule.

See [`experiments/instruction-context-adherence.md`](../../experiments/instruction-context-adherence.md).

## Benchmark dimensions

For a representative task, change one meaningful layer at a time when the tradeoff is uncertain:

1. platform defaults;
2. + concise outcome-first task prompt;
3. + minimal global/repository instructions;
4. + scoped/on-demand efficiency skill;
5. + tuned tool/config/enforcement layer.

For a particular instruction group, also consider **ablation**: compare the normal stack with that group removed or demoted to on-demand context. Do not exhaustively test combinations unless interaction is the question.

Hold constant where practical:

- repo commit;
- model and reasoning effort;
- task text except the variant under test;
- acceptance tests;
- machine/runtime state.

Run stochastic variants multiple times when variance could change the decision. Report median/spread rather than elevating one run into a law.

## Context-pressure testing

An instruction can work alone and fail in the real stack. Test important rules at three useful levels:

- **low:** small task + core rule — can the model understand it?
- **representative:** normal instructions/tools/files — does it work in production-like conditions?
- **high:** legitimately larger working set with competing relevant rules — does adherence collapse before the nominal context limit?

Do not pad context with irrelevant junk. The pressure case should resemble real work.

## Instruction efficiency metrics

Record only what the harness can support reliably:

- substantive acceptance pass/fail;
- human corrections/retries;
- total input tokens;
- cached input tokens;
- output/reasoning tokens;
- model turns;
- tool/model calls;
- wall time;
- duplicate reads or revalidation;
- resolved worker model/tier where visible.

Useful derived values:

```text
fresh_input = input - cached_input
cache_ratio = cached_input / input
input_saving = 1 - tuned_input / baseline_input
output_saving = 1 - tuned_output / baseline_output
wall_saving = 1 - tuned_wall / baseline_wall
```

Only report savings when outcome/quality is non-inferior.

For the file-based lower bound of instruction footprint:

```bash
python tools/instruction-footprint.py .
```

The script's token estimate is a comparison proxy, not actual tokenizer/runtime usage. Native harness context inspection is preferable because system prompts, memory, skill metadata, and tool/MCP schemas may be invisible on disk.

## Common anti-patterns and observable signals

| Anti-pattern | Signal |
| --- | --- |
| Instruction scar tissue | Every failure adds another global paragraph; old rules are never removed |
| Globalizing local knowledge | A rule matters only in one subtree/workflow but loads everywhere |
| Description-as-procedure | Discovery metadata becomes a shortcut and the agent skips the actual skill |
| Prompt folklore | Changes are justified by “models like this” without a failing behavior or comparison |
| Compliance theater | Agent repeats the rule but execution trace violates it |
| Rule interaction bug | Each rule is plausible alone; complete stack produces the wrong policy |
| Context laundering | A large document is moved to another file but still force-loaded/imported |
| Cached-context fallacy | Cached input is treated as if it no longer consumes model attention/context |
| Mechanical prose | The model is asked to remember something a script/test could enforce exactly |
| Over-compression | Summaries discard awkward exceptions or decision-bearing detail |
| Context replay | Orchestrator rereads all worker inputs, erasing isolation/delegation benefits |

## When a thin agent keeps ignoring the rules

Do not immediately make the instruction longer.

Escalate in this order:

1. confirm the instruction actually loaded;
2. remove conflicting/duplicate guidance;
3. sharpen the decision boundary or trigger;
4. move the rule to a better scoped/on-demand mechanism;
5. test the behavior with the real stack;
6. enforce mechanically where feasible;
7. use a more capable orchestrator if the workload exceeds the thinner model's reliable control capacity.

The cheapest model call is not the cheapest workflow if non-adherence creates retries, discarded work, human corrections, or stronger-model recovery.

## Evidence and external research

The detailed external research behind these choices is intentionally not duplicated here. See [`references/context-and-instruction-engineering-2026-09.md`](../../references/context-and-instruction-engineering-2026-09.md) only when improving/auditing this methodology.
