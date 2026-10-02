# {{name}}

**Kind:** workbench

**Theme.** {{question}}

A workbench in the sense of the [study protocol](https://github.com/polarizetech/scientific-research-scaffold/blob/main/PROTOCOL.md):
where work starts, and where most of it stays. It holds what is general, and the studies that use it.

| | |
|---|---|
| `tools/` | tools any study can use: claim-agnostic, reusable code that has not earned its own repo |
| `sims/` | general simulators |
| `apps/` | general apps: dashboards, browsers, anything not tied to one study's question |
| `studies/<name>/` | one question each, with its own apps, sims, datasets, calculators and tools (`scaffold new study <name> --inside .`) |
| `WORKBENCH.toml` | the manifest: theme, visibility, private folders, and the register of studies |

A study leaves for its own repo when someone outside must see it without the rest, when it must stay
reproducible after the workbench moves on, or when it needs its own releases.
