# Configured self-hosted runner versus ChatGPT native execution

**Measured September 27, 2026.** This follow-up executed the original [ChatGPT parallel Godot fixture](../chatgpt-parallel-native-processes-2026-09/README.md) through an already authorized self-hosted GitHub Actions runner. It did not move to an unrestricted desktop session or change the runner to make the experiment pass.

**Result: three concurrent headless Godot processes passed. The current runner's isolated X11 connection failed, so graphical fan-out was not attempted.** ChatGPT had passed both headless and off-screen rendering with its supplied engine and software-driver route. The runner is immediately useful for native non-rendering tests; it does not yet provide a verified replacement for that ChatGPT image loop under the tested configuration.

## Scope and evidence provenance

The native comparison used public source **`fab177bb1d2de09561f8b6b7b155cbc67e7f9698`**. It reused the exact GDScript and project files from the earlier experiment; [results.json](results.json) retains their Git blob hashes and the runtime observations. The orchestration change was an opt-in **inherited-driver mode**, plus workspace-local temporary storage and honest unknown values for hidden resource counters. There was no private game code, renderer replacement or alternate physics implementation.

The coordinator read completed job results and their native JSON/error excerpts. This report publishes an allowlisted, anonymized transcription, not the full job logs: runner identities, private project references and host paths are deliberately absent. Public source identity and actual values remain. The earlier ChatGPT report is a dated baseline, not a fresh rerun or an official specification of all ChatGPT sessions.

Three pipeline invocations were sufficient: a prerequisite check, the staged native test, and a smaller display-only diagnostic. The latter did not repeat passed physics work. Overall job outcomes were **success, failure, failure** respectively. The two failures remain failures; successful subcases do not make the full graphical claim pass.

## The configured runner, not the whole workstation

The inspected [runner-pool source](https://github.com/rmkn85/github-actions-runners/tree/d5d662d2f5da1ea4bb541f9c8fba6023788a4b55) describes organization-scoped Bubblewrap filesystem views, read-only system/toolchain inputs, no real user home or unrelated projects, and no mounted host Docker socket. It also describes a shared job-admission mechanism. Job execution showed the corresponding workspace and admission hooks. This is configuration evidence, not a penetration test or attestation of the exact service revision.

| Capability | Observed boundary |
| --- | --- |
| Native engine | Existing Godot **4.7.2**, distribution build; `--headless --version` exited 0 without stderr |
| Execution | Linux x86-64, **non-root**, Python **3.14.7**; no installation needed |
| Required tools | Godot, Xvfb, xvfb-run, xauth and taskset were discoverable; actual use is tested separately below |
| CPU availability | Enough existing affinity-available CPUs for three one-CPU child assignments; not a promise of dedicated cores |
| CPU/memory/process quotas | The standard cgroup limit files were not readable/available in this view; **unknown, not unlimited** |
| Mutable state | Each child had its own project, HOME, user-data, configuration, cache, runtime and output directory beneath the job workspace |
| Child boundary | Distinct engine PIDs/user directories; sampled namespace and cgroup membership matched their coordinator |
| Networking | Ordinary pinned GitHub checkout worked. The native probe made no network request; broader network access was not explored |
| Docker | An executable on PATH does not establish daemon access. No daemon/socket call or nested-container attempt was made |
| Graphics | Xvfb presence did not establish a usable X11 client connection. No driver override or installation was attempted |

Self-hosted runners are environments maintained by their operator and are not necessarily pristine for every job [S1]. Job labels route work to an eligible online runner, rather than allocating a new computer [S2]. Our child processes consumed the resources available to one admitted job. Three subprocesses are neither three AI subagents nor three newly provisioned sandboxes. Matching namespaces also means separate directories are organization, not hostile-peer isolation. Cgroup limits, where visible, constrain inherited resource groups [S3].

## Native results

Every headless worker advanced **6,000 actual physics ticks**, approximately 100 simulated seconds. Parameters were unchanged: gravity 4.9/9.8/19.6, horizontal speed 0.6/1.2/1.8 and distinguishable presentation hues. Each healthy worker checked completed ticks, gravity response, lateral response, floor contact, resting height and ownership of its saved user-state marker.

| Case | Result | Group wall time | Sampled sum of Godot RSS |
| --- | --- | ---: | ---: |
| Headless pilot, one process | 6/6 checks passed | 1.216747 s | 122.24 MiB |
| Headless batch, three processes | **18/18 checks passed** | **1.317619 s** | **363.96 MiB** |
| Missing-floor control, one process | Expected native exit 1; exactly contact/rest checks failed | 0.461100 s | 121.86 MiB |
| Off-screen render pilot | Failed before native readiness at X11 connection | No successful workload timing | No completed capture |
| Off-screen batch, three processes | **Not run** after pilot failure | Not measured | Not measured |

The missing-floor case passed the *negative-control expectation*, not the contact claim. Its other four checks passed; an arbitrary crash or absent report would not have qualified.

### Evidence of real parallelism

The three healthy workers had **722.255 ms of common native active time**. The sampler observed all three in progress together and CPU-time increases of approximately 0.74, 0.83 and 0.83 seconds. At tick 30 their y positions were approximately 2.407916, 1.815833 and 0.631666, and their x positions 0.29, 0.58 and 0.87. All recorded one contact and settled near y=0.24. These match the early responses documented in the ChatGPT baseline.

This is stronger than counting three launches or three processes waiting at a barrier. It is still a small bounded concurrency demonstration, not a maximum-throughput test. RSS sums can count shared pages more than once. Hidden cgroup memory remained null rather than being presented as zero usage.

## The graphics failure: what we know and what we do not

The first native rendering attempt reported:

```text
ERROR: X11 Display is not available
WARNING: Display driver x11 failed, falling back to wayland.
```

The fallback also reported an overlong Unix socket path and no Wayland connection. That later message is **not evidence that path length caused the original X11 failure**. We did not relabel the attempted fallback as a successful test or remove the software-renderer assertion.

A discriminating follow-up used the existing Xvfb and libX11 without Godot. It created a short, owned workspace-local runtime path (60 bytes), ran Xvfb with TCP listening disabled, and asked `XOpenDisplay(NULL)` to connect. The call returned false. The filtered server/client logs supplied no additional diagnostic error. No subsequent render pilot or batch ran.

Therefore the current failure is demonstrable at the **display-connection boundary before Godot**, independent of the later long-path fallback. Its precise cause is **unresolved**. The result does not prove a GPU deficiency, broken Mesa, missing Vulkan, inadequate hardware, a general Bubblewrap limitation or an unavoidable GitHub Actions restriction. None of those explanations was tested. No user display, permissive socket setting, driver forcing, device mount, network change or sandbox escape was tried.

This also qualifies the historical container-rendering success: a different, earlier prepared Docker execution route cannot certify today's differently constrained runner. The fact that a computer rendered successfully in another context does not prove a current job can reach the same display/driver facilities.

## Compare with the ChatGPT experiment

| Dimension | Earlier ChatGPT Python sandbox | Current configured self-hosted runner |
| --- | --- | --- |
| Engine preparation | Supplied official engine ZIP had to be verified/extracted | Suitable distribution engine already installed |
| Three-worker headless result | 18/18 passed; 1.006 s | 18/18 passed; 1.318 s |
| Three-worker overlap | 365.648 ms | 722.255 ms |
| Three-worker sampled RSS | 310.23 MiB | 363.96 MiB |
| Off-screen rendering | Three renderers passed 27 checks; 5.638 s | X11 pilot failed; three-way render not attempted |
| Driver policy | Explicit LLVMpipe and one rasterizer thread | Existing configuration preserved; no inherited overrides were present |
| Resource knowledge | Measured shared four-CPU-equivalent quota / 4 GiB memory limit | Adequate affinity for this test; actual quota unavailable |
| Input/source path | Supplied files and connector-derived selected source; direct clone failed in that session | Exact public Git checkout completed through the ordinary pipeline |
| Result access | Native files directly available to local analysis/image inspection | Native summaries accessible in job logs; no image transfer exercised |
| Lifecycle | Session-local runtime must be rediscovered | Job orchestration depends on online runner/pool admission and current provisioned tools |

**Do not report these rows as a speedup or a platform ranking.** The distribution and official Godot executable hashes differ, despite the same engine source revision suffix. Python, libraries, scheduling, driver policy and unmeasured competing work differ. There is only one successful sample per case. A one-process pilot versus a three-process batch is not the same as running all three configurations serially. Fixed-step simulation throughput is not gameplay FPS or hardware-GPU frame time.

For perspective, the native comparison job spanned about **16 seconds** from its reported start to completion, while the three-worker headless group itself took 1.318 seconds. The job also performed checkout, regression tests, a pilot, a negative control, the failed renderer and cleanup; the difference is not a measured pure queue penalty. Neither developer turnaround nor maximum parallel capacity can be inferred from the inner-loop number alone.

## Which surface to choose

| Work | Practical choice under the measured conditions |
| --- | --- |
| Small physics/logic hypothesis, inputs already in the chat | ChatGPT local execution avoids a pipeline round trip; retain a meaningful rejecting control |
| Repeated checks of committed source, ordinary build/integration work | Existing runner is a good fit: engine is available, checkout works, and source/run identity comes naturally |
| Several independent parameter cases | Either supports a small native subprocess pool; select by actual input access, workload and resource budget, not model branding |
| Immediate inspection/tuning of small Compatibility scenes | The verified ChatGPT image route currently has the advantage; this runner's X11 claim remains blocked |
| Larger native suite or production dependencies | Prefer a suitably prepared runner only after its specific dependencies and budget are checked; more workstation hardware is not automatically exposed to a sandboxed job |
| Hardware GPU performance, physical controls or real-device acceptance | Use an explicitly authorized suitable target. Neither this headless runner result nor ChatGPT software rendering establishes those claims |
| Independent design/reasoning review | Requires actual model/reviewer capabilities; creating more Godot processes does not supply them |

Keep **job concurrency and per-job child concurrency** separate. A pool admission limit counts jobs; each job may create multiple engines or test workers. Their combined demand can exceed the intended workload even when the listener count looks safe. Here one bounded job used at most three engine processes, one existing affinity CPU per child, a 25-second group watchdog and owned process-group cleanup. This is a tested small starting point, not a rule to maximize every job or change the owner's pool settings.

For future graphics work, the missing input is a working, policy-compliant display route in the *current* runner context. This investigation provides a minimal reproducer; it does not authorize broadening that context. Continue valid headless tasks meanwhile and keep graphics-specific acceptance open.

## Reproduce and retain only useful results

The committed [compare.py](compare.py) imports the existing [run.py](../chatgpt-parallel-native-processes-2026-09/run.py). Supply an existing authorized workspace and configured engine:

```sh
# Explicit headless scope: this is the route verified on the runner.
python3 -S references/self-hosted-native-comparison-2026-09/compare.py \
  --workspace "$GITHUB_WORKSPACE" --headless-only

# Includes graphics. It must remain failed when the X11 route does not work.
python3 -S references/self-hosted-native-comparison-2026-09/compare.py \
  --workspace "$GITHUB_WORKSPACE"
```

The executable comes from `GODOT_BIN`, `GODOT` or normal PATH; the script does not search the workstation or install packages. The current fixture intentionally expects software rendering. A different default adapter would require a separately defined comparison, not overriding the driver or hiding an assertion. Native errors stop expansion and return sanitized first-error excerpts.

All experiment-created project, user, cache and output data is placed beneath the supplied workspace and removed after producing compact results. Xvfb uses the sandbox's normal temporary socket facilities. Existing toolchain/OS read interfaces and standard GitHub checkout mechanics remain unchanged. No extra host paths were exposed. The native attempt generated **46,842,033 temporary bytes**, then cleaned them; the small display-only diagnostic generated 21 bytes. Their contents were not inventoried to attribute the total to a particular cache. No source tarball, engine, screenshot or raw workstation log was added to this public repository or uploaded as an Actions artifact.

The dedicated investigation workflow was temporary; the reproducible Python source and this result are the durable artifacts. It did not deploy a game, alter runner configuration or install an ongoing monitoring service.

## Validation and remaining limitations

Seventeen focused Python tests passed locally: seven existing coordinator tests, six configured-driver tests and four comparison/diagnostic tests. The ten new tests also passed in both native and display-diagnostic pipeline invocations. The original GDScript/project hashes were checked before execution. We did not run the repository-wide `make check` locally because a full local checkout was unavailable; that is separate from native execution and this selected-source test suite.

There was no successful current-runner screenshot, visual review, normal-speed motion review, Forward+/Vulkan test, browser export, terrain-addon test, saturation benchmark, privilege probe, hostile-isolation test or AI-agent delegation. A failed graphics claim remains open even though headless physics works. The reports are measurements of this configured environment, not an assurance about all self-hosted runners.

## Primary sources and revision boundary

- **S1:** [GitHub: self-hosted runners](https://docs.github.com/en/actions/concepts/runners/self-hosted-runners). Operator-managed environments and non-pristine job lifecycles.
- **S2:** [GitHub: runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners). Label/group matching, online availability and queue behavior.
- **S3:** [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html). Resource-group membership and quota semantics; hidden counters are not unlimited allocations.
- **S4:** [Python subprocess](https://docs.python.org/3/library/subprocess.html). Native launch/session/wait mechanics, not model-agent or environment allocation.
- **S5:** [Configured runner-pool source](https://github.com/rmkn85/github-actions-runners/tree/d5d662d2f5da1ea4bb541f9c8fba6023788a4b55). The inspected setup, not proof that a service has loaded every latest change.
- **S6:** [Original measured ChatGPT case](../chatgpt-parallel-native-processes-2026-09/README.md), source `6b73481b9925f3295fd0edbfcd7f0aabe6619c01`. Prior measurements and comparison limits.

Review date: September 27, 2026. Recheck current source and the actual executor before relying on mutable capabilities.
