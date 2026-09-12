# AGENTS.md template

Keep this file small and durable.

## Repository purpose
Describe what the repository owns and explicitly does not own.

## Start here
Point to the minimum canonical architecture/task documentation.

## Build and test
Document deterministic commands and the cheapest useful validation sequence.

## Agent execution rules
- Inspect before modifying.
- Preserve behavior unless the task explicitly changes it.
- Prefer deterministic tools for deterministic transformations.
- Keep tool output concise; inspect full logs only when needed.
- Record important assumptions and invalidations.
- Validate locally before declaring work complete.

## Local overrides
Document project-specific constraints here rather than modifying shared engineering guidance.
