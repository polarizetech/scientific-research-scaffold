# {{name}}

**Kind:** study · **Stage:** SKETCH

**Question.** {{question}}

A study in the sense of the [study protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/main/PROTOCOL.md):
apps to explore the question, sims to model it, datasets to test it against, and calculators for its
mathematics, each preregistered where it predicts something.
Findings go to [`{{corpus_repo}}`](https://github.com/{{corpus_repo}}), not here. See [`RESEARCH.md`](RESEARCH.md).
`HYPOTHESIS.toml` links every unit to accepted study elements. The managing agent runs
`scaffold sync-hypothesis` after relevant claim, evidence or finding changes and carries affected-unit review
state into each unit's `SCOPE.toml`.

## Run

```bash
uv sync --frozen
make check
```

## Layout

| | |
|---|---|
| `apps/` | interactive exploration and demonstration, one folder per version (`scaffold new app <slug>`) |
| `sims/` | simulators still living inside this study (`scaffold new sim <slug> --inside .`) |
| `datasets/` | dataset analyses: the data pinned through dataset-fetch, the analysis preregistered (`scaffold new dataset <slug>`) |
| `calculators/` | the study's mathematics as tested code (`scaffold new calculator <slug>`) |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | the register of every preregistration, wherever it lives |
| [`HYPOTHESIS.toml`](HYPOTHESIS.toml) | the person's hypothesis, decomposed into evidence-backed or falsifiable steps and integrations |
| [`RESEARCH.md`](RESEARCH.md) | links each hypothesis element and experiment to the canonical corpus project |
| `STUDY.toml` | the manifest: stage, visibility, corpus project, and every app, sim, dataset, calculator and tool |
