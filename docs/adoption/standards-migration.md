# Start and migrate with engineering standards

Use this procedure when a project first adopts the [specification contract](../specifications/README.md), when approved guidance changes, or when an active task reveals a relevant gap. Preserve the [newcomer contract](newcomer-contract.md), local authority and the assigned product outcome. This is an incremental adoption route, not permission for a repository-wide rewrite.

## When to adopt or migrate

| Situation | Action now | Work that does not follow automatically |
| --- | --- | --- |
| New project or new component | Select the relevant profile, state the first useful contract, choose native checks and build one verified vertical slice | A compliance platform, every standard or a large specification before useful work |
| Active task with unfinished changes | Checkpoint owned work, read the approved update and reassess the affected contract before the next relevant write | Discarding work, switching branches or restarting the entire project |
| Existing component being changed | Compare its actual behavior/constraints to the new obligations; characterize relevant legacy behavior and close in-scope gaps | Reformatting or redesigning unrelated modules |
| Known material safety, security, data-integrity or accessibility violation | Prevent the dependent harmful action; repair in scope or escalate the exact unresolved risk through its owner | Hiding an immediate problem in an indefinite migration backlog |
| Stable untouched legacy area | Preserve behavior; record only material known debt with an owner and review trigger | A big-bang conversion or inventing defects without evidence |
| New standard edition or changed guidance | Review applicability and semantic differences through the project's normal update route | Automatic adoption, altered legal claims or fetching every upstream source on every task |
| Formal assurance required by product or contract | Obtain the required edition, expertise and evidence before the relevant acceptance/delivery claim | Self-certifying from a summary or substituting a convenient newer edition |

A request to adopt newer engineering guidance authorizes the bounded guidance integration, not unrelated product changes or a waiver of stronger local requirements. Ordinary in-scope fixes need no additional approval. Separate conflicting product decisions from implementation choices the agent is already authorized to make.

## New work

Read the local entry and approved profile. Identify purpose, relevant consumers, trust boundaries, state/effects and the existing delivery route. Use [precise technical language](../specifications/technical-language.md) and the smallest adequate requirement/mechanism/check record. For a small task this can live in the existing issue or test.

Reuse native components, formatter, type checker, tests, CI and diagnostics. Add only missing checks that protect a real obligation. Establish expected behavior before implementation; include the consequential failure or boundary case. Ship and validate a coherent slice rather than treating documentation volume as progress. Resolve material uncertainty using the [specification contract](../specifications/README.md#resolve-uncertainty-without-inventing-requirements).

## Existing and active work

### 1. Preserve identity and owned work

Record the current task, source revision, dirty-state qualification, active checks and next action in the existing continuation record. Preserve unrelated edits and coordinate with other writers. Use the project's authorized checkpoint/commit route; do not blindly commit other agents' work or sensitive files. A checkpoint is not permission to reset, clean, delete, force-push or switch branches.

Read the approved upstream revision through an authorized checkout or connector. Record the exact commit used. A request to use latest means resolve the upstream head now and pin the reviewed snapshot, not trust a stale checkout or continually move the target during implementation. Keep stricter applicable local/product rules; reconcile contradictions rather than silently choosing the easier rule.

### 2. Compare three sources

Compare the previously adopted guidance, the newly reviewed guidance and current local adaptations. When the previous snapshot is unknown, say so and use the actual local instructions as the migration baseline. Do not invent provenance or overwrite local changes with an upstream copy.

Then compare desired behavior against current code and tests on the affected path. Characterization tests capture observed behavior; they do not make a known bug authoritative. Preserve legitimate compatibility until a change is explicitly accepted. Distinguish a new requirement from clearer wording of an existing one.

### 3. Classify and bound the delta

Use the existing task/provenance record rather than a new mandatory tracker. Retain only decision-bearing fields:

```text
Source: prior adopted revision (or unknown) -> reviewed upstream commit
Scope: affected local instructions, components, consumers and work in progress
Profile: applicable standards/editions and any local terminology convention
Delta: wording-only | equivalent mechanism | behavior change | assurance gap
Evidence: current checks and their limits; evidence invalidated by this delta
Disposition: adopted | already equivalent | deferred | blocked | not applicable
Remaining gap: consequence, owner, mitigation and concrete review/retry trigger
```

Not applicable needs a real scope reason. Deferred requires a bounded reason and review trigger; it cannot excuse a new in-scope violation or known immediate harm. Already equivalent requires evidence of equivalent behavior and delivery, not a matching file name. Adopted identifies the guidance integration; verified product properties require their separate results.

### 4. Migrate in coherent increments

Separate semantic-preserving language changes from behavioral changes. Preserve actors, obligation strength, conditions, units, exceptions, identifiers and protected state. Do not rename public fields, alter accepted thresholds or tighten client preconditions as a prose cleanup.

For a behavior change, update the authoritative requirement, preserving mechanism and dependent tests together. Test the old and new consumer boundaries where compatibility matters. Data/schema changes need an authorized plan for old/new versions, interrupted execution and data preservation. Rehearse recovery on suitable non-production fixtures; do not claim rollback can reverse an irreversible external effect. A missing restore or authorization prerequisite blocks that effect, not unrelated work.

Enable new mechanical checks using the project's normal commands. A scoped existing-debt baseline may prevent new violations while known unrelated debt is resolved, but must retain scope, owner and exit trigger. Do not disable checks, raise thresholds or suppress failures merely to make migration green. Retire superseded duplicate guidance only after the replacement routes and required resources are verified.

### 5. Deliver instructions to the actual agents

Updating a file does not reload a running host or worker. Explicitly read the revised local entry in the active session. Pass the affected contract and revision to active workers before their next relevant write. Confirm which revision each relevant context received; receipt is not evidence of behavioral adherence.

Where the host cannot refresh a context, checkpoint and restart only the affected work at a supported safe boundary. Preserve completed work and reconcile outputs produced under the prior contract. Do not invent a reload command or assume every host inherits the same files. Keep the changes in the local approved instruction route so future sessions receive them without this chat.

### 6. Verify and continue the original task

Run focused checks on the changed contract and broader acceptance at the existing integration boundary. Validate an ordinary representative task with no extra standards reminder when possible. Keep human/assistive-technology, real-host and independent-agent checks explicitly open when they have not run. Use the [behavioral probes](../../experiments/specification-integrity.md) for adoption evaluation, not as a new product backlog.

Record source revision, local mapping/adaptations, actual results and remaining gaps. Resume the original product task in the same authorized run when unblocked. A standards update is not a reason to stop at a documentation report, nor to claim all legacy areas were migrated.

## Maintenance and rollback

Review the profile when affected behavior changes, an incident exposes a gap, required tooling/standards change, or the owner requests an upgrade. Reuse valid checks and stable local copies between those triggers. Do not fail a build merely because upstream released another commit.

If an adoption mechanism causes regressions, revert or repair that coherent change through the normal source-control route while preserving evidence and local edits. Reverting an instruction file does not remove safety obligations or undo product data changes. Report the remaining contract and risk explicitly.

## Active-agent handoff

Use this compact prompt, substituting the reviewed revision when known:

```text
Adopt the reviewed update from rmkn85/agentic-engineering.
Read its AGENTS.md, docs/agent-corpus/README.md and
 docs/adoption/standards-migration.md. Resolve and record the upstream commit.
Preserve current work and stronger local rules. Apply the relevant language,
requirements, implementation, evidence and accessibility contracts to your
active task; migrate incrementally, not by a blanket rewrite. Refresh the
local instructions and affected worker contexts. Run the project's native
checks, report remaining gaps honestly, then continue the original task.
```

The source repository can make this route available; only a real host/project trial can show that another running agent received and applied it. Do not claim a cross-project rollout from an upstream commit alone.
