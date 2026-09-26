# ChatGPT subagents, sandbox boundaries and parallel native execution

**Reviewed and measured: September 26, 2026.** This is a bounded case study, not a platform specification or a claim that every ChatGPT model/account exposes the same tools. The experiment ran in the current ChatGPT execution environment, not in Codex or on a GitHub runner.

## Answer to the original question

There are two distinct results:

1. **Documented product capability:** OpenAI documents parallel subagent workflows in **ChatGPT Work** for eligible accounts, independently of running the Codex application. The documentation distinguishes explicitly requested delegation from proactive delegation at the supported Ultra level. This does not establish that any particular ordinary Chat session exposes the same orchestration tools. [S1]
2. **Measured capability here:** this session exposed native shell/Python execution but **no general model-subagent spawn/wait/message interface and no independent-sandbox creation interface**. No model subagents or new sandboxes were created. We did execute **three concurrent Godot processes with different parameters**, and separately **three concurrent software-rendered Godot processes**, using disjoint work directories in the existing environment.

The second result is useful, but is not evidence for the first. A subprocess does not have its own model/context merely because it is named a worker. A different process, directory, virtual display, Python tool or terminal session is not automatically a separately provisioned sandbox.

OpenAI's Agents API explicitly documents that coordinator and subagents share the configured environment's filesystem; creating a subagent does not create a new environment. That statement concerns that API, not an independently measured isolation guarantee for ChatGPT Work. We did not invoke the API, configure keys, change plans, or incur external model usage. [S2]

## Why this experiment was worth doing

The immediate engineering need was to execute independent parameterized native tests from ChatGPT without desktop access, remote-job turnaround or recurring cloud artifact uploads. An extra reasoning agent is unnecessary for a known deterministic test command; the coordinator can dispatch bounded subprocesses and inspect their reports. Independent reasoning/review and extra compute capacity are different reasons to introduce another executor.

This is deliberately a small, original, asset-free public fixture. It includes no private game code, project instructions, assets or proprietary scenes. The executable supplied by the user is an upstream binary input, not committed to this repository. All three workers share that executable while receiving separate project copies, configuration files, XDG directories and outputs.

## System and capability observations

See [environment.json](environment.json) for the machine-readable capability snapshot. These values describe the ephemeral execution environment, not the owner's workstation. Collection was allowlisted; no credential/environment dump, host identity, private address, unrelated process inspection or personal configuration was published.

| Observation | Measured value or precise boundary |
| --- | --- |
| OS / ABI | Linux x86-64; Debian 13 (trixie); kernel 6.18.44; glibc version in the JSON snapshot |
| Python | 3.13.5; the experiment runner uses only the standard library |
| Godot | 4.7.2.stable.official.ed1daf0bf, verified supplied Linux x86-64 executable |
| CPU view | Five visible/affinity-available logical CPUs; `cpu.max = 400000 100000`, a shared four-CPU-equivalent quota |
| Memory | `memory.max = 4294967296`, a shared 4 GiB cgroup limit |
| Process limit | Leaf `pids.max = max`; this is not a claim of unlimited process capacity or resources |
| Tool identities | Shell route uid 0; Python/Jupyter route uid 1000; all final native experiment groups were launched through Python as uid 1000 |
| Graphics | Xvfb/xauth available; actual OpenGL 4.5 Core Profile, Mesa 25.0.7-2, LLVMpipe (LLVM 19.1.7, 256 bits) |
| Software Vulkan | No ICD manifest in the standard location; not provisioned or executed in this experiment |
| Native executables | Git, Node, GNU timeout, taskset, FFmpeg and a compiler available; no Codex, Docker or Podman executable on PATH |
| Network | One ordinary public Git clone failed on GitHub DNS resolution. Web/GitHub connector reads worked separately. A generic download tool did not deliver the repository archive. No broader network capability was inferred |
| Input availability | The previously supplied/project-associated Godot ZIP was mounted in this session. Its continued availability is an observation, not proof of a persistent installed engine across all chats |
| Model routing | No callable general spawn interface exposed here; model token/cost/routing telemetry unavailable, not zero |

The CPU quota is derived from its quota/period, not from visible processor count. Linux cgroup controllers apply resource limits to process groups; spawning children does not itself allocate additional quota. [S3]

### Input integrity

The archive was 77,860,424 bytes with SHA-256:

```text
cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4
```

That matched the previously retrieved official upstream release-asset metadata. Only the expected executable was extracted. Its 146,414,384 bytes hashed to:

```text
8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e
```

`--headless --version` reported the expected engine build. Integrity identifies the input; it does not certify an arbitrary user script or every engine feature. [S6]

## Are Python and shell separate sandboxes?

A synthetic marker written by Python was readable from the shell. The two routes matched the observed mount, PID, network, IPC, UTS and user namespace identities. Their cgroup namespace identities differed, while the reported cgroup membership and resource view matched. Only equality results, not raw namespace identifiers, are retained.

We also observed a real permissions boundary: Python could read the shell-created directory but could not write to the root-owned location. The experiment then used a Python-owned temporary output directory. Only the new experiment executable's file mode was made readable/executable; no host services, permissions outside the experiment, system installation or privilege escalation was used.

Conclusion: the exposed tools are not interchangeable permission contexts, but these observations do **not** support treating them as independently allocated sandbox instances. The tested Python coordinator and its Godot children matched all seven sampled namespace identities and reported the same cgroup membership. Separate directories prevent accidental output collisions, not access by a hostile peer with the same identity.

## Reproducible method

Files in this directory:

- [probe.gd](probe.gd) and [project.godot](project.godot): original native rigid-body fixture, with optional viewport readback.
- [run.py](run.py): a bounded Linux subprocess coordinator, not an agent framework.
- [test_runner.py](test_runner.py): seven offline regression checks for the coordinator.
- [results.json](results.json): native check values, parameter sets, timing/overlap, sampled memory, identity comparisons and source hashes.

The coordinator starts one pilot before a three-worker batch. Each child waits until the coordinator sees all ready records, then receives a release marker. It receives a unique project, `user://` backing directory, configuration, cache/config/runtime paths and output directory. Python's `Popen` supplies native subprocess execution; `start_new_session` and bounded process-group cleanup are used, not a claimed container boundary. [S4]

Each worker is pinned to one available CPU for this demonstration; software rendering uses one LLVMpipe worker thread. These are local experimental controls, not recommended universal defaults. The group has a 25-second watchdog; a caller also bounded each invocation at 32 seconds. Missing readiness/completion, native errors, missing checks, unexpected exits and invalid PNG hashes fail the run. The engine is never installed or downloaded by this runner.

### Workload and parameters

The fixture creates a sphere of radius 0.25 at y=3, a large static floor, and actual Godot rigid-body simulation. Gravity scale and initial horizontal velocity differ:

| Worker | Gravity | Initial horizontal speed | Render hue |
| --- | ---: | ---: | ---: |
| 1 | 4.9 | 0.6 | 0.05 |
| 2 | 9.8 | 1.2 | 0.35 |
| 3 | 19.6 | 1.8 | 0.65 |

At tick 30 the test checks approximate free-fall and horizontal displacement against these inputs. Its tolerances allow a callback-order tick and are disclosed in the source. At completion it checks tick count, contact, resting height and an unchanged worker-specific user-data marker. The missing-floor control must reject contact and resting-height claims while still reporting its other observations.

The headless workload advances 6,000 physics ticks per process, or 100 simulated seconds. The rendering workload advances 180 physics ticks per process and reads back one final 320 x 240 PNG. Normal Godot runs inside separate Xvfb displays for rendering; `--headless` is used only for the non-rendering experiment. Godot's display/render/clock CLI options are documented separately. [S5]

## Measured results

| Final workload | Processes | Expected result | Group wall time | Simultaneous native-work interval | Sampled sum of Godot RSS |
| --- | ---: | --- | ---: | ---: | ---: |
| Headless pilot | 1 | 6/6 checks pass | 0.898 s | Not a parallel claim | 104.16 MiB |
| Headless batch | 3 | 18/18 checks pass | 1.006 s | 365.648 ms common overlap | 310.23 MiB |
| Missing-floor control | 1 | Native exit 1; contact/rest checks fail | 0.610 s | Not a parallel claim | 103.94 MiB |
| Off-screen Compatibility batch | 3 | 27/27 checks pass | 5.638 s | 623.854 ms common overlap | 827.46 MiB |

The outer runner returns success for the negative-control experiment only because the specified native failure was actually observed. It is not a successful floor-contact result. A crash or missing native report is not an acceptable negative-control rejection.

### Evidence of actual overlapping work

All three headless workers were observed with positive in-progress physics counts at the same sampling point. Their native active intervals also overlap, and sampled per-process CPU-time increases were approximately 0.41, 0.40 and 0.39 seconds. All three rendering workers likewise had overlapping in-progress physics observations; sampled CPU-time increases were about 2.01, 2.27 and 2.12 seconds. The combined evidence is stronger than merely counting three `Popen` calls or three processes waiting at a startup barrier.

At tick 30, the three workers reported y approximately **2.407916, 1.815833 and 0.631666**, and x approximately **0.29, 0.58 and 0.87**. All healthy runs reported one floor contact and ended near y=0.24. Each owned user-state check passed. This shows different inputs reached actual engine simulation without colliding through a shared `user://` directory.

Each renderer produced a separately hashed PNG: **941, 947 and 948 bytes**, respectively. All three were decoded locally and opened for inspection: the small visible sphere was orange, green and blue at distinct horizontal positions against a dark floor/background. The fixture intentionally is not artwork; no aesthetic, smoothness, particle, terrain-addon or game-quality verdict follows. Image bytes stayed in the session, not Git or Actions storage.

### What the timings do not show

These are single-run demonstrations, not confidence intervals, maximum concurrency, a saturation study or a matched serial/parallel speedup benchmark. `--fixed-fps` controls simulation steps; the observed headless runtime was much shorter than simulated time despite also requesting `--max-fps`. Do not report these times as gameplay FPS or infer a wall-time guarantee from that flag combination.

The rendered and headless groups use different tick counts and rendering work. Their timing ratio is not a graphics overhead estimate. Reported RSS sums may count shared engine/library pages more than once; the sampled cgroup memory peak includes the coordinator, notebook and page cache. It peaked around 668 MiB in the headless batch and 1,126 MiB in the rendered batch. These are not dedicated per-worker allocations or exact private-memory measurements.

## Failures retained rather than disguised

The first native pilot stopped before readiness: the synthetic `SceneTree` callbacks were declared with `void` returns, but the installed engine requires boolean returns for those main-loop callbacks. The fixture was corrected; no engine check was disabled.

The first 180-tick headless batch passed its six checks per worker but completed native physics in only a few milliseconds. A 20ms observer saw at most one in-progress worker, so that run was **not** used as evidence of simultaneous physics execution. The final bounded headless workload used 6,000 ticks, 2ms observation and native interval timestamps; all three then showed overlapping work. This is a measurement repair, not a reason to inflate every future workload.

The initial Python write permission error and the direct Git DNS failure also remained explicit. No account keys were sought, no model service was invoked and no sandbox restrictions were bypassed.

## Running the case again

Supply an already verified matching Godot executable and use **new output directories**:

```sh
python3 -S -m unittest discover -s references/chatgpt-parallel-native-processes-2026-09 -p test_runner.py -v

python3 -S references/chatgpt-parallel-native-processes-2026-09/run.py \
  --engine "$GODOT_BIN" --output /tmp/native-pilot-new --workers 1
python3 -S references/chatgpt-parallel-native-processes-2026-09/run.py \
  --engine "$GODOT_BIN" --output /tmp/native-three-new --workers 3
python3 -S references/chatgpt-parallel-native-processes-2026-09/run.py \
  --engine "$GODOT_BIN" --output /tmp/native-rejection-new --workers 1 --omit-floor
python3 -S references/chatgpt-parallel-native-processes-2026-09/run.py \
  --engine "$GODOT_BIN" --output /tmp/render-three-new --workers 3 --render
```

The graphics option additionally requires Xvfb, xauth, Mesa OpenGL and matching native libraries. The code has no model, API, network or installation step. Use this as a reproducible case study, not as a substitute for a game's established test runner. Original fixture source hashes are stored with the measurements.

## Engineering conclusion and boundaries

For independent deterministic Godot parameter tests, a small subprocess pool already provides the requested useful work **without Codex, extra model calls or cloud artifact transport**. Begin with a pilot and a small concurrency count, give each worker disjoint mutable state and bound process cleanup. Keep the coordinator's model context for diagnosis and decisions, not per-frame logs.

Use actual AI subagents when independent reasoning, exploration or review justifies their context and coordination cost. Verify that the active host exposes the interface and record actual agent IDs/results before claiming delegation. Use independent sandbox allocation only when isolation or additional resources are required; do not infer it from agent count. A model name or documented feature is not a live-tool entitlement.

This session did **not** execute multiple AI agents, create multiple ChatGPT sandboxes, test ChatGPT Work delegation, run Vulkan/Forward+, run private game code, benchmark hardware GPUs, perform normal-speed gameplay review, test a browser export, or test the maximum supported fan-out. The seven coordinator tests passed, as did the native experiments above. The repository-wide `make check` was not run locally because the public checkout download/clone was unavailable; that check remains separate from this selected-source case study.

## Primary sources

All product capabilities were reviewed September 26, 2026; these pages can change.

- **S1:** [OpenAI: Subagents in ChatGPT Work and Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents). Product support, eligibility and explicit/proactive delegation. Not evidence of this session spawning agents.
- **S2:** [OpenAI Agents API: Multi-agent](https://developers.openai.com/api/docs/guides/agents-api/multi-agent). Own agent contexts and a shared configured environment; spawning does not allocate another environment.
- **S3:** [Linux kernel: cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html). Quota, memory and process-group interpretation.
- **S4:** [Python: subprocess](https://docs.python.org/3/library/subprocess.html). Native process creation, session and timeout primitives; not model delegation.
- **S5:** [Godot: command-line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html). Headless/display/render selection and clock controls.
- **S6:** [Official Godot 4.7.2 release](https://github.com/godotengine/godot-builds/releases/tag/4.7.2-stable), [specific Linux asset metadata](https://api.github.com/repos/godotengine/godot-builds/releases/assets/519677358). Input identity and digest.
