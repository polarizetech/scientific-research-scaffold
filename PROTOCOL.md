<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# The study protocol

How a piece of research is laid out across repositories: what a **study** is, what a **sim** is, what each
one contains, what it depends on and how, and how a sim graduates out of a study into its own repo.

This document is generic. Everything specific to one organisation (which repo holds the research corpus,
which design system the apps use, which workbench holds shared tools) lives in a **profile**
(`profiles/*.toml`). Fork the repo, write your own profile, and the rest applies unchanged.

`bin/scaffold` creates repos in this shape and checks existing ones against it. The rules below are
what `scaffold check` enforces; where a rule is advice rather than a check, it says so.

---

## 0. The idea in one paragraph

A study is **one question, pursued with whatever it takes**: small versioned apps to explore it,
simulations to model it, preregistered experiments to test it, and datasets to test it against. Its
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

A profile fills five **roles** that studies and sims depend on but never contain:

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

- `kind = "study"` (or `"sim"`) in the manifest, and
- the kind line directly under the README's title: `**Kind:** study · **Stage:** SKETCH`.

An index of which repo is which kind is kept outside the repos (the organisation's site or profile), not
in their names.

---

## 2. The manifest

Every study has `STUDY.toml`; every sim has `SIM.toml`. It is the machine-readable register for the repo.

```toml
kind = "study"
name = "reef-acoustics"
question = "Does the sound of a reef track its coral cover across survey sites?"
stage = "SKETCH"                 # SKETCH | PROBE | BENCH | SHIPPED (§ 9)
visibility = "private"           # decided, never defaulted
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
```

Experiments are registered in `EXPERIMENTS.md` (the prereg kit's register), not duplicated here.

**`path` overrides the default location.** It is how an existing repo adopts this protocol without moving
working code (see [`ADOPTING.md`](ADOPTING.md)). A new repo leaves it out.

---

## 3. What a study contains

```
<study>/
  README.md            title, kind line, the question, how to run it
  CLAUDE.md            "@AGENTS.md", then anything specific to this study
  AGENTS.md            instructions every coding assistant reads (managed by the prereg kit)
  STUDY.toml           the manifest (§ 2)
  RESEARCH.md          which corpus project and claim IDs this study bears on
  EXPERIMENTS.md       the experiment register
  LICENSE              code MIT; text and figures CC BY 4.0
  CITATION.cff
  pyproject.toml + uv.lock   every library and external sim pinned to a tag
  Makefile             `make check` runs everything CI runs
  apps/<vN-slug>/      versioned exploratory apps (§ 5)
  sims/<slug>/         simulators still living inside the study (§ 6)
  experiments/<EID>/   preregistered experiments (§ 7)
  data/manifest.json   every dataset by DOI or URL plus sha256; raw data is gitignored and fetched
  shared/workbench.py  the one resolver for workbench tools (§ 4)
  .agents/             the prereg kit's protocols and tools
```

### Apps are for exploring; experiments are for testing

An app is a small piece of software for trying out part of the question by hand: playing a stimulus,
scrubbing through a recording, seeing whether an idea looks like anything. It answers "is this worth
testing?" A result from an app is never a finding. A finding comes from a preregistered experiment.

---

## 4. Dependencies

The direction is fixed: a study depends on sims and libraries; sims depend on libraries; nothing depends
on a study. Nobody imports the corpus.

| depending on | how | never |
|---|---|---|
| a library or an external sim | a pinned **tag** in `pyproject.toml` and `uv.lock` | a branch, a sibling folder, an editable install, for anything a result is quoted from |
| the corpus | its claim IDs and links, in `RESEARCH.md` | a submodule, a copy, an import |
| a dataset | DOI or URL plus sha256 in `data/manifest.json` | committed bulk data |
| a workbench tool | `shared/workbench.py`, for local development only | an absolute path |
| the design system | served through an allow-list by each app's `serve.py` (§ 5) | a CDN |

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

**No absolute home-directory paths, anywhere.** A path that names one person's machine is a result nobody
else can regenerate. `scaffold check` flags them.

---

## 5. Apps

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

## 6. Sims

A sim is a simulator under adaptive preregistration. Its layout is the prereg kit's:

```
<sim>/
  README.md  CLAUDE.md  AGENTS.md  SIM.toml  LICENSE  CITATION.cff
  model/               the simulator, tagged model-vX.Y.Z when it changes
  experiments/<EID>/   PREREG.md, DEVIATIONS.md, RESULTS.md, ENV.lock, config, run.py, outputs/
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

## 7. Preregistration

Every experiment, in a study or a sim, follows the prereg kit's protocol:

1. `PREREG.md` is written and tagged `<EID>-prereg` **before** the first run that could be quoted.
2. Predictions are risky, numeric and directional, and each says what would count against it.
3. A failure closes the version; it does not edit it.
4. Every change after the tag goes in `DEVIATIONS.md`, with whether the outcome was already known.
5. Exploratory work stays under `exploratory/`, and says so.

The kit is installed, not linked: `kit_ap init` copies the protocols into `.agents/` and pins the kit's
commit in `.agents/kit_ap.lock`. `scaffold new` runs it for you when it can find the kit.

A repo that already froze analyses under an **earlier** preregistration system keeps them exactly as
frozen. It uses the kit for new experiments only, and lists the earlier ones in `EXPERIMENTS.md` with a
note saying which system froze them. Converting a frozen record would change the thing the freeze exists
to protect.

---

## 8. Research

Findings are written to the **corpus**, in the study's project folder there. The study carries only
`RESEARCH.md`: the corpus project, the claim prefix, and the claim IDs each experiment bears on.

- **A study never raises a claim's tier.** The corpus decides what a result does to a claim.
- **The corpus is never a submodule of a study.** Two working copies of one corpus drift.
- A sim that has no corpus project yet says so in its `RESEARCH.md` rather than inventing one.

---

## 9. Stages

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

## 10. What `scaffold check` enforces

| check | study | sim | sim inside a study |
|---|---|---|---|
| manifest parses, and `kind`, `name`, `question`, `stage` are valid | ✓ | ✓ | ✓ |
| no `lab-`/`sim-`/`study-` style prefix on the name | ✓ | ✓ | ✓ |
| README kind line matches the manifest | ✓ | ✓ | ✓ |
| `visibility` is set, with the date it was decided | ✓ | ✓ | |
| `CLAUDE.md`, `AGENTS.md`, `LICENSE`, `EXPERIMENTS.md` exist | ✓ | ✓ | |
| prereg kit installed (`.agents/kit_ap.lock` with the `prereg` module) | ✓ | ✓ | |
| `RESEARCH.md` exists and names a corpus project | ✓ | ✓ | |
| every app and local sim listed exists; every app has `index.html` | ✓ | | |
| every external sim is pinned to a tag, not a branch | ✓ | | |
| the corpus is not a submodule | ✓ | ✓ | |
| no absolute home-directory paths in tracked text files | warning | warning | warning |

It exits nonzero on any failure, so it can gate CI. Warnings are printed and do not fail.

---

## Where this comes from

The rules are drawn from practice written up in: Noble (2009) on organising a computational project;
Wilson et al. (2014, 2017) on scientific computing practice; Sandve et al. (2013) on reproducible
computational research; Nosek et al. (2018) on preregistration; Gould et al. (2026) on adaptive
preregistration for model-based research; and Barker et al. (2022) on research software as a citable
output. **No published protocol for laying out a whole research programme across repositories was
found**, so the split into studies, sims and a shared corpus is our own extrapolation from those, and it
should be read as one.
