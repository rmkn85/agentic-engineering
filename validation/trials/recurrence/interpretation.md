# Recurrence experiment status

Status on 2026-11-09: **native sandbox execution works; the first matched pair
exposed two defects and corrected trials are pending**.
The original CLI 0.156.1 attempt could not initialize its read-only native state.
That historical failure remains in `native-smoke.json`. The follow-up
`native-recovery.json` retains three materially different calibration attempts.

A private writable home is a supported preparation route: [CODEX_HOME](https://learn.chatgpt.com/docs/config-file/environment-variables)
relocates native state, and the [authentication documentation](https://learn.chatgpt.com/docs/auth)
describes private headless credential-cache copying. The earlier stop should have
tested this route. Original host configuration was not changed. The private copy
retained existing permissions, approval policy, rules, instructions and plugins;
only the neutral project layers and exact reviewed lifecycle hooks received trust.
Credential material and personal configuration are excluded from public evidence.

The old CLI then reached the service but could not use the specified model. A
complete official CLI 0.167.0 package, pinned by release digest, returned the
requested reply using `gpt-6.1-sol`/Medium. An intermediate standalone-binary
attempt lacked its code-mode helper; its result is retained separately. Neither
model reply proves that the agent can run commands or deliver a consumer result.

Native `hooks/list` confirmed discovery and exact-hash trust. Start and Stop
adapter records matched the calibration thread identity. The CLI JSON stream
exposed no native hook events, so these observations remain distinct and do not
establish scored adoption. A model-issued shell command failed before execution:
the outer sandbox masks the shared native socket directory read-only with mode
`000`, while the inner sandbox requires `0700`. This matches the open
[nested sandbox issue](https://github.com/openai/codex/issues/53799), checked
2026-11-09. No mask, permissions, approval rule or trust control was bypassed.

Four matched pairs were prepared and frozen at candidate `40daa16`, and remain
**unrun**. The independent preparer repaired one held-out fixture hook-path
translation before scoring and retained the original; its scenario and oracle
remained undisclosed to the coordinator. Prepared attempts and native failures
are retained privately. These preparations were superseded, not scored. The
evaluator and its source remain outside the worker corpus.

The subsequent calibration used the already enforced outer sandbox as the
execution boundary. The [official app-server documentation](https://learn.chatgpt.com/docs/app-server)
defines `externalSandbox` for this arrangement. The native CLI used its explicit
inner `danger-full-access` selection within that existing isolated environment,
as scoped by the [noninteractive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).
The parent and model-issued command observed the same outer namespace; root and
socket restrictions, approval policy and hook trust remained enforced. This
required no privileged access. The earlier conclusion that a normal terminal was
required was incorrect.

The opt-in runner checks the expected containment before launch and freezes its
observations and exact settings. This is an environment check, not a hostile-host
attestation. Missing or changed observations stop execution. Default execution
still uses the native sandbox. No socket mask or filesystem permission was changed.

Candidate `7bc6568` and baseline `4cdeefd` were frozen with all four tasks before
the first pair ran through native `codex exec`, using fresh `gpt-6.1-sol`/Medium
sessions. Both produced working consumer outputs. The baseline passed the frozen
assertions. The candidate failed integrity after following an audit instruction
to overwrite the embedded dependency handoff. Separately, the evaluator replaced
its valid implementation with a narrower canned positive control, breaking valid
iterator coverage. Independent reproduction isolated both causes; see the
[retained first-pair review](first-native-pair/verdict.md) and
[original result summary](first-native-pair/retained-results.json).

The original failed candidate remains failed. It is not evidence of comparative
superiority or of a candidate product regression. The reusable audit ownership
boundary and evaluator positive control were corrected at `8093943`; independently
reviewed, newly frozen runs are in progress. The remaining three original pairs were not launched. Automatic truthful
completion remains unknown and requires separate semantic review.

Deterministic regression tests exercise contract retention, stale evidence,
correction transitions, adapter subprocess behavior, fixture calibration and
trial attribution. Mutation proofs test whether each designated assertion catches
a disabled protection. These are mechanical results, not measurements of agent
adherence, autonomous recovery, normal host adoption or productivity.

The original `run_trial.py` interface and historical results are retained. They
use injected guidance and must not be relabeled native uncoached evidence.
If both eventual arms succeed, the comparative result is inconclusive. Even a
candidate-only success on four examples would not establish broad reliability,
efficiency gains, live-project adoption or immunity to future framing failures.
