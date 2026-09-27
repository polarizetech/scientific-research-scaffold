@AGENTS.md

# {{name}}

**Kind:** study. The layout and rules are the study protocol's; `STUDY.toml` is the register.

- **Explore in `apps/`, test in `experiments/`.** Nothing an app shows is a finding. A new idea gets a new
  app version (`scaffold new app <slug>`); a superseded version is left as it was.
- **Predict first.** No run that could be quoted happens before its `PREREG.md` is tagged
  (`.agents/protocols/PREREG_PROTOCOL.md`).
- **Findings go to the corpus**, `{{corpus_repo}}`, and are referenced here by claim ID in `RESEARCH.md`.
  Never add the corpus as a submodule; never raise a claim's tier from here.
- **Depend on tags.** Libraries and external sims are pinned in `pyproject.toml`. Workbench tools go through
  `shared/workbench.py`, for local exploration only.
- **No absolute home-directory paths.**
- `make check` must pass before a commit is pushed.
