# Changelog

## Unreleased

- **The tool kind.** A third kind of repo, for one job done for other repos with no research in it:
  `TOOL.toml` with a `job` in place of a question, a `version`, and `[[consumers]]` naming what each
  dependent repo `uses`. `scaffold new tool <name> --job "..."` creates one. `check` fails a tool that
  holds research (a question, `[corpus]`, `RESEARCH.md`, `EXPERIMENTS.md`, `experiments/`), whose version
  differs across `TOOL.toml`, `pyproject.toml`, `CITATION.cff` and `CHANGELOG.md`, or whose consumers
  don't say what they use. Modelled on the `TOOL.toml` an existing tool repo already used; PROTOCOL.md § 7.
- **`scaffold status` and `scaffold update`.** `status` gives one line per repo: kind, stage, scaffold
  release, CI ref, check result and pending update. `update` brings a repo's scaffold-owned files (the CI
  workflow, `Makefile`, `shared/workbench.py`) up to this release. It replaces only files nobody edited,
  known from the new `.scaffold.lock` that `new` writes, or by matching what an earlier release wrote. In
  an edited workflow it moves only the scaffold `ref:`; other edited files are kept unless `--adopt`ed. A
  dry run unless `--apply`; refuses to overwrite uncommitted work; never commits. PROTOCOL.md § 12.
- Studies and sims list the tools they use under `[[tools]]`, and `check` fails a tool pinned to a branch.
- PROTOCOL.md sections from Preregistration on are renumbered by one (Preregistration is now § 8).
- The built-in TOML parser (Python < 3.11) reads arrays that span lines, and decodes non-ASCII strings
  correctly; before, `"µV"` came back garbled.

## v0.2.0 (2026-09-29)

- **No default profile.** `scaffold new` takes `--profile NAME` or `$SCAFFOLD_PROFILE`, and fails with the
  list of profiles if neither is set. Before, it silently used `polarizetech`.
- **Visibility is never defaulted.** New manifests say `visibility = "undecided"` unless `--visibility
  public|private` is given, and `scaffold check` fails on `undecided`. Before, the template wrote
  `"private"` with today's date, which passed `check` without anyone deciding.
- Generated study and sim CI checks out `v0.2.0`.

## v0.1.0 (2026-09-27)

First release.

- The study protocol, the adoption guide, study/sim/app templates, and `scaffold` (`new`, `promote-sim`,
  `check`, `profiles`), with the `example` and `polarizetech` profiles.
- Generated study and sim CI checks out this release (`v0.1.0`) rather than `main`.
