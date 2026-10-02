# SPDX-License-Identifier: MIT
"""End-to-end: render every template, check it passes; break it, check it fails."""
import importlib.machinery
import importlib.util
import io
import os
import re
import shutil
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

    def tearDown(self):
        shutil.rmtree(self.tmp)
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def study(self, name="colony", profile="polarizetech", visibility="private"):
        vis = ["--visibility", visibility] if visibility else []
        code, out = run("new", "study", name, "-q", "Does it?", "--dir", str(self.tmp), "--profile", profile,
                        *vis, "--no-git")
        self.assertEqual(code, 0, out)
        repo = self.tmp / name
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_kit(repo)
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
        self.assertTrue((repo / "apps" / "v2-second" / "index.html").exists())
        code, out = run("check", str(repo))
        self.assertEqual(code, 0, out)
        self.assertNotIn("{{", "".join(p.read_text() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts))

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
        code, out = run("new", "study", "orphan", "-q", "?", "--dir", str(self.tmp), "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("no profile", out)
        self.assertIn("SCAFFOLD_PROFILE", out)
        self.assertFalse((self.tmp / "orphan").exists())

    def test_profile_from_environment(self):
        os.environ["SCAFFOLD_PROFILE"] = "example"
        code, out = run("new", "study", "envy", "-q", "?", "--dir", str(self.tmp), "--no-git")
        self.assertEqual(code, 0, out)
        self.assertEqual(scaffold.load_toml(self.tmp / "envy" / "STUDY.toml")["profile"], "example")

    def test_study_manifest_profile_wins_over_environment(self):
        repo = self.study("pinned", profile="example")
        os.environ["SCAFFOLD_PROFILE"] = "polarizetech"
        self.assertEqual(run("new", "sim", "inner", "-q", "Sim", "--inside", str(repo))[0], 0)
        self.assertEqual(scaffold.load_toml(repo / "sims" / "inner" / "SIM.toml")["profile"], "example")

    def tool(self, name="recorder"):
        code, out = run("new", "tool", name, "-j", "Records a signal", "--dir", str(self.tmp),
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
            code, out = run("new", "tool", "gauge", *args, "--dir", str(self.tmp), "--profile", "example",
                            "--no-git")
            self.assertEqual(code, 1, args)
            self.assertIn("--job", out)
        code, out = run("new", "study", "asks", "-j", "Records", "--dir", str(self.tmp), "--profile", "example",
                        "--no-git")
        self.assertEqual(code, 1)
        self.assertIn("needs --question", out)

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
                        "--study", str(repo))
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
        code, out = run("new", "study", "hearing", "-q", "Does it?", "--inside", str(bench))
        self.assertEqual(code, 0, out)
        study = bench / "studies" / "hearing"
        self.assertTrue((study / "STUDY.toml").exists())
        for shared in (".github", "Makefile", "LICENSE", ".scaffold.lock", "CLAUDE.md", ".git", ".claude"):
            self.assertFalse((study / shared).exists(), shared)  # the workbench's, not the study's
        self.assertIn('[[studies]]\nslug = "hearing"\npath = "studies/hearing"', (bench / "WORKBENCH.toml").read_text())
        self.assertNotIn("visibility", (study / "STUDY.toml").read_text())  # the workbench decides it

        self.assertEqual(run("new", "app", "tone-explorer", "-q", "Hear it?", "--study", str(study))[0], 0)
        self.assertEqual(run("new", "sim", "cochlea", "-q", "A filterbank", "--inside", str(study))[0], 0)
        self.assertEqual(run("new", "tool", "level-meter", "-j", "Reads a level", "--inside", str(study))[0], 0)
        self.assertEqual(run("new", "dataset", "assr", "-q", "40 Hz?", "--study", str(study))[0], 0)
        self.assertEqual(run("new", "tool", "plotter", "-j", "Plots", "--inside", str(bench))[0], 0)  # general
        self.assertEqual(run("new", "sim", "tissue", "-q", "General", "--inside", str(bench))[0], 0)
        self.assertIn('path = "tools/level-meter"', (study / "STUDY.toml").read_text())
        self.assertTrue((bench / "tools" / "plotter" / "README.md").exists())
        code, out = run("check", str(bench))
        self.assertEqual(code, 0, out)

    def test_workbench_checks_the_studies_inside_it(self):
        bench = self.workbench()
        self.assertEqual(run("new", "study", "hearing", "-q", "Does it?", "--inside", str(bench))[0], 0)
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

    def test_mini_toml_matches_tomllib(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest("tomllib needs Python 3.11+")
        rendered = self.tmp / "rendered"
        for kind in ("study", "sim", "tool"):
            scaffold.render(scaffold.TEMPLATES / kind, rendered / kind,
                            {**scaffold.template_vars({}, "x", "Does it?"), "job": "Does a job",
                             "visibility": "private", "visibility_decided": "2026-01-01"})
        for p in [*sorted((ROOT / "profiles").glob("*.toml")), ROOT / "tests" / "fixtures" / "multiline.toml",
                  *sorted(rendered.glob("*/*.toml"))]:
            text = p.read_text(encoding="utf-8")
            self.assertEqual(scaffold._mini_toml(text, p), tomllib.loads(text), p.name)


if __name__ == "__main__":
    unittest.main()
