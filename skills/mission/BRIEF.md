# Worker brief

Give one worker a self-contained task with pointers to the authoritative material.

- **Task and ID:** the exact ledger task or tracker ticket title/link.
- **Done condition:** observable outcome, exact checks, and expected results.
- **Role and model:** assigned OpenCode agent, requested route, and reasoning variant if configured.
- **Workflow:** exact SKILL.md paths to read and the part of the method to perform.
- **Read:** spec, issue, confirmed decisions, relevant Rulings, and repository rules.
- **Dependencies:** evidence that prerequisites are met; implementation base commit and integration branch.
- **May edit:** exact owned files, output path, or worktree. Read-only workers return findings for the orchestrator to save.
- **Authority:** permitted local actions and any explicitly authorized publication. List material `Needs user:` constraints; a worker inherits no broader authority than the mission.
- **Return to:** the orchestrator, with the task/session ID used for follow-up.

Workers execute only this assignment. They do not create `.loop`, update the mission ledger or shared tracker, launch another scheduler, or merge the protected target branch. Use the workflow's method directly if its usual nested helper is unavailable. Return proposed decisions rather than changing shared assumptions.

Return:

1. Files changed and exact branch/worktree/commit, or cited findings for read-only work.
2. Commands, observed outputs, and unmet acceptance criteria.
3. Proposed Rulings, unresolved evidence, and any action requiring authority.
4. Actual reported model/variant, when exposed; distinguish it from the configured route.

The orchestrator checks the integrated result and decides whether to tick the ledger. Only the serialized merger may update the integration branch when its brief explicitly assigns that work.
