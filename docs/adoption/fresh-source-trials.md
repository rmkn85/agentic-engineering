# Exercise the native check from cold and stale source

Review date: 2026-09-20. This is one mechanical layer of the [newcomer contract](newcomer-contract.md), not a model-evaluation service, second task ledger or deployment controller.

## Run

From a clean committed checkout with its parent available:

```sh
python3 tools/check-fresh.py --timeout 120 -- make check
```

Use the actual repository-owned **source-only** check instead of `make check` when its name differs. This repository exposes `make contributor-trial`. Copy the reviewed helper locally with upstream commit and hash provenance. Do not fetch policy at startup. Python 3.9+ and Git are base prerequisites; validate other operating systems separately.

The helper invokes that exact command in two disposable clones: the candidate directly, and its parent followed by a fast-forward to the candidate. The latter retains untracked and ignored sentinel files. Each native invocation gets a new home/config/cache location without inherited credentials or import paths. The original checkout is never switched, cleaned, reset, committed or pushed. Uncommitted source and missing parent history fail rather than receiving a pass for another state.

The result records candidate/tree, stale base, command, per-scenario status and native duration, and total wall duration. Complete command logs and receipt JSON stay in a newly allocated temporary directory. Success is compact; failure includes at most 3,000 bytes from the decisive log. Retain useful evidence in the existing owner record; local temporary output and CI logs have their normal retention, not a new durable evidence service. No artifact upload is needed to see the verdict.

## Scope and limits

This is a local Git transport and clean-source/config/cache test, **not** cold network authentication, package installation, instruction delivery, model behavior or application deployment. The stale test uses Git fast-forward directly; it does not certify an IDE's synchronization mechanism or the separate checkout guard. PATH/base tooling and host filesystem/network capabilities remain available. New HOME is not a security sandbox. Execute only trusted checks without product/operator side effects; permissions and real-resource gates remain unchanged.

Do not use the helper to install a full portfolio or call a production lifecycle command. Declare a different, authorized trial for dependencies, service composition, actual minor feature behavior and deployed identity. Two passing source checks do not close those layers. This gate costs two native checks; keep cheap targeted checks during edits and use this at the contributor-infrastructure integration boundary. Do not wrap the trial in itself.

## Discriminating local evidence

Fifteen real local-Git regression tests passed on 2026-09-20 before publication. One case first demonstrates a native command passing with an existing home-only configuration, then demonstrates the cold trial rejecting that hidden dependency. Other cases cover cold/stale candidate identity, preserved local files, uncommitted work, missing history, failed commands, timeout, source/candidate mutation, stale-file deletion, inherited CI identity, credential/import isolation, noisy output and the actual Make invocation. These are fixture results; the repository's complete automatic trial is a separate CI result.

## Platform references

[Git clone](https://git-scm.com/docs/git-clone) documents local cloning and avoiding hardlinked objects. [Git merge](https://git-scm.com/docs/git-merge) documents fast-forward-only and ignored-file preservation. [GitHub workflow variables](https://docs.github.com/en/actions/reference/workflows-and-actions/variables) distinguishes the workflow source SHA and workspace. These describe mechanics, not evidence that a particular project or agent has passed its journey.
