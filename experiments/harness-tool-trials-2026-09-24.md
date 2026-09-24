# Harness tool trials (2026-09-24)

These trials evaluated candidates in two external research notes against this repository's existing tools. They are functional and payload-size checks, not evidence of lower cost per accepted engineering task.

## Observation recall: integrated

The existing `quiet-run` retained full command output and returned a compact bundle path. A 300-line synthetic failure produced 5,780 raw log bytes and a one-line receipt, but the receipt did not bind the bytes or offer exact bounded recall. We added SHA-256 to each bundle evidence entry and [`observation-recall.py`](../tools/observation-recall.py) for verified line, byte, and literal-search retrieval. A matched 300-line run retained the same 5,780 bytes; requesting two middle lines returned those exact lines after hash verification. The contributor regression suite checks exact retrieval, hash mismatch, path escape, and output limits.

This adapts the observation-handle mechanism described by [SoL-Pi](https://github.com/NVlabs/SoL-Pi) to the existing local bundle. It does not install Pi or claim SoL-Pi's reported model-token savings. Actual model-visible reads and accepted diagnosis should be compared on representative noisy failures before claiming an efficiency gain. The local bundle remains transient; no durable storage or deduplication is claimed.

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
