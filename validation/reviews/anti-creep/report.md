# Independent implementation review (blind, two-phase), reviewed commit on claude/audit-self-anti-creep

The change does what its goal says for the work audit but weakens the protections against an agent switching a guard off, which should block it. All checks I ran pass: make check (538 tests, 1 skipped), make audit-self (exit 0), prove_guards --only caught all 9 changed mutations; make review-check fails as expected on the 4 review-gated files this change touches.

Blocker (C5): relevant() in tools/check_review.py is now an allowlist that drops files which run or configure guards and used to need review. In a scratch clone, removing the hooks block from .claude/settings.json, multiplying the first number in configs/guidance-budget.json by ten, appending sys.exit(0) to tools/check-outcome-controls.py, and loosening tools/check_hygiene.py and tools/check-fresh.py together passed the new check_review.py (rc=0); the origin/main version flagged all five (rc=1). .codex/hooks.json and configs/allowed-activities.json are also no longer gated.

Should-fix: a product-glob override in .agent/audit.json reclassifies records as product and switches off audit-self (500 lines of validation/reviews/run.jsonl + 2 code lines: rc=1; with {"product":["validation/*"]}: rc=0; force-added, review-check still rc=0). Records outside the evidence folders (data/receipts.json, evidence.json, validation/x.ndjson) count as product.

Should-fix: an unresolvable --since ref fails open ("last 0 commits: no history", rc=0).

Minor: EVIDENCE_DATA counts product data under results/, reports/, runs/, logs/, artifacts/, snapshots/ as records (app/reports/definitions.yaml 400 lines + loader.py 100 lines: 80%, rc=1).
Minor: classing validation/mutations/ as test moves 69 of this change's 240 added lines out of records (29% vs about 57%); defensible but flattering.
Minor: docs list fewer gated surfaces than CONTROLS; neither covers hook or allowlist configuration.

Confirmed working: 85869a1..3b1ae2b reports 48% (3391 of 7113) and exits 1 where the old audit gave no direction finding; the 1-line-code + 500-record-lines commit is flagged; behaviour-heavy fixtures pass; CI runs make audit-self with full history; routine AGENTS.md, docs/, skills/, tools/repo-index.py edits pass review-check; make findings still catches a deleted referenced mutation.

C1 met. C2 met. C3 partly met (bad base passes; audit config override). C4 met. C5 not met. C6 met (71% code+tests; one receipt tied to a named failure). C7 partly met.

BEGIN FINDINGS
{"severity": "blocker", "target": "tools/check_review.py:21", "problem": "The new allow-list drops review for files that run or configure guards (.claude/settings.json hooks, .codex/hooks.json, configs/guidance-budget.json, configs/allowed-activities.json, tools/check-outcome-controls.py, tools/check_hygiene.py, tools/check-fresh.py), so an agent can switch a guard off without independent review.", "reproduction": "Scratch clone edits to those files; new check_review.py --base HEAD rc=0; origin/main version flags all five, rc=1", "scope": "in"}
{"severity": "should-fix", "target": "tools/work_audit.py:142", "problem": "A product-glob override in .agent/audit.json reclassifies records as product and switches off audit-self, and review-check does not gate that file even when force-added.", "reproduction": "500 lines validation/reviews/run.jsonl + 2 code lines: rc=1; add .agent/audit.json {\"product\":[\"validation/*\"]}: rc=0; git add -f; check_review rc=0", "scope": "in"}
{"severity": "should-fix", "target": "tools/work_audit.py:155", "problem": "An unresolvable --since ref fails open: git errors become empty output, the audit sees no commits and exits 0.", "reproduction": "work_audit.py --since nonexistent-ref --fail-on loop,records-heavy -> 'last 0 commits: no history' rc=0", "scope": "in"}
{"severity": "minor", "target": "tools/work_audit.py:77", "problem": "EVIDENCE_DATA counts product data under results/, reports/, runs/, logs/, artifacts/ or snapshots/ folders as records, so ordinary feature work fails the records-heavy gate.", "reproduction": "app/reports/definitions.yaml (400) + app/reports/loader.py (100): 80% records, rc=1; kind('src/results/schema.json') -> records", "scope": "in"}
{"severity": "minor", "target": "tools/work_audit.py:68", "problem": "Classing validation/mutations/ as test moves 69 of this change's own 240 added lines out of records; with them as records the change measures about 57% records/process.", "reproduction": "git diff --numstat origin/main...HEAD classified with work_audit.kind -> test 120, records 63, product 51, process 6", "scope": "in"}
{"severity": "minor", "target": "docs/execution/executable-reflection.md:70", "problem": "The documented review-trigger rule omits tools that check_review.py gates, and neither covers hook or allow-list configuration.", "reproduction": "Compared docs sentence with CONTROLS in tools/check_review.py:21", "scope": "in"}
END FINDINGS

## Follow-up review of a38032b
Blocker fixed: check_review flags all 7 guard files (.claude/settings.json, .codex/hooks.json, configs/allowed-activities.json, configs/guidance-budget.json, tools/check-fresh.py, tools/check-outcome-controls.py, tools/check_hygiene.py), rc=1. .agent/audit.json override fixed: force-added file needs review, rc=1. --since bad ref fixed: fails closed, rc=1 ('HEAD~1 --' and '--all' also rejected; --since HEAD passes as an empty change). Evidence-data false positive partly fixed: app/results and app/logs now product; app/reports/definitions.yaml still records via the pre-existing RECORDS pattern (reports/, research/, docs/), which this change makes merge-blocking. Moving records to other folder names still evades, minor. Tests, 5/5 mutations, findings --strict and audit-self pass.
Additional minor finding: tools/work_audit.py:61 older RECORDS pattern counts product data under reports/, research/ or docs/ as records.
VERDICT: accepted
