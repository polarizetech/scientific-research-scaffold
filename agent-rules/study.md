# {{name}}

**Kind:** study. The layout and rules are the study protocol's; `STUDY.toml` is the register.

- **Size the goal first.** A new study or tool starts exploratory, from the person's goal and a rough idea of
  how to get there (`--goal`, `--approach`), not from a claim. Before building anything, talk it through with
  the person, back and forth: is the goal one study's worth, or should it be broken up? Propose a split when
  it is too big, in plain words, and let the person decide. Record the decision as `scope = "one"` or
  `scope = "split: a, b"` with `scope_decided` (YYYY-MM-DD) in `HYPOTHESIS.toml`; `scaffold check` warns until it is there.
  After a split, each piece starts the same way. A claim comes later, when the person wants one.
- **When the person gives a hypothesis, it is the source.** Preserve it verbatim in `HYPOTHESIS.toml` and set
  `mode = "hypothesis"`; an exploratory study stays at SKETCH until then. Use the relevant
  specialist briefs, with the `researcher` responsible for literature and evidence, to propose a decomposition
  into falsifiable steps and integrations. Never silently substitute an agent-authored hypothesis or
  counts-against criterion for the person's wording. Keep each element proposed until the person accepts that
  exact revision; only accepted elements can derive unit scope.
- **Every hypothesis element has a basis.** Mark it `established` only from verified corpus evidence referenced
  in `RESEARCH.md`. Otherwise it is `open` or `exploratory` and has both a concrete goal and what would count
  against it. An unestablished integration between established steps is its own element and its own goal.
- **Every unit derives from the map.** Each app version, sim, dataset analysis and calculator maps to one or
  more element IDs in `HYPOTHESIS.toml`; the managing agent derives the association from the unit's recorded
  scope and purpose, states its role, and writes the same provenance into `SCOPE.toml`. Preserve an existing
  narrower accepted unit claim; association with a broader element does not replace it. Snapshot element and
  evidence revisions and fingerprints.
- **Agents propagate impacts.** Run `scaffold sync-hypothesis` after changing an element, evidence link, finding
  or corpus revision. It marks affected units `needs-review`; the agent working on each affected unit reviews and
  records the appropriate disposition (new version/experiment, reproduction, design update plus preregistration,
  or retirement/closure). Routine linking, queueing and synchronization use the study's standing
  `impact_management` policy and do not prompt the person. Ask only when the hypothesis or falsifier's meaning
  would change, a new scientific choice is not already authorized, or safety/scope requires it.
- **Keep the corpus overview current.** The corpus project's README is the canonical cross-repo overview. When a
  unit, decision, experiment or finding changes an element, update its corpus references and project overview,
  then update `HYPOTHESIS.toml`/`RESEARCH.md`; do not copy the corpus into this repo. Treat the overview as a
  reverse impact index: follow referenced claim IDs into every study and element they affect, synchronize each
  available checkout, and record unavailable studies as pending cross-study impacts.
- **Work types.** An idea for exploring or demonstrating goes in `apps/` (a new idea gets a new version);
  a model in `sims/`; an analysis of an existing dataset in `datasets/`; a piece of mathematics in
  `calculators/`; reusable code in a tool repo. Create each with `scaffold new app|sim|dataset|calculator`,
  and follow its section of the study protocol, including what it needs before it starts.
- **A unit starts with its claim, in one question** (the claim and what would count against it, recorded in
  its `SCOPE.toml`; `.agents/protocols/SCOPE_PROTOCOL.md`). If the person says a unit is exploratory, don't
  ask: create it with `--exploratory`, or set that stage in its `SCOPE.toml`, and build. It gets its claim
  before its first preregistered experiment.
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
