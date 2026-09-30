@AGENTS.md

# {{name}}

**Kind:** tool (`TOOL.toml`). {{job}}

- **No research here.** No questions, preregistrations, results or findings, no `RESEARCH.md`,
  `EXPERIMENTS.md`, `experiments/` or `preregistrations/`. A measurement made with this tool belongs to the study that made it.
- **Scope before science.** The claim, then the features, then an evidence basis and the person's recorded
  decision for every scientific feature, in `SCOPE.toml` (`.agents/protocols/SCOPE_PROTOCOL.md`). Infrastructure
  is yours to decide; nothing scientific is built before it is scoped.
- **One version.** `version` in `TOOL.toml`, `pyproject.toml` and `CITATION.cff`, and a `CHANGELOG.md`
  heading, all agree; `scaffold check` fails when they drift. Releases are tagged `vX.Y.Z`.
- **Consumers.** Each repo that depends on this tool is listed in `TOOL.toml` with what it `uses`. A change
  to any of those is a change for that consumer even when every test here passes: name it under
  `### Outputs changed` in `CHANGELOG.md`.
- **No absolute home-directory paths.**

## Agents

Hand each task to the specialist in `.claude/agents/` whose description fits, and keep general work
(planning, small edits, git) here. When a task spans several, run them in order:

- a scientific feature: `researcher` (what is known, and its tier), then the user's decision, then
  `computational-engineer`;
- an interface: `designer` (mockup on the design system), then `frontend-developer`;
- a result: `analyst` (numbers, with their uncertainty), then `science-writer`.

Disciplines the researcher, analyst and writer draw on are in `.claude/disciplines.md`.
Agents hand back in 150 words or fewer, and run in parallel only on independent work
([coordination protocol](https://github.com/polarizetech/scientific-research-agents/blob/{{agents_ref}}/COORDINATION.md)).
`scaffold usage` shows what this repo's sessions cost.
