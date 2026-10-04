# Cost-aware delegation: parallelism must earn explicit complexity

Subagents are useful. They also duplicate model calls, context, tool use, and coordination. The correct policy is **not** "never delegate" and it is **not** "single agent is always best."

Platform defaults are a baseline for unconstrained choices, not permission to inherit worker cost settings. The explicit dispatch contract below takes precedence over general advice to preserve defaults, reuse context or select a stronger specialist.

The broader decision order—deterministic operation → cheapest capable worker → stronger reasoning only at uncertainty boundaries—is summarized in the [efficiency control plane](../principles/efficiency-control-plane.md). Worker escalation always remains within the dispatch ceiling.

## Named model and effort policy

Reviewed **2026-10-04**. These are explicit repository operating defaults, not a universal optimum, a native Codex allowlist, or measured savings. No additional policy file or custom-agent installation is needed. Stricter owner constraints take precedence. Validate support in the live client/account once per run; do not silently substitute a new model when a named choice is unavailable.

| Assignment | Deliberate selection | Boundary |
| --- | --- | --- |
| Exact inventory, formatting, known tests, structured filtering | Deterministic tool | No worker just to run a known command |
| Routine extraction, classification, structured summary, small explicit edit or established-rubric check | `gpt-6-luna` / `low` | Preserve evidence and required instructions |
| Focused implementation, tests against a clear contract, localized diagnosis or review needing judgment | `gpt-6-luna` / `medium` | Normal coding-worker starting point |
| Same bounded problem requiring deeper edge-case reasoning or hypothesis checking | `gpt-6-luna` / `high` | State the particular reasoning need; do not raise effort for a large batch merely because it is large |
| Ambiguous cross-boundary implementation, complex research/tool use, or synthesis exceeding Luna's demonstrated/expected capability | `gpt-6.1-sol` / `medium` | Normal main coding/orchestration choice; worker use needs a task-specific capability reason |
| Difficult coupled debugging, consequential correctness review or deeper analysis | `gpt-6.1-sol` / `high` | A specific unresolved decision, not a blanket reviewer setting |
| Hardest owner-led planning or exceptional maximum-intelligence decision | User-selected `gpt-6-astra`, effort chosen for that planning task | Never an autonomously dispatched worker; hardest planning may justify High, ordinary planning need not use Astra |

**Allowed autonomous worker pairs:** Luna at `low`, `medium` or `high`; Sol at `medium` or `high`. **Excluded:** Astra, other unapproved models, and `xhigh`, `max` or `ultra` worker effort. This replaces the undefined word "premium" and the earlier Medium-only ceiling. A coordinator can intentionally escalate to an allowed Sol/High pair without asking again; it cannot add models or raise the ceiling on its own.

Choose **model and effort jointly** for the actual goal. A focused assignment usually needs less reasoning than orchestration, but small scope can still contain a hard semantic decision. More files, visual input, independence or a "reviewer" title do not establish that need. An observed failure or a concrete explanation of anticipated coupling can justify escalation; do not purchase a doomed cheap attempt merely to tick a box. Missing instructions, tools, data, permissions or a broken test harness are not automatically model-capability failures. After an accepted decision, return routine implementation/checking to Luna or exact tools.

A rough **80/20 Luna/Sol assignment mix** and, among Medium/High assignments, roughly **80/20 Medium/High** can be useful review expectations. Low should displace Medium whenever adequate. They are not quotas, minimum allocations, workload partitions or spending caps. Do not create tasks, force weak execution, or add Sol/High work to satisfy a ratio. Investigate a persistent expensive skew in the existing run record; acceptance and total cost decide whether it is justified.

### Evidence and economics

OpenAI's [GPT-6 practical guide](https://openai.com/index/practical-guide-building-gpt-6/) distinguishes focused Luna work, complex Sol work and hardest Astra reasoning; it associates Low with routine work, Medium with judgment and High with deeper analysis. Its general Codex advice is to start from the model's default and adjust to the task.

The [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) and [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) API pages list Medium as their default. The separate [Codex subagents guide](https://learn.chatgpt.com/docs/agent-configuration/subagents) recommends High as an explicit Luna starting setting and Low for Astra. This repository deliberately tries Luna Medium/Low for bounded work; that is an economy policy requiring acceptance checks, not a claim about Codex's universal default. [Astra's model page](https://developers.openai.com/api/docs/models/gpt-6-astra) documents its supported effort levels.

Standard API text prices on the review date, per million tokens:

| Model | Input | Cached input | Output |
| --- | ---: | ---: | ---: |
| Luna | $0.10 | $0.01 | $0.50 |
| Sol | $2.00 | $0.10 | $10.00 |
| Astra | $10.00 | $1.00 | $50.00 |

These rates do not convert subscription credits, include all service/tool/long-context charges, or predict token counts at a given effort. At equal uncached input/output volumes, Sol's listed rates are 20 times Luna's. A hypothetical 80 Luna / 20 Sol mix with equal tokens per assignment would therefore put about 83% of worker model spend in Sol. Assignment share and spending share are different. Likewise, changing a Luna main agent to Sol is a capability upgrade, not intrinsically a cost reduction; measure the whole accepted workflow, including coordinator usage, caching, retries and repairs.

## Executor-routing checkpoint

Before a substantial batch of reading, editing, or validation, choose who performs it. A one-line choice in the existing plan is enough; this is not a new planning document or a pause for approval.

Reading a complete corpus does not ordinarily require the orchestrator to ingest every byte: independent readers can cover defined portions, preserve contradictions and cite original evidence. Instructions that explicitly require the main agent's own read still take precedence. Do not substitute a summary for required source coverage or let a worker silently omit difficult material.

Choose an outcome-sized assignment, not one agent per command or document. Keep an immediate decision local when the coordinator is capable and transfer would cost more than it saves; otherwise route the bounded decision to an allowed capable worker and start useful independent work. For a large routine batch retained locally, state the actual reason: required direct inspection, no compliant authorized worker/tool, coupling, transfer overhead, or demonstrated worker unreliability. "Defaults" alone does not explain ignoring an available independent split after the user requested efficient delegation.

Model choice is separate from spawning. Inspect the live models, effort levels, tools, executors and available cost/usage information, then select the cheapest adequate pair from the named policy. Reuse that inspected mapping until relevant configuration, availability or evidence changes. The policy already supplies the permitted pairs: do not refuse delegation merely because no custom allowlist file is installed. Unsupported selection or no adequate allowed pair does block that route; continue with exact tools/the authorized coordinator where adequate.

The coordinator must still be able to judge and integrate the artifact. If it cannot, preserve the unresolved requirement for an authorized decision; never buy an Astra worker or silently switch the coordinator to Astra. Reuse findings without preserving an expensive configuration merely to avoid a small handoff.

### Launch preflight

This contract applies to **every launch, fork, resume and follow-up**. Keep its receipt in the existing launch/task record; do not add a tracker or perform repeated model research.

- **Explicit selection.** Set an allowed supported model, reasoning effort and bounded context through actual launch controls or an explicitly selected inspected role. Omitted/inherited cost settings are invalid. The same model as the parent can be chosen independently and explicitly. A model name inside a prompt does not itself set the runtime model. Inspect role/config precedence and actual override exposure. In native V2 choose `fork_turns` explicitly: it defaults to `all`; `none` or a positive integer string bounds inherited history. Current V2 full-history forks can override model/effort and roles; reject a path only when its actual controls defeat selection, not from a remembered blanket limitation.
- **Intentional escalation.** Use the named policy, not an undefined price category. Luna Medium is the focused coding default; Low for routine work; Sol or High needs a concise task-specific reason. Coordinator-authorized Sol/High is within policy, not a new owner-approval gate. Keep costly judgment bounded and route down afterward.
- **Finite budgets.** Before dispatch, allocate numeric assignment and aggregate delegation limits in time or total tokens according to the workload and owner limits. Do not invent a universal numeric optimum. Include input/context and reasoning where measurable. The starter attempt limit remains one execution plus one targeted repair; workers do not redelegate. Follow-ups, replacements, retries and any explicitly authorized descendants debit the same allocations. A restart or new assignment label cannot reset them. At exhaustion, return evidence and unresolved work rather than automatically increasing spend; necessary authorized coordinator work can continue only within applicable native budgets, without claiming incomplete work is done.
- **Context and reuse.** Prefer a fresh bounded handoff. Reuse only when the worker's known model, effort, retained context and remaining budget remain appropriate for the new subtask. Reusing an allowed Sol/High worker for a routine follow-up still needs a cost justification; its previous escalation is not permanent permission. Native V2 `followup_task` has no model/effort override fields: transfer findings to a newly configured worker when downgrading. Context minimization must retain permissions, applicable repository instructions, evidence and acceptance constraints.
- **Verification and rejection.** No dispatch through unsupported or out-of-policy controls, and no continuation after a disallowed resolved setting is discovered. Record requested/resolved settings from native evidence when observable; absent telemetry is unknown, not verified compliance. Metadata visibility is not a resolved-settings receipt. Inspect a representative launch before multiplying the pattern. A mismatch stops further dispatch until corrected; post-launch inspection cannot prevent the first call's cost. Distinguish soft allocations, native exhaustion boundaries and exact billing ceilings; a required hard cap unavailable on the host blocks that path.

A compact receipt is sufficient:

```text
Outcome / scope: <bounded artifact and acceptance>
Selected model/effort: <allowed supported pair; why adequate or escalation needed>
Context: <bounded inputs or inspected compliant reuse>
Budget: <numeric assignment and aggregate limits; remaining; attempts>
Enforcement: <native exhaustion boundary / soft checkpoints / unavailable; scope and overshoot limits>
Resolved: <observed model/effort/context or unknown; native evidence reference>
```

### Native Codex configuration

The [source-backed V2 audit](multi-agent-v2.md) records the exact upstream snapshot, supported fields, inheritance and prompt interactions, coordination semantics, budgets and version limitations. Read it when configuration is the current decision, not on every assignment. Public documentation alone is not a complete feature inventory.

`[agents]` defaults and `[features.multi_agent_v2]` are complementary. Preserve an intentional V2 mode hint: it changes delegation policy independently of reasoning effort, whereas worker defaults select fallback cost settings. The updated [configuration example](../../configs/codex/efficient-local.config.toml) keeps both. Enabled V2 takes precedence over `agents.enabled = false`; disabling delegation requires resolving both controls and checking a fresh tool surface. `agents.max_depth` is V1-only, not V2 enforcement against grandchildren.

Effective model/effort precedence is **custom agent file → explicit spawn value → corresponding `[agents]` default → parent fallback**. Set both fields in selected roles and inspect personal/project overrides. With no effort supplied by spawn/defaults, explicitly selecting a model uses its default effort before custom-role overrides. In current V2, `expose_spawn_agent_model_overrides` controls model/effort schema exposure independently of `hide_spawn_agent_metadata`; the latter is not a native price-control mechanism or proof of what ran.

Merge rather than replace unrelated permissions, approvals, tools and intentional compaction settings. Do not copy private workstation configuration into this public repository. Check a fresh run's effective settings and existing role overrides before fan-out; changing a file does not reconfigure already-running workers. A custom hint is an instruction, not a runtime model assignment or allowlist.

Concurrency and context windows are not cumulative spending caps. The inspected native `features.rollout_budget` implementation is more than reminders: shared root/worker accounting can raise `SessionBudgetExceeded`. Its scope, accounting units, response-boundary overshoot and process/resume behavior are distinct from per-worker allocations and exact dollar/credit caps. Keep it optional until a task-sized limit and actual-client trial are established; do not invent keys, install an arbitrary global budget or introduce another orchestration service. See the audit's [budget boundary](multi-agent-v2.md#6-rollout-budgets-real-native-enforcement-but-not-an-exact-invoice-ceiling).

### Responses API multi-agent is a different surface

Reviewed 2026-10-04 against the [Responses multi-agent guide](https://developers.openai.com/api/docs/guides/responses-multi-agent).

The hosted beta shares the request's model and tools among agents. It therefore does **not** provide Sol-root/Luna-worker routing through `multi_agent.enabled`; no per-worker model override is documented there. Do not enable that path as an implementation of this mixed-model policy. An explicitly authorized homogeneous API workflow is a different choice; heterogeneous API work needs separately model-selected requests through an already-authorized executor, not invented hosted parameters. This hosted limitation does not prohibit mixed models in native Codex V2.

`max_concurrent_subagents` defaults to 3, covers active descendants and excludes the root; it does not cap total agents, depth or spending. Hosted collaboration calls are server-executed; applications handle ordinary function calls. WebSocket continuation can reduce tool-result waiting. Agents' contexts compact separately and automatically; `/responses/compact`, `reasoning.summary` and `max_tool_calls` are unsupported in this mode. Preserve attribution and unresolved acceptance. Apply shared-tool permission boundaries and avoid competing writes; separate context is not a permission boundary or a lower-price guarantee.

### Capability escalation and de-escalation

A 3D asset, level, or presentation assignment can warrant deeper reasoning when it couples spatial composition, navigation or camera behavior, lighting/materials, approved visual references, runtime constraints, and perceptual review. The artifact category alone is not a reason to escalate. Choose an allowed adequate pair, or keep the coupled decision with the coordinator without weakening acceptance.

Route down after the specialist or coordinator converts ambiguity into an accepted decision artifact: approved references, scene boundaries, constraints, fixtures, measurable budgets, or repeatable acceptance scenarios. Exact edits, builds, captures, and tests can then return to deterministic tools or cheaper capable workers. Re-escalate only when new evidence reopens the coupled decision; an ordinary failing check follows routine diagnosis first.

Give workers minimal context and disjoint write scopes. Workers keep logs on disk and return only results, evidence paths, validation, limitations, and unresolved decisions. The coordinator reviews decision-bearing source without replaying commands or importing logs already consumed by workers. When evidence is insufficient, request targeted worker investigation within its remaining allocation; read only excerpts needed for a coordinator decision.

Revisit the choice at integration boundaries or when actual quality, cost, rate-limit, or collision evidence changes it. Do not narrate a routing choice before every tool call. A short direct command often has less overhead than any subagent.

### Handoff and retained context

Use the return contract in [`efficient-execution`](../../skills/efficient-execution/SKILL.md). A launch handoff should make these fields explicit when they matter, in addition to the mandatory dispatch receipt:

```text
Outcome and concrete artifact:
Owned scope/files:
Constraints, permissions, and preserved invariants:
Authoritative inputs and precedence:
Acceptance: deterministic, runtime, visual, and human boundaries
Required capability within the worker ceiling:
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

The orchestrator uses the task's existing notes for current outcomes, assumptions, decisions, changes, evidence references, blockers and next actions. Read an image when visual judgment is required; inspect original source for a disputed claim; ask a compliant worker for a targeted follow-up when routine evidence is incomplete. Do not ingest the entire archive as a handoff ritual. At a phase boundary, prepare these notes for runtime-supported compaction; neither an artifact nor a shorter summary removes already-consumed history by itself.

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

Justify this when work is genuinely independent and critical-path wall time or independent review quality matters enough to pay for duplicated model usage. All workers must pass the dispatch contract and fit the aggregate allocation.

### Explicitly constraining fan-out

Justify this when observed delegation is consuming quota/rate limits, creating collisions, duplicating discovery, or producing coordination overhead that outweighs its benefit.

A hard concurrency cap is therefore a workload policy, not a universal efficiency setting or a total-spend limit.

## Red flag: orchestration as spectacle

"150 parallel subagents" is not inherently impressive or inherently wrong. For trivial tasks it is usually suspicious because each worker has fixed context/orchestration cost. For 150 truly independent expensive tasks on a critical path it may be rational within the owner's authorization and aggregate budget.

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

If a normal run already behaves well and complies with the dispatch contract, leave it alone.

If delegation is a material cost or opportunity, compare the smallest useful alternatives first (for example current behavior versus an explicit 2- or 4-way split). Stop once the operating decision is clear; do not scale to 8/16/32/150 simply to draw a curve.

Useful ratios when needed:

```text
speedup = serial_or_normal_wall_time / delegated_wall_time
token_amplification = delegated_tokens / serial_or_normal_tokens
parallel_value = speedup / token_amplification
```

These are decision aids, not universal objective functions. Quality and human attention can dominate the numeric ratio. A high subagent share of usage identifies an accounting bucket, not waste: compare total coordinator plus worker usage, setup, retries, review and repair for the same accepted outcome. Keep tokens, priced usage/credits and wall time distinct; missing model/effort attribution remains unknown.

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

Cloud delegation can be valuable for independent parallel work or when the local machine is unavailable. Local execution can exploit a permanently warm repo, dependency caches, compiler caches, indexes, and services. Neither should be declared universally cheaper: apply the same explicit worker selection and ceilings on either surface, then measure consequential workload-dependent tradeoffs.
