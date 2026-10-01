# scientific-research-scaffold

The study protocol (`PROTOCOL.md`), its adoption guide (`ADOPTING.md`), and `bin/scaffold`.

**This repo is meant to be read and forked by people outside the organisation that wrote it.** Keep it
generic: anything specific to one organisation belongs in `profiles/<name>.toml`, never in the protocol,
the templates or the CLI. The polarizetech profile is a worked example, not the default of the protocol.

- `bin/scaffold` is stdlib only and runs on Python 3.9+. `tomllib` is used when present; the small built-in
  parser covers the rest, and `tests/` asserts the two agree on every profile.
- Every rule the protocol calls enforced has a check in `check_repo()` and a test. A rule that is advice
  says so in `PROTOCOL.md`.
- Templates use `{{placeholders}}`; an unknown placeholder is an error, not a blank.
- `scaffold new` never publishes: it prints the `gh repo create` line and leaves visibility to the person.
- Don't install the preregistration kit into this repo itself; it is a tool, not a study.
- A release that changes what repos contain adds its section to `UPGRADING.md`: what `scaffold update` does,
  and what a session does by hand. `tests/` fails a release without one.
- The agents are a submodule (`agents/`, scientific-research-agents) pinned to a tag; change them there.

Tests: `python3 -m unittest discover -v tests`
