# Default model routes

Default open-weight model per mission role when neither the user nor the objective names one. [MODEL_ROUTING.md](MODEL_ROUTING.md) defines how a model is chosen for an assignment; this file holds the defaults, and [SETUP.md](SETUP.md) writes them into an OpenCode profile. Verify each route exists in the active environment (`opencode models`) before relying on it, and substitute the environment's own route IDs when they differ.

| Role | OpenCode agent | Default model | Route |
|---|---|---|---|
| Orchestrator (plans) | `mission` | GLM 5.3 | `openrouter/z-ai/glm-5.3` |
| Build (implementation) | `mission-implement` | DeepSeek V4.1 Flash | `openrouter/deepseek/deepseek-v4.1-flash` |
| Research | `mission-research` | DeepSeek V4.1 Flash | `openrouter/deepseek/deepseek-v4.1-flash` |
| Merge | `mission-merger` | DeepSeek V4 Pro | `openrouter/deepseek/deepseek-v4-pro` |
| Review | `mission-review` | Qwen 3.6-35B | `openrouter/qwen/qwen3.6-35b-a3b` |
| Judge (consequential calls) | `mission-judge` | Qwen 3.5-397B | `openrouter/qwen/qwen3.5-397b-a17b` |

Small, distinct tasks with no dedicated role run on a local route when one is available, such as Recursive Flint served by a local provider (`flint/flint` in the reference setup). No mission agent owns that row: the orchestrator passes the route per task and records it in the ledger.

The hosted defaults assume an OpenRouter provider configuration; an environment using a proxy or local endpoints substitutes its own route IDs for the same models. Route IDs were checked against the live OpenRouter catalog on 2026-10-26. The judge default is intentionally a different model family from the orchestrator and the builders, so independent judging starts from a genuinely different model; preserve that separation when overriding routes ([JUDGE.md](JUDGE.md)).
