# Source identity and recoverable writes

Use this when resuming, changing execution hosts, publishing a checkpoint, or recovering an uncertain Git operation. The project's native task and branch policies remain authoritative.

## Verify before changing source

Resolve the intended repository, actual checkout, current HEAD, authorized branch, selected fetch/push destination and owned changes. Refresh remote evidence through the available authorized route; an IDE branch label and cached refs do not prove freshness. Preserve dirty, staged and untracked work. An unavailable CLI is not evidence an independent connector lacks write permission.

No one should switch a shared working directory under another active writer. Prefer isolated preparation when local policy permits it. Direct-to-main projects can still serialize actual writes and integrate coherent deltas; this guide does not impose pull requests or a universal branch policy.

## Parallel worktrees and PR coordination

Use a separate owned worktree/branch for each independent writing lane when concurrent edits, builds or checkouts could collide. Reuse a suitable owned worktree before creating another. A read-only review or tiny serialized edit may need no new checkout. Record the repository, worktree, branch/base, owned paths, shared interfaces and integration owner in the existing assignment. Never copy uncommitted changes implicitly or assume isolated worktrees isolate shared ports, caches, credentials, services or Git metadata.

Make early coherent commits so work survives interruption. Where the repository uses PRs, open one coherent PR per independently integrable outcome and use its URL plus exact base/head identities as the coordination point. Describe behavior and acceptance, keep it current as scope changes, and report whether it is draft, checked, reviewed, merged or blocked. A PR link is not proof of integration. Prefer compact event-driven status and maintained CI-log activity commands supervised by Luna; do not reread full logs or ask approval for inline retrieval commands.

One owner integrates shared-contract changes and serializes merges. Refresh remote/base evidence before integration; review the actual diff and required checks for the candidate head. Reconcile semantic conflicts and run affected integration checks on the resulting candidate. Preserve valid evidence whose inputs did not change; rerun checks invalidated by the new base. Coordinate cross-PR dependencies explicitly rather than independently editing competing contracts. Follow the repository's existing merge/approval policy and never infer merge authority from write access. In a direct-to-main project, apply the same ownership, coherent-commit and exact-result checks through its native route.

After read-back confirms the integrated result and required evidence is durable, retire the worker and archive/remove only its owned worktree and temporary branch through the supported route. First inspect dirty, untracked and ignored files, unpushed commits, open PRs and active users; preserve any useful source/data/evidence. Do not delete unrelated worktrees, force-remove a dirty checkout, or treat a merged PR as proof that every ignored artifact is disposable. Shared caches have their own lifecycle. Keep an unresolved or independently useful lane recoverable in its existing handoff.

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
