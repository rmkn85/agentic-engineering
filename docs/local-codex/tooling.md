# Deterministic tooling and concise output

## Objective

Anything that can be computed exactly without model inference should normally be computed exactly without model inference.

This does not mean “never let the model inspect code.” It means do not spend model turns rediscovering facts a local tool already knows.

## Retrieval ladder

Use the cheapest adequate representation first:

1. **Git metadata** — tracked files, blob IDs, changed paths, rename detection.
2. **Text search** — `rg`, `git grep`, `fd`/`find`.
3. **Symbol index** — universal-ctags, LSP, SCIP where available.
4. **Structural search** — `ast-grep`, compiler/AST tooling.
5. **Dependency graph** — language-native build/package tools.
6. **Full file content** — when semantic reasoning actually needs it.
7. **Broad model-driven exploration** — only when deterministic retrieval cannot narrow the problem.

The model may still need every file for a specific task. In that case the index is still useful **after** the first read, so later reference questions do not force unnecessary rereads.

## Tier-0 repo inventory

`tools/repo-index.py` builds a generic JSONL inventory from Git-tracked files using Git blob IDs, sizes, extensions, and line counts. It does not use an LLM.

```bash
python3 tools/repo-index.py --repo . --output .agent-cache/repo-index.jsonl
```

Use richer language-specific indexes where they exist. Do not replace a compiler-quality symbol graph with embeddings just because embeddings sound agentic.

## Quiet command protocol

Full logs belong on disk. Model-visible output should answer:

- did it succeed?
- what failed?
- what compact evidence should be inspected next?
- where is the full evidence if deeper inspection is needed?

`tools/quiet-run` implements a minimal layered version of that pattern:

```bash
tools/quiet-run -- pytest -q
tools/quiet-run -- cargo test
tools/quiet-run -- npm test
```

Each run writes a small bundle under `.agent-cache/logs/`:

```text
<run>/
  manifest.json
  failure-excerpt.log   # failures only
  full.log
```

On success it prints one compact line. On failure it still prints one compact line, pointing to the manifest, retained failure excerpt and full log. The excerpt is **not** pasted automatically into model context unless `QUIET_RUN_INLINE_FAILURE=1` is explicitly set.

The agent should inspect progressively:

```text
status / manifest
-> failure excerpt if needed
-> targeted `rg`/`sed`/parser slice of full log
-> whole full log only when necessary
```

For processes that can terminate completely, use the same idea at larger scale: [`../runtime/postmortem-bundles.md`](../runtime/postmortem-bundles.md) defines a manifest that can link to focused stack/event/environment/trace artifacts and then to minidumps/cores/heap dumps/full logs without requiring the dead process to answer queries.

## Prefer native structured protocols over terminal scraping

If a tool already emits a stable machine-readable protocol, use it before parsing styled console output.

Examples include:

- compiler/linter JSON diagnostics;
- JUnit or equivalent structured test reports;
- SARIF static-analysis findings;
- Bazel Build Event Protocol / build-event services;
- OTLP/OpenTelemetry telemetry;
- profiler/dump query tools that can extract top/relevant records without rendering the whole artifact.

Reduce structured output deterministically to stable failed identities, locations, codes, counts and artifact references before involving a model.

## Prefer structured summaries

Examples:

```bash
git status --short
git diff --name-status
git diff --stat
rg -l 'SymbolName'
```

before dumping:

```bash
git diff
rg 'SymbolName' .
```

For compiler/test tools, prefer machine-readable or terse modes and locally reduce them to `file:line:code:message` or another project-stable schema where possible.

## Validation ladder

A generic efficient validation sequence is:

```text
syntax/parse
-> formatter/lint for affected units
-> type/compile affected units
-> affected tests
-> broader integration checks at a meaningful boundary
-> one final full validation when the task requires it
```

Repeat broad checks only when new changes or evidence invalidate the previous result.

Current OpenAI model guidance explicitly recommends calibrating test scope and avoiding repeated broad testing when already-passing checks have not been invalidated.

## Tool-output measurement

For each benchmark, record at least:

- number of command executions
- bytes of raw stdout/stderr saved locally
- bytes/lines actually emitted back to the model where measurable
- number and total size of diagnostic artifacts opened by the model
- failed command count
- repeated identical commands
- repeated broad test runs

A tuned system should often increase local retained evidence while **decreasing model-visible diagnostic tokens**. That is a win when diagnosis/acceptance remains non-inferior: evidence is preserved without forcing the model to ingest it.
