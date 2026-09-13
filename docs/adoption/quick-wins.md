# Quick wins without major refactoring

Use these when a team wants immediate efficiency gains before changing architecture, agent frameworks, or workflow ownership. Start with the **lowest-risk mechanical wins**, observe the result, then add behavioral tuning only where a real problem remains.

## 1. Inspect the instruction footprint

Before adding another rule, inventory what is already resident.

```bash
python tools/instruction-footprint.py .
```

Treat the reported token estimate only as a comparison proxy. Use your harness's native context inspector when available because system prompts, memories, skill metadata, MCP/tool schemas, and runtime state may dominate the file-based total.

Immediate actions:

- remove duplicated global instructions;
- move task-specific procedures from always-loaded files into skills/on-demand docs;
- move file/directory-specific guidance into scoped/nested rules where the harness supports them;
- keep rationale and external research in `references/`, not runtime instructions.

## 2. Make noisy commands progressively inspectable

Keep full logs on disk but expose only the smallest useful diagnostic layer first.

```bash
tools/quiet-run -- make test
```

`quiet-run` now writes a small bundle containing `manifest.json`, a bounded failure excerpt when needed, and the full log. Its normal model-facing output is one line with paths rather than an automatic tail dump.

On failure:

```text
one-line status / manifest
        ↓ if needed
failure excerpt
        ↓ if needed
targeted search/slice of full log
        ↓ only when necessary
entire full log
```

For programs that may terminate or become unreachable, generalize the same pattern with [`../runtime/postmortem-bundles.md`](../runtime/postmortem-bundles.md): a persisted manifest should link to progressively deeper stack/event/environment/trace/dump artifacts so diagnosis does not depend on querying a live process.

## 3. Route exact work away from the model

Before asking an agent to reason about a mechanical batch, ask whether a deterministic command/script can do it exactly:

```text
inventory/search/hash/format/build/test/filter/move?
  yes -> deterministic tool
  no  -> model judgment may be useful
```

Do not create a subagent to run one obvious shell command.

## 4. Stop rereading unchanged work

Record enough state to know what has already been inspected or validated and what input invalidates it. Reopen detailed evidence only after a relevant change or contradiction.

This is often a larger win than prompt tuning because it removes repeated model work entirely.

## 5. Keep validation proportional to the change

During iteration, run the cheapest test that can catch the likely local failure. Broaden validation at integration/final boundaries or when dependency/risk evidence justifies it.

Do not repeatedly rerun a passing broad suite when no relevant input changed.

## 6. Add an executor checkpoint for substantial batches

For a non-trivial batch, make one terse choice before consuming it:

```text
route: tool — exact inventory
route: self — tightly coupled semantic edit
route: worker/smaller — independent routine inspection batch
```

This is a phase-boundary control, not narration before every command. If a lightweight orchestrator repeatedly ignores the checkpoint, test the behavior and escalate placement/enforcement/model capability instead of adding paragraphs of synonyms.

## 7. Make new and touched source weak-reader legible

Do **not** start by rewriting the repository.

For source directories, add/adapt the compact [`../../templates/source-AGENTS-agent-legible.md`](../../templates/source-AGENTS-agent-legible.md) as a scoped/nested rule where the harness supports it. Then apply one invariant to every new or touched unit:

> A fresh weaker coding model should be able to predict representative behavior from the unit plus a small explicit contract/dependency context.

When touching code, cheaply remove obvious local obstacles such as hidden dependencies/state, gratuitous indirection, needless branching, swallowed errors, or tests coupled to implementation details. Do not broaden the task into unrelated cleanup.

If a 15-line function still needs six wrappers and several hidden collaborators to explain, making it shorter is not the quick win. Reduce the **semantic-hop/context radius** instead.

## 8. Benchmark only the uncertain decisions

If an optimization is mechanically favorable and preserves the outcome, use it. If the tradeoff is workload/model dependent, compare the smallest useful alternatives with the same task and acceptance criteria.

For local Codex:

```bash
python tools/codex-bench.py \
  --label baseline \
  --prompt-file task.txt \
  --eval-command './test-or-acceptance-check'
```

Then change **one meaningful variable**: model tier, instruction variant, delegation split, tool/config layer, code-structure hypothesis, diagnostic representation, or context placement.

## Decision order

```text
Is the work exact/mechanical?
  -> tool/script
else
Is the problem repeated reading/log/context noise?
  -> cache, reduce, scope, layer, or isolate context/evidence
else
Am I writing/touching source?
  -> keep the local mental model bounded for a weak/fresh reader
else
Is a persistent instruction causing/solving behavior?
  -> behavioral baseline + smallest rule + pressure test
else
Is independent work materially expensive or on the critical path?
  -> evaluate bounded worker delegation
else
  -> keep the platform default
```

The purpose of these quick wins is to remove waste, not to install a new ceremony layer. Stop when the current workflow is already efficient enough for the task.
