# Optional Local Codex experiment matrix

This is a menu of experiments for unresolved questions, **not a checklist to execute**.

Start with normal Codex behavior on real work. Run a comparison only when a concrete inefficiency or tradeoff needs evidence.

| Question | Baseline | Possible variant | Run only when... |
|---|---|---|---|
| Do custom instructions help? | current defaults | minimal targeted `AGENTS.md` rule | a repeated failure suggests the rule may pay for its context cost |
| Does a skill help? | no custom skill | on-demand skill | a recurring procedure is complex enough to justify reusable guidance |
| Are quiet tools valuable? | normal command output | save-full/log-summary wrapper | real outputs are materially polluting model context |
| Does repo indexing help? | native/default discovery | deterministic index | repeated discovery/search is consuming noticeable turns/context |
| Local or cloud? | current preferred mode | alternate mode | setup cost, parallelism, or machine availability makes the choice material |
| Explicit fan-out? | normal Codex behavior | 2/4/... agents | work is genuinely independent and critical-path speed matters |
| Explicit concurrency cap? | normal Codex behavior | lower cap | observed fan-out is exhausting quota/rate limits or causing coordination waste |
| Context/output limit? | platform default | custom limit | retained context/tool output is demonstrably excessive |

## Fan-out investigation

If explicit delegation is the question, increase concurrency gradually and stop as soon as marginal speedup no longer justifies duplicated model work. There is no value in exploring 16/32/64/150 agents merely to complete a curve.

The purpose of the experiment is to choose a simple operating rule for that workload, then stop experimenting.
