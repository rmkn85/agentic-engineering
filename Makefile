.DEFAULT_GOAL := help
.PHONY: help check contributor-trial external-report external-smoke
help:
	@printf '%s\n' 'Read AGENTS.md for scope and privacy.' 'make check: offline contributor tool regression suite; Python 3.9+ and Git.' 'make contributor-trial: run make check from cold/stale disposable clones of committed HEAD.' 'make external-report: show instrumented external-practice use in this checkout.' 'make external-smoke: network-enabled pinned-upstream fixture; installs into a private cache.'
check:
	@python3 -m unittest discover -s tools/tests -v
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
