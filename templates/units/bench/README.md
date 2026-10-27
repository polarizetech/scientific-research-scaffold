# Bench: {{slug}}

{{question}}

A **bench** of {{name}} (TOOL_VERSIONING.md §1b): it runs like part of the test suite, against reference
implementations in other repos pinned by tag, and passes or fails against tolerances the owner chose before
scoring. It is a test, not an experiment: no claim, no preregistrations. Nothing here is a research finding.

| File | What it holds |
|---|---|
| `SCOPE.toml` | what it compares, and each reference under `[[references]]`: repo, tag, commit, subdirectory, licence, how it runs |
| `pyproject.toml` | the bench's own environment; each `runs = "python"` reference pinned at its tag |
| `tolerances.toml` | the owner's bounds, decided before scoring |
| `run.py` | checks the pins and tolerances, scores the cases, writes `results/<tool version>.json` |
| `results/` | one result per tool version; committed |

Run it from the tool's root with `make bench`, or here:

    uv run python run.py --verify   # pins and tolerances only
    uv run pytest                   # the bench, as a test

A reference whose licence the tool can't take on (GPL code in an MIT tool) is `runs = "process"`: fetched at
its pinned commit into `.references/` (ignored), run as a separate program, never imported, linked or copied
into the repo.
