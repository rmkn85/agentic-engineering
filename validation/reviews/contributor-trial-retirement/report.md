# Independent contributor trial lifecycle review

Verdict: accepted for the reviewed source change against `origin/main`. Independent criteria were sealed before reading the candidate diff. Role: bounded Engineer review supporting the Operator's disposal outcome. Reviewed byte identities are in the adjacent implementation manifest. This review made no implementation changes or remote writes.

The initial review found that KeyboardInterrupt reached directory deletion without stopping the separate-session child. The initial mocked observation is retained in `initial-cancellation-result.json`. The correction now kills and reaps the child before retirement, returns a cancelled receipt, and maps CLI SIGTERM to that handled path. The current bounded reproduction in `cancellation-check.py` observes child-group stop, a second wait, returned cancellation and execution removal. It uses a fake child and does not prove live signal behavior.

Independent verification: `python3 -m unittest tools.tests.test_check_fresh` passed all 23 tests. The real POSIX SIGTERM regression verifies signal-derived exit status, retained matching receipt JSON and log, removed execution storage, and absence of the actual command process. Existing real-Git tests preserve cold/stale source identity, sentinel preservation and source integrity checks. Success, command failure and timeout assertions now check retirement; failure diagnostics remain outside the retired directory. Cleanup errors remain failures and preserve the original command reason. The existing-directory test confirms that an unowned execution path is preserved.

Deletion is confined to the newly created execution child of the run's output directory, and is conditional on successful creation. Both clones and isolated homes reside there; logs and the CLI receipt remain in the parent. The source checkout and unrelated siblings are outside that scope. The documented abrupt-interruption runner-recovery boundary remains appropriate: SIGKILL, host loss and repeated interruption are not proved cleanup paths. This is local source-level lifecycle acceptance, not live CI, deployment, model behavior or storage-usage measurement.

C1 met: ordinary completion retires both scenario clones and isolated homes while evidence remains.
C2 met: command failure and handled timeout retire owned scratch and retain diagnostics; cleanup errors are explicit.
C3 met: owned path creation and narrow retirement boundaries preserve pre-existing storage and the original source.
C4 met within the supported boundary: handled interruption stops/reaps the child before retirement and retains a failed cancelled receipt; abrupt termination remains a recovery case.
C5 met: 23 meaningful regressions pass, including a real signalled invocation; `make review-check` passes with the exact-byte accepted manifest.

FINDINGS_START
FINDINGS_END
