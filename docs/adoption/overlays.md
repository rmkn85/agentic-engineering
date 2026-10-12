# Shared defaults and local overlays

The effective methodology for a task should be composed rather than centralized.

Conceptually:

```text
shared engineering defaults
+ organization/domain practices
+ repository-specific instructions
+ current task constraints
= effective policy
```

Follow the host's instruction precedence and the user's authorized scope. A local overlay cannot override higher-priority runtime policy or grant new permissions.

## Promotion rule

A practice should move into shared guidance only when there is a reason to expect it to remain useful after changing domains.

When uncertain, keep the rule local. Premature generalization turns a useful knowledge base into bureaucracy.

## Consumption

Projects should be able to adopt shared material selectively. Avoid hard dependencies on a central repository for ordinary development unless a tool truly requires them. Shared knowledge should improve local autonomy, not create a new central point of failure.

For a fresh or stale checkout given only a repository location, use the [repository-only contributor contract](newcomer-contract.md). Bind shared lessons to existing native setup, checks and delivery; apply them by process capability rather than by which project first encountered a failure. The [anonymized contributor lessons](../../references/portable-contributor-lessons-2026-09.md) preserve rationale outside normal task context.

## Portable skill routing

Keep one maintained procedure and a short route to it. Use these layers:

| Layer | Keep here |
| --- | --- |
| Host configuration / global instructions | A short trigger to use the available skill; no checkout-specific paths or full protocol |
| Workspace instructions | The actual workspace-relative skill path and what to do if the optional checkout is absent |
| [`efficient-execution`](../../skills/efficient-execution/SKILL.md) | Executor choice, worker return contract, evidence inspection and phase-boundary notes |
| [`steering-delivery`](../../skills/steering-delivery/SKILL.md) | Checkpoint direction, authorized plan changes, task/commit decision rationale and observed effect |
| Linked operational documentation | Examples, exceptions and rationale, loaded when needed |

For a host that discovers the skills, the router can be:

> For substantial iterative engineering, use efficient-execution and steering-delivery when available. The coordinator owns authorized next-action decisions at checkpoints and records their rationale and effect in tasks or commit messages.

If the skills are not in the host's catalog, place an explicit path router in the workspace's normal startup instructions. For example, **adapt the path to the adopting workspace**:

> Before the first substantial batch, read `agentic-engineering/skills/efficient-execution/SKILL.md` and `agentic-engineering/skills/steering-delivery/SKILL.md` from this workspace root when present. Use steering-delivery at subsequent meaningful checkpoints without rereading unchanged guidance. If the optional checkout is absent, use the local contributor core and simplest adequate route; do not claim the skills were loaded.

Choose the discoverable-skill route or the workspace-path fallback as appropriate; do not paste the entire procedure into both configuration and `AGENTS.md`. Existing global executor-selection guidance can stay short. Put any additional handoff detail in the skill and link to examples from there.

Use a maintained checkout or the host's supported skill installation mechanism. Preserve referenced resources: copying only `SKILL.md` can break its relative links into this repository. A path or symlink must resolve on the consuming machine; a link on one workstation is not an installation on another. Record the adopted repository revision in the project's normal dependency or setup record when reproducibility matters.

Do not copy a personal config wholesale. It may contain machine paths, service settings, permissions or credentials. Install only the required routing text through a mechanism supported by that host; a custom configuration key observed in one runtime is not a portable interface. If the current sandbox cannot update that location, prepare a reviewable patch and report that activation remains pending.

## Reload an active task

An explicitly authorized reload uses the existing snapshot/update route, preserving local adaptations, unfinished changes, active ownership and consumed allocations. Read the updated repository entry, operating corpus and relevant skills. Record the adopted revision in the existing task or next coherent commit message, perform one steering checkpoint against current evidence, and execute the resulting authorized next action. Do not turn reloading into a new project or a request for routine approval.

Deliver material changes to active worker briefs through supported controls and verify their adoption. A file update alone does not refresh an already-running worker or parent. Use the host's normal continuation path when live refresh is unavailable; do not claim a new session or installed callback without evidence. No automatic upstream pull, global Git hook or new orchestrator is installed by these documents. See [steering adoption](../execution/delivery-steering.md#activate-in-an-existing-task).

## Verify adoption in a fresh task

Check these separately after changing host, user, workspace or runtime:

1. **Available:** the skill and its referenced resources resolve locally.
2. **Delivered:** a fresh task receives the router or skill metadata. Check child workers independently; parent-directory startup may omit child-repository instructions.
3. **Applied:** a representative task loads the relevant procedure and returns compact, traceable evidence while meeting the original acceptance criteria.

A saved config, successful manual read or explanation of the rule proves neither automatic delivery nor behavior. An already-running parent may retain stale instructions. Keep simple tasks as a negative case: they should not load the full workflow merely because it exists.

Use the [instruction-adherence protocol](../../experiments/instruction-context-adherence.md) for the smallest relevant behavioral check, including [delivery-steering trials](../../experiments/delivery-steering.md) when checkpoint decisions change. Record the decision, actual worker adoption and subsequent effect separately; a good-looking plan is not evidence of better delivery. The [September portability observations](../../references/portable-execution-lessons-2026-09.md) explain the failure cases behind this guidance; they do not establish universal compliance or measured token savings.
