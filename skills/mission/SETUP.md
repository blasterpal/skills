# Mission setup

`/mission setup` installs mission's OpenCode runtime: the agents, the continuation and task-model plugins, and a model profile chosen with the user from [MODEL_DEFAULTS.md](MODEL_DEFAULTS.md). An explicit user request to set up mission follows this file even when the `/mission` command does not exist yet — the plugins registered below are what provide the command. Setup changes only the files named here; it never creates or resumes a mission, ledger, `.loop`, or worker assignment.

## 1. Locate

- Skill directory: the folder containing this file.
- OpenCode config directory: `${XDG_CONFIG_HOME:-~/.config}/opencode` unless the user's setup differs; ask when unclear.

## 2. Agents

Copy the six files from `opencode/agents/` — the `mission` primary agent and its five workers — into `<config>/agents/`, creating the folder when needed. Report any replaced file whose contents differed.

## 3. Plugins

Read the config file in the config directory (`opencode.jsonc`, or `opencode.json`). Its `plugin` array needs these two entries, with the absolute path of this skill's copy of the continuation plugin:

```json
"file://<skill-directory>/opencode/mission-loop.js",
"opencode-task-model@1.3.1"
```

Add the missing entries, preserving existing entries and formatting; create the file with a minimal `plugin` array when no config exists. Show the user the change before writing it. OpenCode installs the npm package at startup. The bundled plugin resolves SKILL.md, AFK.md, and HELP.md relative to its own file, so keep the skill directory intact. This step is what registers `/mission`; when setup ran without it, the command appears after the restart in step 6.

## 4. Models

Read [MODEL_DEFAULTS.md](MODEL_DEFAULTS.md) and check which of its routes the active environment offers (`opencode models`; never print credentials or raw resolved configuration). Then ask in one question set whether to keep the default routes or replace specific roles, offering only routes available and permitted in this environment; the boundaries in [MODEL_ROUTING.md](MODEL_ROUTING.md) apply. A user who keeps separate OpenCode environments, for example personal and work, runs setup once per environment; setup configures only the environment it runs in.

Prefer a question tool that waits for the answer so setup completes in this turn; that keeps it from interleaving with an active mission loop's idle continuation.

## 5. Profile

Write the chosen routes as `<config>/profiles/mission-<name>.json` in the shape of [opencode/mission-default.json](opencode/mission-default.json); `name` defaults to `default`, and an existing profile of that name is shown to the user before being replaced. Optionally link `opencode/oc-mission` onto the user's PATH; `oc-mission --profile <name>` then starts OpenCode with that profile.

## 6. Finish

Report every file written or changed. Tell the user to restart OpenCode — agents and plugins load at startup — and to verify with `/mission help`, which creates nothing.
