# scientific-research-scaffold

A protocol for laying out research across repositories, and `scaffold`, a small CLI that sets up new
studies and simulators in that shape and checks existing ones against it.

- **The protocol:** [`PROTOCOL.md`](PROTOCOL.md)
- **Bringing an existing repo onto it:** [`ADOPTING.md`](ADOPTING.md)

## Two kinds of repo

| | a **study** | a **sim** |
|---|---|---|
| is | one research question, and everything used to pursue it | one simulator, under adaptive preregistration |
| holds | versioned exploratory apps, sims still in development, preregistered experiments, dataset pins | the model, its experiments, its assumptions |
| versions | `apps/v1-*`, `apps/v2-*` folders, and tags | `model-vX.Y.Z` tags, all in one repo |
| findings go to | the shared research corpus, referenced by claim ID | the same |

A sim starts as a folder inside the study that needs it, and moves to its own repo when a second study
uses it, it needs its own releases, or it is shared on its own. Repos are named for their subject, with no
`lab-` or `sim-` prefix: the kind goes in the manifest.

Studies and sims build on four other pieces, named in a **profile** so the protocol itself stays generic:

- a **research corpus**, the one shared record of claims and findings;
- a **preregistration kit**, [adaptive-preregistration](https://github.com/polarizetech/adaptive-preregistration), which installs the predict-first protocol;
- a **design system** for the apps, [polarize-ui](https://github.com/polarizetech/polarize-ui) in ours;
- a **workbench** of shared tools not yet released as libraries.

## Quick start

```bash
git clone https://github.com/polarizetech/scientific-research-scaffold.git
git clone https://github.com/polarizetech/adaptive-preregistration.git   # found automatically as a sibling
cd ~/code
export SCAFFOLD_PROFILE=example   # or your own; there is no built-in default (see below)

scientific-research-scaffold/bin/scaffold new study reef-acoustics \
  -q "Does the sound of a reef track its coral cover?" --visibility private
cd reef-acoustics
../scientific-research-scaffold/bin/scaffold new app site-listener -q "Can a degraded site be heard?"
../scientific-research-scaffold/bin/scaffold new sim sound-propagation -q "How reef sound carries" --inside .
../scientific-research-scaffold/bin/scaffold check
```

`new study` renders the template, makes the first commit, installs the preregistration kit and prints
the `gh repo create` line. It never publishes anything. Visibility is yours to decide: without
`--visibility public|private` the manifest says `undecided`, and `check` fails until you record a decision.

| command | does |
|---|---|
| `scaffold new study <name> -q "..." [--visibility public\|private]` | a new study repo |
| `scaffold new sim <name> -q "..." [--inside STUDY]` | a new sim repo, or a sim folder inside a study |
| `scaffold new app <slug> -q "..."` | the next `apps/vN-<slug>/` in the current study, registered in `STUDY.toml` |
| `scaffold promote-sim sims/<slug>` | split a sim out of a study into its own repo, keeping its history |
| `scaffold check [PATH]` | check a repo against the protocol; nonzero exit on failure, for CI |
| `scaffold profiles` | list profiles |

Requirements: Python 3.9+ and git. No other dependencies.

## Using it for your own work

The protocol is written to be forked. Copy [`profiles/example.toml`](profiles/example.toml), name your own
corpus, preregistration kit, design system and workbench (any can be left empty), and pass
`--profile <name>` (or set `SCAFFOLD_PROFILE`). There is no default profile, so nothing of ours ends up in your
repos by accident. [`profiles/polarizetech.toml`](profiles/polarizetech.toml) is ours, as a worked example.

## Licence

Code is MIT; the protocol and documentation are CC BY 4.0. See [`LICENSE`](LICENSE). To cite it, see
[`CITATION.cff`](CITATION.cff).
