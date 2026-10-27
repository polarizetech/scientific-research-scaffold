# `make check` runs exactly what CI runs.
SCAFFOLD ?= scaffold

.PHONY: check bench
check:
	$(SCAFFOLD) check .
	@if [ -d tests ]; then uv run pytest -q tests; fi

# Every bench (benches/<slug>/, TOOL_VERSIONING.md §1b), each in its own environment, against its pinned
# references. Run it before every release and commit each bench's results/<version>.json.
bench:
	@status=0; for b in benches/*/; do \
	  [ -f "$$b/pyproject.toml" ] || continue; \
	  echo "bench $$b"; (cd "$$b" && uv run pytest -q) || status=1; \
	done; exit $$status
