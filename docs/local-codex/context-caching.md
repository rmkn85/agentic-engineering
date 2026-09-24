# Context and caching

## Principle

There are several independent caches. Optimize each without confusing them:

1. **model prompt cache** — repeated stable model-input prefixes;
2. **Codex session/state** — resumable conversation/runtime state;
3. **semantic repo cache** — deterministic metadata about files, symbols, dependencies, and prior decisions;
4. **tool/build cache** — compiler, package, test, and generated artifacts;
5. **OS cache** — filesystem/page cache, usually a minor factor for ordinary source trees.

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

## Cache invalidation

Never turn “do not reread” into dogma. Reuse prior semantic work while its inputs remain valid.

A unit becomes dirty when an input that can alter its conclusion changes, for example:

- the file itself
- imported/exported interface it depends on
- task requirement affecting it
- compiler/test evidence contradicting the prior conclusion

This is incremental compilation applied to model work.

## References

- OpenAI model guidance: https://developers.openai.com/api/docs/guides/latest-model
- Codex config reference/sample: https://learn.chatgpt.com/docs
- Codex AGENTS.md: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Codex customization/skills: https://learn.chatgpt.com/docs/customization/overview
- Codex non-interactive usage: https://learn.chatgpt.com/docs/non-interactive-mode
