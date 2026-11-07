@AGENTS.md

## Claude Code

- `.claude/settings.json` runs `tools/finish_check.py` as a Stop hook. It blocks finishing while a check in `.agent/goal.json` is unmet (at most three times, then ends with a visible warning), and asks once for a goal record when files changed without one.
- Skills are in `skills/<name>/SKILL.md`; open the one the current decision needs.
- `permissions.allow`, rendered from `configs/allowed-activities.json`, runs sanctioned activities without approval. Otherwise, get approval or propose a new reviewed activity. `tools/guard_command.py` is only a backstop for accidental destructive commands.
