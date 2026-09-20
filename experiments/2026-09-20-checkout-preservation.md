# Checkout preservation regression

Review and execution date: 2026-09-20. Scope: the checkout helper, not a complete agent or delivery journey.

The exact helper blob at upstream commit `be8c458c4ace6a56934ea1c50378b6574940046d` was reconstructed through authorized source retrieval and matched Git blob `ae359dbf1f70abe43c04881576e3f8960809131e` before running the experiment. The test environment needed Python and Git only; no private account, workstation files or external network was used by the fixtures.

Four real local-Git tests were executed. Two failed before the change: a fast-forward overwrote an ignored local settings file introduced as tracked source upstream, and a branch switched during fetch at the same HEAD was silently advanced. The unchanged-HEAD check alone did not detect that branch switch.

The fix disables ignored-file overwrites and autostashing for the deliberate fast-forward and rechecks branch identity immediately before mutation and at completion. All four tests passed afterward. Contrasting cases prove that an unrelated ignored file does not block a clean fast-forward and that dirty work is preserved even when the host enables autostash. This is not an atomic multi-process lock; simultaneous writers still require owned isolated preparation under local policy.

Reproduce with `python3 -m unittest discover -s tools/tests -p test_checkout_preservation.py -v`. `make check` and the new lightweight CI workflow execute the entire existing tool suite, including these cases. No result for that full CI run is asserted by this record; consult its actual exact-commit check.

The general lesson is to test preserved user state, not merely an exit code. Git ignores describe tracking, not permission to destroy local content. See the official [git merge options](https://git-scm.com/docs/git-merge) for `--no-overwrite-ignore` and `--no-autostash` behavior. Apply this protection to all relevant consumers, regardless of which project first exposed the failure.
