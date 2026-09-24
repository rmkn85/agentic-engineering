# Harness tool trials (2026-09-24)

These trials evaluated candidates in two external research notes against this repository's existing tools. They are functional and payload-size checks, not evidence of lower cost per accepted engineering task.

## Observation recall: integrated

The existing `quiet-run` retained full command output and returned a compact bundle path. A 300-line synthetic failure produced 5,780 raw log bytes and a one-line receipt, but the receipt did not bind the bytes or offer exact bounded recall. We added SHA-256 to each bundle evidence entry and [`observation-recall.py`](../tools/observation-recall.py) for verified line, byte, and literal-search retrieval. A matched 300-line run retained the same 5,780 bytes; requesting two middle lines returned those exact lines after hash verification. The contributor regression suite checks exact retrieval, hash mismatch, path escape, and output limits.

This adapts the observation-handle mechanism described by [SoL-Pi](https://github.com/NVlabs/SoL-Pi) to the existing local bundle. It does not install Pi or claim SoL-Pi's reported model-token savings. Actual model-visible reads and accepted diagnosis should be compared on representative noisy failures before claiming an efficiency gain. The local bundle remains transient; no durable storage or deduplication is claimed.

### Skill wording pilot: do not promote

We then tested whether the `efficient-execution` skill should explicitly tell agents to use a hash-bound receipt and bounded recall for large observations. Two isolated in-app workers used the same model, task, checkout commit (`ebe0447`), root instructions and 6,000-line diagnostic fixture. Only the candidate worktree's skill gained this sentence:

> For recurring large observations, keep the exact source and use a hash-bound receipt with bounded recall when available.

Both workers ran the fixture through `quiet-run` and wrote a JSON answer containing the log SHA-256 and every exact assertion line. The independent [`check.py`](fixtures/skill-observation/check.py) accepted both: three correct assertions, 838,653 raw bytes retained, identical SHA-256. In their handoffs, the baseline reported one targeted `rg -n` search; the candidate reported `rg -c` followed by `rg -n`. Neither reported using `observation-recall.py`. These command accounts are worker reports, not an instrumented trace. No per-worker token or cost telemetry was available, so the pilot does not establish a resource difference. It does show that the extra skill sentence was unnecessary for this case; the shared skill remains unchanged.

To repeat this behavioral pilot, use two disposable worktrees from the same commit and change only the candidate's `skills/efficient-execution/SKILL.md` as quoted above. Give each worker the same task, substituting only its checkout and run directory:

```text
Read AGENTS.md, docs/agent-corpus/README.md and skills/efficient-execution/SKILL.md.
Run python3 experiments/fixtures/skill-observation/emit.py through tools/quiet-run,
with QUIET_RUN_LOG_DIR=<run-directory>/logs. Do not read emit.py source.
Diagnose the retained output. Write <run-directory>/answer.json containing
{"sha256":"<full-log digest>","failures":[{"line":<1-based line>,"text":"<exact line>"}, ...]}
for every ASSERTION line in order. Keep model-visible output bounded.
```

Then run `python3 experiments/fixtures/skill-observation/check.py <run-directory>` for each worker. The checker reads the retained raw log, verifies its hash and checks the answer exactly. Compare accepted results and inspect the execution trace for evidence reads and extra calls. For token, wall-time and cost claims, run the same task through an authenticated JSONL harness such as [`codex-bench.py`](../tools/codex-bench.py), then render the `metrics.json` files with [`bench-compare.py`](../tools/bench-compare.py). This pilot's sandbox could not authenticate a nested Codex CLI run, so those measurements remain open.

## MCP schema compression: conditional experiment

We exercised [Atlassian mcp-compressor](https://github.com/atlassian-labs/mcp-compressor) 0.32.1 in an isolated environment against the eight-tool server in [`fixtures/mcp-compressor/`](fixtures/mcp-compressor/). Each variant retrieved the selected full schema and returned the same deterministic tool result as the direct server.

| Route | Initial `tools/list` JSON bytes | Selected schema response bytes | Same result |
| --- | ---: | ---: | --- |
| Direct | 7,105 | 0 | yes |
| Low | 3,965 | 1,105 | yes |
| Medium | 2,021 | 1,105 | yes |
| High | 1,438 | 1,105 | yes |
| Max | 1,202 | 1,105 | yes |

The byte counts are serialized MCP responses, not model tokens. The extra schema lookup and invocation overhead were not measured as model turns or task latency. The fixture uses the MCP Python SDK v1 (`mcp<2`); SDK v2 changed the FastMCP interface used by this fixture. This compatibility pin is a trial detail, not a compressor defect.

Reproduce this optional trial in a disposable environment:

```bash
python3 -m venv /tmp/ae-mcp-trial
/tmp/ae-mcp-trial/bin/python -m pip install 'mcp-compressor==0.32.1' 'mcp<2'
PATH=/tmp/ae-mcp-trial/bin:$PATH /tmp/ae-mcp-trial/bin/python experiments/fixtures/mcp-compressor/trial.py
```

**Decision:** retain the fixture and [conditional selection rule](../docs/local-codex/tooling.md#tool-schema-disclosure); do not add a default dependency or client configuration. A real MCP-heavy task must first show material recurring schema input. Promotion then requires matched direct/compressed runs with full task acceptance, model-visible and cached tokens, tool-selection errors, schema lookups, wall time, and actual cost where available.

## Other candidates

[Astra Flash Orchestrator](https://github.com/ethanplusai/astra-flash-orchestrator) would change model routing and acceptance ownership. The current [subagent policy](../docs/local-codex/subagents.md) already supports bounded delegation; a fixed-task, same-acceptance comparison is needed before adding another profile. [SoL-Pi](https://github.com/NVlabs/SoL-Pi) is a Pi extension; its current upstream version requirement had changed since the supplied notes were written. Its action-fusion and compaction features need host-compatible trials before any Codex-specific integration. Self-hosted inference caches and gateways need an actual serving workload, which this repository does not provide.

## Conditional skill follow-up

We screened three proposed additions against the unchanged `efficient-execution` skill at source revision `dcd142c`. Paired in-app workers used the same model setting, checkout contents, root instructions, task and acceptance checker; only the candidate skill sentence or the explicitly named MCP route changed. The resolved model identity, model tokens and per-worker wall time were unavailable. Worker command descriptions below are self-reports except for the MCP client's `actions.jsonl` trace and independent checker results. The [public fixtures](fixtures/skill-improvements/README.md) provide seeded tasks and reproduction commands.

| Candidate and screen | Independent acceptance | Observed behavior | Decision |
| --- | --- | --- | --- |
| Verified bounded recall: add a trigger for `quiet-run` manifests; 4,500-line, 654,899-byte seeded log with five failed jobs and earlier causes | Both arms passed the exact log, receipt and answer checker | Baseline used targeted `rg` plus a deterministic parser. Candidate also used `rg` plus a parser and did not invoke `observation-recall.py`. An earlier 6,000-line trial had the same non-use. | Keep the optional tool; the skill sentence did not improve this workload. |
| Predictable edit plus validation in one execution step: small status-normalization edit | Both arms passed public tests and eight independent cases | Both edited with `apply_patch` and ran the known test command in a separate tool call. | Do not add this instruction or an action-fusion wrapper based on this screen. |
| Progressive tool disclosure: one of eight similar MCP tools selected through direct or medium compressed route | All four paired tasks (screen seed 11, unseen seeds 12–14) selected the right tool and returned the same result | Compressed runs listed the compact facade, retrieved the chosen schema, then invoked it. Direct runs listed the full catalogue. One direct screen worker repeated its call while saving the answer; one compressed confirmation worker had a CLI syntax retry. | Add a conditional decision rule for recurring large MCP catalogues, without enabling a proxy by default. |

In the three unseen MCP pairs, serialized client response bytes for list plus selected schema plus one call were **7,626 / 3,269**, **7,624 / 3,265**, and **7,624 / 3,265** (direct / compressed). Run order alternated: direct first for seeds 12 and 14, compressed first for seed 13. Each pair passed the independent checker, had zero wrong tool calls, and the compressed route used one extra schema lookup. A separate local protocol timing run for these three seeds measured median **1.87 s direct** and **2.86 s compressed** for the complete list/lookup/call sequence. This timing excludes model reasoning and is not an end-to-end task latency claim. Bytes are serialized responses, not token or cost savings. The extra lookup and process overhead matter; the trial supports comparison on MCP-heavy workloads, not unconditional compression.

To test whether extra skill wording itself changes tool choice, we offered both a full catalogue and compact index for the same twelve-tool task. With explicit route options (seed 11) and with only CLI discovery (seed 12), **both** baseline and candidate chose the compact index, fetched one schema and passed the checker. Each pair had identical serialized response bytes (1,916 and 1,901 respectively). The existing skill already led workers to make this choice when the option was available. The promoted sentence therefore focuses on recognizing and measuring a recurring MCP schema cost, with the [tooling procedure](../docs/local-codex/tooling.md#tool-schema-disclosure) loaded only when relevant.

The final skill wording was checked once more against an unseen MCP selection (seed 15) and an ordinary 12-line counting task. Both MCP routes passed: 7,622 direct versus 3,261 compressed serialized response bytes, with one selected schema lookup. Both ordinary-task arms returned the correct count of two. The direct MCP worker tried one unnecessary schema lookup before its successful call; the fixture trace captures successful protocol actions, while the worker report captures this failed CLI attempt. This final check supports task acceptance and the conditional route's payload reduction; it does not establish lower overall task cost.

Routing, prefix-cache handling and phase-boundary compaction already have operational guidance. A general recovery controller lacks a recurring failure case and a host route to compare here. These attachment proposals remain research candidates rather than defaults.

The benchmark tools now represent missing usage as unavailable and require a successful independent evaluation before displaying `PASS`. A completed worker response alone is not task acceptance. An authenticated Codex JSONL run is still needed before claiming model-token, total-cost or accepted-task wall-time improvement; the current host did not provide an authenticated writable CLI trial in this session.
