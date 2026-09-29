---
name: new-study
description: Set up a new research study, simulator or tool repo with scientific-research-scaffold, or bring an existing one onto the study protocol. Use when the user says "new study", "start a study", "new sim", "new simulator", "new tool", or asks to make a repo follow the study protocol.
---

# New study or sim

Follow `PROTOCOL.md` in scientific-research-scaffold. Find the scaffold checkout first (a sibling of the
current repo, or ask); never guess a home-directory path.

1. **Ask for what only the person can decide:** the subject name (no `lab-`/`sim-` prefix), and whether it
   is a study, a sim or a tool. A study or sim needs its one-sentence question; a tool needs its job
   instead, since it holds no research (PROTOCOL.md § 7). If a sim: its own repo, or `--inside` an existing study?
   The default is inside, until a second study needs it (PROTOCOL.md § 6). Which profile? (There is no
   default; `$SCAFFOLD_PROFILE` may already name one.)
2. **Create it:** `scaffold new study|sim <name> -q "<question>" --profile <p>`, or
   `scaffold new tool <name> -j "<job>" --profile <p>`. Pass
   `--visibility public|private` only if the person has already decided it; never pick one for them.
   Report what it printed, including whether the preregistration kit was installed.
3. **Do not create the GitHub repo or choose visibility.** If visibility is `undecided`, ask, and record
   the answer and today's date in the manifest. Then show the `gh repo create` line and ask.
4. **Check it:** `scaffold check`. It must pass before anything else is added.

For an existing repo, follow `ADOPTING.md`: additive first (manifest with `path` entries, kind line,
RESEARCH.md, the kit), and the repo's own gate must pass exactly as before.
