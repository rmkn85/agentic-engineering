# Repository-only contributor contract

The acceptance target is a capable newcomer given only a repository location and a small authorized change. The newcomer may be a junior engineer or a low-cost agent. Fresh, stale and interrupted working copies must have a documented, tested path to the same accepted result. Preparation, source synchronization, validation and delivery are engineering infrastructure, not puzzles to solve again with model inference.

This extends the existing [execution corpus](../agent-corpus/README.md) and [local overlays](overlays.md). It does not replace a project's task authority, branching policy, package manager, CI or publisher. No new task database, agent orchestrator, mandatory central checkout, automatic policy download, or personal IDE configuration is required.

## Boundary and prerequisite

Repository automation starts after the host can read the repository and run its declared base tooling. It cannot manufacture account consent, network access, credentials, licensed data, physical hardware or an authorized deployment destination. Provision these once through the host's supported setup. Classify a missing prerequisite once with its owner and retry condition; do not make every task rediscover it or broaden permissions to work around it.

Reading a remote `AGENTS.md` through an authorized connector is a valid ingress when no checkout exists. Use a normal clone into a new, explicit location when shell/Git access is available. A connector-only editor uses the existing CI execution route; it must not claim local execution.

## The thin repository entry

Keep one discoverable root entry, normally `AGENTS.md`, with a short route to an existing or new `CONTRIBUTOR-ENTRY.md`. That page supplies the actual native commands and owners, not a generic checklist that makes the newcomer invent commands:

| Need | Repository-owned binding |
| --- | --- |
| Start/resume | Current instructions, task authority and small continuation record |
| Source safety | Expected repository, selected remote, permitted current branch and synchronization route |
| Preparation | Idempotent source-only bootstrap and selected locked environment; explicit expensive/real-resource opt-ins |
| Fast validation | Exact native command used during local work |
| Integration | Installed/packed consumer test and exact sibling/fixture source identities where relevant |
| Delivery | Existing CI workflow and publisher, artifact identity and deployed-identity verification |
| Recovery | Durable checkpoint/evidence location and next command; no chat dependency |

Do not add a second entry document where an existing one already fulfills this contract. Bind the existing document instead. Keep current task progress out of permanent instructions.

## Mechanical source guard

`tools/agent-checkout.py` is a small optional standard-library helper for one owned checkout. Copy it locally when useful; it has no upstream runtime dependency.

```sh
# Read-only local inspection; cached refs deliberately do not prove freshness.
python3 tools/agent-checkout.py --expect example/project --branch main
# Refresh the exact branch, but do not move the working copy.
python3 tools/agent-checkout.py --expect example/project --branch main --fetch
# Only after this checkout/branch is authorized for the task:
python3 tools/agent-checkout.py --expect example/project --branch main --ff-only
# CI validates its exact immutable candidate, including detached HEAD.
python3 tools/agent-checkout.py --expect example/project --revision "$GITHUB_SHA"
```

Adapt paths and branch to the local policy. `main` is an example, not a universal requirement. Exit 0 means the stated **checkout-only** claim passed, not environment readiness, product acceptance or deployment. Exit 3 contains a bounded JSON blocker. The guard never switches branches, commits, pushes, resets, installs software or changes permissions. It checks all configured push destinations as well as fetch identity. Git configuration, transport rewrites and hooks remain trusted host concerns; this is a sanity guard, not a security sandbox or cross-process ownership lock.

Unpublished commits, dirty work, unfinished Git operations and divergence must be preserved and reconciled through the existing ownership policy. Do not convert every problem into `pull`, a forced update or deletion. For isolated task branches use the authorized branch and normal integration route. Read the current instructions again if synchronization changes them.

## A native delivery chain, not an agent-operated release console

Preparation and tests should be callable independently of the IDE. Use the repository's existing Make/npm/uv/CMake/etc. commands and supported cloud setup hooks. Do not require the entire multi-repository environment for a one-owner change. Source access, package installation, small fixtures, private data, production startup and deployment are separate operations.

Use one authoritative CI chain. Its local equivalents run the same scripts with the same locks, source inputs and acceptance criteria. Cache by inputs that affect validity; record and invalidate stale results. Reuse the accepted artifact for downstream checks and promotion instead of rebuilding a different candidate. An unrelated documentation successor is not a new tested runtime identity.

A local or self-hosted fallback needs a pre-authorized runner and the same candidate checks. A queued job, exhausted allowance, unavailable runner or skipped check is not success. Do not dynamically reroute untrusted code to a personal account or grant privileges to make a fallback work. Changes to runner eligibility, secrets, branch protection and publication policy require their normal authority. For a ready-to-adopt pattern that keeps untrusted pull requests hosted while routing trusted main to a maintained self-hosted runner, plus artifact-quota and rerun recovery, use [CI and delivery resilience](../execution/ci-delivery-resilience.md).

A source push, successful tests, accepted artifact, successful publisher and verified served bytes are different claims. Keep those identities connected in existing evidence. Libraries prove installed consumers, data repositories prove usable fixtures/contracts, documentation proves navigation and substantive reader use, and hardware projects distinguish replay from physical-device acceptance. Do not invent a deployment for a repository that does not ship a service or application.

## Capability-based adoption

Every maintained repository gets source safety, bounded context, interruption recovery, evidence integrity and privacy. Apply additional lessons by actual process needs, not by whether the repository previously suffered that incident:

| Process property | Additional requirement |
| --- | --- |
| Multiple writers | Explicit write boundaries, independent preparation and one integration owner; classify collisions |
| Multiple repositories | Exact source vector, scoped environments and installed-provider/consumer tests |
| Large/private data or devices | Small deterministic fixtures/replay; explicit real-resource gates; no silent synthetic fallback |
| Public artifacts | Allowlisted output, retained notices, no private source/logs/data and exact served identity |
| Expensive CI | Early discriminating checks, nonduplicated workflows, valid cache reuse and bounded fallback; separate test verdicts from evidence transport |
| Multiple hosts/IDEs | Thin native adapters; verify instruction availability, delivery and actual application separately |
| Repeated diagnostics | Small outcome first, durable structured detail and raw evidence reachable on demand |

First-party source, publishing-only repositories, mirrors, third-party forks and reference clones are different roles. Inventory all of them; do not bulk-rewrite upstream/reference repositories as if they were product owners.

## Selective local inheritance

Maintain reusable mechanisms here. Adopters copy a reviewed subset and its required resources into their repository, preserving source structure or deliberately rewriting links. Record upstream commit, source-to-local mapping, hashes and intentional adaptations in one small provenance file. This is not a task ledger.

Ordinary work needs no network fetch of this knowledge base. Upgrades are explicit reviewed changes. Compare old upstream, new upstream and local content; refuse unexpected overwrites. Do not fail a build because a newer upstream version exists. Keep organization/product additions outside exact shared copies. Promote a useful local improvement back upstream after anonymization; preserve private evidence with its original owner.

Codex, Cursor, Copilot and JetBrains do not necessarily deliver the same files to every execution surface. Native adapters route to the local entry; they are not independent handbooks. Changing a file is not proof an already-running host reloaded it. Test workspace-root, repository-root and worker entry separately.

## Acceptance, not installed-file counting

Run the same bounded feature task from: a clean cold checkout; a clean stale checkout; an interrupted checkout with owned work; a wrong branch; divergent history; no optional sibling checkout; and a cold dependency cache. Include denied network/tool access as an honest-blocker test, not a reason to weaken checks. Preserve sentinel unrelated edits in recovery cases.

For each trial record requested task, start/source identity, actual host/model setting where available, native commands, changed paths, check/candidate/artifact identities, human interventions, infrastructure retries and final user-visible result. Compare against the same acceptance bar. Measure tokens only when actual usage is available; file size and invocation counts are proxies, not savings proof.

Mechanical fixtures validate the helper, not the entire newcomer journey. A low-cost-model run, real host instruction delivery, full environment bootstrap, cross-repository integration and actual deployment each require their own executed evidence. Keep unrun layers explicitly open. Retain the simple-task negative case: do not load the research archive or every skill to edit one function.

Related: [Git write recovery](../collaboration/git-write-safety.md), [recovery skill](../../skills/recovering-interrupted-work/SKILL.md), [method improvement](../../skills/improving-execution-guidance/SKILL.md), and [anonymized lessons and source notes](../../references/portable-contributor-lessons-2026-09.md).
