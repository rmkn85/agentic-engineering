@AGENTS.md

## Claude Code

- `.claude/settings.json` runs `tools/finish_check.py` as a Stop hook. It does nothing until `.agent/goal.json` exists; then it blocks the first stop while a check is unmet.
- Skills are in `skills/<name>/SKILL.md`; open the one the current decision needs.
- A PreToolUse hook runs `tools/guard_command.py`: it refuses desktop control or capture outside an isolated display, force-push, and commands that discard uncommitted or unmerged work. Ask the owner instead of working around a refusal.
