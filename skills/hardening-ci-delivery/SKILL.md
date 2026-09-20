---
name: hardening-ci-delivery
description: Use when CI, self-hosted runners, artifact storage, packaging, publication, deployment, or workflow reruns are blocking an otherwise normal engineering change.
---

# Harden CI and delivery without weakening acceptance

1. **Identify the exact current candidate.** Read remote main and the current workflow/check suite. Do not diagnose from an older red run unless its SHA is intentionally under investigation.

2. **Classify the first failed boundary:** trigger, runner, setup, product test/build, post-job cleanup, evidence transport, package handoff, promotion, or live serving. Keep earlier valid evidence, but do not promote a later stage to green.

3. **Preserve trust boundaries and pool capacity.** One runner process is one job slot. On a multi-core host, use multiple isolated runner instances plus capability labels (`general`, `heavy`, `io-heavy`) to bound expensive concurrency without a custom scheduler. Keep trusted-main self-hosted routing separate from untrusted PR routing.

4. **Preserve trust boundaries.** Keep untrusted pull requests on disposable/hosted infrastructure unless explicitly hardened. Trusted main may use a maintained ordinary-user self-hosted runner. Keep genuine cross-platform matrices on their required operating systems. Route by actual capability labels; remove stale machine-specific labels when an equivalent authorized runner can execute the job.

4. **Separate tests from evidence transport.** If only optional logs/screenshots fail to upload, retain an allowlisted runner-local copy and make the redundant upload non-blocking. Evidence steps running after failure must tolerate missing outputs and must not mask the original blocker. If downstream delivery requires the package, use an immutable release asset or deterministic reconstruction verified by a digest; never silently substitute different bytes.

5. **Remove false-red infrastructure.** Inspect post-job action steps. Disable unused cache/save behavior or configure a real cache path rather than allowing cleanup failure to invalidate successful product checks.

6. **Keep CI policy executable.** If repository tests assert workflow structure, update those tests narrowly when the design changes; allow new exceptions only at the intended step type and keep negative cases.

7. **Make reruns idempotent.** Include attempt identity where provider artifact names must be unique. Keep source/candidate identity separate from retry identity.

8. **Verify the trigger.** A successful Git/API write is not proof the workflow ran. Check for a run/check suite on the exact current SHA and use a supported explicit trigger when required.

9. **Integrate on latest main.** Re-read current main before each write, apply the smallest non-force change, read back the resulting head, and validate that exact source. Do not leave the fix on a hidden branch or stale checkout.

10. **Report the layers separately.** State what passed: source, tests, browser/integration, package, publisher, deployment, live identity. Include the remaining first blocker and exact retry condition.

For concrete GitHub Actions patterns, read `templates/github-actions/ci-delivery-resilience.md`. For deeper rationale, read `docs/execution/ci-delivery-resilience.md`.
