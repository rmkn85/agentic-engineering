# Contributing

Contributions should improve the engineering discipline around software-development agents while preserving the requested task and quality bar.

Prefer concise, evidence-backed mechanisms and decision rules over broad collections of tips. Generalize private/project-specific lessons before publishing them.

## Place knowledge before polishing it

Do not automatically add new guidance to `AGENTS.md`, the global template, or a frequently loaded skill.

Ask where the information belongs:

- mechanical constraint -> script/config/test/hook;
- nearly universal execution invariant -> concise always-loaded guidance;
- path/task-specific rule -> scoped instruction;
- reusable occasional procedure -> skill/on-demand doc;
- external research, rationale, competing ideas, provenance -> `references/`.

For methodology changes, include the problem, mechanism, expected tradeoff, scope, evidence level, and how the claim could be measured or challenged. If the change affects persistent instructions, use or extend the behavioral cases in [`experiments/instruction-context-adherence.md`](experiments/instruction-context-adherence.md) when the tradeoff is material.

Preserve useful research depth in `references/` instead of bloating runtime guidance or deleting the evidence that led to a decision.

## Public-corpus privacy

Review the complete tracked text corpus, including historical `references/`, before publishing. Remove personal environment identifiers and copied configuration such as personal usernames or account URLs unrelated to public project/source identity, host or runner names, private addresses, workstation paths, hardware/OS/driver inventories, and machine-specific settings. Use placeholders or capability statements instead.

Keep facts that are necessary to reproduce or qualify a claim: supported product/platform families, required dependency versions, execution capabilities, and whether a result used an unidentified or fallback renderer. If exact environment data is necessary for a benchmark, place the minimum non-identifying data in its scoped evidence artifact and explain why it affects interpretation. Do not publish a raw host inventory.

An exact scan can catch obvious residues before semantic review:

```bash
git grep -nE '(/home/|/Users/|[A-Z]:\\Users\\|[[:alnum:]_.%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}|git@|ssh://|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.|10\.[0-9]+\.[0-9]+\.[0-9]+|([[:xdigit:]]{2}:){5}[[:xdigit:]]{2})' -- ':!CONTRIBUTING.md'
```

A clean scan is not proof of privacy: also inspect prose for named machines, account-owned links unrelated to public project/source identity, distinctive hardware, personal configuration keys, and first-person workstation history.
