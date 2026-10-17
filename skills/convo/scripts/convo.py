#!/usr/bin/env python3
"""Local conversation storage; Python standard library only.

Configuration lives in ${XDG_CONFIG_HOME:-~/.config}/convo/config.json. One conversation
folder is the common case, written by `setup --root <folder>`:

    {"profiles": {"me": "/Users/you/context/convos"}}

Several folders are profiles. A profile value is the folder, or a dict with "root" and options:

    {
      "default": "me",
      "profile_env": ["HQ_DOM"],
      "profiles": {
        "me":   "~/context/convos",
        "work": {"root": "~/work/convos", "aliases": ["w"], "dirs": ["~/work"],
                 "instructions": "~/work/convos/CONVO.md", "save_hook": "~/bin/convo-save-hook"}
      }
    }

Profile selection order: --profile (or --dom), then CONVO_PROFILE and any variables listed in
profile_env, then a profile whose dirs contain the working directory, then "default", then "me".
"""

import argparse
import csv
import datetime as dt
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

NEW_SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
STORED_SLUG = r"[A-Za-z0-9][A-Za-z0-9._-]*"
SNAPSHOT_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})-(" + STORED_SLUG + r")\.md")
SKILL_DIR = Path(__file__).resolve().parent.parent
EPISODIC_WORDS = ("--episodic", "-e", "+episodic", "episodic")
LIVE_ROW = "(this session)|general|(not yet saved; run save to record)"


class ConvoError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def warn(message):
    print(f"convo: {message}", file=sys.stderr)


def config_path():
    return Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "convo/config.json"


def load_config():
    file = config_path()
    if not file.exists():
        return {"profiles": {}}
    config = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("profiles"), dict):
        raise ConvoError(f"invalid configuration: {file}")
    for name, value in config["profiles"].items():
        if not isinstance(value, (str, dict)):
            raise ConvoError(f"invalid profile {name} in {file}")
    return config


def profile_settings(config, name):
    """A profile's settings dict; a plain string value is the conversation folder."""
    value = config["profiles"].get(name)
    return {"root": value} if isinstance(value, str) else value


def atomic_write(file, content):
    file.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=file.parent, delete=False) as tmp:
            name = tmp.name
            tmp.write(content)
        os.replace(name, file)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def profile_named(config, word):
    """Canonical profile name for a profile name or alias, or None."""
    if word in config["profiles"]:
        return word
    for name in config["profiles"]:
        if word in profile_settings(config, name).get("aliases", []):
            return name
    return None


def select_profile(config, explicit):
    if explicit:
        return profile_named(config, explicit) or explicit
    for key in ["CONVO_PROFILE"] + list(config.get("profile_env", [])):
        value = os.environ.get(key, "")
        if value:
            name = profile_named(config, value)
            if name is None:
                raise ConvoError(f"SETUP_REQUIRED: {key}={value} names no configured profile", 3)
            return name
    cwd = Path.cwd().resolve()
    best = None
    for name in config["profiles"]:
        for folder in profile_settings(config, name).get("dirs", []):
            folder = Path(folder).expanduser().resolve()
            if (cwd == folder or folder in cwd.parents) and (best is None or len(folder.parts) > len(best[1].parts)):
                best = (name, folder)
    if best:
        return best[0]
    return config.get("default", "me")


def setup_required(config, profile):
    which = f" for profile {profile}" if config["profiles"] else ""
    return ConvoError(f"SETUP_REQUIRED: choose a conversation folder{which}", 3)


def settings_for(config, profile):
    settings = profile_settings(config, profile)
    if settings is None:
        raise setup_required(config, profile)
    return settings


def root_for(config, profile):
    value = settings_for(config, profile).get("root")
    if value is None:
        raise setup_required(config, profile)
    if not isinstance(value, str) or not Path(value).expanduser().is_absolute():
        raise ConvoError(f"invalid conversation folder for profile {profile}")
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ConvoError(f"conversation folder is missing: {root}; restore it or run setup --root <folder>")
    return root


def base_for(config, profile, root):
    """Folder that <alias>:path and convos/... refs are relative to; the root's parent by default."""
    value = settings_for(config, profile).get("base")
    return Path(value).expanduser().resolve() if value else root.parent


def scalar(value):
    value = value.strip()
    if value.startswith('"'):
        decoded = json.loads(value)
        if not isinstance(decoded, str):
            raise ConvoError("title, slug, and project must be strings")
        return decoded
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


def metadata(file):
    fields = {}
    lines = file.read_text(encoding="utf-8").splitlines()
    if lines and lines[0] == "---":
        for line in lines[1:]:
            if line == "---":
                break
            key, sep, value = line.partition(":")
            if sep and key in ("title", "slug", "project"):
                fields[key] = scalar(value)
    return fields


def snapshot_path(root, file):
    resolved = file.resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        raise ConvoError(f"path is outside conversation folder: {file}")
    match = SNAPSHOT_NAME.fullmatch(resolved.name)
    if not match or len(relative.parts) != 2 or relative.parts[0] != match[1][:7]:
        raise ConvoError(f"expected YYYY-MM/YYYY-MM-DD-<slug>.md: {file}")
    dt.date.fromisoformat(match[1])
    if not resolved.is_file():
        raise ConvoError(f"snapshot does not exist: {file}", 1)
    return resolved, match


def snapshots(root):
    """Every readable snapshot; a file that does not fit the layout is skipped with a warning."""
    rows = []
    for file in sorted(root.glob("????-??/*.md")):
        try:
            file, match = snapshot_path(root, file)
            fields = metadata(file)
            slug = fields.get("slug", match[2])
            if not re.fullmatch(STORED_SLUG, slug):
                raise ConvoError(f"invalid slug {slug}")
        except (ConvoError, ValueError) as error:
            warn(f"skipping {file}: {error}")
            continue
        rows.append({"date": match[1], "slug": slug, "title": fields.get("title", slug),
                     "project": fields.get("project", "general"), "path": str(file)})
    return sorted(rows, key=lambda row: (row["date"], row["slug"]), reverse=True)


def duplicate_slugs(rows):
    seen = {}
    for row in rows:
        seen.setdefault(row["slug"], []).append(row["path"])
    return {slug: paths for slug, paths in seen.items() if len(paths) > 1}


def write_index(root, rows):
    for slug, paths in duplicate_slugs(rows).items():
        raise ConvoError(f"duplicate slug {slug}:\n  " + "\n  ".join(paths))
    output = io.StringIO()
    writer = csv.writer(output, delimiter="|", lineterminator="\n")
    for row in rows:
        writer.writerow([row["date"], row["slug"], Path(row["path"]).name, row["project"], row["title"]])
    atomic_write(root / "index.tsv", output.getvalue())
    return root / "index.tsv"


def resolve_ref(config, profile, root, rows, ref):
    if not ref:
        if not rows:
            raise ConvoError("no saved conversations", 1)
        return Path(max(rows, key=lambda row: (Path(row["path"]).stat().st_mtime_ns, row["path"]))["path"])
    alias = re.fullmatch(r"([A-Za-z0-9_-]+):(.+)", ref)
    if alias and not Path(ref).is_absolute():
        other = profile_named(config, alias[1])
        if other is None:
            raise ConvoError(f"{alias[1]} is not a configured profile or alias: {ref}")
        if other != profile:
            raise ConvoError(f"{ref} belongs to profile {other}; rerun with --profile {other}")
        return snapshot_path(root, base_for(config, profile, root) / alias[2])[0]
    if "/" in ref or Path(ref).is_absolute():
        file = Path(ref).expanduser()
        if file.is_absolute():
            return snapshot_path(root, file)[0]
        for candidate in (root / file, base_for(config, profile, root) / file):
            if candidate.exists():
                return snapshot_path(root, candidate)[0]
        return snapshot_path(root, root / file)[0]
    matches = [row["path"] for row in rows if ref in (row["slug"], Path(row["path"]).name)]
    if not matches:
        raise ConvoError(f"no conversation matches {ref}", 1)
    if len(matches) > 1:
        raise ConvoError(f"multiple matches for {ref}:\n  " + "\n  ".join(matches))
    return Path(matches[0])


def session_ref(explicit=""):
    if explicit and not explicit.endswith(":") and "${" not in explicit:
        return explicit
    if os.environ.get("CODEX_THREAD_ID"):
        return "codex:" + os.environ["CODEX_THREAD_ID"]
    if os.environ.get("OPENCODE"):
        return ""
    for key in ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID"):
        if os.environ.get(key):
            return "claude:" + os.environ[key]
    return ""


def instructions_file(config, profile, root):
    """Per-profile instructions appended to preload output: config "instructions", else <root>/CONVO.md."""
    value = settings_for(config, profile).get("instructions")
    file = Path(value).expanduser() if value else root / "CONVO.md"
    return file if file.is_file() else None


def save_hook_output(config, profile, root):
    """Stdout of the profile's save_hook command, run with CONVO_ROOT and CONVO_PROFILE set."""
    command = settings_for(config, profile).get("save_hook")
    if not command:
        return ""
    env = {**os.environ, "CONVO_ROOT": str(root), "CONVO_PROFILE": profile}
    try:
        result = subprocess.run(command, shell=True, env=env, capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as error:
        return f"SAVE_HOOK_FAILED={error}\n"
    if result.returncode != 0:
        return f"SAVE_HOOK_FAILED=exit {result.returncode}: {result.stderr.strip()}\n"
    return result.stdout


def parse_request(config, profile, text):
    """Split a request into (profile, verb, topic words, episodic flag).

    A profile name or alias before the verb or right after it selects that profile, except after
    `send`, where the word names a destination the agent handles.
    """
    words = text.split()
    if words and profile_named(config, words[0].lower()):
        profile, words = profile_named(config, words[0].lower()), words[1:]
    verb = words[0].lower() if words else ""
    rest = words[1:]
    if verb != "send" and rest and profile_named(config, rest[0].lower()):
        profile, rest = profile_named(config, rest[0].lower()), rest[1:]
    topic = [word for word in rest if word not in EPISODIC_WORDS]
    return profile, verb, topic, len(topic) != len(rest)


def refresh_index(root, rows):
    """Rebuild index.tsv when a snapshot is newer than it; other tools may read the index."""
    index = root / "index.tsv"
    newest = max((Path(row["path"]).stat().st_mtime_ns for row in rows), default=0)
    if (index.is_file() and index.stat().st_mtime_ns >= newest) or duplicate_slugs(rows):
        return
    try:
        write_index(root, rows)
    except OSError:
        print(f"INDEX_STALE=could not rebuild {index}")


def apply_setup(config, profile, args):
    """Write the setup options for one profile and print its settings."""
    settings = dict(profile_settings(config, profile) or {})
    if args.root is not None:
        if not args.root.strip():
            raise ConvoError("choose a non-empty conversation folder")
        root = Path(args.root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        settings["root"] = str(root)
    if "root" not in settings:
        raise ConvoError(f"profile {profile} needs --root before other options")
    for alias in args.alias:
        if not re.fullmatch(NEW_SLUG, alias):
            raise ConvoError("an alias must use lowercase letters, digits, and hyphens")
        owner = profile_named(config, alias)
        if owner not in (None, profile):
            raise ConvoError(f"{alias} already names profile {owner}")
        if alias != profile and alias not in settings.setdefault("aliases", []):
            settings["aliases"].append(alias)
    for folder in args.dir:
        if folder not in settings.setdefault("dirs", []):
            settings["dirs"].append(folder)
    for key, value in (("base", args.base), ("instructions", args.instructions), ("save_hook", args.save_hook)):
        if value is not None:
            settings[key] = value
    config["profiles"][profile] = settings["root"] if list(settings) == ["root"] else settings
    if args.default:
        config["default"] = profile
    for variable in args.env:
        if variable not in config.setdefault("profile_env", []):
            config["profile_env"].append(variable)
    atomic_write(config_path(), json.dumps(config, indent=2) + "\n")
    print(f"Configured {profile}: {settings['root']}")
    print(json.dumps(settings, indent=2))


SETUP_WORDS = ("setup", "profile", "profiles", "config")


def preload(config, profile, text, explicit_session):
    text = text.replace("\n", " ").strip()
    if text == "$ARGUMENTS":
        text = ""
    profile, verb, topic, episodic = parse_request(config, profile, text)
    out = [f"REQUEST={text or '<none>'}", f"PROFILE={profile}"]

    def reference(name):
        file = SKILL_DIR / "references" / f"{name}.md"
        out.append(f"\n===== references/{name}.md =====")
        out.append(file.read_text(encoding="utf-8").rstrip("\n"))

    if verb in SETUP_WORDS:
        out.append(f"CONFIG_FILE={config_path()}")
        out.append("CONFIG=" + json.dumps(config, ensure_ascii=False))
        reference("profiles")
        print("\n".join(out))
        return
    try:
        root = root_for(config, profile)
    except ConvoError as error:
        if error.code != 3:
            raise
        out.append(f"SETUP_REQUIRED={str(error).split(': ', 1)[-1]}")
        reference("profiles")
        print("\n".join(out))
        return
    rows = snapshots(root)
    refresh_index(root, rows)
    today = dt.date.today().isoformat()
    if episodic:
        out.append("EPISODIC_REQUESTED=1")

    def listing(label, selected):
        out.append(f"{label} (DATE|REF|PROJECT|TITLE, newest first):")
        out.append(f"{today}|{LIVE_ROW}")
        out.extend(f"{row['date']}|{row['slug']}|{row['project']}|{row['title']}" for row in selected)

    def recent_rows():
        listing("RECENT", rows[:15])

    def filtered(label, days=None, limit=None):
        words = " ".join(topic).casefold()
        cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat() if days else ""
        selected = [row for row in rows if words in row["title"].casefold() and row["date"] >= cutoff]
        listing(label, selected[:limit])
        if words and not selected:
            out.append(f"NO_TITLE_MATCH={' '.join(topic)}")
            recent_rows()

    def show(ref):
        try:
            file = resolve_ref(config, profile, root, rows, ref)
            out.append(f"CONVO={file}")
            out.append(file.read_text(encoding="utf-8").rstrip("\n"))
        except (ConvoError, ValueError) as error:
            code = getattr(error, "code", 2)
            if ref and code == 1 and re.fullmatch(r"[0-9a-fA-F]{8,}", ref):
                out.append(f"EPISODIC_REF={ref}")
                return
            out.append(f"SHOW_FAILED=exit {code} for ref: {ref or '<last>'}")
            out.append(f"convo: {error}")
            recent_rows()

    def save_metadata():
        now = dt.datetime.now().astimezone()
        out.append(f"CREATED_AT={now.isoformat(timespec='seconds')}")
        out.append(f"SESSION_REF={session_ref(explicit_session)}")
        out.append(f"CONVO_ROOT={root}")
        out.append(f"TODAY={today}")
        out.extend(f"TODAY_CONVO={row['slug']}|{row['path']}|{row['title']}|{row['project']}"
                   for row in rows if row["date"] == today)
        hook = save_hook_output(config, profile, root)
        if hook:
            out.append(hook.rstrip("\n"))

    if verb == "recent":
        if topic:
            filtered("RECENT", limit=15)
        else:
            recent_rows()
        reference("read")
    elif verb == "list":
        filtered("LIST", days=30)
        reference("read")
    elif verb == "last":
        show("")
        reference("read")
    elif verb in ("open", "read", "show"):
        if topic:
            show(topic[0])
        else:
            out.append("SHOW_FAILED=no ref given")
            recent_rows()
        reference("read")
    elif verb == "save":
        save_metadata()
        recent_rows()
        reference("save")
    elif verb in ("", "send"):
        save_metadata()
        if verb == "":
            recent_rows()
    else:
        recent_rows()
    instructions = instructions_file(config, profile, root)
    if instructions:
        out.append(f"\n===== {instructions} =====")
        out.append(instructions.read_text(encoding="utf-8").rstrip("\n"))
    print("\n".join(out))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", "--dom", dest="profile",
                        help="conversation folder profile; only needed with several folders configured")
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup", help="show the selected profile's settings, or set its folder and options")
    setup.add_argument("--root", help="chosen conversation folder, not its parent context directory")
    setup.add_argument("--alias", action="append", default=[], help="another name for the profile; repeatable")
    setup.add_argument("--dir", action="append", default=[], help="working directory that defaults to the profile; repeatable")
    setup.add_argument("--base", help="folder that <alias>:path refs are relative to")
    setup.add_argument("--instructions", help="Markdown file appended to every preload")
    setup.add_argument("--save-hook", help="command whose output joins the save metadata")
    setup.add_argument("--default", action="store_true", help="make this the default profile")
    setup.add_argument("--env", action="append", default=[], help="environment variable whose value selects a profile; repeatable")
    commands.add_parser("root", help="print the selected profile's conversation folder")
    for name in ("list", "recent"):
        listing = commands.add_parser(name, help="JSON rows; list covers --days, recent the newest --limit")
        listing.add_argument("topic", nargs="*", help="literal title substring")
        listing.add_argument("--days", type=int, default=30)
        listing.add_argument("--limit", type=int)
    for name in ("show", "open", "read", "last"):
        showing = commands.add_parser(name, help="print CONVO=<path> and the snapshot")
        showing.add_argument("ref", nargs="?")
    prepare = commands.add_parser("prepare-save", help="JSON save metadata for a slug")
    prepare.add_argument("slug")
    register = commands.add_parser("register", help="validate a written snapshot and rebuild index.tsv")
    register.add_argument("file")
    commands.add_parser("build-index")
    pre = commands.add_parser("preload", help="everything one request needs, for a skill's first turn")
    pre.add_argument("--stdin", action="store_true", help="read the request text from standard input")
    pre.add_argument("session", nargs="?", default="", help="harness-qualified session ref, e.g. claude:<uuid>")
    args = parser.parse_args()
    if args.profile and not re.fullmatch(NEW_SLUG, args.profile):
        raise ConvoError("profile must use lowercase letters, digits, and hyphens")
    config = load_config()
    profile = select_profile(config, args.profile)
    if args.command == "setup" and any([args.root is not None, args.alias, args.dir, args.base is not None,
                                        args.instructions is not None, args.save_hook is not None,
                                        args.default, args.env]):
        apply_setup(config, profile, args)
        return
    if args.command == "preload":
        preload(config, profile, sys.stdin.read() if args.stdin else "", args.session)
        return
    root = root_for(config, profile)
    if args.command == "root":
        print(root)
        return
    if args.command == "setup":
        print(json.dumps({"profile": profile, **settings_for(config, profile), "root": str(root),
                          "config_file": str(config_path()), "profiles": sorted(config["profiles"])}, indent=2))
        return
    rows = snapshots(root)
    if args.command in ("list", "recent"):
        if args.days < 0 or (args.limit is not None and args.limit < 0):
            raise ConvoError("days and limit must be non-negative")
        topic = " ".join(args.topic).casefold()
        cutoff = (dt.date.today() - dt.timedelta(days=args.days)).isoformat()
        selected = [row for row in rows if topic in row["title"].casefold()
                    and (args.command == "recent" or row["date"] >= cutoff)]
        limit = args.limit if args.limit is not None else (15 if args.command == "recent" else None)
        print(json.dumps(selected[:limit], indent=2, ensure_ascii=False))
    elif args.command in ("show", "open", "read", "last"):
        file = resolve_ref(config, profile, root, rows, args.ref)
        print(f"CONVO={file}\n{file.read_text(encoding='utf-8')}", end="")
    elif args.command == "prepare-save":
        if not re.fullmatch(NEW_SLUG, args.slug):
            raise ConvoError("slug must use lowercase letters, digits, and hyphens")
        now = dt.datetime.now().astimezone()
        today = now.date().isoformat()
        print(json.dumps({"created_at": now.isoformat(timespec="seconds"), "today": today,
                          "session_ref": session_ref(), "convo_root": str(root), "profile": profile,
                          "new_path": str(root / today[:7] / f"{today}-{args.slug}.md"),
                          "slug_matches": [row for row in rows if row["slug"] == args.slug],
                          "today_convos": [row for row in rows if row["date"] == today]}, indent=2))
    elif args.command in ("register", "build-index"):
        if args.command == "register":
            file = Path(args.file).expanduser()
            if not file.is_absolute():
                raise ConvoError("register requires an absolute snapshot path")
            snapshot_path(root, file)
        index = write_index(root, rows)
        print(f"Built {index}: {len(rows)} entries")


if __name__ == "__main__":
    try:
        main()
    except ConvoError as error:
        print(f"convo: {error}", file=sys.stderr)
        sys.exit(error.code)
    except (OSError, ValueError) as error:
        print(f"convo: {error}", file=sys.stderr)
        sys.exit(2)
