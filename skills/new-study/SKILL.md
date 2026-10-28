---
name: new-study
description: Set up a new research study, simulator or tool repo with scientific-research-scaffold, or bring an existing one onto the study protocol. Use when the user says "new study", "start a study", "new sim", "new simulator", "new tool", or asks to make a repo follow the study protocol.
---

# New study or sim

Explicit user instructions take precedence over this workflow. This skill needs filesystem and shell access
to the target checkout; if they are unavailable, explain that boundary instead of pretending files were made.

Follow `PROTOCOL.md` in scientific-research-scaffold. Find the scaffold checkout first (a sibling of the
current repo, or ask); never guess a home-directory path.

1. **Ask for what only the person can decide:** the subject name (no `lab-`/`sim-` prefix), and whether it
   is a study, a sim or a tool. A study or a tool starts exploratory, from the person's goal and a rough idea
   of how to get there; no claim is asked for. A sim needs its one-sentence question. If a sim: its own repo,
   or `--inside` an existing study? The default is inside, until a second study needs it (PROTOCOL.md § 7).
   Only if the person already has a hypothesis, take it in their own words and do not rewrite it. Which
   profile? (There is no default; `$SCAFFOLD_PROFILE` may already name one.)
2. **Create it:** `scaffold new study <name> --goal "<goal>" --approach "<rough approach>" --profile <p>`,
   `scaffold new tool <name> --goal "<what it does for other repos>" --approach "<rough approach>" --profile <p>`,
   or `scaffold new sim <name> -q "<question>" --profile <p>`. With the person's hypothesis, a study starts from
   it instead: `scaffold new study <name> -q "<question>" --hypothesis "<person's exact words>"`. Pass
   `--visibility public|private` only if the person has already decided it; never pick one for them.
   Report what it printed, including whether the preregistration kit was installed.
3. **Do not create the GitHub repo or choose visibility.** If visibility is `undecided`, ask, and record
   the answer and today's date in the manifest. Then show the `gh repo create` line and ask.
4. **Size the goal with the person.** Talk it through, back and forth: is the goal one study's or tool's worth,
   or should it be broken up? Propose a split when it is too big and let the person decide. Record
   `scope = "one"` or `scope = "split: a, b"` and `scope_decided` (in `HYPOTHESIS.toml` for a study, under
   `[exploration]` in `SCOPE.toml` for a tool). After a split, create each piece the same way.
5. **Map a study's hypothesis, once the person has one:** put it in `HYPOTHESIS.toml` verbatim and set
   `mode = "hypothesis"`. Apply the
   relevant specialist briefs; the researcher uses the profile's retrieval tool before literature/evidence
   answers. Propose falsifiable steps and integrations for the person's decision. Each element is either
   established with verified corpus evidence, or has a goal and what would count against it. Reconcile the
   canonical corpus project overview and `RESEARCH.md`. Leave agent proposals marked proposed until the person
   accepts the exact element revision; only accepted elements can derive a unit's scope.
6. **Check it:** `scaffold check`. It must pass before anything else is added.

To bring existing repos up to the current scaffold, run `scaffold status <paths>` for the overview, then
`scaffold update <repo>` (a dry run) for each repo, and show the person the plan. Run `--apply` only with
their go-ahead, and never pass `--adopt` for a file they have not agreed to lose their edits in. Leave the
result uncommitted for them to review.

**Adding work to a study.** When someone wants to explore or demonstrate something (an app), model it (a
sim), test it against existing data (a dataset) or pin down its mathematics (a calculator), create the unit
with `scaffold new app|sim|dataset|calculator <slug> -q "..." --hypothesis-element <ID>` (repeat the flag
for multiple elements) and follow its section of `PROTOCOL.md`, including what it needs before it starts.
Derive its scope from those elements with the person. Preregistrations live in the unit they test. When an
element or evidence revision changes, run `scaffold sync-hypothesis`. Under `impact_management =
"agent-managed"`, routine linking and queueing use the person's standing delegation: the agent reviews each
affected unit and records one of the dispositions allowed by `HYPOTHESIS.toml`, bound to the exact stale revision
and fingerprints. Ask again only for meaning-changing hypothesis/falsifier wording, an unrecorded scientific
choice, safety, publication scope or another decision the standing policy does not cover.

For an existing repo, follow `ADOPTING.md`: additive first (manifest with `path` entries, kind line,
`HYPOTHESIS.toml`, `RESEARCH.md`, the kit), and the repo's own gate must pass exactly as before. Add legacy
units as `unmapped`, then use `scaffold link-hypothesis` after reading each unit's recorded scope and purpose;
never infer a link from its folder name. Maintain the corpus project overview as the reverse impact index across
studies and record unavailable affected repos as pending.
