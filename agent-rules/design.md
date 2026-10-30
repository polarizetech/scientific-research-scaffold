- **Visual work uses the design system.** Anything visual or user-facing built here (a web UI, a dashboard, a
  chart, a figure or report page, slides) uses {{design_label}}, pinned to `{{design_ref}}`. Its own
  [instructions]({{design_rules}}) are the source of truth: read them before building, follow them over any
  summary here, and link to them rather than copying them into this repo. {{design_source}}
  - Colours, type, spacing and radii come from its tokens, never literals. Don't edit its generated files; a
    change to the look is made upstream, in its token source, and arrives here with a new tag.
  - In anything that could be pushed to a public repo, use only standard visualisation techniques, and demo
    data that is public (licensed, with attribution) or synthetic. When unsure, ask the person before pushing.
  - An app made with `scaffold new app` comes wired to it: its README § Design says what the page links and
    how `serve.py` serves the pinned files. Keep that wiring when you rewrite a page; a yellow banner across
    the page means the design system isn't being served, and says how to fix it.
  - `scaffold check` warns when a page here doesn't load the design system (or its `<body>` class), when it
    is pinned to a branch, or when a page hand-writes a hex colour outside the files listed under
    `[design] allow_hex` in the manifest. The theme pages pin (`data-theme`) is recorded there as `theme`.
    The other points above are advice, not checks.
{{design_house_rules}}