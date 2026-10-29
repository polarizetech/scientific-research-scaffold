# SPDX-License-Identifier: MIT
"""End-to-end: render every template, check it passes; break it, check it fails."""
import importlib.machinery
import importlib.util
import hashlib
import io
import json
import os
import re
import shutil
import runpy
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_loader = importlib.machinery.SourceFileLoader("scaffold", str(ROOT / "bin" / "scaffold"))
_spec = importlib.util.spec_from_loader("scaffold", _loader)
scaffold = importlib.util.module_from_spec(_spec)
_loader.exec_module(scaffold)

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = scaffold.main(list(argv))
    return code, out.getvalue() + err.getvalue()


def fake_kit(repo):
    """Stand in for `kit_ap init`: the tests exercise this scaffold, not the kit."""
    (repo / ".agents").mkdir(exist_ok=True)
    (repo / ".agents" / "kit_ap.lock").write_text('{"modules": ["core", "prereg"]}')
    add_kit_block(repo)


def add_kit_block(repo):
    """The kit adds its own marked section to AGENTS.md and leaves the rest of the file alone."""
    path = repo / "AGENTS.md"
    old = path.read_text() if path.exists() else ""
    path.write_text("<!-- kit_ap:start -->\n<!-- kit_ap:end -->\n\n" + old)


class Scaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._env = {k: os.environ.get(k) for k in GIT_ENV}
        os.environ.update(GIT_ENV)
        self._env["KIT_AP"] = os.environ.pop("KIT_AP", None)
        self._env["SCAFFOLD_PROFILE"] = os.environ.pop("SCAFFOLD_PROFILE", None)
        self._env["TAILNET_URL"] = os.environ.pop("TAILNET_URL", None)

    def tearDown(self):
        shutil.rmtree(self.tmp)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def study(self, name="colony", profile="polarizetech", visibility="private"):
        vis = ["--visibility", visibility] if visibility else []
        code, out = run("new", "study", name, "-q", "Does it?", "--hypothesis", "Does it?",
                        "--dir", str(self.tmp), "--profile", profile,
                        *vis, "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / name
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        hypothesis = repo / "HYPOTHESIS.toml"
        hypothesis.write_text(hypothesis.read_text()
                              .replace('corpus_revision = "unverified"', 'corpus_revision = "0000000"')
                              .replace('acceptance = "proposed"', 'acceptance = "accepted"')
                              .replace("accepted_revision = 0", "accepted_revision = 1")
                              .replace('accepted = ""', 'accepted = "2026-10-17"')
                              .replace('goal = ""', 'goal = "Test the accepted hypothesis."')
                              .replace('counts_against = ""', 'counts_against = "The accepted hypothesis fails."'))
        return repo

    def test_chatgpt_codex_plugin_matches_the_scaffold_release(self):
        portable = scaffold.json.loads((ROOT / "plugin.json").read_text())
        codex = scaffold.json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual(portable["name"], "scientific-research-scaffold")
        self.assertEqual(portable["version"], scaffold.SCAFFOLD_REF.removeprefix("v"))
        self.assertEqual(codex["version"], portable["version"])
        self.assertEqual(codex["skills"], "./skills/")
        self.assertTrue((ROOT / "skills" / "new-study" / "SKILL.md").exists())

    def test_new_study_passes_check(self):
        repo = self.study()
        self.assertEqual(run("new", "app", "explorer", "-q", "Look?", "--study", str(repo))[0], 0)
        self.assertEqual(run("new", "app", "second", "-q", "Again?", "--study", str(repo))[0], 0)
        self.assertEqual(run("new", "sim", "model-a", "-q", "Sim", "--inside", str(repo))[0], 0)
        self.assertTrue((repo / "apps" / "second" / "v1" / "index.html").exists())
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        # an unfilled {{placeholder}}; the CI workflow's own `${{ secrets.X }}` is not one
        self.assertNotRegex("".join(p.read_text() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts),
                            r"\{\{\w+\}\}")

    def test_hypothesis_map_links_units_and_detects_stale_snapshots(self):
        words = 'If "signal A" changes, then signal B changes.\nSecond line stays verbatim.'
        code, out = run("new", "study", "quoted", "-q", "Does it?", "--hypothesis", words,
                        "--dir", str(self.tmp), "--profile", "polarizetech", "--visibility", "private", "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / "quoted"
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        hypothesis = repo / "HYPOTHESIS.toml"
        self.assertEqual(scaffold.load_toml(hypothesis)["hypothesis"], words)
        hypothesis.write_text(hypothesis.read_text()
                              .replace('corpus_revision = "unverified"', 'corpus_revision = "0000000"')
                              .replace('acceptance = "proposed"', 'acceptance = "accepted"')
                              .replace("accepted_revision = 0", "accepted_revision = 1")
                              .replace('accepted = ""', 'accepted = "2026-10-17"')
                              .replace('goal = ""', 'goal = "Test the accepted hypothesis."')
                              .replace('counts_against = ""', 'counts_against = "The accepted hypothesis fails."'))
        code, out = run("new", "app", "explorer", "-q", "Look?", "--study", str(repo),
                        "--hypothesis-element", "H1")
        self.assertEqual(code, 0, out)
        unit = scaffold.load_toml(hypothesis)["units"][0]
        self.assertEqual(unit["elements"], ["H1"])
        self.assertEqual(unit["element_revisions"], ["H1@1"])
        scope_path = repo / "apps" / "explorer" / "v1" / "SCOPE.toml"
        scope_record = scaffold.load_toml(scope_path)
        self.assertEqual(scope_record["hypothesis_elements"], ["H1"])
        self.assertEqual(scope_record["claim"]["counts_against"], "The accepted hypothesis fails.")
        self.assertEqual(run("check", str(repo))[0], 0)

        # Fingerprints catch a meaning change even if someone forgets to increment the element revision.
        text = hypothesis.read_text().replace('statement = "If \\"signal A\\" changes, then signal B changes.\\nSecond line stays verbatim."',
                                              'statement = "A changed statement."', 1)
        hypothesis.write_text(text)
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("hypothesis/evidence changed", out)
        self.assertIn("queued for agent review", out)
        code, out = run("sync-hypothesis", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("flagged for agent review", out)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("queued for agent review", out)

        hypothesis.write_text(hypothesis.read_text().replace(
            'disposition = ""', 'disposition = "new-version-or-experiment"'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("disposition must be bound", out)

        current = scaffold.load_toml(hypothesis)
        element = current["elements"][0]
        meaning_fp, evidence_fp = scaffold.hypothesis_fingerprints(element)
        revisions = '["H1@1"]'
        evidence_revisions = '["H1@unverified"]'
        hypothesis.write_text(hypothesis.read_text()
                              .replace("disposition_for_element_revisions = []",
                                       f"disposition_for_element_revisions = {revisions}")
                              .replace("disposition_for_accepted_revisions = []",
                                       f"disposition_for_accepted_revisions = {revisions}")
                              .replace("disposition_for_evidence_revisions = []",
                                       f"disposition_for_evidence_revisions = {evidence_revisions}")
                              .replace("disposition_for_element_fingerprints = []",
                                       f'disposition_for_element_fingerprints = ["H1@{meaning_fp}"]')
                              .replace("disposition_for_evidence_fingerprints = []",
                                       f'disposition_for_evidence_fingerprints = ["H1@{evidence_fp}"]')
                              .replace('disposition_for_corpus_revision = ""',
                                       'disposition_for_corpus_revision = "0000000"'))
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_hypothesis_elements_require_basis_evidence_or_falsifiable_goal(self):
        repo = self.study()
        hypothesis = repo / "HYPOTHESIS.toml"
        hypothesis.write_text(hypothesis.read_text().replace('goal = "Test the accepted hypothesis."', 'goal = ""'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("open requires a goal", out)

        hypothesis.write_text(hypothesis.read_text()
                              .replace('status = "open"', 'status = "established"')
                              .replace('basis = "gap"', 'basis = "established"'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("requires verified corpus evidence IDs", out)

        hypothesis.write_text(hypothesis.read_text()
                              .replace("evidence = []", 'evidence = ["CLAIM-1"]')
                              .replace('evidence_revision = "unverified"', 'evidence_revision = "0000000"'))
        research = repo / "RESEARCH.md"
        research.write_text(research.read_text() + "\n| H1 | CLAIM-10 | different exact ID |\n")
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("evidence IDs must also be referenced", out)
        research.write_text(research.read_text() + "| H1 | CLAIM-1 | exact ID |\n")
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_agent_can_link_an_existing_exploratory_unit_and_sync_impacts(self):
        repo = self.study()
        code, out = run("new", "app", "legacy-viewer", "-q", "Inspect a compact view", "--study", str(repo),
                        "--exploratory")
        self.assertEqual(code, 0, out)
        code, out = run("link-hypothesis", "apps/legacy-viewer/v1", "--path", str(repo),
                        "--element", "H1", "--role", "Inspects the accepted seed element.")
        self.assertEqual(code, 0, out)

        hypothesis = scaffold.load_toml(repo / "HYPOTHESIS.toml")
        unit = hypothesis["units"][0]
        self.assertEqual(unit["elements"], ["H1"])
        self.assertEqual(unit["role"], "Inspects the accepted seed element.")
        self.assertEqual(unit["state"], "current")
        scope_path = repo / "apps" / "legacy-viewer" / "v1" / "SCOPE.toml"
        scope = scaffold.load_toml(scope_path)
        self.assertEqual(scope["stage"], "exploratory")
        self.assertEqual(scope["exploration"]["building"], "Inspect a compact view")
        self.assertEqual(scope["hypothesis_elements"], ["H1"])
        self.assertEqual(scope["hypothesis_review_state"], "current")

        path = repo / "HYPOTHESIS.toml"
        path.write_text(path.read_text().replace('statement = "Does it?"',
                                                 'statement = "Its meaning changed."', 1))
        self.assertEqual(run("sync-hypothesis", str(repo))[0], 0)
        unit = scaffold.load_toml(path)["units"][0]
        scope = scaffold.load_toml(scope_path)
        self.assertEqual(unit["state"], "needs-review")
        self.assertEqual(scope["hypothesis_review_state"], "needs-review")

    def test_study_requires_hypothesis_and_unit_links_prevalidate_before_writes(self):
        code, out = run("new", "study", "missing-hypothesis", "-q", "Does it?", "--claim", "--dir", str(self.tmp),
                        "--profile", "polarizetech", "--visibility", "private", "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("needs --hypothesis", out)
        code, out = run("new", "study", "missing-goal", "-q", "Does it?", "--dir", str(self.tmp),
                        "--profile", "polarizetech", "--visibility", "private", "--no-git")
        self.assertEqual(code, 1)  # the default start is a goal and an approach, not a bare question
        self.assertIn("--approach", out)
        self.assertFalse((self.tmp / "missing-hypothesis").exists())

        repo = self.study()
        manifest_before = (repo / "STUDY.toml").read_text()
        hypothesis_before = (repo / "HYPOTHESIS.toml").read_text()
        code, out = run("new", "app", "bad-link", "-q", "Look?", "--study", str(repo),
                        "--hypothesis-element", "NOPE")
        self.assertEqual(code, 1)
        self.assertIn("unknown hypothesis element", out)
        self.assertFalse((repo / "apps" / "bad-link").exists())
        self.assertEqual((repo / "STUDY.toml").read_text(), manifest_before)
        self.assertEqual((repo / "HYPOTHESIS.toml").read_text(), hypothesis_before)

        hypothesis = repo / "HYPOTHESIS.toml"
        hypothesis.write_text(hypothesis.read_text()
                              .replace('acceptance = "accepted"', 'acceptance = "proposed"')
                              .replace("accepted_revision = 1", "accepted_revision = 0"))
        code, out = run("new", "app", "unaccepted", "-q", "Look?", "--study", str(repo),
                        "--hypothesis-element", "H1")
        self.assertEqual(code, 1)
        self.assertIn("not accepted by the person", out)
        self.assertFalse((repo / "apps" / "unaccepted").exists())

    def test_proposed_elements_and_blank_falsifiers_are_not_settled(self):
        code, out = run("new", "study", "proposal", "-q", "Does it?", "--hypothesis", "Maybe it does.",
                        "--dir", str(self.tmp), "--profile", "polarizetech", "--visibility", "private", "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / "proposal"
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("needs the person's acceptance", out)
        self.assertIn("requires what would count against it", out)
        (repo / "STUDY.toml").write_text((repo / "STUDY.toml").read_text().replace(
            'stage = "SKETCH"', 'stage = "PROBE"'))
        (repo / "README.md").write_text((repo / "README.md").read_text().replace(
            "**Stage:** SKETCH", "**Stage:** PROBE"))
        self.assertEqual(run("check", str(repo))[0], 1)

    def test_local_corpus_revision_reconciliation_stales_linked_units(self):
        corpus = self.tmp / "research"
        corpus.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=corpus, check=True)
        (corpus / "claims.md").write_text("first\n")
        subprocess.run(["git", "add", "."], cwd=corpus, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "first"], cwd=corpus, check=True)
        rev1 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=corpus, capture_output=True,
                              text=True, check=True).stdout.strip()

        repo = self.study()
        hypothesis = repo / "HYPOTHESIS.toml"
        hypothesis.write_text(hypothesis.read_text().replace('corpus_revision = "0000000"',
                                                              f'corpus_revision = "{rev1}"'))
        self.assertEqual(run("new", "app", "linked", "-q", "Look?", "--study", str(repo),
                             "--hypothesis-element", "H1")[0], 0)
        self.assertEqual(run("check", str(repo))[0], 0)

        (corpus / "claims.md").write_text("second\n")
        subprocess.run(["git", "add", "."], cwd=corpus, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "second"], cwd=corpus, check=True)
        rev2 = subprocess.run(["git", "rev-parse", "HEAD"], cwd=corpus, capture_output=True,
                              text=True, check=True).stdout.strip()
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("corpus checkout changed", out)

        hypothesis.write_text(hypothesis.read_text().replace(rev1, rev2, 1))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("hypothesis/evidence changed", out)

    def test_an_app_has_its_own_versions(self):
        repo = self.study()
        for q in ("Look?", "Look again?"):
            self.assertEqual(run("new", "app", "explorer", "-q", q, "--study", str(repo))[0], 0)
        self.assertEqual(run("new", "app", "other", "-q", "Else?", "--study", str(repo))[0], 0)
        for rel in ("apps/explorer/v1", "apps/explorer/v2", "apps/other/v1"):
            self.assertTrue((repo / rel / "index.html").exists(), rel)
        self.assertEqual([(a["slug"], a["version"]) for a in scaffold.load_toml(repo / "STUDY.toml")["apps"]],
                         [("explorer", "v1"), ("explorer", "v2"), ("other", "v1")])
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_an_app_prints_its_tailnet_url_and_takes_an_override(self):
        repo = self.study()
        code, out = run("new", "app", "explorer", "-q", "Look?", "--study", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("https://joshuas-macbook-pro.tailc463ae.ts.net/explorer/v1/", out)
        serve = repo / "apps" / "explorer" / "v1" / "serve.py"
        self.assertIn('TAILNET_URL = os.environ.get("TAILNET_URL", '
                      '"https://joshuas-macbook-pro.tailc463ae.ts.net")', serve.read_text())
        self.assertIn('SLUG = "explorer"', serve.read_text())
        for env, want in ((None, "https://joshuas-macbook-pro.tailc463ae.ts.net/explorer/v1/"),
                          ("https://other.example.ts.net/", "https://other.example.ts.net/explorer/v1/")):
            e = {k: v for k, v in os.environ.items() if k != "TAILNET_URL"}
            if env:
                e["TAILNET_URL"] = env
            got = subprocess.run([sys.executable, "-c",
                                  f"import runpy; m = runpy.run_path({str(serve)!r}, run_name='x'); "
                                  "print(m['TAILNET_URL'] + '/' + m['SLUG'] + '/' + m['VERSION'] + '/')"],
                                 env=e, capture_output=True, text=True, check=True).stdout.strip()
            self.assertEqual(got, want)

    def test_an_app_url_ends_in_its_version(self):
        repo = self.study()
        self.assertEqual(run("new", "app", "explorer", "-q", "Look?", "--study", str(repo))[0], 0)
        serve = repo / "apps" / "explorer" / "v1" / "serve.py"
        m = runpy.run_path(str(serve), run_name="x")
        for path, want in (("/v1/app.js", "/app.js"), ("/explorer/v1/app.js", "/app.js"),
                           ("/explorer/app.js", "/app.js"), ("/v1/", "/"), ("/app.js", "/app.js")):
            self.assertEqual(m["unmount"](path), want, path)

    def test_a_profile_without_a_tailnet_prints_none(self):
        repo = self.study("plain", profile="example")
        code, out = run("new", "app", "explorer", "-q", "Look?", "--study", str(repo))
        self.assertEqual(code, 0, out)
        self.assertNotIn("tailnet:", out)

    def test_the_earlier_app_layout_still_passes(self):
        repo = self.study()
        self.assertEqual(run("new", "app", "explorer", "-q", "Look?", "--study", str(repo))[0], 0)
        (repo / "apps" / "explorer" / "v1").rename(repo / "apps" / "v1-explorer")
        (repo / "apps" / "explorer").rmdir()
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_example_profile_has_no_workbench_resolver(self):
        repo = self.study("plain", profile="example")
        self.assertFalse((repo / "shared" / "workbench.py").exists())
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_new_sim_standalone(self):
        self.assertEqual(run("new", "sim", "memory", "-q", "Tape", "--dir", str(self.tmp), "--profile", "example",
                             "--visibility", "public", "--no-git")[0], 0)
        repo = self.tmp / "memory"
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_visibility_is_never_defaulted(self):
        repo = self.study("undecided", visibility=None)
        self.assertIn('visibility = "undecided"', (repo / "STUDY.toml").read_text())
        code, out = run("check", str(repo))
        self.assertEqual(code, 1, out)
        self.assertIn("visibility is undecided", out)
        self.assertIn("visibility_decided must be the date", out)

    def test_visibility_flag_records_the_decision(self):
        repo = self.study("decided", visibility="public")
        m = scaffold.load_toml(repo / "STUDY.toml")
        self.assertEqual(m["visibility"], "public")
        self.assertEqual(m["visibility_decided"], scaffold._dt.date.today().isoformat())
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_visibility_is_refused_for_a_sim_inside_a_study(self):
        repo = self.study()
        code, out = run("new", "sim", "inner", "-q", "Sim", "--inside", str(repo), "--visibility", "public")
        self.assertEqual(code, 1)
        self.assertIn("shares its visibility", out)

    def test_there_is_no_default_profile(self):
        code, out = run("new", "study", "orphan", "-q", "?", "--hypothesis", "?",
                        "--dir", str(self.tmp), "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("no profile", out)
        self.assertIn("SCAFFOLD_PROFILE", out)
        self.assertFalse((self.tmp / "orphan").exists())

    def test_profile_from_environment(self):
        os.environ["SCAFFOLD_PROFILE"] = "example"
        code, out = run("new", "study", "envy", "-q", "?", "--hypothesis", "?",
                        "--dir", str(self.tmp), "--no-git")
        self.assertEqual(code, 0, out)
        self.assertEqual(scaffold.load_toml(self.tmp / "envy" / "STUDY.toml")["profile"], "example")

    def test_study_manifest_profile_wins_over_environment(self):
        repo = self.study("pinned", profile="example")
        os.environ["SCAFFOLD_PROFILE"] = "polarizetech"
        self.assertEqual(run("new", "sim", "inner", "-q", "Sim", "--inside", str(repo))[0], 0)
        self.assertEqual(scaffold.load_toml(repo / "sims" / "inner" / "SIM.toml")["profile"], "example")

    def tool(self, name="recorder"):
        code, out = run("new", "tool", name, "-j", "Records a signal", "--claim", "--dir", str(self.tmp),
                        "--profile", "example", "--visibility", "public", "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / name
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        add_kit_block(repo)
        return repo

    def test_new_tool_passes_check(self):
        repo = self.tool()
        m = scaffold.load_toml(repo / "TOOL.toml")
        self.assertEqual((m["kind"], m["job"], m["version"]), ("tool", "Records a signal", "0.1.0"))
        self.assertNotIn("question", m)
        for research in scaffold.RESEARCH_FILES:
            self.assertFalse((repo / research).exists(), research)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_scoped_tool_warns_until_it_has_a_scope_record(self):
        repo = self.tool()
        (repo / ".agents" / "protocols").mkdir(parents=True, exist_ok=True)
        (repo / ".agents" / "protocols" / "SCOPE_PROTOCOL.md").write_text("# scope\n")  # prereg, kit 0.6+
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("unscoped: no SCOPE.toml yet", out)
        (repo / "SCOPE.toml").write_text("format = 1\n")
        self.assertNotIn("unscoped", run("check", str(repo))[1])

    def test_tool_takes_a_job_not_a_question(self):
        for args in (["-q", "Does it?"], ["-q", "Does it?", "-j", "Records"], []):
            code, out = run("new", "tool", "gauge", *args, "--claim", "--dir", str(self.tmp),
                            "--profile", "example", "--no-git")
            self.assertEqual(code, 1, args)
            self.assertIn("--job", out)
        code, out = run("new", "study", "asks", "-j", "Records", "--dir", str(self.tmp), "--profile", "example",
                        "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("--goal", out)

    def test_tool_holds_no_research(self):
        repo = self.tool()
        (repo / "EXPERIMENTS.md").write_text("# Experiments\n")
        (repo / "experiments").mkdir()
        with (repo / "TOOL.toml").open("a") as f:
            f.write('question = "Does it?"\n\n[corpus]\nproject = "x"\n')
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        for needle in ("EXPERIMENTS.md is research", "experiments is research", "TOOL.toml has 'question'",
                       "TOOL.toml has 'corpus'"):
            self.assertIn(needle, out)

    def test_tool_may_hold_comparison_units(self):
        """TOOL_VERSIONING.md §1a: sims and datasets that compare the tool with other tools."""
        repo = self.tool()
        code, out = run("new", "sim", "vs-other", "-q", "Compare the recorder with other", "--inside", str(repo),
                        "--compares", "other 1.0.0", "--exploratory")
        self.assertEqual(code, 0, out)
        code, out = run("new", "dataset", "bench", "-q", "Compare on a public recording", "--study", str(repo),
                        "--compares", "ref 2.1")
        self.assertEqual(code, 0, out)
        scope = scaffold.load_toml(repo / "sims" / "vs-other" / "SCOPE.toml")
        self.assertEqual(scope["compares"], ["recorder 0.1.0", "other 1.0.0"])
        self.assertEqual(scope["stage"], "exploratory")
        self.assertEqual(scaffold.load_toml(repo / "datasets" / "bench" / "SCOPE.toml")["stage"], "testing")
        m = scaffold.load_toml(repo / "TOOL.toml")
        self.assertEqual([c["path"] for c in m["comparisons"]], ["sims/vs-other", "datasets/bench"])
        self.assertTrue((repo / "EXPERIMENTS.md").exists())
        self.assertFalse((repo / "sims" / "vs-other" / "RESEARCH.md").exists())
        self.assertNotIn("corpus", scaffold.load_toml(repo / "sims" / "vs-other" / "SIM.toml"))
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_tool_comparison_units_are_checked(self):
        repo = self.tool()
        self.assertEqual(run("new", "sim", "vs-other", "-q", "Compare", "--inside", str(repo))[0], 1)  # no --compares
        run("new", "sim", "vs-other", "-q", "Compare", "--inside", str(repo), "--compares", "other 1.0")
        scope = repo / "sims" / "vs-other" / "SCOPE.toml"
        scope.write_text(scope.read_text().replace(', "other 1.0"', ""))
        (repo / "sims" / "stray" / "preregistrations").mkdir(parents=True)
        (repo / "pkg" / "preregistrations").mkdir(parents=True)
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        for needle in ("sims/vs-other/SCOPE.toml: compares must name the tool and at least one other tool",
                       "sims/stray: a comparison unit needs a SCOPE.toml",
                       "sims/stray is not listed under [[comparisons]]",
                       "pkg/preregistrations: a tool's preregistrations go directly inside a comparison unit"):
            self.assertIn(needle, out)
        self.assertEqual(run("new", "sim", "x", "-q", "Q", "--dir", str(self.tmp), "--profile", "example",
                             "--compares", "y 1", "--no-git")[0], 1)  # --compares outside a tool

    # ------------------------------------------------------------------------- bench sims (TOOL_VERSIONING.md §1b)

    def reference_repo(self, tag="ref/v1.0.0"):
        """A repo holding a reference implementation, with an annotated release tag."""
        ref = self.tmp / "refs"
        (ref / "sims" / "ref").mkdir(parents=True)
        ref = ref.resolve()
        (ref / "sims" / "ref" / "model.m").write_text("disp(1)\n")
        for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-qm", "ref"], ["tag", "-a", tag, "-m", "2026-10-01"],
                    ["commit", "-q", "--allow-empty", "-m", "after the tag"]):
            subprocess.run(["git", *cmd], cwd=ref, check=True)
        sha = subprocess.run(["git", "rev-parse", f"{tag}^{{commit}}"], cwd=ref, check=True, capture_output=True,
                             text=True).stdout.strip()
        return ref, sha

    def bench(self, *refs):
        repo = self.tool()
        code, out = run("new", "sim", "vs-ref", "-q", "Agree with the reference", "--inside", str(repo),
                        *[x for r in refs for x in ("--reference", r)])
        self.assertEqual(code, 0, out)
        return repo, repo / "sims" / "vs-ref"

    def test_new_bench_passes_check(self):
        ref, sha = self.reference_repo()
        repo, bench = self.bench(f"ref={ref}@ref/v1.0.0#sims/ref,licence=MIT",
                                 f"oct={ref}@ref/v1.0.0#sims/ref,licence=GPL-3.0,runs=process,command=octave model.m")
        scope = scaffold.load_toml(bench / "SCOPE.toml")
        self.assertEqual(scope["kind"], "bench")
        self.assertEqual(scope["compares"], ["recorder 0.1.0", "ref ref/v1.0.0", "oct ref/v1.0.0"])
        self.assertEqual([r["commit"] for r in scope["references"]], [sha, sha])  # the tag's, not the tip
        self.assertEqual(scope["references"][0]["package"], "ref")
        pyproject = (bench / "pyproject.toml").read_text()
        self.assertIn(f'"ref @ git+{ref.as_uri()}@ref/v1.0.0#subdirectory=sims/ref"', pyproject)
        self.assertNotIn("oct @", pyproject)  # a process reference is never installed
        for f in ("run.py", "tolerances.toml", "tests/test_bench.py", ".gitignore", "README.md"):
            self.assertTrue((bench / f).exists(), f)
        self.assertNotIn("{{", (bench / "run.py").read_text())
        self.assertFalse((repo / "EXPERIMENTS.md").exists())  # a bench sim is not an experiment
        self.assertFalse((bench / "preregistrations").exists())
        m = scaffold.load_toml(repo / "TOOL.toml")
        self.assertEqual([(c["kind"], c["path"]) for c in m["comparisons"]], [("bench", "sims/vs-ref")])
        self.assertIn("sims:", (repo / "Makefile").read_text())
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_new_bench_refuses_unpinned_or_unsafe_references(self):
        ref, sha = self.reference_repo()
        repo = self.tool()
        for spec, needle in ((None, "needs --compares"),
                             (f"ref={ref}@ref/v1.0.0", "say the reference's licence"),
                             (f"ref={ref}@main,licence=MIT", "not a release tag"),
                             (f"ref={ref}@ref/v9.9.9,licence=MIT", "could not find tag ref/v9.9.9"),
                             (f"ref={ref}@ref/v1.0.0,licence=GPL-3.0", "runs as a separate process"),
                             (f"ref={ref}@ref/v1.0.0,licence=MIT,commit=abc", "full 40-character commit"),
                             (f"ref={ref}@ref/v1.0.0,licence=MIT,colour=red", "unknown option")):
            code, out = run("new", "sim", "vs-ref", "-q", "Q", "--inside", str(repo),
                            *(["--reference", spec] if spec else []))
            self.assertEqual(code, 1, spec)
            self.assertIn(needle, out)
        self.assertFalse((repo / "sims").exists())
        code, out = run("new", "sim", "vs-ref", "-q", "Q", "--inside", str(repo), "--reference",
                        f"lgpl={ref}@ref/v1.0.0,licence=LGPL-2.1,commit={sha}")  # given commit: no lookup
        self.assertEqual(code, 0, out)
        self.assertIn("--reference is for a bench sim",
                      run("new", "sim", "b", "-q", "Q", "--inside", str(self.study()), "--reference", "a=o/r@v1")[1])
        self.assertIn("--compares is for a preregistered comparison unit",
                      run("new", "sim", "sx", "-q", "Q", "--inside", str(repo), "--compares", "x 1",
                          "--reference", "a=o/r@v1,licence=MIT")[1])

    def test_bench_pins_are_checked(self):
        ref, _ = self.reference_repo()
        repo, bench = self.bench(f"ref={ref}@ref/v1.0.0#sims/ref,licence=MIT")
        pyproject = bench / "pyproject.toml"
        original = pyproject.read_text()
        cases = {
            original.replace("@ref/v1.0.0#", "@ref/v1.1.0#"): "pyproject.toml pins ref at ref/v1.1.0, SCOPE.toml declares ref/v1.0.0",
            original.replace("@ref/v1.0.0#", "#"): "pins ref to a default branch, not a tag",
            original.replace("#subdirectory=sims/ref", ""): "subdirectory '' differs",
            original.replace(ref.as_uri(), "https://github.com/o/elsewhere"): "fetches ref from https://github.com/o/elsewhere",
            original.replace(f'"ref @ git+{ref.as_uri()}@ref/v1.0.0#subdirectory=sims/ref",', ""): "ref is not pinned",
            original.replace(f'"ref @ git+{ref.as_uri()}@ref/v1.0.0#subdirectory=sims/ref",', '"ref",') +
            f'\n[tool.uv.sources]\nref = {{ git = "{ref.as_uri()}", branch = "main", subdirectory = "sims/ref" }}\n':
                "pins ref to a branch, not a tag",
        }
        for text, needle in cases.items():
            pyproject.write_text(text)
            code, out = run("check", str(repo))
            self.assertEqual(code, 1, needle)
            self.assertIn(needle, out)
        pyproject.write_text(original.replace(f'"ref @ git+{ref.as_uri()}@ref/v1.0.0#subdirectory=sims/ref",', '"ref",')
                             + f'\n[tool.uv.sources]\nref = {{ git = "{ref.as_uri()}.git", tag = "ref/v1.0.0", '
                               'subdirectory = "sims/ref" }\n')
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        scope = bench / "SCOPE.toml"
        scope.write_text(re.sub(r'commit = "[0-9a-f]+"', 'commit = "abc123"', scope.read_text())
                         .replace('licence = "MIT"', 'licence = "GPL-3.0-only"'))
        code, out = run("check", str(repo))
        self.assertIn("commit must be the tag's full 40-character commit", out)
        self.assertIn("GPL-3.0-only code is imported", out)
        (bench / "preregistrations").mkdir()
        self.assertIn("tolerances are its preregistration", run("check", str(repo))[1])

    def test_bench_tolerances_come_before_results(self):
        ref, _ = self.reference_repo()
        repo, bench = self.bench(f"ref={ref}@ref/v1.0.0#sims/ref,licence=MIT")
        tolerances = bench / "tolerances.toml"
        (bench / "results").mkdir()
        result = bench / "results" / "0.1.0.json"

        def score(sha):
            result.write_text(json.dumps({"tolerances_sha256": sha, "passed": True,
                                          "references": [{"name": "ref", "tag": "ref/v1.0.0"}]}))
        score(hashlib.sha256(tolerances.read_bytes()).hexdigest())
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("tolerances are decided by the owner before scoring", out)
        tolerances.write_text(tolerances.read_text().replace('decided_by = ""', 'decided_by = "the owner"')
                              .replace('decided = ""', 'decided = "2026-10-27"')
                              + '\n[[metrics]]\nname = "max-abs-diff"\nreference = "ref"\nat_most = 1e-6\n'
                                'why = "float32 round-off"\n')
        code, out = run("check", str(repo))
        self.assertIn("scored against other tolerances than tolerances.toml now holds", out)
        score(hashlib.sha256(tolerances.read_bytes()).hexdigest())
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        tolerances.unlink()
        self.assertIn("no tolerances.toml", run("check", str(repo))[1])

    @unittest.skipIf(sys.version_info < (3, 11), "the bench's run.py uses tomllib")
    def test_bench_run_scores_and_records(self):
        """The rendered run.py: refuses before tolerances are decided, fetches a process reference at its pinned
        commit, scores the worst case against each bound, and writes a result `scaffold check` accepts."""
        ref, sha = self.reference_repo()
        repo, bench = self.bench(f"oct={ref}@ref/v1.0.0#sims/ref,licence=GPL-3.0,runs=process,command=octave")
        loader = importlib.machinery.SourceFileLoader("bench_run", str(bench / "run.py"))
        spec = importlib.util.spec_from_loader("bench_run", loader)
        bench_run = importlib.util.module_from_spec(spec)
        loader.exec_module(bench_run)
        bench_run.cases = lambda: {"one": 1.0, "two": 2.0}
        bench_run.outputs = lambda who, case, ref=None: case if who == "tool" else case + 1e-7
        bench_run.measure = lambda metric, a, b: abs(a - b)
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "bench"], cwd=repo, check=True)
        with self.assertRaisesRegex(SystemExit, "has not decided"):
            bench_run.main(["--verify"])
        tolerances = bench / "tolerances.toml"
        tolerances.write_text('decided_by = "the owner"\ndecided = "2026-10-27"\n\n[[metrics]]\n'
                              'name = "max-abs-diff"\nreference = "oct"\nat_most = 1e-6\nwhy = "round-off"\n')
        with self.assertRaisesRegex(SystemExit, "uncommitted"):
            bench_run.main([])
        subprocess.run(["git", "commit", "-qam", "the owner's tolerances"], cwd=repo, check=True)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(bench_run.main([]), 0)
        checkout = bench / ".references" / "oct"
        self.assertEqual(subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True,
                                        text=True).stdout.strip(), sha)
        result = json.loads((bench / "results" / "0.1.0.json").read_text())
        self.assertTrue(result["passed"])
        self.assertEqual(result["references"][0]["commit"], sha)
        self.assertAlmostEqual(result["metrics"][0]["value"], 1e-7)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        bench_run.outputs = lambda who, case, ref=None: case if who == "tool" else case + 1e-3
        with redirect_stdout(io.StringIO()):
            self.assertEqual(bench_run.main([]), 1)
        self.assertFalse(json.loads((bench / "results" / "0.1.0.json").read_text())["passed"])
        subprocess.run(["git", "tag", "-f", "-a", "ref/v1.0.0", "-m", "moved", "HEAD"], cwd=ref, check=True,
                       capture_output=True)
        shutil.rmtree(checkout)
        with self.assertRaisesRegex(SystemExit, "the tag moved"):
            bench_run.main(["--verify"])

    def test_tool_version_is_said_once(self):
        repo = self.tool()
        manifest = repo / "TOOL.toml"
        manifest.write_text(manifest.read_text().replace('version = "0.1.0"', 'version = "0.2.0"'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        for needle in ("pyproject.toml says version 0.1.0, TOOL.toml says 0.2.0",
                       "CITATION.cff says version 0.1.0, TOOL.toml says 0.2.0",
                       "CHANGELOG.md has no heading for version 0.2.0"):
            self.assertIn(needle, out)
        for f in ("pyproject.toml", "CITATION.cff"):
            (repo / f).write_text((repo / f).read_text().replace("0.1.0", "0.2.0"))
        with (repo / "CHANGELOG.md").open("a") as f:
            f.write("\n## [0.2.0] (2026-09-29)\n")
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_tool_consumers_say_what_they_use(self):
        repo = self.tool()
        with (repo / "TOOL.toml").open("a") as f:
            f.write('\n[[consumers]]\nname = "colony"\nrepo = "o/colony"\nuses = ["GET /status"]\n'
                    '\n[[consumers]]\nname = "vague"\nrepo = "o/vague"\n')
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("consumer vague: list what it relies on", out)
        self.assertNotIn("consumer colony", out)

    def test_study_pins_its_tools_to_a_tag(self):
        repo = self.study()
        with (repo / "STUDY.toml").open("a") as f:
            f.write('\n[[tools]]\nslug = "recorder"\nrepo = "o/recorder"\nref = "v0.3.0"\n')
        self.assertEqual(run("check", str(repo))[0], 0)
        with (repo / "STUDY.toml").open("a") as f:
            f.write('\n[[tools]]\nslug = "loose"\nrepo = "o/loose"\nref = "main"\n')
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("tool loose: must be pinned to a tag", out)

    # ------------------------------------------------------------------------- status, update

    def committed(self, repo):
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-qm", "state"], cwd=repo, check=True)

    def plan(self, repo, **kw):
        return {rel: action for rel, action, *_ in scaffold.plan_update(repo, **kw)[2]}

    def test_new_repo_records_its_files_and_is_up_to_date(self):
        repo = self.study()
        lock = scaffold.read_lock(repo)
        self.assertEqual(lock["scaffold"], scaffold.SCAFFOLD_REF)
        self.assertEqual(set(lock["files"]), set(scaffold.OWNED["study"]))
        self.assertEqual(set(self.plan(repo).values()), {"current"})
        self.assertEqual(set(scaffold.read_lock(self.tool())["files"]), set(scaffold.OWNED["tool"]))

    def age(self, repo, ref="v0.0.9"):
        """Make the repo look as if an earlier release wrote its CI, and nobody has touched it since."""
        ci = repo / ".github" / "workflows" / "check.yml"
        ci.write_text(ci.read_text().replace(f"ref: {scaffold.SCAFFOLD_REF}", f"ref: {ref}"))
        lock = scaffold.read_lock(repo)
        lock["files"][".github/workflows/check.yml"] = scaffold.sha256(ci.read_text())
        (repo / scaffold.LOCK).write_text(scaffold.json.dumps(lock))
        return ci

    def test_update_replaces_what_nobody_edited(self):
        repo = self.study()
        ci = self.age(repo)
        self.committed(repo)
        self.assertEqual(self.plan(repo)[".github/workflows/check.yml"], "update")
        code, out = run("update", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("dry run", out)
        self.assertIn("ref: v0.0.9", ci.read_text())
        code, out = run("update", str(repo), "--apply")
        self.assertEqual(code, 0, out)
        self.assertIn(f"ref: {scaffold.SCAFFOLD_REF}", ci.read_text())
        self.assertEqual(scaffold.read_lock(repo)["files"][".github/workflows/check.yml"],
                         scaffold.sha256(ci.read_text()))
        self.assertEqual(set(self.plan(repo).values()), {"current"})

    def test_update_keeps_edited_files_unless_adopted(self):
        repo = self.study()
        make = repo / "Makefile"
        make.write_text(make.read_text() + "\ntest:\n\tpytest\n")
        self.committed(repo)
        self.assertEqual(self.plan(repo)["Makefile"], "edited")
        self.assertEqual(run("update", str(repo), "--apply")[0], 0)
        self.assertIn("pytest", make.read_text())
        self.assertNotIn("Makefile", scaffold.read_lock(repo)["files"])
        code, out = run("update", str(repo), "--apply", "--adopt", "Makefile")
        self.assertEqual(code, 0, out)
        self.assertNotIn("\ntest:", make.read_text())
        self.assertEqual(run("update", str(repo), "--adopt", "README.md")[0], 1)

    def test_update_pins_the_scaffold_ref_in_an_edited_workflow(self):
        repo = self.study()
        ci = self.age(repo, ref="main")
        ci.write_text(ci.read_text() + "      - run: make extra\n")
        self.committed(repo)
        self.assertEqual(self.plan(repo)[".github/workflows/check.yml"], "pin")
        self.assertEqual(run("update", str(repo), "--apply")[0], 0)
        text = ci.read_text()
        self.assertIn(f"ref: {scaffold.SCAFFOLD_REF}", text)
        self.assertIn("make extra", text)
        self.assertNotIn(".github/workflows/check.yml", scaffold.read_lock(repo)["files"])

    def test_update_never_adds_files_to_an_adopted_repo_unasked(self):
        repo = self.study()
        (repo / scaffold.LOCK).unlink()
        (repo / "Makefile").unlink()
        self.committed(repo)
        self.assertEqual(self.plan(repo)["Makefile"], "missing")
        self.assertEqual(run("update", str(repo), "--apply")[0], 0)
        self.assertFalse((repo / "Makefile").exists())
        self.assertEqual(run("update", str(repo), "--apply", "--adopt", "Makefile")[0], 0)
        self.assertTrue((repo / "Makefile").exists())

    def test_an_adopted_repo_stays_adopted_across_updates(self):
        repo = self.study()
        (repo / scaffold.LOCK).unlink()
        (repo / "Makefile").unlink()
        self.committed(repo)
        self.assertEqual(run("update", str(repo), "--apply", "--adopt", ".claude/agents")[0], 0)
        self.assertTrue(scaffold.read_lock(repo)["adopted"])
        self.committed(repo)
        self.assertEqual(self.plan(repo)["Makefile"], "missing")  # the lock doesn't make it scaffold-made
        self.assertEqual(run("update", str(repo), "--apply")[0], 0)
        self.assertFalse((repo / "Makefile").exists())
        self.assertTrue(scaffold.read_lock(repo)["adopted"])
        self.assertNotIn("adopted", scaffold.read_lock(self.study("made")))

    def test_update_refuses_to_overwrite_uncommitted_work(self):
        repo = self.study()
        ci = self.age(repo)
        self.committed(repo)
        with ci.open("a") as f:
            f.write("# mine\n")
        lock = scaffold.read_lock(repo)
        lock["files"][".github/workflows/check.yml"] = scaffold.sha256(ci.read_text())
        (repo / scaffold.LOCK).write_text(scaffold.json.dumps(lock))
        code, out = run("update", str(repo), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("uncommitted changes", out)
        self.assertIn("# mine", ci.read_text())

    @unittest.skipUnless((ROOT / ".git").exists(), "needs this scaffold's git history")
    def test_update_recognises_an_earlier_release_without_a_lock(self):
        repo = self.study()
        ci = repo / ".github" / "workflows" / "check.yml"
        ci.write_text(ci.read_text().replace(f"ref: {scaffold.SCAFFOLD_REF}", "ref: main"))
        (repo / scaffold.LOCK).unlink()
        self.assertEqual(self.plan(repo)[".github/workflows/check.yml"], "update")

    #: The CI workflow v0.8.0 wrote for every kind, before it could read private dependencies.
    V080_CI = """name: check
on:
  push:
    branches: [main]
  pull_request:
permissions:
  contents: read
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: polarizetech/scientific-research-scaffold
          ref: v0.8.0
          path: .scaffold
      - uses: astral-sh/setup-uv@v6
      - run: uv sync --frozen || uv sync
      - run: make check SCAFFOLD="python3 .scaffold/bin/scaffold"
"""

    def on_v080(self, repo, lock=True):
        """Make the repo's CI what v0.8.0 wrote, recorded in the lock or not."""
        ci = repo / ".github" / "workflows" / "check.yml"
        ci.write_text(self.V080_CI)
        if lock:
            recorded = scaffold.read_lock(repo)
            recorded["scaffold"] = "v0.8.0"
            recorded["files"][".github/workflows/check.yml"] = scaffold.sha256(self.V080_CI)
            (repo / scaffold.LOCK).write_text(scaffold.json.dumps(recorded))
        else:
            (repo / scaffold.LOCK).unlink()
        return ci

    def test_update_moves_a_v0_8_0_repo_to_the_workflow_that_reads_the_token(self):
        for repo in (self.study(), self.tool(), self.workbench()):
            ci = self.on_v080(repo)
            self.committed(repo)
            self.assertEqual(self.plan(repo)[".github/workflows/check.yml"], "update", repo.name)
            code, out = run("update", str(repo), "--apply")
            self.assertEqual(code, 0, out)
            self.assertIn("secrets.PRIVATE_DEPS_TOKEN", ci.read_text())
            self.assertEqual(set(self.plan(repo).values()), {"current"}, repo.name)

    @unittest.skipIf(subprocess.run(["git", "cat-file", "-e", "v0.8.0:templates/study/.github/workflows/check.yml"],
                                    cwd=ROOT, capture_output=True).returncode, "needs this scaffold's v0.8.0 tag")
    def test_update_recognises_v0_8_0_ci_without_a_lock(self):
        repo = self.study()
        self.on_v080(repo, lock=False)
        self.assertEqual(self.plan(repo)[".github/workflows/check.yml"], "update")

    def test_ci_reads_private_dependencies_with_the_profiles_org(self):
        for kind in scaffold.KINDS:
            for pname in ("example", "polarizetech"):
                profile = scaffold.load_profile(pname)
                text = scaffold.render_owned(kind, ".github/workflows/check.yml",
                                             scaffold.template_vars(profile, "x", "?"), profile)
                self.assertIn("DEPS_TOKEN: ${{ secrets.PRIVATE_DEPS_TOKEN }}", text, kind)
                self.assertEqual(set(re.findall(r"github\.com/([\w.-]*)/", text)), {profile["org"]}, kind)
                self.assertIn(f'.insteadOf "https://github.com/{profile["org"]}/"', text, kind)

    def install_step(self, repo, pyproject, token, uv_works):
        """Run the generated workflow's install step with a stand-in `uv`. Returns (exit status, output)."""
        text = (repo / ".github" / "workflows" / "check.yml").read_text()
        block = re.search(r"- name: Install dependencies\n        run: \|\n((?:          .*\n)+)", text).group(1)
        work = self.tmp / "ci"
        (work / "bin").mkdir(parents=True, exist_ok=True)
        uv = work / "bin" / "uv"
        uv.write_text(f"#!/bin/sh\nexit {0 if uv_works else 1}\n")
        uv.chmod(0o755)
        (work / "pyproject.toml").write_text(pyproject)
        env = {**os.environ, "PATH": f"{work / 'bin'}{os.pathsep}{os.environ['PATH']}", "DEPS_TOKEN": token}
        done = subprocess.run(["bash", "-e", "-c", "\n".join(line[10:] for line in block.splitlines())],
                              cwd=work, env=env, capture_output=True, text=True)
        return done.returncode, done.stdout + done.stderr

    def test_ci_install_without_a_token_warns_only_for_private_pins(self):
        repo = self.study()
        private = 'dependencies = ["lib @ git+https://github.com/polarizetech/lib@v1.0.0"]\n'
        public = 'dependencies = ["numpy"]\n'
        self.assertEqual(self.install_step(repo, public, "", uv_works=True), (0, ""))
        code, out = self.install_step(repo, private, "", uv_works=False)
        self.assertEqual(code, 0, out)
        self.assertIn("::warning::PRIVATE_DEPS_TOKEN is not set", out)
        self.assertEqual(self.install_step(repo, private, "t0ken", uv_works=False)[0], 1)  # a token that cannot read them
        self.assertEqual(self.install_step(repo, public, "", uv_works=False)[0], 1)  # nothing to do with the token

    def test_a_sim_inside_a_study_is_updated_with_the_study(self):
        repo = self.study()
        self.assertEqual(run("new", "sim", "inner", "-q", "Sim", "--inside", str(repo))[0], 0)
        code, out = run("update", str(repo / "sims" / "inner"))
        self.assertEqual(code, 1)
        self.assertIn("update the study", out)

    def test_pin_scaffold_ref(self):
        wf = ("      - id: scaffold\n"
              "        uses: actions/checkout@v4\n"
              "        with:\n"
              "          ref: main\n"
              "          repository: someone/scientific-research-scaffold\n"
              "          token: ${{ secrets.T }}\n"
              "      - uses: actions/checkout@v4\n"
              "        with:\n"
              "          repository: someone/other\n"
              "          ref: main\n")
        text, old = scaffold.pin_scaffold_ref(wf, "v9.9.9")
        self.assertEqual(old, "main")
        self.assertEqual(text.count("ref: v9.9.9"), 1)
        self.assertIn("repository: someone/other\n          ref: main", text)
        self.assertEqual(scaffold.pin_scaffold_ref("jobs: {}\n", "v1.0.0"), ("jobs: {}\n", None))

    def test_status_surveys_many_repos(self):
        study, tool = self.study(), self.tool()
        (self.tmp / "loose").mkdir()
        code, out = run("status", str(study), str(tool), str(self.tmp / "loose"))
        self.assertEqual(code, 0, out)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("repo"))
        self.assertRegex(out, r"colony\s+study\s+SKETCH\s+v\d+\.\d+\.\d+\s+v\d+\.\d+\.\d+\s+ok\s+up to date")
        self.assertRegex(out, r"recorder\s+tool")
        self.assertRegex(out, r"loose\s+-\s+.*no manifest")

    # ---------------------------------------------------------------------------------- agents

    def frontmatter(self, path):
        text = path.read_text()
        self.assertTrue(text.startswith("---\n"), path.name)
        head = text.split("---\n")[1]
        fields = dict(line.split(": ", 1) for line in head.strip().splitlines())
        return fields, text

    def test_each_kind_gets_its_agents(self):
        study, tool = self.study(), self.tool()
        self.assertEqual(run("new", "sim", "memory", "-q", "Tape", "--dir", str(self.tmp), "--profile", "example",
                             "--visibility", "public", "--no-git")[0], 0)
        for repo, kind in ((study, "study"), (tool, "tool"), (self.tmp / "memory", "sim")):
            agents = repo / ".claude" / "agents"
            self.assertEqual(sorted(f.stem for f in agents.glob("*.md")), sorted(scaffold.AGENTS[kind]), kind)
            self.assertTrue((repo / ".claude" / "disciplines.md").exists())
        self.assertNotIn("designer", scaffold.AGENTS["sim"])
        self.assertEqual(run("new", "sim", "inner", "-q", "Sim", "--inside", str(study))[0], 0)
        self.assertFalse((study / "sims" / "inner" / ".claude").exists())

    def test_agent_files_are_valid_subagents(self):
        repo = self.study()
        for f in sorted((repo / ".claude" / "agents").glob("*.md")):
            fields, text = self.frontmatter(f)
            self.assertEqual(fields["name"], f.stem)
            self.assertGreater(len(fields["description"]), 80, f.name)
            self.assertNotIn(": ", fields["description"], f"{f.name}: ': ' breaks YAML frontmatter")
            self.assertNotIn("{{", text, f.name)

    def test_agents_carry_the_profile(self):
        ours = self.study("ours", profile="polarizetech")
        disciplines = (ours / ".claude" / "disciplines.md").read_text()
        for heading in ("## Neuroscience", "## Cardiology", "## Auditory neuroscience", "## Bioelectricity"):
            self.assertIn(heading, disciplines)
        engineer = (ours / ".claude" / "agents" / "computational-engineer.md").read_text()
        self.assertIn("pyright in strict mode", engineer)
        self.assertIn("`polarizetech/polarize-ui`", (ours / ".claude" / "agents" / "designer.md").read_text())

        plain = self.study("plain", profile="example")
        self.assertIn("None are named", (plain / ".claude" / "disciplines.md").read_text())
        self.assertIn("follow this repo's existing configuration",
                      (plain / ".claude" / "agents" / "computational-engineer.md").read_text())
        self.assertIn("not named in this repo's profile", (plain / ".claude" / "agents" / "designer.md").read_text())

    def test_unknown_discipline_is_an_error(self):
        with self.assertRaises(scaffold.Fail):
            scaffold.discipline_briefs(["alchemy"])

    def test_update_adopts_agents_into_an_existing_repo(self):
        repo = self.study()
        (repo / scaffold.LOCK).unlink()
        shutil.rmtree(repo / ".claude")
        self.committed(repo)
        plan = self.plan(repo)
        self.assertEqual({plan[f".claude/agents/{a}.md"] for a in scaffold.AGENTS["study"]}, {"missing"})
        self.assertEqual(run("update", str(repo), "--apply", "--adopt", ".claude/agents")[0], 0)
        self.assertEqual(sorted(f.stem for f in (repo / ".claude" / "agents").glob("*.md")),
                         sorted(scaffold.AGENTS["study"]))
        self.assertFalse((repo / ".claude" / "disciplines.md").exists())

    # ---------------------------------------------------------------------- routing, AGENTS.md

    def test_agents_start_on_their_routed_model(self):
        repo = self.study("routed", profile="example")
        agents = repo / ".claude" / "agents"
        for name, (model, effort) in scaffold.ROUTING.items():
            fields, _ = self.frontmatter(agents / f"{name}.md")
            self.assertEqual((fields["model"], fields["effort"]), (model, effort), name)
        self.assertEqual(self.frontmatter(agents / "scout.md")[0]["tools"], "Read, Grep, Glob")

    def test_profile_overrides_routing(self):
        profile = {"agents": {"routing": {"analyst": "opus:xhigh", "designer": "haiku"}}}
        v = scaffold.agent_vars({}, ".claude/agents/analyst.md", profile)
        self.assertEqual((v["model"], v["effort"]), ("opus", "xhigh"))
        v = scaffold.agent_vars({}, ".claude/agents/designer.md", profile)
        self.assertEqual((v["model"], v["effort"]), ("haiku", "medium"))
        self.assertNotIn("model", scaffold.agent_vars({}, "Makefile", profile))

    def test_agents_md_gets_the_scaffold_section_for_every_assistant(self):
        repo = self.study("roles", profile="polarizetech")
        text = (repo / "AGENTS.md").read_text()
        self.assertIn("<!-- kit_ap:start -->", text)
        self.assertEqual(text.count(scaffold.BLOCK_START), 1)
        for agent in scaffold.AGENTS["study"]:
            self.assertIn(f"`.claude/agents/{agent}.md`", text)
        self.assertIn("No run that could be quoted", text)
        self.assertEqual((repo / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        self.assertIn("gpt-5.6-sol", text)
        self.assertNotIn("{{", text)

    def test_every_question_goes_to_the_profiles_retrieval_tool(self):
        text = (self.study("roles", profile="polarizetech") / "AGENTS.md").read_text()
        self.assertIn("**Every question starts with the retrieval tool.**", text)
        self.assertIn("`research-rag`", text)
        self.assertIn("A question about this repo's own code or files is no exception", text)
        self.assertNotIn("doesn't need it", text)
        self.assertIn("The person can tell you not to use it", text)
        self.assertIn("**The retrieval tool picks the specialist.**", text)
        self.assertIn("`pipeline__profile_route`", text)
        self.assertLess(text.index("Every question starts with the retrieval tool"),
                        text.index("## Agents and coordination"))
        code, out = run("new", "tool", "recorder", "-j", "Records a signal", "--claim", "--dir", str(self.tmp),
                        "--profile", "polarizetech", "--visibility", "private", "--no-git")
        self.assertEqual(code, 0, out)  # every kind gets it, not only studies
        self.assertIn("**Every question starts with the retrieval tool.**",
                      (self.tmp / "recorder" / "AGENTS.md").read_text())
        none = (self.study("plain", profile="example") / "AGENTS.md").read_text()  # a profile that names no tool
        self.assertNotIn("retrieval tool", none)

    def test_a_retrieval_profile_gets_the_prompt_hook_and_others_do_not(self):
        settings = scaffold.json.loads((self.study("hooked", profile="polarizetech") / ".claude" / "settings.json")
                                       .read_text())
        prompt = [h["command"] for g in settings["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(sum(scaffold.RAG_HOOK_MARK in c and "--server research-rag" in c for c in prompt), 1)
        plain = scaffold.json.loads((self.study("unhooked", profile="example") / ".claude" / "settings.json")
                                    .read_text())
        self.assertNotIn("UserPromptSubmit", plain["hooks"])
        kit = {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "prereg-status"}]}]}}
        twice = scaffold.with_session_hook(scaffold.with_session_hook(scaffold.json.dumps(kit), "research-rag"),
                                           "research-rag")
        prompt = [h["command"] for g in scaffold.json.loads(twice)["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertIn("prereg-status", prompt)
        self.assertEqual(sum(scaffold.RAG_HOOK_MARK in c for c in prompt), 1)
        dropped = scaffold.json.loads(scaffold.with_session_hook(twice, ""))  # the profile stopped naming a tool
        self.assertEqual([h["command"] for g in dropped["hooks"]["UserPromptSubmit"] for h in g["hooks"]],
                         ["prereg-status"])

    def test_the_prompt_hook_never_fails_and_says_what_it_knows(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("RESEARCH_RAG_")}
        def hook(prompt, **extra):
            out = subprocess.run([sys.executable, str(ROOT / "bin" / "scaffold"), "rag-hook", "--server", "research-rag"],
                                 input=scaffold.json.dumps({"prompt": prompt}), capture_output=True, text=True,
                                 env={**env, **extra}, timeout=30)
            self.assertEqual(out.returncode, 0, out.stderr)
            return out.stdout
        self.assertEqual(hook("/compact"), "")
        text = scaffold.json.loads(hook("Why is pink noise pink?"))["hookSpecificOutput"]["additionalContext"]
        self.assertIn("retrieve passages for this request with `research-rag`", text)
        self.assertIn("are not set on this machine", text)
        down = hook("Why?", RESEARCH_RAG_URL="http://127.0.0.1:9/", RESEARCH_RAG_TOKEN_FILE=str(self.tmp / "none"))
        self.assertIn("did not answer", down)
        route = {"specialist": "noise-engineering", "roles": ["researcher"], "guidance": "Name the domain.",
                 "profiles": [{"name": "noise-engineering", "path": "agents/noise-engineering.md",
                               "repository": "/x/agents"}]}
        text = scaffold.rag_context("research-rag", route)
        self.assertIn("to the `noise-engineering` specialist", text)
        self.assertIn("Its guidance: Name the domain.", text)
        self.assertIn("names no specialist", scaffold.rag_context("research-rag", {"specialist": "", "roles": []}))

    def test_each_kind_puts_its_shared_rules_in_agents_md(self):
        study, tool = self.study(), self.tool()
        self.assertEqual(run("new", "sim", "memory", "-q", "Tape", "--dir", str(self.tmp), "--profile", "example",
                             "--visibility", "public", "--no-git")[0], 0)
        self.assertIn("Preregistrations live in the unit", (study / "AGENTS.md").read_text())
        self.assertIn("A model change is a new tag", (self.tmp / "memory" / "AGENTS.md").read_text())
        self.assertIn("No research here", (tool / "AGENTS.md").read_text())

    def test_update_refreshes_only_the_scaffold_section(self):
        repo = self.study()
        agents_md = repo / "AGENTS.md"
        head, rest = agents_md.read_text().split(scaffold.BLOCK_START)
        stale = head + scaffold.BLOCK_START + "\nold roles\n" + scaffold.BLOCK_END + "\n\nMy own notes.\n"
        agents_md.write_text(stale)
        self.committed(repo)
        self.assertEqual(self.plan(repo)["AGENTS.md"], "update")
        self.assertEqual(run("update", str(repo), "--apply")[0], 0)
        text = agents_md.read_text()
        self.assertNotIn("old roles", text)
        self.assertIn("My own notes.", text)
        self.assertIn("<!-- kit_ap:start -->", text)
        self.assertEqual(self.plan(repo)["AGENTS.md"], "current")

    def test_adopted_repo_gets_the_section_only_when_asked(self):
        repo = self.study()
        (repo / scaffold.LOCK).unlink()
        (repo / "AGENTS.md").write_text("<!-- kit_ap:start -->\n<!-- kit_ap:end -->\n")
        self.committed(repo)
        self.assertEqual(self.plan(repo)["AGENTS.md"], "missing")
        self.assertEqual(run("update", str(repo), "--apply", "--adopt", "AGENTS.md")[0], 0)
        self.assertIn(scaffold.BLOCK_START, (repo / "AGENTS.md").read_text())

    # ---------------------------------------------------------------------------------- usage

    def test_usage_passes_through_to_the_agents_tool(self):
        env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.tmp / "none"), "CODEX_HOME": str(self.tmp / "none")}
        r = subprocess.run([sys.executable, str(ROOT / "bin" / "scaffold"), "usage", str(self.tmp), "--days", "3"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Claude Code, last 3 day(s)", r.stdout)
        self.assertIn("no sessions found", r.stdout)

    # ------------------------------------------------------------------------------ work types

    def test_new_study_has_work_type_folders_not_experiments(self):
        repo = self.study()
        self.assertFalse((repo / "experiments").exists())
        self.assertFalse((repo / "data" / "manifest.json").exists())
        for folder in ("apps", "sims", "datasets", "calculators"):
            self.assertTrue((repo / folder / "README.md").exists(), folder)

    def test_dataset_is_pinned_once_selected(self):
        repo = self.study()
        code, out = run("new", "dataset", "resting-eeg", "-q", "Does it?", "--study", str(repo))
        self.assertEqual(code, 0, out)
        ds = repo / "datasets" / "resting-eeg"
        for f in ("DATASET.toml", "README.md", "analysis/README.md", "preregistrations/.gitkeep"):
            self.assertTrue((ds / f).exists(), f)
        self.assertIn('[[datasets]]\nslug = "resting-eeg"', (repo / "STUDY.toml").read_text())
        self.assertEqual(run("check", str(repo))[0], 0)  # a candidate needs nothing more

        toml = ds / "DATASET.toml"
        toml.write_text(toml.read_text().replace('status = "candidate"', 'status = "selected"')
                        .replace('version = ""', 'version = "latest"'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        for needle in ("needs provider", "needs accession", "needs licence", "pinned to a version, not latest",
                       "selection criteria"):
            self.assertIn(needle, out)
        toml.write_text(toml.read_text().replace('provider = ""', 'provider = "openneuro"')
                        .replace('accession = ""', 'accession = "ds004024"').replace('"latest"', '"1.0.2"')
                        .replace('licence = ""', 'licence = "CC0-1.0"')
                        .replace("criteria = []", 'criteria = ["resting-state EEG", "open licence"]'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_calculator_needs_reference_values_from_probe_on(self):
        repo = self.study()
        code, out = run("new", "calculator", "ear-canal-resonance", "-q", "Resonance from canal length",
                        "--study", str(repo), "--hypothesis-element", "H1")
        self.assertEqual(code, 0, out)
        calc = repo / "calculators" / "ear-canal-resonance"
        self.assertIn("Resonance from canal length", (calc / "CALCULATOR.md").read_text())
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("reference.csv has no reference values", out)  # a warning at SKETCH

        manifest = repo / "STUDY.toml"
        manifest.write_text(manifest.read_text().replace('stage = "SKETCH"', 'stage = "PROBE"'))
        readme = repo / "README.md"
        readme.write_text(readme.read_text().replace("**Stage:** SKETCH", "**Stage:** PROBE"))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("required from PROBE on", out)
        (calc / "reference.csv").write_text("case,source,length_mm,f_hz\nadult,hand,25,3430\n")
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

    def test_old_layout_and_unregistered_units_warn(self):
        repo = self.study()
        (repo / "experiments" / "E01-old").mkdir(parents=True)
        (repo / "data").mkdir()
        (repo / "data" / "manifest.json").write_text('{"datasets": []}')
        (repo / "datasets" / "stray").mkdir()
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        for needle in ("experiments/ is the old layout", "data/manifest.json is the old layout",
                       "datasets/stray is not registered"):
            self.assertIn(needle, out)

    def test_adopted_units_owe_their_manifest_later(self):
        repo = self.study()
        (repo / "datasets" / "old-analysis").mkdir(parents=True)
        (repo / "calculators" / "old-maths").mkdir(parents=True)
        with (repo / "STUDY.toml").open("a") as f:
            f.write('\n[[datasets]]\nslug = "old-analysis"\npath = "datasets/old-analysis"\nadopted = true\n'
                    '\n[[calculators]]\nslug = "old-maths"\npath = "calculators/old-maths"\nadopted = true\n'
                    '\n[[datasets]]\nslug = "gone"\npath = "datasets/gone"\nadopted = true\n')
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)  # only the one that does not exist fails
        self.assertIn("dataset gone: datasets/gone does not exist", out)
        self.assertIn("dataset old-analysis: adopted from an earlier layout; add its DATASET.toml", out)
        self.assertIn("calculator old-maths: adopted from an earlier layout; add its CALCULATOR.md", out)
        self.assertNotIn("DATASET.toml is missing", out)

    def test_units_need_a_study_and_a_question(self):
        self.assertEqual(run("new", "dataset", "x-data", "--study", str(self.study()))[0], 1)
        self.assertEqual(run("new", "calculator", "x-calc", "-q", "?", "--study", str(self.tmp))[0], 1)

    def test_exploratory_unit_gets_a_build_note_not_a_claim(self):
        repo = self.study()
        self.assertEqual(run("new", "app", "tone-sketch", "-q", "A tone viewer", "--study", str(repo), "--exploratory")[0], 0)
        self.assertEqual(run("new", "dataset", "assr", "-q", "A first look", "--study", str(repo), "--exploratory")[0], 0)
        self.assertEqual(run("new", "calculator", "spl", "-q", "Level sums", "--study", str(repo), "--exploratory")[0], 0)
        self.assertEqual(run("new", "sim", "cochlea", "-q", "A filterbank", "--inside", str(repo), "--exploratory")[0], 0)
        self.assertEqual(run("new", "tool", "meter", "-j", "Reads a level", "--inside", str(repo), "--exploratory")[0], 0)
        for unit, doc in (("apps/tone-sketch/v1", "README.md"), ("datasets/assr", "README.md"),
                          ("calculators/spl", "CALCULATOR.md"), ("sims/cochlea", "README.md"), ("tools/meter", "README.md")):
            rec = scaffold.load_toml(repo / unit / "SCOPE.toml")
            self.assertEqual((rec["format"], rec["stage"]), (3, "exploratory"), unit)
            self.assertTrue(rec["exploration"]["building"], unit)
            self.assertRegex(rec["exploration"]["started"], r"^\d{4}-\d{2}-\d{2}$")
            self.assertEqual(rec["claim"]["text"], "", unit)  # no claim is asked for or invented
            self.assertIn("**Scope:** exploratory", (repo / unit / doc).read_text(), unit)
        self.assertEqual(scaffold.load_toml(repo / "apps/tone-sketch/v1/SCOPE.toml")["exploration"]["building"],
                         "A tone viewer")
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        # without the flag nothing is written: the session settles the claim (the kit's SCOPE_PROTOCOL.md)
        self.assertEqual(run("new", "dataset", "mmn", "-q", "Is it there?", "--study", str(repo))[0], 0)
        self.assertFalse((repo / "datasets" / "mmn" / "SCOPE.toml").exists())

    def test_a_study_starts_from_a_goal_and_a_rough_approach(self):
        code, out = run("new", "study", "reef", "--goal", "Map how reef sound changes with season",
                        "--approach", "Record at two sites monthly and compare spectra", "--dir", str(self.tmp),
                        "--profile", "example", "--visibility", "private", "--no-git")
        self.assertEqual(code, 0, out)
        self.assertIn("size it with the person first", out)
        repo = self.tmp / "reef"
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        h = scaffold.load_toml(repo / "HYPOTHESIS.toml")
        self.assertEqual((h["mode"], h["hypothesis"], h["scope"]), ("exploratory", "", ""))
        self.assertEqual(h["goal"], "Map how reef sound changes with season")
        self.assertEqual(h["approach"], "Record at two sites monthly and compare spectra")
        self.assertEqual((h["elements"][0]["status"], h["elements"][0]["basis"]), ("exploratory", "exploratory"))
        readme = (repo / "README.md").read_text()
        self.assertIn("**Scope:** exploratory", readme)
        self.assertIn("**Rough approach:** Record at two sites", readme)
        self.assertEqual(scaffold.load_toml(repo / "STUDY.toml")["question"], h["goal"])
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)  # no claim, no counts-against: still passes
        self.assertIn("scope is not decided yet", out)
        path = repo / "HYPOTHESIS.toml"
        path.write_text(path.read_text().replace('scope = ""', 'scope = "split: seasons, sites"')
                        .replace('scope_decided = ""', 'scope_decided = "2026-10-28"'))
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertNotIn("scope is not decided", out)
        path.write_text(path.read_text().replace('scope = "split: seasons, sites"', 'scope = "maybe"'))
        self.assertIn('scope must be "one" or "split: a, b"', run("check", str(repo))[1])
        manifest = repo / "STUDY.toml"
        manifest.write_text(manifest.read_text().replace('stage = "SKETCH"', 'stage = "PROBE"'))
        self.assertIn("an exploratory study stays at SKETCH", run("check", str(repo))[1])

    def test_exploratory_work_needs_no_licence_yet(self):
        """The person's decision (2026-10-29): an exploratory study or tool needs no LICENSE; claimed work does."""
        code, out = run("new", "study", "drift", "--goal", "See how drift sounds", "--approach", "Listen, then look",
                        "--dir", str(self.tmp), "--profile", "example", "--visibility", "private", "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / "drift"
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        (repo / "LICENSE").unlink()
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("LICENSE is missing: not needed while exploratory", out)
        claimed = self.study()
        (claimed / "LICENSE").unlink()
        code, out = run("check", str(claimed))
        self.assertEqual(code, 1, out)
        self.assertIn("LICENSE is missing", out)
        self.assertNotIn("not needed while exploratory", out)
        tool = self.tmp / "gauge"
        self.assertEqual(run("new", "tool", "gauge", "--goal", "Read levels", "--approach", "A meter",
                             "--dir", str(self.tmp), "--profile", "example", "--visibility", "private",
                             "--no-git")[0], 0)
        (tool / "LICENSE").unlink()
        self.assertIn("not needed while exploratory", run("check", str(tool))[1])

    def test_a_tool_starts_from_a_goal_and_a_claim_is_opt_in(self):
        code, out = run("new", "tool", "gauge", "--goal", "Read sound levels for any study", "--approach",
                        "Wrap the calibrated meter code", "--dir", str(self.tmp), "--profile", "example",
                        "--visibility", "public", "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / "gauge"
        rec = scaffold.load_toml(repo / "SCOPE.toml")
        self.assertEqual((rec["stage"], rec["exploration"]["building"]),
                         ("exploratory", "Read sound levels for any study"))
        self.assertEqual((rec["exploration"]["approach"], rec["exploration"]["scope"]),
                         ("Wrap the calibrated meter code", ""))
        self.assertEqual(scaffold.load_toml(repo / "TOOL.toml")["job"], "Read sound levels for any study")
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        add_kit_block(repo)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertIn("scope is not decided yet", out)
        code, out = run("new", "tool", "meter", "-j", "Reads a level", "--dir", str(self.tmp), "--profile",
                        "example", "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("--approach", out)
        code, out = run("new", "tool", "meter", "-j", "Reads a level", "--claim", "--dir", str(self.tmp),
                        "--profile", "example", "--no-git")
        self.assertEqual(code, 0, out)  # the claim-first start is still there, on request
        self.assertFalse((self.tmp / "meter" / "SCOPE.toml").exists())
        code, out = run("new", "tool", "dial", "-j", "x", "--claim", "--approach", "y", "--dir", str(self.tmp),
                        "--profile", "example", "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("--approach is for", out)

    def test_exploratory_is_for_studies_and_units_not_workbenches(self):
        code, out = run("new", "workbench", "reefs", "-q", "x", "--dir", str(self.tmp), "--profile", "example",
                        "--exploratory")
        self.assertEqual(code, 1)
        self.assertIn("starts with its question", out)
        code, out = run("new", "sim", "wave", "-q", "A wave model", "--dir", str(self.tmp), "--profile", "example",
                        "--exploratory", "--no-git")
        self.assertEqual(code, 0, out)
        self.assertEqual(scaffold.load_toml(self.tmp / "wave" / "SCOPE.toml")["stage"], "exploratory")
        self.assertIn("**Scope:** exploratory", (self.tmp / "wave" / "README.md").read_text())

    def test_exploratory_unit_says_so_and_has_no_experiments(self):
        repo = self.study()
        run("new", "dataset", "assr", "-q", "A first look", "--study", str(repo), "--exploratory")
        unit = repo / "datasets" / "assr"
        (unit / "preregistrations" / "E01-first").mkdir(parents=True)
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("datasets/assr: exploratory, yet it has preregistered experiments (E01-first)", out)
        scope = unit / "SCOPE.toml"
        scope.write_text(scope.read_text().replace('stage = "exploratory"', 'stage = "testing"'))
        self.assertEqual(run("check", str(repo))[0], 0)  # with its claim stage, experiments are expected
        scope.write_text(scope.read_text().replace('stage = "testing"', 'stage = "exploratory"'))
        shutil.rmtree(unit / "preregistrations" / "E01-first")
        readme = unit / "README.md"
        readme.write_text(readme.read_text().replace(scaffold.EXPLORATORY_LABEL, ""))
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("datasets/assr: SCOPE.toml says exploratory, but its README doesn't", out)

    def test_tool_holds_no_preregistrations(self):
        repo = self.tool()
        (repo / "preregistrations").mkdir()
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        self.assertIn("preregistrations is research", out)

    # -------------------------------------------------------------------------------- versions

    def test_every_release_has_upgrade_notes(self):
        changelog = (ROOT / "CHANGELOG.md").read_text()
        upgrading = (ROOT / "UPGRADING.md").read_text()
        for v in re.findall(r"^## (v\d+\.\d+\.\d+)", changelog, re.M):
            if scaffold.parse_version(v) >= (0, 2, 0):
                self.assertIn(f"\n## {v}\n", upgrading, f"UPGRADING.md has no section for {v}")

    def test_version_says_when_a_repo_is_behind_and_how_to_upgrade(self):
        repo = self.study()
        code, out = run("version", str(repo), "--offline")
        self.assertEqual(code, 0)
        self.assertIn(f"follows scaffold {scaffold.SCAFFOLD_REF}, the release this checkout is", out)
        self.assertEqual(run("version", str(repo), "--offline", "--hook")[1], "")  # quiet when current

        lock = scaffold.read_lock(repo)
        lock["scaffold"] = "v0.2.0"
        (repo / scaffold.LOCK).write_text(scaffold.json.dumps(lock))
        code, out = run("version", str(repo), "--offline", "--hook")
        self.assertEqual(code, 0)
        self.assertIn(f"follows scaffold v0.2.0; {scaffold.SCAFFOLD_REF} is available", out)
        self.assertIn("offer to upgrade", out)
        self.assertIn("## v0.3.0", out)
        self.assertNotIn("## v0.2.0", out)  # already there
        self.assertIn("## v0.3.0", run("update", str(repo))[1])

    def test_version_without_a_lock_or_manifest(self):
        repo = self.study()
        (repo / scaffold.LOCK).unlink()
        self.assertIn("no .scaffold.lock", run("version", str(repo), "--offline")[1])
        self.assertEqual(run("version", str(self.tmp), "--offline", "--hook"), (0, ""))

    def test_new_repo_gets_the_session_hook_beside_the_kits(self):
        repo = self.study()
        settings = scaffold.json.loads((repo / ".claude" / "settings.json").read_text())
        commands = [h["command"] for g in settings["hooks"]["SessionStart"] for h in g["hooks"]]
        self.assertEqual(sum(scaffold.HOOK_MARK in c for c in commands), 1)
        self.assertIn("scaffold version", (repo / "AGENTS.md").read_text())

        kit = {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "kit_ap check --hook"}]}],
                         "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "prereg-status"}]}]}}
        merged = scaffold.json.loads(scaffold.with_session_hook(scaffold.with_session_hook(scaffold.json.dumps(kit))))
        commands = [h["command"] for g in merged["hooks"]["SessionStart"] for h in g["hooks"]]
        self.assertIn("kit_ap check --hook", commands)
        self.assertEqual(sum(scaffold.HOOK_MARK in c for c in commands), 1)
        self.assertEqual(merged["hooks"]["UserPromptSubmit"], kit["hooks"]["UserPromptSubmit"])

    def test_update_adds_the_hook_to_an_adopted_repo_only_when_asked(self):
        repo = self.study()
        (repo / scaffold.LOCK).unlink()
        (repo / ".claude" / "settings.json").write_text('{"hooks": {}}\n')
        self.committed(repo)
        self.assertEqual(self.plan(repo)[".claude/settings.json"], "missing")
        self.assertEqual(run("update", str(repo), "--apply", "--adopt", ".claude/settings.json")[0], 0)
        self.assertIn(scaffold.HOOK_MARK, (repo / ".claude" / "settings.json").read_text())

    # ------------------------------------------------------------------------------- workbench

    def workbench(self, name="bench", visibility="private"):
        code, out = run("new", "workbench", name, "-q", "How the senses reach attention and memory",
                        "--dir", str(self.tmp), "--profile", "example", "--visibility", visibility, "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / name
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        return repo

    def test_workbench_holds_studies_and_general_units(self):
        bench = self.workbench()
        self.assertEqual(run("check", str(bench))[0], 0)
        code, out = run("new", "study", "hearing", "-q", "Does it?", "--hypothesis", "Does it?",
                        "--inside", str(bench))
        self.assertEqual(code, 0, out)
        study = bench / "studies" / "hearing"
        self.assertTrue((study / "STUDY.toml").exists())
        for shared in (".github", "Makefile", "LICENSE", ".scaffold.lock", "CLAUDE.md", ".git", ".claude"):
            self.assertFalse((study / shared).exists(), shared)  # the workbench's, not the study's
        self.assertIn('[[studies]]\nslug = "hearing"\npath = "studies/hearing"', (bench / "WORKBENCH.toml").read_text())
        self.assertNotIn("visibility", (study / "STUDY.toml").read_text())  # the workbench decides it

        self.assertEqual(run("new", "app", "tone-explorer", "-q", "Hear it?", "--study", str(study))[0], 0)
        self.assertEqual(run("new", "sim", "cochlea", "-q", "A filterbank", "--inside", str(study))[0], 0)
        self.assertEqual(run("new", "tool", "level-meter", "-j", "Reads a level", "--claim", "--inside",
                             str(study))[0], 0)
        self.assertEqual(run("new", "dataset", "assr", "-q", "40 Hz?", "--study", str(study))[0], 0)
        self.assertEqual(run("new", "tool", "plotter", "-j", "Plots", "--claim", "--inside", str(bench))[0], 0)
        self.assertEqual(run("new", "sim", "tissue", "-q", "General", "--inside", str(bench))[0], 0)
        self.assertIn('path = "tools/level-meter"', (study / "STUDY.toml").read_text())
        self.assertTrue((bench / "tools" / "plotter" / "README.md").exists())
        code, out = run("check", str(bench))
        self.assertEqual(code, 0, out)

    def test_workbench_checks_the_studies_inside_it(self):
        bench = self.workbench()
        self.assertEqual(run("new", "study", "hearing", "-q", "Does it?", "--hypothesis", "Does it?",
                             "--inside", str(bench))[0], 0)
        manifest = bench / "studies" / "hearing" / "STUDY.toml"
        manifest.write_text(manifest.read_text().replace('stage = "SKETCH"', 'stage = "DONE"')
                            + '\n[[tools]]\nslug = "gone"\npath = "tools/gone"\n')
        (bench / "studies" / "stray").mkdir()
        code, out = run("check", str(bench))
        self.assertEqual(code, 1)
        for needle in ("hearing: stage 'DONE'", "hearing: tool gone: tools/gone does not exist",
                       "studies/stray is not registered"):
            self.assertIn(needle, out)

    def test_workbench_with_private_folders_must_be_private(self):
        bench = self.workbench("open-bench", visibility="public")
        (bench / "recordings").mkdir()
        m = bench / "WORKBENCH.toml"
        m.write_text(m.read_text().replace("private = []", 'private = ["recordings", "absent"]'))
        code, out = run("check", str(bench))
        self.assertEqual(code, 1)
        self.assertIn("visibility must be 'private'", out)
        self.assertIn("private folder 'absent' does not exist", out)

    def test_what_goes_inside_what(self):
        bench, study = self.workbench(), self.study()
        for args, needle in ((["study", "s2", "-q", "?", "--inside", str(study)], "goes --inside a workbench"),
                             (["workbench", "w2", "-q", "?", "--inside", str(bench)], "always its own repo"),
                             (["sim", "s3", "-q", "?", "--inside", str(self.tmp)], "no STUDY.toml or WORKBENCH.toml")):
            code, out = run("new", *args)
            self.assertEqual(code, 1, args)
            self.assertIn(needle, out)

    def test_prefixed_names_are_refused(self):
        for bad in ("lab-reef-acoustics", "sim-sound-propagation", "Study", "x"):
            self.assertEqual(run("new", "study", bad, "-q", "?", "--dir", str(self.tmp), "--no-git")[0], 1, bad)

    def test_broken_study_fails(self):
        repo = self.study()
        manifest = repo / "STUDY.toml"
        manifest.write_text(manifest.read_text().replace('stage = "SKETCH"', 'stage = "DONE"')
                            + '\n[[sims]]\nslug = "ext"\nrepo = "o/ext"\nref = "main"\n'
                            + '\n[[apps]]\nversion = "v1"\nslug = "gone"\n')
        (repo / "LICENSE").unlink()
        (repo / ".gitmodules").write_text('[submodule "research"]\n\turl = https://github.com/polarizetech/research.git\n')
        code, out = run("check", str(repo))
        self.assertEqual(code, 1)
        for needle in ("stage 'DONE'", "LICENSE is missing", "pinned to a tag", "apps/gone/v1", "is a submodule",
                       "README stage SKETCH disagrees"):
            self.assertIn(needle, out)

    def test_legacy_paths_are_honoured(self):
        repo = self.study()
        (repo / "projects" / "old-ui").mkdir(parents=True)
        (repo / "projects" / "old-ui" / "index.html").write_text("<html></html>")
        with (repo / "STUDY.toml").open("a") as f:
            f.write('\n[[apps]]\nversion = "v1"\nslug = "old-ui"\npath = "projects/old-ui"\nstatus = "superseded"\n')
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_absolute_paths_warn_but_do_not_fail(self):
        repo = self.study()
        (repo / "notes.md").write_text("see /Users/someone/Sites/thing\n")
        subprocess.run(["git", "add", "notes.md"], cwd=repo, check=True)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0)
        self.assertIn("absolute home-directory path", out)

    def test_release_version_agrees(self):
        ref = scaffold.template_vars({}, "x", "?")["scaffold_ref"]
        citation = re.search(r"^version: (\S+)$", (ROOT / "CITATION.cff").read_text(), re.M).group(1)
        changelog = re.search(r"^## (v\S+)", (ROOT / "CHANGELOG.md").read_text(), re.M).group(1)
        self.assertEqual((ref, changelog), (f"v{citation}", f"v{citation}"),
                         "scaffold_ref, CITATION.cff and the newest CHANGELOG heading must name the same release")

    def test_mini_toml_reads_multiline_arrays(self):
        """Runs on every Python: the built-in parser is the only one 3.9 and 3.10 have."""
        p = ROOT / "tests" / "fixtures" / "multiline.toml"
        m = scaffold._mini_toml(p.read_text(encoding="utf-8"), p)
        self.assertEqual(m["job"], "Records one channel at 250 Hz, in µV")
        self.assertEqual(m["empty"], [])
        self.assertEqual(m["flat"], ["a", "b # not a comment", "lit]eral"])
        self.assertEqual([c["name"] for c in m["consumers"]], ["colony", "bench"])
        self.assertEqual(m["consumers"][0]["uses"], ["apps/server/rig.py UV_PER_COUNT", "GET /status rateMeasured",
                                                     "black-box CSV format sample_index,value,t_us"])
        self.assertEqual(m["consumers"][1]["uses"], ["one", "two", "three"])
        with self.assertRaises(scaffold.Fail):
            scaffold._mini_toml('uses = [\n  "never closed",\n', "open.toml")
        with self.assertRaises(scaffold.Fail):
            scaffold._mini_toml('state = "one"\nstate = "two"\n', "duplicate.toml")

    def test_mini_toml_matches_tomllib(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest("tomllib needs Python 3.11+")
        rendered = self.tmp / "rendered"
        for kind in ("study", "sim", "tool"):
            scaffold.render(scaffold.TEMPLATES / kind, rendered / kind,
                            {**scaffold.template_vars({}, "x", "Does it?"), "job": "Does a job",
                             "hypothesis_toml": scaffold.toml_str("Does it?"),
                             "visibility": "private", "visibility_decided": "2026-01-01"})
        for p in [*sorted((ROOT / "profiles").glob("*.toml")), ROOT / "tests" / "fixtures" / "multiline.toml",
                  *sorted(rendered.glob("*/*.toml"))]:
            text = p.read_text(encoding="utf-8")
            self.assertEqual(scaffold._mini_toml(text, p), tomllib.loads(text), p.name)


if __name__ == "__main__":
    unittest.main()
