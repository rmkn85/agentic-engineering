# Observation economy: compact receipts, restorable evidence

Tool output is often much larger than the decision it supports. Replaying full logs, search results, traces, diffs, or command output through later model turns converts evidence retention into recurring token cost.

```text
producer
  ↓
full evidence retained outside active context
  ↓
compact receipt / index / stable reference
  ↓ if needed
targeted exact retrieval
  ↓ only when necessary
broader artifact inspection
```

## Core rule

**Compress representation, not evidence.**

Do not delete the raw artifact merely to make the prompt smaller. Make it progressively addressable so the model can recover exact evidence when a later decision needs it.

## Useful receipt fields

Depending on the artifact, retain only fields that help decide whether deeper inspection is necessary:

- status: pass/fail/partial;
- stable path or handle;
- byte/line count;
- checksum or revision identity when staleness matters;
- bounded preview;
- structured failure count/index;
- command or producer identity;
- retrieval methods such as line range, grep, test name, trace/span ID, or artifact-relative path;
- known limitations or omitted scope.

Example:

```json
{
  "type": "observation_ref",
  "id": "obs:sha256:<digest>",
  "bytes": 1834921,
  "summary": "pytest: 7 failed / 814 passed",
  "index": [
    {"kind": "failure", "key": "test_cache.py::test_invalidate", "line": 8821}
  ],
  "retrieval": {
    "path": ".agent/evidence/<digest>.txt",
    "supports": ["lines", "grep"]
  }
}
```

The exact schema is optional. The invariant is not.

## Small output stays inline

Externalization has overhead. Keep a small result inline when it is already concise, exact content is decision-critical, or artifact creation/retrieval would cost more than retaining it.

Use artifact-backed receipts when output is large, repetitive, or likely to survive across several turns/phases.

## Retrieve exact evidence before semantic summaries

Prefer deterministic retrieval when practical:

1. structured index lookup;
2. exact identifier/test/path lookup;
3. grep/search;
4. bounded line/byte range;
5. broader artifact read;
6. semantic summarization only when exact retrieval cannot answer efficiently.

A model-generated summary can help navigation, but it is not a substitute for preserving the source.

## Lifecycle and invalidation

A stable reference is useful only while its identity is trustworthy. Record enough information to answer:

- which run/revision produced this artifact?
- did an input that can affect it change?
- is it session-local or durable?
- can the exact source still be retrieved?
- has a newer artifact superseded it?

When a relevant input changes, mark the prior observation stale rather than silently presenting it as current.

Hash verification proves retained bytes, not current applicability. Bind the
existing run/handoff to the tested source/candidate and compare it with the
current candidate before reusing the result. A valid old log remains historical
evidence after source changes; `observation-recall.py` does not infer freshness.

## Worker handoffs

Workers should normally return:

```text
result / decision
changed scope
validation status
compact evidence references
limitations / untested scope
open decisions
```

Do not return the entire worker transcript or raw logs unless the coordinator needs them. Keep evidence retrievable through integration.

## Before compaction

Persist:

- task/acceptance criteria;
- accepted decisions;
- completed units;
- relevant hashes/revisions;
- validation results;
- unresolved failures;
- stable evidence references;
- invalidated/rejected decisions that must not be rediscovered.

Compaction may shorten the conversation; durable evidence makes it reconstructable.

## Failure modes

**Over-eager truncation:** a preview hides the useful error. Retain the full artifact and expose targeted retrieval.

`quiet-run`'s failure excerpt is the final 80 lines by default, not a complete
failure index. Use `python3 tools/observation-recall.py MANIFEST --find EXACT_ID`
or `--lines START:COUNT` on `full-log` when the cause is earlier. Hash mismatch
blocks recall; repair the evidence route rather than using unverified bytes as
the same observation.

Compact reports preserve negation, uncertainty, units, conditions/exceptions,
exact IDs, source and owner, and individual check states. Missing data, measured
zero, an uncertain estimate and a negative result must remain distinguishable.
For example, “unit checks passed; render/device/integration unrun” does not close
those other gates. Use fuller reasoning when a compact form would obscure the
condition, source coverage or acceptance gap. See the
[scoped compression cases](../../experiments/instruction-context-adherence.md#scoped-compression-and-evidence-recall).

**Stale handle:** a receipt points to an older revision. Include revision/hash identity and explicit invalidation.

**Summary becomes authority:** a semantic summary silently replaces original evidence. Resolve disputed or exact claims against the source artifact.

**Artifact sprawl:** everything becomes retained forever. Use session-local retention by default; promote only evidence that must survive the boundary.

## Measurement

When this optimization is material, compare:

```text
raw_tool_bytes
model_visible_tool_bytes
fresh_input_tokens
repeated_observation_bytes
targeted_retrieval_count
model_turns
wall_time
acceptance_result
```

A good observation layer reduces recurring model-visible evidence without degrading later exact recall or task acceptance.
