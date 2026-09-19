# Newcomer checkout guard: executed evidence

Date: 2026-09-19. Scope: `tools/agent-checkout.py` and its offline fixtures. Evidence class: measured functional result, not a model-efficiency benchmark.

Executed `python3 -m unittest discover -s tools/tests -v` in a temporary tool-capable environment: **21 tests passed**. The fixtures create real local bare/working Git repositories. A test-only identity adapter maps their local remote path to an anonymous GitHub identity; fetch, merge, status, refs and commits use real Git. No private repository, external network, personal checkout or hosted runner is required by the suite.

Covered cached-ref uncertainty, fresh fetch, stale read-only inspection, idempotent fast-forward, preservation of tracked/untracked work and local commits, divergence, wrong branch, detached exact candidate, candidate mismatch, wrong repository, wrong push destination, unfinished Git operations, failed fetch, subdirectory entry, multiple push destinations, URL normalization, unsupported transport, missing Git and timeout.

The multiple-push-destination case failed against the first implementation, which read only one destination. The implementation now inspects all configured destinations, and the discriminating regression passes.

Not established: actual low-cost-model task completion, native host instruction delivery, full dependency bootstrap, cross-repository integration, product acceptance, CI runner availability, deployment, or token savings. Those are separate layers of the [repository-only contributor contract](../docs/adoption/newcomer-contract.md).

Rerun the suite after modifying the helper or adopting a changed copy. A copy's hash identifies content; it does not substitute for behavioral validation of the surrounding workflow.
