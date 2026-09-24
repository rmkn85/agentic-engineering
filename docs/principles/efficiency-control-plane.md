# Efficiency control plane

Recent agentic-efficiency work converges on one operational idea: optimize **information and decision flow** before adding more inference infrastructure.

The control plane keeps the model as the expensive probabilistic component inside a mostly deterministic system:

```text
exact/deterministic operation
        ↓ if insufficient
cheapest capable bounded worker
        ↓ if ambiguity/risk exceeds capability
stronger specialist / orchestrator
        ↓
decision artifact / explicit constraints
        ↓
deterministic execution + verification
        ↓
compact receipt + restorable evidence
```

This is a decision model, not a framework requirement. It can be applied with the platform and tools already in use.

## Spend intelligence at uncertainty boundaries

Use model inference where the result can materially change interpretation, architecture, risk handling, or acceptance. Avoid spending it on work deterministic infrastructure already knows how to perform: exact lookup, inventory, hashing, formatting, predictable validation, bounded retry, waiting/polling, or replaying retained evidence.

A useful diagnostic is **decision density**: how many model turns materially change a decision versus merely advance deterministic control flow. Do not maximize it mechanically; use it to find low-value turns such as "now run the obvious test" or "retry the same transient failure."

## Route down after ambiguity is resolved

A strong model or specialist should convert ambiguity into an artifact cheaper execution can consume: accepted constraints, approved interfaces/references, explicit scope ownership, measurable acceptance criteria, and escalation conditions.

Once those exist, route implementation, exact checks, and routine evidence handling back to deterministic tools or cheaper capable workers. Re-escalate only when new evidence reopens the coupled decision.

## Externalize state; preserve exact evidence

Do not use active conversation history as the durable database.

```text
large observation
      ├── durable/restorable artifact
      ├── checksum / identity
      ├── structured metadata or index
      └── compact model-visible receipt
                    └── targeted exact recall when needed
```

The goal is to **compress representation, not evidence**. See [observation economy](../execution/observation-economy.md).

## Prefer local recovery before global replanning

```text
failure
  ↓
classify exact failure
  ↓
known bounded recovery?
  ├─ yes → execute recovery → verify
  └─ no  → escalate to model reasoning
```

Keep recovery bounded, observable, and verification-gated. See [bounded recovery](../execution/bounded-recovery.md).

## Preserve stable prefixes before semantic compression

Before introducing summarizers or learned context managers:

1. keep durable instructions stable;
2. move volatile state later;
3. keep serialization deterministic where the host permits;
4. avoid changing tool/instruction catalogs without a reason;
5. measure actual cached-input reuse when exposed;
6. externalize bulky observations;
7. compact completed phases only after durable state exists.

See [prefix stability](../local-codex/prefix-stability.md).

## Treat fan-out as a latency/coverage trade

Parallel workers can reduce critical-path wall time and improve independent coverage, but they duplicate fixed context, model calls, tool work, and integration effort. Outcome-sized assignments are normally preferable to micro-delegation.

Use the existing measures when the trade is material:

```text
speedup = baseline_wall_time / delegated_wall_time
token_amplification = delegated_tokens / baseline_tokens
parallel_value = speedup / token_amplification
```

## Fuse predictable transitions, not semantic decisions

Some transitions are deterministic enough that returning to the model only to choose the next obvious action is waste:

```text
edit
→ repository-declared targeted validator
→ PASS or compact structured failures
→ model reasons only if failures require judgment
```

Do not hide broad or expensive workflows behind a small action. Fusion should be predictable, inspectable, and bounded by repository policy.

## Quality gate every efficiency claim

> same task + same success criteria + same quality bar → less total resource consumption

Optimize cost, wall time, fresh input, total tokens, or human effort **subject to acceptance quality**.

## Adoption order

Prefer the lowest-complexity layers first:

1. deterministic-first execution;
2. stable prompt/instruction prefix;
3. avoid irrelevant context;
4. externalize bulky observations;
5. route routine bounded work to the cheapest capable executor;
6. fuse predictable validation transitions;
7. use bounded deterministic recovery;
8. compare compaction strategies only when context pressure remains material;
9. consider learned routing or self-hosted serving optimizations only after telemetry shows a real bottleneck.

This ordering deliberately favors portable practices before new runtimes, models, or infrastructure.
