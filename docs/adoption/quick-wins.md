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

## 2. Make noisy commands quiet

Keep full logs on disk and show the model only status plus relevant failures.

```bash
tools/quiet-run .agent-logs/test.log -- make test
```

Expand the log only when the compact result identifies a failure that needs diagnosis.

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

## 7. Benchmark only the uncertain decisions

If an optimization is mechanically favorable and preserves the outcome, use it. If the tradeoff is workload/model dependent, compare the smallest useful alternatives with the same task and acceptance criteria.

For local Codex:

```bash
python tools/codex-bench.py \
  --label baseline \
  --prompt-file task.txt \
  --eval-command './test-or-acceptance-check'
```

Then change **one meaningful variable**: model tier, instruction variant, delegation split, tool/config layer, or context placement.

## Decision order

```text
Is the work exact/mechanical?
  -> tool/script
else
Is the problem repeated reading/log/context noise?
  -> cache, reduce, scope, or isolate context
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
