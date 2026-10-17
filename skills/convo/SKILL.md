---
name: convo
description: Save compressed current-state conversation briefs for continuation, or list, reopen, and search saved briefs and optional episodic history.
argument-hint: "[profile] list [--episodic] [topic] | recent [--episodic] [topic] | last | open|read <ref> | save [new] [topic] | setup [--root <folder> ...]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/convo.py:*)
---

# Convo

**Status:** experimental — compression behavior is being tested in use.

Save conversation context as Markdown that another session can use to continue the work. Invoke as `/convo` where slash skills are supported, `$convo` in Codex, or ask the agent to use this skill.

The bundled helper needs Python 3.9 or newer and only the standard library. Resolve its path from this skill's directory and call it directly; a system `convo` command may belong to a different installation:

```sh
python3 <skill-directory>/scripts/convo.py root
```

Conversations go in one folder, or in separate personal and work folders so the two contexts never mix. The paths persist in `${XDG_CONFIG_HOME:-~/.config}/convo/config.json`, outside the downloaded skill, so updating the skill keeps them. Nothing else needs configuring.

## First use

A preload that prints `SETUP_REQUIRED=` (or a `root` command that exits 3) means no folder is configured yet. Follow [references/profiles.md](references/profiles.md), which the preload includes: ask whether to keep personal and work conversations apart and where to keep them, run `setup` for each folder, and resume the original request. If the request already supplies a destination, use it.

## Requests

| Request | Action |
|---|---|
| No arguments | Show `recent`; save only when requested. |
| `list [topic]` | Last 30 days, filtered by title. |
| `recent [topic]` | Newest 15 snapshots, filtered by title. |
| `last` | The most recently saved or amended snapshot. |
| `open <ref>` / `read <ref>` | A snapshot by slug, exact filename, `YYYY-MM/<file>`, or absolute path within the store. |
| `save [new] [topic]` | Read [references/save.md](references/save.md) and save or amend the current conversation. |
| `setup [...]` | Show the configuration, finish first use, or add and change folders and profiles per [references/profiles.md](references/profiles.md). |

For reads, follow [references/read.md](references/read.md). `--episodic` adds historical transcripts through an available episodic-memory capability; it is optional and requires no particular plugin. Local storage works without archived history.

Snapshots are minimal continuation briefs: current state, decisions, constraints, and next actions. Optional memos hold supporting reasoning that still affects those decisions. Compress both on each save; the detailed thought and work history belongs in episodic transcripts when available. Plans remain separate, lossless files. This skill does not require a context-management system, todo tracker, repository, or harness-specific hooks.

## Preloaded context

`preload` prints what one request needs in a single call: the request, the rows or the opened snapshot, save metadata (`CREATED_AT`, `SESSION_REF`, `CONVO_ROOT`, `TODAY`, `TODAY_CONVO` rows), and the verb's reference file. With that output a read needs no further command and a save needs no `prepare-save`. Run another command only when it reports `SHOW_FAILED`, `NO_TITLE_MATCH`, `EPISODIC_REQUESTED`, or `EPISODIC_REF`, or the task needs more than it shows.

## Several folders (optional)

Someone who keeps separate conversation folders, such as personal and work, configures each as a profile with `setup --profile <name> ...`; [references/profiles.md](references/profiles.md) has the options and the selection order. `PROFILE=` in the preload names the one in use. A configured profile name or alias before the verb or right after it (`/convo work recent`, `/convo save work topic`) selects that profile for the request; pass it as `--profile <name>` on every follow-up helper call and stay in that store unless the user selects another. Any other word is part of the topic.

Refs may name a profile as `<profile-or-alias>:<path>`; a ref that belongs to another profile is refused rather than read. A profile's instructions file is appended to every preload, and its save hook output joins the save metadata; apply both, as they take precedence over the reference files where they differ.

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
