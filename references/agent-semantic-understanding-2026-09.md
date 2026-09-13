# Language-model semantic code understanding — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

Operational guidance: [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md)

## Research question

When we say source should be “analyzable” for agents, what should that mean?

The useful target is not formal verification and not “a sufficiently large model can eventually solve it.” It is **bounded mental-model construction**: a fresh weaker coding model, with limited context and reasoning budget, should be able to read a short local unit plus its immediate explicit contracts and predict representative behavior with useful reliability.

That includes basic questions about:

- control-flow paths;
- data dependencies;
- reachable calls;
- state/liveness;
- side effects and errors;
- resource/retry bounds;
- contract/invariant effects.

The amount of additional repository context and reasoning required to answer those questions is itself an efficiency variable.

---

## SemBench (2026): generation skill is not semantic understanding

Primary source:

- Jade Xu et al., *How well do LLMs understand code?*, Communications AI & Computing (2026): https://www.nature.com/articles/s44488-026-00014-y

SemBench contains 1,000 real-world C programs and 15,404 deterministic semantic questions across six compiler-level properties:

1. dead-code statement;
2. data dependency;
3. function reachability;
4. dominators;
5. dead-code loop;
6. liveness.

The benchmark intentionally asks constrained semantic questions whose ground truth can be computed using AST/compiler/LLVM analyses.

### Results relevant to Agentic Engineering

The paper reports a clear generation/understanding gap:

- evaluated state-of-the-art models reached up to 93.4% pass@1 on standard code-generation benchmarks;
- their SemBench semantic accuracy was substantially lower (reported overall figure 80.42% for the comparison highlighted by the paper);
- simple semantic properties were much easier than complicated ones;
- variable liveness was particularly difficult;
- larger and instruction-tuned models helped, but scaling alone did not close the gap;
- function-reachability accuracy showed moderate correlation with code-generation benchmark performance, suggesting that at least some semantic competence materially affects coding ability.

The authors also report characteristic errors where models use a plausible but incorrect mental model: confusing reachability with usefulness, reversing dominance direction, substituting dynamic feasibility for static reachability, or evaluating liveness at the wrong program point.

### What this suggests here

A codebase should not assume that because an agent can generate a plausible implementation, it can cheaply and reliably reconstruct the semantics of arbitrary existing code.

The structural goal should be to keep ordinary maintenance units inside a **reliable semantic envelope**:

- limited branching/state interactions;
- explicit dependencies and contracts;
- local data flow;
- obvious call relationships;
- visible error/resource bounds;
- minimal hidden runtime wiring.

A stronger model's ability to recover after more context/search/reasoning does not prove the code is agent-legible.

### Caveats

- SemBench focuses mainly on static semantic properties, not full software-maintenance tasks.
- The main benchmark is C; the paper reports a preliminary Python extension with broadly aligned model behavior, but this is not proof across all languages/frameworks.
- It does not directly establish that lowering complexity or shortening functions improves LLM semantic accuracy. That should be tested separately.

---

## LongCodeU (ACL 2025): nominal context is not reliable code comprehension

Primary source:

- Jia Li et al., *Benchmarking Long-Context Language Models on Long Code Understanding*, ACL 2025: https://aclanthology.org/2025.acl-long.1324/

LongCodeU evaluates nine long-context language models on several code-understanding dimensions. The reported results are directly relevant to the “just give the model the whole repository/file” fallback:

- performance drops dramatically once long-code inputs exceed roughly 32K tokens/length scale used by the study, despite advertised context windows of 128K–1M;
- understanding relations **between code units** is the most difficult evaluated category.

### What this suggests here

A huge nominal context window is not a substitute for source organization.

If ordinary behavior requires loading tens of thousands of tokens and reconstructing relations across many units, the code has already exceeded the cheap-maintenance target even if the harness technically accepts the input.

This strengthens the case for:

- narrow mental-model boundaries;
- predictable dependency direction;
- few required inter-unit hops;
- explicit contracts that let the reader stop traversing;
- local code that is understandable before long-context fallback is needed.

The number 32K should **not** become an Agentic Engineering threshold. The paper studies particular models/tasks and future models will change. The durable lesson is to benchmark effective comprehension, not advertised context capacity.

---

## Code semantics equivalence benchmark (2026)

Source:

- Cosimo Laneve, *Understanding code semantics: a benchmark study of LLMs*, International Journal on Software Tools for Technology Transfer (2026): https://link.springer.com/article/10.1007/s10009-026-00842-4

This study probes whether LLMs recognize semantic equivalence/inequivalence under meaning-preserving program transformations such as copy propagation and constant folding. Across the evaluated cases/models, the paper reports that models misclassified 41% of equivalent cases without context and 29% even with minimal context.

### Relevance

It reinforces the distinction between surface-form familiarity and semantic reasoning. For Agentic Engineering, stylistic consistency helps retrieval and pattern recognition, but the deeper goal is keeping behavior easy to reconstruct rather than merely syntactically familiar.

It also suggests that adding a little more prompt context can improve performance without removing the underlying semantic weakness — another reason to improve the source representation itself rather than expecting prompt engineering to compensate indefinitely.

---

## Human-code understandability metrics do not give us a magic scalar

Sources:

- Luigi Lavazza et al., *An empirical evaluation of the “Cognitive Complexity” measure as a predictor of code understandability*, Journal of Systems and Software 197 (2023): https://www.sciencedirect.com/science/article/abs/pii/S0164121222002370
- Luigi Lavazza, Sandro Morasca, Marco Gatto, *An empirical study on software understandability and its dependence on code characteristics*, Empirical Software Engineering 28 (2023): https://link.springer.com/article/10.1007/s10664-023-10396-7
- Marvin Muñoz Barón, Marvin Wyrich, Stefan Wagner, *An Empirical Validation of Cognitive Complexity as a Measure of Source Code Understandability* (2020): https://arxiv.org/abs/2007.12520

The literature supports a cautious view:

- structural measures such as LOC, McCabe/cyclomatic complexity and Cognitive Complexity correlate with at least some aspects of understandability;
- Cognitive Complexity is not consistently a substantially better predictor than older measures;
- models based only on structural measures have substantial prediction error;
- actual comprehension depends on both code structure and the reader/task.

### What this suggests here

Do not define “agent-friendly code” by a single static threshold.

Complexity, function length, nesting, fan-out and similar measures are useful **smoke alarms**. The actual objective should be behavioral:

> Can the target reader accurately build the required mental model with a bounded context and reasoning budget?

This is why [`../experiments/agent-legibility.md`](../experiments/agent-legibility.md) includes a weak-reader semantic test rather than only static metrics.

---

## Proposed weak-reader semantic test

For a target code unit and a representative weaker coding model:

1. provide only the unit plus the contracts/types that the design claims should be sufficient;
2. ask deterministic semantic questions about representative paths, dependencies, state, effects, errors, and bounds;
3. compare answers with tests, static analysis, or hand-verified ground truth;
4. record accuracy;
5. record how often the model asks for/needs additional files;
6. record added source context, searches, model turns, and reasoning budget needed to reach an accepted answer;
7. compare the baseline structure against a targeted refactor that preserves behavior.

A good refactor should improve or preserve semantic accuracy **while reducing the context/reasoning expansion needed by the weaker reader**.

This is closer to the actual maintenance economics than enforcing a universal 40-line/10-complexity rule.

---

## Important distinction: approximation is enough for routine maintenance

The target is not proof of all possible behavior.

For most ordinary engineering work, an agent needs a useful operational model:

- what happens on normal inputs;
- what important edge/error paths exist;
- which state/dependencies influence the result;
- where the contract boundary lies;
- what an intended change is likely to affect;
- which tests/invariants can independently verify the change.

If answering that requires exhaustive symbolic execution or whole-repository loading, the code is outside the desired cheap-maintenance envelope even if formal tooling could eventually analyze it.

Conversely, a local unit can be agent-legible even when the full system is undecidable in the theoretical sense. Agentic Engineering optimizes practical maintenance work, not computability theory.

---

## Operational conclusion

The hierarchy should be:

```text
PRIMARY OUTCOME
weak/fresh model can build an accurate bounded mental model

SUPPORTING DESIGN MECHANISMS
semantic locality
explicit state/dependencies/contracts
simple/enumerable control flow
stable names and direct call relationships
independent behavioral tests
useful diagnostics

MECHANICAL PROXIES / GUARDRAILS
complexity/nesting/function-size thresholds
dependency-cycle checks
static analysis/type checking
formatters/lints

NOT THE OBJECTIVE
minimum LOC
maximum abstraction
formal proof of arbitrary behavior
strongest-model eventual success
```

This definition should guide source from its first line and be reconsidered whenever code is touched, not only during later cleanup.
