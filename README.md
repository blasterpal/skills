# skills

Agent skills by [blasterpal](https://github.com/blasterpal), in the [Agent Skills](https://agentskills.io) `SKILL.md` format.

Install into your harness with [`npx skills`](https://github.com/vercel-labs/skills):

```sh
npx skills add blasterpal/skills --list
npx skills add blasterpal/skills --skill memorywipe --skill tldr -a claude-code
```

## Skills

| Skill | What it does |
|---|---|
| [memorywipe](skills/memorywipe/SKILL.md) | Audit and clean the memory files, instruction chains, and injected context that Claude Code, Codex, or OpenCode load at the start of every session. Finds stale, duplicate, and oversized entries; presents one batched decision set; compresses what survives. |
| [tldr](skills/tldr/SKILL.md) | Shorten prose for a busy reader: lead with the answer, cut filler and repetition, keep every fact, caveat, and item number. Self-contained; no external style guide needed. |
