<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# Adopting the protocol in an existing repo

An existing study already has working code, frozen results and gates that pass. Adopting the protocol must
not break any of them, so adoption is **additive first, moves later**.

## 1. Add, don't move

1. Run `scaffold check`. The failures are the to-do list.
2. Add the manifest (`STUDY.toml` or `SIM.toml`). For anything that already exists somewhere other than the
   default location, give its `path`:

   ```toml
   [[apps]]
   version = "v1"
   slug = "first-explorer"
   path = "projects/first-explorer"   # stays where it is
   status = "superseded"
   ```

3. Add the kind line under the README's title: `**Kind:** study · **Stage:** SKETCH`.
4. For a study, add `HYPOTHESIS.toml`: preserve the person's hypothesis verbatim, then use the relevant
   specialist profiles and retrieval tool to propose falsifiable steps and integrations for the person's
   decision. Mark established elements with verified corpus evidence; give every other element a goal and
   what would count against it. Keep agent proposals marked `proposed` until the person accepts the exact
   revision. Register existing units as `unmapped`. After elements are accepted, the managing agent reads each
   unit's recorded scope and purpose and uses `scaffold link-hypothesis` to state its role and associations; it
   never infers them from a folder name or replaces an existing narrower claim. Set the study's standing
   `impact_management` policy, and run `scaffold sync-hypothesis` after relevant changes.
   Add `RESEARCH.md` naming the corpus project and linking the evidence IDs. A sim adds `RESEARCH.md` naming
   its corpus project and claim IDs.
5. Install the preregistration kit (`kit_ap init`, then `kit_ap add experiment-pr-log`). If the repo already
   has a `CLAUDE.md`, the kit adds an `@AGENTS.md` import to it and leaves the rest alone.
6. Add a `LICENSE` if there is none, once the licence is decided.
7. Run the repo's own gate. It must pass exactly as it did before.
8. Optionally, run `scaffold update` to see how the repo's CI workflow and `Makefile` compare with the
   scaffold's. In an adopted repo it adds nothing unless asked (`--adopt FILE`). An edited workflow only
   gets its scaffold `ref:` moved.

### A tool

For a repo that does a job for other repos rather than asking a question, the manifest is `TOOL.toml`
(PROTOCOL.md § 8). Adopting it usually means **moving research out**: measurements, validation write-ups,
`EXPERIMENTS.md` and `experiments/` go to the study that made them, which records them against the tool
release it used. Then make the version agree across `TOOL.toml`, `pyproject.toml`, `CITATION.cff` and
`CHANGELOG.md`, and list each repo that depends on the tool under `[[consumers]]` with what it `uses`.

### Work-type folders

A study that has an `experiments/` folder or a `data/manifest.json` keeps them where they are. `check` warns
about both, as the old layout, and nothing more. New preregistrations go in the unit they test
(`<unit>/preregistrations/<EID>/`); new datasets get `scaffold new dataset`. Move an old experiment only when
it is worth doing, one commit per move, and keep it listed in `EXPERIMENTS.md` either way.

### A design system

The protocol does not choose a look. An organisation that has a design system names it in its profile;
one that has none leaves `[design]` empty and nothing changes:

```toml
[design]
name = "our-ui"
package = "@our-org/our-ui"                  # for build-based apps; leave empty if there is no package
repo = "our-org/our-ui"                      # its git source
ref = "v2.1.0"                               # a release tag, never a branch
rules = "https://github.com/our-org/our-ui/blob/v2.1.0/README.md"   # its own instructions, at that tag
css = "our-ui.css"                           # the stylesheet a zero-build page links
js = ""
house_rules = []                             # optional reminders, each naming the file that holds the rule
```

`scaffold` refuses a profile whose `ref` is a branch, or whose `rules` URL names a different tag. Keep the
design system's rules in the design system: `house_rules` point at them, and never restate them in full.
New repos then get the agent rule, a README **Design** section and a `[design]` table in the manifest. In
an existing repo, add the README section and the `[design]` table by hand (`theme = ""`, `allow_hex = []`),
then read `scaffold check`'s design warnings: list a file that has to keep its colours (a vendored chart
library, an exported figure) under `allow_hex`, and move the rest to tokens when the page is next changed.

## 2. Earlier preregistrations stay frozen

A repo that froze analyses under an earlier system (hash files, freeze scripts, a `PREREGISTRATION.md` at the
root) keeps them exactly as frozen. List them in `EXPERIMENTS.md` with a note on which system froze them,
and use the kit for **new** experiments only. Converting a frozen record changes the thing the freeze exists
to protect.

## 3. Moves, later, one at a time

Moving a folder into its default location (`projects/foo` → `apps/foo/v1`) is optional. When it is worth
doing, do it as one commit per move, with the gate run before and after, and update the manifest's `path`
in the same commit.

## 4. Renaming a repo to drop a prefix

GitHub redirects the old URL, so clones, submodules and links keep working. What it does not fix:

- **absolute paths** that name the local folder (scripts, launch agents, editable installs);
- **names written into outputs** (provenance records, package names). Change the code that writes them;
  leave records that were already written;
- **URLs a site derives from the repo name**, which need a redirect;
- **text** that names the old repo. Update docs; leave dated logs, conversation records and history as they
  are.

`grep -rn "<old-name>"` across every checkout on the machine before and after is the check.
