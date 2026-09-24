# Coordination replay fixture

This targets a recurring failure mode in long engineering sessions: the
coordinator repeatedly carries a growing working set while integrating
independent components, even when most input is cached. It measures that
pressure alongside completion of the real task slice.

This original, synthetic Python project tests a release task that crosses a
builder, installer, and consumer. A published version can contain new source
bytes while version-only decisions in installation and response caching leave
old bytes live. The worker must repair the behavior and verify the identity of
the selected source, package, installed copy, and served response. Retained run
logs supply diagnostic context without making the full logs part of the prompt.

Prepare two independent copies with the same seed, then give each worker only
its copy of `task.txt` and the ordinary repository instructions. Apply the
candidate guidance to only one copy. The generated repository includes its own
`AGENTS.md` and public tests. Use different seeds for later paired runs.

```sh
python3 experiments/fixtures/coordination-replay/prepare.py prepare --out /tmp/coord-baseline --seed 11
python3 experiments/fixtures/coordination-replay/prepare.py prepare --out /tmp/coord-candidate --seed 11
(cd /tmp/coord-baseline && python3 -m unittest discover -s tests -q)
python3 experiments/fixtures/coordination-replay/prepare.py check --repo /tmp/coord-baseline
```

`check` runs the public tests and a separate end-to-end acceptance suite from
this fixture directory. It checks protected task material, then creates fresh
source and deployment directories to test a same-version source update,
idempotence, and failed-package preservation. The seeded baseline should fail
the independent suite. The checker does not inspect agent actions; retain the
Codex event stream separately to compare coordinator and worker behavior.

From the agentic-engineering repository root, an authenticated Codex CLI run
can use the existing benchmark wrapper. Set `AE_REPO` to that root and run the
same command for each prepared copy:

```sh
AE_REPO="$PWD"
python3 tools/codex-bench.py --repo /tmp/coord-baseline --label baseline-11 \
  --prompt-file /tmp/coord-baseline/task.txt \
  --eval-command "python3 $AE_REPO/experiments/fixtures/coordination-replay/prepare.py check --repo ." \
  --keep-worktree
python3 tools/codex-bench.py --repo /tmp/coord-candidate --label candidate-11 \
  --prompt-file /tmp/coord-candidate/task.txt \
  --eval-command "python3 $AE_REPO/experiments/fixtures/coordination-replay/prepare.py check --repo ." \
  --keep-worktree
python3 tools/bench-compare.py /tmp/coord-baseline/.agent-bench/runs/*/metrics.json \
  /tmp/coord-candidate/.agent-bench/runs/*/metrics.json
```

As written, both arms use the same guidance and measure run variance. For a
candidate comparison, add `--codex-home` or `--profile` to select two otherwise
identical Codex configurations that differ only in candidate skill guidance.
Use new seed numbers and alternate run order for confirmation. Inspect the
retained worktrees and event streams: the checker proves the result but does
not prove delegation, selective log reading, or a useful handoff occurred.
The comparison reports actual CLI tokens and, when the local session trace is
available, peak root input per response. The optional per-million rate flags
on `bench-compare.py` give a price-equivalent estimate from measured tokens.

Fixture calibration with seed 17: the initial public suite passed two tests,
but independent acceptance failed at installed identity. Repairing the
installer alone then failed at served identity. Repairing both installer and
consumer passed public and independent acceptance, including preservation of
the live consumer after a corrupt package. This calibrates the checker; it is
not a model-efficiency result.

This fixture is a proxy for multi-component coordination and selective
diagnostic reading. It does not reproduce a private project, forced context
compaction, or account-level costs. Pair it with the existing Codex CLI usage
capture to measure actual reported tokens and wall time.
