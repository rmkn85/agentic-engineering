# From local lesson to shared practice

Projects are laboratories. Shared methodology should be the result of learning across them, not the starting assumption.

## Lifecycle

### Observation
A concrete failure, success, bottleneck, or repeated behavior occurs.

### Local adaptation
The project changes its workflow or tooling to address the issue.

### Measurement
The project observes effects on time, usage, quality, collisions, retries, or human effort.

### Generalization
Ask which parts depend on the domain and which describe a broader agent-engineering mechanism.

### Promotion
A sufficiently general, evidence-backed mechanism becomes shared guidance.

### Challenge
Other projects test the practice under different constraints and record counterexamples.

### Revision
Scope, defaults, or mechanisms change as evidence improves.

## Suggested evidence record

```yaml
practice: short name
origin: anonymized project/workload class
problem: what repeatedly happened
change: what was altered
observations: measurable or concrete effects
scope: where it appears applicable
costs: tradeoffs introduced
exceptions: known counterexamples
confidence: hypothesis | observed | repeated | benchmarked
```

## Close the loop in the existing run record

Use one compact receipt for consequential workflow decisions, changed practices or an evaluation—not one entry per tool call. A routine edit needs no new form. Keep detailed native logs privately and return a summary plus exact evidence handles. Do not publish private project examples or raw traces into this public methodology repository.

Record **which practice/revision, why it applied, what path was chosen, and what evidence bears on the outcome**. Distinguish `not_used`, `selected`, `loaded` and `applied`; record the highest stage actually supported. A file read is not understanding, a sign-off is not use, and a matching artifact hash is not causal proof. Mark attribution as `self_report`, `tool_trace` or `independent_review`; none is authenticated by this file format. Preserve unsuccessful and unchanged cases, not just success stories.

The optional `practice-feedback/v1` receipt can live beside an existing native run/benchmark record:

```json
{
  "schema": "practice-feedback/v1",
  "record_kind": "agent_run",
  "run_id": "unique-run-and-attempt",
  "source": "immutable-tested-revision",
  "task_class": "boundary-change",
  "practices": [{
    "id": "preserve-invariants", "revision": "exact-policy-revision",
    "stage": "applied", "basis": "self_report",
    "trigger": "Verification was narrowed, not product scope.",
    "decision": "Retained the existing consumer mechanism and probed its next extension.",
    "evidence": []
  }],
  "outcome": {
    "status": "unverified", "evidence": [],
    "preventable_corrections": null, "creative_changes": null,
    "structural_regressions": null, "rework_cycles": null
  },
  "measurements": {
    "wall_seconds": null, "tokens": null, "instruction_bytes": null,
    "first_actionable_failure_seconds": null
  }
}
```

This is a shape example, not a real run. References use `{"path":"native.log","sha256":"<64 lowercase hex characters>","lines":[2,8]}` relative to the authorized evidence root. `lines` is optional; the hash covers exact bytes including newline endings in that range, or the whole file. A fixed range supports append-only logs. Use native trace/report, actual diff/consumer call and inspected artifact evidence rather than a second prose assertion. No remote locator is fetched by the analyzer.

```sh
python3 tools/practice_feedback.py run/practice-feedback.json --evidence-root run --output run/practice-summary.json
```

The helper verifies receipt shape and local evidence identity, preserves missing/mismatched evidence, and aggregates known-value denominators. It never infers approval, reviewer independence, omitted requirements, instructions delivered by a host, or aesthetic quality. Exit 2 means invalid input; a valid report with unresolved evidence is not acceptance. Output files are not overwritten. See [tools](../../tools/README.md) for the existing benchmark integration.

## Measure benefit, not declarations

Inspect native actions/diffs to confirm the claimed path. Compare first-pass substantive acceptance, structural regressions after an ordinary extension, preventable owner corrections, rework and time to actionable failure. Keep creative direction separate from avoidable mistakes. Observe instruction footprint and validation cost alongside quality; fewer tokens with weaker outcomes is not improvement.

The summarizer keeps fixtures/manual reviews/agent runs and task classes separate, reports practice revisions, and shows known/total denominators. It does not rank models or calculate a causal effect. Further comparisons must match task/input revision, tools, permission, review bar and resources. Unknown costs/model settings remain unknown. Do not average only successful attempts and omit failed work from cost.

To test generalization, use the normal instruction stack and an ordinary prompt, with evaluator expectations withheld. Have a fresh agent make a follow-up extension; retain an already-good implementation, authorized narrow prototype, explicit scope change and trivial edit as controls. Public cases that shaped the practice are regression material, not held out. See [instruction experiments](../../experiments/instruction-context-adherence.md).

If reported loading rises but useful decisions do not, fix the trigger or construction mechanism rather than adding prose. If outcomes stay equivalent while overhead rises, simplify, scope or remove the practice. A finite sample or missing instrumentation cannot establish universal compliance or zero value.
