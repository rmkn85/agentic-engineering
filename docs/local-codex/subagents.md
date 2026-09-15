# Cost-aware delegation: parallelism must earn explicit complexity

Subagents are useful. They also duplicate model calls, context, tool use, and coordination. The correct policy is **not** "never delegate" and it is **not** "single agent is always best."

The current platform behavior is the baseline. Intervene only when the workload gives a reason.

## Executor-routing checkpoint

Before a substantial batch of reading, editing, or validation, choose who performs it. A one-line choice in the existing plan is enough; this is not a new planning document or a pause for approval.

| Work | Preferred executor when applicable | Return / acceptance |
| --- | --- | --- |
| File inventory, hashes, exact search, formatting, known command batch | Deterministic tool/script | Machine-readable result, exit status, retained logs |
| Independent source extraction, routine edits, command selection and failure triage | Bounded worker with sufficient capability; often a lower-cost model | Findings with source locations, changes, checks, failures and uncertainties |
| Coupled semantic, spatial, perceptual, or cross-boundary decision | Bounded specialist or orchestrator with the required capability | Decision artifact supported by original evidence and explicit acceptance boundaries |
| Integration | Coordinator capable of judging and reconciling the returned artifact | Accepted integration or a stated escalation |

Reading a complete corpus does not ordinarily require the orchestrator to ingest every byte: independent readers can cover defined portions, preserve contradictions and cite original evidence. Instructions that explicitly require the main agent's own read still take precedence. Do not substitute a summary for required source coverage or let a worker silently omit difficult material.

Choose an outcome-sized assignment, not one agent per command or document. Keep an immediate decision local when the coordinator is capable and transfer would cost more than it saves; otherwise route the bounded decision to a capable specialist and start useful independent work. For a large routine batch retained locally, state the actual reason: required direct inspection, no authorized worker/tool, coupling, transfer overhead, or demonstrated worker unreliability. "Defaults" alone does not explain ignoring an available independent split after the user requested efficient delegation.

Model choice is separate from spawning. Select the required capability before a model name: for example, coherent spatial synthesis, visual-reference interpretation, cross-boundary reasoning, tool fluency, or perceptual review. Inspect the models, effort levels, tools, and executors exposed in the current run, then choose the cheapest supported option likely to meet acceptance. A low-cost coordinator may dispatch a stronger specialist; the coordinator does not have to be the highest-capability model.

Do not infer availability from documentation, an earlier run, or a model family name. If live discovery is unavailable, use only a platform-supported default or report the routing choice as unresolved. Record the requested and resolved tier/capability when the harness reports them. An omitted model that inherits the orchestrator is not evidence of lower-cost delegation. Named models in dated evidence are illustrations, not stable routing interfaces or promises about future models.

The coordinator must still be able to judge and integrate the specialist's artifact. If it cannot, escalate the integration decision too. Reuse relevant worker context rather than restarting completed work just to change tiers.

### Capability escalation and de-escalation

Route up when a bounded decision combines several concerns that a routine executor is unlikely to reconcile without rework. A 3D asset, level, or presentation assignment can qualify when it couples spatial composition, navigation or camera behavior, lighting/materials, approved visual references, runtime constraints, and perceptual review. The artifact category alone is not a reason to escalate.

Route down after the specialist converts ambiguity into an accepted decision artifact: approved references, scene boundaries, constraints, fixtures, measurable budgets, or repeatable acceptance scenarios. Exact edits, builds, captures, and tests can then return to deterministic tools or cheaper capable workers. Re-escalate only when new evidence reopens the coupled decision; an ordinary failing check follows routine diagnosis first.

Give workers minimal context and disjoint write scopes. Workers keep logs on disk and return only results, evidence paths, validation, limitations, and unresolved decisions. The coordinator reviews decision-bearing source without replaying commands or importing logs already consumed by workers. When evidence is insufficient, request targeted worker investigation; read only excerpts needed for a coordinator decision.

Revisit the choice at integration boundaries or when actual quality, cost, rate-limit, or collision evidence changes it. Do not narrate a routing choice before every tool call. A short direct command often has less overhead than any subagent.

### Handoff and retained context

Use the return contract in [`efficient-execution`](../../skills/efficient-execution/SKILL.md). A launch handoff should make these fields explicit when they matter:

```text
Outcome and concrete artifact:
Owned scope/files:
Constraints, permissions, and preserved invariants:
Authoritative inputs and precedence:
Budgets: scope, attempts, variants, time or tokens when applicable
Acceptance: deterministic, runtime, visual, and human boundaries
Required capability and live requested/resolved executor:
Escalate or stop when:
Return: result, revision/scope, changed artifacts, checks, evidence, limits, open decisions
```

For 3D, level, or presentation work, include any frozen simulation/interaction behavior, approved references, target scenes or viewpoints, resource/performance bounds, and perceptual judgment that remains human-owned. Put detailed evidence in a retrievable artifact and keep the return about that artifact. For example:

```text
Result: web smoke check passed for revision <sha>, desktop viewport only.
Checks: <command>, exit 0; rendered scene and keyboard input observed.
Evidence: <artifact-relative manifest/log/capture references>.
Open: mobile layout untested; no performance or human-play acceptance claimed.
```

Keep evidence available through integration; move required durable evidence to the task's normal artifact location before temporary files are removed. Include contradictions and untested scope even when the summary grows. A successful exit alone cannot establish visual or human acceptance.

The orchestrator uses the task's existing notes for current outcomes, assumptions, decisions, changes, evidence references, blockers and next actions. Read an image when visual judgment is required; inspect original source for a disputed claim; ask the worker for a targeted follow-up when routine evidence is incomplete. Do not ingest the entire archive as a handoff ritual. At a phase boundary, prepare these notes for runtime-supported compaction; neither an artifact nor a shorter summary removes already-consumed history by itself.

### Launch-context routing

A worker launched from a parent multi-repository directory may receive the parent's instruction chain but no child-repository instructions. The child files can exist on disk, and a worker can be coached to read them, without proving that the runtime delivered them at startup. Treat stale parent-session inheritance as another possible cause: startup discovery is rebuilt per run, not retroactively refreshed by changing directories or files.

Operational decision: before relying on repository-specific guidance, check the worker's actual launch cwd and the instruction sources delivered in that run. If the child is not in the delivered chain, place concise common discovery instructions at the workspace root, launch from the child root, or use the runtime's supported project-instruction loading mechanism. A Markdown router does not itself launch or load another file. Record the observed cwd, delivered sources, and the substantive behavior; do not infer delivery from file presence or a coached read.

For behavioral regression and instruction-pressure testing, use [`../../experiments/instruction-context-adherence.md`](../../experiments/instruction-context-adherence.md). Historical delegation-specific observations are retained under [`../../references/delegation-adherence-2026-09.md`](../../references/delegation-adherence-2026-09.md), outside the normal reading path.

## Outcome-preserving delegation

For a broad transformation, partition the complete input scope into owned deliverables and explicit dispositions (synthesize, retain, merge, retire, or unresolved). Preserve exceptions and contradictions. A source inventory is not proof that the source's useful substance reached the result.

Give each worker the actual reader/user outcome, representative questions, source boundaries, expected depth and evidence needs, and disjoint write ownership. Ask for a compact handoff **about** the substantive artifact, not a compact artifact unless the user requested one. For knowledge work, useful acceptance can require the reader to make a decision, follow a worked example, understand failure cases and locate evidence without reconstructing the answer from outbound links. Do not impose arbitrary length or illustration quotas; those can become another proxy.

Review an early representative artifact before multiplying the pattern. At integration, use independent reader tasks on the deliverable itself and reconcile the whole source-to-result coverage. Structural checks remain necessary but separate. If the result is a foundation rather than the requested final product, report it as partial and continue within scope; do not relabel the foundation as complete.

A small direct edit does not need a coverage matrix or independent review. Keep coverage in the task's existing plan/evidence rather than creating a permanent second tracker.

## Two different deviations

### Explicitly increasing fan-out

Justify this when work is genuinely independent and critical-path wall time or independent review quality matters enough to pay for duplicated model usage.

### Explicitly constraining fan-out

Justify this when observed delegation is consuming quota/rate limits, creating collisions, duplicating discovery, or producing coordination overhead that outweighs its benefit.

A hard concurrency cap is therefore a workload policy, not a universal efficiency setting.

## Red flag: orchestration as spectacle

"150 parallel subagents" is not inherently impressive or inherently wrong. For trivial tasks it is usually suspicious because each worker has fixed context/orchestration cost. For 150 truly independent expensive tasks on a critical path it may be rational.

Ask:

- what work is actually independent?
- what is the serial critical path?
- what context does each worker duplicate?
- what wall-clock speedup was achieved?
- what token/quota amplification occurred?
- did quality improve?
- would deterministic local tooling have done the trivial parts without any model calls?

The burden of justification grows with explicit fan-out.

## Measure only when the answer is uncertain

If a normal run already behaves well, leave it alone.

If delegation is a material cost or opportunity, compare the smallest useful alternatives first (for example current behavior versus an explicit 2- or 4-way split). Stop once the operating decision is clear; do not scale to 8/16/32/150 simply to draw a curve.

Useful ratios when needed:

```text
speedup = serial_or_normal_wall_time / delegated_wall_time
token_amplification = delegated_tokens / serial_or_normal_tokens
parallel_value = speedup / token_amplification
```

These are decision aids, not universal objective functions. Quality and human attention can dominate the numeric ratio.

## Delegation versus deterministic tools

Before creating a worker for a trivial deterministic operation, ask whether a local program can perform it exactly:

- search/index lookup;
- file inventory/hash;
- path rename;
- formatting;
- generated-code refresh;
- compilation/type checking;
- test selection from a known dependency graph;
- log filtering/summarization by structured fields.

A deterministic tool often costs effectively zero model tokens and scales better than cloning model context across workers.

## Local versus cloud workers

Cloud delegation can be valuable for independent parallel work or when the local machine is unavailable. Local execution can exploit a permanently warm repo, dependency caches, compiler caches, indexes, and services. Neither should be declared universally cheaper: keep the normal choice unless a real workload makes the tradeoff material, then measure that workload.
