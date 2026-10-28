#!/usr/bin/env python3
"""Bench sim {{slug}} of {{name}}: the tool against its pinned references (TOOL_VERSIONING.md §1b).

  uv run python run.py            check the pins and tolerances, score, write results/<tool version>.json
  uv run python run.py --verify   check the pins and tolerances only; score nothing

Fill in cases(), outputs() and measure() below. The rest (pins, tolerances, results) is the sim's contract:
it refuses to score against a reference at another commit than SCOPE.toml declares, or before the owner's
tolerances are decided and committed.
"""
import argparse
import datetime
import hashlib
import importlib.metadata
import json
import pathlib
import subprocess
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE.parents[1]
CACHE = HERE / ".references"  # runs = "process" references, fetched at their pinned commit; git-ignored


# ------------------------------------------------------------------------------------------- fill these in

def cases():
    """The sim's fixed inputs, as a dict of case name -> input. Declared here, never chosen after scoring."""
    raise NotImplementedError("declare the sim's cases")


def outputs(who, case, ref=None):
    """What `who` computes on `case`: "tool" for this repo's tool, else a reference name. `ref` is that
    reference's SCOPE.toml table; for runs = "process", ref["path"] is its checkout at the pinned commit. Run
    such a reference as a separate process (subprocess, Octave, a container) and read its output files; never
    import it."""
    raise NotImplementedError("compute each side's output")


def measure(metric, tool_out, ref_out):
    """The value of one tolerances.toml metric (by metric["name"]) for one case."""
    raise NotImplementedError("compute each metric")


# ------------------------------------------------------------------------------------------- the contract

def git(*args, cwd=TOOL):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


def repo_url(repo):
    """owner/name means GitHub; anything else is used as given."""
    if "://" in repo or repo.startswith(("git@", "/", ".")):
        return repo
    return f"https://github.com/{repo}"


def pinned(ref):
    """Check one reference is at its declared commit; return it with "path" set for a process reference."""
    name, tag, commit = ref["name"], ref["tag"], ref["commit"]
    if ref["runs"] == "python":
        try:
            raw = importlib.metadata.distribution(ref["package"]).read_text("direct_url.json")
        except importlib.metadata.PackageNotFoundError:
            raise SystemExit(f"{name}: package {ref['package']!r} is not installed; it is pinned in pyproject.toml")
        vcs = json.loads(raw or "{}").get("vcs_info", {})
        if vcs.get("commit_id") != commit:
            raise SystemExit(f"{name}: installed at {vcs.get('commit_id')}, but SCOPE.toml pins {tag} at {commit}; "
                             "the tag may have moved. Re-run `uv sync`, or ask the owner")
        return dict(ref)
    checkout = CACHE / name
    if not checkout.exists():
        CACHE.mkdir(exist_ok=True)
        code, _ = git("clone", "--quiet", "--depth", "1", "--branch", tag, repo_url(ref["repo"]), str(checkout))
        if code:
            raise SystemExit(f"{name}: could not fetch {ref['repo']} at {tag}")
    _, head = git("rev-parse", "HEAD", cwd=checkout)
    if head != commit:
        raise SystemExit(f"{name}: {checkout} is at {head}, but SCOPE.toml pins {tag} at {commit}; "
                         "delete it to re-fetch, or ask the owner whether the tag moved")
    return {**ref, "path": str(checkout / ref.get("subdirectory", ""))}


def decided_tolerances(names):
    path = HERE / "tolerances.toml"
    tol = tomllib.loads(path.read_text(encoding="utf-8"))
    if not tol.get("decided_by") or not tol.get("decided"):
        raise SystemExit("tolerances.toml: the owner has not decided the bounds (decided_by, decided)")
    metrics = tol.get("metrics", [])
    if not metrics:
        raise SystemExit("tolerances.toml: no [[metrics]]")
    for m in metrics:
        if m.get("reference") not in names:
            raise SystemExit(f"tolerances.toml: metric {m.get('name')!r} names no reference in SCOPE.toml")
        if ("at_most" in m) == ("at_least" in m):
            raise SystemExit(f"tolerances.toml: metric {m.get('name')!r} needs exactly one of at_most, at_least")
    _, changed = git("status", "--porcelain", "--", str(path.relative_to(TOOL)))
    if changed:
        raise SystemExit("tolerances.toml has uncommitted changes; commit the owner's decision before scoring")
    return metrics, hashlib.sha256(path.read_bytes()).hexdigest()


def tool_version():
    return str(tomllib.loads((TOOL / "TOOL.toml").read_text(encoding="utf-8"))["version"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true", help="check pins and tolerances only")
    a = ap.parse_args(argv)
    scope = tomllib.loads((HERE / "SCOPE.toml").read_text(encoding="utf-8"))
    refs = {r["name"]: pinned(r) for r in scope.get("references", [])}
    if not refs:
        raise SystemExit("SCOPE.toml declares no [[references]]")
    metrics, tol_hash = decided_tolerances(set(refs))
    if a.verify:
        print(f"sim {{slug}}: {len(refs)} reference(s) at their pinned commits; tolerances decided")
        return 0

    inputs = cases()
    tool_out = {name: outputs("tool", case) for name, case in inputs.items()}
    ref_out = {r: {name: outputs(r, case, refs[r]) for name, case in inputs.items()} for r in refs}
    scored = []
    for m in metrics:
        values = [float(measure(m, tool_out[c], ref_out[m["reference"]][c])) for c in inputs]
        if "at_most" in m:
            value, ok = max(values), max(values) <= m["at_most"]
        else:
            value, ok = min(values), min(values) >= m["at_least"]
        scored.append({"metric": m["name"], "reference": m["reference"], "value": value,
                       **({"at_most": m["at_most"]} if "at_most" in m else {"at_least": m["at_least"]}),
                       "passed": ok})

    version = tool_version()
    _, commit = git("rev-parse", "HEAD")
    results_rel = (HERE / "results").relative_to(TOOL).as_posix()
    _, dirty = git("status", "--porcelain", "--", ".", f":(exclude){results_rel}")
    result = {
        "sim": "{{slug}}",
        "tool": {"name": "{{name}}", "version": version, "commit": commit, "uncommitted_changes": bool(dirty)},
        "references": [{"name": r["name"], "repo": r["repo"], "tag": r["tag"], "commit": r["commit"]}
                       for r in refs.values()],
        "tolerances_sha256": tol_hash,
        "cases": list(inputs),
        "metrics": scored,
        "passed": all(s["passed"] for s in scored),
        "run_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    out = HERE / "results" / f"{version}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for s in scored:
        bound = f"<= {s['at_most']}" if "at_most" in s else f">= {s['at_least']}"
        print(f"  {'pass' if s['passed'] else 'FAIL'}  {s['metric']} vs {s['reference']}: {s['value']:.6g} {bound}")
    print(f"sim {{slug}} at {{name}} {version}: {'passed' if result['passed'] else 'FAILED'} -> {out.name}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
