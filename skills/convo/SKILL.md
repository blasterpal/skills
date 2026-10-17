---
name: convo
description: Save compressed current-state conversation briefs for continuation, or list, reopen, and search saved briefs and optional episodic history.
argument-hint: "[profile] list [--episodic] [topic] | recent [--episodic] [topic] | last | open|read <ref> | save [new] [topic] | setup"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/convo.py:*)
---

# Convo

**Status:** experimental — compression behavior is being tested in use.

Save conversation context as Markdown that another session can use to continue the work. Invoke as `/convo` where slash skills are supported, `$convo` in Codex, or ask the agent to use this skill.

The bundled helper needs Python 3.9 or newer and only the standard library. Resolve its path from this skill's directory and call it directly; a system `convo` command may belong to a different installation:

```sh
python3 <skill-directory>/scripts/convo.py root
```

Conversations go in one folder. Its path persists in `${XDG_CONFIG_HOME:-~/.config}/convo/config.json`, outside the downloaded skill, so updating the skill keeps it. Nothing else needs configuring.

## First use

Run `root`. If it reports `SETUP_REQUIRED`, ask where the user would like to save conversations. Suggest a context directory for persistent notes, such as `~/context`, with conversations in `~/context/convos`. Explain that the chosen path is the conversation folder itself. Wait for their answer; the suggestion is not consent to create it. If the request already supplies a destination, use it. After they choose, run:

```sh
python3 <skill-directory>/scripts/convo.py setup --root '<chosen-conversation-folder>'
```

Resume the original request after setup. `setup` on a configured folder prints its settings; change a path only when requested, and note that changing it does not move existing snapshots.

## Requests

| Request | Action |
|---|---|
| No arguments | Show `recent`; save only when requested. |
| `list [topic]` | Last 30 days, filtered by title. |
| `recent [topic]` | Newest 15 snapshots, filtered by title. |
| `last` | The most recently saved or amended snapshot. |
| `open <ref>` / `read <ref>` | A snapshot by slug, exact filename, `YYYY-MM/<file>`, or absolute path within the store. |
| `save [new] [topic]` | Read [references/save.md](references/save.md) and save or amend the current conversation. |
| `setup` | Show the current settings, or complete first-use setup above. |

For reads, follow [references/read.md](references/read.md). `--episodic` adds historical transcripts through an available episodic-memory capability; it is optional and requires no particular plugin. Local storage works without archived history.

Snapshots are minimal continuation briefs: current state, decisions, constraints, and next actions. Optional memos hold supporting reasoning that still affects those decisions. Compress both on each save; the detailed thought and work history belongs in episodic transcripts when available. Plans remain separate, lossless files. This skill does not require a context-management system, todo tracker, repository, or harness-specific hooks.

## Preloaded context

`preload` prints what one request needs in a single call: the request, the rows or the opened snapshot, save metadata (`CREATED_AT`, `SESSION_REF`, `CONVO_ROOT`, `TODAY`, `TODAY_CONVO` rows), and the verb's reference file. With that output a read needs no further command and a save needs no `prepare-save`. Run another command only when it reports `SHOW_FAILED`, `NO_TITLE_MATCH`, `EPISODIC_REQUESTED`, or `EPISODIC_REF`, or the task needs more than it shows.

## Several folders (optional)

Someone who keeps separate conversation folders, such as personal and work, configures each as a profile in the same config file; the README shows the keys. `PROFILE=` in the preload names the one in use. The helper picks it in this order: `--profile <name>` on the command line, then the `CONVO_PROFILE` variable and any variables named in the config's `profile_env` list, then a profile whose `dirs` contain the working directory, then the config's `default`, then `me`. A configured profile name or alias before the verb or right after it (`/convo work recent`, `/convo save work topic`) selects that profile for the request; pass it as `--profile <name>` on every follow-up helper call and stay in that store unless the user selects another. Any other word is part of the topic.

Refs may name a profile as `<profile-or-alias>:<path>`; a ref that belongs to another profile is refused rather than read. A profile's `instructions` file (or `<root>/CONVO.md`) is appended to every preload, and its `save_hook` output joins the save metadata; apply both, as they take precedence over the reference files where they differ. `setup --profile <name> --root <folder>` adds a folder.

In Claude Code, the block below runs before this skill reaches the model and is replaced by its output. If you see the block itself instead (Codex, OpenCode, or another harness), get the same output with one shell call, passing the user's request after the skill name verbatim (empty when there is none) between the heredoc lines:

```bash
python3 <skill-directory>/scripts/convo.py preload --stdin <<'CONVO_ARGS'
<request, e.g. recent, read home-wifi-upgrade, save new topic>
CONVO_ARGS
```

Do not read the reference files separately; the output includes the one the verb needs.

```!
python3 ${CLAUDE_SKILL_DIR}/scripts/convo.py preload --stdin claude:${CLAUDE_SESSION_ID} <<'CONVO_ARGS'
$ARGUMENTS
CONVO_ARGS
```
