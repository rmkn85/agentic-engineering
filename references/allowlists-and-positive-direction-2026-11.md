# Allowlists and positive direction: what the labs publish (reviewed 2026-11-07)

Why this repository moved from a deny-pattern command guard to a host-neutral
activity allowlist, and from prohibitions to stated actions. Claims below are
labelled: **documented** (vendor documentation or engineering posts),
**measured** (a number the source reports), **hypothesis** (our inference).

## Observed failure here

Four blind reviews of `tools/guard_command.py` each found new spellings that
slipped past it (redirects, wrappers, aliases, interpreter calls). Each fix
moved the boundary; none closed it. A pattern denylist cannot terminate against
a capable agent, and every refusal invites a search for another route.

## What the sources say

- **Boundaries beat prompts and per-command approval.** Anthropic sandboxes the
  Claude Code bash tool with filesystem and network limits and reports 84% fewer
  permission prompts in internal use (measured; [Anthropic, Oct 2025](https://anthropic.com/engineering/claude-code-sandboxing)).
  Its containment write-up reports users approved about 93% of prompts, so
  prompts train inattention; auto mode's classifier is defence in depth inside a
  sandbox, not a substitute, and missed 17% of overeager actions (measured;
  "How we contain Claude across products", May 2026, as summarised by
  [secondary sources](https://jc-aiwiki.pages.dev/claude-ai/anthropic-how-we-contain-claude)).
- **The sandbox is the default; rules are the named exceptions.** Codex separates
  the sandbox boundary from the approval policy and uses `prefix_rule` entries to
  allow, prompt or forbid specific command prefixes outside it; rules can carry
  `match`/`not_match` examples validated at load (documented; [Codex sandboxing](https://developers.openai.com/codex/concepts/sandboxing), [Codex rules](https://developers.openai.com/codex/rules)).
- **Default-deny allowlists are a documented pattern.** Gemini CLI's policy
  engine evaluates every tool call against tiered allow/deny/ask rules
  (documented; [policy engine](https://geminicli.com/docs/core/policy-engine)).
- **Say what to do, and why.** Anthropic's prompting guidance: tell the model what
  to do instead of what not to do, and give the reason, because the model
  generalises from the motivation (documented; Claude prompting best practices).
- **Pressure against observed misbehaviour teaches hiding.** OpenAI found that
  penalising a monitor-detected hack during training produced obfuscated reward
  hacking, not less hacking (measured; [Baker et al., 2025](https://arxiv.org/abs/2503.11926)).
  Anthropic found that reframing reward hacking as acceptable in training cut
  broad misalignment by 75-90% (measured; [MacDiarmid et al., 2025](https://arxiv.org/pdf/2511.18397v1)).
  Both are training-time results.
- **A map, not a manual; errors that teach.** OpenAI's Codex team kept AGENTS.md
  to about 100 lines pointing into a versioned docs tree, enforced architecture
  mechanically, and wrote lint messages as instructions (documented; [harness engineering](https://openai.com/index/harness-engineering/)).
- **Rules are prompts, not enforcement.** Cursor recommends short rules for
  repeated mistakes, on-demand skills, and hooks or tests for enforcement
  (documented; [agent best practices](https://cursor.com/blog/agent-best-practices)).
- **Agents judge their own work poorly.** Anthropic's long-running harness work
  uses a progress file, a feature list with pass flags, a baseline test at
  session start, and a separate evaluator (documented; Effective harnesses for
  long-running agents, Nov 2025).

## What changed in this repository

- `configs/allowed-activities.json` is the single, host-neutral list of local
  activities any agent may run without approval. `tools/allowlist.py` renders it
  for Claude (`permissions.allow`, held identical by a test) and Codex
  (`prefix_rule`). External effects stay with per-use approval.
- `tools/guard_command.py` is frozen as a backstop with a declared scope;
  reviewers test against that scope, and evasion findings are declined.
- AGENTS.md states actions with reasons where it previously only prohibited
  (`references/`, missing activities, next steps); hard limits such as private
  content stay prohibitions.

## Open questions and what would revise this

- Hypothesis: a runtime refusal can push an agent toward workarounds the way
  training penalties push toward obfuscation. The sources above measure
  training, not runtime refusals. A trial comparing refusal-only and
  refusal-plus-route messages would test it.
- Codex prefix rules cannot express an exact command; `make check` rendered for
  Codex also matches `make check other-goal`. A strict wrapper, as
  `tools/make` already does for other activities, would close that.
- Whether project-level Codex rule files load depends on the Codex config layer
  in use; `tools/allowlist.py` only prints them.
