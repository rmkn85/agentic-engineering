# Local Codex CLI with any editor

## Goal

Keep the agent CLI, repository state, dependencies, indexes, and caches independent from the editor lifecycle. Replacing or updating an editor should not rebuild the engineering environment.

## 1. Install Codex independently of the editor

Use a supported standalone Codex CLI installation so an editor update does not affect the agent runtime. Check the current official instructions for the operating system and package method in use; for example:

```bash
curl -fsSL https://chatgpt.com/codex/install.sh | sh
codex
```

Sign in with ChatGPT when using plan allowance, or configure API authentication deliberately when you want API billing. Current Codex documentation also supports npm and release-binary installation.

Verify inside the editor's integrated terminal, not only an external shell:

```bash
command -v codex
codex --version
```

If `codex` is absent there, fix the integrated terminal's supported shell or environment configuration rather than adding an editor-specific copy of Codex.

## 2. Keep self-contained editor packages at the editor layer

When an editor ships as a self-contained image or application bundle, keep repositories, package caches, compiler caches, Codex state, and helper tools outside that package. Choose the intended integrated-terminal profile and verify that it exposes the required CLI and dependency versions.

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

An editor may maintain its own code index. Do **not** assume Codex CLI automatically consumes that index.

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
- Codex non-interactive JSONL: https://learn.chatgpt.com/docs/non-interactive-mode

Last reviewed: 2026-09-12.
