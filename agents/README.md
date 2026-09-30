<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Agents

Specialist agents that every repo the scaffold makes gets in `.claude/agents/`. Each is a Claude Code
subagent: a session hands a task to whichever one's description fits, so each agent can stay narrow and
get better at its own job instead of one general agent doing everything. The templates are in
[`templates/agents/`](../templates/agents/).

| agent | for | study | sim | tool |
|---|---|---|---|---|
| `scout` | finding and summarising, read-only, so other agents don't read everything themselves | ✓ | ✓ | ✓ |
| `computational-engineer` | simulators, models, numerical code, pipelines; language choice, typing, linting, reuse vs duplication | ✓ | ✓ | ✓ |
| `mathematician` | equations, constants and scaling laws, with units, sources and valid ranges; specifies calculators | ✓ | ✓ | ✓ |
| `designer` | layout and visual design on the design system; how to show a dataset | ✓ | | ✓ |
| `frontend-developer` | React and shadcn/ui interfaces built from the designer's mockups, on the design system's components | ✓ | | ✓ |
| `researcher` | literature and evidence, evidence tiers, claims in the corpus | ✓ | ✓ | ✓ |
| `analyst` | data analysis and statistics, preregistered analysis plans | ✓ | ✓ | ✓ |
| `science-writer` | papers, and blog posts as a separate register | ✓ | ✓ | ✓ |

**How they work together** is the [coordination protocol](COORDINATION.md): one lead delegates,
agents pass 150-word handoffs rather than transcripts, a scientific feature goes researcher, then the
person's decision, then engineer, and parallel work is limited to independent tasks.

**Which model each starts on.** There is no automatic per-task model router, so each agent starts cheap and
the lead escalates a task on a clear signal (two failed attempts, a design decision across many files,
subtle scientific or statistical judgment):

| agent | model | effort |
|---|---|---|
| `scout` | haiku | low |
| `computational-engineer`, `mathematician` | sonnet | high |
| `designer`, `frontend-developer` | sonnet | medium |
| `researcher`, `science-writer` | sonnet | medium |
| `analyst` | sonnet | high |

A profile overrides any of them in `[agents.routing]`, as `analyst = "opus:high"`.

**Codex and other assistants** don't read `.claude/agents/`, but they read `AGENTS.md`. The scaffold keeps a
marked section there (`<!-- scaffold:start -->` to `<!-- scaffold:end -->`, beside the preregistration
kit's own) listing the roles, pointing at the same agent files as briefs, and giving the coordination rules
and Codex routing: the models named in the profile's `[agents.codex]`, and reasoning effort by task.

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

**Keeping them current.** The agent files, `.claude/disciplines.md` and the `AGENTS.md` section are
scaffold-owned, so `scaffold update` brings them up to date in repos where nobody has edited them. An agent a
repo has tuned is kept as it is. To add them to a repo made before they existed, run
`scaffold update --apply --adopt .claude/agents --adopt .claude/disciplines.md --adopt AGENTS.md`.

**What it costs.** `scaffold usage` reads Claude Code's and Codex's local logs and reports, per repo, the
tokens used by model, the API-equivalent cost at the rates in [`prices.toml`](prices.toml), a monthly
projection, and, for Codex, the plan's rate-limit windows. Each API response is counted once. On a
subscription the dollar figure is a measure of scale, not a bill.

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
