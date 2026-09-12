# Linux Mint + Cursor AppImage + Local Codex

## Goal

Make Cursor a thin editor/terminal around a persistent, warm local Codex environment. The editor packaging should not cause dependencies, indexes, caches, or Codex state to be rebuilt per task.

## 1. Install Codex independently of Cursor

Use the standalone Codex CLI so an editor update or AppImage replacement does not affect the agent runtime:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex
```

Sign in with ChatGPT when using plan allowance, or configure API authentication deliberately when you want API billing. Current Codex documentation also supports npm and release-binary installation.

Verify inside **Cursor's integrated terminal**, not only an external shell:

```bash
command -v codex
codex --version
```

If `codex` is absent there, fix `PATH` in the interactive shell configuration (`~/.bashrc` on a normal Mint bash setup) rather than adding an editor-specific copy of Codex.

## 2. Cursor AppImage is only the editor layer

Cursor supports AppImage on Linux (`chmod +x Cursor-*.AppImage && ./Cursor-*.AppImage`). Cursor currently recommends its apt package for tighter desktop integration, but using AppImage does not prevent the local Codex strategy.

Keep repositories, package caches, compiler caches, Codex state, and helper tools outside the AppImage. Replacing the AppImage should therefore have essentially zero warm-up cost for the engineering environment.

Choose the intended shell in Cursor with **Terminal: Select Default Profile** and verify that it loads the same environment used by external terminals.

## 3. Prefer CLI for measured runs

For ordinary interactive work, use whichever local Codex UI is most convenient. For efficiency experiments, use:

```bash
codex exec --json "<task>" > run.jsonl
```

A completed turn includes usage such as:

```json
{
  "input_tokens": 24763,
  "cached_input_tokens": 24448,
  "output_tokens": 122,
  "reasoning_output_tokens": 0
}
```

This makes prompts/config/skills/local-vs-cloud claims testable instead of anecdotal.

The repository tool `tools/codex-bench.py` wraps this into reproducible Git worktrees and records metrics.

## 4. Persist state on fast local storage

Keep these persistent across sessions:

- repo and Git object database
- Codex home/state DB
- language/package caches
- build outputs that support incremental compilation
- test caches
- language-server/index data
- `.agent-cache/` deterministic inventories and full logs

Codex currently exposes `sqlite_home` for its resumable SQLite state. Its stable `shell_snapshot` feature is enabled by default to accelerate repeated command execution. Do not disable it without a benchmark showing a reason.

## 5. Warm dependencies before expensive model work

A model should not spend turns rediscovering whether the environment can build.

Before a substantial task, establish a known baseline with deterministic commands:

```text
dependency restore is complete
build succeeds or known failures are recorded
tests have a known baseline
format/lint versions are fixed
required local services are available
```

Use ecosystem caches rather than generic reinvention:

- C/C++: `ccache` or `sccache`, Ninja/incremental build directories
- Rust: Cargo registry/git cache, `target/`, optionally `sccache`
- Python: package/wheel cache, venv/uv environment, pytest/type-check caches
- JS/TS: pnpm/npm store, existing dependency tree, TypeScript incremental state, linter/bundler caches
- JVM: Gradle daemon/build cache or Maven local repository
- Go: module and build caches

## 6. Separate editor indexing from Codex evidence

Cursor may maintain its own code index. Do **not** assume Codex CLI automatically consumes that index.

Give Codex access to deterministic local interfaces that any agent can use:

- `git ls-files` / Git object IDs
- `rg` / `git grep`
- universal-ctags or a language server for symbols
- language-native module/dependency graphs
- a small generated repo inventory

This avoids tying the methodology to one editor and makes benchmark results portable.

## Current references

- Codex install and local CLI: https://github.com/openai/codex
- Codex configuration index: https://learn.chatgpt.com/docs
- Cursor Linux/AppImage quickstart: https://prod.cursor.com/docs/get-started/quickstart
- Cursor terminal behavior: https://prod.cursor.com/docs/agent/tools/terminal
- Codex non-interactive JSONL: https://learn.chatgpt.com/docs/non-interactive-mode

Last reviewed: 2026-09-12.
