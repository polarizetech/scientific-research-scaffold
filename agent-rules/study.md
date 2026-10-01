# {{name}}

**Kind:** study. The layout and rules are the study protocol's; `STUDY.toml` is the register.

- **Work types.** An idea for exploring or demonstrating goes in `apps/` (a new idea gets a new version);
  a model in `sims/`; an analysis of an existing dataset in `datasets/`; a piece of mathematics in
  `calculators/`; reusable code in a tool repo. Create each with `scaffold new app|sim|dataset|calculator`,
  and follow its section of the study protocol, including what it needs before it starts.
- **Preregistrations live in the unit they test** (`<unit>/preregistrations/<EID>/`) and are listed in
  `EXPERIMENTS.md`. Nothing an app shows is a finding.
- **Predict first.** No run that could be quoted happens before its `PREREG.md` is tagged
  (`.agents/protocols/PREREG_PROTOCOL.md`).
- **Findings go to the corpus**, `{{corpus_repo}}`, and are referenced here by claim ID in `RESEARCH.md`.
  Never add the corpus as a submodule; never raise a claim's tier from here.
- **Depend on tags.** Libraries and external sims are pinned in `pyproject.toml`. Workbench tools go through
  `shared/workbench.py`, for local exploration only.
- **No absolute home-directory paths.**
- `make check` must pass before a commit is pushed.
