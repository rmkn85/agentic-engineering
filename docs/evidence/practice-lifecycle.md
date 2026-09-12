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
