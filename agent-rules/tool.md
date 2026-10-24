# {{name}}

**Kind:** tool (`TOOL.toml`). {{job}}

- **No research here, except comparisons with other tools.** No questions, findings or `RESEARCH.md`, and no
  root `experiments/` or `preregistrations/`. A measurement made with this tool belongs to the study that made
  it. The exception is comparison units: `sims/<slug>/` and `datasets/<slug>/` that compare this tool's
  functionality against other tools, preregistering predictions based on inputs and checking whether the run is
  correct, as an extension of the test suite (`.agents/protocols/TOOL_VERSIONING.md` §1a). Each names what it
  `compares` in its `SCOPE.toml`, is listed under `[[comparisons]]` in `TOOL.toml`, keeps its preregistrations
  and results inside it, and predicts tool outputs, never the world.
- **Scope before science.** The claim, then the features, then an evidence basis and the person's recorded
  decision for every scientific feature, in `SCOPE.toml` (`.agents/protocols/SCOPE_PROTOCOL.md`). Infrastructure
  is yours to decide; nothing scientific is built before it is scoped. An override's experiment is
  preregistered in the research corpus, not here. A tool the person calls exploratory skips this until it
  gets its claim (`stage = "exploratory"` in `SCOPE.toml`); nothing it shows is a finding.
- **Releases** follow `.agents/protocols/TOOL_VERSIONING.md`; run `python3 .agents/tools/release-check` before
  tagging.
- **One version.** `version` in `TOOL.toml`, `pyproject.toml` and `CITATION.cff`, and a `CHANGELOG.md`
  heading, all agree; `scaffold check` fails when they drift. Releases are tagged `vX.Y.Z`.
- **Consumers.** Each repo that depends on this tool is listed in `TOOL.toml` with what it `uses`. A change
  to any of those is a change for that consumer even when every test here passes: name it under
  `### Outputs changed` in `CHANGELOG.md`.
- **No absolute home-directory paths.**
