---
name: using-external-practices
description: Use for consequential cross-file relationship discovery with Graphify, or bounded overengineering review with Ponytail, when these upstream capabilities could improve the current authorized task.
---

# Scoped upstream capabilities

Keep the current task, consumer contracts, privacy, correctness, accessibility,
security and risk-appropriate verification unchanged. These tools do not set the
product scope. Do not add global hooks, services, or another instruction stack.

1. **Select, do not mandate.** Prefer exact search for a known symbol. Use Graphify
   when relationship discovery is the expensive part. Use Ponytail for a bounded
   complexity review of understood code; it is not the correctness reviewer.
   A trivial task should not load this workflow. A considered but rejected use can
   be recorded with `skip`; absence of a receipt is unknown use, not zero use.
2. **Use the maintained upstream.** Pins and modes live in
   `configs/external-practices.json`. The setup command retains the whole upstream
   checkout; do not paste a rewritten version of its skill/engine into the corpus.
   Setup is explicit and logged. Never install dependencies during an ordinary
   lookup, use a random PATH executable, or overwrite another installation.
3. **Route through `tools/external_practices.py`.** Set `--repo` to the consuming
   checkout and reuse its task/run ID and a short concrete `--why`. Commands retain
   private native logs and `practice-feedback/v1` receipts. No API keys or model
   calls are needed for setup/code extraction. Setup still needs network access.
4. **Graphify:** `build` the relevant scope, then `query`, `explain` or `path`.
   Unchanged captured inputs and graph bytes are reused; missing/stale/changed
   graphs block query. Rebuild or fall back to exact tools after a failure, never
   relabel a failed query as acceptance. Inspect the returned log and actual source
   before acting; a parsed/inferred graph is not a complete compiler or authority.
   This route is code-only: it makes no claim about document or media coverage.
5. **Ponytail:** `load` emits the pinned, unmodified `ponytail-review` skill. Apply
   it in a bounded review phase or an available isolated reviewer, with the touched
   code, callers, diff and acceptance constraints. Do not activate the persistent
   whole-session persona. Record findings with locations and concrete replacements;
   accept, reject, or defer them against the actual contract. No mandatory second
   model, repeated review loop, line-count target, or reduced testing quota.
6. **Close only consequential uses.** `assess RUN --status ... --effect ...`
   records the concrete decision/effect and native evidence. State unchanged,
   harmful and unknown effects too. Loading is not application; a successful CLI
   is not accepted development. Do not infer tokens, cost, avoided bugs or savings.
   Use an existing matched benchmark when attribution is consequential.
7. **Surface the evidence.** Add the receipt/report path to the existing handoff or
   run record. `report` gives counts/costs by tool, operation and fixture/live kind;
   `report --details` shows where, why, revision, effect and evidence. Reports can
   combine explicitly named private cache roots; never publish private work traces.

Read `docs/adoption/external-practices.md` for commands, supported scope, retention,
upgrade/uninstall and the remaining validation boundaries. The method does not
require either tool to be installed for normal development or `make check`.
