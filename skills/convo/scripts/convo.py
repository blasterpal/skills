#!/usr/bin/env python3
"""Local conversation storage; Python standard library only."""

import argparse
import csv
import datetime as dt
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile


class ConvoError(Exception):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def config_path():
    return Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "convo/config.json"


def load_config():
    file = config_path()
    if not file.exists():
        return {"profiles": {}}
    config = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get("profiles"), dict):
        raise ConvoError(f"invalid configuration: {file}")
    return config


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


def root_for(config, profile):
    value = config["profiles"].get(profile)
    if value is None:
        raise ConvoError(f"SETUP_REQUIRED: choose a conversation folder for profile {profile}", 3)
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ConvoError(f"invalid conversation folder for profile {profile}")
    root = Path(value).resolve()
    if not root.is_dir():
        raise ConvoError(f"conversation folder is missing: {root}; restore it or run setup --root <folder>")
    return root


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
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md", resolved.name)
    if not match or len(relative.parts) != 2 or relative.parts[0] != match[1][:7]:
        raise ConvoError(f"expected YYYY-MM/YYYY-MM-DD-<slug>.md: {file}")
    dt.date.fromisoformat(match[1])
    if not resolved.is_file():
        raise ConvoError(f"snapshot does not exist: {file}", 1)
    return resolved, match


def snapshots(root):
    rows = []
    seen = {}
    for file in sorted(root.glob("????-??/*.md")):
        file, match = snapshot_path(root, file)
        fields = metadata(file)
        slug = fields.get("slug", match[2])
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ConvoError(f"invalid slug in {file}: {slug}")
        if slug in seen:
            raise ConvoError(f"duplicate slug {slug}:\n  {seen[slug]}\n  {file}")
        seen[slug] = file
        rows.append({"date": match[1], "slug": slug, "title": fields.get("title", slug),
                     "project": fields.get("project", "general"), "path": str(file)})
    return sorted(rows, key=lambda row: (row["date"], row["slug"]), reverse=True)


def resolve_ref(root, rows, ref):
    if not ref:
        if not rows:
            raise ConvoError("no saved conversations", 1)
        return Path(max(rows, key=lambda row: (Path(row["path"]).stat().st_mtime_ns, row["path"]))["path"])
    if "/" in ref or Path(ref).is_absolute():
        file = Path(ref).expanduser()
        return snapshot_path(root, file if file.is_absolute() else root / file)[0]
    matches = [row["path"] for row in rows if ref in (row["slug"], Path(row["path"]).name)]
    if not matches:
        raise ConvoError(f"no conversation matches {ref}", 1)
    if len(matches) > 1:
        raise ConvoError(f"multiple matches for {ref}:\n  " + "\n  ".join(matches))
    return Path(matches[0])


def session_ref():
    if os.environ.get("CODEX_THREAD_ID"):
        return "codex:" + os.environ["CODEX_THREAD_ID"]
    if os.environ.get("OPENCODE"):
        return ""
    for key in ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID"):
        if os.environ.get(key):
            return "claude:" + os.environ[key]
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dom", default="me", help="storage profile (default: me)")
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup")
    setup.add_argument("--root", help="chosen conversation folder, not its parent context directory")
    commands.add_parser("root")
    for name in ("list", "recent"):
        listing = commands.add_parser(name)
        listing.add_argument("topic", nargs="*", help="literal title substring")
        listing.add_argument("--days", type=int, default=30)
        listing.add_argument("--limit", type=int)
    for name in ("show", "open", "read", "last"):
        showing = commands.add_parser(name)
        showing.add_argument("ref", nargs="?")
    prepare = commands.add_parser("prepare-save")
    prepare.add_argument("slug")
    register = commands.add_parser("register")
    register.add_argument("file")
    commands.add_parser("build-index")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.dom):
        raise ConvoError("profile must use lowercase letters, digits, and hyphens")
    config = load_config()
    if args.command == "setup" and args.root is not None:
        if not args.root.strip():
            raise ConvoError("choose a non-empty conversation folder")
        root = Path(args.root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        config["profiles"][args.dom] = str(root)
        atomic_write(config_path(), json.dumps(config, indent=2) + "\n")
        print(f"Configured {args.dom}: {root}")
        return
    root = root_for(config, args.dom)
    if args.command in ("root", "setup"):
        print(root)
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
        file = resolve_ref(root, rows, args.ref)
        print(f"CONVO={file}\n{file.read_text(encoding='utf-8')}", end="")
    elif args.command == "prepare-save":
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
            raise ConvoError("slug must use lowercase letters, digits, and hyphens")
        now = dt.datetime.now().astimezone()
        today = now.date().isoformat()
        print(json.dumps({"created_at": now.isoformat(timespec="seconds"), "today": today,
                          "session_ref": session_ref(), "convo_root": str(root),
                          "new_path": str(root / today[:7] / f"{today}-{args.slug}.md"),
                          "slug_matches": [row for row in rows if row["slug"] == args.slug],
                          "today_convos": [row for row in rows if row["date"] == today]}, indent=2))
    elif args.command in ("register", "build-index"):
        if args.command == "register":
            file = Path(args.file).expanduser()
            if not file.is_absolute():
                raise ConvoError("register requires an absolute snapshot path")
            snapshot_path(root, file)
        output = io.StringIO()
        writer = csv.writer(output, delimiter="|", lineterminator="\n")
        for row in rows:
            writer.writerow([row["date"], row["slug"], Path(row["path"]).name, row["project"], row["title"]])
        atomic_write(root / "index.tsv", output.getvalue())
        print(f"Built {root / 'index.tsv'}: {len(rows)} entries")


if __name__ == "__main__":
    try:
        main()
    except ConvoError as error:
        print(f"convo: {error}", file=sys.stderr)
        sys.exit(error.code)
    except (OSError, ValueError) as error:
        print(f"convo: {error}", file=sys.stderr)
        sys.exit(2)
