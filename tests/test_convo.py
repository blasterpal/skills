import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "skills/convo/scripts/convo.py"


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.env = {**os.environ, "XDG_CONFIG_HOME": str(self.base / "config")}
        for key in ("CONVO_PROFILE", "HQ_DOM", "CODEX_THREAD_ID", "OPENCODE", "CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID"):
            self.env.pop(key, None)
        self.store = self.base / "context with spaces/convos"

    def run_helper(self, *args, code=0, stdin=None, cwd=None):
        result = subprocess.run(["python3", str(HELPER), *args], env=self.env, input=stdin, cwd=cwd,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stderr)
        return result

    def setup_store(self, profile="me", root=None):
        self.run_helper("--dom", profile, "setup", "--root", str(root or self.store))

    def write_config(self, config):
        file = self.base / "config/convo/config.json"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(config))

    def write_snapshot(self, slug="test-topic", title="A test topic", date=None, root=None, body=None):
        date = date or dt.date.today().isoformat()
        file = (root or self.store) / date[:7] / f"{date}-{slug}.md"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(body if body is not None else
                        f"---\ntitle: {json.dumps(title)}\nslug: {slug}\nproject: general\n---\n\n# {title}\n")
        return file

    def configure_profiles(self):
        self.work = self.base / "work/convos"
        self.work.mkdir(parents=True)
        self.store.mkdir(parents=True)
        self.write_config({
            "default": "work",
            "profile_env": ["HQ_DOM"],
            "profiles": {
                "me": {"root": str(self.store), "aliases": ["hq"], "dirs": [str(self.store.parent)]},
                "work": {"root": str(self.work), "dirs": [str(self.work.parent)]},
            },
        })


class ConvoTests(Base):
    def test_first_use_waits_for_a_destination(self):
        for command in ("root", "setup", "recent"):
            result = self.run_helper(command, code=3)
            self.assertIn("SETUP_REQUIRED", result.stderr)
        self.assertFalse((self.base / "config").exists())
        self.assertFalse(self.store.exists())

    def test_one_folder_needs_no_profile_anywhere(self):
        self.run_helper("setup", "--root", str(self.store))
        config = json.loads((self.base / "config/convo/config.json").read_text())
        self.assertEqual(config, {"profiles": {"me": str(self.store)}})
        self.write_snapshot(slug="work-notes", title="Work notes")
        out = self.run_helper("preload", "--stdin", stdin="save work notes\n", cwd=str(self.base)).stdout
        self.assertIn("REQUEST=save work notes\nPROFILE=me\n", out)
        self.assertIn("|work-notes|general|Work notes", out)
        self.assertNotIn("CONVO.md", out)
        self.assertEqual(self.run_helper("--profile", "me", "root").stdout.strip(), str(self.store))

    def test_setup_persists_and_profiles_are_separate(self):
        self.setup_store()
        other = self.base / "other/convos"
        self.setup_store("work", other)
        self.write_snapshot()
        self.assertEqual(self.run_helper("root").stdout.strip(), str(self.store))
        self.assertEqual(json.loads(self.run_helper("--profile", "work", "recent").stdout), [])
        config = json.loads((self.base / "config/convo/config.json").read_text())
        self.assertEqual(config["profiles"], {"me": str(self.store), "work": str(other)})

    def test_list_recent_show_and_register(self):
        self.setup_store()
        file = self.write_snapshot(title="A title: with | punctuation")
        old = (dt.date.today() - dt.timedelta(days=60)).isoformat()
        self.write_snapshot("old-topic", date=old)
        rows = json.loads(self.run_helper("list", "title:").stdout)
        self.assertEqual([row["path"] for row in rows], [str(file)])
        self.assertEqual(len(json.loads(self.run_helper("recent").stdout)), 2)
        shown = self.run_helper("show", "test-topic").stdout
        self.assertEqual(shown, f"CONVO={file}\n" + file.read_text())
        self.run_helper("register", str(file))
        self.assertTrue((self.store / "index.tsv").is_file())
        file.unlink()
        self.assertEqual(len(json.loads(self.run_helper("recent").stdout)), 1)

    def test_memos_and_plans_are_not_snapshots(self):
        self.setup_store()
        file = self.write_snapshot()
        for name in ("memos", "plans"):
            target = file.parent / name / file.name
            target.parent.mkdir()
            target.write_text(file.read_text())
            self.run_helper("show", str(target), code=2)
        self.assertEqual(len(json.loads(self.run_helper("recent").stdout)), 1)

    def test_paths_cannot_escape_the_store(self):
        self.setup_store()
        outside = self.write_snapshot(root=self.base / "outside")
        self.run_helper("show", str(outside), code=2)
        self.run_helper("register", str(outside), code=2)
        self.run_helper("show", "../../outside/" + str(outside.relative_to(self.base / "outside")), code=2)
        link = self.store / outside.parent.name
        link.symlink_to(outside.parent, target_is_directory=True)
        self.run_helper("show", str(link / outside.name), code=2)

    def test_duplicate_slugs_preserve_the_existing_index(self):
        self.setup_store()
        file = self.write_snapshot()
        self.run_helper("register", str(file))
        original = (self.store / "index.tsv").read_bytes()
        yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
        self.write_snapshot(date=yesterday)
        result = self.run_helper("build-index", code=2)
        self.assertIn("duplicate slug", result.stderr)
        self.assertEqual((self.store / "index.tsv").read_bytes(), original)

    def test_prepare_save_reports_existing_target_and_known_session(self):
        self.setup_store()
        file = self.write_snapshot()
        self.env["CODEX_THREAD_ID"] = "test-session"
        data = json.loads(self.run_helper("prepare-save", "test-topic").stdout)
        self.assertEqual(data["slug_matches"][0]["path"], str(file))
        self.assertEqual(data["new_path"], str(file))
        self.assertEqual(data["session_ref"], "codex:test-session")
        self.assertIsNotNone(dt.datetime.fromisoformat(data["created_at"]).tzinfo)

    def test_last_uses_save_time_including_amendments(self):
        self.setup_store()
        older = self.write_snapshot("older", date="2025-01-01")
        newer = self.write_snapshot("newer")
        os.utime(newer, (100, 100))
        os.utime(older, (200, 200))
        self.assertTrue(self.run_helper("last").stdout.startswith(f"CONVO={older}\n"))

    def test_files_outside_the_layout_are_skipped_not_fatal(self):
        self.setup_store()
        kept = self.write_snapshot()
        dotted = self.write_snapshot("policy-v3.5", body="---\ndate: 2026-09-04\ntopic: legacy pointer\n---\n")
        self.write_snapshot("Bad Name", body="# no frontmatter\n")
        result = self.run_helper("recent")
        rows = json.loads(result.stdout)
        self.assertEqual({row["path"] for row in rows}, {str(kept), str(dotted)})
        self.assertEqual([row["slug"] for row in rows if row["path"] == str(dotted)], ["policy-v3.5"])
        self.assertIn("skipping", result.stderr)
        self.assertIn("Bad Name", result.stderr)
        self.run_helper("prepare-save", "policy-v3.5", code=2)


class ProfileTests(Base):
    def setUp(self):
        super().setUp()
        self.configure_profiles()

    def test_profile_from_env_dirs_and_default(self):
        self.assertEqual(self.run_helper("root").stdout.strip(), str(self.work))
        self.env["HQ_DOM"] = "hq"
        self.assertEqual(self.run_helper("root").stdout.strip(), str(self.store))
        self.env["CONVO_PROFILE"] = "work"
        self.assertEqual(self.run_helper("root").stdout.strip(), str(self.work))
        self.env.pop("CONVO_PROFILE")
        self.env.pop("HQ_DOM")
        self.assertEqual(self.run_helper("root", cwd=str(self.store)).stdout.strip(), str(self.store))
        self.assertEqual(self.run_helper("--dom", "hq", "root", cwd=str(self.work)).stdout.strip(), str(self.store))
        self.env["HQ_DOM"] = "nowhere"
        self.assertIn("SETUP_REQUIRED", self.run_helper("root", code=3).stderr)

    def test_alias_and_relative_refs_stay_inside_the_profile(self):
        file = self.write_snapshot()
        relative = f"{file.parent.name}/{file.name}"
        for ref in (f"hq:convos/{relative}", f"me:convos/{relative}", f"convos/{relative}", relative):
            self.assertTrue(self.run_helper("--dom", "me", "show", ref).stdout.startswith(f"CONVO={file}\n"), ref)
        result = self.run_helper("--dom", "work", "show", f"hq:convos/{relative}", code=2)
        self.assertIn("belongs to profile me", result.stderr)
        self.run_helper("--dom", "me", "show", f"nope:convos/{relative}", code=2)

    def test_setup_keeps_other_profile_settings(self):
        moved = self.base / "moved/convos"
        self.run_helper("--dom", "me", "setup", "--root", str(moved))
        config = json.loads((self.base / "config/convo/config.json").read_text())
        self.assertEqual(config["profiles"]["me"]["root"], str(moved))
        self.assertEqual(config["profiles"]["me"]["aliases"], ["hq"])
        settings = json.loads(self.run_helper("--dom", "me", "setup").stdout)
        self.assertEqual(settings["profile"], "me")
        self.assertEqual(settings["root"], str(moved))


class PreloadTests(Base):
    def setUp(self):
        super().setUp()
        self.configure_profiles()

    def preload(self, request, *args, **kwargs):
        return self.run_helper(*args, "preload", "--stdin", stdin=request, **kwargs).stdout

    def test_read_prints_the_snapshot_and_reference(self):
        file = self.write_snapshot()
        out = self.preload("me read test-topic\n")
        self.assertIn("REQUEST=me read test-topic\nPROFILE=me\n", out)
        self.assertIn(f"CONVO={file}\n", out)
        self.assertIn("# A test topic", out)
        self.assertIn("===== references/read.md =====\n# Reading snapshots", out)
        self.assertTrue((self.store / "index.tsv").is_file())

    def test_profile_word_after_the_verb_and_failures(self):
        self.write_snapshot()
        out = self.preload("read me missing-topic")
        self.assertIn("PROFILE=me\nSHOW_FAILED=exit 1 for ref: missing-topic\n", out)
        self.assertIn("RECENT (DATE|REF|PROJECT|TITLE, newest first):", out)
        self.assertIn("|test-topic|general|A test topic", out)
        out = self.preload("recent me --episodic nothing-here")
        self.assertIn("EPISODIC_REQUESTED=1\n", out)
        self.assertIn("NO_TITLE_MATCH=nothing-here\n", out)
        out = self.preload("read me 0123456789abcdef")
        self.assertIn("EPISODIC_REF=0123456789abcdef\n", out)
        self.assertNotIn("\nSHOW_FAILED=", out)

    def test_save_metadata_hook_and_instructions(self):
        file = self.write_snapshot()
        hook = self.base / "hook.sh"
        hook.write_text('#!/bin/sh\necho "HOOK_ROOT=$CONVO_ROOT"\necho "HOOK_PROFILE=$CONVO_PROFILE"\n')
        hook.chmod(0o755)
        notes = self.store / "CONVO.md"
        notes.write_text("# Local rules\nAlways link the todo.\n")
        config = json.loads((self.base / "config/convo/config.json").read_text())
        config["profiles"]["me"]["save_hook"] = str(hook)
        self.write_config(config)
        out = self.run_helper("preload", "--stdin", "claude:abc", stdin="save me", cwd=str(self.work)).stdout
        self.assertIn("PROFILE=me\nCREATED_AT=", out)
        self.assertIn("SESSION_REF=claude:abc\n", out)
        self.assertIn(f"CONVO_ROOT={self.store}\nTODAY={dt.date.today().isoformat()}\n", out)
        self.assertIn(f"TODAY_CONVO=test-topic|{file}|A test topic|general\n", out)
        self.assertIn(f"HOOK_ROOT={self.store}\nHOOK_PROFILE=me\n", out)
        self.assertIn("===== references/save.md =====", out)
        self.assertIn(f"===== {notes} =====\n# Local rules", out)
        out = self.preload("save me", "--dom", "work")
        self.assertIn("PROFILE=me\n", out)
        out = self.run_helper("preload", "--stdin", "claude:${CLAUDE_SESSION_ID}", stdin="$ARGUMENTS").stdout
        self.assertIn("REQUEST=<none>\nPROFILE=work\n", out)
        self.assertIn("SESSION_REF=\n", out)


class LinkTests(unittest.TestCase):
    def test_dry_run_link_repeat_relink_and_directory_conflict(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            env = {**os.environ, "HOME": str(base), "XDG_CONFIG_HOME": str(base / "config")}
            script = REPO / "scripts/link-skills.sh"
            subprocess.run([str(script), "--dry-run"], env=env, check=True, capture_output=True)
            self.assertEqual(list(base.iterdir()), [])
            subprocess.run([str(script)], env=env, check=True, capture_output=True)
            dests = [base / ".claude/skills", base / ".agents/skills", base / "config/opencode/skills"]
            for dest in dests:
                self.assertEqual((dest / "convo").resolve(), REPO / "skills/convo")
            repeated = subprocess.run([str(script)], env=env, check=True, capture_output=True, text=True)
            self.assertNotIn("relink", repeated.stdout)
            target = dests[0] / "convo"
            target.unlink()
            target.symlink_to(base / "missing")
            subprocess.run([str(script)], env=env, check=True, capture_output=True)
            self.assertEqual(target.resolve(), REPO / "skills/convo")
            target.unlink()
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("keep")
            conflict = subprocess.run([str(script)], env=env, capture_output=True, text=True)
            self.assertEqual(conflict.returncode, 1)
            self.assertEqual(marker.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
