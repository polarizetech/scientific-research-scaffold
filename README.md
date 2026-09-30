# scientific-research-scaffold

A protocol for laying out research across repositories, and `scaffold`, a small CLI that sets up new
studies, simulators and tools in that shape and checks existing ones against it.

- **The protocol:** [`PROTOCOL.md`](PROTOCOL.md)
- **Bringing an existing repo onto it:** [`ADOPTING.md`](ADOPTING.md)

## Three kinds of repo

| | a **study** | a **sim** | a **tool** |
|---|---|---|---|
| is | one research question, and everything used to pursue it | one simulator, under adaptive preregistration | one job done for other repos: an instrument, a recorder, a service, a library |
| holds | versioned exploratory apps, sims still in development, preregistered experiments, dataset pins | the model, its experiments, its assumptions | the tool, and the list of repos that depend on it and what they use |
| versions | `apps/v1-*`, `apps/v2-*` folders, and tags | `model-vX.Y.Z` tags, all in one repo | `vX.Y.Z` tags, one version said the same everywhere |
| findings go to | the shared research corpus, referenced by claim ID | the same | none: a tool holds no research |

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
git clone --recurse-submodules https://github.com/polarizetech/scientific-research-scaffold.git
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
| `scaffold new tool <name> -j "..."` | a new tool repo: a job, not a question |
| `scaffold new app <slug> -q "..."` | the next `apps/vN-<slug>/` in the current study, registered in `STUDY.toml` |
| `scaffold promote-sim sims/<slug>` | split a sim out of a study into its own repo, keeping its history |
| `scaffold check [PATH]` | check a repo against the protocol; nonzero exit on failure, for CI |
| `scaffold status [PATH ...]` | one line per repo: kind, stage, scaffold release, CI ref, check result, pending update |
| `scaffold update [PATH] [--apply] [--adopt FILE]` | bring the files the scaffold owns up to this release; a dry run unless `--apply` |
| `scaffold usage [PATH ...] [--days N] [--all]` | tokens and API-equivalent cost per repo from Claude Code and Codex logs, and Codex's plan limits |
| `scaffold profiles` | list profiles |

### Agents

Every repo gets specialist agents in `.claude/agents/`: a scout, a computational engineer, a designer, a
frontend developer, a researcher, an analyst and a science writer. A sim, which has no UI, gets no designer
or frontend developer. A session hands each task to the one whose description fits. Each agent starts on
a cheap model and is escalated on a signal, and agents pass short handoffs, not transcripts
([`agents/COORDINATION.md`](agents/COORDINATION.md)). Codex gets the same roles through a section of
`AGENTS.md`. `scaffold usage` shows what each repo actually costs. The agents live in their own repo,
[scientific-research-agents](https://github.com/polarizetech/scientific-research-agents), included here as a
submodule pinned to a tag: clone with `--recurse-submodules`, or run `git submodule update --init`.

`skills/new-study/` is a Claude Code skill for creating and adopting studies with this scaffold: copy it to
`~/.claude/skills/` (for you) or `.claude/skills/` (for one repo).

### Keeping repos current

`scaffold status ~/code/*` surveys every repo at once. `scaffold update` brings one repo's
**scaffold-owned files** (the CI workflow, the `Makefile`, `shared/workbench.py`, the agents) up to this release,
and never touches anything else. It replaces a file only when nobody has edited it since the scaffold
wrote it, which it knows from `.scaffold.lock`, or by matching the file against what each earlier
release would have written. An edited CI workflow gets only its scaffold `ref:` moved. Any other
edited file is kept, with the difference shown; `--adopt FILE` replaces it anyway. It prints a dry
run first, writes nothing without `--apply`, refuses to overwrite uncommitted work, and never commits.

Requirements: Python 3.9+ and git. No other dependencies.

## Using it for your own work

The protocol is written to be forked. Copy [`profiles/example.toml`](profiles/example.toml), name your own
corpus, preregistration kit, design system and workbench (any can be left empty), and pass
`--profile <name>` (or set `SCAFFOLD_PROFILE`). There is no default profile, so nothing of ours ends up in your
repos by accident. [`profiles/polarizetech.toml`](profiles/polarizetech.toml) is ours, as a worked example.

## Licence

Code is MIT; the protocol and documentation are CC BY 4.0. See [`LICENSE`](LICENSE). To cite it, see
[`CITATION.cff`](CITATION.cff).
