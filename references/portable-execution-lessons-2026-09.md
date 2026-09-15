# Portable execution lessons — September 2026

Status: anonymized qualitative observations from an engineering task and fresh-worker startup probes, recorded 2026-09-15. No controlled token-savings or performance benchmark was performed. Raw transcripts, personal configuration, and product-specific files are not published here; these observations are leads for reproduction, not independent acceptance evidence for another installation.

## Instruction placement and delivery

- An observed runtime supplied a custom multi-agent policy that permitted bounded delegation. This establishes only the effective behavior in that run; copied configuration keys or saved configuration alone would not establish a portable interface or the effective policy elsewhere.
- A repository-local efficiency skill existed but was absent from the runtime skill catalog. Adding a concise workspace path router made the route visible in a fresh worker's supplied startup context. This established delivery of the router, not automatic catalog installation or universal behavioral adherence.
- A worker launched from the multi-repository parent received workspace instructions but read child-repository instructions manually. Those are separate loading paths and must be reported separately.
- One restricted environment could prepare and dry-run a host-level configuration patch but could not apply it within its authorized write scope. Activation in a fresh session remained a separate, unverified step.

## Context growth and handoffs

The task used bounded workers but retained substantial implementation and runtime inspection in the parent. Delegation therefore did not prevent parent context growth. After compaction, a task summary retained changed files, test outcomes and unfinished acceptance; the complete earlier tool stream was no longer directly available to the continuation. No exact allocation of context by tools, workers or instructions was measured.

The operational response is [compact handoffs and selective evidence inspection](../docs/local-codex/subagents.md#handoff-and-retained-context), with [portable routing](../docs/adoption/overlays.md#portable-skill-routing) to activate the existing skill. Adding another large always-loaded policy would also add recurring context.

## Runtime capability and acceptance

One environment-specific audit exercised browser rendering/input, a web export, native rendering/capture, and automation boundaries. Required export dependencies had to be installed, and the actual renderer mattered; software rendering could not establish hardware performance. These capability results require fresh probes in another environment.

The reusable result is the [E2E-readiness method](../docs/runtime/e2e-readiness.md): verify each required surface independently and preserve the distinction between automated assertions, inspected rendering, native behavior, performance and human acceptance. Record required dependency versions in scoped evidence; do not copy host paths, ports, device/driver inventory, or local workarounds into global policy.

## What would revise these practices

If normal runtime discovery reliably exposes the skill, omit the workspace fallback. If an orchestrator must inspect original evidence for a risky decision, expand that evidence selectively. If compact handoffs lose contradictions or require repeated clarification, improve the return contract before shrinking it further. Compare resource use only with equivalent task coverage and acceptance; worker count and shorter prose alone establish no saving.
