# Collisions as architectural signals

Concurrent-agent conflicts are not only operational nuisances. Repeated collisions can reveal poor ownership boundaries.

Examples:

- many agents edit the same registry or index
- unrelated features require updates to a central switch statement
- every task touches one oversized configuration file
- merge retries repeatedly occur in the same module

## Response

1. Record the collision rather than hiding it as a retry.
2. Determine whether the shared edit is inherently global or accidentally centralized.
3. When possible, refactor toward independently owned components, generated aggregation, append-only structures, or stable interfaces.
4. Measure whether collision frequency and retries actually fall.

Not every conflict implies bad architecture. Schema migrations and genuinely global contracts may require synchronization. The useful signal is repeated contention that should not be semantically necessary.
