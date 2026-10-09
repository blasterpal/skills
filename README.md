# skills

Agent skills by [blasterpal](https://github.com/blasterpal), in the [Agent Skills](https://agentskills.io) `SKILL.md` format.

Install into your harness with [`npx skills`](https://github.com/vercel-labs/skills):

```sh
npx skills add blasterpal/skills --list
npx skills add blasterpal/skills --skill memorywipe -a claude-code
```

## Skills

| Skill | What it does |
|---|---|
| [memorywipe](skills/memorywipe/SKILL.md) | Audit and clean the memory files, instruction chains, and injected context that Claude Code, Codex, or OpenCode load at the start of every session. Finds stale, duplicate, and oversized entries; presents one batched decision set; compresses what survives. |
