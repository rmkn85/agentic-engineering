# Trunk-based development with parallel agents (2026-11)

Rationale for the short-lived worktree rule in
[Git write safety](../docs/collaboration/git-write-safety.md#parallel-worktrees-and-pr-coordination)
and the age and count limits in `tools/check_hygiene.py` (`make hygiene`, and
the `hygiene` findings of `tools/work_audit.py`).

## Failure addressed

Parallel coding agents each created a worktree and branch per task or per
iteration, then left them in place after the work landed, stalled or was
superseded. In one multi-repository workspace this produced well over a
hundred registered worktrees, most of them clean and already merged, which
filled the disk and hid the few lanes with unique unpublished work. The
existing check flagged every extra worktree with the same message, whether it
was an hour-old active lane or a month-old leftover. A report that is always
non-empty gets ignored.

## Mechanism

1. Keep one stable `main` in the main checkout. Work on a short branch there
   by default.
2. Create a worktree only when two writers must edit the same repository at
   the same time. Reuse an owned worktree before creating another.
3. Land the branch on `main` the same day, then remove the worktree and delete
   the branch. Split larger work into steps that each land, keeping the old
   path working (feature flag or branch by abstraction) instead of parking it
   on a branch.
4. `make hygiene` fails on a worktree older than 24 hours or on more than
   three at once. A younger worktree within the cap is active work and is not
   reported. Merged branches that were not deleted are still reported.

Age is the modification time of the worktree's `commondir` file in its Git
administrative directory. Git writes that file when it creates the worktree and
does not rewrite it on commit, so the mtime approximates creation time. A
`git worktree repair` or a copied repository can reset it; then the age is
understated and the count limit still applies.

## Sources and evidence status

- **Measured result (correlational), DORA.** The DORA capability page on
  trunk-based development (dora.dev, read 2026-11-08), drawing on the 2016 and
  2017 State of DevOps data, lists for higher performers: three or fewer active
  branches, merges to trunk at least once a day, and no code freezes or
  integration phases. It notes that branches in trunk-based development
  "typically last no more than a few hours". This is survey correlation with
  delivery performance, not a controlled experiment, and it measured human
  teams. The limit of three comes from this finding.
- **Secondary attribution, not checked against the book.** Several secondary
  sources attribute to *Accelerate* (Forsgren, Humble, Kim, 2018, around p. 98)
  the wording "fewer than three active branches" with branch lifetimes under a
  day. The book text was not read here. Rely on the DORA page above instead.
- **Established practice, Martin Fowler.** "Patterns for Managing Source Code
  Branches" (martinfowler.com, 2020) defines continuous integration as
  integrating a healthy commit "usually less than a day's work", with everyone
  committing to the mainline every day. It argues that frequency reduces merge
  difficulty and that long branches deter refactoring. Fowler cites the State
  of DevOps finding on branch lifetimes under a day.
- **Established practice, Paul Hammant.** trunkbaseddevelopment.com (read
  2026-11-08): one shared trunk; short-lived feature branches from a single
  developer workstation (solo, pair or mob) that "should only last a couple of
  days" and are deleted after integration; feature flags and branch by
  abstraction for longer changes; release branches cut late and deleted. The
  site's "couple of days" ceiling is looser than DORA's daily merge; this
  change uses the stricter same-day bound because agents produce small
  changes quickly and the observed failure was accumulation.
- **Documented practice at scale, Google.** Potvin and Levenberg, "Why Google
  stores billions of lines of code in a single repository", *Communications
  of the ACM* 59(7), 2016: most development happens at the head of one
  repository with changes applied in a single serial order, which avoids
  merging long-lived branches. Only the abstract and secondary summaries were
  read here; the section on release branches was not checked.
- **Documented vendor behaviour, Claude Code (review by 2027-05).** The
  "Run parallel sessions with worktrees" documentation (code.claude.com, read
  2026-11-08) describes one worktree per parallel session or subagent,
  automatic removal of clean worktrees on exit, a periodic sweep of subagent
  and background-session worktrees older than `cleanupPeriodDays` that keeps
  any with changes or unpushed commits, and no cleanup for non-interactive
  `-p` runs. Host cleanup is therefore partial; worktrees made with
  `git worktree add` or by headless runs remain the user's to remove.
- **Practitioner opinion, user lead.** Gabriel Anhaia, "Agents make
  trunk-based development cheap: one task, one branch, landed same day"
  (dev.to, 2026; the author builds an IDE product and says so). One branch
  per task cut from trunk, landed the same day; narrow and rerun a task whose
  diff is too large to review; remove the worktree and branch after merge;
  list branches by last commit to find ones that missed the daily merge. He
  notes that three parallel agents already reach DORA's branch limit. The
  rules are his recommendation, reasoned from DORA and other data, not a
  study of agent workflows.
- **Field report, user lead.** Daniel Vacic, "To branch or not to branch"
  (The Growth Project, 2026-11-05): with several agents on separate branches
  and worktrees, worktree copies grew to tens of gigabytes with unclear
  ownership, a stale build from the wrong copy was deployed, unmerged
  half-finished work had to be rescued, and about 60% of test runs went to
  bringing branches up to date. Recommends trunk by default, short-lived
  per-agent workspaces from the latest trunk and a merge queue. One team's
  experience; no cap on worktree count.
- **Vendor page, not relied on.** kawacode.ai/trunk-based-development (user
  lead, undated) promotes a product for detecting overlapping edits before
  commit. It cites a patent and an illustrative scenario and gives an
  unsourced "100x faster" claim. It says nothing about worktrees.

## Cost and when not to use it

The cost is landing work in smaller steps and removing a worktree at the end
of each step instead of keeping it for the next. A long-running owner keeps its
context, not its checkout. Do not apply the age limit to release branches or
to a lane that is waiting on an external blocker and holds unique work:
preserve that work through
[resource lifecycle](../docs/execution/resource-lifecycle.md), then remove the
checkout. Pass `--max-worktree-hours` or `--max-worktrees` to `check_hygiene.py`
for a repository whose owner sets different limits.

## Verification and revision

`tools/tests/test_check_hygiene.py` shows that a fresh worktree within the cap
passes, one older than 24 hours fails, and a fourth concurrent worktree fails.
This proves the check, not adherence. Revise the limits if the check blocks
legitimate parallel work often enough that agents bypass it, or if worktree
accumulation recurs inside the limits. A useful trial: count registered
worktrees across the workspace at the end of each day for a week before and
after adoption.
