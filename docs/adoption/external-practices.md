# Ponytail and Graphify: upstream reuse with observable use

Reviewed: 2026-09-26. Entry point: [using-external-practices](../../skills/using-external-practices/SKILL.md).

## Adoption decisions

| Upstream | Integrated capability | Deliberately not enabled |
| --- | --- | --- |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | Whole pinned checkout; unmodified `ponytail-review` skill emitted on demand for bounded complexity review | Persistent full/ultra persona, host/global hooks, automatic acceptance of a smaller diff |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Actual pinned `graphifyy` package in an isolated editable installation; local code extraction, query, explain and path | Hosted platform, graph database, MCP service, semantic docs/media ingestion, global graph-first rules |

The [pin file](../../configs/external-practices.json) is the installation source
of truth. This is a supported-component integration, not a fork, rewritten skill,
or homegrown graph engine. Upstream retains ownership of parsers and skills. Our
boundary owns invocation, input identity and receipts. The package installer may
resolve transitive dependencies; its `pip freeze` is retained with setup evidence.
The source pin is not a claim of a fully hermetic dependency lock or security audit.

## Use from any authorized Git checkout

Let `AE` be the path to a maintained Agentic Engineering checkout and `PROJECT`
the consuming repository root. No global host configuration is changed.

```sh
# Explicit, once per pin/environment. Does not contact any model provider.
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" setup ponytail \
  --task setup-external-practices --why 'Enable bounded complexity reviews'
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" setup graphify \
  --task setup-external-practices --why 'Enable cross-file relationship lookup' --timeout 600

# Only when relationship discovery warrants it; use the SAME scope when querying.
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" build \
  --scope src --task CHANGE-123 --why 'Locate callers across module boundaries'
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" query \
  --scope src --task CHANGE-123 --why 'Find the affected dependency path' 'normalize'

# Emit the actual upstream reviewer skill for the current agent/reviewer.
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" load \
  --task CHANGE-123 --why 'Check the proposed implementation for unnecessary mechanisms'
```

`path` takes two positional entity names; `explain` takes one. `load` does not
spawn a model: the available agent must read and apply the emitted review skill.
Whole-session Ponytail modes are not automatically injected or claimed tested.
The setup requires Git/network access; Graphify also needs Python 3.10+ and venv/pip.
The core regression suite remains Python 3.9+/Git only, with no external packages.

For a considered nonuse, `skip graphify --task CHANGE-123 --why 'Exact symbol lookup is sufficient'`
records `not_used`; do not require this ceremony on every trivial edit.

## Where, why, how, how much, and effect

Each instrumented operation has a UUID and immutable receipt under
`$PROJECT/.agent-cache/external-practices/runs/`. `--cache PATH` selects another
explicitly authorized private root. Keep cache/source/evidence out of version
control. Verify the default cache is ignored by the consuming repository, or use
`--cache` outside its source tree. The adapter does not edit project ignore rules.
The adapter records an existing `AGENT_RUN_ARTIFACTS` locator when present;
it does not overwrite a benchmark's own receipt or impersonate its evaluator.

| Question | Evidence |
| --- | --- |
| Where? | Consuming repository/scope, source commit, existing task ID, native-run locator |
| Which implementation? | Pinned upstream revision, integration/lock digests, exact command arguments and setup logs |
| Why/how? | Concrete trigger, operation, selected/loaded/applied/not-used stage; source-input and graph identity for Graphify |
| How much? | Instrumented records and attempted subprocess calls, wrapper wall time, retained output bytes, emitted skill bytes, cache hits; setup/fixtures/failed attempts remain separate |
| What changed? | Explicit assessment, decision/finding evidence, reported acceptance and an optional matched-comparison reference |
| What is unknown? | Undetected/unwrapped use, actual model consumption of emitted text, tokens, total agent cost, peak memory, installed footprint, downstream benefit without assessment, causal savings without a controlled comparison |

```sh
# RUN is the UUID returned by an operation. Evidence is a file within PROJECT.
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" assess RUN \
  --status accepted --effect 'Reused the existing normalizer; preserved caller behavior' \
  --evidence evidence/CHANGE-123.diff --evidence evidence/CHANGE-123-checks.log

python3 "$AE/tools/external_practices.py" --repo "$PROJECT" report
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" report --details
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" report --json > "$PROJECT/.agent-cache/external-usage.json"

# Combine explicitly authorized roots without a server or automatic workspace crawl.
python3 "$AE/tools/external_practices.py" --repo "$PROJECT" report --details \
  --include-cache /path/to/another-project/.agent-cache/external-practices
```

The assessment is a separate, non-overwriting record, attributed `self_report`.
A digest match establishes artifact identity, not independent judgment. Inspect
native diffs/checks; do not submit a successful graph command as product acceptance.
Blocked attempts cannot be relabeled accepted; retain them and create a new attempt.
Reports expose missing/tampered evidence and pending effects. No receipt does not
mean no use. Emitted bytes are not measured tokens, and bytes retained are not bytes
actually read by a model. Aggregate setup, fixtures and agent runs separately.

An existing [practice-feedback analyzer](../../tools/practice_feedback.py) can also
consume the original `practice-feedback.json` files with this cache as evidence
root. It intentionally retains the original unverified outcome; later assessments
are shown by the external-practice report, not retroactively forged into tool traces.
For causal comparisons use the existing [benchmark path](../../tools/README.md):
match task, source, instructions, model, permissions and acceptance; include index
build/update/setup costs when relevant. Keep unsuccessful attempts in the comparison.

In the Agentic Engineering checkout, `make external-report` is the compact report
entry point. For consuming repositories use the explicit `--repo` form above.
One existing run/handoff can link several operation receipts; do not introduce a
second task tracker or a prose record for each internal subprocess.

## Freshness, coverage and failure handling

Graphify output is built in a fresh operation directory; only a successful stable
build publishes the active pointer. The adapter hashes tracked and nonignored
untracked working-tree contents in the selected scope, checks upstream revision,
and verifies retained graph bytes. It checks inputs again after execution. A warm
build reuses a matching index without invoking Graphify. Queries never auto-build
or silently accept stale state. Failed/time-limited commands leave logs and blocked
receipts; narrow scope or fix the actual cause before scaling.

This is a conservative Git-working-set identity, NOT a language-coverage proof.
Ignored source, symlink inputs, submodules and semantic docs/media ingestion are
outside this first integration's contract. Unsupported languages or unresolved
edges require native tools/source inspection. Do not force Graphify into a task
where it cannot produce trustworthy relationships. Environment/ignore-policy
changes also require an explicit new cache/build; source identity alone does not
capture every possible external input.

## Adoption, updates, retention and removal

The normal corpus routes here conditionally; existing task constraints and
verification remain authoritative. The integration is available after fetching the
repository; that is not proof of delivery/application in every host or child agent.
Run a fresh task on each adopting surface and retain observed loading/actions.
Do not duplicate these instructions into every host's global config.

Upgrade by reviewing the upstream diff, changing the pin in a normal code review,
running offline tests and the bounded upstream smoke, and repeating a representative
accepted task. New pins use separate installations. The smoke is an integration
fixture, not proof of better development, weaker-model adherence, or lower cost.

No global hooks are installed. Stop routing to this skill to disable it. Remove an
owned private cache only after retaining any required receipts/evidence. Active graph
pointers refer to build bundles: deleting those bundles invalidates the cache. Logs,
queries, source paths, prompts and diffs may be sensitive; use existing project
retention/access rules. No automatic upload or public telemetry is performed.

## Verified integration boundary

The first integrated source, commit
[`eb73fbc`](https://github.com/rmkn85/agentic-engineering/commit/eb73fbc3ef8b3f104863b0accce0da1a2a133dce),
passed these checks on 2026-09-26:

- [Native contributor checks](https://github.com/rmkn85/agentic-engineering/actions/runs/36243423969):
  `make check` passed from both cold and stale committed-source checkouts.
- [Pinned external-practice checks](https://github.com/rmkn85/agentic-engineering/actions/runs/36243424082):
  13 offline adapter tests passed; the actual pinned upstream packages passed a
  two-file fixture covering unchanged Ponytail skill delivery, a cross-file call
  relationship, located query output, explain/path, warm reuse, stale-query
  rejection, rebuild and successful query after the change.

The fixture report retained 11 instrumented records: the intentionally blocked
stale query stayed visible, and all 11 effects remained unassessed rather than
being invented. Three Graphify build records invoked the extractor twice and
reused the graph once. The Ponytail delivery emitted 2,383 skill bytes; this is
not a measurement of model consumption or useful review.

These checks establish bounded integration mechanics, not improved development
quality, universal parser coverage, host/subagent adoption, token savings or causal
benefit. Run `make external-smoke` to repeat the real-upstream fixture (network and
installation required); normal `make check` stays offline. CI runs the network
smoke only for relevant integration changes or manual dispatch. Its summary/logs
use normal Actions retention; full private cache bundles on ephemeral runners do
not survive job cleanup. Preserve required evidence through the adopting project's
existing authorized retention path, not by uploading every graph or raw log.
