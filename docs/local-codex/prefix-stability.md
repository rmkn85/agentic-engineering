# Prompt-prefix stability

Prompt caching and repeated-prefix reuse can make long-running agent sessions cheaper, but only when the recurring prefix remains stable enough for the host/provider to reuse it.

This guide requires no new model or framework. It is instruction/context hygiene.

## Stable-first ordering

Prefer:

```text
stable global operating rules
stable repository rules
stable selected workflow/skill
stable task specification
current evidence
latest failures / progress
```

Put volatile state late.

## Common accidental cache breakers

Review persistent prompt construction for:

- timestamps near the front;
- current Git status or branch summaries regenerated every turn;
- progress counters in persistent instructions;
- non-deterministic map/object ordering;
- dynamically reordered tool schemas;
- large generated summaries inserted before stable rules;
- repeatedly changing skill/tool catalogs;
- duplicated instructions rewritten rather than reused;
- session-specific identifiers embedded in otherwise stable text.

Do not remove useful information merely for cacheability. Move volatile content to the cheapest appropriate layer.

## Tool schemas and catalogs

When the host permits, prefer stable tool definitions plus state-aware availability over repeatedly rebuilding a different tool catalog. A changing early schema can invalidate a large reusable prefix and can make historical tool references harder to interpret.

This is host-dependent. Treat it as behavior to observe, not a universal API guarantee.

## Deterministic serialization

When your own harness serializes persistent state:

- use deterministic key ordering;
- avoid random IDs in stable sections;
- keep equivalent configuration byte-equivalent where practical;
- append new evidence rather than rewriting old stable material;
- separate durable configuration from volatile execution state.

## Measure actual reuse

When the runtime exposes usage, retain raw fields:

```text
input_tokens
cached_input_tokens
output_tokens
reasoning_tokens
```

Then, only when accounting semantics are known:

```text
cache_ratio = cached_input_tokens / input_tokens
fresh_input = max(input_tokens - cached_input_tokens, 0)
```

Do not infer cache effectiveness from conversation length.

## Prefix stability before semantic compression

Use this order when context cost becomes material:

1. remove accidental prefix churn;
2. stop injecting irrelevant context;
3. externalize bulky tool observations;
4. isolate temporary worker context;
5. compact completed phases after durable state is persisted;
6. evaluate aggressive semantic/selective compaction only if pressure remains.

This prevents solving a serialization problem with a summarization model.

## Correctness beats cacheability

Do not freeze stale state just to preserve a cache hit. A cache-friendly prefix is valuable only while it represents current durable rules and task state. When an input that can change the decision changes, invalidate or update it explicitly.

## Review checklist

Before changing the prompt/instruction stack, ask:

- is the changed text actually needed for this task?
- could it be scoped to a path, skill, worker, or later evidence section?
- is serialization deterministic?
- does the runtime report cached-input reuse?
- did the change improve fresh-input cost without harming adherence or acceptance?

Prefer observed cache behavior over folklore.
