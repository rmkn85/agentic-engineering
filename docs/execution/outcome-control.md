# Executable outcome controls

This opt-in helper rejects stale assignments, unsupported delivery claims and
unsafe recovery attempts in an **existing canonical task**. It adds no task
database, service, agent call or command runner. Python 3.9+ and the standard
library are sufficient. Review date: 2026-11-07.

The mechanism is executable; savings remain an engineering hypothesis. The
regressions and local example establish the documented file-boundary behavior,
not universal engineering judgment, model adherence or production acceptance.
Hashing and input validation cost time and storage. Use this extension where
stale authority, confused delivery states or interrupted work justify those costs;
keep simple legacy tasks unchanged when these controls add no useful protection.

## Adopt through the native owner

Keep the repository's existing task writer and qualification authority. Vendor
`tools/outcome_control.py` beside `tools/project_work.py`, with an upstream
revision in the normal provenance record. Add `control` to selected task JSON
records; other task fields and extensions remain compatible. Do not rewrite all
unfinished work merely to adopt the helper. Native CI must execute
`project_work.py --root . validate`: it checks controlled records even after a
direct JSON edit, including an attempted `status: done` shortcut. A controlled
record fails when the companion validator is absent. In the existing frontier,
declare the adoption boundary with the [required-control policy](../../schemas/outcome-policy-v1.schema.json):

```json
"controlPolicy": {"schema": "outcome-policy/v1", "requiredTasks": ["RESULT-1"]}
```

A required task cannot delete its `control` extension and pass as legacy. Unknown
IDs, malformed policy, missing required records and missing helper fail closed.
Repositories without a policy keep legacy compatibility. The trusted owner must
protect this frontier policy and the native CI invocation through existing review
and permissions; deleting the policy itself is an authority change the helper
cannot authenticate. This is native configuration, not a second task store.
The general task view stays read-only.

The companion and native caller are trusted code. These gates verify consistency
and file identity; they cannot authenticate the human who edits a JSON file,
grant filesystem permission, prove that a named expert reviewed something or
prevent a privileged author from replacing both policy and evidence. The owner
must protect authorization and its native writer through existing review and host
permissions. A malicious same-user process can still race filesystem checks.
These helpers reject detected changes; they are not a filesystem snapshot or a
transaction against uncooperative writers.

## Authority and source identity

The versioned [control schema](../../schemas/outcome-control-v1.schema.json)
is the `control` extension, not a replacement task schema. Its fields are:

- `authorization`: revision, owner, non-goals, invariants, decision rights,
  allowed and denied edit scopes, required capability policies and all five claim
  policies. Paths are exact files or directory prefixes, with no glob syntax.
  A denied prefix wins over an allowed prefix.
- `assignment`: actor, authorized event rights, `authorityDigest`, `sourceDigest`
  and `conditionsDigest`.
- `source`: a nonempty file manifest. Each reference is
  `{ "path": "src/result.txt", "sha256": "<64 lowercase hex digits>" }`.
- `conditions`: owner-selected environment/consumer facts that affect evidence.
- `claims`, `decisions` and `wip`: the current claims and retained history below.

`authority_digest(task)` hashes canonical JSON containing task ID, outcome,
acceptance, the **entire authorization**, and WIP limits/exceptions. A changed goal, criterion,
applicability, reviewer policy or permission invalidates an assignment even if
its revision string stays unchanged. `source_digest(manifest)` hashes the
path-sorted manifest. `digest(conditions)` binds the selected conditions.
Canonical JSON sorts keys, uses compact separators and rejects NaN/Infinity.
This is a source-set identity: do not include the evidence envelope itself in
its source manifest or bind proof to a commit that contains that proof.

The helper reads actual file bytes and rejects missing files, altered hashes,
symlinks, duplicate source paths, normalized-path violations, absolute paths,
backslashes and parent escapes. Each file is limited to 4 MiB. Source coverage
remains an owner decision: a correct hash of an incomplete manifest does not
prove coverage of an entire product. Version 1 supports checked file manifests,
not opaque external immutable source identities. Export selected external bytes
through the native owner or keep that external acceptance gate open.

## Independent delivery claims

Declare each of `implemented`, `verified`, `integrated`, `available` and
`accepted` separately in `authorization.claims`. Each policy declares:
`applicable`, an explicit `reason`, an owner-selected `scenario`, `prerequisites`, required `classes`
(`mechanical`, `expert`, `human`), authorized `producers` and `reviewers`, and
`loadedRequired`. Optional `maxAgeSeconds` is an owner freshness requirement;
there is no universal TTL. Policies cannot contain prerequisite cycles or point
to an inapplicable prerequisite. An owner can require acceptance independent of
availability, or give those claims different evidence classes.

Each current claim has `state: open|satisfied|not-applicable` and an `evidence`
array. An inapplicable claim must use `not-applicable` with no evidence; an
applicable claim cannot skip itself. `satisfied` requires satisfied prerequisites
and evidence covering **every** required class. A `done` task requires every
applicable claim satisfied and no pending feedback decision. Keep old evidence
as immutable files and references in decision history; do not rewrite a prior
acceptance record to match a new result. Open-claim evidence is hash-checked
history and never supports a claim.

A referenced [evidence envelope](../../schemas/outcome-evidence-v1.schema.json)
is JSON with `schema: outcome-evidence/v1`, exact `claim` and authorized
`scenario`, authority/source digests, exact
`conditions`, class, producer, reviewer, aware `observedAt`, `status` and `native`.
A receipt for one claim/scenario cannot satisfy another. A claim requires `status: passed`, a nonfuture observation, an unexpired optional
`expiresAt`, and any policy max-age. Conditions, class or source mismatches fail;
an expert or human receipt is not silently upgraded from a mechanical one.

`native` requires `completed: true`, `pass: true`, `errors: []` and actual
`candidateDigest`; a loaded-source claim additionally requires `loadedDigest`
equal to the source digest. An exit code alone is deliberately insufficient.
The native producer must derive these fields from the relevant positive oracle
and actual loaded candidate. A helper cannot distinguish a fabricated receipt
from truthful bytes. Keep arbitrary diagnostics outside product acceptance;
only owner-authorized proof for the applicable claim belongs here. Runtime
observation/retirement receipts can be retained as hashed supporting artifacts;
they are not automatically acceptance evidence.

## Native entry gates and WIP

The CLI uses repository-relative task paths:

```sh
python3 tools/outcome_control.py --root . --task work/tasks/RESULT-1.json digest
python3 tools/outcome_control.py --root . --task work/tasks/RESULT-1.json validate
python3 tools/outcome_control.py --root . --task work/tasks/RESULT-1.json gate pre-write --request /path/to/request.json
```

`check_gate(task, root, event, request, now=None)` returns an error list; an
empty list means the declared preconditions passed. Events are `start`, `resume`,
`pre-write`, `pre-integration` and `pre-completion`. A request follows the
[gate schema](../../schemas/outcome-gate-v1.schema.json): authority digest,
assigned actor, purpose (`admission`, `reduction`, `recovery`), requested edit
paths, capability observations and projected `wipAfter`. All gates check current
assignment, source bytes, event rights and explicit edit scope.
Pre-integration also requires applicable implemented/verified claims;
pre-completion requires all applicable claims and reconciled feedback.

Authorization `requiredCapabilities` declares objects with `name`, repository-
relative directory `scope` and trusted native `producer`. Each supplied request
capability has that name, `status: available` and a hashed reference to the real
`runtime-control/v1` capability receipt from `tools/control_runtime.py`. The
runtime request must include `authorityDigest`, `conditionsDigest` and `producer`
in addition to its scoped permission observation and `authorizationRevision`.
The delivery gate requires the receipt's current authority and conditions,
authorization revision, exact absolute scope resolved from the owner-selected
repository path, expected producer, `authorization: allowed`, `probe: passed`
and `effective: observed-writable`. A sidecar saying only available is not proof.
Every required capability must be present; undeclared/duplicate observations,
denied/unknown results, future timestamps, probe errors and mismatches fail.
Successful probing never overrides permission denial. Version 1 has no capability
TTL: change conditions or collect a new native observation when the operating
environment changes. This runtime probe proves writable scratch capability only;
other capabilities need an owner-specific future adapter rather than relabeling
this probe as proof of installation, service health or product behavior.

WIP counts unresolved assumption IDs, unintegrated change IDs, unverified claim
IDs and unreconciled experiment IDs in the four `wip.items` arrays (`assumptions`,
`changes`, `claims`, `experiments`). The owner declares any limits; there is no
universal quota. Admission fails when current or projected counts exceed a
limit. A time-bounded exception needs the authorization owner's name, category,
limit, aware expiry and reason. Expired exceptions do not help. Reduction and
recovery may proceed above a limit, but projected IDs must be subsets of the
existing IDs, so relabeling new work as reduction fails. Retain limits, history
and exceptions during handoff. `overheadSeconds` is measured nonnegative seconds
or `null` for unknown, never an invented savings estimate. Nonfinite numeric
policies/overhead are rejected. Limits and exceptions bind authority; changing
them requires renewed assignments and evidence.

The caller must pass the actual planned paths and WIP projection, run gates
before effects, and bind its native write to the checked task bytes using its
existing lock/compare-and-swap route. Gates themselves never write tasks. The optional reconciliation command below
binds a state update to the checked canonical task; a separate source edit or
external effect still needs the native owner's gate/write binding. For source edits, gate against the current manifest first, then have the native
writer apply the planned bytes, regenerate the source manifest and assignment,
reopen affected claims and renew the latest decision's input binding in its next
record. Collect new proof before satisfaction. The intermediate changed source
correctly fails validation until this native update is complete. A false request cannot
be recognized without the native caller's actual write set. Native validation
still catches stale evidence or direct unsupported done transitions.

## Optional canonical-task reconciliation

Use the existing native writer when it already provides equivalent preservation
and concurrency checks. Otherwise the optional reference writer is:

```sh
python3 tools/outcome_control.py --root . --task work/tasks/RESULT-1.json reconcile --expected-sha256 <current-task-file-hash> --proposal /path/to/proposed-task.json
```

`reconcile(root, task_path, expected_sha256, proposal)` acquires an exclusive
sibling `.outcome.lock`, checks exact current bytes under that lock, and validates
the complete proposed task against actual source/evidence. It requires unchanged
task ID, authorization digest and dependency contract. It preserves unknown
existing top-level extensions, task evidence/history prefixes, WIP history and
prior decision records. Only the final pending decision may gain its observed
effect and change dispatch state; original inputs cannot be rewritten. A changed
source manifest/assignment and reopened claims can therefore reconcile a stale
post-edit task without demanding that its obsolete source proof first pass.

For unexpected source corruption, the recovery gate deliberately rejects stale
source/evidence too. First prepare a truthful same-authority reconciliation:
record the **actual observed bytes** in the source manifest, reopen affected
claims (retaining their old hashed evidence as open-claim history), reopen a done
task and refresh the assignment. If decisions exist, close any pending prior
decision with hashed failure-observation evidence and append a recovery decision
bound to the actual current inputs; preserve the old decision identities. Apply that proposal with the expected current task hash. This
records the failure; it does not bless the damaged source as a passing product.
The full `pre-write` gate with purpose `recovery` can then pass against that
truthful current state before repair. Repair only the authorized paths, CAS-
reconcile the repaired manifest/assignment, and collect fresh claim proof before
completion. If protected authorization changed, use the owner route instead;
recovery does not widen permissions or turn stale evidence into passing proof.

The writer rechecks current bytes immediately before atomic replacement and
reads back the new task. It returns `taskDigest`. A stale expected hash, lock
contention, unsupported done claim, lost history, symlink target, altered WIP
policy or authorization change fails closed. Proposal files are data; no command
is executed. The existing native source/effect caller must still enforce the
gate's actual planned scope and WIP projection. This command reconciles state
within authorization; owner authorization changes use the separately reviewed
native route. All cooperating writers must respect the sibling lock. An
interrupted process may leave a lock; the owner must verify that no writer is
active before removing it. The helper does not break stale locks automatically.

## Feedback, then the next batch

`control.decisions` is retained inside the canonical task. A material decision
records `id`, `owner`, `authorityDigest`, `sourceDigest`, `conditionsDigest`, `trigger`, current `constraint`, `action`, `expected`,
`reconsider`, related hashed `evidence`, `effect` and explicit
`state: continuation|blocked|stopped|complete`. Triggers cover result, goal,
capability, repeated-failure, resume and completion. Coalesce unchanged events;
there is no per-command record requirement.

An `effect` is initially null, then records the exact `decisionId`, observed
behavior, `matchesExpected: true|false`, `followUp` and a nonempty array of hashed
result `evidence`. Text claiming success alone does not close the loop. The
latest decision must bind current authority and inputs; earlier reconciled
decisions retain their original identities and evidence as history. A negative finding can justify an
investigation; it is not forced into success. A pending prior outcome blocks a
new decision and admission batch, while reduction/recovery remains available
to finish the pending action or reconcile it. Completion cannot leave it pending.
The native writer appends the new pending decision only after the admission
gate, together with the new work; it reconciles that decision before the next
batch. It must also ensure stopped/blocked decisions control actual dispatch;
the gate rejects admission after a blocked/stopped latest decision; it does not
schedule workers. Recovery/reduction can reconcile that state.

## Consistent checkpoints and safe recovery

```sh
python3 tools/outcome_control.py --root . --task work/tasks/RESULT-1.json checkpoint --destination /durable/new-checkpoint
python3 tools/outcome_control.py --root . --task work/tasks/RESULT-1.json resume --checkpoint /durable/new-checkpoint --destination /owned/new-recovery
```

Checkpointing validates the task, collects its complete bytes and all referenced
source, claim and decision-evidence bytes, reads back the collected hashes,
rechecks live inputs and publishes the snapshot under a new outside directory.
An interrupted collection does not publish partial bytes. The returned digest
identifies the [manifest](../../schemas/outcome-checkpoint-v1.schema.json).
The output layout is `<checkpoint>/snapshot/{manifest.json,files/...}`.
Keep that directory in owner-approved durable storage outside the disposable
source tree; the helper does not infer storage durability or authorize deletion.

Resume verifies the full snapshot and its task/evidence relationships and
requires the **current canonical task bytes** still equal the checkpoint task.
A changed authorization at the same revision, new source manifest, altered task
or damaged snapshot rejects stale recovery. Source files themselves may have
been removed; retained bytes still restore. Recovery publishes only under a
new destination as `<destination>/restored/...`; it refuses every existing
destination and never overwrites live work. This deliberately stricter version 1
route does not merge divergent work or restore into an existing equivalent tree.
After restore, execute the normal resume gate against current authorization and
native capability observations before continuing engineering work. Preserve and
reconcile changed current work through the existing owner, then create a fresh
checkpoint; do not force an old snapshot over it.

Tests simulate interrupted publication, missing source, corrupt bytes and stale
resume. They establish process-interruption behavior, not power-loss durability,
transactional snapshots against adversarial writers or a full host disaster
recovery drill. Keep checkpoint paths nonsymlinked and access-controlled.

## Verification and revision

Run the [executable local example](../../examples/outcome-control/README.md),
`python3 -m unittest discover -s tools/tests -p 'test_outcome_control.py'` and
native `make check`. The suite includes direct done edits, missing companion,
stale same-revision goals, wrong loaded identity, false positive completion,
class/expiry/condition mismatches, denied scope after a positive probe, WIP
reduction and false reduction, unreconciled decisions and interrupted/stale
recovery. A healthy two-claim local task is the low-overhead contrast.

Revise or scope the control when a real supported-owner trial shows excessive
recording overhead, omitted decision-bearing inputs or inadequate native
binding. Report failed/unfinished attempts, rescue/rework, complete feedback and
lead intervals and control overhead separately. Passing these regressions does
not establish those empirical savings or human acceptance of another product.
