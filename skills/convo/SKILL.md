---
name: convo
description: Save compressed current-state conversation briefs for continuation, or list, reopen, and search saved briefs and optional episodic history.
---

# Convo

**Status:** experimental — compression behavior is being tested in use.

Save conversation context as Markdown that another session can use to continue the work. Invoke as `/convo` where slash skills are supported, `$convo` in Codex, or ask the agent to use this skill.

Use the bundled helper with Python 3.9 or newer, resolving its path from this skill's directory:

```sh
python3 <skill-directory>/scripts/convo.py --dom me root
```

Call this helper directly; a system `convo` command may belong to a different installation. It uses only the Python standard library. `me` is the default profile. A leading profile in the request selects another configured store; pass `--dom <profile>` before the helper's command on every call for that request. Stay within that store unless the user explicitly selects another.

## First use

Run `root`. If it reports `SETUP_REQUIRED`, ask where the user would like to save conversations. Suggest a context directory for persistent notes, such as `~/context`, with conversations in `~/context/convos`. Explain that the chosen path is the conversation folder itself. Wait for their answer; the suggestion is not consent to create it. If the request already supplies a destination, use it.

After they choose, run:

```sh
python3 <skill-directory>/scripts/convo.py --dom me setup --root '<chosen-conversation-folder>'
```

Settings persist in `${XDG_CONFIG_HOME:-~/.config}/convo/config.json`, outside the downloaded skill. Resume the original request after setup. `setup` on an existing profile shows its current path; change it only when requested. Additional profiles use the same setup command with another `--dom` value. Changing a path does not move existing snapshots.

## Requests

| Request | Action |
|---|---|
| No arguments | Show `recent`; save only when requested. |
| `list [topic]` | Run `list [topic]`: last 30 days, filtered by title. |
| `recent [topic]` | Run `recent [topic]`: newest 15 snapshots, filtered by title. |
| `last` | Run `show` to read the most recently saved or amended snapshot. |
| `open <ref>` / `read <ref>` | Run `show <ref>`; refs are slugs, exact filenames, or paths within the store. |
| `save [new] [topic]` | Read [references/save.md](references/save.md) and save or amend the current conversation. |
| `setup` | Show the current path, or complete first-use setup above. |

For reads, follow [references/read.md](references/read.md). `--episodic` adds historical transcripts through an available episodic-memory capability; it is optional and requires no particular plugin. Strip it from the local topic before calling the helper. Local storage works without archived history.

Snapshots are minimal continuation briefs: current state, decisions, constraints, and next actions. Optional memos hold supporting reasoning that still affects those decisions. Compress both on each save; the detailed thought and work history belongs in episodic transcripts when available. Plans remain separate, lossless files. This skill does not require a context-management system, todo tracker, repository, or harness-specific hooks.
