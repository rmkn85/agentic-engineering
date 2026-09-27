# Configured self-hosted runner versus ChatGPT native execution

This bounded follow-up reuses the original [ChatGPT native fixture](../chatgpt-parallel-native-processes-2026-09/README.md), not private game code. It checks one headless pilot, three concurrent headless workers, a missing-floor rejection, one off-screen pilot and three concurrent renderers. Measurements are pending native execution at this implementation checkpoint; 17 focused Python tests passed locally.

The comparison uses the existing configured Godot binary, default graphics selection, standard tool paths and an authorized workspace. It does not install anything, probe the network, call a Docker daemon, bypass Bubblewrap, access the user's desktop, mount devices, edit permissions outside newly created owned files, or change quotas. `run.py --configured-drivers` preserves only allowlisted inherited graphics settings instead of the earlier explicit LLVMpipe override. The fixture's software-renderer assertion remains intact: a default renderer that does not satisfy it is reported as a failed/unsupported comparison, not silently replaced.

```sh
python3 -S references/self-hosted-native-comparison-2026-09/compare.py --workspace "$GITHUB_WORKSPACE"
```

All generated project/user/cache/config/output data goes into a new directory beneath the authorized workspace, and is removed after the result is summarized. Xvfb is a process-owned display using the sandbox's normal temporary socket facilities, not the user's display. The coordinator retains the exact first failure excerpt, not complete private machine logs. No cloud artifacts are uploaded. Three processes share one job's existing resource limits; this is neither model delegation nor allocation of three machines.

Results, comparison qualifications, limitations and primary references will be added after reading actual pipeline output. Any missing or blocked capability remains explicit rather than triggering a privileged workaround.
