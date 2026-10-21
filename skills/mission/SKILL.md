---
name: mission
description: Explicit /mission command only. Pursue the supplied plan or objective across idle turns, with optional unattended AFK mode.
disable-model-invocation: true
---

# /mission

The **ledger** is the plan file and the record of task progress. A **tick** is `- [x] <task> — evidence: <check or source> → <observed result>`; a tick without evidence counts as unticked. A **brief** is a self-contained assignment using [BRIEF.md](BRIEF.md). **BLOCKED** is `BLOCKED: <task> — <what the user must provide>` and stops the whole mission early.

Run this skill only when the user explicitly invokes `/mission` (or the equivalent skill command in Claude Code or Codex). OpenCode ignores `disable-model-invocation`; its `/mission` command loads this file directly, so the description also says explicit invocation only. OpenCode's mission plugin reads `.loop` and resumes on idle. Claude Code and Codex do not use that plugin: follow the same ledger and verification rules, continue through the plan in the active turn, and stop only on completion or a genuine block. Keep the ledger in an allowed workspace path and follow local restrictions on Git and worktrees. Use a worker only when this runtime offers one and separate context materially helps.

## Mode

`/mission [plan path]` runs the plan below. `/mission --afk [objective or plan path]` runs unattended: read [AFK.md](AFK.md) and follow its Start, Round, and Exit instead. With no argument after `--afk`, take the objective from this session's current work. The AFK mode makes provisional decisions on ambiguity and records them for the user's review.

## Start

1. Use the ledger path in the arguments. Otherwise use the plan written in this session. If neither exists, write a short ledger from the stated objective and done criteria. Resolve the path to an absolute path. Continue when the ledger exists.
2. Make each task one `- [ ]` line with a checkable done condition, including a command that can be run locally. Preserve the plan's requirements and dependencies. Continue when every task has a done condition.
3. In OpenCode only, at the working root write `.loop` as JSON: `{"ledger":"<absolute path>","max_rounds":20}`. The ledger remains the state record; `.loop` only enables plugin continuation. In other harnesses, proceed directly to Round.

## Round

1. Read the ledger. Pick the first unticked task whose dependencies are met. Read the relevant repository rules. Continue when one task and its done condition are identified.
2. When a separate worker is useful and available, dispatch one with [BRIEF.md](BRIEF.md) and give it only the files it may edit. Otherwise do the task directly. Continue when the changed files and unresolved items are known.
3. Run the done-condition command yourself and inspect the changed files against the task and repository rules. Treat a worker's report as input. On failure, retry the work at most twice with the actual failure. Continue when the done condition passes and the work meets the task, or the retry limit is reached.
4. On success, replace the task line with a tick containing the exact command and observed result. Resolve ordinary ambiguity yourself and add `Ruling: <decision> — <why> — <cost if wrong>` to the ledger. For irreversible or destructive actions, secrets, pushes, merges, publishes, or a plan where every path is a guess, write a BLOCKED line naming the needed input or approval. Write BLOCKED after two failed re-briefs as well. Continue when the ledger records the verified tick or BLOCKED line.
5. Print one line: `mission: <ticked>/<total> ticked; next <task>` or `mission: BLOCKED <task>`. In OpenCode, end this assistant turn after one task so the plugin can continue on idle. In other harnesses, continue to the next task in this turn.

## Exit

When every task has a tick with evidence, or a BLOCKED line exists, remove `.loop` if this run created it, notify the user when notification is available, and report the ticked count, every BLOCKED line, and every Ruling. In OpenCode, an unfinished round yields to plugin continuation; in other harnesses, continue working.
