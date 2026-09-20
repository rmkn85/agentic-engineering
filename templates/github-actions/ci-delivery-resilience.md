# GitHub Actions CI/delivery resilience patterns

Copy only the pattern your repository actually needs. Pin action versions according to the repository's existing dependency policy. These snippets do not grant new permissions or replace project-specific acceptance.

## Trusted main on self-hosted; pull requests hosted

```yaml
jobs:
  check:
    runs-on: ${{ github.event_name == 'pull_request' && 'ubuntu-latest' || 'self-hosted' }}
    steps:
      - uses: actions/checkout@<pinned-sha>
        with:
          persist-credentials: false
      - name: Refuse privileged trusted-runner execution
        if: runner.environment == 'self-hosted'
        run: |
          test "$(id -u)" -ne 0
          : "${RUNNER_TOOL_CACHE:?runner-local cache/evidence root required}"
      - run: make check
```

Use repository-specific runner labels when available. Do not send fork/untrusted PRs to a personal/self-hosted runner by default.

## Isolated Python on self-hosted runner

Prefer the host's declared base Python plus a repository-local environment instead of an action that assumes a GitHub-hosted toolcache:

```yaml
- name: Prepare isolated Python
  run: |
    python3 -c 'import sys; assert sys.version_info >= (3, 10), sys.version'
    python3 -m venv .venv-ci
    .venv-ci/bin/python -m pip install -r requirements-test.txt
```

Use a version-provisioning action only when the exact version is part of acceptance and the self-hosted runner supports that provisioning path.

## Optional evidence with local retention

```yaml
- name: Retain evidence locally
  if: always() && runner.environment == 'self-hosted'
  shell: bash
  run: |
    set -euo pipefail
    : "${RUNNER_TOOL_CACHE:?required}"
    umask 077
    destination="$RUNNER_TOOL_CACHE/project-evidence/$GITHUB_REPOSITORY/$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT"
    mkdir -p "$destination"
    cp -R verification/. "$destination/"
    printf 'source=%s\nrun=%s\nattempt=%s\n'       "$GITHUB_SHA" "$GITHUB_RUN_ID" "$GITHUB_RUN_ATTEMPT" > "$destination/identity.txt"

- name: Also upload evidence when remote capacity exists
  if: always()
  continue-on-error: true
  uses: actions/upload-artifact@<pinned-sha>
  with:
    name: verification-${{ github.sha }}
    path: verification/
```

Do **not** make the remote upload optional if downstream delivery requires that artifact.

## Deterministic reconstruction instead of artifact download

Producer:

```yaml
- name: Verify build and export digest
  id: identity
  run: |
    make build
    digest="$(sha256sum dist/index.html | awk '{print $1}')"
    echo "sha256=$digest" >> "$GITHUB_OUTPUT"
```

Consumer:

```yaml
- name: Reconstruct tested output
  env:
    EXPECTED_SHA256: ${{ needs.verify.outputs.sha256 }}
  run: |
    make build
    test "$(sha256sum dist/index.html | awk '{print $1}')" = "$EXPECTED_SHA256"
```

Only use this for deterministic builds with pinned inputs.

## Immutable release-asset handoff

After all required checks pass on trusted main:

```yaml
permissions:
  contents: write

- name: Publish immutable candidate package
  if: github.ref == 'refs/heads/main'
  env:
    GH_TOKEN: ${{ github.token }}
  shell: bash
  run: |
    set -euo pipefail
    asset="web-${GITHUB_SHA}.zip"
    tag="web-${GITHUB_SHA}"
    (cd dist && zip -9 -r "../$asset" .)
    gh release create "$tag" "$asset"       --target "$GITHUB_SHA"       --prerelease       --title "Web candidate ${GITHUB_SHA::12}"       --notes "Produced by CI run $GITHUB_RUN_ID"
```

The downstream publisher should verify the release/tag resolves to the tested SHA and verify the provider-supplied or independently computed SHA-256 before promotion. If replacing an existing tag is allowed, do so only for the same exact source identity and under the repository's release policy.

## Avoid setup-action cache false reds

```yaml
- uses: astral-sh/setup-uv@<pinned-sha>
  with:
    version: "0.12.10"
    enable-cache: false
```

Use this when the workflow does not actually create a cache worth saving. Otherwise configure an explicit populated cache path.

## Rerun-safe GitHub Pages artifact

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

This prevents a rerun from seeing multiple fixed-name Pages artifacts in the same workflow run.

## Final current-main verification

Before calling the repository repaired:

```sh
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
# Then verify the workflow/check run whose head SHA equals that exact commit.
```

For API/connector-driven work, use the provider's commit/check APIs instead of assuming a write generated a workflow event.
