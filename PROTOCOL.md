<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The study protocol

How a piece of research is laid out across repositories: what a **study** is, what a **sim** is, what a
**tool** is, what each one contains, what it depends on and how, and how a sim graduates out of a study into
its own repo.

This document is generic. Everything specific to one organisation (which repo holds the research corpus,
which design system the apps use, which workbench holds shared tools) lives in a **profile**
(`profiles/*.toml`). Fork the repo, write your own profile, and the rest applies unchanged.

`bin/scaffold` creates repos in this shape and checks existing ones against it. The rules below are
what `scaffold check` enforces; where a rule is advice rather than a check, it says so.

---

## 0. The idea in one paragraph

A study is **one question, pursued with whatever it takes**: apps to explore and demonstrate it, sims to
model it, datasets to test it against, calculators for its mathematics, and tools it builds for reuse. Each
of these **work types** has its own folder, its own entry requirements and its own strictness (§ 5). Its
findings do not live in the study: they go to **one shared research corpus**, which the study refers to by
claim ID. Its predictions are written down and tagged **before** anything runs. Simulators it depends on
are either folders inside it or, once they earn it, **their own versioned repos**, pinned like any other
library. Nothing in it resolves a path on one person's machine.

---

## 1. Kinds, and naming

| kind | what it is | versions live |
|---|---|---|
| **study** | one research question and everything used to pursue it | as tags and as `apps/vN-*` folders |
| **sim** | one simulator, under adaptive preregistration | as `model-vX.Y.Z` tags inside one repo |
| **tool** | one job done for other repos (an instrument, a recorder, a service, a library); no research | as `vX.Y.Z` tags inside one repo |
| **workbench** | where work starts: general tools, sims and apps, and the studies that use them, in one repo | per unit; the workbench itself has no one stage |

A profile fills five **roles** that studies and sims depend on but never contain. There is no default
profile: `scaffold new` takes `--profile NAME` or `$SCAFFOLD_PROFILE`, and a study's manifest records which
one it uses from then on.

| role | what it provides | example (polarizetech profile) |
|---|---|---|
| **corpus** | the one shared record of citations, claims and findings | `polarizetech/research` |
| **prereg kit** | the preregistration protocol and its installer | `polarizetech/adaptive-preregistration` |
| **design system** | the look for every app, and labels for how sure a number is | `polarizetech/polarize-ui` |
| **workbench** | shared tools not yet released as libraries | `polarizetech/audio-projects` |
| **libraries** | released, versioned code | `dataset-fetch`, `universal-wave-translation-layer` |

**Names are the subject, with no prefix.** `reef-acoustics`, `sound-propagation`, not
`lab-reef-acoustics` or `sim-sound-propagation`. A prefix fixes a classification into a name that outlives it, and
renaming later breaks absolute paths and links. The kind is declared in two places instead, and
`scaffold check` makes sure they agree:

- `kind = "study"` (or `"sim"`, or `"tool"`) in the manifest, and
- the kind line directly under the README's title: `**Kind:** study · **Stage:** SKETCH`.

An index of which repo is which kind is kept outside the repos (the organisation's site or profile), not
in their names.

---

## 2. The manifest

Every study has `STUDY.toml`; every sim has `SIM.toml`; every tool has `TOOL.toml` (§ 8). It is the machine-readable register for the repo.

```toml
kind = "study"
name = "reef-acoustics"
question = "Does the sound of a reef track its coral cover across survey sites?"
stage = "SKETCH"                 # SKETCH | PROBE | BENCH | SHIPPED (§ 13)
visibility = "private"           # public | private: decided, never defaulted
visibility_decided = "2026-01-15"
profile = "polarizetech"

[corpus]
project = "reef-acoustics"       # the study's folder in the corpus
claim_prefix = "REEF"

[[apps]]                         # one entry per version, oldest first
version = "v1"
slug = "site-listener"
question = "Can a healthy and a degraded site be told apart by ear?"
status = "superseded"            # active | superseded | abandoned

[[sims]]                         # a folder inside this study...
slug = "sound-propagation"
path = "sims/sound-propagation"

[[sims]]                         # ...or a pinned repo
slug = "fish-chorus"
repo = "your-org/fish-chorus"
ref = "model-v0.2.0"             # a tag. Never a branch.

[[tools]]                        # a tool this study uses, pinned the same way
slug = "hydrophone-logger"
repo = "your-org/hydrophone-logger"
ref = "v1.2.0"
```

**Visibility is a person's decision.** `scaffold new` writes `visibility = "undecided"` unless it is given
`--visibility public|private`, and `scaffold check` fails until a decision and its date are recorded.

Experiments are registered in `EXPERIMENTS.md` (the prereg kit's register), not duplicated here.

**`path` overrides the default location.** It is how an existing repo adopts this protocol without moving
working code (see [`ADOPTING.md`](ADOPTING.md)). A new repo leaves it out.

---

## 3. What a study contains

```
<study>/
  README.md            title, kind line, the question, how to run it
  CLAUDE.md            "@AGENTS.md", the Claude Code adapter
  AGENTS.md            shared instructions for repository-aware assistants (managed in marked sections)
  STUDY.toml           the manifest (§ 2)
  RESEARCH.md          which corpus project and claim IDs this study bears on
  EXPERIMENTS.md       the register of every preregistration, wherever it lives (the prereg kit's)
  LICENSE              code MIT; text and figures CC BY 4.0
  CITATION.cff
  pyproject.toml + uv.lock   every library, tool and external sim pinned to a tag
  Makefile             `make check` runs everything CI runs
  apps/<vN-slug>/      interactive exploration and demonstration, one folder per version (§ 6)
  sims/<slug>/         simulators still living inside the study (§ 7)
  datasets/<slug>/     dataset analyses: the data pinned, the analysis preregistered (§ 9)
  calculators/<slug>/  the study's mathematics as tested code (§ 10)
  shared/workbench.py  the one resolver for workbench tools (§ 4)
  .agents/             the prereg kit's protocols and tools
  .claude/agents/      specialist role briefs: scout, engineer, mathematician, designer, frontend, researcher, analyst, writer
  .claude/disciplines.md   the research disciplines those agents draw on, from the profile
```

A folder for a work type exists only once the study has one of them: `scaffold new
app|sim|dataset|calculator` creates it, registers it in `STUDY.toml`, and gives it the files its type needs.

---

## 4. Dependencies

The direction is fixed: a study depends on sims, tools and libraries; sims depend on tools and libraries;
tools depend on other tools and libraries; nothing depends on a study. Nobody imports the corpus.

| depending on | how | never |
|---|---|---|
| a library, a tool or an external sim | a pinned **tag** in `pyproject.toml` and `uv.lock`, and in the manifest's `[[sims]]` or `[[tools]]` | a branch, a sibling folder, an editable install, for anything a result is quoted from |
| the corpus | its claim IDs and links, in `RESEARCH.md` | a submodule, a copy, an import |
| a dataset | a dataset-fetch reference pinned to a version, in `datasets/<slug>/DATASET.toml` (§ 9) | committed bulk data, or "latest" |
| a workbench tool | `shared/workbench.py`, for local development only | an absolute path |
| the design system | served through an allow-list by each app's `serve.py` (§ 6) | a CDN |

**The workbench resolver.** Tools that have not yet been released as libraries are reached through
`shared/workbench.py`, generated from the profile. It:

1. reads `SCAFFOLD_WORKBENCH` (and any older variable names the profile lists), then tries a sibling
   checkout;
2. accepts a directory only if it contains the profile's marker file;
3. **raises with the line that would fix it** rather than guessing;
4. records the workbench commit it resolved, through `provenance()`, so every output says which version of
   the shared code produced it.

A result produced through the workbench resolver is an exploratory result. Before it is quoted outside,
the tool it used is released and pinned.

**Private dependencies in CI.** The token GitHub Actions gives a workflow reads only its own repo, so a
pinned git URL to another private repo fails there with `could not read Username for 'https://github.com'`.
The generated workflow reads one optional Actions secret, `PRIVATE_DEPS_TOKEN`: a token with read-only
**Contents** access to the private repos the project pins, and nothing else. When it is set, CI uses it for
git URLs under the profile's `org` on github.com. When it is not, and the install fails in a repo that pins
that organisation by git URL, CI says so in a warning and still runs `scaffold check`; tests that need the
dependencies will fail until the secret is added. Pull requests from forks never receive the secret. This is
advice about the generated CI, not a rule `check` enforces.

**No absolute home-directory paths, anywhere.** A path that names one person's machine is a result nobody
else can regenerate. `scaffold check` flags them.

---

## 5. Work types

A study is built from units of work, each of one type. The types differ in what they are for and how
strict they must be, so each has a folder, a register in `STUDY.toml`, and rules of its own:

| type | where | for | before it starts |
|---|---|---|---|
| **app** | `apps/vN-<slug>/` | exploring or demonstrating a concept interactively; may become a deliverable | the concept, the research it draws on, and what it should help someone understand |
| **sim** | `sims/<slug>/`, or its own repo | running a model forward, often on an existing open-source simulator | the model's equations and every parameter with its source, the question, and a prediction |
| **dataset** | `datasets/<slug>/` | testing the question against data that exists | a pinned reference to the data, selection criteria, and a preregistered analysis plan, before the outcome is opened |
| **calculator** | `calculators/<slug>/` | the mathematics: equations, constants, ratios, scaling laws | the equation, its source or derivation, units, valid range and reference values |
| **tool** | its own repo (§ 8) | reusable code with no research of its own | a job, and the repos that will use it |

### The cycle

The types feed each other through the research corpus, in both directions:

- **Research to unit.** A unit starts only when the research meets its entry requirement above. A sim with
  unsourced parameters, or a dataset chosen before its criteria were written, has not met it.
- **Unit to research.** Every unit ends by writing back: a sim or dataset result as a finding, against its
  frozen predictions; what an app or calculator revealed as understanding, labelled as exploration; and in
  every case what to research or refine next.
- **Research changes a unit.** When research a unit depends on changes, the unit is revisited: a new app
  version, a sim rerun, a calculator's values rechecked.

Nothing an app shows is a finding. A finding comes from a preregistered prediction, in a sim, a dataset or a
calculator (§ 11).

### Where units live: a study's own repo, or a workbench

A study can be its own repo, or a folder in a **workbench** (`WORKBENCH.toml`): one repo that holds what is
general at the top and one folder per study.

```
<workbench>/
  WORKBENCH.toml       the theme, visibility, private folders, and the register of studies
  tools/  sims/  apps/ general, claim-agnostic units any study can use
  studies/<name>/      a study: STUDY.toml, RESEARCH.md, and its own apps/ sims/ datasets/ calculators/ tools/
  EXPERIMENTS.md  AGENTS.md  .agents/  CI  ...   shared by everything in the repo
```

- **General at the top, specific in the study.** A tool, sim or app that serves one study's question lives in
  that study. When a second study needs it, it moves up to the workbench's `tools/`, `sims/` or `apps/`.
- **A study in a workbench shares the repo's files**: the kit, the agents, CI, the licence. It has its own
  manifest, research references and units. `scaffold new study <name> --inside <workbench>` creates one, and
  `scaffold new tool|sim <name> --inside <study or workbench>` adds units to either.
- **A workbench has no one stage and no one corpus project**: each study has its own.
- **A workbench may mount the corpus** as a submodule, which nothing else may, because it is where the
  corpus is worked on alongside everything that uses it.
- **Private folders are declared.** `private = [...]` lists folders holding data about people; listing any
  requires `visibility = "private"`.
- **A study leaves for its own repo** when someone outside must see it without the rest, when it must stay
  reproducible after the workbench moves on, or when it needs its own releases. Leaving is advice, not a
  check.

### Adding a work type

When a new kind of work keeps appearing and needs its own strictness, it becomes a type. It gets: a folder
name (plural, saying what is built), a record of what it is, an entry requirement, a way of writing back
to research, a `scaffold new` command, and `check` rules. It is added to this section and to the table in
§ 14. Until then, it lives in the closest existing type.

---

## 6. Apps

- **One folder per version**: `apps/v1-site-listener/`, `apps/v2-site-comparison/`. A new idea gets a new
  version; a superseded version is left as it was and marked `superseded` in the manifest, so the path the
  study took stays visible.
- Each app is `index.html` + `app.js` + `app.css` + `serve.py`, with no build step unless it needs one.
- `serve.py` serves the design system through an **allow-list** of named files, never a directory mount,
  and the app must still work unstyled if the design system is absent.
- An app that shows a number shows **how sure** the number is, in a label the design system never lets be
  hidden.
- `scaffold new app <slug>` adds the next version and its manifest entry.

---

## 7. Sims

A sim is a simulator under adaptive preregistration. Its layout is the prereg kit's:

```
<sim>/
  README.md  CLAUDE.md  AGENTS.md  SIM.toml  LICENSE  CITATION.cff
  model/               the simulator, tagged model-vX.Y.Z when it changes
  preregistrations/<EID>/   PREREG.md, DEVIATIONS.md, RESULTS.md, ENV.lock, config, run.py, outputs/
  EXPERIMENTS.md       the register
  ASSUMPTIONS.md       every parameter, tagged [LIT] [DERIVED] or [ARBITRARY]
  CHANGELOG.md         what changed between model versions, and why
```

**Several versions of a sim live inside one sim repo, as tags.** A new model version never becomes a new
repo. Two genuinely different simulators are two sims.

### Where a sim lives, and when it moves

A sim **starts as a folder** inside the study that needs it (`sims/<slug>/`, with its own `SIM.toml`).
It is **promoted to its own repo** when any one of these becomes true:

| trigger | why it forces the move |
|---|---|
| a **second study** uses it | two studies importing one folder is two copies waiting to diverge |
| it needs **releases on its own schedule** | its versions no longer line up with the study's |
| it is **shared outside on its own** | it needs its own README, licence, citation and visibility decision |

Not triggers: tidiness, size, "it might be reused someday".

`scaffold promote-sim sims/<slug>` does the mechanical part: it splits the folder's history into its own
branch with `git subtree split`, so the new repo keeps every commit, and prints the remaining steps. The
study then deletes the folder and pins the new repo by tag in its manifest and lockfile.

---

## 8. Tools

A tool does **one job for other repos** and holds no research: an instrument and its recorder, a data
service, an importable library. A study asks a question; a tool is something studies use to answer theirs.

```
<tool>/
  README.md  CLAUDE.md  AGENTS.md  TOOL.toml  LICENSE  CITATION.cff
  CHANGELOG.md         every release, and what changed for the repos that depend on it
  pyproject.toml       when it is a Python package or has Python parts
  ...                  the tool's own layout: firmware, apps, a package, whatever the job needs
```

```toml
kind = "tool"
name = "hydrophone-logger"
job = "Records calibrated hydrophone audio to disk, with the gain it used"
stage = "BENCH"
visibility = "public"
visibility_decided = "2026-02-01"
profile = "polarizetech"
version = "1.2.0"                # the one version; everything else says the same

[[consumers]]                    # one entry per repo that depends on it
name = "reef-acoustics"
repo = "your-org/reef-acoustics"
uses = ["the WAV + sidecar layout", "GAIN_DB_DEFAULT"]
```

- **No research in a tool.** No question, no `[corpus]`, no `RESEARCH.md`, `EXPERIMENTS.md`,
  `experiments/` or `preregistrations/`. A measurement made with a tool, even a measurement *of* the tool, is a finding of the
  study that made it, recorded there against the tool release it used.
- **One version, said the same everywhere.** `version` in `TOOL.toml`, `[project] version` in
  `pyproject.toml`, `version` in `CITATION.cff`, and a heading in `CHANGELOG.md`. Releases are tagged
  `vX.Y.Z`.
- **Consumers say what they use.** Each `[[consumers]]` entry lists the routes, constants, files and
  formats that repo relies on. A change to any of them is a change for that consumer even when every
  test in the tool passes, so the release names it under `### Outputs changed` in `CHANGELOG.md`. (That
  heading is advice; `scaffold check` does not read changelog sections.)
- **A tool is scoped before anything scientific is built in it.** The prereg kit's `prereg` module settles
  the tool's claim with the person first, then its features, then an evidence basis and the person's recorded
  decision for each scientific feature, in `SCOPE.toml` at the root. A tool the person marks exploratory
  (§ 11) waits for all of that until it gets its claim. An override's experiment is preregistered
  in the research corpus, never in the tool. Infrastructure is the agent's to decide. `check` warns while a
  tool has no `SCOPE.toml`.
- **A tool is released by the kit's `tool-versioning` protocol**, installed in place of the profile's
  preregistration modules: annotated `vX.Y.Z` tags, a release that changes an output bumps MINOR and names it
  under `### Outputs changed` with the consumers to re-run, and `release-check` before tagging.
- **Where a tool starts.** Usually in the profile's workbench, reached through `shared/workbench.py`. It
  becomes its own repo when a number a study quotes depends on it (§ 4: before it is quoted, the tool it
  used is released and pinned), or when it is shared on its own. This is advice, not a check.

`scaffold new tool <name> --job "..."` creates one. A tool is always its own repo; there is no `--inside`.

---

## 9. Datasets

A dataset analysis tests the question against data that already exists. Its predictions and its
analysis are as much a deliverable as its result, so it is the strictest of the work types.

```
datasets/<slug>/
  DATASET.toml         where the data lives, its licence, and why it was chosen
  README.md            the question, and the order below
  analysis/            the program that produces every number, in named stages
  preregistrations/<EID>/   PREREG.md, DEVIATIONS.md, RESULTS.md
```

- **The data is referenced, never committed.** `DATASET.toml` holds a dataset-fetch reference: provider,
  accession, and a **pinned version**, never "latest", with the data's licence. `status` moves from
  `candidate` to `selected` to `fetched`; `check` requires the full reference once it is selected.
- **Criteria before selection.** What the data must contain to answer the question is written in
  `[selection] criteria` before a dataset is selected.
- **The order**, each step closing a way analyses have failed: check that the design can answer the
  question; check that the method works on this data without opening the outcome; preregister the
  predictions and the analysis plan, naming the stage that first opens the outcome; say what an adequate
  test of the smallest effect of interest needs, so a null means something; then run it, and make every
  number regenerable from the pinned data and the code.
- **Tools it uses are pinned**: the organisation's by tag, open-source packages by version.

`scaffold new dataset <slug> -q "..."` creates one.

---

## 10. Calculators

A calculator is one piece of the study's mathematics as tested code: an equation, a constant, a ratio, a
scaling law. Biology is variable, but some of what looks variable is not: a value that differs person to
person may reduce to a few measurable variables. Writing those down once, with their sources, lets the
research, sims, apps and analyses all use the same numbers.

```
calculators/<slug>/
  CALCULATOR.md        the equation, every symbol with its units, parameters with sources, valid range
  reference.csv        reference cases: inputs, expected output, and where each comes from
  (the code)           typed, one function per quantity; tests run every row of reference.csv
  preregistrations/<EID>/   when the calculator predicts something measurable
```

- **Every parameter has a source**, tagged `[LIT: doi]`, `[DERIVED: from what]` or `[ARBITRARY]`, with a
  BioNumbers ID where one exists. A value no one could verify is marked as a gap, not guessed.
- **Reference values** from a paper or a hand calculation are required from the PROBE stage on; `check`
  warns at SKETCH.
- **The same maths is recorded in the research corpus**, in the study's project under `calculators/`, so
  that it outlives the study.
- **A prediction** a calculator makes about measured data is preregistered like any other.
- **When a second study needs it**, it moves into a tool, pinned by tag, as a sim would.

This follows practice in quantitative biology: curated values with their literature source
(BioNumbers), and models that state their reference description and expected results (MIRIAM).

`scaffold new calculator <slug> -q "..."` creates one.

---

## 11. Preregistration

Every prediction that could be quoted, in a sim, a dataset or a calculator, follows the prereg kit's
protocol. A preregistration lives in the unit it tests, in `<unit>/preregistrations/<EID>/`, and is
listed in `EXPERIMENTS.md`:

1. `PREREG.md` is written and tagged `<EID>-prereg` **before** the first run that could be quoted.
2. Predictions are risky, numeric and directional, and each says what would count against it.
3. A failure closes the version; it does not edit it.
4. Every change after the tag goes in `DEVIATIONS.md`, with whether the outcome was already known.
5. Exploratory work stays under `exploratory/`, and says so.

**A unit starts with a claim, or is marked exploratory.** By default the first work in a unit is one question
from the session: the claim it tests, and what would count against it (the kit's `SCOPE_PROTOCOL.md`, recorded
in the unit's `SCOPE.toml`). The rest of the claim, what its terms mean, how it is measured and the smallest
effect that matters, is stated in its first `PREREG.md`. A unit the person calls exploratory skips the claim and
the evidence step: `scaffold new <app|sim|tool|dataset|calculator> ... --exploratory` writes its `SCOPE.toml`
with a build note (what is being built, and the date) and labels the unit's README. Nothing an exploratory
unit shows is a finding, and it has no preregistered experiments: preregistering the first one is when its
claim is settled and its record moves to `stage = "testing"`. A study or a workbench is never exploratory: it
starts with its question. Needs kit 0.9.0 or later.

The kit is installed, not linked: `kit_ap init` copies the protocols into `.agents/` and pins the kit's
commit in `.agents/kit_ap.lock`. `scaffold new` runs it for you when it can find the kit.

A repo that already froze analyses under an **earlier** preregistration system keeps them exactly as
frozen. It uses the kit for new preregistrations only, and lists the earlier ones in `EXPERIMENTS.md` with a
note saying which system froze them. Converting a frozen record would change the thing the freeze exists
to protect.

---

## 12. Research

Findings are written to the **corpus**, in the study's project folder there. The study carries only
`RESEARCH.md`: the corpus project, the claim prefix, and the claim IDs each unit bears on.

- **A study never raises a claim's tier.** The corpus decides what a result does to a claim.
- **The corpus is never a submodule of a study.** Two working copies of one corpus drift.
- A sim that has no corpus project yet says so in its `RESEARCH.md` rather than inventing one.

---

## 13. Stages

How strict to be scales with what a mistake would cost. Declare the stage in the manifest and the README.

| stage | means | owes |
|---|---|---|
| **SKETCH** | trying things | honest labels; say what was not done |
| **PROBE** | a number is being produced | preregistration before quoted runs; tests on the code that makes the number |
| **BENCH** | a second repo depends on it, or a number from it is quoted | CI, a lockfile, tagged releases |
| **SHIPPED** | someone outside is relying on it | a frozen release, a DOI, external preregistration |

These never relax at any stage: safety of anyone taking part, honest labels, other people's data licences,
and saying plainly what was not done.

---

## 14. What `scaffold check` enforces

| check | study | sim | sim inside a study | tool |
|---|---|---|---|---|
| manifest parses, and `kind`, `name`, `stage` are valid | ✓ | ✓ | ✓ | ✓ |
| manifest has a `question` (a tool: a `job`) | ✓ | ✓ | ✓ | ✓ |
| no `lab-`/`sim-`/`study-` style prefix on the name | ✓ | ✓ | ✓ | ✓ |
| README kind line matches the manifest | ✓ | ✓ | ✓ | ✓ |
| `visibility` is decided (`public` or `private`, not `undecided`), with the date | ✓ | ✓ | | ✓ |
| `CLAUDE.md`, `AGENTS.md`, `LICENSE` exist | ✓ | ✓ | | ✓ |
| `EXPERIMENTS.md` and `RESEARCH.md` exist | ✓ | ✓ | | |
| the manifest names a corpus project (`[corpus] project`) | ✓ | warning | | |
| prereg kit installed (`.agents/kit_ap.lock` with the `prereg` module) | ✓ | ✓ | | |
| every app and local sim listed exists; every app has `index.html` | ✓ | | | |
| a dataset listed has `DATASET.toml`; once selected, it is pinned to a version with a provider, accession, licence and selection criteria | ✓ | | | |
| a calculator listed has `CALCULATOR.md`, and reference values in `reference.csv` from PROBE on (a warning at SKETCH) | ✓ | | | |
| `experiments/` or `data/manifest.json` (the old layout), or an unregistered unit folder | warning | | | |
| every external sim is pinned to a tag, not a branch | ✓ | | | |
| every `[[tools]]` entry has a repo and is pinned to a tag, not a branch | ✓ | ✓ | | |
| holds no research: no `question`, `[corpus]`, `RESEARCH.md`, `EXPERIMENTS.md`, `experiments/`, `preregistrations/` | | | | ✓ |
| `CHANGELOG.md` and `CITATION.cff` exist; one `X.Y.Z` version across `TOOL.toml`, `pyproject.toml`, `CITATION.cff` and a `CHANGELOG.md` heading | | | | ✓ |
| every consumer has a `name`, a `repo` and a non-empty `uses` | | | | ✓ |
| a unit whose `SCOPE.toml` says `stage = "exploratory"` says so in its README (or `CALCULATOR.md`), and has no preregistered experiments | ✓ | ✓ | ✓ | ✓ |
| the corpus is not a submodule | ✓ | ✓ | | ✓ |
| no absolute home-directory paths in tracked text files | warning | warning | warning | warning |

A **workbench** is checked for: a valid manifest (no stage), the README kind line, decided visibility,
`CLAUDE.md` and `AGENTS.md`, the prereg kit, private folders that exist and a private repo when any are
listed, and every study it lists, each checked as a study minus the repo-level rows (unregistered
`studies/` folders are a warning). A study's or workbench's in-repo tool (`[[tools]]` with a `path`) must
exist. A dataset or calculator registered with `adopted = true` predates the unit formats: it must exist,
and a warning says it owes its manifest when it is next worked on.

It exits nonzero on any failure, so it can gate CI. Warnings are printed and do not fail.

---

## 15. Keeping repos current

This section is advice about the tool, not rules `check` enforces.

A repo the scaffold made records what it wrote in `.scaffold.lock`: the release, and a hash of each
file the scaffold **owns**. Those are the CI workflow, the `Makefile`, in a study `shared/workbench.py`, and the
agents in `.claude/agents/` with `.claude/disciplines.md`, and the marked scaffold section of `AGENTS.md`
([`agents/README.md`](agents/README.md)).
Everything else belongs to the repo from the moment it is created.

`scaffold update` moves the owned files to the current release:

| the file is | update |
|---|---|
| missing, in a repo the scaffold made | adds it |
| missing, in a repo that adopted the protocol | reports it; `--adopt FILE` adds it |
| unedited (its hash is in the lock, or it matches what an earlier release wrote) | replaces it |
| an edited CI workflow whose scaffold `ref:` is behind | moves only that line |
| otherwise edited | keeps it and shows the difference; `--adopt FILE` replaces it |

It is a dry run unless given `--apply`, refuses to overwrite uncommitted changes, and leaves the result
uncommitted for review. `scaffold status` gives one line per repo, so a whole organisation can be
surveyed at once. Structural changes, such as moving research out of a tool, are never made
automatically; `check` names them and a person does them.

### New releases reach repos by themselves

The scaffold never goes out and changes other repos. Instead, every release documents how to upgrade to
it, and every repo notices:

- **Each release has a section in [`UPGRADING.md`](UPGRADING.md)**: what `scaffold update` does, and what
  a session does by hand, with the person's go-ahead where a decision is theirs.
- **Each repo records its release** in `.scaffold.lock`.
- **Each session checks.** A session hook in `.claude/settings.json` runs `scaffold version` when a Claude
  Code session starts; the scaffold section of `AGENTS.md` tells ChatGPT, Codex and other repository-aware
  assistants to run it. When
  the repo is behind, it prints the upgrade notes in between, and the session offers to do the upgrade. It
  also says when the local scaffold checkout is behind the latest release on GitHub.

---

## Where this comes from

The rules are drawn from practice written up in: Noble (2009) on organising a computational project;
Wilson et al. (2014, 2017) on scientific computing practice; Sandve et al. (2013) on reproducible
computational research; Nosek et al. (2018) on preregistration; Gould et al. (2026) on adaptive
preregistration for model-based research; Barker et al. (2022) on research software as a citable output;
Milo et al. (2010) on curated biological numbers with their sources (BioNumbers); and Le Novère et al.
(2005) on the minimum description of a quantitative model (MIRIAM). **No published protocol for laying out
a whole research programme across repositories was found**, so the split into studies, work types and a
shared corpus is our own extrapolation from those, and it should be read as one.
