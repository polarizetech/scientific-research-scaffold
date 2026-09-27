---
name: new-study
description: Set up a new research study or simulator repo with scientific-research-scaffold, or bring an existing one onto the study protocol. Use when the user says "new study", "start a study", "new sim", "new simulator", or asks to make a repo follow the study protocol.
---

# New study or sim

Follow `PROTOCOL.md` in scientific-research-scaffold. Find the scaffold checkout first (a sibling of the
current repo, or ask); never guess a home-directory path.

1. **Ask for what only the person can decide:** the subject name (no `lab-`/`sim-` prefix), the one-sentence
   question, and whether it is a study or a sim. If a sim: its own repo, or `--inside` an existing study?
   The default is inside, until a second study needs it (PROTOCOL.md § 6).
2. **Create it:** `scaffold new study|sim <name> -q "<question>" [--profile <p>]`. Report what it printed,
   including whether the preregistration kit was installed.
3. **Do not create the GitHub repo or choose visibility.** Show the `gh repo create` line and ask.
4. **Check it:** `scaffold check`. It must pass before anything else is added.

For an existing repo, follow `ADOPTING.md`: additive first (manifest with `path` entries, kind line,
RESEARCH.md, the kit), and the repo's own gate must pass exactly as before.
