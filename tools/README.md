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

## `external_practices.py`

Use pinned upstream Ponytail review and Graphify local code relationships through
an opt-in, instrumented route. The [adoption guide](../docs/adoption/external-practices.md)
and [conditional skill](../skills/using-external-practices/SKILL.md) define setup,
use, freshness, effect assessment, and private evidence retention.

```bash
make external-report
python3 tools/external_practices.py --repo /path/to/consumer report --details
```

Receipts reuse `practice-feedback/v1`. Reports distinguish setup, selected/loaded/
applied/nonuse, fixture/live records, failed attempts and unknown effects. Loading
Ponytail is not applying its advice; Graphify execution is not accepted development.
No global hooks, model provider calls, graph service or automatic uploads are added.
`make external-smoke` runs the separate network-enabled pinned-upstream fixture;
it is not a prerequisite for normal offline `make check`.

## `bench-compare.py`

Render one or more `metrics.json` files as a compact Markdown comparison.

```bash
python3 tools/bench-compare.py \
  .agent-bench/runs/*default*/metrics.json \
  .agent-bench/runs/*efficient*/metrics.json
```

Acceptance must remain non-inferior before lower token/time numbers are called an improvement.

## Bounded local Codex settings activity

The executable `./tools/make` is a strict activity parser, **not GNU Make**.
It accepts exactly one of these forms and one declared argument:

```bash
./tools/make codex-settings-plan HINT_FILE=/private/path/reviewed-hint.txt
./tools/make codex-settings-apply PLAN_SHA256=<printed-lowercase-sha256>
./tools/make codex-settings-allowlist PLAN_SHA256=<printed-lowercase-sha256>
```

This optional activity requires Python 3.11+, standard-library `tomllib`, and
POSIX ownership/mode APIs (`os.getuid`, `fchmod`).
Normal `make check` still supports Python 3.9+; transformation tests skip when
`tomllib` is unavailable. No packages are installed. There are no destination,
profile, permission, model, command, GNU Make option or additional-goal overrides.
Shell-quote the entire `HINT_FILE=...` argument when its path needs quoting.
Do not pass hint contents as executable shell syntax.

The destination is always the native `~/.codex/config.toml`. Planning reads an
owned UTF-8 hint file with no group/other permissions, validates the TOML, and
prepares exactly two changes: remove the top-level
`model_auto_compact_token_limit` override and replace
`features.multi_agent_v2.multi_agent_mode_hint_text` with that literal text.
The helper requires both existing settings, an integer compaction override and
an explicit `[features.multi_agent_v2]` section with a string hint assignment.
Other spellings or ambiguous transformations can be refused. It compares the
parsed result against precisely these allowed changes and retains unrelated
text, comments, saved models and reasoning effort.

Planning leaves the config unchanged. It saves only the allowed operations,
hint and original/result digests in a mode-0600 JSON plan under a fixed,
owned mode-0700 `codex-settings-<uid>` directory in the system temporary root.
The printed SHA-256 identifies the exact plan. Apply verifies that receipt and
the current config, creates a private original backup in the same cache, then
atomically replaces the config while preserving its file mode. Repeating apply
with the expected result reports `already_applied`. Retain the private cache
for backup recovery according to your own retention policy; it contains private
hint text and, after apply, a full private config backup. Do not publish it.

Symlink paths, changed plans/configs and undeclared arguments are refused.
Drift checks are not locks and do not exclude a simultaneous writer between the
final check and replacement. Coordinate other config writers before apply.
Output contains actions, digests and status; errors omit underlying parser/OS
messages that could reveal private values. This wrapper constrains activity
arguments; approval rules and operating-system permissions remain external.

After the planned settings are applied, `codex-settings-allowlist` can install
one persistent native approval rule. Its first invocation requires native
approval for this fixed installation activity; it never authorizes itself.
It revalidates the private digest-bound plan and requires the current config to
match the exact planned result. It writes only
`~/.codex/rules/agentic-engineering-settings.rules`, allowing exactly the
absolute sibling `tools/make` executable followed by `codex-settings-apply`.
The strict wrapper continues to validate that activity's one digest argument.
There are no caller-selected rule prefixes or destination paths.

The installer creates a missing owned rules directory with mode 0700 and a
missing dedicated rule file exclusively with mode 0600. An identical owned,
private regular file reports `already_installed`; different content, symlinks,
foreign ownership or directories writable by group/others are refused.
Existing rule files and directory modes are preserved. No config is changed.
Run installation from the intended stable canonical checkout, after integration;
do not install from a temporary worker worktree that will be retired. The
absolute wrapper prefix identifies that execution checkout. The rule trusts
maintained, mutable code at that absolute path, not an immutable code digest. Review later changes to that wrapper and helper accordingly.
Installation is separate from fresh-runtime adoption: verify the native rule
load and approval behavior in a fresh runtime before claiming adoption. The
installer's drift checks do not exclude simultaneous external writers.


## Documentation-result preflight

`docs_result_cache.py` is a Python-standard-library offline cache for explicit native MCP callers. There is no new network client, proxy, credential handling, mandatory service or global interception. Run it from the owner checkout; the default private directory is `.agent-cache/docs-results` (already ignored). The coordinator must pass one shared ignored private `--cache-dir` and the same nonsecret namespace to cooperating workers using the same client/auth scope, including sibling worktrees. Separate defaults cannot suppress each other's probes. Different namespaces represent actual different clients/accounts/permissions, never a workaround for a blocked gate. Concurrent records are written atomically with unique immutable response files; gate updates use a bounded exclusive lock and retain every unresolved failure boundary, so a later finite outage cannot shorten an unknown quota or a later reset. Valid exact cached hits remain available during gate updates. A pending gate lock blocks new probes; update contention waits at most five seconds and then exits with an error. After interruption, inspect the preserved raw records and establish that the lock owner has stopped before removing an owned stale lock; do not blindly retry or delete failure state. This is not a reservation/single-flight service, so coordinate concurrent producers in the existing task owner path. Only share a directory whose writers are trusted. Hashes detect accidental corruption, not hostile rewriting by those writers.

Create a private request JSON file with exactly these fields (neutral example):

```json
{"provider":"context7","operation":"query-docs","arguments":{"libraryId":"/org/library/v2","query":"Configure routing"},"namespace":"public-docs-client-a","source":"https://docs.example/library/v2"}
```

`arguments` must match the actual MCP call exactly; do not add a language field that the native operation does not accept. Put any relevant language/version not present in native arguments in `source`, without claiming the provider supplied a version it did not. Use the actual operation name. A resolution request has its own operation/arguments/source identity. The namespace is a nonsecret client/auth-scope label, never a token or copied config. Change it only when scope actually changes; do not rotate it to bypass a provider failure gate. Source identity must change when known provider/source revision or freshness requirements invalidate the old result; the offline tool cannot discover upstream changes itself.

```sh
python3 tools/docs_result_cache.py lookup --request request.json --max-age 3600
```

Inspect the JSON status. A valid exact cached success remains usable while a provider gate blocks new calls. On `hit`, use `response` and retain the returned record path/hash; on `blocked`, inspect the failure evidence and obey the boundary. On `miss`, perform the authorized native MCP call, save its actual JSON response to a private file, then classify and record it:

```sh
python3 tools/docs_result_cache.py record --request request.json --response response.json --kind success --valid-for 3600
python3 tools/docs_result_cache.py record --request request.json --response response.json --kind quota
```

Choose `quota`, `auth`, `spend` or `outage` only for provider-wide failures; `request` represents a request-specific failure such as a missing page. These are never reusable documentation. The tool rejects explicit MCP error envelopes classified as success, but the caller must inspect plain strings and error content too. Record only the observed message; do not infer an HTTP status, reset metadata or account scope absent from the response. A known future provider boundary may be recorded with `--retry-at 2026-11-01T00:00:00Z`; do not invent a reset date. Without it the gate remains until meaningful changed-condition evidence:

```sh
python3 tools/docs_result_cache.py release --request request.json --evidence 'Provider status confirms restoration after the recorded outage'
```

Release requires an existing gate and keeps its prior failure reference and the evidence in the gate; it does not create docs or prove the explanation. The caller remains responsible for evidence quality and authorized retry. Corrupt/missing failure evidence blocks probes pending inspection. Invalid/missing docs produce a miss. `--cache-dir PATH` goes before the subcommand. Malformed input exits 2; status results exit 0, so callers must inspect `status`. Preserve useful raw evidence before normal owned-cache cleanup. Do not publish private cache files. This is an opt-in command workflow: normal-stack model adoption and actual provider use need separate trials.

## Context7 native stdio cache default

`context7_cache_stdio.py` is the optional deterministic integration for Context7's newline-JSON stdio MCP transport. After the reviewed native configuration switch and MCP client restart, agents issue ordinary `tools/call` requests; the bridge performs preflight and recording without a reminder. It forwards initialization, tool listing, notifications and other protocol messages to the existing child. It preserves request IDs and stores actual child tool results before adding `_meta.context7Cache` status/source/hash to the returned result. Metadata distinguishes `hit`, `produced`, `blocked` and failure outcomes for a bounded activation check. A current session may retain the old server: a fresh subagent does not prove a fresh MCP connection.

The default child is pinned `npx -y @upstash/context7-mcp@4.4.2`; this version and the resolution response format were inspected in installed package source on 2026-10-18. This is source inspection, not a successful authenticated provider trial. Resolution positives require the known library-list shape; documentation positives require source-linked code/heading content. Unknown prose and explicit errors are retained as request failures, never cached documentation. Known leading quota/auth/spend/outage messages establish the corresponding shared gate without inferring HTTP status, retry metadata or account identity. Unsupported successful shapes can remain uncached; revise recognition only with source/evidence, not speculative keyword expansion.

All clients configured with the same absolute workspace cache path and nonsecret client/auth namespace share successful results and failure gates across working directories and worktrees. One bounded provider-scope producer lock covers lookup through response recording, preventing concurrent sibling misses from duplicating a producer. Waiting is finite; abandoned locks require owner/evidence inspection. Child response deadlines stop the child and return an error, without an automatic retry. Initialize/list calls may still start the child even when docs are cached; the measured avoided work is documentation production, not process startup or model tokens. Server-initiated protocol messages pass through while a docs result is pending.

Use the separate maintained `tools/make` activities to prepare and apply the native change; the existing `codex-settings-*` activities retain their previous scope. Prepare a private JSON specification with `config`, `workspace`, `repository`, `namespace`, `max_age`, `valid_for` and optional boolean `forward_api_key` or private staged `auth_config` path. Paths must be absolute; the external activity additionally requires the canonical running repository, its workspace parent and the current user's native config. Choose the existing real client/auth namespace and cache root; do not bypass a recorded gate by inventing a label. Root coordination owns that concrete identity. `forward_api_key: true` adds only the environment name `CONTEXT7_API_KEY` to `env_vars`, preserving existing names and the env map. It does not acquire, copy or print a secret or prove the MCP host has that variable.

```sh
./tools/make context7-cache-plan SPEC_FILE=/private/review/context7-cache.json
./tools/make context7-cache-apply PLAN_SHA256=<reviewed-64-character-hash>
```

`make context7-cache-plan SPEC_FILE=...` and `make context7-cache-apply PLAN_SHA256=...` route to those maintained activities. The plan is read-only toward native config and returns only the command/args (and optional env-name) diff. Private plan/backup files use mode 0600. Apply checks the reviewed plan hash, exact source-file set and hashes, config content/mode drift and the candidate hash, then reconstructs the supported Context7-only transformation before replacing config atomically. An altered plan with a recomputed hash still cannot install arbitrary child arguments, change unrelated env values or settings, or redirect the host activity to another repository/config. Unsupported remote/auth migrations and duplicate TOML tables are rejected. The child override exists for sandbox fixtures; the host activity never emits it.

Generate the production plan after the reviewed files are integrated at the canonical repository path; temporary worktree paths are not durable installation targets. Review the concrete diff, approve only the parameterized apply activity if required, and restart the native MCP connection through its supported UI. Observe `_meta.context7Cache` on one bounded ordinary native call before claiming activation. The offline regression launches separate cold MCP clients and confirms shared hits, quota cross-operation suppression, protocol forwarding, concurrency, invalidation and child failure. This proves the fixture integration only; live host activation/authentication and model adherence remain separate evidence. The bridge preserves stdio authentication; a dashboard/CLI login alone does not authenticate that child. The fixed-key staging adoption below is a separate supported configuration action.


For an existing official Context7 CLI device login, an owner may run the official CLI's project-scoped stdio setup in a private task staging directory. The native config activity can adopt its `auth_config` path only beneath the workspace's `.agent-cache/context7-auth/.../.codex/config.toml`. It does not inspect the CLI's login store, implement OAuth or acquire a key itself. The staging root must be owned mode0700; its nonsymlink config and the target native config must be owned/private mode0600. The accepted source is the inspected official stdio shape `npx` with the package plus one `--api-key` pair; arbitrary child/auth configurations are rejected.

With `auth_config`, use the fixed nonsecret namespace `context7-stdio-cli-auth`. The tool privately extracts and validates only the staged Context7 key, binds the entire auth-input hash at plan/apply, and adds or updates only `[mcp_servers.context7.env].CONTEXT7_API_KEY`. It preserves other env entries and settings, rejects unsupported existing env spellings safely, and returns a redacted env change without the key. Private plan/candidate/backup artifacts contain configuration material and must remain private; do not print or publish them. Auth-file drift, unsafe permissions, paths outside staging, symlinks and rehashed out-of-scope mutations are rejected. The anonymous failure gate stays in its original namespace. Key adoption and native authentication success remain separate claims until the restarted MCP connection is exercised.


## Bounded native Context7 acceptance

After the configuration activity, `./tools/make context7-cache-probe CONFIG_SHA256=<reviewed-native-config-hash>` is the maintained external acceptance activity. It has no command, config-path, cache-path, query or credential arguments. It reads only the canonical native config, verifies its reviewed hash before parsing/using credentials, requires owned mode0600 and the exact supported authenticated bridge launch, and privately passes that fixed env to the child. It does not change native configuration or the running app's MCP connection.

The activity starts an owned native stdio process group, initializes MCP, lists tools, and asks one fixed Context7 CLI stdio-authentication resolution question. After a successful produced/hit response, it verifies the identical valid record offline before starting a second cold client for the same request. A failure, blocked result, missing metadata or invalid cache prevents that second trial. The activity itself adds the bridge's fixed `--cache-only` flag to the second client: expiration or invalidation after the offline check returns an error and cannot reach a documentation producer. Only matching hit metadata proves the second client reused the response. This tests native configured execution, separately from the desktop app's retained connection; it does not prove app hot reload or model usage savings.

Initialization/list/first-call deadlines are 90/15/65 seconds; the second call allows 5 seconds after the same bounded startup. Cleanup terminates the complete owned process group, including descendants, with bounded forced teardown. Raw stderr and protocol artifacts stay in an owned private workspace cache directory with mode0600 files. The command prints only bounded status/phase/hash/error-class metadata and artifact paths, never provider error text, config contents or env values. Required network/npm writes outside a read-only sandbox belong to this single reviewed parameterized activity; do not replace it with an ad-hoc escalated script. An unconfigured or drifted target is refused. Offline tests cover real fixture MCP messages, cold shared hits, launch/drift rejection, redaction and suppression of the second trial when offline evidence is missing.
