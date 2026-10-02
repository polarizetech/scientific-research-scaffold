<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Upgrading a repo to a newer scaffold

Each release has a section here. **`scaffold update`** does the mechanical part: the files the scaffold
owns, the scaffold section of `AGENTS.md`, the session hook, and the CI ref. **The session** (a person, or an
agent with the person's go-ahead) does the rest, which needs judgment. A repo records the release it was
last brought to in `.scaffold.lock`; `scaffold version` says when a newer one exists and prints the
sections in between.

To upgrade a repo:

1. `scaffold update` (a dry run) and read the plan, then `scaffold update --apply`.
2. Do the session steps of every release between the repo's and the current one, oldest first.
3. `scaffold check`, then commit.

Every release adds a section here, newest first. A step a session can't do without the person's decision
says so.

## Unreleased

**`scaffold update` does:** moves the CI ref; nothing else new.

**The session does:** nothing for existing studies, sims and tools. A repo that is really a workbench (many
projects, general tools, no single question) can adopt the kind: add `WORKBENCH.toml`, list its private
folders, and create or register its studies with `scaffold new study --inside .`

## v0.7.0

**`scaffold update` does:** moves the CI ref to `v0.7.0`; refreshes the specialist briefs from
scientific-research-agents v0.2.0; and adds the repo kind's scientific rules to the scaffold-managed section
of `AGENTS.md`, so Claude Code, ChatGPT, Codex and other repository-aware assistants receive the same rules.

**The session does:** nothing. Existing `CLAUDE.md` files remain untouched and continue to import
`AGENTS.md`; newly scaffolded repositories use a one-line `CLAUDE.md` adapter. No Claude Code agent, routing,
or session hook is removed.

## v0.6.0

**`scaffold update` does:** moves the CI ref to `v0.6.0`; nothing else new, since this release changes what new tools get.

**The session does:**
- **Update the preregistration kit to v0.7.0 or later** (`.agents/bin/kit_ap update`). `tool-scope` is merged
  into `prereg` (kit 0.6.0), so a repo that had it drops it and keeps scoping; skip v0.5.0's "add `tool-scope`"
  step. Every unit now starts with a claim (`SCOPE.toml`).
- **Tool repos add `tool-versioning`** (`.agents/bin/kit_ap add tool-versioning`) and run
  `python3 .agents/tools/release-check`. Fix what it reports with the person: a released version with no tag
  gets its tag only if the person confirms the release; research it finds in the tool moves to the research
  repo, with their go-ahead.
- **A tool's override experiments** are preregistered in the research corpus, linked from its `SCOPE.toml`.

## v0.5.1

**`scaffold update` does:** moves the CI ref to `v0.5.1`, and keeps `"adopted": true` in the lock of a repo
that adopted the scaffold.

**The session does:**
- **A repo that adopted the scaffold before this release** (its manifest was added by hand, not by
  `scaffold new`) has a lock without the flag. Add `"adopted": true` to its `.scaffold.lock`, so that `update`
  never adds the scaffold's CI or `Makefile` to it unasked.

## v0.5.0

**`scaffold update` does:** moves the CI ref to `v0.5.0`; otherwise nothing new, since this release
changes what new tools get.

**The session does:**
- **Tool repos get `tool-scope`.** Update the preregistration kit to v0.5.0 or later (`.agents/bin/kit_ap update`), then
  `.agents/bin/kit_ap add tool-scope`. Scoping then applies to the tool itself, with its record at `SCOPE.toml`
  in the root. For a tool that is already built, and especially one at SHIPPED, ask the person whether to scope
  it now or only its next scientific change; don't write its claim or decisions for them.

## v0.4.0

**`scaffold update` does:**
- adds or refreshes the agents (now from scientific-research-agents, including the new `scout` and
  `mathematician`, each with a starting model and effort), `.claude/disciplines.md`, the scaffold section of
  `AGENTS.md`, and the session hook that runs `scaffold version`. In a repo without `.scaffold.lock`, add
  them with `--adopt .claude/agents --adopt .claude/disciplines.md --adopt AGENTS.md --adopt .claude/settings.json`.
- moves the CI ref to the new release.

**The session does:**
- **`experiments/` is the old layout.** Leave existing experiment folders where they are and keep them in
  `EXPERIMENTS.md`; new preregistrations go in the unit they test, `<unit>/preregistrations/<EID>/`. Move an
  old one only if the person wants it moved, one commit per move.
- **`data/manifest.json` is the old layout.** For each dataset listed there, run `scaffold new dataset <slug>`
  and move its reference into `DATASET.toml` (provider, accession, pinned version, licence, and the selection
  criteria if they were written down). Then remove the old file. Don't select a dataset or invent criteria
  on the person's behalf.
- **Register existing units.** A dataset or calculator folder that `check` reports as unregistered gets its
  `[[datasets]]` or `[[calculators]]` entry in `STUDY.toml`.
- **Mathematics in apps or scripts** that is really a calculator (an equation with constants the research
  reuses) can move to `calculators/<slug>/` with `scaffold new calculator`; ask before moving working code.
- **The preregistration kit still guards only `experiments/`** until it is updated to find
  `preregistrations/` folders. Until then, tag each new preregistration by hand as the kit's protocol says.

## v0.3.0

**`scaffold update` does:** writes `.scaffold.lock`; moves the CI ref to `v0.3.0`; adds the agents in
`.claude/agents/` and `.claude/disciplines.md` to repos the scaffold made (adopted repos: `--adopt`).

**The session does:**
- **A repo that does a job for other repos** becomes a tool: add `TOOL.toml` (PROTOCOL.md, Tools), move any
  research out to the study that made it, and list its consumers with what they use.
- **Studies and sims that use a tool** list it under `[[tools]]` in their manifest, pinned to a tag.

## v0.2.0

**`scaffold update` does:** nothing; this release changed how new repos are made.

**The session does:**
- **Visibility.** Repos made by v0.1.0 recorded `visibility = "private"` with a date, whether or not anyone
  decided it. Ask the person to confirm the decision, and correct the manifest if it was never made.
- **Profile.** Make sure the manifest names its `profile`; there is no longer a default.
