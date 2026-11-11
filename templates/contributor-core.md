# Shared contributor core

Apply this to the task you were given. Product rules, task ownership, branch
policy and acceptance stay local; the repository entry names its commands.
This copy needs no upstream checkout.

## Every task, in this order

1. **Focus.** Run the repository's work audit (`work_audit.py`) and do its FOCUS
   line first, unless the user names a different task. It reads the
   repository's history, so every agent gets the same answer.
2. **Goal.** Take the user outcome from the task. Write it and the checks that
   prove it in the goal record. A ready task is eligible, not automatically the
   priority: pick the one that closes the largest gap in a user journey.
3. **Change behaviour.** Progress is changed behaviour that a check proves.
   Complete the next missing connection through its existing owner and public
   contract. Keep enabling work tied to that result; records, handoffs and
   process changes support it and stay a small share of commits.
4. **Build the simplest sufficient code.** Compare one simpler complete
   implementation and use it unless a required case fails. Route every caller
   through the single owner of the behaviour; do not copy its policy.
5. **Prove it at the real boundary.** Test the changed behaviour with a case that
   would fail without the change. A green pipeline, a push or a skipped test is
   not acceptance. Diagnose, repair and re-check failures before finishing.
6. **Finish.** Compare the request with actual state. Do the remaining work you
   can do now; "next steps" are only for work you cannot do. Stop incomplete only
   at a named external blocker, and say what is missing.

## Preserve architectural decisions

Before changing who calls whom, authorizes actions, owns data or makes decisions,
trace the accepted design to its product invariant. Compare that authority with
current code, documentation and the proposal; code and green tests cannot
overturn it. Verify both the intended flow and the forbidden dependency:
prove the dependency is absent or make its attempted use observable. Restore
conformance within existing authority; take an actual design change to the
System Architect through the existing decision route. Routine implementation
within the accepted boundary needs no new approval or standing review board.

## When stuck

Do not repeat a step that failed: name what it failed to achieve and change the
approach. Classify a missing prerequisite once and use its supported route.
Recover from the smallest diagnostic artefact, make the smallest repair, and
resume the original delivery. At checkpoints of long work, use the
`steering-delivery` skill, or this fallback: compare progress and cost with the
goal, choose the next action, and check its effect next time.

## Hard limits

- Preserve other writers' uncommitted and unmerged work: never force-push,
  reset or switch their checkout.
- Never hunt for credentials or widen permissions to get past a sandbox; use
  the allowlisted activities and ask for anything else.
- Never claim completion, approval or acceptance that did not happen.

## Handoff

Replace one current handoff under 800 words: goal, proven state, next action;
history stays in Git/tasks. Touched audit-flagged areas must meet their limits.

## Engineering personas

Use these role names in assignments, handoffs and reports:

| Persona | Responsibility |
| --- | --- |
| System Architect | Architecture, system boundaries and technical design decisions. |
| Product Manager | Product direction, intended behavior, priorities and acceptance expectations. |
| Operator | Uses the delivered system and handles operational actions through established controls. |
| Component Epic Owner | Owns a component's backlog and end-to-end delivery. |
| Software Engineer | Implements, tests, publishes, deploys and repairs within the assigned scope. |

Choose the persona from the responsibility in the current request. Labels
describe responsibility; they grant no permission and create no approval.
Restoring a delivered capability is an Operator concern handled by its
engineering owner. Escalate only real architecture or product-direction
decisions.

## Share improvements

Offer the smallest tested recurring-failure fix upstream without private detail.
Review adoption differences; do not fetch upstream text every task.
