# Agent-legible code research and historical lineage — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

Operational guidance distilled from this research lives in [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md). This file preserves the deeper history, source links, caveats, and rejected cargo-cult interpretations.

## Research question

If a repository is increasingly written, read, refactored, reviewed, and debugged by coding agents, what source-code properties reduce the amount of model context, reasoning, search, validation, and recovery required for future work?

The question is deliberately narrower than “what is good software architecture?” A practice belongs in Agentic Engineering only when it plausibly changes the **execution cost of maintaining the same required software**, and non-obvious claims should be testable.

## Main synthesis

Across several generations of software engineering, the recurring high-value idea is **analyzability**:

- early batch systems punished unnecessary compile/run cycles;
- structured programming made control flow easier to reason about;
- information hiding limited how much of a system must be understood or changed at once;
- safety-critical standards constrained language/runtime features so tools could prove more properties;
- real-time profiles constrained concurrency and resources so timing/state could be analyzed;
- flight-software frameworks used stable layers and explicit interfaces to enable reuse;
- modern testing and code-review practice favors small coherent changes and behavior-level contracts;
- repository-level coding agents perform better when relevant symbols/dependencies can be localized and retrieved without loading the entire repository;
- current agent-first production experience emphasizes mechanically enforced architecture, repository legibility, stable/boring abstractions, and continuous cleanup.

The agent-era translation is:

> **Code should make the smallest sufficient context for the next correct change as small, explicit, and mechanically verifiable as practical.**

This does **not** mean minimizing LOC, maximizing abstraction, or splitting every function/file. Excessive fragmentation can increase retrieval and navigation cost.

---

## 1. Punch cards and batch computing: expensive feedback changes engineering behavior

Sources:

- IBM, *The punched card*: https://www.ibm.com/history/punched-card
- IBM, *What are batch jobs?*: https://www.ibm.com/think/topics/batch-jobs
- IBM, *Time-sharing*: https://www.ibm.com/history/time-sharing
- IBM, *The IBM 650*: https://www.ibm.com/history/650

IBM documents that one punched card commonly represented one source line on an 80-column card, and programs were physical decks. Early jobs were submitted and processed in batches; computers were scarce and expensive, and batch processing existed partly to keep the machine busy rather than idle during interactive human work.

### Durable lesson

When feedback is expensive, engineers have strong incentives to:

- validate inputs/setup before launching a run;
- make jobs deterministic and restartable;
- separate reusable routines from repeated manual setup;
- avoid unnecessary compile/run/debug cycles;
- preserve enough diagnostics to learn from a failed run.

### What **not** to import

Scarce storage/columns historically encouraged terse names and compact source. That is not a useful agent-era lesson. Model context is scarce, but semantic compression through cryptic identifiers can make reasoning harder. Optimize **information density and locality**, not character count.

---

## 2. Structured programming: constrain control flow so state is easier to reconstruct

Primary historical source:

- Edsger W. Dijkstra, *Go To Statement Considered Harmful* (1968), DOI 10.1145/362929.362947: https://ir.cwi.nl/pub/28228

Dijkstra's argument was fundamentally about **program intelligibility**: arbitrary jumps make it difficult to relate the static program text to the dynamic execution state.

### Agent-era translation

An agent debugging or modifying code has the same reconstruction problem. Structured control flow reduces the number of possible execution histories it must consider.

Useful descendants include:

- shallow/obvious branching;
- explicit state transitions;
- limited non-local jumps/exceptions used as ordinary control flow;
- bounded recursion/retries where boundedness matters;
- complexity metrics as warning signals.

This is not a rule that every function must have one return or zero exceptions. Holzmann explicitly notes that an early error return can be simpler than forcing a single exit.

---

## 3. Parnas: modularity is about limiting knowledge and change ripple

Primary source:

- David L. Parnas, *On the Criteria To Be Used in Decomposing Systems into Modules* (1972), Communications of the ACM 15(12): https://doi.org/10.1145/361598.361623

The paper frames modularization as a way to improve flexibility and comprehensibility and shorten development time, and argues that decomposition quality depends on **what decisions modules hide**, not merely splitting a flowchart into steps.

### Agent-era translation

A useful module lets an agent change one volatile decision without opening every caller.

This is more precise than “SOLID” as a blanket prescription:

- hide things likely to change independently;
- expose stable contracts;
- keep dependency information requirements small;
- co-locate things that change together;
- do not create interfaces that merely add hops without isolating volatility.

The relevant metric is **change/context radius**, not the number of classes or interfaces.

---

## 4. Cleanroom: defect prevention and independent correctness arguments

Source:

- CMU Software Engineering Institute, *Cleanroom Software Engineering Reference* (1996): https://www.sei.cmu.edu/library/cleanroom-software-engineering-reference/

Cleanroom combined mathematically based specification/design/correctness verification with statistical usage-based testing, emphasizing defect prevention rather than relying only on debugging defects after execution.

### Agent-era translation

Do not use an LLM's ability to rapidly generate/fix code as an excuse to make debugging the primary correctness mechanism.

Useful transferable ideas:

- explicit specifications/contracts;
- independent verification mechanisms;
- generate evidence that is different in form from the production implementation;
- prevent classes of errors mechanically when possible.

Agentic Engineering does not adopt the full Cleanroom process as a mandatory methodology.

---

## 5. JPL Holzmann Power of Ten: optimize for mechanical analyzability

Primary source:

- Gerard J. Holzmann, *The Power of Ten — Rules for Developing Safety Critical Code* (2006): https://spinroot.com/gerard/pdf/P10.pdf

NASA/JPL also indexes the paper in the Software Engineering Handbook.

The paper starts with a remarkably relevant criticism: many coding standards grow into hundreds of rules, have little effect on actual developer behavior, and cannot be comprehensively checked by tools. Holzmann argues for a small set that is memorable and mechanically checkable.

### The actual ten rules

The social-media image that motivated this research is directionally useful but mixes Holzmann with generic advice. The actual paper says:

1. use simple control flow; no `goto`, `setjmp`/`longjmp`, or direct/indirect recursion;
2. every loop must have a statically provable upper bound (except intentionally non-terminating loops, whose non-termination should be provable);
3. no dynamic memory allocation after initialization;
4. functions should fit on one printed page, typically about 60 lines;
5. average at least two meaningful assertions per function;
6. data objects should have the smallest possible scope;
7. check non-void return values and validate function parameters;
8. restrict preprocessor use;
9. restrict pointer use/indirection;
10. compile with the strongest warnings and use static analyzers, with zero warnings.

The image's “two nesting levels,” resource-closing rule, and `except: pass` rule are **not** Holzmann's Power of Ten.

### What matters for agents

The paper repeatedly explains the rules in terms of what static analyzers can prove. This is the strongest transferable lesson.

Useful generalizations beyond C/safety-critical code:

- keep control/data flow statically discoverable;
- make resource bounds explicit when predictability matters;
- keep state scopes small;
- expose contracts/preconditions/errors;
- write code simple enough that analyzers do not become confused;
- prefer a small enforced rule set over a giant prose style guide.

### What should **not** become universal agent rules

Do not globally ban recursion, heap allocation, callbacks/function pointers, macros, or dynamic dispatch in ordinary application code. Those restrictions were chosen for safety-critical C and specific verification goals. Translate the mechanism (analyzability/boundedness), then tailor by language and risk.

---

## 6. NASA coding standards and complexity: readability is an operational risk variable

Sources:

- NASA Software Engineering Handbook, SWE-061 Coding Standards: https://swehb.nasa.gov/spaces/7150/pages/16450283/SWE-061%2B-%2BCoding%2BStandards
- NASA Software Engineering Handbook, SWE-220 Cyclomatic Complexity: https://swehb.nasa.gov/spaces/SWEHBVD/pages/105709643/SWE-220%2B-%2BCyclomatic%2BComplexity%2Bfor%2BSafety-Critical%2BSoftware
- NASA NPR 7150.2D, Software Implementation: https://nodis3.gsfc.nasa.gov/displayDir.cfm?Internal_ID=N_PR_7150_002D_&page_name=Chapter4
- NASA Software Analysis Handbook (1994): https://ntrs.nasa.gov/citations/19950005501

NASA's coding-standard guidance explicitly connects uniform coding practices with reduced errors and improved readability/maintenance over long project lifecycles and personnel turnover. It calls out code structure, error handling, module size, constants/types, global data, library usage, and formatting. It also emphasizes automated verification/static analysis.

For safety-critical components, current NASA guidance requires cyclomatic complexity ≤15 unless reviewed/waived, with the rationale that complexity increases path count, testing burden, maintenance difficulty, and failure risk.

### Agent-era translation

Agent turnover is effectively extreme: every new context starts partially cold. Practices that helped new human maintainers also reduce reconstruction work for new agent runs.

Use complexity thresholds as triggers for review/refactoring, not as universal aesthetic scores. A mechanically extracted function can reduce LOC while preserving the same tangled conceptual state; that is not a win.

---

## 7. MISRA and restricted language subsets: remove expensive states from the language

Source:

- MISRA C:2023 Addendum 2 (public cross-reference): https://misra.org.uk/app/uploads/2024/10/MISRA-C-2023-ADD2.pdf

The public addendum confirms, among many other rules, MISRA C's general prohibition on dynamic memory allocation in its target domain.

### Durable lesson

For high-assurance systems, restricting expressive power can lower verification cost more than documenting “use this carefully.”

Agent-era analogues can include project-specific restrictions on:

- reflection/metaprogramming;
- dynamic dependency lookup/service locators;
- unchecked data shapes;
- implicit global mutation;
- unbounded retries/concurrency;
- runtime code generation;
- multiple equivalent ways to express the same architectural edge.

Only impose a restriction when it removes a meaningful source of uncertainty and can be enforced with low noise.

---

## 8. Ravenscar / hard real-time: predictability through a smaller concurrency model

Sources:

- AdaCore, *Concurrency and Real-Time — Ravenscar*: https://learn.adacore.com/courses/Ada_For_The_Embedded_C_Developer/chapters/03_Concurrency.html
- Ada language Ravenscar profile documentation: https://docs.adacore.com/live/wave/arm12/html/arm12/arm12-D-13.html

Ravenscar restricts tasking facilities to support determinism, schedulability analysis, constrained memory use, formal verification, and certification. Constructs that make analysis prohibitively complex are disallowed.

### Agent-era translation

Concurrency can have a disproportionately high reasoning cost. Prefer explicit, bounded concurrency models when the application allows them:

- fixed/controlled worker pools rather than unbounded fan-out;
- explicit queue limits/backpressure;
- clear ownership of mutable state;
- structured cancellation/timeouts;
- deterministic scheduling semantics where required by the domain.

Again, this is not an instruction to make every web service Ravenscar-like. The general mechanism is **constrain nondeterminism enough that correctness and performance remain analyzable**.

---

## 9. NASA core Flight System: stable layers and reusable boundaries reduce repeated integration work

Sources:

- NASA cFS overview: https://etd.gsfc.nasa.gov/capabilities/core-flight-system
- NASA Software Catalog cFS Framework: https://software.nasa.gov/software/GSC-18719-1
- NASA NTRS, *A Core Plug and Play Architecture for Reusable Flight Software Systems* (2006): https://ntrs.nasa.gov/citations/20060026204

cFS uses a layered, component-based, platform-independent architecture with an OS abstraction layer and a message bus. NASA describes its goals in terms of reuse, portability, rapid development, and limiting integration complexity.

### Agent-era translation

Stable directional layers and narrow communication mechanisms can make retrieval/localization easier because the set of legal dependencies is predictable.

But a message bus can also hide call relationships from static search. The useful lesson is not “use pub/sub”; it is:

- define a small number of architectural interaction patterns;
- make them discoverable and mechanically checkable;
- isolate platform/external variability behind stable boundaries;
- reuse validated components rather than repeatedly generating near-duplicates.

---

## 10. Linux kernel practice: small cohesive functions and comments that add information

Source:

- Linux kernel coding style: https://cdn.kernel.org/doc/html/latest/process/coding-style.html

The kernel guide recommends short functions that do one thing, while explicitly allowing longer functions when the code is conceptually simple. It also warns against comments that explain *how* badly written code works, preferring clear code and comments that add purpose/rationale.

### Agent-era translation

This is a useful antidote to blind line-count limits:

- complexity should drive decomposition more than raw length;
- a helper should name/extract a meaningful concept;
- comments should carry information not reconstructable from the syntax.

For agents, redundant comments add context tokens and create another stale source of truth.

---

## 11. Google engineering practice: small conceptual changes and resilient behavioral tests

Sources:

- Google Engineering Practices, *Small CLs*: https://google.github.io/eng-practices/review/developer/small-cls.html
- Google Engineering Practices, *What to look for in a code review*: https://google.github.io/eng-practices/review/reviewer/looking-for.html
- Google Testing Blog, *Test Behavior, Not Implementation*: https://testing.googleblog.com/2013/08/testing-on-toilet-test-behavior-not.html
- Google Testing Blog, *What Makes a Good Test?*: https://testing.googleblog.com/2014/03/testing-on-toilet-what-makes-good-test.html
- Google Testing Blog, *How I Learned To Stop Writing Brittle Tests and Love Expressive APIs* (2024): https://testing.googleblog.com/2024/04/how-i-learned-to-stop-writing-brittle.html

Google argues for self-contained small changes because they are easier to review thoroughly, reason about, merge, roll back, and design well. Their testing guidance emphasizes clarity, resilience, testing public behavior instead of implementation details, and asking whether a test would actually fail when the production behavior breaks.

### Agent-era translation

Tests are a particularly important source of agent leverage because they can replace semantic rereading with executable evidence — but only when they are independent oracles.

Agent-hostile tests include:

- asserting the exact internal call sequence for behavior that does not require it;
- computing expected results by duplicating the production algorithm;
- giant snapshots whose failures do not localize meaning;
- over-mocked internals that make every refactor rewrite tests.

Prefer behavior/invariant/contract tests that survive refactors and fail precisely when the contract changes.

---

## 12. Repository-level LLM work: localization/context selection is a primary cost

Sources:

- Aider, *Building a better repository map with tree-sitter*: https://aider.chat/2023/10/22/repomap.html
- Aider repo map documentation: https://aider.chat/docs/repomap.html
- Zhang et al., *RepoCoder: Repository-Level Code Completion Through Iterative Retrieval and Generation* (2023): https://arxiv.org/abs/2303.12570
- Microsoft Research, *CodePlan: Repository-level Coding using LLMs and Planning* (FSE 2024): https://www.microsoft.com/en-us/research/publication/codeplan-repository-level-coding-using-llms-and-planning-2/

Aider explicitly frames complex repository edits as three tasks: find the relevant code, understand its relations, then make the change. Its repository map uses AST-derived symbols and dependency/reference graph ranking to fit the most useful structural context into a small token budget.

RepoCoder reports gains from iterative retrieval of repository context over in-file and vanilla retrieval baselines. CodePlan similarly starts from the fact that repository-level tasks involve interdependent code too large to place wholly in a prompt.

### Agent-era implication

Source organization affects retrieval cost:

- precise stable symbols are easier to search/rank;
- statically discoverable imports/calls help graph-based maps;
- narrow public surfaces reduce what must be retrieved;
- hidden dynamic wiring/reflection makes structural maps less complete;
- duplicated implementations can send retrieval toward the wrong copy.

This is evidence for **making architecture discoverable**, not for any specific folder naming convention.

---

## 13. OpenAI Harness Engineering: agent legibility and mechanically enforced architecture

Source:

- OpenAI, *Harness engineering: leveraging Codex in an agent-first world* (2026): https://openai.com/index/harness-engineering/

This is currently the most directly relevant public case study found: OpenAI describes a production repository with essentially all code written by Codex. The team explicitly names **agent legibility** as a goal.

Reported practices include:

- a short repository map instead of a huge always-loaded manual;
- repository-local structured knowledge;
- strict architectural layers and allowed dependency directions;
- custom linters/structural tests enforcing those boundaries;
- boundary parsing/validation of data shapes;
- stable/“boring” dependencies and abstractions that agents can internalize;
- structured logging/observability directly accessible to agents;
- file-size/naming/reliability rules enforced mechanically;
- recurring cleanup/“garbage collection” of bad patterns before agents replicate them;
- constraints on boundaries/invariants while leaving local implementation freedom.

The article also makes an important counterintuitive point: in an agent-first repository, rules that might feel pedantic in a human-first environment can compound because they are enforced uniformly across high-volume generation.

### Qualification

This is one team's recent experience, not proof that their exact architecture is optimal for every codebase. The transferable mechanism is:

> make good structure **legible and enforceable**, because agents strongly reproduce the patterns already present in the repository.

---

## 14. Context engineering: tools and code should be self-contained and unambiguous

Source:

- Anthropic, *Effective context engineering for AI agents* (2025): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

Anthropic recommends high-signal context and notes that tools should be self-contained, robust to error, and clear about intended use; bloated/overlapping tool sets create ambiguous decisions.

### Code analogy

The same property is useful at source boundaries:

- one component with a clear role is cheaper than several overlapping “maybe use this” helpers;
- an API whose parameters/contracts are explicit is cheaper than a flexible but ambiguous surface;
- a narrow module boundary helps the agent choose correctly without loading every implementation.

This is an analogy and engineering hypothesis, not a controlled result about source-code architecture.

---

## Where SOLID helps — and where it becomes agent-hostile

The user's motivating hypothesis mentioned SOLID and abstract interfaces. Several parts are well aligned with the historical evidence:

- **Single Responsibility:** good when it creates a cohesive semantic unit and reduces edit radius.
- **Open/Closed:** useful when a stable contract genuinely isolates a changing implementation.
- **Liskov Substitution:** valuable because reliable contracts let agents reason from interfaces.
- **Interface Segregation:** narrow contracts reduce irrelevant context.
- **Dependency Inversion:** can isolate volatile infrastructure/external systems.

But mechanical SOLID can be harmful to agents:

- interface + implementation + factory + provider + adapter for a component with one stable implementation multiplies symbols/hops;
- every extra polymorphic implementation expands the hypothesis space;
- dependency-injection/service-locator frameworks can hide the concrete runtime graph;
- one class per tiny responsibility can scatter a coherent change over many files.

The better invariant is **information hiding + semantic locality + explicit dependency direction**, not “maximum abstraction.”

---

## Formatting and token efficiency

No strong evidence was found that custom formatting designed around a tokenizer improves repository-level coding performance enough to justify deviating from standard source formatting.

Important distinction:

- fewer characters/tokens can reduce raw context volume;
- but dense, unusual, or minified code can reduce semantic clarity, training-distribution familiarity, diff quality, parser/tool behavior, and failure localization.

The operational recommendation is therefore conservative:

- use standard automatic formatting;
- reduce semantic redundancy, not whitespace for its own sake;
- use intermediate names when they expose concepts;
- avoid unrelated reformatting churn.

This should be benchmarked before making language-specific token-layout claims.

---

## Candidate measurable properties for agent legibility

Static metrics alone are proxies. The strongest validation is a representative maintenance task.

### Structural proxies

- cyclomatic/cognitive complexity distribution;
- dependency cycles;
- dependency fan-out/fan-in;
- public API surface size;
- function/module size distribution;
- global mutable state count;
- duplicate/near-duplicate code;
- dynamic/reflection-heavy call edges invisible to static tools;
- number of distinct conventions for equivalent operations.

### Agent-work metrics

- files/symbols opened before localization;
- unique source context loaded;
- dependency hops followed;
- turns/searches before first correct edit;
- edit radius (files/modules touched for one conceptual change);
- test files rewritten by behavior-preserving refactors;
- validation breadth/time;
- retries/reverts/human corrections;
- defect/regression rate under equivalent acceptance.

### Important caveat

A refactor can improve a static metric while making future work worse. Examples:

- extracting many tiny methods lowers function LOC but increases navigation hops;
- creating interfaces lowers concrete coupling metrics but obscures the runtime implementation;
- aggressive deduplication can create a generic abstraction that couples previously independent concepts.

Always tie proxy metrics back to representative accepted work.

---

## Proposed experimental shape

Take a real code region with a recurring maintenance task and compare two equivalent revisions:

1. baseline structure;
2. targeted legibility refactor preserving behavior.

Examples of targeted changes:

- split a high-complexity function along real decisions;
- remove an unnecessary abstraction layer;
- isolate external I/O from deterministic logic;
- make hidden dependency/state explicit;
- replace duplicate implementations with one stable component;
- replace implementation-coupled tests with behavioral/contract tests;
- encode architectural dependency rules mechanically.

Give agents the same task prompt/acceptance suite on the same model/settings and compare localization, context loaded, turns/tools, edit radius, validation effort, and accepted outcome.

Do not compare a clean rewrite against a broken legacy system and attribute the whole difference to one rule.

See [`../experiments/agent-legibility.md`](../experiments/agent-legibility.md).

---

## Bottom line

The historical line is not “old programmers knew ten magic rules.” It is more useful:

```text
expensive execution
  -> make each run count
structured programming
  -> make control flow locally understandable
information hiding
  -> limit what each change must know
safety-critical coding
  -> restrict code until tools can analyze it
real-time profiles
  -> constrain nondeterminism/resources until timing is analyzable
reusable flight architecture
  -> stabilize interfaces and dependency directions
modern testing/review
  -> small coherent changes + independent behavioral evidence
repository-level LLMs
  -> retrieval/localization becomes an explicit bottleneck
agent-first engineering
  -> make legibility and architectural invariants mechanically self-maintaining
```

The common principle is **reduce the state space the maintainer — human or agent — must reconstruct before making a safe change**.
