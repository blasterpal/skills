# Per-assignment models in OpenCode V1

`opencode-task-model@1.3.1` replaces the native `task` tool with one accepting `model`, `reasoning`, and `background`. Use named mission roles for their instructions/permissions and select models separately. Multiple foreground task calls can execute concurrently; background mode in this release is read-only.

## Resolve the model

1. Stay inside the launching environment. `oc-me` and `oc-work` select distinct credentials, provider allowlists and session stores. Inspect available IDs with `opencode models` in that inherited environment; avoid printing raw resolved configuration or credentials.
2. Honor a model explicitly requested for the assignment first. Otherwise use an applicable profile/agent assignment when its provider is enabled. Without either, reuse the current model for ordinary work or select a cheaper permitted route according to the owner's stated preferences. Record the choice once and reuse it for equivalent tasks; do not spend a planning round choosing a model for every small edit.
3. For independent judging, choose an explicit different model, preferably a different family, from enabled providers. Pass the same model when resuming the judge task. A role without a configured model simply inherits; that is not evidence of independence. If no permitted independent model can be established, record the limitation and continue independent work rather than claiming convergence.
4. For an open-weight-only request, require published weights and an available approved endpoint. Check the active environment’s actual provider allowlist; a separate work environment may not permit the same providers as a personal one. Do not borrow personal routes or credentials for work. If the requirement cannot be met in that environment, record the exact missing route. Do not broaden provider allowlists to make a model work.

An example synthetic connection check used `openrouter/deepseek/deepseek-v4.1-flash` and `openrouter/moonshotai/kimi-k3` as distinct working task routes. This is connection evidence, not a task-quality benchmark or a permanent eligibility guarantee. Recheck on failure. A model can be blocked by account provider policy even when present in the catalog; listing a model in the catalog alone does not prove an eligible endpoint.

## Dispatch and inspect

Use `task` with `subagent_type`, `description`, a self-contained `prompt`, empty `task_id` for a new child, exact `provider/model` in `model`, and `reasoning: default` unless a supported variant is requested. Use `background: false` for implementation and for a verified mission batch; dispatch independent calls concurrently, then collect their results before the round yields. A read-only background assignment is appropriate only when its automatic completion cannot race another mission round.

The explicit per-call model overrides an agent's configured model. `model: inherit` preserves ordinary agent/parent precedence but is insufficient to establish a separate judge. Agent permissions still apply; changing its model does not change its authority.

Record task ID, role, requested model and actual child-session model metadata when exposed. Empty output, child API errors, and a mismatched model are failures even when the task envelope says completed. Inspect the child with OpenCode's session tools or `opencode export <task_id>`; extract only needed error/model fields. Validate route IDs before dispatch: the pinned plugin has an open invalid-model-validation issue, so do not rely on it to reject a malformed route safely. Retry only within mission's limits and preserve the actual failure. A different endpoint or model must remain within existing authorization.
