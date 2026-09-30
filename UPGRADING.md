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
