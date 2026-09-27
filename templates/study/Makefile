# `make check` runs exactly what CI runs.
SCAFFOLD ?= scaffold

.PHONY: check
check:
	$(SCAFFOLD) check .
	@if [ -d tests ]; then uv run pytest -q; fi
