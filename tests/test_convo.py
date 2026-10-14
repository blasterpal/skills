import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "skills/convo/scripts/convo.py"


class ConvoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.env = {**os.environ, "XDG_CONFIG_HOME": str(self.base / "config")}
        self.store = self.base / "context with spaces/convos"

    def run_helper(self, *args, code=0):
        result = subprocess.run(["python3", str(HELPER), *args], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stderr)
        return result

    def setup_store(self, profile="me", root=None):
        self.run_helper("--dom", profile, "setup", "--root", str(root or self.store))

    def write_snapshot(self, slug="test-topic", title="A test topic", date=None, root=None):
        date = date or dt.date.today().isoformat()
        file = (root or self.store) / date[:7] / f"{date}-{slug}.md"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(f"---\ntitle: {json.dumps(title)}\nslug: {slug}\nproject: general\n---\n\n# {title}\n")
        return file

    def test_first_use_waits_for_a_destination(self):
        for command in ("root", "setup", "recent"):
            result = self.run_helper(command, code=3)
            self.assertIn("SETUP_REQUIRED", result.stderr)
        self.assertFalse((self.base / "config").exists())
        self.assertFalse(self.store.exists())

    def test_setup_persists_and_profiles_are_separate(self):
        self.setup_store()
        other = self.base / "other/convos"
        self.setup_store("work", other)
        self.write_snapshot()
        self.assertEqual(self.run_helper("root").stdout.strip(), str(self.store))
        self.assertEqual(json.loads(self.run_helper("--dom", "work", "recent").stdout), [])
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
