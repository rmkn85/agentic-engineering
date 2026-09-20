# CI capacity and candidate identity

A newcomer path is only as dependable as its slowest required boundary. Source access, runner execution, dependency/provider access, artifact storage, publishing and actual serving are separate capabilities. A self-hosted worker does not establish that a cloud artifact service will accept a new upload.

## Classify the first failed boundary

Keep build/test outcomes attached to the exact candidate even when later transport fails. An artifact-quota failure is not a source-code defect, a missing browser, or evidence that Git write access is unavailable. Conversely, successful tests do not turn failed artifact transport into accepted deployment.

On a storage or quota failure, retain the compact failure class, exact source/run/job and which gates completed. Do not rerun the entire build repeatedly with unchanged quota evidence. Prefer the existing artifact-preserving retry/recovery route once its prerequisite changes. A delayed provider accounting update must not be presented as a known recovery time.

Engineer capacity before making the agent improvise: bound the retained outputs, avoid duplicated workflow chains and redundant source/dependency archives, choose retention by real consumers, preserve durable concise evidence before transient artifacts expire, and reuse accepted immutable artifacts. A cache is not a durable release store. A separate pre-authorized artifact route may be appropriate, but it must preserve identity, privacy and acceptance. Do not bypass gates, publish private source to save storage, silently increase spend, grant a workflow new authority, or delete the only failed-run evidence.

The smallest operational report distinguishes: code/build, unit/consumer checks, rendered checks, artifact transport, promotion and served identity. A blocked later boundary leaves earlier evidence useful without making the full outcome green.

## Do not inherit another repository's identity

A library or nested workspace checkout often inherits `GITHUB_ACTIONS`, `GITHUB_SHA` and the other environment variables of its consumer. That SHA identifies the workflow's primary candidate, not every source tree installed beneath it. Validate a dependency against the explicit source vector owned by the composition test, not the caller's SHA.

`check-adoption.py` compares HEAD with `GITHUB_SHA` only when its root is the declared `GITHUB_WORKSPACE`. Otherwise it reports that primary-candidate identity was not established and leaves dependency identity to the native composition verifier. Its offline copy validation still runs. An isolated checkout whose identity matters may use the source guard's explicit `--revision` route.

The 2026-09-19 suite now passes **34 offline tests**, including regressions for inherited consumer CI environment and an unknown primary checkout. These tests establish the helper behavior, not any particular host/model, product integration or deployment.

## Sources and applicability

Reviewed 2026-09-19. GitHub documents separate artifact/cache allowances and billing scopes in [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions). The maintained [upload-artifact documentation](https://github.com/actions/upload-artifact) describes retention, artifact outputs and storage limitations. These sources document platform behavior, not the capacity available to a particular account.

This method applies to any workflow with expensive execution and retained/promoted output. Projects without public deployment still need source and evidence identity; they do not need an invented publisher. For concrete runner routing, artifact-quota recovery, rerun-safe Pages artifacts, deterministic reconstruction and immutable release handoff, use [CI and delivery resilience](ci-delivery-resilience.md) and its [copyable GitHub Actions patterns](../../templates/github-actions/ci-delivery-resilience.md). See also the [repository-only contributor contract](../adoption/newcomer-contract.md).
