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
| [convo](skills/convo/SKILL.md) | Experimental: save compressed continuation briefs, optional reasoning memos, and lossless plans. Asks where to store conversations on first use; defaults to the `me` profile. Python 3.9+, no additional packages. |
| [memorywipe](skills/memorywipe/SKILL.md) | Audit and clean the memory files, instruction chains, and injected context that Claude Code, Codex, or OpenCode load at the start of every session. Finds stale, duplicate, and oversized entries; presents one batched decision set; compresses what survives. |
| [tldr](skills/tldr/SKILL.md) | Shorten prose for a busy reader: lead with the answer, cut filler and repetition, keep every fact, caveat, and item number. Self-contained; no external style guide needed. |

## Conversation storage

Invoke `/convo save` or `$convo save` to save the current conversation. On first use,
the agent asks where to store it and suggests `~/context/convos`. The chosen folder
contains monthly Markdown snapshots, memos, and plans. Configuration lives in
`${XDG_CONFIG_HOME:-~/.config}/convo/config.json`, so updating the skill preserves
your choice. `me` is the default profile; additional profiles can use separate folders.

Use `convo recent`, `convo last`, or `convo open <slug>` through your agent to resume
saved context. Optional episodic search uses whatever transcript-search capability
your agent already has.

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
```
