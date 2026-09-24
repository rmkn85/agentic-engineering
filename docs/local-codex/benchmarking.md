# Measurement and benchmarking as decision aids

Benchmarking is not the goal of this methodology. The goal is to perform the required work efficiently and correctly.

Use measurement to answer a real question. Once the question is resolved, encode the simplest useful operational rule and return to doing the work.

## Defaults are the baseline, not the opponent

Current Codex/model/tool defaults are presumed reasonable for general workloads. Do not design experiments with the goal of "beating the defaults."

A deviation should begin with a concrete statement such as:

- this repository repeatedly emits 100k-line test logs into model context;
- this build recompiles unchanged artifacts for every agent turn;
- this task has eight genuinely independent packages on the critical path;
- this `AGENTS.md` instruction appears to prevent a repeated failure mode;
- a large global skill catalog materially increases first-turn context.

Then decide whether the expected gain is obvious enough to adopt directly or uncertain enough to measure.

## When *not* to benchmark

Do not create artificial experiments for direct mechanical wins whose correctness conditions are already understood, for example:

- a valid deterministic cache hit versus recomputing the identical artifact;
- reading a compact failure summary first while retaining the full log on disk;
- reusing already-installed locked dependencies instead of downloading them again;
- using an exact index/search tool for an exact lookup instead of asking an LLM to rediscover it.

Monitor these practices for correctness (especially invalidation and truncation), but do not turn the obvious case into permanent benchmark overhead.

## When benchmarking is valuable

Benchmark or measure when:

1. two alternatives are both plausible;
2. an override changes model/context/orchestration behavior;
3. the change may improve one resource while worsening another;
4. the expected saving is large enough to matter;
5. a model/Codex release may have invalidated an old workaround;
6. a local practice is being promoted into shared guidance.

Typical examples: subagent fan-out, custom instruction stacks, custom tool-output limits, local vs cloud execution, custom compaction strategy, model/reasoning selection, or targeted-vs-broad validation heuristics.

## Claim only what the comparison isolates

### Model experiment

Hold execution mode, task, repo, acceptance criteria, tools, and configuration constant. Change only model/reasoning effort.

### Execution experiment

Hold model/reasoning effort, task, repo, acceptance criteria, and useful input/output constant as far as the platform permits. Change local/cloud, instruction stack, tools, caching policy, or delegation.

Do not attribute a combined change to one cause.

## Lightweight observation before full benchmark

Prefer the cheapest evidence that can answer the question:

1. inspect one real run;
2. compare before/after metrics from normal work;
3. if variance or confounding prevents a conclusion, run a controlled A/B;
4. repeat only enough to make the decision robust.

The benchmark harness exists for step 3, not as the mandatory entry point.

## Controlled run protocol

When a controlled experiment is actually warranted:

1. Pin a Git commit.
2. Create a disposable detached worktree.
3. Record the tool/Codex versions and only the non-identifying execution capabilities needed to interpret the comparison.
4. Select a named `CODEX_HOME` / config variant.
5. Use the same task prompt for variants that are not prompt experiments.
6. Run with `codex exec --json` and preserve the JSONL event stream.
7. Run an independent deterministic acceptance command after Codex exits.
8. Record Git diff statistics.
9. Save metrics and logs.
10. Repeat enough times to observe material variance; prefer medians over cherry-picked best runs.

`tools/codex-bench.py` automates most of this when needed.
When the local Codex session trace is available, it also records the root
agent's peak and median input tokens per model response. Those figures expose
a growing coordinator context that one aggregate turn total can hide. Session
trace availability and format vary by host; an unavailable figure is not zero.

`tools/bench-compare.py` accepts `--input-per-million`,
`--cached-input-per-million`, and `--output-per-million` together when a
price-equivalent estimate is useful. Supply the applicable rates for the model
and date being compared. It charges cached input once at its own rate and
counts reasoning output within output tokens, rather than adding it twice.
The estimate is not a measured Codex subscription charge. Missing usage stays
unavailable. If child-agent usage is not present in the captured event stream,
the reported tokens and estimate cover only the visible run; record worker
usage separately before claiming a total.

## Useful metrics

Choose only metrics relevant to the decision.

### Outcome / quality gate

- deterministic acceptance exit code
- tests passed/failed
- required behavior present
- human defects found after run
- unintended diff count where measurable

An optimization that fails the required outcome is not cheaper; it is incomplete.

### Model usage

- input tokens
- cached input tokens / cache ratio
- output tokens
- reasoning output tokens
- model turns

### Orchestration

- agents/subagents spawned
- max concurrency
- total agent turns
- duplicated context / token amplification where observable

### Tool activity

- command executions
- failed/repeated commands
- raw log bytes versus model-visible output
- repeated source reads
- repeated validation work

### Time / deterministic compute

- wall-clock duration
- environment/bootstrap duration
- build/test time
- cache-hit/miss counts when useful

## Derived ratios for specific investigations

```text
cache_ratio = cached_input / input
fresh_input = max(input - cached_input, 0)
speedup = baseline_wall / variant_wall
token_ratio = variant_total_tokens / baseline_total_tokens
fanout_amplification = variant_total_tokens / normal_execution_total_tokens
parallel_value = speedup / fanout_amplification
```

Do not compute every ratio for every run. Use the one that answers the current question.

## Prompt, skill, and AGENTS.md changes

Instructions are not free: they consume context and can alter behavior in unexpected ways. Therefore:

- keep the platform behavior when there is no demonstrated problem;
- add the smallest instruction that addresses an observed failure mode;
- remove it when upstream behavior makes it redundant;
- use ablation only when it is unclear whether the instruction helps.

A 400-token rule that reliably prevents a 20k-token recovery loop is useful. A 400-token rule that merely restates what Codex already does is configuration debt.

## Publication format

For results worth publishing, include enough context to make the conclusion falsifiable: date, Codex/model version, mode, workload class, changed setting/practice, acceptance result, relevant metrics, and known limitations. Raw artifacts are useful when practical but are not the product.
