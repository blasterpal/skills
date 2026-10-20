# skills

Agent skills by [blasterpal](https://github.com/blasterpal), in the [Agent Skills](https://agentskills.io) `SKILL.md` format.

Install into your harness with [`npx skills`](https://github.com/vercel-labs/skills):

```sh
npx skills add blasterpal/skills --list
npx skills add blasterpal/skills --skill convo --skill memorywipe --skill tldr -a claude-code
```

## Skills

| Skill | What it does |
|---|---|
| [autonomous](skills/autonomous/SKILL.md) | Complete a multi-step task without routine interruptions. Record judgment calls in one append-only decision file for later human review; required approvals still block the affected action. |
| [convo](skills/convo/SKILL.md) | Experimental: save compressed continuation briefs, optional reasoning memos, and lossless plans. On first use asks where to store conversations and whether to keep personal and work apart; needs nothing else. Profiles can add local conventions per folder. Python 3.9+, no additional packages. |
| [hashout](skills/hashout/SKILL.md) | Two to five agents in different harnesses (Claude Code, Codex, OpenCode) debate a question in turns through one shared Markdown file until they agree or deadlock, for architecture and design decisions or brainstorming. Can apply another skill (such as a grilling session) and act on the agreed decision. POSIX `sh` and core tools only. |
| [memorywipe](skills/memorywipe/SKILL.md) | Audit and clean the memory files, instruction chains, and injected context that Claude Code, Codex, or OpenCode load at the start of every session. Finds stale, duplicate, and oversized entries; presents one batched decision set; compresses what survives. |
| [tldr](skills/tldr/SKILL.md) | Shorten prose for a busy reader: lead with the answer, cut filler and repetition, keep every fact, caveat, and item number. Self-contained; no external style guide needed. |

## Conversation storage

Invoke `/convo save` or `$convo save` to save the current conversation. On first use,
the agent asks whether to keep personal and work conversations in separate folders and
where to put them, suggesting `~/context/convos`. Each folder contains monthly Markdown
snapshots, memos, and plans. That is the whole setup; the paths are written to
`${XDG_CONFIG_HOME:-~/.config}/convo/config.json`, so updating the skill preserves
your choice:

```json
{"profiles": {"me": "/Users/you/context/convos"}}
```

With personal and work apart, `me` is the default and a session started inside a work
directory you named saves to `work`; `/convo work recent` picks it for one request.

Use `convo recent`, `convo last`, or `convo open <slug>` through your agent to resume
saved context. Claude Code runs the helper's `preload` before the first model turn, so
a read takes no tool call; other harnesses run the same command first. Optional
episodic search uses whatever transcript-search capability your agent already has.

### Several folders

To keep conversations apart, for example personal and work, add a profile per folder.
Ask the agent (`/convo setup`), or run the helper yourself; it writes the config:

```sh
python3 skills/convo/scripts/convo.py --profile work setup --root ~/work-notes/convos --alias w --dir ~/work-notes
```

A plain string is the folder; an object adds options. Pick one with `--profile <name>`,
an environment variable, the working directory, or the profile's name in the request
(`/convo work recent`). [references/profiles.md](skills/convo/references/profiles.md)
describes each option:

```json
{
  "default": "me",
  "profile_env": ["HQ_DOM"],
  "profiles": {
    "me": "~/context/convos",
    "work": {
      "root": "~/work-notes/convos",
      "aliases": ["w"],
      "dirs": ["~/work-notes", "~/code/work-repo"],
      "instructions": "~/work-notes/convos/CONVO.md",
      "save_hook": "~/bin/convo-work-hook"
    }
  }
}
```

`instructions` (or a `CONVO.md` in the folder) holds conventions for that folder alone,
such as where memos go or how to link a task tracker; `save_hook` runs a command whose
output joins the save metadata.

Compression is an experiment under active testing. Snapshots retain the minimum
current state needed to continue correctly. Memos are optional and retain only
supporting reasoning that still affects decisions. Detailed history stays in
episodic transcripts when available. Test whether a fresh session can continue
without missing a consequential constraint or repeating rejected work; adjust
compression based on those results.

## Developing from a checkout

Link the skills from your clone so edits are available in the next agent session:

```sh
scripts/link-skills.sh --dry-run
scripts/link-skills.sh
```

The script links every `skills/<name>/` into `~/.claude/skills/`, `~/.agents/skills/`
(shared skills discovery for Codex), and `${XDG_CONFIG_HOME:-~/.config}/opencode/skills/`.
It replaces existing symlinks and refuses to overwrite real files or directories.
Review the dry run first: a link from another source will switch to this checkout.
Use either development links or `npx skills add` for these skills on a machine.

Validate local changes with:

```sh
python3 -m unittest discover -s tests -v
bash -n scripts/link-skills.sh
sh tests/test_hashout.sh
```
