# Changelog

## Unreleased

- **Agent coordination.** [`agents/COORDINATION.md`](agents/COORDINATION.md): one lead delegates, agents pass
  150-word handoffs instead of transcripts, parallel work only for independent tasks (at most three, each in
  its own worktree), agent teams only for tight back-and-forth, and the science gate never skipped.
- **Mathematician agent.** Equations, constants, units and valid ranges; records each piece of maths with its
  source (BioNumbers style) and specifies calculators with reference values, handing code to the engineer.
- **Model routing.** Each agent's frontmatter now sets its starting `model` and `effort` (a new `scout` on
  Haiku; the others on Sonnet), overridable in a profile's `[agents.routing]`; the lead escalates a task on a
  clear signal.
- **Codex.** A marked scaffold section in `AGENTS.md` gives every assistant the roles, the coordination rules
  and Codex routing from the profile's `[agents.codex]`. `update` maintains it and leaves the rest of the file
  alone.
- **`scaffold usage`.** Tokens and API-equivalent cost per repo and model from Claude Code's and Codex's local
  logs, a monthly projection, and Codex's plan rate-limit windows. Prices are in `agents/prices.toml`. Each
  response is counted once: Claude Code writes one response as several transcript lines.

## v0.3.0 (2026-09-30)

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
- **Specialist agents.** Every new repo gets Claude Code subagents in `.claude/agents/`:
  `computational-engineer`, `designer`, `frontend-developer`, `researcher`, `analyst` and `science-writer`
  (a sim has no UI agents), plus `.claude/disciplines.md`. A profile's new `[agents]` table chooses the
  discipline briefs (`agents/disciplines/`) and the code conventions written into the agents. The agents
  are scaffold-owned, so `update` keeps them current; `--adopt` now takes a folder, to add them to an
  existing repo. Generated `CLAUDE.md` says which agent takes which task, and in what order.
- Studies and sims list the tools they use under `[[tools]]`, and `check` fails a tool pinned to a branch.
- PROTOCOL.md sections from Preregistration on are renumbered by one (Preregistration is now § 8).
- The built-in TOML parser (Python < 3.11) reads arrays that span lines, and decodes non-ASCII strings
  correctly; before, `"µV"` came back garbled.
- Generated CI checks out `v0.3.0`, and `update` moves existing repos' CI to it.

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
