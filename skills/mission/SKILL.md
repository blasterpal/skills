---
name: mission
description: Explicit /mission command only. Orchestrate a plan or objective with workflow skills, parallel workers, and judged AFK decisions.
disable-model-invocation: true
---

# /mission

Mission is the orchestrator. It chooses ready work, delegates bounded tasks, verifies results, and records progress. Workers perform assigned work; they do not start mission loops.

The **ledger** records the objective and progress. A **tick** is `- [x] <task> — evidence: <check or source> → <observed result>`; without evidence it remains unticked. A **brief** follows [BRIEF.md](BRIEF.md). `Needs user: <decision or approval>` records a pending human action. `BLOCKED: <task> — <what the user must provide>` ends the mission only when no meaningful authorized work can advance. Omit `BLOCKED:` entirely when there is no blocker; do not write a placeholder such as `BLOCKED: none`.

Run only on an explicit `/mission` invocation. For engineering work, read [MATT.md](MATT.md) to use Matt's skills. This invocation delegates their methods within the mission's objective; it does not authorize additional publishing or implementation.

## Help

If the arguments are exactly `help`, `--help`, or `-h`, read [HELP.md](HELP.md) and explain usage. This is a read-only help request: do not create or modify a ledger, `.loop`, branches, worker assignments, or project files, and do not resume an existing mission. Return after showing help. With no objective or recoverable current work, explain the syntax and ask what result the user wants.

## Mode and runtime

`/mission [plan path or objective]` follows Start and Round below. `/mission --afk [objective or plan path]` follows [AFK.md](AFK.md) instead. With no AFK argument, recover the objective from this session. AFK makes provisional judgments and uses the independent judge described in [JUDGE.md](JUDGE.md).

In OpenCode, use the `mission` primary agent inside `oc-me` or `oc-work`. Read [MODEL_ROUTING.md](MODEL_ROUTING.md) to select a permitted model per assignment; profiles are optional defaults. Read [OPENCODE.md](OPENCODE.md) for launch and continuation details. The plugin reads `.loop` and resumes the same root session on idle. Claude Code and Codex have no such plugin: continue in the active turn until completion or a genuine block. Use an allowed workspace path and follow local restrictions on Git and worktrees, including any restrictions for synced folders. If worker tools are unavailable, do the work directly and report that limitation.

## Input and conclusion

Accept a prompt, idea, concept, feature brief, or existing plan. Preserve supplied source files; a brief is input, not a ledger to overwrite. Extract the desired outcome, required user features, constraints, non-goals, and acceptance examples. Record their sources and distinguish explicit requirements from inferred defaults. Reuse existing work only after checking it against these inputs.

For a request to take a software idea through implementation, the conclusion is a tested local implementation on an integration branch, with review findings addressed and a reviewable handoff. A request limited to planning, a spec, or tickets stops at that artifact. Publishing and merging the protected target branch remain separate permissions. For other kinds of work, define the concrete requested deliverable rather than forcing a code workflow.

## Start

1. Read the supplied ledger, or create one from the objective. Record an absolute ledger path, source pointers, the required user features, the requested result, **Done when**, confirmed constraints, non-goals, existing authorization, and the active environment, optional profile, and model choices. A planning request ends in planning; a build request may include implementation. Keep external actions and merging the target branch separate from local integration.
2. Make tasks `- [ ]` lines with dependencies and checkable outcomes. Use commands for executable behavior and cited inspection criteria for design or research. Add a final audit against **Done when** and every required user feature. Keep feature-to-spec/ticket/check pointers in the result so a feature cannot disappear during decomposition. For tracker-backed work, link the canonical issues rather than copying their requirements into the ledger.
3. In OpenCode only, write `.loop` at the working root as `{"ledger":"<absolute path>","max_rounds":20}`. Use a session ID only if the harness already provides it; otherwise omit it and let the plugin bind on idle. Do not inspect runtime source or session databases to discover an optional ID. Never overwrite another session's binding. The plugin binds the selected model and variant on first continuation. Preserve that binding on resume. Other harnesses proceed directly to Round.

## Delegation

1. Dispatch ready independent tasks concurrently, bounded by runtime capacity and the selected profile. Before dispatch, record the task, worker, owned files or worktree, dependencies, and starting commit in the ledger. Reconcile existing assignments on resume before launching replacements. Claim tracker tickets using the repository's convention; the ledger distinguishes workers sharing one login.
2. Give each worker a [brief](BRIEF.md) with exact skill and source pointers. Use the task plugin’s explicit model and reasoning arguments as described in [MODEL_ROUTING.md](MODEL_ROUTING.md); inspect the child result and model record rather than trusting the completed envelope alone. Research workers return evidence; the orchestrator writes shared notes. Each implementer owns a separate branch/worktree based on the integration branch, with isolated databases and ports where required. Shared ledger, glossary, ADR, spec, and map updates have one writer.
3. Run one implementation scheduler: the mission orchestrator follows `implement-spec` itself and dispatches its workers. A worker does not launch another scheduler or create `.loop`. One merger updates the integration branch at a time; parallel implementation does not authorize merging the protected target branch.
4. The merger prepares each integration on a separate candidate branch/worktree based on the last verified integration commit. The orchestrator verifies that candidate before advancing the integration branch to the identical checked commit. Failed candidates stay isolated for repair; other ready work keeps the last verified base. A worker's report alone cannot tick a task or release its dependents. Finish or safely stop active workers before yielding an OpenCode round. Read-only review tasks may run concurrently on the same pinned commit.

## Round

1. Read the ledger and current deliverables. Select ready work; resolve or skip pending human actions while independent authorized work remains. Advance from decisions to spec, tickets, implementation, and verification when their prerequisites hold and the requested endpoint includes them. Add newly exposed work before the final audit; completing the initial task list is not enough if the requested outcome is still missing. Load the applicable workflow skill before assigning the task.
2. Dispatch the ready tasks using Delegation, or do the task directly. Keep decisions shared by multiple tasks as prerequisites rather than letting workers choose inconsistent answers.
3. Inspect the changes and run the done conditions yourself, after serialized integration when applicable. Retry failed work at most twice with the actual failure, recording attempts in the ledger so a restart does not reset the allowance. Ordinary local integration is part of an authorized build; pushes, publication, protected-branch merges, secrets, and destructive actions need the user's existing authorization.
4. Tick verified tasks with the checked commit, exact command or source, and observed result. Record `Ruling: <decision> — <why> — <cost if wrong>` for ordinary ambiguity. Record pending authority as `Needs user:`. Exhausted retries or required input block their task; write `BLOCKED:` only when nothing else can advance. Inspect active work before reporting a block; do not discard verified results from other workers.
5. Print `mission: <ticked>/<total> ticked; next <task>` or `mission: BLOCKED <task>`. In OpenCode, finish the current verified batch and yield for idle continuation; one round may complete several independent tasks. In other harnesses continue with the next ready work.

## Exit

Complete only when every task, including the final audit, has evidenced ticks and **Done when** holds. Distinguish draft, locally implemented, integrated/verified, published, and merged results. For a build, every required user feature needs implementation and observed acceptance evidence, or the mission remains incomplete with the specific blocker. A deferred approval, passing unit tests alone, or a completed planning artifact is not an implemented feature.

On completion or a genuine block, remove only the `.loop` this run owns, notify the user when available, and report the outputs, ticked count, Rulings, judge outcomes, and remaining `Needs user:` or `BLOCKED:` lines. A plugin round-cap or no-progress stop preserves the ledger and partial result for resumption.
