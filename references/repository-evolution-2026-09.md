# Repository evolution lessons — 2026-09

Status: research/reference material. **Not part of the normal agent reading corpus.**

This note records what the repository learned from its first real uses. The important signal is not the exact wording of each commit; it is the sequence by which apparently reasonable guidance failed under live work and was converted into more observable decision points and behavioral checks.

## Sequence

### 1. General delegation caution was not enough

Commit: [`e0582251` — Require executor and model routing before substantial work](https://github.com/rmkn85/agentic-engineering/commit/e0582251ede8e24862b3801bddaca704e1c7dabc)

Observed pattern recorded by the repository: the agent had efficiency guidance available but still consumed a long routine batch itself and delegated only after human correction. The first worker also inherited the expensive orchestrator model, so “delegated” did not automatically mean “cheaper.”

Correction:

- introduce an executor-routing checkpoint **before** the batch;
- distinguish spawning a worker from choosing its model/tier;
- make the choice observable in the existing work context;
- keep one-line direct commands local instead of turning the checkpoint into ceremony.

Lesson: **an instruction that describes a preference can be too weak if the behavior needs a decision at a specific execution boundary.**

### 2. Correct routing still did not guarantee the requested outcome

Commit: [`1e890074` — Preserve substantive outcomes in delegated transformations](https://github.com/rmkn85/agentic-engineering/commit/1e89007411508a720222584cd4f31048c24ba300)

A later broad knowledge-consolidation task showed another proxy failure: source inventory, worker completion, navigable files, and structural checks could all look successful while the resulting material remained too shallow and left important synthesis in the original sources.

Correction:

- assign outcome-sized deliverables, not merely source partitions;
- distinguish structural acceptance from substantive acceptance;
- inspect an early representative artifact before multiplying the pattern;
- reconcile source-to-result coverage at integration;
- keep the orchestrator responsible for uncovered scope.

Lesson: **efficiency mechanisms must preserve the actual user outcome, not optimize a proxy such as worker completion, link coverage, or file count.**

### 3. Guidance needed clearer grouping and deviation semantics

Commit: [`7d4931d7` — Group delegation deviation guidance under its heading](https://github.com/rmkn85/agentic-engineering/commit/7d4931d7c734c8a14a9618f9ecae6c498f4cf672)

As the delegation guidance grew, organization itself became part of instruction quality. Distinguishing increased fan-out from intentionally constrained fan-out prevents contradictory guidance from becoming one undifferentiated list.

Lesson: **instruction structure affects the decision the agent extracts. Adding correct sentences can still make the combined policy less clear.**

### 4. Live review exposed defects that structural/dry-run checks missed

Commit: [`41ccfb99` — Record live outcome-preserving delegation observation](https://github.com/rmkn85/agentic-engineering/commit/41ccfb99e22966adb1d68c32fc8c618eaeb3c0a6)

The recorded qualitative observation notes that independent readers using the produced reference exposed shallow leaf material, missing integrated explanation, non-runnable example setup, and prose/implementation mismatches after earlier structural checks had passed.

Lesson: **behavioral and artifact-level acceptance catches failures that instruction presence, worker handoffs, schemas, and link checks cannot.**

## Meta-pattern

The early repository evolution follows a useful loop:

```text
reasonable guidance
    -> live agent finds/creates a loophole
    -> identify the actual decision boundary or proxy failure
    -> make behavior observable
    -> add a targeted regression scenario
    -> keep economic claims separate until measured
```

This is stronger than accumulating “best practices.” The repository should continue to evolve from concrete failures and measured uncertainty.

## Implication for instruction/context work

The next predictable failure would be to respond to every observed non-adherence by appending more global prose. That would repeat the same pattern at a higher level: solving a local failure with a proxy (“the instruction exists”) while degrading the agent's working context.

Therefore the current changes add a second loop:

```text
observed instruction failure
    -> verify what actually loaded
    -> test interaction with the normal stack
    -> smallest instruction/scoping/enforcement change
    -> pressure-test behavior
    -> ablate/remove/demote guidance that does not earn residency
```

The `references/` split is itself a response to this evolution: preserve rich reasoning and external research **without making ordinary agents pay for all of it on every task**.
