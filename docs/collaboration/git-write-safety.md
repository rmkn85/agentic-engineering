# Source identity and recoverable writes

Use this when resuming, changing execution hosts, publishing a checkpoint, or recovering an uncertain Git operation. The project's native task and branch policies remain authoritative.

## Verify before changing source

Resolve the intended repository, actual checkout, current HEAD, authorized branch, selected fetch/push destination and owned changes. Refresh remote evidence through the available authorized route; an IDE branch label and cached refs do not prove freshness. Preserve dirty, staged and untracked work. An unavailable CLI is not evidence an independent connector lacks write permission.

No one should switch a shared working directory under another active writer. Prefer isolated preparation when local policy permits it. Direct-to-main projects can still serialize actual writes and integrate coherent deltas; this guide does not impose pull requests or a universal branch policy.

## Classify rather than blindly retry

| Observed failure | Correct response |
| --- | --- |
| Unrelated changes repeatedly edit one file | Improve ownership boundaries; do not grow another global router |
| Unrelated files conflict only because the branch head advanced | Rebase/rebuild the candidate on the new base; do not fragment coherent modules |
| Clean textual merge creates competing schema/authority | Reconcile one contract and exercise installed consumers |
| Derived index/catalogue collides | Edit its independent sources and regenerate deterministically |
| Write response is ambiguous | Read back the exact ref/file and compare intended content before retrying |
| Missing executable or denied transport | Use a separately authorized working route or record one concrete prerequisite; no credential hunting |

For API multi-file writes, use the current tree, actual parent and a non-force ref update. A rejected update is successful protection. Check for already-landed work, reconcile only the intended delta, rerun affected checks, and retry within a bounded scope. Never replace a hot file from an old full-text copy.

For a clean stale local checkout, a permitted fast-forward is mechanical. Divergence, another task's branch, an unfinished merge/rebase or unknown dirty work requires ownership-aware recovery, not reset/clean/force. Reuse existing checkpoints and preserve a patch or coherent commit through the repository's accepted route when interrupted.

## Evidence and closure

Record source identity, check identity, artifact identity and integration/publication result separately in existing work records. Read back successful remote writes. A local commit or unattached object is not a remote checkpoint; a remote checkpoint is not accepted delivery. If another writer advances the branch, ancestry and the affected diff determine which evidence remains valid.

Improve repeated failure classes in the smallest useful layer: mechanical guard first, native configuration/test next, concise instruction or on-demand procedure only when judgment is required. See [collisions as signals](collisions-as-signals.md) and the [newcomer contract](../adoption/newcomer-contract.md).
