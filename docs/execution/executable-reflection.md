# Executable reflection and recurrence prevention

Use the existing goal record, native checks and findings ledger. A successful
receipt means the declared checks passed for the recorded inputs; it does not
prove the original requirements were complete or the causal explanation true.

## Preserve acceptance and current evidence

The finish gate pins the goal, acceptance IDs/descriptions/check targets,
requirement references and their contents, declared inputs, and review kind.
Progress, blockers and evidence can change without redefining acceptance.
An intentional contract revision needs `supersedes` with the previous `digest`,
a reason and an authority reference. The earlier contract remains in history.
An authority pointer makes a change reviewable; it does not authenticate approval.

Success receipts bind that contract to source bytes and the executing validators.
The source inventory includes tracked and nonignored files, plus files declared
in `inputs` and `requirement_refs`; declare ignored or external dependencies
explicitly. The gate's own generated state is excluded. Manual local evidence is
an input too. Source mutation during verification or before receipt publication
prevents a successful result from being attached to the new bytes.

`finish_check.py --inspect` and the work audit inspect freshness without executing
acceptance. Old receipts remain readable but are unverified until a new check.
Changed source, requirements or validators make earlier success stale. This is
cheap invalidation, not a demand to rerun every check on each audit.

## Correct an observed discrepancy

Stale evidence alone requires explicit full acceptance verification on stable
current inputs. The gate retains old/new identities and generated check results;
healthy tasks need no authored intervention record. Inspect and audit never refresh.
Failed acceptance, revision, repeated/no-progress work, concurrent changes and
methodology/control obligations still require explicit correction. Use the existing
goal's `reflection.interventions` list:

```json
{
  "observation": "The consumer rejects the current exported format",
  "evidence": "evidence/consumer-failure.txt",
  "hypothesis": "The existing serializer omits the required field",
  "expected_effect": "The consumer accepts the repaired export",
  "run": "consumer-check"
}
```

`run` names a maintained Make target already present in acceptance. The gate runs
it, binds the observation to current inputs and records pending, supported,
refuted or inconclusive results. A supported result establishes that this check
passed with stable inputs; it does not establish the hypothesis's causal truth.
Review the explanation against independent evidence. Keep unsuccessful attempts
and revise the approach when the observation contradicts the prediction.

Unresolved correction prevents a completed claim. A real external blocker may
end the session incomplete with the existing reflection and gap record. Bounded
Stop retries prevent infinite loops; exhausting retries never becomes success.

## Review the framing before the implementation

For methodology/control tasks, declare `kind` and `review.kind` as `methodology`
or `control`. The review declaration names `request`, `failure_evidence` and
`framing` files. First give a fresh reviewer only the original request and failure
evidence through `blind_review.py frame-prompt`. Retain independently derived
criteria using `seal-frame`. Then use `implementation-prompt` to compare the
actual contract and change with those criteria. Retain discrepancies and the
artifacts resolving them. `validate-frame` checks binding and completeness, not
the truth of judgment or independence of the reviewer.

The finish gate checks the declared review. Integration separately uses
`make review-check BASE=<review base>`: changed methodology needs a current
`methodology-review/v1` manifest under `validation/reviews`, binding reviewed
files, request, failure evidence, sealed framing and the independent report.
The manifest's `input_hashes` binds `request`, `failure_evidence` and `framing`
to the exact inputs the accepted report examined; resealing a different frame
cannot reuse that acceptance.
Unrelated product edits need no new review receipt. Changes to reviewed bytes
invalidate coverage. `make check` rejects unresolved findings at integration.

Use `check_findings.py --reopen ID --evidence FILE --reason TEXT` when a previous
finding recurs or its assumptions change. The earlier disposition and the new
evidence hash remain in the same finding's history. A justified declined finding
is an explicit tradeoff, not proof the risk disappeared.

## Native execution and proof boundaries

Repository-local Codex and Claude hooks call the same `agent_hooks.py` adapter.
Startup/resume provides the current audit focus and records relevant correction
triggers. Stop delegates to the finish gate. Adapter errors end unchecked with a
visible explanation. They never manufacture a passing goal or silently bypass
the gate. Review and trust host hooks through the host's native mechanism; no
script here grants trust, changes global permissions or bypasses a sandbox.
Codex commands resolve from the Git root, including sessions started in a
subdirectory. Host formats and trust behavior were checked against the
[official hook documentation](https://learn.chatgpt.com/docs/hooks) on
2026-11-09. Native discovery and trust still require an actual host trial.

Configured hooks, adapter-written logs and native host invocation are separate
observations. Retain actual host events when claiming automatic invocation.
Codex trials use native instruction discovery and preserve user configuration
and rules; pasted instructions are labeled coached legacy trials.

Run recurrence experiments using the native trial commands. Freeze source,
prompt, fixture, evaluator and host identities before scoring. Keep evaluators
outside worker repositories. Compare accepted consumer behavior, erroneous
completion, corrective actions, assistance and available cost observations.
Retain negative and interrupted attempts; a healthy contrast tests unnecessary
process work. Held-out cases cease being held out after they inform a repair.
Instruction exports exclude `validation` and `tools/tests`, including derived
solutions in tests and review reports; export receipts retain the removed hashes.
Global Codex instruction-file identities are bound alongside configuration and
rules, so a changed surrounding instruction stack invalidates a frozen run.

The trial runner defaults to `--boundary native`, preserving its existing inner
sandbox startup probe and launch. `prepare`, `preflight` and `smoke` accept the
explicit `--boundary outer-codex-sandbox` option. Maintained preflight/smoke
activities accept the same strict enum as `BOUNDARY`; `run` has no override and
reads the sealed specification. A failed boundary at preparation retains its observation and stops before fixture
construction; prepare a fresh trial after restoring containment.

The outer option is for an already isolated Codex Linux executor. It checks its
own read-only root, owned mode-000 read-only reserved socket mask for its numeric effective UID, NoNewPrivs,
seccomp filtering and inherited permission-profile identity. It compares the
stable signature at run time and retains namespace identity only as an
observation, since normal executions can have different namespace identifiers.
These observations are a scoped guard, not a complete policy attestation.
Missing or changed guards retain a hash-bound failed report and refuse launch.
After verification, the CLI uses `--sandbox danger-full-access` to omit redundant
inner sandbox creation while preserving actual outer restrictions, configuration,
rules, approvals and hook trust. The nested read-only probe is reported as
`not_applicable`, never passed. Smoke proves at most a model response; model tool
use, writes, hooks and accepted consumer delivery remain separate evidence.

Documented behavior, reviewed 2026-11-09: the official
[non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
permits this CLI sandbox selection in an already isolated environment. A private
pinned CLI 0.167.0 execution demonstrated model shell use within the same outer
mount namespace while read-only repository and socket masking remained enforced.
This observation corrects the execution-layout diagnosis in ER-13; it does not
prove the recurrence consumers or generalize the guard to other host layouts.

These mechanisms operate within a cooperative, reviewed workflow. They cannot
defend against an actor replacing policy, checks and receipts together, judge
human acceptance, or guarantee discovery of every future failure. Retire or
revise controls when observed delivery cost and false alarms outweigh benefit.

Research rationale remains in the [outcome-control source map](../../references/outcome-control-source-map.md).
The links and evidence types there support design hypotheses, not effectiveness
claims for this implementation. The [current experiment status](../../validation/trials/recurrence/interpretation.md)
separates mechanical protection from unproved native behavior.
