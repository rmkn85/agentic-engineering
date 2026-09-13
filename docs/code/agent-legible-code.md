# Agent-legible code: make future work cheap

Source code is persistent context for future agents. A design that is correct today can still be expensive tomorrow if a routine change requires loading many unrelated files, reconstructing hidden state, following deep indirection, or rewriting brittle tests.

The optimization target here is therefore:

> **same required behavior + same quality bar → less code/context to localize, understand, change, validate, and debug**

This is not a universal product-architecture prescription. Apply these rules only where they reduce future reasoning and change cost without weakening the requested design or runtime constraints.

## Core principle: optimize semantic locality

Prefer structures that let an agent answer a local question with local evidence.

A good unit of code should make its contract, dependencies, state changes, errors, and tests discoverable without reconstructing a large portion of the repository.

The strongest recurring mechanisms are:

1. **small reasoning surfaces** — keep functions/modules cohesive and control flow simple enough to understand as a unit;
2. **small change surfaces** — hide volatile decisions so one conceptual change touches few modules;
3. **explicit boundaries** — types, schemas, contracts, dependency direction, errors, and resource limits should be visible rather than implicit;
4. **independent verification** — tests and static checks should catch defects without copying the implementation's logic;
5. **mechanical consistency** — formatting, dependency rules, complexity limits, and other exact constraints should be enforced by tools instead of prose.

## Locality beats fragmentation

Small functions and files are useful only while they reduce the amount of state that must be held in mind.

Prefer:

- one cohesive responsibility per function/module;
- helpers when they name a real concept or isolate a meaningful decision;
- co-location of code that normally changes together;
- interfaces that reveal the information needed to use a component without opening its implementation.

Avoid splitting code until a simple operation requires traversing a chain of tiny files or functions. A 10-line function whose meaning depends on six wrappers, factories, decorators, and service locators can be harder for an agent than a direct 40-line function.

**Decision rule:** minimize the smallest sufficient context set for representative changes, not line count in isolation.

## Hide volatility, not everything

Modularity pays when a boundary contains a decision likely to change independently of its callers.

Good candidates for isolation include:

- external service or storage details;
- serialization/protocol formats;
- platform/runtime differences;
- algorithms likely to be swapped;
- policy/configuration that changes independently of execution mechanics.

Do **not** introduce an interface, base class, factory, adapter, or dependency-injection layer merely because abstraction is fashionable. Speculative abstraction increases symbol count, navigation hops, and possible implementations the agent must consider.

Use the simplest concrete implementation until a real change boundary or test seam earns an abstraction.

## Keep dependency direction obvious

Prefer an acyclic dependency graph with a small number of permitted directions.

Useful properties:

- modules expose a narrow public surface;
- lower-level code does not reach upward into orchestration/UI layers;
- cross-cutting dependencies enter through explicit boundaries rather than globals or hidden registries;
- circular dependencies are rejected mechanically where tooling permits;
- imports/dependencies are conventional and statically discoverable.

A dependency graph an indexer can reconstruct cheaply is also easier for an agent to retrieve selectively.

## Make control flow analyzable

The safety-critical tradition is useful here because analyzability and agent legibility often align.

Prefer:

- direct structured control flow;
- guard clauses when they reduce nesting;
- bounded retries, queues, pagination, recursion depth, and loops when the workload admits a useful bound;
- explicit timeout/cancellation behavior for external or concurrent operations;
- functions whose branching complexity remains easy to enumerate and test.

Use cyclomatic complexity, nesting depth, or function size as **signals**, not universal aesthetic limits. When a component becomes expensive to explain or test, split the underlying decisions rather than mechanically extracting arbitrary blocks.

## Make state and data flow explicit

Prefer:

- the smallest practical variable/state scope;
- immutable values or explicit state transitions where practical;
- typed data at module boundaries;
- validation/parsing at trust boundaries rather than repeated defensive guesses downstream;
- explicit function inputs and outputs over ambient globals/thread-local/service-locator state;
- one stable name for one domain concept.

Hidden mutation is expensive because every reader must search for all possible writers before trusting a value.

## Keep side effects near boundaries

Where the domain permits it, separate deterministic transformation/decision logic from I/O, clock, randomness, network, filesystem, process, database, and UI effects.

This is not a mandate for functional programming. It is a locality mechanism: deterministic cores are cheaper to test, replay, cache, inspect, and refactor; effectful edges make environmental assumptions explicit.

## Make errors impossible to overlook

Errors should be visible in control flow and observable in diagnostics.

Prefer:

- explicit error/result propagation appropriate to the language;
- checked return/status values where failures are meaningful;
- actionable error context at boundaries;
- structured logs/events rather than opaque prose where tooling will consume them;
- assertions/invariants for states that should be impossible, with appropriate recovery/termination semantics for the system.

Avoid silent catches, ignored failed results, default-success fallbacks, or logging an error and continuing as if success occurred unless that behavior is explicitly the contract.

## Names are retrieval infrastructure

Agents use symbol search, repository maps, ASTs, LSPs, and text retrieval. Names therefore affect both comprehension and retrieval quality.

Prefer names that:

- state the domain concept and operation precisely;
- use the repository's existing vocabulary consistently;
- distinguish similar concepts instead of overloading `data`, `manager`, `handler`, `util`, or `helper`;
- remain stable when the implementation changes but the concept does not.

Avoid gratuitously clever abbreviations and multiple aliases for the same concept.

## Comments should preserve information the code cannot

Self-explanatory code does not mean comment-free code.

Use comments/docstrings for:

- **why** a non-obvious choice exists;
- invariants and pre/postconditions not expressible in types/tests;
- external constraints, protocols, standards, compatibility behavior, or intentional oddities;
- safety/performance assumptions whose removal would be dangerous;
- rationale for deliberately ignored errors or exceptional constructs.

Do not narrate obvious syntax or maintain a second, manually synchronized implementation description in prose. If a comment must explain several blocks of `how`, simplify or extract the code first.

## Use conventional machine-friendly formatting

Prefer the ecosystem's standard autoformatter and stable syntax.

Useful properties include:

- deterministic formatting;
- one meaningful statement/action per syntactic unit;
- diffs that isolate semantic edits instead of reflowing unrelated code;
- limited deeply nested/chained expressions when intermediate names clarify concepts;
- generated code isolated from hand-maintained source where possible.

Do **not** optimize formatting for guessed tokenizer tricks. There is currently no strong basis for custom minified or token-gamed source layouts outperforming conventional well-represented code, and they can damage tool support, diffs, and training-distribution familiarity.

## Tests are executable contracts, not duplicate implementations

A test suite should make future changes safer **and cheaper**.

Prefer tests that:

- state one behavior/invariant clearly;
- exercise public or stable module contracts rather than private implementation details;
- would actually fail when the behavior is broken;
- survive behavior-preserving refactors;
- keep expected results independent from the algorithm under test;
- use property/contract/boundary tests when they express an invariant more directly than many examples;
- keep focused unit tests for diagnostic precision and a deliberately small set of integration/end-to-end tests for real boundaries;
- add characterization tests before risky refactors when current behavior is insufficiently protected.

Avoid tests that recreate the production algorithm to compute the expected answer, assert incidental call ordering, snapshot huge unstable structures without semantic reason, or mock every internal collaborator. Those tests increase refactoring cost while providing weak independent evidence.

## Design for diagnosis

A cheap-to-debug system exposes enough state to locate a failure without replaying the whole program mentally.

Prefer:

- structured diagnostics with stable event/error names;
- request/job/correlation identifiers across boundaries;
- explicit state transitions;
- deterministic reproduction fixtures where practical;
- local health/invariant checks;
- retained detailed evidence with concise top-level failure summaries.

Debuggability is part of agent legibility: a failure that names the violated contract and relevant identifiers can save a large exploratory model loop.

## Keep changes conceptually small

When practical, separate behavior-preserving restructuring from behavior changes.

A self-contained change should make one coherent conceptual move and include the tests needed to prove it. Small changes reduce the number of competing hypotheses an agent/reviewer must consider and make rollback/bisection cheaper.

This is conceptual smallness, not a hard line-count quota.

## Enforce invariants mechanically

Do not spend model context reminding every agent about constraints a tool can verify.

Depending on language/project, useful enforcement may include:

- formatter and import ordering;
- compiler/type-checker warnings as errors;
- static analysis/security rules;
- dependency direction and cycle checks;
- dead/unused code detection;
- selected complexity/function/module-size thresholds;
- schema/API compatibility checks;
- test and coverage requirements appropriate to risk;
- generated-source freshness checks.

Prefer a small number of high-value, low-noise rules. A noisy rule that agents routinely suppress is not a useful guardrail.

## Common agent-hostile structures

| Pattern | Why it increases future agent cost |
| --- | --- |
| Mega-function / mega-module | Large context must be loaded for small changes; branching and state interact |
| Micro-abstraction maze | Too many navigation hops and possible implementations for one concept |
| Generic `utils` dumping ground | Poor ownership/searchability; unrelated dependencies accumulate |
| Hidden global/service-locator state | Reader must search globally to learn dependencies and mutation |
| Reflection/metaprogramming for ordinary control flow | Static tools and repository maps cannot cheaply expose real behavior |
| Cyclic dependencies | Local edits require global reasoning and coordinated changes |
| Copy-pasted near-duplicates | Fixes require discovering all variants; agents may extend the wrong copy |
| Clever compressed expressions | Fewer lines but more semantic work per line and worse diffs/diagnostics |
| Comments that narrate implementation | Duplicate source of truth that drifts |
| Tests mirroring internals | Refactors break tests even when behavior is preserved |
| Broad mocks/snapshots | High maintenance and weak localization when they fail |
| Unbounded retries/queues/work | Runtime and debugging cost becomes unpredictable |

## Do not cargo-cult SOLID

Several SOLID ideas align with agent legibility, especially cohesion, dependency direction, substitutable contracts, and isolating volatility. But applying them mechanically can produce an interface/class explosion.

For agentic efficiency, the more useful question is:

> **Does this boundary let the next change be understood and verified with less repository context?**

If an abstraction increases indirection without reducing change ripple, uncertainty, or test cost, it is probably negative leverage.

## Measure the effect on future work

Do not claim that smaller files or lower complexity save model tokens merely because they sound plausible.

For representative changes, useful observations include:

- files/symbols opened before the correct edit is localized;
- unique source bytes/tokens loaded into model context;
- dependency hops followed;
- number of files changed for one conceptual change (**edit radius**);
- unrelated files touched because of coupling;
- model turns/tool calls to obtain a passing change;
- validation wall time and breadth;
- regressions/retries/human corrections;
- whether behavior-preserving refactors require test rewrites.

See [`../../experiments/agent-legibility.md`](../../experiments/agent-legibility.md) for a comparison protocol.

## Historical/evidence archive

The research behind these rules — punched-card/batch constraints, structured programming, Parnas information hiding, JPL/NASA safety-critical rules, real-time restrictions, flight-software architecture, modern testing practice, repository-level LLM retrieval, and agent-first repository experience — is preserved in [`../../references/agent-legible-code-history-2026-09.md`](../../references/agent-legible-code-history-2026-09.md).
