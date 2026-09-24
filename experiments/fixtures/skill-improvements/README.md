# Conditional skill trial fixtures

These seeded fixtures let paired workers perform the same task from the same seed. Only the MCP route requires an optional external package in a disposable environment. Keep each worker's run directory separate. Use one seed for a matched pair, then use unseen seeds for confirmation. The checkers recompute expected results instead of trusting a worker's answer.

## Large diagnostic log

From the repository root, for each worker:

```sh
QUIET_RUN_LOG_DIR=/tmp/trial-log-baseline/logs tools/quiet-run -- python3 experiments/fixtures/skill-improvements/log_case.py emit --seed 11
```

Task: identify every job whose `phase=complete` status is `failed`, match it to that job's earlier `state=blocked` cause, and write `/tmp/trial-log-baseline/answer.json` with `sha256` of the retained full log and a `failures` array. Each failure contains `job`, `code`, `cause_line`, `cause_text` (the exact event text after the four-digit line prefix), and `failure_line`. Sort by `failure_line`. A recovered job is not a failure. The log has 4,500 lines and five failures among fourteen interleaved jobs.

```sh
python3 experiments/fixtures/skill-improvements/log_case.py check --seed 11 --run-dir /tmp/trial-log-baseline
```

The checker verifies the seed's exact raw log, quiet-run hash receipt, and all answer fields. Use another run directory for the candidate and the same seed. Seeds 12, 13, and 14 provide unseen variants. Record the worker action trace separately to see whether bounded recall was actually used.

## Similar tool descriptions

For a real MCP protocol comparison, use the existing eight-tool test server and a disposable environment with `mcp-compressor==0.32.1` and `mcp<2`. The same seeded scenario is routed either directly or through medium compression:

```sh
PATH=/tmp/ae-mcp-trial/bin:$PATH /tmp/ae-mcp-trial/bin/python experiments/fixtures/skill-improvements/mcp_route.py scenario --seed 11 --variant direct --run-dir /tmp/trial-mcp-direct
PATH=/tmp/ae-mcp-trial/bin:$PATH /tmp/ae-mcp-trial/bin/python experiments/fixtures/skill-improvements/mcp_route.py list --seed 11 --variant direct --run-dir /tmp/trial-mcp-direct
PATH=/tmp/ae-mcp-trial/bin:$PATH /tmp/ae-mcp-trial/bin/python experiments/fixtures/skill-improvements/mcp_route.py call --seed 11 --variant direct --run-dir /tmp/trial-mcp-direct --name inspect_docs
PATH=/tmp/ae-mcp-trial/bin:$PATH /tmp/ae-mcp-trial/bin/python experiments/fixtures/skill-improvements/mcp_route.py check --seed 11 --variant direct --run-dir /tmp/trial-mcp-direct
```

For `--variant compressed`, list first, retrieve `schema --name inspect_docs`, then call the same backend tool. Save the exact JSON result from `call` as `answer.json` before checking. The checker verifies the correct result and invocation, then separately reports whether catalogue listing and schema retrieval occurred. Seeds 12, 13, and 14 select other domains. The trace records serialized MCP response bytes and actions; MCP subprocess stderr is retained as `mcp-stderr.log`. The fixture does not measure model tokens, cost, or time spent launching the MCP process. Commands above show `/tmp/ae-mcp-trial` as an example disposable environment; substitute its actual path.

For a no-dependency behavior screening case, the stdlib catalogue below is also available.

The stdlib CLI simulates twelve similarly described tools. Its `list --detail full` response includes every full schema. `list --detail index` gives short names and summaries; `schema --name ...` reveals one full schema. Both paths call the same deterministic tool. Every list, schema, or call action writes a machine-readable entry to `actions.jsonl` in that run directory.

```sh
python3 experiments/fixtures/skill-improvements/tool_case.py scenario --seed 11 --run-dir /tmp/trial-tool-baseline
python3 experiments/fixtures/skill-improvements/tool_case.py list --seed 11 --run-dir /tmp/trial-tool-baseline --detail full
python3 experiments/fixtures/skill-improvements/tool_case.py list --seed 11 --run-dir /tmp/trial-tool-baseline --detail index
python3 experiments/fixtures/skill-improvements/tool_case.py schema --seed 11 --run-dir /tmp/trial-tool-baseline --name inspect_docs_archive
python3 experiments/fixtures/skill-improvements/tool_case.py call --seed 11 --run-dir /tmp/trial-tool-baseline --name inspect_docs_archive --record-id R-42 --mode full
```

Task: use the scenario and tool catalogue to select and invoke the appropriate tool, then save the exact call result as `answer.json`. The displayed name above is only valid for seed 11; derive the choice for each other seed. Check with:

```sh
python3 experiments/fixtures/skill-improvements/tool_case.py check --seed 11 --run-dir /tmp/trial-tool-baseline
```

The checker requires an actual correct call, reports catalogue payload bytes, schema lookups, wrong calls, and whether an index was used. Those bytes are serialized CLI responses, not measured model tokens or cost. Seeds 12, 13, and 14 vary the intended tool and order.

## Small code edit and ordinary control

Set up each worker separately, then give it only that run directory's `task.txt` and normal repository instructions:

```sh
python3 experiments/fixtures/skill-improvements/edit_case.py setup --seed 11 --run-dir /tmp/trial-edit-baseline
python3 experiments/fixtures/skill-improvements/edit_case.py check --seed 11 --run-dir /tmp/trial-edit-baseline
python3 experiments/fixtures/skill-improvements/small_case.py setup --seed 11 --run-dir /tmp/trial-small-baseline
python3 experiments/fixtures/skill-improvements/small_case.py check --seed 11 --run-dir /tmp/trial-small-baseline
```

The edit task's documented validation is `python3 -m unittest -q` from its run directory. The independent checker exercises eight input classes. The ordinary task counts exact states in a 12-line file; its checker verifies the unchanged input and answer. Use fresh seeds and separate run directories for confirmation.
