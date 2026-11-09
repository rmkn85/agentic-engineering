# Failure evidence used before implementation review

Baseline: `4cdeefd11dd415512d691f4bf5a6197132141123`.

The existing findings ledger contains R5-07, declined on 2026-11-08: a goal
recorded as met remains met after source regression. Its rationale treated
trusting the last finish verdict as the alternative to rerunning checks in the
audit. The missing alternative was input-bound evidence invalidation without
executing acceptance. That distinction is the reason to reopen the finding;
the prior disposition must remain in history.

The earlier ordinary finish route compared goal text within a session. It did
not bind the full acceptance meaning across sessions, so removing a failing
acceptance item while retaining goal wording could conceal unfinished work.
Green internal checks could therefore coexist with an unresolved consumer
outcome. A source-only gate cannot determine acceptance completeness without
recovering original intent and independently challenging the frame.

Reflection fields previously explained why a task stopped. An explanation alone
did not execute a proposed correction or establish its effect. Likewise a
configured host hook did not establish native discovery, trust or invocation.
These distinctions define what the new tests and independent review must assess.

This file is a public, domain-neutral account of repository-local failures.
It contains no private project transcripts or proprietary source.
