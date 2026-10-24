# Matt's workflows inside mission

Read each named skill's actual `SKILL.md` before using it. Resolve it through the installed skill catalog or shared skill directories; do not route from a summary alone. Mission's explicit invocation delegates the relevant workflow methods even when a runtime hides an explicit-only skill from its skill tool: read its file directly, preserving upstream invocation settings. If a required skill cannot be found, identify the missing dependency instead of inventing its instructions.

## Choose the entry point and requested end

| Current work | Workflow | Result used by the next step |
|---|---|---|
| Large unresolved effort spanning sessions | `wayfinder` | Map and linked decision evidence |
| Bounded idea with open choices | `grill-with-docs`, using `grilling` and `domain-modeling` | Confirmed answers or visibly provisional AFK answers |
| Missing facts or behavior that needs a concrete trial | `research` or `prototype` | Cited findings or a preserved prototype |
| Decisions sufficient to specify the requested work | `to-spec` | Spec covering behavior, testing, decisions, and exclusions |
| Spec ready to split | `to-tickets` | Verifiable vertical slices and dependency edges |
| One implementation ticket | `implement`, using `tdd` | Tested local commit |
| Multiple implementation tickets | `implement-spec`, using `tdd` workers | One verified integration branch |
| Implementation ready for review | `code-review` | Separate Standards and Spec findings against a pinned base |

Enter at the actual state of the work; reuse valid specs and tickets. Continue only to the result authorized by the objective. Preserve the distinction between wayfinder decision tickets and implementation tickets. Research is evidence, not approval.

## Confirmations and publication

Normal mode respects the skills' human confirmations. In AFK, [AFK.md](AFK.md) and [JUDGE.md](JUDGE.md) replace ordinary design waits with judged provisional choices. Record them beside the affected draft; never present them as the user's answers.

Wayfinder HITL tickets remain open without a genuine human exchange, even if an AFK answer is converged. Keep its one-non-research-resolution-per-session rule; parallelize research and preparation instead of manufacturing sessions to bypass it. A completed draft can meet a planning objective while its formal decisions remain unapproved.

`to-spec` test-boundary confirmation, `to-tickets` breakdown approval, and `tdd` testing choices remain distinguishable from provisional substitutes. A pending mandatory human decision can coexist with useful draft work. Approved planning is required unless the build objective explicitly delegates the relevant low-stakes provisional choices; a judge cannot supply that authorization.

Some skills publish issues, push research branches, open PRs, commit, merge, or close tickets. Apply the mission's existing authorization and repository workflow to each action. Without publication authority, prepare reviewable local drafts in the repository's session workspace and record the missing action. Never label an unapproved proposal `ready-for-agent` or claim that tickets exist before publishing them. Do not close implementation tickets before the repository's completion condition holds.

## Parallel implementation

The mission primary agent performs `implement-spec`'s coordinator work. It dispatches implementers directly, observes dependencies, and gives a single merger each completed branch in turn. It does not launch an `implement-spec` coordinator that also schedules the same tickets. Workers read their assigned method directly when the runtime's nesting limit prevents that skill's usual helper delegation.

Pin the review base before implementation. Test each candidate integration before advancing the integration branch; keep a failed candidate separate so unrelated work uses the last verified base. Release dependent tickets only after the integration branch points to the checked candidate commit. Run independent Standards and Spec reviews against the same final commit, then fix and verify relevant findings. Resolve disagreements against the requirements and evidence rather than averaging the reviews.
