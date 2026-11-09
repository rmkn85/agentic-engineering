# Independent final source review

Reviewed clean candidate `5b534f35ba0e12572ac07f97b3c1dfb38da92a7e` against baseline `4cdeefd11dd415512d691f4bf5a6197132141123`. Exact changed-file SHA256s are retained in `reviewed-identity.json`. The original independent criteria are preserved in `criteria.json`.

**Mechanical source verdict: changes required for one remaining trial-integrity defect.** The five previous defect mechanisms are corrected. This verdict does not cover subsequent commits or final integration checks still running elsewhere.

## Remaining finding

**P2 — Derived evaluator solutions remain installed in the uncoached worker corpus.** `tools/native_trial.py:exclude_trial_assets` removes the evaluator, its identical copies and `validation/trials`, but preserves `tools/tests/test_native_trial.py`. The installed test includes the solved export implementation, the exact workflow repair `out.write('check: consumer-check\n')`, and assertions accepting the repair. The new candidate arm therefore receives solution cues absent from the historical baseline arm. Removing the evaluator bytes alone does not preserve the intended separation.

Reproduction: use `native_trial.prepare` on the reviewed commit, the maintained recurrence builder/evaluator, and `healthy-small-change`; inspect the exported `.agentic-engineering/tools/tests/test_native_trial.py`. `oracle-exclusion.log` records the actual prepared result: evaluator absent, derived test installed, explicit workflow solution visible, solved export visible, expected acceptance visible. The disposable preparation and its receipt are retained under `oracle-probe-audit` and `oracle-probe-worker`.

Exclude scenario-specific tests and other derived oracle material from the instruction export before invoking the builder, retain their excluded identities, and test the export with the full candidate corpus rather than only a miniature source tree. General operating guidance and normal product consumer tests can remain available.

## Confirmed repairs and verification

Six independent confirmations now pass using the current schema, including a fully valid initial accepted-review manifest with `input_hashes`. They confirm:

- Replacing request, failure evidence and sealed criteria invalidates the earlier accepted report.
- Methodology documentation, the native wrapper and recurrence fixtures require review.
- Replacing ignored intervention evidence invalidates prior success.
- A post-run external repair cannot be attributed to the earlier native attempt.
- A second launch against the same fixture is rejected.
- The maintained activity forwards constrained hook-trust evidence as argument data.

The focused current repository suite also passed: **55 tests**, covering missing-goal authority retained across sessions, current/stale retained success, actual adapter subprocesses from nested directories, correction input stability, acceptance publication identity, trust binding, and interrupted attempts. See `focused-suite.log`, `confirm_fixes.py` and `confirm-fixes.log`. These are deterministic source/adapter checks; mocked host completion remains explicitly mechanical evidence. Validator identities and before/after snapshots are included in success receipts; configured hooks and adapter logs are not treated as native invocation proof.

The public changes were read for privacy and evidence claims, with an additional scan for personal paths, usernames, private addresses and credential markers. No new public-corpus privacy defect was identified. The documentation correctly limits semantic and causal claims and preserves the distinction between mechanics and behavior.

## Native and release readiness

**Native acceptance remains unfulfilled; release/merge readiness is not approved.** The native smoke stopped before model execution because host installation/state was read-only. It establishes that execution limitation only. The paired fresh/resumed recurrence behavior, actual host hook delivery/response handling, held-out acceptance and comparative efficiency remain unrun. The held-out condition was not opened in this review. Keep the PR draft and retain these gates after repairing the export defect. Do not relabel deterministic checks or this review as native recurrence proof.
