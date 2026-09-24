# Bounded recovery before model replanning

Many agent failures are operational rather than semantic. Asking a model to rethink the whole plan after every timeout, schema error, stale generated file, or formatter failure spends reasoning on control flow that can often be deterministic.

## Recovery loop

```text
execute
  ↓
success? ── yes → verify → continue
  │
  no
  ↓
classify failure
  ↓
known bounded recovery?
  ├─ yes → recover → verify
  │             ├─ pass → continue
  │             └─ fail → budget exhausted?
  │                          ├─ no → retry allowed recovery
  │                          └─ yes → escalate
  └─ no → escalate to model reasoning
```

The important properties are **bounded**, **observable**, and **verification-gated**.

## Starter taxonomy

| Failure signal | First response | Escalate when |
| --- | --- | --- |
| timeout / transient network failure | bounded retry with backoff | budget exhausted or operation is not safe to retry |
| rate limit | obey retry-after / wait policy | deadline or quota makes completion infeasible |
| command not found | inspect declared toolchain/environment | expected dependency cannot be located safely |
| parser / syntax error | return exact location to responsible editor | ownership or expected source is ambiguous |
| formatter/lint issue with approved fixer | run the known deterministic fixer once | fixer changes semantics/scope or remains failing |
| stale generated output | run repository-declared generator | generator is ambiguous, destructive, or fails |
| test assertion failure | expose assertion + minimal traceback/evidence | diagnosis requires semantic reasoning |
| tool/schema argument error | deterministic repair when unambiguous | multiple valid interpretations exist |
| write/merge collision | stop, refresh authoritative state, serialize ownership | conflict requires semantic reconciliation |
| ambiguous regression | none | immediately escalate |

This is a starting policy, not a universal list.

## Recovery budget

Each recovery class should define a finite budget:

- maximum attempts;
- maximum elapsed time;
- whether backoff applies;
- whether the operation must be idempotent;
- verification required after recovery;
- conditions that forbid automatic recovery.

Do not let "self-healing" become an infinite retry loop.

## Local repair before global replan

Prefer the smallest intervention that addresses the observed failure:

```text
argument mismatch → repair arguments
single generated file stale → run generator
approved formatter failure → run formatter
semantic contradiction across modules → model reasoning / replan
```

Global replanning is appropriate when the failure invalidates assumptions or goals, not merely because a tool returned non-zero.

## Verification is separate from recovery

A recovery action is not success. Verify the outcome using the cheapest acceptance surface that can establish it.

Examples:

- retry returned HTTP 200 → still validate expected payload/state;
- formatter exited 0 → still run relevant syntax/type/test checks when required;
- generator completed → verify generated artifacts are current;
- argument repair executed → verify the result matches the intended operation.

## Safety and ownership

Automatic recovery must not expand authority. Do not automatically:

- delete or overwrite unrelated user work;
- force-push or rewrite history;
- disable tests or security checks;
- broaden network/account permissions;
- install undeclared dependencies;
- choose among semantically different migrations;
- weaken a failed acceptance criterion.

Those are decision boundaries, not recovery mechanics.

## Telemetry

When recovery is material, retain:

```text
failure_class
original_operation
recovery_action
attempt_count
elapsed_time
verification_result
escalated?
final_acceptance
```

Ask: how many failures were resolved without a new reasoning turn, which classes repeatedly escalate, which recoveries create rework, and whether retries are hiding flaky infrastructure.

## Promotion rule

Start with explicit repository-declared recovery rules. Promote a pattern only after repeated evidence shows that classification is reliable and recovery preserves the requested outcome.

Do not begin with a general autonomous recovery framework when a small deterministic policy table is sufficient.
