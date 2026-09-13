# Contributing

Contributions should improve the engineering discipline around software-development agents while preserving the requested task and quality bar.

Prefer concise, evidence-backed mechanisms and decision rules over broad collections of tips. Generalize private/project-specific lessons before publishing them.

## Place knowledge before polishing it

Do not automatically add new guidance to `AGENTS.md`, the global template, or a frequently loaded skill.

Ask where the information belongs:

- mechanical constraint -> script/config/test/hook;
- nearly universal execution invariant -> concise always-loaded guidance;
- path/task-specific rule -> scoped instruction;
- reusable occasional procedure -> skill/on-demand doc;
- external research, rationale, competing ideas, provenance -> `references/`.

For methodology changes, include the problem, mechanism, expected tradeoff, scope, evidence level, and how the claim could be measured or challenged. If the change affects persistent instructions, use or extend the behavioral cases in [`experiments/instruction-context-adherence.md`](experiments/instruction-context-adherence.md) when the tradeoff is material.

Preserve useful research depth in `references/` instead of bloating runtime guidance or deleting the evidence that led to a decision.
