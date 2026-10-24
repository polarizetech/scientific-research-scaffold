# Changelog

## Unreleased

- **Comparison units in a tool.** A tool repo may hold `sims/<slug>/` and `datasets/<slug>/` "as long as they
  are about comparing the tool's functionality against other tools (aka preregistering predictions based on
  inputs and seeing if the run is correct - essentially treating these like an extension on the test suite)"
  (the person's wording, 2026-10-24; the prereg kit's `TOOL_VERSIONING.md` §1a). `scaffold new sim <name>
  --inside <tool> --compares "<other> <version>"` and `scaffold new dataset <name> --study <tool> --compares ...`
  create one: its `SCOPE.toml` says what it `compares`, it is registered under `[[comparisons]]` in `TOOL.toml`,
  and the tool gets a root `EXPERIMENTS.md`. `scaffold check` on a tool now allows that `EXPERIMENTS.md` and
  `preregistrations/` directly inside a comparison unit, and fails a comparison unit with no `compares`, one
  missing from `[[comparisons]]`, or `preregistrations/` anywhere else. The agent rules and templates for tools
  say the same.

## v0.11.1 (2026-10-21)

- Pins scientific-research-agents v0.8.0, including the public installer for private researcher
  extensions. Future scaffolded repositories receive the current public researcher brief; private
  specialist briefs remain in a separate checkout and are installed only into selected repositories.
- Generated CI checks out `v0.11.1`.

## v0.11.0 (2026-10-18)

- **Agent-managed impact propagation.** A study records whether hypothesis impacts are `agent-managed` or
  `person-managed`. Under the default agent-managed policy, routine mapping and stale-impact queues do not ask
  the person to repeat decisions: `scaffold link-hypothesis` records an existing unit's role and accepted element
  links, and `scaffold sync-hypothesis` marks affected units `needs-review` without changing their claims.
- **Local context for every unit.** Exploratory as well as testing units carry element IDs, accepted revisions,
  fingerprints and review state in `SCOPE.toml`. Existing unit claims remain intact: association with a broader
  study element does not silently replace a narrower accepted unit claim.
- **Cross-study routing through the corpus.** The corpus project overview is the reverse impact index. An agent
  changing a corpus claim, finding or evidence link follows its study/element references, synchronizes each
  available study, and records any unavailable checkout as pending rather than asking the person to coordinate it.
- Pins scientific-research-agents v0.6.0, whose researcher, analyst and computational-engineer briefs assign
  ownership of that propagation to the agent making the evidence, finding or implementation change.
- Generated CI checks out `v0.11.0`.

## v0.10.0 (2026-10-17)

- **Study-level hypothesis maps.** New studies require `--hypothesis` and carry the person's wording verbatim
  in `HYPOTHESIS.toml`; the question is never silently substituted. Specialist agents propose falsifiable steps
  and integrations, but each remains proposed until the person accepts its exact revision. Evidence status is
  separate from established/supported/derived/gap/exploratory basis, and every non-established accepted element
  has a real goal and falsifier rather than a placeholder.
- **Hypothesis-to-unit dependency graph.** Each app version, sim, dataset analysis and calculator maps to one
  or more accepted elements. `scaffold new ... --hypothesis-element ID` prevalidates before writing. Testing
  scopes carry accepted element provenance. Changes require a disposition bound to the exact stale revisions,
  fingerprints and corpus revision. Legacy mappings remain `unmapped` and become failures from PROBE onward.
- **Corpus project overview and local reconciliation.** `RESEARCH.md` links the canonical corpus overview and
  evidence IDs are matched exactly. The study rules use specialist profiles and the retrieval tool first.
  Offline checks compare the recorded corpus revision with a sibling corpus checkout; reconciling a new revision
  makes linked units stale for explicit review.
- Generated CI checks out `v0.10.0`.

## v0.9.2 (2026-10-14)

- **Apps are laid out as `apps/<slug>/vN/`**: one folder per app, one inside it per version, each app
  numbered from v1. `scaffold new app <slug>` gives a new slug its `v1` and an existing slug its next
  version. Before, a study had one number sequence and folders named `apps/vN-<slug>/`, which put unrelated
  apps side by side in number order and split one app's versions apart.
- **The earlier layout still passes `check`.** An `[[apps]]` entry with no `path` is looked for at
  `apps/<slug>/<version>/` and then at `apps/<version>-<slug>/`. No repo has to move anything.
- The app template's `serve.py` looks one folder further up for the design system, to match the new depth.
- Needs the preregistration kit release that reads the same layout (adaptive-preregistration, unreleased).

## v0.9.1 (2026-10-13)

- **Research questions go to the retrieval tool first.** A profile can name the organisation's literature and
  evidence search (`[retrieval]`: `server`, the MCP server's name in a session, and `repo`). When it does, the
  scaffold's section of `AGENTS.md` in every kind of repo tells every assistant to search with it before
  answering a question about science, the literature or evidence, to say so when the tool isn't available, and
  not to use it when the person says so. A profile that names none gets no such rule.
- Pins scientific-research-agents v0.3.0 (adds a local-model roles template; the coordination protocol points
  to it).
- Generated CI checks out `v0.9.1`.

## v0.9.0 (2026-10-07)

- **Exploratory units.** `scaffold new app|sim|tool|dataset|calculator ... --exploratory` creates the unit
  without a claim: it writes the unit's `SCOPE.toml` at the exploratory stage, with a build note taken from
  `--question` (or `--job`) and the date, and labels the unit's README. Sessions don't ask for a claim or an
  evidence basis in such a unit. A study or workbench can't be exploratory.
- **`check`** fails an exploratory unit that doesn't say so in its README, or that has preregistered
  experiments: it gets its claim (and `stage = "testing"`) first.
- **The claim step is one question** for every other new unit, from preregistration kit 0.9.0: the claim and
  what would count against it. The shared rules in `AGENTS.md` say so for each kind.
- Generated CI checks out `v0.9.0`.

## v0.8.1 (2026-10-06)

- **Generated CI can install private dependencies.** A repo that pins the organisation's private repos by git
  URL failed at `uv sync` in GitHub Actions (`could not read Username for 'https://github.com'`), because the
  default token reads only its own repo, and `make check` never ran. The workflow of every kind now reads an
  optional `PRIVATE_DEPS_TOKEN` secret and, when it is set, uses it for the profile's `org` on github.com.
  Without the secret, an install that fails in a repo with such pins is a warning and the scaffold check still
  runs; any other failed install still fails the job. See PROTOCOL.md § 4.
- Generated CI checks out `v0.8.1`.

## v0.8.0 (2026-10-02)

- **The workbench kind.** `WORKBENCH.toml`: one repo holding general `tools/`, `sims/` and `apps/` and one folder
  per study. `scaffold new workbench` creates one; `new study --inside <workbench>` creates a study that shares
  the repo's kit, agents, CI and licence; `new tool|sim --inside <study or workbench>` adds units to either. A
  workbench has no one stage or corpus project, may mount the corpus as a submodule, and declares its
  `private` folders, which requires a private repo. `check` on a workbench checks every study it lists.
- A study may hold its own tools (`[[tools]]` with a `path`); a tool inside a study is a unit, not a tool repo.
- A study inside a workbench carries no `visibility` of its own: the workbench decides it.
- **Adopted units.** A `[[datasets]]` or `[[calculators]]` entry with `adopted = true` predates the unit formats:
  `check` requires only that it exists, and warns that it owes its manifest when next worked on.
- Generated CI checks out `v0.8.0`.

## v0.7.0 (2026-10-01)

- Pins scientific-research-agents v0.2.0, with provider-neutral role bodies and Claude Code subagent
  frontmatter retained as an adapter.
- Makes `AGENTS.md` the shared instruction surface for Claude, ChatGPT, Codex and other repository-aware
  assistants. Per-kind scientific rules now live in its scaffold-managed block; new `CLAUDE.md` files import
  it without duplication, while existing Claude customizations remain untouched.
- Packages `new-study` as a portable ChatGPT/Codex skills-only plugin and documents Claude and Codex skill
  installation separately.
- Generated CI checks out `v0.7.0`.

## v0.6.0 (2026-10-01)

- Needs adaptive-preregistration v0.7.0 or later. Generated CI checks out `v0.6.0`.
- New tools start at `0.1.0`, in preparation (an undated changelog heading), so `release-check` and `check` agree.
- **Tools use kit v0.7.0.** `new tool` installs `tool-versioning` (releases: annotated tags, outputs changed, consumers,
  `release-check`) in place of the profile's preregistration modules; `prereg`, a kit default, now scopes the tool
  claim first (`tool-scope` was merged into it). A tool's override experiments are preregistered in the research
  corpus. `check` warns while a tool with the scope protocol has no `SCOPE.toml`.

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
