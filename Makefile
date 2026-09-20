.DEFAULT_GOAL := help
.PHONY: help check
help:
	@printf '%s\n' 'Read AGENTS.md for scope and privacy.' 'make check: offline contributor tool regression suite; Python 3.9+ and Git.'
check:
	@python3 -m unittest discover -s tools/tests -v
