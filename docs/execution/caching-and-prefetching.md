# Caching and prefetching

Caching should be layered. Different caches reduce different costs.

## 1. Model-context reuse

Keep durable instructions and architecture stable. Avoid constantly rewriting global instruction files with progress. Put volatile progress in separate machine-readable state.

## 2. Repository semantic index

Precompute inexpensive metadata before expensive model work:

- files and hashes
- languages
- imports and dependency edges
- exported/public symbols
- references where reliable
- build/test ownership
- generated/vendor classification

Use language-native tooling when available, with generic tools such as ripgrep, Tree-sitter, ctags, SCIP, or AST tooling where appropriate.

## 3. Decision cache

Persist what the model already decided and what evidence validated it. Reopen source when invalidated, not simply because a later stage wants reassurance.

## 4. Diagnostic reduction

Capture full logs to disk and feed the model compact results first:

- pass/fail counts
- failing target names
- diagnostic code + file + line + message
- paths to full logs for targeted inspection

## 5. Build and dependency caches

Warm language/toolchain caches before long agent runs. Examples include compiler caches, incremental build metadata, package stores, language-server indexes, test caches, and already-running local services.

## 6. Filesystem prefetch

Usually low priority for ordinary source repositories on SSD/NVMe. Model inference and tool orchestration normally dominate raw source-read latency. Measure before adding explicit page-cache machinery.
