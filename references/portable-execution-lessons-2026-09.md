# Portable execution lessons — September 2026

Status: qualitative observations from a maintainer-run engineering task and fresh-worker startup probes, recorded 2026-09-15. No controlled token-savings or performance benchmark was performed. Raw task transcripts and product-specific files are not published here; these observations are leads for reproduction, not independent acceptance evidence for another installation.

## Instruction placement and delivery

- A custom multi-agent policy was present in the effective developer context and permitted bounded delegation without an explicit-user-request-only restriction. That host exposed `features.multi_agent_v2.enabled` and `multi_agent_mode_hint_text`; these are observed host-specific settings, not a supported configuration promise for other versions. Checking the saved configuration alone would not have established the effective policy.
- A repository-local efficiency skill existed but was absent from the runtime skill catalog. Adding a concise workspace path router made the route visible in a fresh worker's supplied startup context. This established delivery of the router, not automatic catalog installation or universal behavioral adherence.
- A worker launched from the multi-repository parent received workspace instructions but read child-repository instructions manually. Those are separate loading paths and must be reported separately.
- The active sandbox rejected editing a global config outside its writable roots. A one-line patch could be prepared and dry-run checked without broadening permissions. The user subsequently reported applying it; fresh-session activation still requires its own check.

## Context growth and handoffs

The task used bounded workers but retained substantial implementation and runtime inspection in the parent. Delegation therefore did not prevent parent context growth. After compaction, a task summary retained changed files, test outcomes and unfinished acceptance; the complete earlier tool stream was no longer directly available to the continuation. No exact allocation of context by tools, workers or instructions was measured.

The operational response is [compact handoffs and selective evidence inspection](../docs/local-codex/subagents.md#handoff-and-retained-context), with [portable routing](../docs/adoption/overlays.md#portable-skill-routing) to activate the existing skill. Adding another large always-loaded policy would also add recurring context.

## Runtime capability and acceptance

A prior local runtime audit reported working loopback HTTP, integrated-browser rendering/input and a successful engine web export after missing export templates were installed. Native rendering/capture was possible, while native GUI player control was unavailable through the exposed automation surface. Writable engine state directories and the actual graphics renderer mattered; software rendering could not establish hardware performance. These capabilities are environment-specific and require fresh probes on another host.

The reusable result is the [E2E-readiness method](../docs/runtime/e2e-readiness.md): verify each required surface independently and preserve the distinction between automated assertions, inspected rendering, native behavior, performance and human acceptance. Do not copy an engine version, graphics fallback, local port or workaround into global policy.

## What would revise these practices

If normal runtime discovery reliably exposes the skill, omit the workspace fallback. If an orchestrator must inspect original evidence for a risky decision, expand that evidence selectively. If compact handoffs lose contradictions or require repeated clarification, improve the return contract before shrinking it further. Compare resource use only with equivalent task coverage and acceptance; worker count and shorter prose alone establish no saving.
