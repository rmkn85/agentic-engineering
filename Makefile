.DEFAULT_GOAL := help
.PHONY: help check control-trial contributor-trial external-report external-smoke guidance-budget guidance-delta finish-check hygiene
help:
	@printf '%s\n' 'Read AGENTS.md for scope and privacy.' 'make check: offline contributor regressions and native control integration; Python 3.9+ and Git.' 'make finish-check: refuse to finish while .agent/goal.json is unmet.' 'make hygiene: fail on merged-but-kept branches, extra worktrees, dated plan/handoff trees or tracked scratch.' 'make guidance-delta: fail when runtime prose grows since BASE (default origin/main) without a mechanism.' 'make control-trial: exercise outcome, runtime, recovery and evaluation command routes.' 'make contributor-trial: run make check from cold/stale disposable clones of committed HEAD.' 'make external-report: show instrumented external-practice use in this checkout.' 'make external-smoke: network-enabled pinned-upstream fixture; installs into a private cache.'
check:
	@python3 -m unittest discover -s tools/tests -v
	@python3 tools/check-outcome-controls.py
	@python3 tools/check_guidance_budget.py
control-trial:
	@python3 tools/check-outcome-controls.py
guidance-budget:
	@python3 tools/check_guidance_budget.py
guidance-delta:
	@python3 tools/check_guidance_budget.py --base $(or $(BASE),origin/main)
finish-check:
	@python3 tools/finish_check.py
hygiene:
	@python3 tools/check_hygiene.py --strict $(if $(BASE),--base $(BASE),)
contributor-trial:
	@python3 tools/check-fresh.py --timeout 120 -- make check
external-report:
	@python3 tools/external_practices.py report
external-smoke:
	@python3 tools/check-external-practices.py

.PHONY: context7-cache-plan context7-cache-apply
context7-cache-plan:
	@./tools/make context7-cache-plan SPEC_FILE=$(SPEC_FILE)
context7-cache-apply:
	@./tools/make context7-cache-apply PLAN_SHA256=$(PLAN_SHA256)

.PHONY: context7-cache-probe
context7-cache-probe:
	@./tools/make context7-cache-probe CONFIG_SHA256=$(CONFIG_SHA256)
