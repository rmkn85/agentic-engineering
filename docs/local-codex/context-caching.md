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

Compact at coherent milestones, not mid-change.

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
