# Changelog

## v0.5.1 (2026-09-30)

- **Adopted repos stay adopted.** `.scaffold.lock` records `"adopted": true` for a repo that took up the scaffold
  rather than being made by it, and `update` never adds a missing file to such a repo unasked. Before, a lock
  written by an adopting `update` made the next `update` treat the repo as scaffold-made and add its CI and
  `Makefile`.

## v0.5.0 (2026-09-30)

- Needs adaptive-preregistration v0.5.0 or later, whose `tool-scope` applies to tool repositories.
- Generated CI checks out `v0.5.0`.
- **Tools are scoped.** `new tool` installs the profile's `[prereg] tool_modules` (`tool-scope`) in place of its
  preregistration modules, so a tool's claim, features and every scientific feature's evidence and decision are
  settled with the person first (`SCOPE.toml` at the root; kit `tool-scope` now applies to tool repositories).
  `check` warns while a scoped tool has no `SCOPE.toml`.

## v0.4.0 (2026-09-30)

- Generated CI checks out `v0.4.0`; `update` moves existing repos' CI to it, and `UPGRADING.md` says what else to do.
- **Repos notice new releases.** `UPGRADING.md` says, per release, what `scaffold update` does and what a
  session does by hand. `scaffold version` compares a repo's recorded release with the current one (and with
  GitHub's latest) and prints the steps in between; a session hook in `.claude/settings.json` runs it when a
  Claude Code session starts, beside the kit's hooks, and the `AGENTS.md` section tells Codex to. `update` adds
  the hook, and prints the upgrade notes with its plan.
- **Work types replace `experiments/`.** A study is built from apps, sims, datasets, calculators and tools
  (PROTOCOL.md § 5), each with its own folder, entry requirement and way of writing back to research.
  `scaffold new dataset` creates `datasets/<slug>/` (a dataset-fetch reference pinned to a version, selection
  criteria, `analysis/`); `scaffold new calculator` creates `calculators/<slug>/` (`CALCULATOR.md`,
  `reference.csv`). Preregistrations live in the unit they test, `<unit>/preregistrations/<EID>/`, listed in
  `EXPERIMENTS.md`; sims use `preregistrations/` too. `check` enforces a selected dataset's pinned reference
  and licence, and calculator reference values from PROBE on; `experiments/`, `data/manifest.json` and
  unregistered unit folders are warnings. PROTOCOL.md sections from Apps on are renumbered.
- **The agents moved to their own repo**, [scientific-research-agents](https://github.com/polarizetech/scientific-research-agents),
  included as a submodule at `agents/` pinned to `v0.1.1`: the briefs, the coordination protocol, discipline
  briefs, prices and the usage tool. `scaffold usage` passes through to its `bin/agents usage`. The
  `new-study` skill moved to `skills/`. Clone with `--recurse-submodules`.
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
