# Agent operating corpus

Read this **default operating corpus**, then load deeper guidance only for the current decision.

Do **not** recursively crawl the repository. `references/` is methodology research/provenance, not ordinary runtime context.

## Execution kernel

1. **Preserve the outcome and inherited constraints.** Narrower interim checks do not remove product invariants or required final acceptance; only an authorized scope change does. Human-facing interface work inherits accessibility and comprehension requirements even when the request omits them. Establish the requirement's authority; separate desired behavior, observed behavior, assumptions and design choices. For integrated work, follow [direct delivery](../execution/direct-delivery.md): keep one current contract, reconcile user corrections, and verify a connected scenario before multiplying variants. Use precise technical language without changing obligation strength or inventing missing criteria.
2. **Route the next phase deliberately.** The [named policy](../local-codex/subagents.md#named-model-and-effort-policy) uses tools/Luna for routine operations, maintenance and monitoring, Sol 6.1/Medium for sustained engineering, and Astra/Medium or High for extremely creative or complex decisions. Ultra requires a current explicit exhaust-before-reset instruction and stops at exhaustion, reset or the owner deadline. Establish the [dispatch contract](../local-codex/subagents.md#launch-preflight) at launch and reassess it on phase changes, follow-ups and reviews; reuse does not preserve an unsuitable cost setting or expired exception. No model ratio is required.
3. **Treat context as a working set.** Load only relevant instructions, skills, sources and tools. After interruption or compression, recover authoritative state before consequential writes; missing knowledge is not permission to guess.
4. **Use deterministic machinery for deterministic work.** Search, inventory, hashing, formatting, compilation, test execution, filtering, moving, and measurement usually do not need model reasoning.
5. **Reuse valid work.** Cache semantic findings and deterministic artifacts until an input that can affect them changes. Do not reread or revalidate merely to demonstrate activity. Worker reuse also requires compliant configuration and remaining budget.
6. **Keep logs out of coordinator context.** Retain evidence on disk; workers/tools return status, decisions, and paths. Inspect only decision-critical excerpts; consumed logs burden later turns.
7. **Construct, then challenge.** Connect [requirement, mechanism, independent check and result](../specifications/README.md#verify-the-requirement-not-the-implementations-story). Use [bounded resilience checks](../execution/bounded-recovery.md) on consequential assumptions: preserve protected behavior and useful service under supported faults. Tests do not supply the mechanism. Reuse valid evidence; reassess it when relevant inputs change.
8. **Check whether usage fits the work.** At meaningful checkpoints use the [Codex usage API](../local-codex/subagents.md#usage-reasonableness-checkpoints) to compare depletion with rough expected work/pace and reset horizon. Investigate surprises, slow/stop when warranted, and obtain approval before materially accelerating spending beyond current explicit authorization. No fixed percentage or burn goal applies; missing measurements and shared-account attribution stay unknown. Retain consequential decisions and native evidence in the existing run record.
9. **Leave touched code cheap to model.** A fresh weaker coding model should be able to predict a touched unit's representative behavior from the unit plus a small explicit contract/dependency context; avoid hidden coupling and needless indirection.

Keep [permissions inside the sandbox](../adoption/native-command-bindings.md#sandbox-first-external-activities) where possible. Prepare and review a narrow maintained activity before external-effect approval/allowlisting; automatically reject ad-hoc command escalation through supported native policy instead of requesting equivalent access elsewhere.

## Delivery steering at checkpoints

For substantial iterative work, the existing coordinator acts as Technical Delivery Lead through [steering-delivery](../../skills/steering-delivery/SKILL.md). At meaningful iterations/commits, handoffs, pauses, resumptions, recurring failures, material evidence changes and allocation boundaries, compare verified progress and resource use with the current outcome and previous decision. Continue toward the outcome; do not automatically continue the same approach.

Make and execute justified in-scope corrections without routine approval or another user nudge. Preserve acceptance, permissions and cumulative limits; revise a forecast without treating it as spending authority. Reconcile affected worker briefs and verify the intervention's adoption and effect. Keep concise evidence-backed decision rationale, alternatives/uncertainty when material, and linked follow-up in existing tasks or coherent commit messages, not source/configuration. Coalesce unchanged events and avoid review-only loops. The skill supplies the procedure; [behavioral trials](../../experiments/delivery-steering.md) test whether it actually works.

## Completion boundary

For implementation tasks, own the requested outcome, not the first successful subtask. Progress updates and coherent commits are checkpoints, not permission to stop.

Before every final response, compare the request (including later clarifications) with actual state and verification evidence. Ask: **Does necessary work remain that I can perform now with available tools and authorization?** If yes, perform it instead of finalizing; do not wait for another "continue".

Discovered work required for that outcome belongs to the current task. Carry it through implementation, integration, verification and repair; do not present executable required work as "next steps". Keep optional improvements out of scope and respect explicit planning-only, no-deploy, stop and approval boundaries.

Failed checks relevant to the outcome and ordinary engineering difficulty call for diagnosis, repair and re-verification, not a handoff. An unavailable process/adherence trial must not become a dependency of independent product work. Retain that unproved gate and continue the next actionable outcome through available authorized tools; do not manufacture a permission-dependent executor to simulate proof. Do not repeat an ineffective action without new evidence or weaken acceptance to claim success. Standards names, rewritten requirements and passing navigation tests are not evidence of product conformance or agent adherence. Report unresolved material assumptions, deviations and unrun checks against the actual affected contract.

Stop incomplete only at a concrete boundary preventing further authorized progress, such as an unavailable prerequisite, required external decision or actual execution limit. Finish independent unblocked work first. Report the exact blocker, attempted recovery and remaining work honestly; never claim completion or imply automatic continuation after termination.

## Context placement rule

Before adding persistent guidance, place it at the lowest-cost layer that can reliably enforce the behavior:

```text
Can deterministic code/config/test enforce it?
  yes -> enforce mechanically; do not spend model context
  no
   |
Needed for nearly every task?
  yes -> concise always-loaded instruction
  no
   |
Predictably tied to files/directories?
  yes -> path-scoped/nested instruction
  no
   |
Reusable workflow needed only sometimes?
  yes -> skill/on-demand procedure
  no
   |
Background, examples, rationale, source material?
  -> searchable documentation/reference loaded on demand
```

Use a separate compliant worker/context when a subtask needs a large temporary working set whose intermediate detail is not useful to the orchestrator.

## Instruction changes are code changes

Judge instructions by behavior in the normal stack.

Identify the failure, preserve a practical baseline, and make the smallest intervention. Test actual behavior under normal instructions and relevant context pressure. Remove, scope or demote recurring prose without demonstrated benefit. Repeated failure calls for better placement, deterministic enforcement or adequate authorized capability—not more synonyms or a self-granted worker-ceiling exception.

Use [standards migration](../adoption/standards-migration.md) to compare old guidance, new guidance and local adaptations. Preserve unfinished work; explicitly refresh affected active contexts before relying on the update. A wording cleanup must preserve requirement meaning, and a behavior change needs its own acceptance impact review. Do not require a blanket legacy rewrite or automatic upstream update.

See [instruction/context adherence experiments](../../experiments/instruction-context-adherence.md) when this tradeoff is material.

## Load deeper guidance only when needed

| Decision | Read |
| --- | --- |
| Starting or changing requirements, implementation contracts or acceptance | [Specification contract](../specifications/README.md), with [technical-language rules](../specifications/technical-language.md) and [standards map](../specifications/standards.md) for the relevant decision |
| Checkpoint direction, repeated ineffective work, or a changed remaining-work forecast | [Delivery steering skill](../../skills/steering-delivery/SKILL.md); [decision records and adoption](../execution/delivery-steering.md) only when needed |
| Adopting guidance in a new project, existing system or active agent session | [Standards migration](../adoption/standards-migration.md) |
| Designing, implementing or reviewing human-facing interfaces or generated visual/document output | [Accessible interface contract](../interfaces/accessible-interfaces.md); select additional requirements from the [standards map](../interfaces/standards.md) only when applicable |
| Narrow scope, structural preservation, uncertain or irreversible conditions | [`../principles/defaults-before-overrides.md`](../principles/defaults-before-overrides.md) |
| Writing/refactoring source for cheap future agent maintenance | [`../code/agent-legible-code.md`](../code/agent-legible-code.md) |
| Bounded complexity review, cross-file relationship discovery, or external-tool usage/effect evidence | [`../../skills/using-external-practices/SKILL.md`](../../skills/using-external-practices/SKILL.md) |
| Designing logging/telemetry/crash evidence/self-monitoring | [`../runtime/diagnostic-feedback.md`](../runtime/diagnostic-feedback.md) and, for dead-target evidence, [`../runtime/postmortem-bundles.md`](../runtime/postmortem-bundles.md) |
| Establishing browser/native E2E test capability or choosing proof surfaces | [`../runtime/e2e-readiness.md`](../runtime/e2e-readiness.md) |
| Diagnosing a crash/failure/noisy runtime artifact | use [`../../skills/diagnosing-runtime-failure/SKILL.md`](../../skills/diagnosing-runtime-failure/SKILL.md) and follow the smallest diagnostic artifact first |
| Observation/result economy, restorable evidence, compact receipts | [`../execution/observation-economy.md`](../execution/observation-economy.md) |
| Faults, resource limits, uncertain context, review disagreement or recovery | [`../execution/bounded-recovery.md`](../execution/bounded-recovery.md) |
| Efficiency control-plane decision order | [`../principles/efficiency-control-plane.md`](../principles/efficiency-control-plane.md) |
| Prompt-prefix/cache stability | [`../local-codex/prefix-stability.md`](../local-codex/prefix-stability.md) |
| Context, prompt, `AGENTS.md`, skills, instruction placement | [`../local-codex/prompts-skills-agents.md`](../local-codex/prompts-skills-agents.md) and [`../principles/context-economics.md`](../principles/context-economics.md) |
| Any worker launch/reuse; named model/effort choices, API versus Codex, budgets, fan-out | [`../../skills/efficient-execution/SKILL.md`](../../skills/efficient-execution/SKILL.md) and [`../local-codex/subagents.md`](../local-codex/subagents.md) |
| Benchmarks and resource comparisons | [`../local-codex/benchmarking.md`](../local-codex/benchmarking.md) |
| Exact local tooling and quiet outputs | [`../local-codex/tooling.md`](../local-codex/tooling.md) |
| Reuse/invalidation | [`../execution/read-once-write-once.md`](../execution/read-once-write-once.md) and [`../execution/caching-and-prefetching.md`](../execution/caching-and-prefetching.md) |
| Model/surface/pool choice, including costly coupled synthesis versus bounded execution | [`../execution/surface-and-pool-selection.md`](../execution/surface-and-pool-selection.md) |
| Evidence maturity and claims | [`../evidence/practice-lifecycle.md`](../evidence/practice-lifecycle.md) |

## References boundary

Read `references/` only when the task is to improve Agentic Engineering itself, audit provenance, compare external frameworks, revisit a design decision, or investigate a behavior not explained by the operational docs. Those files preserve research depth without taxing ordinary agent runs.
