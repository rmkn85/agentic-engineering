# Deterministic efficiency tools

These helpers exist to move exact work out of the model and make optimization measurable.

## `quiet-run`

Capture full command output locally while exposing only a compact result and links to progressively deeper evidence.

```bash
tools/quiet-run -- pytest -q
tools/quiet-run -- cargo test
```

Each run creates a small diagnostic bundle:

```text
.agent-cache/logs/<run>/
  manifest.json
  failure-excerpt.log   # failures only
  full.log
```

The command prints one line containing status, timing/size metadata, and paths to the manifest/excerpt/full log. It does **not** paste the excerpt into model context by default.

On failure, inspect in this order:

1. the one-line result / `manifest.json`;
2. `failure-excerpt.log` if the failure class is not already clear;
3. targeted searches/slices of `full.log`;
4. the entire `full.log` only when genuinely necessary.

Environment controls:

- `QUIET_RUN_LOG_DIR` (default `.agent-cache/logs`)
- `QUIET_RUN_TAIL_LINES` (default `80`, controls the retained failure excerpt)
- `QUIET_RUN_INLINE_FAILURE=1` explicitly prints the excerpt for interactive use; leave unset for agent-efficient operation.

This is deliberately a minimal example of a **postmortem evidence graph**: compact manifest first, retained detail behind references. More capable applications should use the same principle with structured events, environment fingerprints, traces, dumps, profiles and other artifacts.

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
  --codex-home /tmp/codex-benchmark-profile \
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
