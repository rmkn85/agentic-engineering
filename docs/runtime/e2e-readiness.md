# Runtime E2E readiness

End-to-end readiness is a set of **scoped capabilities**, not a single environment label. Probe only the boundaries required by the acceptance plan, record what actually ran, and keep unavailable capabilities separate from product failures.

## Choose the proof surface

Use this compact rule:

- use **web** for browser, DOM, responsive-layout and WebGL behavior;
- use **native** for operating-system integration, packaging and device behavior;
- use **both** when shared visual or input changes ship on both targets;
- treat **headless engine runs as supplementary** unless headless execution is itself the shipped target.

Do not infer one surface from another. A loopback site may be reachable and WebGL may render even when native window automation or capture is unavailable. Conversely, a native launch says nothing about browser input, DOM integration or responsive layout.

## Probe capabilities before spending the full run

Run the smallest harmless probe that answers whether each required boundary is usable. Prefer project-owned entry points and documented tool interfaces; do not improvise undocumented flags or installation steps.

| Boundary | Minimum decisive probe | Evidence to retain |
| --- | --- | --- |
| External web service | Resolve and make one bounded request to the exact required service; check the expected status and a stable response property. | Service identity, operation, result, timestamp and sanitized error. |
| Loopback HTTP | Start the project-owned server, wait on its readiness endpoint or expected page, make one request, then stop only the process started by the run. | Run/server identity, resolved address, readiness result, logs and teardown result. |
| Integrated browser | Load the exact loopback page; query one stable DOM target, perform one representative input, collect console errors, capture and inspect an image, and exercise required viewport sizes. If WebGL matters, use a supported capability probe or application graphics diagnostics. | URL, build/run identity, DOM and input assertions, viewport sizes, console summary, inspected captures and available renderer report. |
| Engine headless | Launch the project through its owned engine entry point and execute the smallest deterministic scene/test relevant to the change. | Project/build identity, invoked target, exit/result and focused logs. |
| Web export and play | Verify required export support independently of engine launch, write to an explicit resolved output path, serve the artifact, and exercise it in the browser. | Export configuration/result, resolved artifact path, server identity and browser evidence. |
| Native application | Launch the packaged or project-native target, prove a rendered frame, exercise required player controls, and capture through an available native/platform path. | Package/build and process/run identity, render/capture evidence, exercised controls and platform details. |

Keep probes narrow. A generic internet request does not establish access to the required service. A listening port does not establish that the intended build is serving. A DOM lookup does not establish rendering. An engine version response does not establish that export templates or platform support are installed.

For local-only checks, prefer loopback binding and an available port; preserve existing listeners owned by other work. Verify export dependency versions and official integrity information before downloading, and reuse valid cached artifacts. If browser tooling cannot inspect an application-owned graphics context, report the direct capability/renderer probe as unverified; do not disturb that context just to obtain a result.

## Separate a prepared state from the journey into it

Use a named, seeded fixture to make an important state cheap to inspect. Expose a small read-only interface for its current mode, authoritative state revision, simulation time, readiness, active view and bounded work counters. Keep setup mutation explicitly test-owned.

Exercise the transition separately through ordinary inputs. Loading a completed state cannot prove loading, navigation, interaction, cancellation or save/reload on the way into it. For a spatial application, a visible surface does not prove contact or hazard queries are ready: delay those dependencies and verify the application's pending behavior, recovery and stale-result rejection. Tie screenshots to the state and input trace that produced them.

When diagnosing visual and timing failures together, compare the same starting state, input path and quality policy. Isolate a suspected effect or scheduling policy before widening the change. Fewer draw calls, transferred bytes or discarded jobs prove changes in that work; they do not alone prove faster frames or good interaction. Human review remains necessary for perceptual and experiential acceptance.

## Make each run reproducible and attributable

Record enough identity to distinguish the tested artifact from stale or parallel work:

- source revision and dirty-state qualification;
- build/export identity and resolved artifact path;
- test, server, browser and application run IDs where available;
- target surface, viewport/device and meaningful configuration;
- engine/runtime and actual graphics renderer identity;
- start, readiness, shutdown and artifact status.

Resolve the intended output location explicitly before invoking an exporter. Relative export paths may be interpreted from the project rather than the caller's current directory; an explicit resolved path avoids inspecting or serving an older artifact by mistake.

In restricted environments, isolate writable runtime state in task-owned locations when the runtime supports standard state/config/cache directories. For example, a writable XDG-compatible state boundary can be necessary even when project files are writable. Treat this as a scoped runtime prerequisite, not permission to redirect or inspect unrelated user state.

For graphics-dependent claims, identify the renderer that actually ran or report it as unknown. A successful WebGL or native frame may use software rendering or another fallback. That can prove functional rendering, but it cannot support hardware-performance, driver or acceleration claims.

## Keep evidence levels distinct

| Claim | Required evidence | Does not establish |
| --- | --- | --- |
| Automated behavior passed | Named assertions against the intended run/build. | Visual quality or human usability. |
| A rendered frame was captured | Capture tied to the intended run and visibly inspected. | Interaction, animation over time or acceptance. |
| Native-platform behavior passed | Native package/project run on the named platform with required controls and integration exercised. | Other platforms or browser behavior. |
| Hardware performance passed | Measurements on identified representative hardware, renderer/driver and workload with an explicit threshold. | Performance on fallback rendering or unidentified hardware. |
| Human acceptance passed | A human completed the defined acceptance journey and recorded the outcome. | Nothing stronger than the journey and targets actually reviewed. |

Screenshot file existence is only artifact production. It becomes rendered visual proof after someone or a suitable visual oracle inspects the pixels and ties them to the intended run. Neither a screenshot nor automated input is, by itself, interactive human acceptance.

## Report outcomes without collapsing blockers into failures

For every planned check, report one of:

- **passed** — the named assertion or acceptance criterion ran and succeeded;
- **failed** — it ran against the intended target and contradicted the criterion;
- **blocked** — a required capability was probed and unavailable;
- **not run** — it was outside the chosen run or no attempt was made.

Preserve the test/run identity and the failing or blocking boundary. Browser-tool unavailability is not an application failure; a product assertion failure is not merely a readiness blocker. If a capability probe fails, keep its focused evidence and stop before launching an expensive suite that depends on it.

## Completion check

An E2E claim is ready only when the acceptance matrix names the shipped targets, every required capability has decisive current-run evidence, captures were inspected, inputs were exercised on the required surfaces, and blocked/not-run work remains visible. Source review, export success, server readiness, headless execution and screenshot creation are useful layers of evidence, but none should be promoted to full E2E success on its own.
