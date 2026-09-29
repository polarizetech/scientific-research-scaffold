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
4. Add `RESEARCH.md` naming the corpus project and claim IDs.
5. Install the preregistration kit (`kit_ap init`, then `kit_ap add experiment-pr-log`). If the repo already
   has a `CLAUDE.md`, the kit adds an `@AGENTS.md` import to it and leaves the rest alone.
6. Add a `LICENSE` if there is none, once the licence is decided.
7. Run the repo's own gate. It must pass exactly as it did before.
8. Optionally, run `scaffold update` to see how the repo's CI workflow and `Makefile` compare with the
   scaffold's. In an adopted repo it adds nothing unless asked (`--adopt FILE`). An edited workflow only
   gets its scaffold `ref:` moved.

### A tool

For a repo that does a job for other repos rather than asking a question, the manifest is `TOOL.toml`
(PROTOCOL.md § 7). Adopting it usually means **moving research out**: measurements, validation write-ups,
`EXPERIMENTS.md` and `experiments/` go to the study that made them, which records them against the tool
release it used. Then make the version agree across `TOOL.toml`, `pyproject.toml`, `CITATION.cff` and
`CHANGELOG.md`, and list each repo that depends on the tool under `[[consumers]]` with what it `uses`.

## 2. Earlier preregistrations stay frozen

A repo that froze analyses under an earlier system (hash files, freeze scripts, a `PREREGISTRATION.md` at the
root) keeps them exactly as frozen. List them in `EXPERIMENTS.md` with a note on which system froze them,
and use the kit for **new** experiments only. Converting a frozen record changes the thing the freeze exists
to protect.

## 3. Moves, later, one at a time

Moving a folder into its default location (`projects/foo` → `apps/v1-foo`) is optional. When it is worth
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
