# SPDX-License-Identifier: MIT
"""End-to-end: render every template, check it passes; break it, check it fails."""
import importlib.machinery
import importlib.util
import io
import os
import shutil
import subprocess
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
    (repo / "AGENTS.md").write_text("<!-- kit_ap:start -->\n<!-- kit_ap:end -->\n")


class Scaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._env = {k: os.environ.get(k) for k in GIT_ENV}
        os.environ.update(GIT_ENV)
        os.environ.pop("KIT_AP", None)

    def tearDown(self):
        shutil.rmtree(self.tmp)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def study(self, name="colony", profile="polarizetech"):
        code, out = run("new", "study", name, "-q", "Does it?", "--dir", str(self.tmp), "--profile", profile,
                        "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / name
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        return repo

    def test_new_study_passes_check(self):
        repo = self.study()
        self.assertEqual(run("new", "app", "explorer", "-q", "Look?", "--study", str(repo))[0], 0)
        self.assertEqual(run("new", "app", "second", "-q", "Again?", "--study", str(repo))[0], 0)
        self.assertEqual(run("new", "sim", "model-a", "-q", "Sim", "--inside", str(repo))[0], 0)
        self.assertTrue((repo / "apps" / "v2-second" / "index.html").exists())
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertNotIn("{{", "".join(p.read_text() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts))

    def test_example_profile_has_no_workbench_resolver(self):
        repo = self.study("plain", profile="example")
        self.assertFalse((repo / "shared" / "workbench.py").exists())
        self.assertEqual(run("check", str(repo))[0], 0)

    def test_new_sim_standalone(self):
        self.assertEqual(run("new", "sim", "memory", "-q", "Tape", "--dir", str(self.tmp), "--no-git")[0], 0)
        repo = self.tmp / "memory"
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)

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
        for needle in ("stage 'DONE'", "LICENSE is missing", "pinned to a tag", "apps/v1-gone", "is a submodule",
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

    def test_mini_toml_matches_tomllib(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest("tomllib needs Python 3.11+")
        for p in [*sorted((ROOT / "profiles").glob("*.toml"))]:
            self.assertEqual(scaffold._mini_toml(p.read_text(), p), tomllib.loads(p.read_text()), p.name)


if __name__ == "__main__":
    unittest.main()
