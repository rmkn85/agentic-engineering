# Context and caching

## Principle

There are several independent caches. Optimize each without confusing them:

1. **model prompt cache** — repeated stable model-input prefixes;
2. **Codex session/state** — resumable conversation/runtime state;
3. **semantic repo cache** — deterministic metadata about files, symbols, dependencies, and prior decisions;
4. **tool/build cache** — compiler, package, test, and generated artifacts;
5. **OS cache** — filesystem/page cache, usually a minor factor for ordinary source trees.

For a focused audit checklist, see [prompt-prefix stability](prefix-stability.md).

## Prompt-cache friendliness

Prompt caching rewards repeated stable prefixes. Keep durable content stable and put volatile task state later.

Prefer the conceptual order:

```text
stable global operating rules
stable repository rules
stable selected skill/workflow
stable task specification
current local evidence
latest failures / progress
```

Avoid timestamps, current Git status, progress counters, or regenerated summaries near the beginning of long persistent instructions.

Measure actual reuse through `cached_input_tokens` in `codex exec --json`; do not infer cache performance from session length.

### Useful metrics

If `cached_input_tokens` is a subset of `input_tokens` for the reported client version:

```text
cache_hit_ratio = cached_input_tokens / input_tokens
fresh_input_tokens = input_tokens - cached_input_tokens
```

Always keep the raw usage fields too, because accounting semantics can change across versions.

## Keep AGENTS.md small

Codex loads an instruction chain from global and repository `AGENTS.md` files at session start. Current config defaults allow up to 32 KiB of project documentation to enter first-turn instructions.

Large permanent instruction files therefore have a recurring tax. Put only frequently applicable invariants in `AGENTS.md`; move optional procedures into skills or referenced documentation.

A good global `AGENTS.md` is hundreds of tokens, not a handbook.

## Keep the skills catalog small

Codex uses progressive disclosure for skills: metadata is available for discovery; the full `SKILL.md` is loaded only when selected; references/scripts are read only when needed.

This is more cache- and context-efficient than putting every workflow into `AGENTS.md`.

Current Codex config exposes `skills.max_context_tokens`; the documented default is 2% of model context and explicit values are capped at 10,000 tokens. If you have many global skills, begin with a deliberately small catalog budget (for example 2,000 tokens), then benchmark whether skill-selection recall remains acceptable.

## Cap tool-output history

Current Codex config exposes `tool_output_token_limit`, the token budget stored for each tool/function result in history.

Use it as a **last line of defense**, not as the primary log compressor. A better pattern is:

```text
command -> full output to local file
        -> one-line PASS summary
        OR short failure index + selected excerpts
```

The model can explicitly read more from the file when the failure requires it.

## Compaction

Compaction is lossy by design. Before natural compaction boundaries, persist important state outside chat:

- task specification / acceptance criteria
- completed units
- file/input hashes
- validation results
- unresolved failures
- invalidated decisions

Then a compacted session can reconstruct working state from deterministic files rather than hoping a prose summary retained every important detail.

Codex exposes `model_auto_compact_token_limit`, a token threshold for automatic history compaction. When unset, the model default applies. `model_auto_compact_token_limit_scope` defaults to `total`; `body_after_prefix` counts only growth after the carried compaction-window prefix. These settings control *when* compaction runs, not how much useful task state it preserves. Do not use `model_context_window` as a way to manufacture more model capacity. See the [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) (reviewed 2026-09-24).

For a host-specific trial, use a one-off `codex -c model_auto_compact_token_limit=<tokens>` override or a private profile, starting from measured context-window and post-compaction sizes. Keep `total` when the goal is to cap the full active context. Compare accepted work, peak input, cached and fresh input, wall time, and compaction count against the default; earlier compaction may create more summaries or discard needed detail. `PreCompact` and `PostCompact` hooks expose `manual` versus `auto` triggers for prospective local telemetry; ordinary transcript markers alone do not identify the trigger. See [one-off overrides](https://learn.chatgpt.com/docs/config-file/config-advanced) and [hooks](https://learn.chatgpt.com/docs/hooks).

Prefer coherent milestones. If context pressure appears mid-change, first save the exact in-progress state and next action, then compact using the host's supported control. A note or short worker return does not itself remove earlier context.

### Use a larger model window deliberately

Reviewed **2026-10-18**. Sol 6.1 can retain a larger coherent engineering working set, but API capacity and a particular Codex client's advertised capacity are different evidence. The [API model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol) lists 1,050,000 tokens; one inspected native Codex catalog advertises 500,000 with a 95% effective-window setting. That is an observed client limit, not a universal Codex entitlement or a promise that every token is available for source. Inspect the actual selected model's catalog, effective settings and reserves once per run. Do not set `model_context_window` to the API maximum to bypass a smaller supported client window.

Use Sol 6.1/Medium for sustained work whose contracts, implementation, tests and current evidence need to stay together: for example, one cross-module change with shared invariants. Keep that owner across coherent iterations rather than repeatedly rebuilding its context. Load the relevant related sources; keep unrelated backlog history and verbose CI output outside the window. Luna can supervise routine operations and return compact evidence while Sol retains the engineering decisions. Use Astra for the demanding creative/complex decision, then transfer its accepted result instead of copying its entire history.

Before adopting a larger-window model, inspect old fixed compaction overrides. A 220,000-token threshold still triggers at that size on a 500,000-token model. The [configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) documents that leaving `model_auto_compact_token_limit` unset uses the model default. Start there unless an intentional measured override is needed; preserve unrelated settings and validate a fresh run. If testing a different threshold, use a bounded private profile/one-off override, leave response/reasoning headroom, and compare accepted outcome, reconstruction, compactions, input/cache usage and wall time. A larger window is capacity, not a requirement to fill it or proof of better recall.

This also handles model switching without assigning a Sol-sized global threshold to Astra. In the reviewed [native source](https://github.com/openai/codex/blob/main/codex-rs/protocol/src/openai_models.rs), an absent per-model/configured limit derives from 90% of the resolved raw window; a supplied limit is clamped to that boundary. With the inspected catalog's absent per-model limit, the source-derived thresholds are 450,000 for Sol 6.1's 500,000 window and 244,800 for Astra/Luna's 272,000 window. The separate 95% usable-window calculation gives 475,000 and 258,400. These calculations are not observed runtime trigger events, and the displayed context counter may use a different accounting base. Keep `model_auto_compact_token_limit_scope = "total"` for the full-context boundary. Do not invent a model-name table, modify the provider-owned catalog or install a watcher to rewrite global settings on every model switch. If a deliberately earlier threshold is needed, use a supported explicit profile/one-off override and verify it applies to the intended run.

The API page also lists higher full-request rates above 272K input tokens (2× input/cache, 1.5× output). API rates do not establish Codex subscription-credit accounting. Larger retained context can reduce reconstruction and still increase total inference cost; measure the accepted workflow before claiming savings. Keep the [model/effort and allowance policy](subagents.md#named-model-and-effort-policy) unchanged by context size.

## Cache invalidation

Never turn “do not reread” into dogma. Reuse prior semantic work while its inputs remain valid.

A unit becomes dirty when an input that can alter its conclusion changes, for example:

- the file itself
- imported/exported interface it depends on
- task requirement affecting it
- compiler/test evidence contradicting the prior conclusion

This is incremental compilation applied to model work.

## Native documentation result preflight

Documentation-result reuse is separate from the model prompt cache. For unwrapped documentation tools, use the explicit offline [docs-result tool](../../tools/README.md#documentation-result-preflight) before a native MCP documentation call. Once the reviewed Context7 bridge is configured and active, ordinary native calls use its automatic preflight; callers do not also create manual request/response JSON. The standalone tool does not intercept MCP, contact providers, manage credentials or automatically install a host workflow. For a deterministic Context7 stdio default, the separately reviewed [native bridge](../../tools/README.md#context7-native-stdio-cache-default) performs this step on ordinary tool calls after configuration and MCP restart; source/fixture proof does not establish live activation. The caller inspects `hit`, `miss` or `blocked`; only a miss permits the planned native call. Record its actual JSON response, including an error, explicitly afterward. A scoped instruction must route callers through this step; file presence and manual tests do not prove normal startup adoption.

For cooperating workers the coordinator passes one shared ignored cache directory and the same client/auth namespace, including across worktrees; separate default directories do not coordinate probes. Different namespaces require an actual client/account/permission difference. Choose a private, nonsecret client/auth namespace and explicit provider, operation, exact arguments and source/version identity. Cache library resolution separately from version/language/question-specific documentation. Reuse only while both the recorded validity and caller freshness bound hold. Changed arguments, source, version or namespace, expiration, missing response and hash mismatch invalidate reuse. Do not use paraphrase matching as an identity check. The cache stores recoverable response content plus time/hash provenance; raw response text is source evidence, not a new authority claim.

Classify failures from observed responses. Valid cached docs remain usable during a provider failure. Provider-wide quota, authentication, spending or outage state suppresses new duplicate probes across different queries/operations in that namespace until an observed retry/reset boundary or explicit meaningful changed-condition evidence. A request-specific missing page does not block other queries. Never store failure text as successful documentation. An error message is an observation, not proof of account scope, transport, credential state or root cause. Missing reset metadata means unknown retry time, not permission to keep probing. Use [proportionate diagnosis](../execution/bounded-recovery.md#choose-diagnosis-investment-before-deeper-work) before investigating further.

Reviewed 2026-10-18: Context7's [API guide](https://context7.com/docs/api-guide) recommends caching responses for hours or days; resolution and documentation queries each use a counted API call. Its [client guide](https://context7.com/docs/resources/all-clients) distinguishes OAuth for HTTP clients from API-key stdio setup. The [usage endpoint](https://context7.com/docs/api-reference/usage/get-api-usage) is read-only and does not count against requests, but requires an API key. These facts suggest bounded checks; they do not diagnose a particular quota message or authorize extracting credentials. Set freshness according to the task and source volatility, not a universal duration.

Keep request/response files private and exclude credentials, headers, personal identifiers and confidential queries from published fixtures. Existing `.agent-cache/` is ignored. A missing cache says prior reuse is unavailable; it does not measure zero savings. Count avoided producers only where the caller actually observes hit/miss and native-call execution; no token or live-provider savings are established by offline fixtures.

## Cache lifecycle and cleanup

Give each temporary working set an owner, purpose and reuse boundary using the existing task/artifact location. Reuse deterministic build/dependency caches and semantic findings while their source/dependency/configuration inputs remain valid. A cache hit is usable only for the same relevant identity; do not silently reuse a stale executable, index or capture as evidence for a newer candidate. Share read-only pinned caches where supported; isolate mutable outputs and use the tool's native locking rather than concurrent writers in one cache directory.

Classify before clearing. Source, downloaded asset/license provenance, user data, accepted captures and required evidence are durable even if ignored by Git or stored under a directory called cache. Preserve them in the owner's normal artifact store before deleting task-local scratch, failed variants and reconstructible intermediates. At integration/retirement release the task's temporary cache, stop its consumers and prune only its owned paths with the maintained cleanup command. Check containment, symlinks, active users and outstanding handoffs; preview destructive cleanup where supported. Keep useful shared build/package caches under their native quota/eviction policy instead of flushing them after every commit.

Do not use blanket cache deletion to repair an unexplained failure. Invalidate the input-dependent entry or run a bounded cold-cache comparison when that distinguishes a stale-cache hypothesis. Preserve the decisive before/after evidence, then clear obsolete scratch promptly. Disk cleanup and conversation compaction are different operations: deleting files or closing a worktree does not remove already-loaded model context, and compaction does not delete on-disk caches.

## References

- OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
- Codex config reference/sample: https://learn.chatgpt.com/docs
- Codex AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Codex customization/skills: https://learn.chatgpt.com/docs/customization/overview
- Codex non-interactive usage: https://learn.chatgpt.com/docs/non-interactive-mode
