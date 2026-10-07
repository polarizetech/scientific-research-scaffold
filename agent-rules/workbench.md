# {{name}}

**Kind:** workbench (`WORKBENCH.toml`). Where work starts, and where most of it stays.

- **What goes where.** General, claim-agnostic code goes at the top: `tools/` (reusable tools), `sims/`
  (general simulators), `apps/` (general apps). Work that serves one question goes in that study,
  `studies/<name>/`, in its own `apps/`, `sims/`, `datasets/`, `calculators/` and `tools/`. Create each with
  `scaffold new study|tool|sim|app|dataset|calculator`, passing `--inside` or `--study`.
- **Before building, look in `tools/`.** Reuse what is there. A tool that only one study uses lives in that
  study; when a second study needs it, it moves up to `tools/`.
- **A unit starts with its claim, in one question** (`SCOPE.toml`, `.agents/protocols/SCOPE_PROTOCOL.md`). If
  the person says a unit is exploratory, don't ask: create it with `--exploratory` and build; it gets its
  claim before its first preregistered experiment. A new study always starts with its question.
- **Preregistrations live in the unit they test** (`<unit>/preregistrations/<EID>/`), listed in the root
  `EXPERIMENTS.md`. Nothing an app shows is a finding.
- **Predict first.** No run that could be quoted happens before its `PREREG.md` is tagged
  (`.agents/protocols/PREREG_PROTOCOL.md`).
- **Findings go to the corpus**, `{{corpus_repo}}`, referenced by claim ID in each study's `RESEARCH.md`.
- **Private folders stay private.** The folders listed under `private` in `WORKBENCH.toml` hold data about
  people; nothing in them is copied, quoted or published, and the repo stays private.
- **A study leaves for its own repo** when someone outside must see it without the rest, when it must stay
  reproducible after the workbench moves on, or when it needs its own releases.
- **No absolute home-directory paths.**
