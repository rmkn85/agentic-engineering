---
name: hardening-ci-delivery
description: Use when CI, self-hosted runners, artifact storage, packaging, publication, deployment, or workflow reruns are blocking an otherwise normal engineering change.
---

# Harden CI and delivery without weakening acceptance

1. **Pinpoint the current candidate.** Check remote `main` and the active workflow run; ignore older red runs unless debugging that specific SHA.
2. **Classify the first failed boundary:** trigger, runner, setup, test/build, cleanup, evidence transport, packaging, promotion, or live serving. Retain prior valid evidence without promoting failed stages.
3. **Share one workflow ref & cut ceremony.** Point consumer repos at one shared workflow ref instead of drifted per-repo SHAs. Path-filter heavy integration jobs to affected code, default unit tests to temp dirs so they run offline, keep status in one tracker, and fold notes into feature PRs instead of separate handoff PRs or brittle merge-commit hash trailers.
4. **Preserve trust & runner capacity.** Keep untrusted PRs off trusted self-hosted runners; use capability labels (`general`, `heavy`, `io-heavy`) on multi-core pools without a custom scheduler, and remove stale host labels.
5. **Decouple tests from optional evidence transport.** Keep allowlisted logs runner-local and optional uploads `continue-on-error: true`, tolerating missing outputs. Downstream packages require immutable release assets or digest-verified deterministic rebuilds.
6. **Eliminate false-red cleanup & keep policy executable.** Ensure post-job cache/cleanup never fails passing builds, and update workflow policy tests narrowly when patterns change.
7. **Keep reruns idempotent & verify triggers.** Key artifact names on attempt ID without mixing source vs retry identity; verify a workflow actually ran on the target SHA.
8. **Integrate on latest `main` & report layers separately.** Re-read `main` before writing, verify the exact head, and report source, tests, integration, packaging, deployment, and live status separately with the first blocker and retry condition.

Patterns: `templates/github-actions/ci-delivery-resilience.md`. Rationale: `docs/execution/ci-delivery-resilience.md`.
