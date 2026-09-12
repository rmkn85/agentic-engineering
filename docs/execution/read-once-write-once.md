# Read once, write once, invalidate explicitly

For large transformations, repeated semantic passes can dominate cost.

A useful target is:

1. fully inspect a coherent unit
2. decide its destination and transformation
3. produce the intended result
4. validate it
5. persist the decision and hashes
6. freeze it until a dependency change explicitly invalidates it

## Decision ledger

A compact machine-readable record can include:

```json
{
  "file": "src/example.py",
  "input_hash": "...",
  "output_hash": "...",
  "decision": "move+modify",
  "public_api_changed": false,
  "validated": ["parse", "typecheck", "unit"],
  "status": "done"
}
```

An unchanged file can still carry an explicit semantic decision such as `retain-content/move-only`.

## Invalidation

A completed unit becomes dirty when a relevant assumption changes, such as:

- an imported interface changes
- an architectural rule changes
- a generated contract changes
- a failing integration test reveals a hidden dependency

This mirrors incremental compilation: recompute what is invalid, not everything that existed before it.
