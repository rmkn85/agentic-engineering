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

## Portable skill routing

Keep one maintained procedure and a short route to it. Use these layers:

| Layer | Keep here |
| --- | --- |
| Host configuration / global instructions | A short trigger to use the available skill; no checkout-specific paths or full protocol |
| Workspace instructions | The actual workspace-relative skill path and what to do if the optional checkout is absent |
| [`efficient-execution`](../../skills/efficient-execution/SKILL.md) | Executor choice, worker return contract, evidence inspection and phase-boundary notes |
| Linked operational documentation | Examples, exceptions and rationale, loaded when needed |

For a host that discovers the skill, the router can be:

> For long repository- or tool-heavy work, load efficient-execution when available.

If the skill is not in the host's catalog, place an explicit path router in the workspace's normal startup instructions. For example, **adapt the path to the adopting workspace**:

> Before the first substantial batch of long repository- or tool-heavy work, read `agentic-engineering/skills/efficient-execution/SKILL.md` from this workspace root when present; otherwise use the simplest adequate route.

Choose the discoverable-skill route or the workspace-path fallback as appropriate; do not paste the entire procedure into both configuration and `AGENTS.md`. Existing global executor-selection guidance can stay short. Put any additional handoff detail in the skill and link to examples from there.

Use a maintained checkout or the host's supported skill installation mechanism. Preserve referenced resources: copying only `SKILL.md` can break its relative links into this repository. A path or symlink must resolve on the consuming machine; a link on one workstation is not an installation on another. Record the adopted repository revision in the project's normal dependency or setup record when reproducibility matters.

Do not copy a personal config wholesale. It may contain machine paths, service settings, permissions or credentials. Install only the required routing text through a mechanism supported by that host; a custom configuration key observed in one runtime is not a portable interface. If the current sandbox cannot update that location, prepare a reviewable patch and report that activation remains pending.

## Verify adoption in a fresh task

Check these separately after changing host, user, workspace or runtime:

1. **Available:** the skill and its referenced resources resolve locally.
2. **Delivered:** a fresh task receives the router or skill metadata. Check child workers independently; parent-directory startup may omit child-repository instructions.
3. **Applied:** a representative task loads the relevant procedure and returns compact, traceable evidence while meeting the original acceptance criteria.

A saved config, successful manual read or explanation of the rule proves neither automatic delivery nor behavior. An already-running parent may retain stale instructions. Keep simple tasks as a negative case: they should not load the full workflow merely because it exists.

Use the [instruction-adherence protocol](../../experiments/instruction-context-adherence.md) for the smallest relevant behavioral check. The [September portability observations](../../references/portable-execution-lessons-2026-09.md) explain the failure cases behind this guidance; they do not establish universal compliance or measured token savings.
