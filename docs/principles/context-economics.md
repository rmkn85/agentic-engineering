# Context economics

Model context is a working set, not an archive.

Large repositories create several distinct costs: first-time source reading, repeated context, model reasoning, generated output, tool output, and retries caused by lost or stale state. Optimizing only repository size misses most of the system.

## Stable before volatile

Keep durable context conceptually ahead of changing task state:

1. system and repository instructions
2. architecture and invariants
3. stable repository metadata
4. current task
5. current files and diagnostics

Stable prefixes improve reuse and reduce needless reintroduction of unchanged context.

## Compress semantics, not truth

After a unit has been fully inspected, later work often needs only compact facts:

- content hash
- destination / ownership
- public symbols
- dependencies
- transformation decision
- validation result
- invalidation state

The source remains authoritative and can be reopened when an invalidation requires it. The compact record prevents gratuitous rereading.

## Tool output is context too

Logs stored on disk are cheap. Logs copied into model context are not.

Prefer terse summaries first, then targeted expansion on failure. A successful test suite should normally enter model context as a small result, not thousands of passing test lines.

## Output can dominate

When a workflow requires a model to regenerate large amounts of source, output may dominate model cost. Avoid regenerating unchanged bytes merely to prove they were considered. If intentional preservation is required, record an explicit retain/move decision and use deterministic movement when possible.
