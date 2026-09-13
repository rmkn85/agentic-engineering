# Airborne and real-time assurance lessons for agentic code — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

Reviewed: 2026-09-13.

This note preserves lessons from airborne software assurance and constrained real-time programming that are useful for agent-legible code. It does **not** propose applying aviation certification processes to ordinary software.

Operational guidance: [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md)

## 1. DO-178C / FAA: correctness evidence should not collapse into the implementation

Primary/current FAA source:

- FAA AC 20-115D, *Airborne Software Development Assurance Using EUROCAE ED-12( ) and RTCA DO-178( )*: https://www.faa.gov/airports/resources/advisory_circulars/index.cfm/go/document.information/documentNumber/20-115D

The active advisory circular recognizes DO-178C/ED-12C as an acceptable means for showing compliance for airborne software aspects. DO-178 is fundamentally a **development-assurance/verification framework**, not a source-style guide.

Relevant FAA research sources:

- *An Investigation of Three Forms of the Modified Condition Decision Coverage (MCDC) Criterion*: https://www.faa.gov/sites/faa.gov/files/aircraft/air_cert/design_approvals/air_software/AR-01-18_MCDC.pdf
- *Software Verification Tools Assessment Study*: https://www.faa.gov/sites/faa.gov/files/aircraft/air_cert/design_approvals/air_software/AR-06-54_VerificationTools.pdf
- *Verification of Adaptive Systems*: https://www.faa.gov/sites/faa.gov/files/aircraft/air_cert/design_approvals/air_software/TC-16-4.pdf

### Structural coverage is a second lens

The FAA MCDC study gives a particularly useful explanation of structural coverage: its primary purpose is **not simply to find errors directly**. It acts as a check and balance on requirements-based verification because tests derived only from requirements can fail to expose implementation features that were omitted from/inconsistent with those requirements.

The implication is important:

```text
requirements/contract -> derive expected behavior/tests
implementation        -> independently inspect structural execution
compare the two        -> expose gaps/unintended behavior
```

If the expected result is computed by duplicating the implementation logic, the two lenses collapse into one and common-mode mistakes can survive.

### Agent-era translation

Tests should be independent executable contracts:

- derive assertions from behavior, invariants, examples, schemas, or a simpler independent oracle;
- avoid computing expected results by reimplementing the same algorithm in the test;
- use coverage/trace analysis to discover paths/code the behavioral tests did not exercise;
- investigate untested or unreachable implementation rather than maximizing a coverage percentage mechanically;
- preserve traceability from intended behavior to evidence where consequence justifies it.

An agent can generate thousands of tests cheaply. Quantity does not compensate for a shared misunderstanding between production code and tests.

### Do not cargo-cult MC/DC

High-assurance aviation uses demanding coverage/verification objectives because failure consequences justify the cost. Ordinary application code should not inherit MC/DC or certification ceremony by default.

Transfer the mechanism:

> **independent behavior evidence + structural cross-check, scaled to risk.**

---

## 2. Ravenscar: restrict expressiveness when unrestricted behavior makes analysis too expensive

Sources:

- AdaCore GNAT guide, Ravenscar profile: https://docs.adacore.com/gnat_ugx-docs/html/gnat_ugx/gnat_ugx/the_predefined_profiles.html
- AdaCore embedded-Ada guide, Ravenscar: https://www.adacore.com/uploads/books/pdf/Ada_For_The_Embedded_C_Developer.pdf
- SPARK Ravenscar material: https://docs.adacore.com/sparkdocs-docs/Examiner_Ravenscar.htm

Ravenscar restricts Ada tasking/concurrency for domains requiring predictability, certification, formal verification, constrained memory, and low overhead. AdaCore's documentation is unusually explicit about the motivation: unrestricted tasking can make analysis technically or economically infeasible; the subset is designed to remain analyzable while still useful in practice.

### Agent-era translation

This is very close to the desired “bounded mental model” principle.

For agent-maintained code, consider constraining mechanisms whose flexibility explodes the state space:

- unbounded concurrency/fan-out;
- dynamically created long-lived actors/tasks without ownership rules;
- implicit shared mutable state;
- arbitrary callback/plugin graphs;
- retries/queues with no explicit limits/backpressure;
- runtime dependency mutation;
- multiple concurrency primitives for equivalent jobs.

Do not ban concurrency. Prefer a small, conventional subset whose possible interactions a weak reader can enumerate approximately.

### Technical versus economic analyzability

A behavior can be theoretically analyzable but still fail Agentic Engineering if the analysis consumes an unreasonable amount of model context/compute.

That gives a useful distinction:

```text
possible to understand eventually
!=
cheap enough for routine maintenance
```

The target is the second.

---

## 3. JPL Power of Ten: a small enforceable set beats a huge remembered standard

Primary source:

- Gerard J. Holzmann, *The Power of Ten — Rules for Developing Safety Critical Code*: https://spinroot.com/gerard/pdf/P10.pdf

NASA reference:

- NASA, *Tools Ensure Reliability of Critical Software*: https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20120001915.pdf

Holzmann's starting criticism is itself relevant to agents: coding standards often accumulate hundreds of rules, developers do not consistently follow them, and many cannot be automatically checked. The Power of Ten intentionally reduces the set to rules that are memorable, tied to risk, and largely mechanically verifiable.

### Agent-era translation

Do not solve agent-legibility with a 200-rule prompt.

Use:

- a tiny high-value source-scoped instruction set;
- language/project-specific static enforcement for exact restrictions;
- weak-reader semantic tests for the property static linters cannot prove;
- deeper rationale/reference material off the normal context path.

In this repository that split is represented by:

- [`../templates/source-AGENTS-agent-legible.md`](../templates/source-AGENTS-agent-legible.md) — compact runtime rules;
- [`../docs/code/agent-legible-code.md`](../docs/code/agent-legible-code.md) — operational depth;
- reference notes under `references/` — research/provenance;
- [`../experiments/agent-legibility.md`](../experiments/agent-legibility.md) — behavioral measurement.

---

## 4. Shared lesson: reduce the state space before asking intelligence to conquer it

Aviation/realtime/safety-critical practices often look restrictive because their environment values predictability and assurance over maximum expressiveness.

The transferable agentic principle is not “write avionics code everywhere.” It is:

> **When a language/runtime/design feature adds states and interactions that are rarely needed but repeatedly expensive to understand and verify, constrain it at the project boundary.**

For agents, every extra state can become:

- another branch to simulate;
- another dependency to retrieve;
- another hidden mutation source;
- another test combination;
- another debugging hypothesis;
- another opportunity for a weaker model to use a plausible but wrong mental model.

The best restriction is often the one that converts an open-ended reasoning problem into a small explicit contract a compiler, linter, test, or weak model can check cheaply.

---

## 5. Risk scaling

The stricter the consequences and real-time constraints, the more worthwhile it becomes to reduce expressive freedom and demand independent evidence.

A useful continuum is:

```text
low-risk UI glue
  -> conventional simple code + ordinary behavioral tests

business-critical service
  -> explicit contracts/state/errors + stronger static/integration checks

hard real-time / safety relevant
  -> bounded resources/concurrency + analyzable subsets + independent assurance

certified safety-critical
  -> domain certification standard/process governs
```

Agentic Engineering should preserve this proportionality. The point is to make the **same required system** cheaper and safer to maintain, not to make every repository resemble flight-control software.
