<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Agents

Specialist agents that every repo the scaffold makes gets in `.claude/agents/`. Each is a Claude Code
subagent: a session hands a task to whichever one's description fits, so each agent can stay narrow and
get better at its own job instead of one general agent doing everything. The templates are in
[`templates/agents/`](../templates/agents/).

| agent | for | study | sim | tool |
|---|---|---|---|---|
| `computational-engineer` | simulators, models, numerical code, pipelines; language choice, typing, linting, reuse vs duplication | ✓ | ✓ | ✓ |
| `designer` | layout and visual design on the design system; how to show a dataset | ✓ | | ✓ |
| `frontend-developer` | React and shadcn/ui interfaces built from the designer's mockups, on the design system's components | ✓ | | ✓ |
| `researcher` | literature and evidence, evidence tiers, claims in the corpus | ✓ | ✓ | ✓ |
| `analyst` | data analysis and statistics, preregistered analysis plans | ✓ | ✓ | ✓ |
| `science-writer` | papers, and blog posts as a separate register | ✓ | ✓ | ✓ |

**One agent per role, not per discipline.** Research, analysis and writing are different jobs; neuroscience
and cardiology mostly are not, and they overlap (EEG and ECG share a recording chain). So the science roles
are split by what they do, and each reads `.claude/disciplines.md`: short briefs, from
[`disciplines/`](disciplines/), on what is established in each field, its standards and its traps. A
profile chooses the disciplines.

**What comes from the profile** (`[agents]` in `profiles/<name>.toml`):

- `disciplines`: which briefs go into `.claude/disciplines.md`;
- `conventions`: house rules for code (typing, linting, style), written into the engineer and frontend
  agents. Empty means "follow the repo's own configuration".

The design system the designer and frontend developer build on is the profile's `[design] repo`.

**Keeping them current.** The agent files and `.claude/disciplines.md` are scaffold-owned, so
`scaffold update` brings them up to date in repos where nobody has edited them. An agent a repo has
tuned is kept as it is. To add the agents to a repo made before they existed, run
`scaffold update --apply --adopt .claude/agents --adopt .claude/disciplines.md`.

**The science stays the user's.** Every agent follows the same rule: infrastructure is the agent's to
decide, but equations, parameters and interpretations come from the user and the research. Where the
preregistration kit's `tool-scope` module is installed, no scientific feature is built without an evidence
tier and the user's recorded decision.

[`references/language-routing.md`](references/language-routing.md) is the evidence behind the engineer's
language-choice rule.

## Skills

`skills/new-study/` is a Claude Code skill for creating and adopting studies with this scaffold. To use it,
copy the folder to `~/.claude/skills/` (for you) or `.claude/skills/` (for one repo).

The rules every study and sim carries for coding assistants are in each generated `CLAUDE.md`, and in
`AGENTS.md`, which the preregistration kit installs and keeps up to date.
