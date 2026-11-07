# Executable runtime controls

`python3 tools/control_runtime.py --help` exposes bounded, local operations with
Python 3.9+ and no service, provider calls or arbitrary shell in JSON. The helper
implements selected-state observation, a current owned-scope filesystem probe,
and exact scratch preservation/retirement. It does not scan or delete a resource
inventory. Git worktrees remain with the existing benchmark/checkout producer.

These controls address repeated unchanged observations, stale permission
assumptions and abandoned scratch resources. They cost hashing, temporary storage
and owner bookkeeping. Use them when those costs are smaller than repeated
observation or reconstruction; a short operation without disposable state does
not need a lifecycle record. No measured token, time or storage saving is claimed.

## Trust and native adoption

The native owner supplies selected decision fields, authorization observations,
exact ownership, current consumers, lease and retirement decision. A JSON value
is an observation, **not authentication**. The helper cannot discover undeclared
external consumers or prove that the caller has authority. A random marker binds
a resource instance to an exact path and owner, rather than accepting a path
label; it does not authenticate that owner. Host permissions remain controlling.
Do not run against an untrusted concurrently modified filesystem. Stop producers
and consumers before planning; exclusive use is a precondition of retirement.

Adopters bind these CLI operations to reviewed parameterized native activities.
Retain their JSON receipts as hashed artifacts in the existing task evidence,
with the owner's authorization/source/evidence envelope. Receipts have
`schema: runtime-control/v1`; a receipt is not by itself delivery acceptance.
Unknown observations and failed probes must remain visible to the native gate.
No host policy is modified. No new task database or blanket evidence TTL is added.

## Observe selected decision fields

```sh
python3 tools/control_runtime.py observe --spec examples/runtime-controls/observation-spec.json --observation examples/runtime-controls/observation.json --state /tmp/runtime-state.json --expect absent
```

Use a new state location for the first observation. Subsequent calls must supply
`--expect` equal to the previous `stateDigest`. A per-state exclusive lock and
atomic replacement reject concurrent/stale writes. An interrupted writer can
leave a lock; the owner must reconcile it before removing it. Do not automatically
break unknown locks. The parent directory must be trusted and writable.

`fields` selects top-level decision-bearing JSON values; object key order and
unselected timestamp noise do not affect comparison. Array order remains
meaningful. Optional nonnegative `jitter` values compare numeric changes to the
**last waking baseline**, never to the previous suppressed sample. Thus cumulative
drift wakes the owner. Missing selected fields appear in `unknown`; newly missing fields wake by
default (set `missingActionable:false` only by an owner decision). Mandatory true
`completion`, `failure`, `denial` and `exhaustion` values bypass suppression even
when unselected. Native adapters must map their terminal/error events into these
explicit booleans; the helper cannot interpret arbitrary vendor status strings.
Persistent unchanged critical and unknown sets coalesce and increment suppression
counts. Clearing then reasserting a critical event wakes again. Periodic reminder
or heartbeat policy belongs to the native owner; an incident does not wake on
every poll. Selected decision changes still wake while an incident persists.

The output contains `wake`, changed fields, critical events, unknown fields,
fingerprint, state identity and cumulative observations/wakes/suppressed counts.
A changed spec fails closed; start a new state intentionally. State stores compact
selected values and counts, not full telemetry. Missing telemetry is unknown,
never a measured zero or proof of progress.

## Probe current capability

```sh
python3 tools/control_runtime.py capability --request examples/runtime-controls/capability-request.json
```

The request declares exact `scope`, `owned:true`, `authorization` as
`allowed|denied|unknown`, and `authorizationRevision`. Denied/unknown authorization
returns without probing. Allowed authorization permits an exclusive temporary
child directory, file write/readback/removal and directory removal in that scope.
A native failure reports denied capability while preserving the distinct supplied
authorization observation. Success reports `observed-writable`, never a grant.
Reprobe after a relevant session/profile/scope/revision change; explicit denial
or revocation remains binding even if the directory is technically writable.
For delivery-gate consumption, a native producer supplies optional binding metadata
`authorityDigest`, `conditionsDigest` and `producer` in the request. These fields
are all-or-none; both digests must be 64 lowercase hexadecimal characters and the
producer must be a nonempty string. The receipt echoes exactly those validated
values, including on denial/unknown results. It never fabricates them. The native
gate compares them to the current task authority, conditions and declared producer,
checks `authorizationRevision` against the current authorization revision, and
requires the exact requested scope and a passed writable probe. An unbound receipt
remains usable as a standalone observation, but cannot support that delivery gate.
Binding metadata and a successful probe remain observations, not authentication.

This tests local filesystem capability only, not network, publishing or arbitrary
commands. It does not establish future capability after permissions change.

## Preserve and retire one exact resource

All request, plan, receipt and checkpoint paths are explicit. `--output FILE`
retains any operation's JSON and refuses to overwrite an existing output file.
The checkpoint belongs outside the resource on an owner-selected durable storage
route; `/tmp` in the example is fixture storage, not a durability recommendation.

1. Create an empty scratch directory through `init --request INIT.json`, where
   `INIT.json` contains `resource` and `owner`. Only an empty directory can be
   initialized. Retain the returned random `id` as `resourceId` in the resource
   request. New unique bytes can then be written inside it.
2. Release all consumers and the producer lease. Supply the exact current
   resource request; see [the example](../../examples/runtime-controls/resource-request.json).
   `shared:false`, `dependents:[]`, `lease.state:"released"` and `retire:true` are
   required positive observations. Unknown or active/shared resources survive.
   Cancellation alone does not set these facts.
3. Run `plan --request REQUEST.json --output PLAN.json`. The plan binds the
   complete request, instance marker and exact file/directory manifest, including
   ordinary permission modes and the resource root mode. Special set-user-ID,
   set-group-ID and sticky bits are rejected rather than restored. It
   rejects root, current checkout and its parents, Git resources, protected path
   overlaps, traversal, symlinks, hard links and special files. Declare other
   live/checkpoint/evidence roots in `protected`; the tool cannot discover them.
4. Run `preserve --request REQUEST.json --plan PLAN.json`. It snapshots once to
   a new outside checkpoint, verifies copied bytes, rechecks the source and
   reads back the published snapshot. Existing snapshots are never overwritten.
   `verify --plan PLAN.json` repeats readback without copying. A failed/partial
   preservation retains the source; repair the checkpoint boundary before retry.
5. Run `apply --request REQUEST.json --plan PLAN.json` using current observations.
   Any changed request, lease, source, marker or checkpoint blocks retirement.
   The helper revalidates source and preservation immediately before removal,
   verifies disappearance, and writes `retirement.json` outside the removed tree.
   Interruption during deletion can leave partial source; the verified checkpoint
   survives. Failure writing the receipt reports failure even if removal occurred;
   reconcile actual source/checkpoint state instead of repeating blind deletion.
6. To resume, initialize a **new empty owned destination**. Run
   `restore --plan PLAN.json --request RESTORE.json`, with `destination`, `owner`
   and its new `resourceId`. Restore verifies the checkpoint first, refuses
   differing/nonempty live state, copies bytes, preserves ordinary file/directory permission modes, and checks
   readback while keeping
   the destination's new ownership marker. Failed partial restores are retained
   for owner reconciliation, never deleted automatically. Rebind current task
   authorization and evidence in the native resume gate before continuing work.

Keep the plan and requests outside the disposable resource. Unique work has an
outside verified copy before removal; cleanup never overwrites the only copy.
Filesystem readback proves retained bytes, not power-loss durability or an
undeclared application's restore dependencies. Select durable storage and include
all required inputs in the exact scratch boundary. Resource requests are local
observations, so rechecking an unchanged request cannot discover a consumer that
was never recorded. No locking scheme makes a hostile concurrent writer safe.

## Verification and limits

Run `python3 -m unittest discover -s tools/tests -p test_control_runtime.py`.
The tests exercise fixed-baseline cumulative drift, critical bypass and incident
coalescing/reassertion, missing telemetry, executable/mode restoration and changed
mode rejection, stale/concurrent observation state, denied/revoked capabilities, real
preserve/remove/restore, active/shared/unknown retention, stale source and plans,
corrupt or failed preservation, symlink/hard-link guards and ownership mismatch.
These deterministic checks do not prove host permissions, actual consumer
cessation, power-loss recovery or a real supported-worker adoption trial. Native
owners retain those acceptance obligations and measure control overhead where
available; otherwise the overhead remains unknown.
