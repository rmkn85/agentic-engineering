.DEFAULT_GOAL := help
.PHONY: help check contributor-trial
help:
	@printf '%s\n' 'Read AGENTS.md for scope and privacy.' 'make check: offline contributor tool regression suite; Python 3.9+ and Git.' 'make contributor-trial: run make check from cold/stale disposable clones of committed HEAD.'
check:
	@python3 -m unittest discover -s tools/tests -v
contributor-trial:
	@python3 tools/check-fresh.py --timeout 120 -- make check
