# {{name}}

**Kind:** study · **Stage:** SKETCH

**Question.** {{question}}

A study in the sense of the [study protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/main/PROTOCOL.md):
versioned apps to explore the question, simulations to model it, and preregistered experiments to test it.
Findings go to [`{{corpus_repo}}`](https://github.com/{{corpus_repo}}), not here. See [`RESEARCH.md`](RESEARCH.md).

## Run

```bash
uv sync --frozen
make check
```

## Layout

| | |
|---|---|
| `apps/` | versioned exploratory apps, one folder per version (`scaffold new app <slug>`) |
| `sims/` | simulators still living inside this study |
| `experiments/` | preregistered experiments; the register is [`EXPERIMENTS.md`](EXPERIMENTS.md) |
| `data/manifest.json` | every dataset by DOI or URL plus sha256 |
| `STUDY.toml` | the manifest: stage, visibility, corpus project, apps, sims |
