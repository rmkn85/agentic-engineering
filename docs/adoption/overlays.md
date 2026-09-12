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

The nearest relevant context wins when rules conflict.

## Promotion rule

A practice should move into shared guidance only when there is a reason to expect it to remain useful after changing domains.

When uncertain, keep the rule local. Premature generalization turns a useful knowledge base into bureaucracy.

## Consumption

Projects should be able to adopt shared material selectively. Avoid hard dependencies on a central repository for ordinary development unless a tool truly requires them. Shared knowledge should improve local autonomy, not create a new central point of failure.
