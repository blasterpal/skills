# Pipeline stages

Reached from [SKILL.md](SKILL.md) when the objective is a GitHub issue or epic. The stages run in order — intake, implementation, review, landing — each producing ledger tasks that SKILL.md's Round works, with a gate between stages. Authorization for each stage's external writes is defined in SKILL.md's Mode.

## Intake

Call the Skill tool with `grilling` (in AFK, under AFK.md's absorption rules). Call `to-spec`; the spec issue must reference the epic, and the epic gets a comment linking the spec. Call `to-tickets`: each ticket's done condition — a locally runnable command or an explicit acceptance check — is written and approved together with the breakdown at its step-4 quiz; mission never invents a done condition after approval. The ledger's tasks are the tickets, each carrying its issue URL and its done condition verbatim.

In default mode the step-4 approval is the intake gate, and approved tickets publish with `ready-for-agent`. In AFK the breakdown is provisional: tickets publish **without** `ready-for-agent`, so nothing external can grab them; mission proceeds on its own ledger, and the label is applied at user review.

## Implementation

One execution-route call for the whole ticket graph; the frontier and merge order are the route's business. The physical layout is mission's contract on any route:

- **One worktree per issue** at `<repo>/.worktrees/<issue-slug>`, branched from the integration branch.
- Merges land in the **main worktree** (the repository's primary checkout), which holds the integration branch; seam verification runs there.
- `.worktrees/` is git-ignored before any worktree is created.
- An issue's worktree is removed once its merge has verified.

On return, verification is SKILL.md Round step 3: every covered ticket's done condition, run in the main worktree against the integration-branch head.

## Review

One bounded pass, only when the route's binding provides a critic on a different model family from the implementers and the context permits sending it the work. The critic audits the trace — spec user stories → tickets → ledger evidence — and reports. Findings are review notes or `Needs user:` lines, never new ledger work. When no second family is available or permitted, the route's own review stands, and the final report says the critic pass was skipped, and why.

## Landing

Push the integration branch; ensure the single draft PR exists (the route may have opened it) and mark it ready. The PR body lists `Closes #N` for every ticked ticket, so tickets close at merge — the only place they close. Without the authorization named in SKILL.md's Mode, stop at this gate and report the branch.

