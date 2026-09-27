# {{name}}

**Kind:** sim · **Stage:** SKETCH

**What it simulates.** {{question}}

A sim in the sense of the [study protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/main/PROTOCOL.md):
one simulator under adaptive preregistration. Model versions are tags (`model-vX.Y.Z`) in this repo;
experiments are registered in [`EXPERIMENTS.md`](EXPERIMENTS.md), and each is predicted before it is run.

| | |
|---|---|
| `model/` | the simulator |
| `experiments/<EID>/` | `PREREG.md`, `DEVIATIONS.md`, `RESULTS.md`, `ENV.lock`, config, `run.py`, outputs |
| `ASSUMPTIONS.md` | every parameter and where its value came from |
| `CHANGELOG.md` | what changed between model versions, and why |
