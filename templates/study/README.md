# {{name}}

**Kind:** study · **Stage:** SKETCH

**Question.** {{question}}

A study in the sense of the [study protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/main/PROTOCOL.md):
apps to explore the question, sims to model it, datasets to test it against, and calculators for its
mathematics, each preregistered where it predicts something.
Findings go to [`{{corpus_repo}}`](https://github.com/{{corpus_repo}}), not here. See [`RESEARCH.md`](RESEARCH.md).

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
| `STUDY.toml` | the manifest: stage, visibility, corpus project, and every app, sim, dataset, calculator and tool |
