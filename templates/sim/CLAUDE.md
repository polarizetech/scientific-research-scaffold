@AGENTS.md

# {{name}}

**Kind:** sim. One simulator; its versions are `model-vX.Y.Z` tags in this repo, never new repos.

- **Predict first.** Read `.agents/protocols/PREREG_PROTOCOL.md` before running, changing or reporting any
  experiment. A failure closes a version; it does not edit it.
- **Every parameter is in `ASSUMPTIONS.md`**, tagged `[LIT]`, `[DERIVED]` or `[ARBITRARY]`.
- **A model change is a new tag** and a `CHANGELOG.md` entry, never an edit to a tagged version.
- **No absolute home-directory paths.**

## Agents

Hand each task to the specialist in `.claude/agents/` whose description fits, and keep general work
(planning, small edits, git) here. When a task spans several, run them in order:

- a model change: `researcher` (what is known, and its tier), then the user's decision, then
  `computational-engineer`;
- a result: `analyst` (numbers, with their uncertainty), then `science-writer`.

Disciplines the researcher, analyst and writer draw on are in `.claude/disciplines.md`.
Agents hand back in 150 words or fewer, and run in parallel only on independent work
([coordination protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/main/agents/COORDINATION.md)).
`scaffold usage` shows what this repo's sessions cost.
