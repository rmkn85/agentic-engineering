# One repository task contract

Use this opt-in contract when adopting shared task views. Repository-owned records remain authoritative; the tool adds no registry, queue, activation policy or write API. Preserve stronger project qualification rules and existing extensions during [incremental migration](standards-migration.md). A task marked done does not establish release acceptance.

## Canonical layout

- `work/tasks/<ID>.json`: complete canonical task record, including project extensions and history.
- `work/frontier.json`: explicit ordered active view. It need not contain every task.
- `work/NOW.md`: generated summary, never a second source of task state.
- `work/README.md`: concise router to these sources and the common commands.

The [task schema](../../schemas/axioms-task-v1.schema.json) requires `schema: axioms-task/v1`, `id`, `title`, `status`, `outcome`, `depends`, `acceptance`, `evidence`, and `current` (`summary`, `nextAction`, `blockers`). Status is `planned`, `in-progress`, `blocked`, `done` or `cancelled`. Acceptance and evidence are arrays of strings. Blockers are strings or project-owned objects; rich objects retain their sources, next actions and exit criteria on detail. Strings and objects with an open, unspecified or unknown disposition are active blockers. Objects explicitly marked `resolved` or `superseded` remain visible as retained blocker records but do not prevent readiness. The overview exposes the active blocker count without discarding those records. Optional fields such as area, milestone, modules, specifications, edit boundaries, timestamps and history remain project-owned. Unknown fields are preserved because the generic tool never rewrites task/frontier records.

IDs use letters, digits, dots, underscores and hyphens, beginning with a letter or digit, for example `RUN-001` or `S4.2`. Task references are local IDs or `owner/repository#ID`. Use `completedAt` for actual completion and `updatedAt` for a known update (ISO 8601 date or timestamp). Without completion time, the UI explicitly says “Completion time unknown” and labels the file's source update time. It never calls that timestamp completion evidence.

The [frontier schema](../../schemas/axioms-frontier-v1.schema.json) requires `schema: axioms-frontier/v1`, `repository: owner/name`, `objective`, `mode: product|maintenance`, and ordered task-reference arrays `product`, `maintenance`, `parallel`. Optional `lifecycle: retired` explicitly separates retired work. No mode or status change automatically activates work. Existing project extensions remain valid.

## Common commands

Python 3.9+ and its standard library are sufficient. Vendor the reviewed **exact** `tools/project_work.py` file and retain its upstream commit in the adopter's existing provenance record. There is no sibling repository, package manager, server build or network dependency.

```sh
python3 tools/project_work.py --root . validate
python3 tools/project_work.py --root . build
python3 tools/project_work.py --root . list --status in-progress --json
python3 tools/project_work.py --root . show RUN-001 --json
python3 tools/project_work.py serve --workspace /path/to/workspace --port 8765
```

`--root` also works after the command. `validate`, `build`, `list` and `show` accept `--workspace` to resolve foreign references against available immediate Git projects. Missing local dependencies and frontier tasks are errors. Unavailable foreign repositories are reported as unavailable; they never satisfy prerequisites. Readiness requires a planned task, active lifecycle, valid local inputs, no active blockers, and completed dependencies including their transitive prerequisites. Cycles, missing references and unavailable repositories cannot make a task ready. Queue position is separate from readiness. This tool does not infer ownership, authorize execution or replace product acceptance.

`build` atomically updates `NOW.md` only when its deterministic content changes. It does not edit task records or frontier. `list` and the UI default to the explicit current frontier union, with `queued` on each summary. Use `list --scope all` or the UI “All records” filter to inspect records outside that queue without reclassifying their statuses. Outside records are labeled “Outside current queue” and cannot become ready merely from a planned status. `list` limits output to 100 summaries; use `--limit` and `--offset` for pagination. `show` includes acceptance, evidence and full current blockers; project history and checkpoints stay out of both payloads. Inputs larger than 4 MiB are rejected. The overview includes at most 100 task summaries per page, prioritizing active work and ordered next tasks before other records.

## Read-only local view

`serve` binds only `127.0.0.1`. Open the printed URL in a browser. Stop with Ctrl+C when the local view is no longer needed; it leaves no generated caches or files. The owning session controls its lifetime.

Discovery considers only immediate, nonhidden, nonsymlink Git project directories containing `work/frontier.json`. It does not recursively scan dependency directories or worktrees. Add an excluded or retired repository deliberately with repeatable `--repo /path/to/project`. Explicit repositories retain their declared lifecycle; adding one does not reactivate it.

The view defaults to current queued work and filters by work scope, repository, status and search; shows in-progress/blocked work, ordered next work, done/recent updates and retired work; and offers full task detail. It polls every three seconds and compares source-content identity before changing the display. Input filters survive refresh. No build or canonical write occurs during polling. Errors retain the previous successful view and display a failure message. Server responses expose only `/`, `/api/overview` and `/api/task`; no directory or source-file browser exists. API queries use `scope` (`queued` or `all`), `repository`, `status`, `search`, `offset`, `limit` for overview, and `repository`, `id` for detail. GET and HEAD are read-only; mutations are rejected. Cross-origin requests receive no CORS permission and foreign Host headers are rejected. Untrusted task text is rendered with `textContent`.

The native test suite exercises real HTTP requests, changed inputs, filtering, detail, pagination, traversal/write rejection and core dependency defects. Semantic HTML, labeled native controls, focus restoration, a polite change announcement and responsive layout provide the intended accessible path. Browser-rendered visual, keyboard, assistive-technology and human usability acceptance still require a real browser trial; source/HTTP tests do not prove those properties.

## Router template

Copy this small router into an adopter's `work/README.md`, adjusting only the local tool location and preserving project qualification links:

```markdown
# Work

Canonical records: [tasks](tasks/) · [ordered frontier](frontier.json).
Current summary: [NOW](NOW.md), generated from those records.

Use `python3 tools/project_work.py --root . validate` to check the common contract,
`build` to update NOW, `list` for summaries, and `show ID` for task detail.
Use `serve --workspace /path/to/workspace` for the read-only local view.
Run commands from the repository root. Keep project acceptance and release gates
with their existing owners; completed task counts do not establish release acceptance.
```
