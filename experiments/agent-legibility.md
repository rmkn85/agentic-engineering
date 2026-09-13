# Agent-legibility experiment: does code structure reduce future agent work?

Status: comparison protocol. This does **not** claim that any specific style rule saves tokens by itself.

Use this when a code-structure change is justified partly by making future agent work cheaper: smaller functions/modules, different boundaries, reduced indirection, dependency cleanup, behavioral-test refactoring, explicit state/contracts, or architecture enforcement.

## Governing question

> For the same maintenance task and acceptance bar, does the candidate structure reduce the work needed to localize, understand, modify, validate, and debug the code?

Do not benchmark aesthetics. Start from a real recurring change/debug task or a representative fixture derived from one.

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

## Workloads

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

Treat these as explanatory proxies, not the objective.

## Derived values

Useful workload-specific measures include:

```text
localization_context_ratio = candidate_unique_source_context / baseline_unique_source_context
edit_radius_ratio          = candidate_changed_files / baseline_changed_files
turn_ratio                 = candidate_model_turns / baseline_model_turns
validation_ratio           = candidate_validation_wall / baseline_validation_wall
recovery_ratio             = candidate_retries_or_corrections / baseline_retries_or_corrections
```

Do not collapse them into a universal “agent legibility score.” Different systems value localization, wall time, risk, and runtime performance differently.

## Important counter-tests

A proposed cleanup can make one task easy by making another harder. Look explicitly for:

- **micro-fragmentation:** fewer lines per function but more navigation hops;
- **abstraction inflation:** more interfaces/symbols but no smaller change radius;
- **over-deduplication:** unrelated concepts become coupled through a generic helper;
- **test brittleness migration:** production code becomes cleaner but tests now depend on internals;
- **runtime regression:** agent-friendly structure violates latency/memory/hot-path needs;
- **tooling opacity:** dynamic framework machinery hides dependencies from static maps/search;
- **semantic compression:** shorter code becomes denser and harder to diagnose.

## Interpreting results

Prefer the candidate when:

1. acceptance is non-inferior;
2. the target maintenance tasks require less localization/reasoning/recovery;
3. any added abstraction/runtime cost is justified;
4. the improvement survives more than one cherry-picked task.

If static metrics improve but agent work does not, do not publish the static metric as a proven agent-efficiency rule.

If a change is an obvious mechanical correctness win (for example eliminating a real dependency cycle or swallowing error), fix it without manufacturing an expensive benchmark. Use the protocol when the agent-efficiency tradeoff itself is uncertain or consequential.

## Related guidance

- operational rules: [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md)
- research/provenance: [`../references/agent-legible-code-history-2026-09.md`](../references/agent-legible-code-history-2026-09.md)
- general resource metrics: [`../docs/measurement/metrics.md`](../docs/measurement/metrics.md)
