# Agent-legibility experiment: does code structure reduce future agent work?

Status: comparison protocol. This does **not** claim that any specific style rule saves tokens by itself.

Use this when a code-structure change is justified partly by making future agent work cheaper: smaller functions/modules, different boundaries, reduced indirection, dependency cleanup, behavioral-test refactoring, explicit state/contracts, or architecture enforcement.

## Governing question

> For the same maintenance task and acceptance bar, does the candidate structure reduce the work needed to localize, mentally model, modify, validate, and debug the code?

Do not benchmark aesthetics. Start from a real recurring change/debug task or a representative fixture derived from one.

## Primary test: weak-reader bounded mental model

Static metrics are only proxies. The most direct agent-legibility test is whether a weaker, reasoning-limited, context-limited coding model can build a useful operational model of the unit without broad repository expansion.

### Setup

Choose a reader model materially cheaper/weaker than the normal strong orchestrator but still capable of basic code work.

Give it only the source/context that the design claims should be sufficient:

- target function/module;
- immediate public contract/types;
- explicitly declared dependencies needed to interpret the unit;
- no unrelated repository summary or hidden answer key.

Do not reward the candidate structure by manually supplying extra explanatory prose that the baseline does not receive.

### Semantic questions

Ask a small deterministic set appropriate to the language/unit, for example:

- For representative input A, which branch/path executes and what result is returned?
- What changes for edge input B?
- Which values/statements influence result X?
- Which external functions/services can be reached?
- What state is read or mutated?
- What side effects occur, and in what order where order is contractually relevant?
- What errors can escape or be converted/suppressed?
- Is this retry/loop/work queue visibly bounded, and by what?
- Which invariant/contract would fail after a specified mutation?
- Which immediate dependency must change to alter behavior Y?

Use tests, static/compiler analysis, or hand-reviewed fixtures for ground truth. The goal is not to elicit a long explanation; constrain answers enough to grade behavior accurately.

### Record

- semantic-answer accuracy;
- false confidence versus explicit uncertainty;
- number of additional files/context items requested or opened;
- unique additional source bytes/tokens consumed;
- searches/index/LSP calls;
- model turns/retries;
- reasoning effort where the harness exposes it;
- wall time.

A candidate is stronger when the weak reader remains at least as accurate while requiring **less context expansion and reasoning**.

### Pressure variants

When useful, repeat with:

1. **local only** — target unit + declared contracts;
2. **normal maintenance context** — realistic nearby source/tests;
3. **fresh context** — no prior conversation/repository familiarity.

The goal is not to prove all possible behavior. It is to test whether ordinary behavior fits inside a bounded reliable mental model.

## Hold constant

Where practical, keep constant:

- required behavior and acceptance criteria;
- repository functionality/data fixtures;
- model and reasoning effort;
- agent instructions/tools;
- machine/runtime state;
- task prompt;
- validation suite.

The independent variable should be the code structure under investigation.

## Useful variants

Compare the smallest set needed to resolve the decision. Examples:

- baseline high-complexity function vs decomposition along real semantic decisions;
- abstraction maze vs one direct stable implementation;
- hidden global/service-locator dependency vs explicit dependency;
- mixed I/O + decision logic vs deterministic core + effectful boundary;
- duplicated variants vs one cohesive shared component;
- cyclic package graph vs directional dependency graph;
- implementation-coupled tests vs behavior/contract tests;
- convention documented in prose vs equivalent structural rule enforced by linter/test.

Do not combine all of these in one “clean architecture” rewrite and then attribute savings to a specific mechanism.

## Maintenance workloads

The mental-model test can be run alone, but a claim about maintenance efficiency should also include real change/debug work.

Include at least two task shapes when the claim is meant to generalize:

### Local change

Change one behavior inside the component while preserving its public contract.

Tests whether the agent can localize and edit without loading unrelated context.

### Cross-boundary change

Change a contract or external integration that legitimately affects several components.

Tests whether abstraction/boundaries reduce or merely hide the true change surface.

Useful optional workloads:

- diagnose a seeded bug from an error/log;
- behavior-preserving refactor;
- add one new implementation behind an existing boundary;
- remove/rename a domain concept;
- resume the task in a fresh agent context.

## Outcome gate

A variant qualifies only if it preserves the same required behavior and quality.

Check as appropriate:

- deterministic tests/static checks;
- public behavior/contract;
- performance/resource requirements;
- integration/end-to-end acceptance;
- absence of unintended diff/behavior;
- human or independent-agent defect review for changes not fully mechanically testable.

Fewer tokens with a missed regression is not an efficiency win.

## Agent-work metrics

Record what the harness can expose reliably.

### Localization

- files opened/read before the first correct target is identified;
- unique source bytes/tokens loaded;
- search/index/LSP calls;
- dependency/symbol hops followed;
- wrong candidate files/implementations inspected.

### Mental model

- weak-reader semantic accuracy;
- context expansion required to answer correctly;
- semantic questions answered incorrectly despite confidence;
- number of important behaviors/dependencies missed;
- turns/reasoning required before the model can give a stable correct prediction.

### Modification

- model turns before first passing edit;
- files/modules changed (**edit radius**);
- unrelated files changed because of coupling;
- generated/repeated code volume;
- test files changed for behavior-preserving refactors.

### Validation/debugging

- tests/checks selected and executed;
- validation wall time;
- failure-log context consumed;
- retries/reverts;
- number of distinct hypotheses investigated before root cause/fix;
- human corrections/escalations.

### Static proxies

When relevant, record before/after:

- cyclomatic/cognitive complexity;
- dependency cycles and fan-out;
- public surface/symbol count;
- function/module size distribution;
- global mutable state;
- duplicate-code indicators;
- dynamically hidden edges (reflection/registries/service locator) when tooling can identify them.

Treat these as explanatory proxies, not the objective. Research on code understandability does not support treating any one of them as a sufficiently accurate comprehension metric.

## Derived values

Useful workload-specific measures include:

```text
semantic_accuracy_delta     = candidate_weak_reader_accuracy - baseline_weak_reader_accuracy
context_expansion_ratio     = candidate_extra_context / baseline_extra_context
localization_context_ratio  = candidate_unique_source_context / baseline_unique_source_context
edit_radius_ratio           = candidate_changed_files / baseline_changed_files
turn_ratio                  = candidate_model_turns / baseline_model_turns
validation_ratio            = candidate_validation_wall / baseline_validation_wall
recovery_ratio              = candidate_retries_or_corrections / baseline_retries_or_corrections
```

Do not collapse them into a universal “agent legibility score.” Different systems value semantic reliability, localization, wall time, risk, and runtime performance differently.

## Important counter-tests

A proposed cleanup can make one task easy by making another harder. Look explicitly for:

- **micro-fragmentation:** fewer lines per function but more navigation hops;
- **abstraction inflation:** more interfaces/symbols but no smaller mental model or change radius;
- **over-deduplication:** unrelated concepts become coupled through a generic helper;
- **test brittleness migration:** production code becomes cleaner but tests now depend on internals;
- **runtime regression:** agent-friendly structure violates latency/memory/hot-path needs;
- **tooling opacity:** dynamic framework machinery hides dependencies from static maps/search and the weak reader;
- **semantic compression:** shorter code becomes denser and harder to predict/diagnose.

## Interpreting results

Prefer the candidate when:

1. acceptance is non-inferior;
2. the weak reader can model representative behavior at least as accurately with no more — preferably less — context/reasoning;
3. target maintenance tasks require less localization/recovery;
4. any added abstraction/runtime cost is justified;
5. the improvement survives more than one cherry-picked task.

If static metrics improve but weak-reader comprehension/maintenance work does not, do not publish the static metric as a proven agent-efficiency rule.

If a change is an obvious mechanical correctness win (for example eliminating a real dependency cycle or swallowed error), fix it without manufacturing an expensive benchmark. Use the protocol when the agent-efficiency tradeoff itself is uncertain or consequential.

## Related guidance

- operational rules: [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md)
- historical research/provenance: [`../references/agent-legible-code-history-2026-09.md`](../references/agent-legible-code-history-2026-09.md)
- LLM semantic-understanding evidence: [`../references/agent-semantic-understanding-2026-09.md`](../references/agent-semantic-understanding-2026-09.md)
- general resource metrics: [`../docs/measurement/metrics.md`](../docs/measurement/metrics.md)
