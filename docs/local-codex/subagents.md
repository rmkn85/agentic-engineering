# Cost-aware delegation: parallelism must earn explicit complexity

Subagents are useful. They also duplicate model calls, context, tool use, and coordination. The correct policy is **not** "never delegate" and it is **not** "single agent is always best."

Treat a saved app model selection as session/UI state, not an executor-routing plan. Select the executor, model, effort and useful agent count for the next outcome regardless of that selection. Changing a default cannot replace this decision. The explicit dispatch contract below takes precedence over general advice to preserve defaults, reuse context or select a stronger specialist.

The broader decision order—deterministic operation → cheapest capable worker → stronger reasoning at uncertainty boundaries—is summarized in the [efficiency control plane](../principles/efficiency-control-plane.md). Select for the next decision, not the most expensive phase in the task's history.

## Named model and effort policy

Routing policy reviewed **2026-10-25**; the evidence/prices below retain their original review date, **2026-10-04**. These are explicit repository operating defaults, not a universal optimum, a native Codex allowlist, or measured savings. No additional policy file or custom-agent installation is needed. Owner constraints apply, subject to higher-priority runtime rules. Validate support in the live client/account once per run; do not silently substitute a new model when a named choice is unavailable.

| Assignment | Deliberate selection | Boundary |
| --- | --- | --- |
| Exact inventory, formatting, known tests, structured filtering | Deterministic tool | Keep short commands local; a bounded worker may supervise long/noisy runs for context isolation |
| Usage monitoring, Git staging/committing/publishing, CI-log triage, routine extraction, small explicit edit or established-rubric check | `gpt-6-luna` / `low` when model supervision is needed | Use deterministic commands first; route a discovered substantive defect separately |
| Focused implementation, tests against a clear contract, localized diagnosis or review needing judgment | `gpt-6-luna` / `medium` | Normal coding-worker starting point |
| Same bounded problem requiring deeper edge-case reasoning or hypothesis checking | `gpt-6-luna` / `high` | State the particular reasoning need; do not raise effort for a large batch merely because it is large |
| Sustained engineering, cross-boundary implementation, reasoning with substantial execution, or synthesis beyond a bounded Luna assignment | `gpt-6.1-sol` / `medium` | Normal main coding/orchestration and substantial engineering-worker choice |
| Difficult coupled debugging, consequential correctness review or deeper analysis | `gpt-6.1-sol` / `high` | A specific unresolved decision, not a blanket reviewer setting |
| Extremely creative or complex decisions: demanding graphics, advanced architecture, or comprehension of difficult academic work | `gpt-6-astra` / `medium`, or `high` for the specific coupled reasoning need | A bounded specialist outcome; hand implementation, tests, publication and monitoring back to the appropriate executor |

**Baseline pairs:** Luna at `low|medium|high`, Sol 6.1 at `medium|high`, Astra at `medium|high` for the demanding decisions above. These choices do not require a new approval prompt. Do not default an entire graphics, research or engineering project to its strongest specialist. `xhigh|max` requires explicit scoped owner authorization. **Ultra is forbidden except under the current explicit instruction to exhaust allowance before reset**, as defined below. A model's availability, default effort or a worker's old configuration grants no exception.

### Ultra and allowance-bound work

An Ultra exception requires the owner to explicitly request exhausting allowance **before a reset** in the active assignment. "Use Astra", "maximize usage", an expired/unrelated assignment's exception, or merely having remaining credits is insufficient. A valid scoped authorization survives resume until its stop boundary; do not ask for it again. Keep routine supervision on tools or Luna/Low even during that exception. Record the relevant allowance window, baseline/reset identity, deadline and stop conditions in the existing task state before starting.

Stop allowance-bound work on the **first observed** owner deadline, exhausted included allowance (100% used in a required window), or reset of the relevant window. A reset ends the old authorization; it does not replenish that assignment's budget. `ordinaryUsageAllowed=true` or available paid credits does not authorize credit spending after exhaustion. Unknown usage must not be treated as remaining allowance. Preserve state and cancel affected agents and outstanding operations through supported controls; report any cancellation that cannot be confirmed. A later reset announcement is not authorization to resume an old backlog.

Use native exhaustion/cancellation controls where available. Poll through deterministic tooling, with Luna/Low only when interpretation or supervision is necessary; never devote an Astra/Sol inference loop to watching counters. Bound the polling interval and account for in-flight work. This instruction is not a hard spending cap and cannot guarantee cancellation between observations. If the owner requires a hard cap the host cannot enforce, do not start that path.

### Usage reasonableness checkpoints

Use the native Codex usage API when exposed (`get_usage_limits` in the desktop app) from time to time during substantial work. Take a baseline when practical; revisit at meaningful progress/resource checkpoints, after unexpected retries, context growth or fan-out, and on resume when the last sample is stale. Do not turn this into an inference loop or a mandatory call per operation. Tools or Luna/Low collect a compact snapshot; the coordinator assesses it alongside the work. Use the existing task/steering record, not a second tracker.

Compare depletion and elapsed time in the **same allowance window** with the rough expected work, accepted progress and remaining plan. Check the reset horizon and current authorization. Use the API's named limit buckets where available, keep overlapping/legacy views distinct, and treat absent values as unavailable. One snapshot cannot establish a depletion rate. Resets break simple subtraction; coarse, delayed or unchanged counters do not prove that work is free. There is no universal percentage, polling cadence, target burn rate or requirement to use spare allowance.

If depletion is unexpectedly fast, check actual model/effort selections, retained input, retries, duplicated investigation, review and concurrent agents against the forecast. Also consider other account activity, shared pools, reporting lag and possible platform/accounting faults; the API reports shared account limits, not task-level attribution. Correlate native usage/evidence where available and keep the cause unknown when unsupported. Do not diagnose waste or a vendor fault from a percentage alone, or spend a large probe merely to investigate spending.

Steer within authority: remove waste, reduce concurrency, route the next phase down, slow down, or stop costly work while reconciling an unexplained anomaly. Preserve acceptance and unfinished state. If acceleration would be useful, explain its expected benefit, extra resource use, uncertainty and reset horizon, then obtain owner approval **before materially increasing the spending pace**, unless that acceleration is already explicitly authorized in scope. A nearby reset is a reason to discuss the tradeoff, never automatic permission for fan-out, higher effort, Ultra or paid credits. These qualitative reviews supplement the owner's hard stop conditions; they do not create a new fixed budget or override one.

### Explicit owner exception: designated co-developer

Use the owner's explicit authorization as the contract for designated substantial,
independent parallel outcomes, including concurrency, descendant limits and any
specifically authorized model/effort exception. Co-developer autonomy alone does
not authorize higher effort or Ultra. Ordinary workers use the baseline pairs.
Authorization persists within its scope; do not ask again for each qualifying lane.

Declare the sustained outcome, owned paths, shared interfaces, genuine resource
limits and integration point. An authorized epic owner is an orchestrator for
that outcome: it may delegate scoped work and resolve routine blockers without
waiting for the root's next instruction. Further orchestrating descendants require
explicit authority and a separable outcome; ordinary execution workers may not
create descendants. Every generation retains the same applicable permissions,
model policy and genuine aggregate limits. The root continues independent work
and owns cross-epic integration. Small extractions and routine reviews do not
qualify as epic lanes. Use supported collaboration tools, not nested clients or
permission workarounds.

Choose **model and effort jointly** for the actual goal. A focused assignment usually needs less reasoning than orchestration, but small scope can still contain a hard semantic decision. More files, visual input, independence or a "reviewer" title do not establish that need. An observed failure or a concrete explanation of anticipated coupling can justify escalation; do not purchase a doomed cheap attempt merely to tick a box. Missing instructions, tools, data, permissions or a broken test harness are not automatically model-capability failures. After an accepted decision, transfer the compact result to the appropriate executor. Useful history does not justify assigning a routine monitoring, Git or CI phase to an Astra worker.

Model mix is an observation, not a target or expected ratio. Judge routing by
accepted results and total cost, including reconstruction of useful context.

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

Before a substantial batch of reading, editing, or validation, choose who performs it and how many agents are useful. Consider tools/current coordinator, compliant reuse and a new worker; zero additional agents is a valid choice. Justify concurrent lanes by independent outcomes, context isolation or useful specialist attention, not a fixed quota or the model shown in the app. A one-line choice in the existing plan is enough; this is not a new planning document or a pause for approval.

Reading a complete corpus does not ordinarily require the orchestrator to ingest every byte: independent readers can cover defined portions, preserve contradictions and cite original evidence. Instructions that explicitly require the main agent's own read still take precedence. Do not substitute a summary for required source coverage or let a worker silently omit difficult material.

Choose an outcome-sized assignment, not one agent per command or document. Keep an immediate decision local when the coordinator is capable and transfer would cost more than it saves; otherwise route the bounded decision to an allowed capable worker and start useful independent work. For a large routine batch retained locally, state the actual reason: required direct inspection, no compliant authorized worker/tool, coupling, transfer overhead, or demonstrated worker unreliability. "Defaults" alone does not explain ignoring an available independent split after the user requested efficient delegation.

Model choice is separate from spawning. Inspect the live models, effort levels, tools, executors and available cost/usage information, then select the cheapest adequate pair from the named policy. Reuse that inspected mapping until relevant configuration, availability or evidence changes. The policy already supplies the permitted pairs: do not refuse delegation merely because no custom allowlist file is installed. Unsupported selection or no adequate allowed pair does block that route; continue with exact tools/the authorized coordinator where adequate.

The coordinator must still be able to judge and integrate the artifact. If it cannot, preserve the unresolved requirement for an authorized decision; do not purchase stronger workers merely to escape that judgment boundary or silently switch the coordinator's runtime configuration. Retain useful context within the routing policy; transfer findings when the next phase needs a different executor.

### Routing examples and evidence limits

These examples capture conversational failure patterns, not measured savings or
fixed agent classes:

| Situation | Efficient response | Avoid |
| --- | --- | --- |
| Stable long-running command, noisy output | Use its documented entrypoint; supervise with tools or a small worker if isolation frees useful coordinator work | Reading stable internals or one agent per poll |
| Repeated related visual or domain corrections | Keep the domain owner, send failures and acceptance feedback; use an independent reader for a genuinely fresh check | Rebuilding context for every small iteration |
| Large input, small answer | Small capable reader with source references and explicit coverage | Defaulting all reading tasks to Sol |
| Independent complex outcome | Autonomous epic owner with acceptance, isolated writes and genuine shared limits | Treating it as a short assignment or duplicating its work |
| A reviewer finds the same primary failure again | Revise the hypothesis or design criterion before another variant | Optimizing a proxy while missing acceptance stays open |

The coordinator remains accountable: duplicate investigation, ignored corrections
and unsupported completion claims are execution failures even when guidance
already prohibits them. Do not expand the instruction stack for each occurrence.

### Launch preflight

Establish this contract at launch. Reuse it on resume and follow-up; state only changed scope, constraints or acceptance. Reconsider routing when capability, context, ownership or genuine resource constraints materially change. Keep the receipt in the existing task record; do not add a tracker or repeat model research.

- **Explicit selection.** Set an allowed supported model, reasoning effort and bounded context through actual launch controls or an explicitly selected inspected role. Omitted/inherited cost settings are invalid. The same model as the parent can be chosen independently and explicitly. A model name inside a prompt does not itself set the runtime model. Inspect role/config precedence and actual override exposure. In native V2 choose `fork_turns` explicitly: it defaults to `all`; `none` or a positive integer string bounds inherited history. Fork/override compatibility varies by exposed client schema. If a full-history fork prevents explicit model/effort selection, use a supported bounded-context mode. Inspect actual controls rather than treating an earlier source audit as the current runtime contract.
- **Intentional selection.** Use the named policy: Luna/Low for routine supervision, Luna/Medium for bounded coding, Sol 6.1/Medium for sustained engineering, Astra/Medium or High for the demanding creative/complex decision. A concise task-specific reason is enough; no deliberately failed cheap trial or routine approval prompt is needed. Check the Ultra exception separately before any such launch or reuse.
- **Lifetime, estimates and real limits.** Select the [role and lifetime](#worker-lifetime-and-integration) before defining stops. Record any actual user, account, runtime or resource limit with its source, unit and scope; if none sets a numeric epic budget, say so instead of manufacturing one. A short worker owns a bounded deliverable; a diagnostic experiment can have a finite attempt/time investment. An ongoing orchestrator or epic owner continues through accepted delivery, potentially for hours or days. Its token/time forecast and next checkpoint are planning observations, never an invented hard stop. Revise the approach when an estimate is exceeded; do not report estimated consumption as exhausted account allowance. Preserve cumulative observations and genuine aggregate limits across descendants, retries, replacements and resumes. Unknown measurements stay unknown. Reaching a real hard limit ends the affected execution, with retained evidence and remaining work; it does not prove completion or authorize more spending.
- **Context and reuse.** Choose fresh context or continuity by total expected effort within policy. Reuse only when the known model, effort, retained context and authority fit the next phase. Do not reactivate an Ultra worker after its exception expires, even for a tiny follow-up. Native V2 `followup_task` has no model/effort override fields: transfer findings to a newly configured worker when routing changes. Context minimization must retain permissions, applicable repository instructions, evidence and acceptance constraints. For large coupled work, use the [larger-context procedure](context-caching.md#use-a-larger-model-window-deliberately).
- **Verification and rejection.** No dispatch through unsupported or out-of-policy controls, and no continuation after a disallowed resolved setting is discovered. Record requested/resolved settings from native evidence when observable; absent telemetry is unknown, not verified compliance. Metadata visibility is not a resolved-settings receipt. Inspect a representative launch before multiplying the pattern. A mismatch stops further dispatch until corrected; post-launch inspection cannot prevent the first call's cost. Distinguish soft allocations, native exhaustion boundaries and exact billing ceilings; a required hard cap unavailable on the host blocks that path.

A compact receipt is sufficient:

```text
Role / lifetime: <orchestrator, epic owner, steering reviewer, specialist or execution worker>
Outcome / scope: <complete owned outcome and acceptance; next observable checkpoint>
Executor / count: <tools, coordinator, compliant reuse or new workers; useful concurrency and reason>
Selected model/effort: <allowed supported pair; why adequate or escalation needed>
Context: <bounded inputs or inspected compliant reuse>
Real limits: <source, unit, scope and remaining if known; no invented numeric cap>
Forecast / checkpoint: <estimate when useful; observation or route-reassessment, not epic termination>
Autonomy / delegation: <next-step decisions, authorized descendants, shared integration boundaries>
Enforcement: <actual hard boundary / planning observation / unavailable; scope and overshoot limits>
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

Give workers relevant context and disjoint write scopes. Workers keep logs on disk and return only results, evidence paths, validation, limitations, and unresolved decisions. The coordinator reviews decision-bearing source without replaying commands or importing logs already consumed by workers. When evidence is insufficient, request targeted investigation within the worker's authority and genuine limits; read only excerpts needed for a coordinator decision.

Revisit the choice at integration boundaries or when actual quality, cost, rate-limit, or collision evidence changes it. Do not narrate a routing choice before every tool call. A short direct command often has less overhead than any subagent.

### Worker lifetime and integration

Choose role, lifetime, model and autonomy separately. These roles describe responsibilities, not a required number of agents or a new hierarchy:

| Role | Ownership and continuation | Routing default |
| --- | --- | --- |
| Portfolio/integration orchestrator | Retains overall goals and integration state; keeps authorized outcomes moving, delegates independent epics and resolves shared dependencies. Continues until the requested programme is accepted or a genuine boundary prevents progress. | Sol 6.1 / Medium; prefer its larger supported economical context for coupled state, verified in the current client. Offload noisy routine work. |
| Autonomous epic owner | Owns a domain from requirements through implementation, qualification, receiving-consumer use and acceptance. Retains its worktree and context, chooses next steps, resolves routine blockers, pivots and delegates authorized scoped work. A checkpoint or subordinate result does not end the epic. | Sol 6.1 / Medium for sustained engineering; request a specialist for a specific demanding decision while retaining ownership. |
| Persistent steering reviewer | Retains goals, acceptance, prior corrections and their effects. Reviews meaningful delivery checkpoints or an explicitly requested schedule, challenges drift and ineffective loops, and follows corrections through. It is low traffic and does not gate every owner action or duplicate implementation. | Tools/Luna collect observations; Sol for ordinary cross-boundary review, Astra / Medium or justified High for demanding strategic, creative or complex judgment. A designated stronger reviewer still obeys scoped model/effort authorization. |
| Bounded specialist/reviewer | Resolves one consequential uncertainty or independently checks an artifact; returns the decision, evidence and limitations to its owner. | Choose Sol or Astra by the actual reasoning need, not the reviewer title. Return routine execution to the appropriate worker. |
| Short execution worker | Completes one clear extraction, data-heavy operation, patch, check or diagnostic. Isolates noisy working context, returns a compact usable result, then stops or awaits a specific follow-up. | Deterministic tools first; Luna / Low for routine work, Medium for bounded coding. |

**Ongoing ownership is the default for an explicitly assigned epic.** Its owner may work for hours or days within existing authorization; do not apply a short specialist's token/time estimate to that mandate. It continues autonomously after progress reports and coherent milestones, without a routine renewal request. A missed estimate triggers an explanation, a revised forecast or a changed route, not an "allocation exhausted" handoff. Keep a finite diagnostic experiment finite, then have the epic owner select another useful approach or independent delivery. Do not keep repeating an unchanged failing experiment merely because the epic remains open.

Checkpoints should expose a user-visible improvement, accepted reusable capability, removed blocker with demonstrated effect, or evidence that changes the next decision. Carry useful work through actual receiving use; preparation, source-only success and an active agent are not product delivery. At a dependency wait, continue independent work when possible. Use event-driven waits for a real dependency; do not infer continuous execution from an idle owner or a retained context. A persistent reviewer remains available across iterations, rather than continuously spending inference on polling. Use an authorized existing scheduler for requested periodic reviews; a role description does not install one. No standing panel is required.

Coordinate only the shared boundaries: conflicting writes/contracts, integration, shared execution capacity and decisions outside the owner's authority. Give separable epics persistent owned worktrees and a clear integration responsibility; do not serialize their ordinary decisions behind the main chat. A long-lived mandate does not change permissions, acceptance, actual account/runtime limits or model policy, and does not itself authorize extra paid services. Delegation must be authorized and remain within the owning epic; it cannot reset consumption or genuine limits.

Retire an epic owner after its outcome is accepted and integrated, explicit cancellation, or a supported handoff to a continuing owner. Pause affected work only for a genuine unresolved dependency/decision or execution/authority limit, finishing independent authorized work first. Context compaction, a stale model setting or loss of a runtime handle calls for recovery or a supported handoff, not abandonment of the epic. Preserve owned changes and a compact handoff: branch/worktree, source identities, accepted decisions, checks, evidence and remaining acceptance. Stop/close through supported controls and distinguish idle, waiting, queued, retired and executing owners. Do not claim that a short return clears old context or that a prose mandate guarantees host scheduling.

For concurrent writers, use [separate worktrees and an integration owner](../collaboration/git-write-safety.md#parallel-worktrees-and-pr-coordination). A shared filesystem is not write isolation, and separate worktrees still share repository metadata, remote refs and external resources. Do not switch another worker's checkout or merge through an active writer. Keep temporary evidence/cache with its owner and apply the [cache lifecycle](context-caching.md#cache-lifecycle-and-cleanup) before retiring the checkout.

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
