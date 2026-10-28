# `make check` runs exactly what CI runs.
SCAFFOLD ?= scaffold

.PHONY: check sims
check:
	$(SCAFFOLD) check .
	@if [ -d tests ]; then uv run pytest -q tests; fi

# Every bench sim (sims/<slug>/ with kind = "bench", TOOL_VERSIONING.md §1b), each in its own environment,
# against its pinned references. Not run by CI: run it when tagging a new version, and commit each sim's
# results/<version>.json.
sims:
	@status=0; for s in sims/*/; do \
	  grep -qs '^kind = "bench"' "$$s/SCOPE.toml" || continue; \
	  echo "sim $$s"; (cd "$$s" && uv run pytest -q) || status=1; \
	done; exit $$status
