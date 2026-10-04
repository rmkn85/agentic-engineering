# Native Codex multi-agent V2: source-backed configuration audit

Reviewed **2026-10-04** against OpenAI Codex source snapshot [`d0759639f20af955a5c6447f4683e99bf42ab6cf`](https://github.com/openai/codex/tree/d0759639f20af955a5c6447f4683e99bf42ab6cf). This is a source audit, not a live installed-client trial. A standalone CLI, an IDE extension and an app's bundled backend can run different versions. Match configuration and tool schemas to the binary actually executing the task.

This corrects the earlier recommendation to replace `[features.multi_agent_v2]` with `[agents]` merely because the public configuration page did not enumerate the former. The typed configuration and runtime explicitly support V2 and its hints. **Absence from a documentation index is not evidence of removal or equivalence.** Preserve working behavior until its replacement is verified.

The [named routing policy](subagents.md#named-model-and-effort-policy) remains unchanged: Sol/Medium for substantial orchestration, mostly Luna/Low or Medium workers, intentional bounded Luna/High or Sol/Medium/High escalation, and no autonomous Astra or above-High workers. The [configuration example](../../configs/codex/efficient-local.config.toml) now preserves V2 policy while setting worker defaults.

## 1. Separate activation, behavioral policy, and cost selection

`[agents]` provides general enablement and worker model/effort defaults. `[features.multi_agent_v2]` selects/configures the task-path-based V2 backend. They are complementary, not interchangeable.

The source's `multi_agent_version_override` gives enabled `features.multi_agent_v2` precedence over `agents.enabled = false`. Removing or disabling the V2 force does not by itself guarantee a V1 runtime: model metadata and retained session state also matter. To deliberately disable delegation, disable both controls in the effective configuration and verify a fresh run's actual tool surface. Do not apply that change merely to optimize prices. The schema says `agents.max_depth` is V1-only and ignored by V2; it is not a V2 no-grandchildren guard. [Sources: configuration, backend override, schema.][config]

`multi_agent_mode_hint_text` has operational meaning. In V2, mode resolution uses:

1. the configured custom hint;
2. a model-catalog hint, when present;
3. otherwise the model's proactive policy at `ultra`, or explicit-request-only policy at other efforts, with possible catalog replacements for the bundled policy text.

A custom hint therefore **decouples the delegation policy from reasoning effort**. Removing it can change whether a Medium/High coordinator proactively delegates. It does not choose a cheaper worker model, enforce an allowlist, or cap tokens. A configured empty string is still an explicit custom mode, not the same as an absent setting. [Source: mode resolution.][modes]

There are additional instruction surfaces: root/subagent role hints, an appended spawn-tool hint, inherited developer instructions and optional custom-role instructions. Configured root/subagent hints replace their built-in role text; empty configured role text suppresses fallback. Do not replace all role guidance just to add one cost rule. The spawn description can itself encourage inheritance unless the user explicitly requests another model. An owner-approved Luna/Sol routing policy should make that authorization explicit rather than assuming a generic efficiency slogan defeats every injected default. [Sources: mode resolution and tool descriptions.][modes] [tool-spec]

## 2. Model selection and what metadata visibility does not mean

In this snapshot, `features.multi_agent_v2.expose_spawn_agent_model_overrides = true` exposes `model` and `reasoning_effort` on V2 `spawn_agent`; it defaults to true. An older version, profile or experiment may differ. Inspect the actual tool schema before claiming the model can select them. Writing a model name in the task message does not set a runtime parameter.

`hide_spawn_agent_metadata` is a separate control. In current V2 it does **not** remove model/effort fields when override exposure is enabled. The spawn result contains a task path, optionally a nickname; setting metadata visibility does not turn it into a resolved model/effort receipt. The handler records resolved settings from the child's configuration snapshot in native collaboration telemetry. Use available native trace/session evidence; a worker's self-description is not verification. [Sources: tool specification and spawn handler.][tool-spec] [spawn]

The child configuration applies parent step settings, corresponding `[agents]` defaults or explicit spawn values, then custom-role overrides. Thus effective priority is **custom role > explicit spawn field > corresponding worker default > parent fallback**. Supplying a model without an effort in either spawn/defaults uses that selected model's default effort before role overrides. Set both deliberately and inspect roles. Permission profile, approval policy, cwd and environment are also propagated; cheap/fresh context is not permission to broaden access. [Source: child configuration.][child]

Model availability is not proved by an API model page or a remembered name. The live roster and supported effort metadata are used to validate overrides. An older first-hand [July 31 report](https://github.com/openai/codex/issues/36294) demonstrated Luna running V2 as a root while being rejected as a V2 child by a static catalog filter. Current inspected code no longer uses that exact V1-only exclusion, but that does not establish which installed release/account has the behavior. The [September 17 change](https://github.com/openai/codex/commit/800d183e2d0a3275c1b440992f4b11abbf425711) also corrected children inheriting stale initial-turn settings after an in-turn model change. Version and actual dispatch evidence matter. [Source: current validation path.][child]

## 3. Context forks and worker reuse

V2 uses **`fork_turns`**, not V1's `fork_context`:

| Value | Meaning in the inspected handler |
| --- | --- |
| `"none"` | Do not copy surrounding parent conversation; supply a complete bounded handoff. |
| `"3"`, another positive integer string | Copy the most recent N turns. This is a turn count, not a token budget. |
| `"all"`, omitted or empty | Full-history fork. |
| `"0"` or `fork_context` | Rejected. |

Current V2 **does permit model/effort overrides with a full-history fork**; an explicit role can apply too. Do not generalize an older failure into a universal ban. Prefer `"none"` or a small explicit turn count for economy, while retaining the instructions, inputs and acceptance the worker needs. Select model, effort and context independently. [Sources: spawn parsing and child configuration.][spawn] [child]

`send_message` queues information without starting an idle agent. `followup_task` starts work on an idle non-root agent or steers a running one. Its schema takes target and message, not a new model/effort pair. Reassess retained configuration and budget before reuse; to downgrade, transfer findings to a newly selected cheaper worker instead of pretending a follow-up prompt reconfigures the old one. [Source: tool contracts.][tool-spec]

## 4. Full V2 configuration surface in this source snapshot

These are audit facts, **not a recommendation to set every option**. Unset custom strings use runtime/catalog fallback. Preserve defaults unless a concrete workload requires a change.

| Field under `features.multi_agent_v2` | Purpose / inspected base behavior |
| --- | --- |
| `enabled` | Explicit V2 activation; distinct from general agent enablement. |
| `max_concurrent_threads_per_session` | Concurrent-thread limit; V2 base constant is 4. Other effective configuration may change it. Not cumulative spend. Avoid contradictory caps in multiple tables. |
| `min_wait_timeout_ms`, `default_wait_timeout_ms`, `max_wait_timeout_ms` | Wait-tool timing; base 10,000 / 30,000 / 3,600,000 ms. Supported bounds are 0 to 3,600,000 ms with valid ordering. Not worker execution deadlines. |
| `multi_agent_mode_hint_text` | Overrides delegation mode policy, including effort-derived fallback. |
| `usage_hint_text` | Additional spawn-tool description text. Does not select a model. |
| `usage_hint_enabled` | Deprecated compatibility field; ignored. |
| `root_agent_usage_hint_text`, `subagent_usage_hint_text` | Replace respective role usage instructions; empty values suppress fallback. |
| `subagent_developer_instructions` | Overrides inherited worker developer instructions when role-specific instructions do not replace them. Preserve essential constraints; do not use an empty replacement as an economy trick. |
| `tool_namespace` | Tool namespace; base `collaboration`, validated name syntax. Renaming is not a cost control. |
| `hide_spawn_agent_metadata` | Base true; affects metadata presentation, not an allowlist or resolved-cost guarantee. |
| `expose_spawn_agent_model_overrides` | Base true; exposes model/effort spawn parameters. |
| `wait_agent_enabled` | Base true; exposes mailbox waiting. |
| `disable_direct_message` | Base false; disables direct-message tools, not spawning or automatic child results. |
| `non_code_mode_only` | Base true; keeps V2 tools on the direct-model surface rather than nested code-mode calls. Does not mean non-programming tasks only. |
| `message_board_in_memory` | Base false; in-memory board storage for training/ephemeral contexts. |
| `message_board_remote` | Optional session-scoped remote board configuration. No need to deploy one for cheap worker routing. |

Sources: [typed feature configuration][fields], [runtime defaults and constants][config], [tool exposure planning][exposure]. The typed V2 configuration rejects unknown fields; do not copy plausible-sounding `allowlist`, model-budget or other invented keys into it.

## 5. Coordination, waiting and limits

V2 uses canonical task paths such as `/root/checks` and agent mailboxes. Its wait tool waits for mailbox activity/final-status notifications or steered user input, not necessarily completion of one specific child; timeout does not stop the worker. `interrupt_agent` interrupts a turn while leaving the agent available. Shared-state writes still require explicit ownership; separate model context is not filesystem isolation. [Sources: tools and child runtime settings.][tool-spec] [child]

Avoid reflexive polling and duplicate coordinator work. Keep workers on disjoint deliverables, return decisive evidence, and integrate only after relevant acceptance. "Workers do not redelegate" is an instruction-level boundary here, not something established by V1's `max_depth`. Concurrency, depth, total worker calls, time, tokens and billed usage are different quantities.

Custom Responses-compatible providers must support the actual V2 tool transport, including the encrypted message fields used in its schema. Historical provider errors are evidence to inspect compatibility, not a reason to silently fall back to a differently priced model/backend. The July model-catalog report is also not a current benchmark or universal failure.

## 6. Rollout budgets: real native enforcement, but not an exact invoice ceiling

Do not describe `features.rollout_budget` as only a reminder because it is experimental. The inspected local controller shares a budget across the root and its worker tree. At usage accounting, it returns **`SessionBudgetExceeded`** after the limit is reached. This is a native exhaustion/error path, not merely a request that the model stop. [Sources: accounting and controller.][budget] [budget-control]

The inspected typed settings are `enabled`, `limit_tokens`, `reminder_at_remaining_tokens`, `sampling_token_weight`, and `prefill_token_weight`. With backend-provided `codex_rollout_budget_units`, those units are used. Otherwise accounting is:

```text
output_tokens * sampling_token_weight
  + non_cached_input_tokens * prefill_token_weight
```

The counter is shared across the root session tree, not a separate allowance for every child. Native accounting includes inference responses, including compaction. It is not a model-price-aware billing calculation by default, and it is not the same as the context-window/auto-compaction threshold. [Sources: accounting, shared runtime, controller API.][budget] [runtime] [api]

**Boundary:** usage is recorded after inference. A response or concurrent in-flight work may cross the threshold before the accounting error is observed. Do not promise zero overshoot, immediate global cancellation, durable cross-process accounting, a weekly account cap, or a strict dollar/credit maximum without a real host trial. Also distinguish this whole-tree limit from the skill's per-assignment allocations. A low whole-tree limit can terminate the coordinator as well as workers.

Keep it optional in the generic preset: no arbitrary token allocation is installed. To adopt it, choose a task-sized limit, validate the installed version's typed fields, and run a small approved trial covering exhaustion, child usage, compaction and resume/restart behavior. Never reset a native or policy allocation by respawning solely to evade it. Continue independent work only while authorized and while the applicable native budget permits it.

## 7. Codex V2 is not hosted Responses multi-agent

The [hosted Responses beta](https://developers.openai.com/api/docs/guides/responses-multi-agent) documents shared request model/tools and its own concurrent-subagent setting. It does not supply the native Codex `fork_turns`, custom-role or mixed-model configuration contract. Conversely, hosted same-model behavior does not imply native Codex V2 cannot use Luna children under Sol. Read the correct layer before applying limitations.

## 8. Small verification set, not another infrastructure project

On the actual executing binary, retain its version, effective config/role sources and native trace. Check a fresh run rather than relying on an existing worker's state. The minimum useful acceptance set is:

- The custom mode hint remains delivered when main effort changes; inexpensive worker defaults remain separate.
- One explicit Luna/Low or Medium child with `fork_turns="none"` resolves as requested and receives required repository/permission/acceptance context.
- Metadata hidden and override exposure enabled still exposes the two selection fields; a role override is detected through native configuration evidence.
- Full-history and bounded forks are tested as separate context choices, not assumed model-selection limitations. Follow-up retains its existing configuration.
- The no-descendants rule is checked in the trace; no V1 depth limit is credited as V2 enforcement. A wait timeout is not reported as worker cancellation.
- When a native rollout budget is adopted, exhaustion is distinguished from a soft prompt limit, and overshoot/resume behavior is measured before claiming a hard spending guarantee.

These are proposed behavioral checks. TOML parsing, source inspection and contributor CI do not establish model adherence or savings. Keep private account traces local; report only generalized findings in this public repository.

[fields]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/features/src/feature_configs.rs
[config]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/config/mod.rs
[modes]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/session/multi_agents.rs
[tool-spec]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/tools/handlers/multi_agents_spec.rs
[spawn]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs
[child]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/agent/child_config.rs
[exposure]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/tools/spec_plan.rs
[budget]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/rollout_budget.rs
[budget-control]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/agent/control/budget.rs
[runtime]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/agent/control/runtime.rs
[api]: https://github.com/openai/codex/blob/d0759639f20af955a5c6447f4683e99bf42ab6cf/codex-rs/core/src/agent/api.rs
