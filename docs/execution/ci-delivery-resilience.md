# CI and delivery resilience for agent contributors

Reviewed 2026-09-20. This is a reusable execution practice for repositories whose tests, packaging, or deployment must keep working across hosted runners, self-hosted runners, reruns, artifact quotas, and interrupted agent sessions. It preserves the repository's existing acceptance criteria and product authority.

The core rule is simple:

> Treat source verification, test execution, evidence transport, release packaging, promotion, and live serving as separate stages with separate identities.

A later infrastructure failure must not erase earlier valid evidence, and an earlier green test must not be reported as successful delivery.

## 1. Classify the first failed boundary

Inspect the exact current candidate and actual workflow steps before changing code.

| Failure stage | Typical symptom | Correct response |
| --- | --- | --- |
| Trigger | Current main has no run/check suite | Verify workflow registration/event path and explicitly trigger through a supported route; do not reuse an old run as proof |
| Runner | Job stays queued or never starts | Check runner labels/capacity/eligibility; do not rewrite product code |
| Setup | Toolchain action fails before tests | Remove hidden host assumptions or use the repository's declared environment |
| Product checks | Test/build/browser step fails | Fix the product or test contract and rerun the affected acceptance |
| Post-job cleanup | All requested checks passed but setup/cache cleanup fails | Fix the action configuration; do not classify the product as defective |
| Evidence transport | Artifact upload/cache storage fails after checks | Preserve evidence through an approved fallback and keep the transport failure explicit |
| Release/package | Accepted bytes cannot reach the publisher | Use a durable immutable package route; do not silently rebuild different bytes |
| Promotion/deploy | Publisher cannot update destination | Diagnose credentials/rules/concurrency without weakening tests |
| Live serving | Destination commit exists but served identity differs | Treat deployment as incomplete until live identity matches |

Read the exact step list and current logs where available. A recurring historical failure is not proof of the current first failure.

## 2. Route trusted and untrusted code differently

A self-hosted runner is an execution capability, not a universal replacement for hosted CI.

A useful default for GitHub Actions is:

- **Pull requests or otherwise untrusted code:** run on hosted/disposable infrastructure unless the repository has an explicit hardened policy for untrusted self-hosted execution.
- **Trusted main-branch verification:** a maintained self-hosted runner may be used to conserve hosted budget and reuse expensive tool/browser caches.
- **Cross-platform release matrices:** keep real Windows/macOS/Linux validation on the matching operating systems. Do not replace a three-OS release contract with one Linux runner merely because it is available.

On self-hosted runners, prefer ordinary-user execution, repository-local virtual environments, runner-scoped caches, and no system package mutation during ordinary feature validation. Missing host prerequisites should produce one explicit blocker rather than privilege escalation.

Example routing:

```yaml
runs-on: ${{ github.event_name == 'pull_request' && 'ubuntu-latest' || 'self-hosted' }}
```

Adapt labels and trust policy to the repository; the expression is a pattern, not a mandate.

## 3. Keep tests independent from evidence transport

Artifact storage and test execution are different services.

For **nonessential evidence** such as logs, screenshots, traces, or source archives:

1. Keep the test/check required.
2. Retain the same evidence in an approved runner-local path when using a trusted self-hosted runner.
3. Make the redundant remote evidence upload non-blocking when storage capacity is known to be an independent constraint.

For **deployment packages**, do not simply ignore a failed artifact upload if downstream jobs require that artifact. Choose one of these stronger patterns instead:

### Immutable release asset

After the exact candidate passes, package the accepted bytes and publish them as an immutable prerelease/release asset targeting that exact source SHA. Downstream publication verifies source identity, asset digest, and release/tag identity before promoting the bytes.

This is a good fit when the package must survive Actions artifact expiration/quota and when the publisher already consumes GitHub release assets.

### Deterministic reconstruction with digest verification

When output is genuinely deterministic and cheap to rebuild, downstream jobs may reconstruct it from the exact tested source and compare a cryptographic digest produced by the original verification step.

The digest, not the fact that a second build succeeded, proves that the downstream bytes match the verified candidate.

Do not use deterministic reconstruction for outputs that include timestamps, nondeterministic generators, external mutable downloads, or otherwise unstable inputs unless those sources are pinned and normalized.

## 4. Preserve evidence on a trusted runner

A runner-local evidence copy is useful when cloud artifact capacity is unavailable, but it is not public deployment.

A generic pattern:

```yaml
- name: Retain verification evidence on the trusted runner
  if: always() && runner.environment == 'self-hosted'
  shell: bash
  run: |
    set -euo pipefail
    : "${RUNNER_TOOL_CACHE:?Runner-local tool cache is required}"
    umask 077
    destination="$RUNNER_TOOL_CACHE/project-evidence/$GITHUB_REPOSITORY/$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT"
    mkdir -p "$destination"
    cp -R verification/. "$destination/"
    printf 'source=%s\nrun=%s\nattempt=%s\n'       "$GITHUB_SHA" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" > "$destination/identity.txt"
```

Keep the copied paths allowlisted. Do not dump secrets, raw private datasets, or arbitrary home directories into evidence.

If remote upload is redundant rather than required for publication:

```yaml
- uses: actions/upload-artifact@<pinned-sha>
  if: always()
  continue-on-error: true
  with:
    name: private-verification
    path: verification/
```

The job can then report a transport warning while retaining the actual test verdict.

## 5. Avoid post-job false reds

Setup actions often have post-job cleanup or cache-save phases. A workflow can finish its requested product checks successfully and still end red because a post-action expected a cache directory that was never created.

Diagnose this from the step list. If the cache is not needed, disable it rather than creating meaningless state merely to satisfy cleanup.

Example:

```yaml
- uses: astral-sh/setup-uv@<pinned-sha>
  with:
    version: "0.12.10"
    enable-cache: false
```

If caching is valuable, configure a real stable path and make sure the workload actually populates it. Do not reinterpret a cache cleanup failure as a product test failure.

## 6. Make reruns idempotent

A rerun uses the same workflow-run identity with a new attempt number. Fixed artifact names can collide with artifacts created by an earlier attempt.

For GitHub Pages using versions that support explicit artifact names, make the upload and deploy steps agree on an attempt-specific name:

```yaml
- name: Upload Pages artifact
  uses: actions/upload-pages-artifact@<pinned-sha>
  with:
    name: github-pages-${{ github.run_attempt }}
    path: _site

- name: Deploy Pages
  id: deployment
  uses: actions/deploy-pages@<pinned-sha>
  with:
    artifact_name: github-pages-${{ github.run_attempt }}
```

Apply the same principle to any rerunnable workflow where a provider requires a unique artifact name. Preserve the candidate identity separately from the attempt identity.

## 7. Verify that automation actually triggered

Do not assume every Git/API mutation path emits the same automation event.

After a CI/deployment change:

1. Read current remote main.
2. Confirm the intended commit is an ancestor/current head.
3. Check for a workflow run or check suite on that exact candidate.
4. If none exists, diagnose workflow registration/event filtering or use an explicit supported dispatch/trigger.
5. Never cite the last green run from an older SHA as proof for current main.

This matters especially for connector/API-driven development: successful Git publication and successful CI triggering are separate claims.

## 8. Verify producer/consumer delivery contracts

A source workflow and a central publisher can each be internally correct while the end-to-end handoff is impossible. Before calling delivery repaired, verify that the producer emits the package kind, name, paths and identity that the consumer registry actually expects.

Examples of contract drift include a publisher expecting an immutable release asset while the producer only uploads a transient Actions artifact, or a consumer selecting files beneath `dist/` while the package flattens that directory. Test the real handoff contract, not just each side independently.

For multi-repository composition, a green portfolio run can also be stale if its pinned source vector no longer equals the repositories' accepted current heads. At final integration:

1. read the current accepted/default-branch head for every owned component;
2. compare it with the composition/source-pin manifest;
3. update pins through the normal reviewed route;
4. rerun the composition test on that exact vector;
5. recheck heads before reporting completion, because parallel contributors may have advanced them again.

Do not silently replace deliberate frozen historical pins; this rule applies when the contract claims to validate **current** integrated source.

## 9. Keep current main authoritative

For concurrent agent work, use this integration discipline:

1. Re-read remote `main` immediately before a write.
2. Apply the smallest change on top of that current head.
3. Use a non-force update.
4. Read back the new head.
5. Run or observe acceptance on that exact head.
6. If another contributor advances main, reconcile against the newer head; do not keep a hidden side-branch fix and call the repository repaired.

An old workflow rerun is useful only when its SHA still equals current accepted source or when intentionally diagnosing history.

## 10. Adoption decision tree

Use the smallest applicable mechanism:

- **Hosted minutes exhausted, trusted main only:** route trusted main to a maintained self-hosted runner; keep untrusted PRs isolated.
- **Artifact upload blocks after tests:** classify whether the artifact is evidence or a required package.
  - evidence → runner-local retention + optional remote upload;
  - required package → immutable release asset or verified deterministic reconstruction.
- **Workflow rerun creates duplicate artifacts:** include attempt identity in the artifact name.
- **Tests passed but job red in cleanup:** fix/disable the unrelated cleanup/cache behavior.
- **No run on current main:** fix triggering before changing product code.
- **Cross-platform release:** retain real OS-specific lanes.
- **Deployment claims success but live bytes differ:** fail the serving-identity check.

## Acceptance

A resilient repository should demonstrate at least:

- trusted current-main checks can execute even when hosted capacity is constrained;
- untrusted PRs do not gain accidental access to a personal/self-hosted runner;
- test failure and evidence-transport failure are distinguishable;
- rerunning the same workflow does not collide with prior-attempt artifacts;
- deployment packages retain exact source/digest identity across handoff;
- current remote main, not a stale branch or old run, is the accepted source;
- live deployment identity is checked when the repository actually ships a public/service artifact.

See also [CI capacity and candidate identity](ci-capacity-and-identity.md), [native command bindings](../adoption/native-command-bindings.md), and the [repository-only contributor contract](../adoption/newcomer-contract.md).
