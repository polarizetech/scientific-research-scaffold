#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Serve this app on localhost, with the design system mapped in through an allow-list.

The design system's files are read from a local checkout of {{design_repo}} (DESIGN_DIR, default: beside this
repo) at the pinned tag DESIGN_REF, whatever branch the checkout has out, so the app looks the way the pin says.
When they can't be read, the page shows a banner saying why and how to fix it, instead of quietly going unstyled.

Beyond localhost, apps are viewed through a tailnet gateway at TAILNET_URL/<slug>/<version>/. TAILNET_URL is
read from the environment first; the default below comes from the profile and is empty when it names none.
The URL ends in the version: a bare / (or /<slug>/) redirects to <version>/, and the /<slug> and /<version>
prefixes are stripped, so the same relative paths work locally, behind the gateway and directly.
"""
import functools
import http.server
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PORT = int(os.environ.get("PORT", "{{port}}"))
SLUG = "{{slug}}"
VERSION = "{{version}}"
TAILNET_URL = os.environ.get("TAILNET_URL", "{{tailnet_url}}").rstrip("/")
DESIGN = Path(os.environ.get("DESIGN_DIR", HERE.parents[3] / "{{design_name}}")).expanduser()
DESIGN_REPO = "{{design_repo}}"
DESIGN_REF = os.environ.get("DESIGN_REF", "{{design_ref}}")  # empty: the checkout's files as they are
DESIGN_CSS = "{{design_css}}"

# Named files only: never mount the design system's directory.
DESIGN_PUBLIC = {
    f"/design/{DESIGN_CSS}": DESIGN_CSS,
    "/design/design.js": "design.js",
    "/design/tokens.json": "tokens.json",
    "/design/icons/polarize-icons.svg": "icons/polarize-icons.svg",
}
FONT = re.compile(r"/design/(fonts/[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\.woff2?)")  # the stylesheet's own fonts
TYPES = {".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml",
         ".woff2": "font/woff2", ".woff": "font/woff"}


def design_path(key):
    """The design-system file a request maps to, or None: named files and its fonts only."""
    if key in DESIGN_PUBLIC:
        return DESIGN_PUBLIC[key]
    m = FONT.fullmatch(key)
    return m.group(1) if m else None


@functools.lru_cache(maxsize=None)
def design_file(rel):
    """A design-system file at the pinned tag (or as checked out, with no tag), or None."""
    if DESIGN_REF:
        r = subprocess.run(["git", "-C", str(DESIGN), "show", f"{DESIGN_REF}:{rel}"], capture_output=True)
        return r.stdout if r.returncode == 0 else None
    f = DESIGN / rel
    return f.read_bytes() if f.is_file() else None


def design_problem():
    """Why the design system can't be served, with the fix; empty when it can."""
    if not DESIGN_REPO or design_file(DESIGN_CSS) is not None:
        return ""
    if not DESIGN.is_dir():
        return (f"design system not found at {DESIGN}: git clone https://github.com/{DESIGN_REPO} {DESIGN} "
                "(or set DESIGN_DIR)")
    if DESIGN_REF:
        return f"{DESIGN} has no {DESIGN_REF}:{DESIGN_CSS}: git -C {DESIGN} fetch --tags"
    return f"{DESIGN} has no {DESIGN_CSS}"


def banner(problem):
    """A stylesheet that puts the problem at the top of the page, so nobody mistakes it for the design."""
    text = problem.replace("\\", "\\\\").replace('"', '\\"')
    return (f'body::before{{content:"{text}";display:block;padding:12px 16px;font:14px/1.4 monospace;'
            'background:yellow;color:black;white-space:pre-wrap}').encode()


def unmount(path):
    """Strip /<slug> (if a proxy left it) and then /<version>, so /v1/x and /<slug>/v1/x are /x."""
    for prefix in (f"/{SLUG}", f"/{VERSION}"):
        if path == prefix:
            path = "/"
        elif path.startswith(prefix + "/"):
            path = path[len(prefix):]
    return path


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def translate_path(self, path):
        return super().translate_path(unmount(path.split("?", 1)[0].split("#", 1)[0]))

    def send_design(self, rel):
        body = design_file(rel)
        if body is None and rel == DESIGN_CSS:
            body = banner(design_problem())
        if body is None:
            self.send_error(404, f"{rel} not found in the design system")
            return
        self.send_response(200)
        self.send_header("Content-Type", TYPES.get(Path(rel).suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        raw = self.path.split("?", 1)[0]
        if raw in ("/", f"/{SLUG}/", f"/{VERSION}", f"/{SLUG}/{VERSION}"):
            self.send_response(302)  # relative, so it lands on .../<slug>/<version>/ through the gateway too
            self.send_header("Location", f"{VERSION}/")
            self.end_headers()
            return
        rel = design_path(unmount(raw.split("#", 1)[0]))
        if rel:
            self.send_design(rel)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    problem = design_problem()
    if problem:
        print(f"WARNING {problem}\nThe page shows this banner until it is fixed.", file=sys.stderr)
    elif DESIGN_REPO:
        print(f"design system: {DESIGN} at {DESIGN_REF or 'its checked-out files'}")
    print(f"http://127.0.0.1:{PORT}/{VERSION}/")
    if TAILNET_URL:
        print(f"{TAILNET_URL}/{SLUG}/{VERSION}/  (once the tailnet gateway lists this app)")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
