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
The line and manifest also carry a SHA-256 receipt for the full log. The receipt identifies exact content; the bundle path identifies where that content is currently retained.

On failure, inspect in this order:

1. the one-line result / `manifest.json`;
2. `failure-excerpt.log` if the failure class is not already clear;
3. targeted searches/slices of `full.log`;
4. the entire `full.log` only when genuinely necessary.

For exact, bounded recall, use `observation-recall.py` with the manifest from that run:

```bash
python3 tools/observation-recall.py .agent-cache/logs/<run>/manifest.json --find 'test_name'
python3 tools/observation-recall.py .agent-cache/logs/<run>/manifest.json --lines 120:15
python3 tools/observation-recall.py .agent-cache/logs/<run>/manifest.json --bytes 4096:512
```

Line spans are `START:COUNT` with one-based lines; byte spans use a zero-based offset. Recall verifies the artifact hash before emitting output. The default output limit is 16 KiB; narrow the request or explicitly raise `--max-output-bytes` when more evidence is needed. Bundles are local transient state and are not a durable evidence store.

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

Run artifacts are written under `.agent-bench/runs/` by default. The runner exposes that exact directory as `AGENT_RUN_ARTIFACTS` to the agent process and evaluation command. An authorized producer may write one `practice-feedback.json` there using the [existing practice lifecycle](../docs/evidence/practice-lifecycle.md) format. After evaluation, the runner validates it, checks referenced local artifact digests and retains `practice-summary.json`; `metrics.json` records `recorded`, `not_recorded` or `invalid` separately from native acceptance. No prompt is injected, model call added or sandbox permission widened; use the existing authorized evaluator if the agent cannot write the run directory. Missing feedback is not inferred use, zero cost or failure of the game.

## `practice_feedback.py`

Analyze agent-neutral feedback from any existing run/evaluation path. No Codex installation is needed for this offline analyzer:

```bash
python3 tools/practice_feedback.py run/practice-feedback.json --evidence-root run --output run/practice-summary.json
```

Records name practice/revision, trigger, decision and reported stage (`not_used`, `selected`, `loaded`, `applied`), with self-report/tool-trace/independent-review attribution kept distinct. Evidence is an exact local file or inclusive line range plus SHA-256. Use fixed ranges for logs still being appended. Evidence-root confinement and digest checks do not establish truth or independence; inspect native traces/diffs for that judgment.

For records sharing an authorized evidence root, pass multiple receipt paths to summarize by task class and record kind. Fixtures never count as live agent trials. Unknown metrics retain known/total denominators instead of becoming zeros, duplicate run IDs are rejected, and detail stays in the report. Exit 0 means valid analysis, not accepted work; exit 2 means malformed input. The tool does not execute evidence, fetch URLs, upload data, overwrite output or create telemetry services. Keep reports private and use existing retention/privacy policy.

## `bench-compare.py`

Render one or more `metrics.json` files as a compact Markdown comparison.

```bash
python3 tools/bench-compare.py \
  .agent-bench/runs/*default*/metrics.json \
  .agent-bench/runs/*efficient*/metrics.json
```

Acceptance must remain non-inferior before lower token/time numbers are called an improvement.
