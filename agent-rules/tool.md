# {{name}}

**Kind:** tool (`TOOL.toml`). {{job}}

- **No research here.** No questions, preregistrations, results or findings, no `RESEARCH.md`,
  `EXPERIMENTS.md`, `experiments/` or `preregistrations/`. A measurement made with this tool belongs to the study that made it.
- **Scope before science.** The claim, then the features, then an evidence basis and the person's recorded
  decision for every scientific feature, in `SCOPE.toml` (`.agents/protocols/SCOPE_PROTOCOL.md`). Infrastructure
  is yours to decide; nothing scientific is built before it is scoped. An override's experiment is
  preregistered in the research corpus, not here.
- **Releases** follow `.agents/protocols/TOOL_VERSIONING.md`; run `python3 .agents/tools/release-check` before
  tagging.
- **One version.** `version` in `TOOL.toml`, `pyproject.toml` and `CITATION.cff`, and a `CHANGELOG.md`
  heading, all agree; `scaffold check` fails when they drift. Releases are tagged `vX.Y.Z`.
- **Consumers.** Each repo that depends on this tool is listed in `TOOL.toml` with what it `uses`. A change
  to any of those is a change for that consumer even when every test here passes: name it under
  `### Outputs changed` in `CHANGELOG.md`.
- **No absolute home-directory paths.**
