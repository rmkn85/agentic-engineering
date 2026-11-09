# Independent readiness correction review

Role: bounded independent correctness, framing and public-corpus privacy reviewer. Read-only source review; no delegation or held-out fixture access.

## Acceptance derived before diff inspection

The original request requires executable reflection without weakening the original delivery contract. Native trials must preserve host controls and use the requested fresh native sessions. Writable scratch recovery should be attempted, but a model-only reply is not command, write, hook-adoption or consumer readiness. Every failed, interrupted, assisted or inconclusive attempt must remain retrievable. Four matched pairs and the original delivery/merge gates remain required; source tests are separate evidence. The current nested sandbox failure is a blocker, not an authorized bypass or completed trial.

## Verdict

Changes are directionally correct, but request changes for one demonstrated evidence-preservation defect. This verdict covers the readiness correction and pending sanitized evidence only, not overall reflection delivery, native adherence, comparative benefit or merge readiness.

### P2: a later preflight destroys the preceding failed attempt diagnostics

`tools/native_trial.py:210-223`: `run()` writes the complete check to a single `preflight.json`. An explicit failed sandbox probe appends a status row and returns without `launch.json`. A subsequent invocation therefore passes the reuse guard, replaces that shared file and loses the earlier probe stderr/stdout/argv. The append-only rows retain the attempt statuses but do not contain or reference their full preflight. This violates the required preservation of failed attempts and weakens diagnosis and attribution.

Demonstrated with two consecutive mocked failed preflights against an ordinary prepared fixture: both return `sandbox_preflight_failed`; the first unique stderr marker is absent from every persisted audit file after the second invocation, while the second marker remains. See `retry-diagnostic-loss.json`. Preserve each full check under an immutable attempt-specific filename and bind it in the corresponding row; a latest-view file may remain separately. Add a regression using successive distinct failures that verifies both complete records remain recoverable.

## Positive observations and checks

- The read-only startup probe uses explicit argv, managed requirements and two subprocess timeouts. Unsupported/unobserved states remain unknown rather than successful. The run gate rejects an explicit failed probe.
- Smoke separates model request feasibility from command/write readiness and preserves the independent probe result. Neither the source nor pending public interpretation claims consumer results or scored native trials.
- Optional pinned CLI paths remain literal absolute argv data. Duplicate, relative and newline-bearing values are rejected. No shell evaluation is introduced.
- Public changed files contain no observed private paths, personal account/host identifiers, copied credentials or configuration. Neutral capability descriptions, hashes, public issue URLs and model/version identifiers are appropriately scoped. Historical failed evidence is retained and distinct from successful calibration.
- Ran `python3 -m unittest tools.tests.test_native_trial tools.tests.test_reflection_activity`: 24 tests passed. See `tests.txt`. Performed the additional diagnostic-loss reproduction described above.

## Limits

Raw private calibration transcripts and remote source URLs were not independently verified in this bounded review. The report assesses sanitized claim boundaries and consistency with supplied failure evidence. No native model session, command readiness, four-pair scoring, merge or merged-CI verification was performed. No sandbox settings or source files were changed. Reviewed source identities are in `reviewed-sha256.json`.
