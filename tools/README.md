# Deterministic efficiency tools

These helpers exist to move exact work out of the model and make optimization measurable.

## `quiet-run`

Capture full command output locally while exposing only a one-line success summary or a bounded failure tail.

```bash
tools/quiet-run -- pytest -q
tools/quiet-run -- cargo test
```

Environment controls:

- `QUIET_RUN_LOG_DIR` (default `.agent-cache/logs`)
- `QUIET_RUN_TAIL_LINES` (default `80`)

## `repo-index.py`

Build a no-LLM JSONL inventory of Git-tracked files using Git blob IDs, byte size, line count, extension, and binary detection.

```bash
python3 tools/repo-index.py --repo . --output .agent-cache/repo-index.jsonl
```

This is intentionally a tier-0 inventory. Prefer universal-ctags/LSP/SCIP/language-native metadata for richer symbol or dependency queries.

## `codex-bench.py`

Create a detached worktree, run the same task with `codex exec --json`, capture raw events, aggregate token usage/tool events, run an optional deterministic acceptance command, and record Git statistics.

```bash
python3 tools/codex-bench.py \
  --repo . \
  --label efficient-local \
  --prompt-file benchmark-task.md \
  --codex-home ~/.codex-efficient \
  --eval-command 'make test'
```

Use separate `CODEX_HOME` directories or Codex profiles for baseline and experimental configurations. Do not change model/reasoning/task at the same time as the feature being benchmarked unless the experiment is explicitly about that combined system.

Run artifacts are written under `.agent-bench/runs/` by default.

## `bench-compare.py`

Render one or more `metrics.json` files as a compact Markdown comparison.

```bash
python3 tools/bench-compare.py \
  .agent-bench/runs/*default*/metrics.json \
  .agent-bench/runs/*efficient*/metrics.json
```

Acceptance must remain non-inferior before lower token/time numbers are called an improvement.
