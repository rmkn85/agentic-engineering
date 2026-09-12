---
name: efficient-execution
description: Execute long, repository-heavy or tool-heavy engineering tasks with minimal redundant model work, noisy context, repeated validation, and unnecessary agent fan-out while preserving the requested result and quality.
---

1. Establish the required outcome and acceptance checks; do not reduce them to save tokens.
2. Before model-driven exploration, use deterministic repo metadata/search/indexes to narrow what needs semantic inspection.
3. Keep full logs/evidence on disk and expose terse summaries to model context; inspect detailed excerpts only when needed.
4. Treat completed semantic work as cached until an input that can affect it changes. Record enough state to know what is valid or dirty.
5. Use targeted validation after local changes; perform broader validation at integration boundaries and final completion, not reflexively after every edit.
6. Preserve normal platform delegation behavior unless there is a concrete reason to intervene. Explicitly add broad fan-out only for genuinely independent work with plausible critical-path or quality benefit; explicitly cap it only when quota, rate-limit, or coordination evidence justifies the cap.
7. Prefer stable instructions/context and on-demand references. Do not repeat large task descriptions or repo summaries already available in files.
8. For repeatable work, capture `codex exec --json` metrics and compare against the applicable baseline.
