# Preserve work, retire disposable resources

The [runtime helper](runtime-controls.md#preserve-and-retire-one-exact-resource)
implements this procedure for exact owned scratch resources, with verified
outside checkpoints and guarded restore. Git resources retain their native route.

Use this procedure when creating or retiring a worktree, worker, temporary
artifact, preview, process or other disposable execution resource. It addresses
resources retained indefinitely because their task remains open, and cleanup
that destroys the only recoverable copy of unfinished work. Use existing resource
producers and task records; no lease service, second backlog or mandatory periodic
bulk deletion follows from this guidance.

## Bind retention to purpose and ownership

At the existing producer or task boundary, retain only what the decision needs:
owner and purpose, active use/dependents, durable checkpoint/evidence destination,
retirement condition and native cleanup route. Reuse existing fields and handles.
A small operation that creates no disposable resource needs no lifecycle record.
A shared cache can remain valuable after one task ends; a completed task does not
authorize deleting another owner's input. Unique state is not disposable merely
because its containing directory was called temporary.

Task closure and resource retirement are independent. A cancelled, failed, paused
or externally blocked task can preserve its unfinished checkpoint and release
reproducible execution resources. A running task can replace an obsolete worktree
or worker without erasing its cumulative limits or evidence. Conversely, an
accepted task may still require retained artifacts under the owner's evidence or
operational policy. Do not infer that an idle-looking resource has no consumer.

## Preserve before removing

1. Identify the exact resource, owner, allowed cleanup scope and active consumers.
   Use the producer's current state rather than an old task label. If ownership,
   active use or deletion authority is uncertain, stop that cleanup and resolve it.
2. Preserve unique source edits, untracked inputs, decisions, necessary logs and
   evidence through the authorized durable route. Keep credentials and sensitive
   data in their proper store. A commit alone may omit untracked work; publication
   alone may omit the evidence needed to reconstruct the next action.
3. Verify preservation: read back the checkpoint and required evidence from their
   destination, confirm source/artifact identities and retain a reproducible resume
   path. A copy command's zero exit or matching source file list is insufficient
   when required state or restore dependencies are missing.
4. Reconcile uncertain effects and transfer or end active consumers. Use the
   maintained producer's bounded cleanup operation on the exact owned resource.
   Preserve native safeguards against escaping paths or deleting shared data.
   Task cancellation alone is not proof that all child processes have stopped.
5. Verify retirement and the retained resume/evidence path. Record what was
   preserved, what was removed and any remaining retention obligation in the
   existing task or producer receipt. A failed deletion is explicit; do not claim
   capacity was reclaimed from the requested action alone.

Choose a preservation destination outside the resource being deleted. If it
cannot hold or restore unique work, retain the resource and repair that boundary;
do not free space by deleting the sole checkpoint. After retirement, recovery
uses the durable checkpoint and producer's normal recreation path. Cleanup itself
may be irreversible, so restore prerequisites belong before deletion, not in a
promised rollback afterward.

## Cost and verification

The intended gain is lower idle resource use and less reconstruction after
interruption. Preservation checks cost storage and time; retain valid shared caches
when rebuilding would cost more and their owner permits retention. Do not scan or
revalidate every resource on each code edit.

Test the reached mechanism with an unfinished task containing unique work and a
reproducible scratch resource: preserve and resume the former after retiring the
latter. A contrasting active/shared resource must survive, and failed preservation
must prevent deletion. Native fixture checks do not prove host cleanup permissions
or a real restoration. Keep those layers open until exercised. This is engineering
policy, not a measured resource-saving claim; revise it if bookkeeping exceeds
useful reclamation or obscures ownership.
