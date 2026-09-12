# Prompts, AGENTS.md, and skills: benchmark them separately

## Do not turn instructions into folklore

A longer prompt is not automatically better. A global rule is not free. A skill that is always loaded is no longer progressive disclosure.

Treat every persistent instruction as recurring model input whose value must exceed its context and behavioral cost.

## Responsibility split

### Task prompt

Contains what changes for this run:

- desired outcome
- success criteria
- task-specific constraints
- relevant starting point

Keep it outcome-first. Avoid spelling out deterministic micro-steps the agent/toolchain can choose itself unless the path is part of the requirement.

### Global `~/.codex/AGENTS.md`

Contains only cross-repository operating invariants that should affect nearly every task.

Examples:

- prefer deterministic tools for exact operations
- keep shell output concise and retain full logs on disk
- avoid subagents unless measured benefit is plausible
- do not repeat passing broad validation without invalidation

Keep this deliberately short. See `templates/global-AGENTS-efficient.md`.

### Repository `AGENTS.md`

Contains repo-specific facts needed frequently: canonical build/test commands, local conventions, constraints. This public repository does not prescribe those details.

Codex discovers global and nested repository instruction files and builds the chain once per run/session. Nested overrides should be close to the code they govern.

### Skills

Use a skill for an optional reusable workflow that is relevant only to a subset of tasks. Codex currently uses progressive disclosure: skill metadata first, full `SKILL.md` only if selected, references/scripts only when needed.

A skill therefore usually beats adding a large optional procedure permanently to `AGENTS.md`.

## A/B benchmark dimensions

For a representative task, compare these independently rather than changing everything at once:

1. default Codex instructions only
2. + concise outcome-first task prompt
3. + minimal global `AGENTS.md`
4. + optional efficiency skill
5. + tuned tool/config layer

Hold constant:

- repo commit
- model
- reasoning effort
- task text (except the prompt variant being tested)
- acceptance tests
- local machine state as far as practical

Run each stochastic variant multiple times and report median plus spread.

## Instruction efficiency metrics

Record:

- acceptance pass/fail
- human corrections needed
- total input tokens
- cached input tokens
- output tokens
- reasoning output tokens
- model turns
- clarification/approval pauses
- tool calls
- wall time

Useful derived measures:

```text
fresh_input = input - cached_input
cache_ratio = cached_input / input
input_saving = 1 - tuned_input / baseline_input
output_saving = 1 - tuned_output / baseline_output
wall_saving = 1 - tuned_wall / baseline_wall
```

Only report savings when quality is non-inferior.

## Failure modes to look for

A supposedly helpful instruction can make things worse by:

- adding tokens to every turn/session
- conflicting with another instruction
- causing unnecessary planning or confirmations
- triggering broad testing on trivial changes
- triggering subagents by default
- forcing the model to narrate work instead of doing it
- narrowing the model into a slower procedure when a simpler one exists

GPT-6 Astra is documented as especially sensitive to skills and `AGENTS.md`; audit conflicting instruction sources rather than stacking more instructions to compensate.

## References

- GPT-6 Astra prompting/model guidance: https://developers.openai.com/api/docs/guides/latest-model
- Codex AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Codex customization/skills: https://learn.chatgpt.com/docs/customization/overview
