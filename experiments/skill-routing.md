# Skill granularity experiment: does focus beat routing overhead?

Status: comparison protocol.

Use this when deciding whether one broad skill should be split into several focused skills.

## Governing question

> Does routing to a smaller relevant skill reduce total context/reasoning and improve adherence enough to justify discovery metadata, route selection, and misrouting risk?

## Compare

For the same mixed task set and fixed model/settings where practical:

1. **monolithic** — one broad skill containing all workflows;
2. **focused** — short trigger-only descriptions plus one selected specialized skill;
3. optionally **no custom skill** — platform/default behavior when that is a meaningful baseline.

For agent-legible coding, include tasks from each structural class:

- create new module/boundary;
- add a new unit inside an existing module;
- change/refactor one existing unit;
- refactor a whole module/boundary;
- at least one ambiguous/escalation case.

## Measure

- correct route without extra repository exploration;
- discovery/always-visible skill metadata footprint;
- loaded skill-body tokens/context;
- number of skills loaded per task;
- wrong-route/re-route count;
- instruction adherence on the task-specific decisions;
- substantive task acceptance;
- model turns/tool calls/wall time;
- human correction/recovery work.

## Interpretation

Focused skills are a win when:

- route choice is cheap and usually unambiguous;
- only one body normally loads;
- irrelevant guidance materially disappears from the working context;
- adherence/quality is non-inferior or better;
- rerouting is rare and cheap.

Keep or recombine skills when:

- task categories overlap so heavily that agents repeatedly load several skills;
- descriptions need long workflow summaries to distinguish them;
- routing requires reading the repository first;
- specialized bodies mostly duplicate one another;
- misrouting/recovery erases the context saving.

Do not optimize for the largest possible skill catalog. The desired unit is the **smallest stable set of workflows whose triggers are cheaper than the context they avoid**.
