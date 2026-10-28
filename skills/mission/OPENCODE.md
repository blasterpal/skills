# OpenCode mission setup

Restart OpenCode after changing agents or the mission plugin. Start OpenCode from the project directory, in whichever OpenCode environment you want mission in — a user who keeps separate personal and work environments installs each one separately:

```sh
opencode
# In the session:
/mission --afk <objective or plan path>
```

The runtime supplies the `mission` primary agent, its five bounded worker roles, the continuation plugin, and `opencode-task-model@1.3.1`. The task plugin lets the orchestrator specify a model and reasoning level for each assignment. Profiles are optional defaults; they are not required for parallelism or per-call model selection. Read [MODEL_ROUTING.md](MODEL_ROUTING.md) for routing, result checks, and provider boundaries.

## Model and permission boundaries

Keep separate environments’ provider allowlists, credentials, and session stores separate. Mission selects only models available and permitted in the active environment. If an environment has no permitted open-weight endpoint, record that missing capability rather than borrowing another environment’s credentials. No premium or cross-provider escalation is implied by a judge disagreement.

Subagent depth is one. The mission primary agent performs Matt's coordinator methods and dispatches leaf workers. Research, judge, and review roles deny unspecified tools, shell, edits, and delegation. Implementers and the merger perform local work within their briefs. These permissions are not an OS sandbox. Published task-model 1.3.1 background agents are read-only; use concurrent foreground calls for implementation and verified mission batches.

## Default model profile

[MODEL_DEFAULTS.md](MODEL_DEFAULTS.md) lists the default open-weight route per role, and `opencode/mission-default.json` is the matching example profile. `/mission setup` writes the user's choices as `mission-<name>.json` in the config directory's `profiles/` folder; the optional `oc-mission` launcher starts OpenCode with one — `oc-mission` uses the `default` profile, `oc-mission --profile <name>` another. The launcher uses an existing `oc` wrapper when available, otherwise `opencode`.

Verify the route IDs in the active environment before use (`opencode models`). Agent Markdown intentionally omits model settings because OpenCode 1.19.4 gives them precedence over profile JSON assignments; explicit task-plugin model arguments can override either. An open-weight-only policy can be supplied in the objective and applied per assignment.

## Install with /mission setup

Run `/mission setup` and follow [SETUP.md](SETUP.md): it copies the `mission` primary agent and its five workers, registers the continuation plugin and `opencode-task-model@1.3.1`, walks through the default routes in [MODEL_DEFAULTS.md](MODEL_DEFAULTS.md), and writes a profile with the chosen models. Restart OpenCode afterwards; agents and plugins load at startup.

The `/mission` command itself is registered by the continuation plugin, so a completely fresh installation needs one bootstrap step: with no command yet, tell the agent to set up mission (the skill follows SETUP.md on an explicit request), or register the plugin by hand:

1. Copy or link `opencode/agents/*.md` into your OpenCode config directory's `agents/` folder. Keep the `mission` primary agent and its five worker definitions together.
2. Register the bundled continuation plugin and pinned task-model package in your `opencode.jsonc` plugin list, preserving existing entries:

   ```json
   {
     "plugin": [
       "file:///absolute/path/to/skills/mission/opencode/mission-loop.js",
       "opencode-task-model@1.3.1"
     ]
   }
   ```

   OpenCode installs the npm plugin at startup. The bundled plugin resolves SKILL.md, AFK.md, and HELP.md relative to its own file, so keep the skill directory intact. Use the same setup in each isolated environment where mission should be available.
3. Restart OpenCode and run `/mission help`. Help does not create a ledger or start idle continuation, even when a mission loop already exists in that session.

## Continuation

Only the owning root session may resume `.loop`; children never own it. An unbound loop must originate from `mission`. The plugin preserves its orchestrator model/variant, serializes scheduling, and persists round/stall counters across restarts. A replacement loop remains owned by its new session.

The default cap is 20 continuation rounds; `/mission --afk --max-rounds N ...` changes it. The ledger records task retries. Collect workers and verify each batch before yielding. Cap/no-progress stops retain partial results. Use a persistent TUI/server session for unattended continuation; one-shot `opencode run` is a bounded check, not a persistent mission host.

## Checks

```sh
# From the skills repository root:
node --test skills/mission/opencode/mission-loop.test.mjs
sh -n skills/mission/opencode/oc-mission
sh tests/test_oc_mission.sh
```

Inspect resolved agent and model settings inside the launching environment. Raw resolved configuration can contain sensitive settings; do not publish it. Plugin unit tests use synthetic sessions and mocked provider/notification calls. Live verification records should identify which environment and routes were actually tested; they do not establish success on an arbitrary product build.
