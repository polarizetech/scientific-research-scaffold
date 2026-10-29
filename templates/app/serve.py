#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Serve this app on localhost, with the design system mapped in through an allow-list.

The design system is optional: if it cannot be found the app still works, unstyled.
Set DESIGN_DIR to a checkout of {{design_repo}} to style it.

Beyond localhost, apps are viewed through a tailnet gateway at TAILNET_URL/<slug>/. TAILNET_URL is read
from the environment first; the default below comes from the profile and is empty when it names none.
"""
import http.server
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "{{port}}"))
SLUG = "{{slug}}"
TAILNET_URL = os.environ.get("TAILNET_URL", "{{tailnet_url}}").rstrip("/")
DESIGN = Path(os.environ.get("DESIGN_DIR", HERE.parents[3] / "{{design_name}}")).expanduser()

# Named files only: never mount the design system's directory.
DESIGN_PUBLIC = {
    "/design/{{design_css}}": DESIGN / "{{design_css}}",
    "/design/design.js": DESIGN / "design.js",
    "/design/tokens.json": DESIGN / "tokens.json",
    "/design/icons/polarize-icons.svg": DESIGN / "icons" / "polarize-icons.svg",
}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def translate_path(self, path):
        key = path.split("?", 1)[0].split("#", 1)[0]
        if key in DESIGN_PUBLIC:
            return str(DESIGN_PUBLIC[key])
        return super().translate_path(path)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    if not (DESIGN / "{{design_css}}").exists():
        print(f"design system not found at {DESIGN}; serving unstyled (set DESIGN_DIR)", file=sys.stderr)
    print(f"http://127.0.0.1:{PORT}/")
    if TAILNET_URL:
        print(f"{TAILNET_URL}/{SLUG}/  (once the tailnet gateway lists this app)")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
