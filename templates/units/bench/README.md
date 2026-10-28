# Bench sim: {{slug}}

{{question}}

A **bench sim** of {{name}} (TOOL_VERSIONING.md §1b): a sim in the tool's `sims/` that runs like part of the
test suite, against reference implementations in other repos pinned by tag, and passes or fails against
tolerances the owner chose before scoring. The tolerances are its preregistration: not meeting them is a
failure of the tool. It has no claim and no `preregistrations/` folder, and nothing here is a research finding.

| File | What it holds |
|---|---|
| `SCOPE.toml` | `kind = "bench"`, what it compares, and each reference under `[[references]]`: repo, tag, commit, subdirectory, licence, how it runs |
| `pyproject.toml` | the sim's own environment; each `runs = "python"` reference pinned at its tag |
| `tolerances.toml` | the owner's bounds, decided before scoring |
| `run.py` | checks the pins and tolerances, scores the cases, writes `results/<tool version>.json` |
| `results/` | one result per tool version; committed |

It is not run automatically. Run it when tagging a new version, from the tool's root with `make sims`, or
here:

    uv run python run.py --verify   # pins and tolerances only
    uv run pytest                   # the sim, as a test

A reference whose licence the tool can't take on (GPL code in an MIT tool) is `runs = "process"`: fetched at
its pinned commit into `.references/` (ignored), run as a separate program, never imported, linked or copied
into the repo.
