# Mission help

Mission takes an idea, feature brief, or plan toward a defined result. One orchestrator delegates independent tasks to parallel workers, checks their results, and records evidence in a ledger.

## Start

```text
/mission help
/mission Build a local CSV viewer with filtering and no external services
/mission /absolute/path/to/ledger.md
/mission --afk Build the features in /absolute/path/to/brief.md
/mission --afk --max-rounds 12 /absolute/path/to/ledger.md
```

In Codex use `$mission` instead of `/mission`. Other harnesses may expose it through their own skill command. Help aliases are `help`, `--help`, and `-h`; they show usage without starting or resuming work.

Give mission the user features, constraints, acceptance examples, and desired conclusion. For example:

```text
/mission --afk Build a local CSV viewer. Required: upload a CSV, filter rows,
and export the filtered rows. Keep all data on this machine. No external
services or new dependencies. Finish with tested local code ready for review;
no push, publication, or merge into main.
```

A planning-only request ends at a draft, specification, or ticket breakdown. An implementation request continues through tested code and review. Existing source briefs are preserved rather than overwritten as ledgers.

## Attended or AFK

| Mode | What it does |
|---|---|
| `/mission ...` | Works autonomously inside the objective and asks for required human decisions |
| `/mission --afk ...` | Makes visibly provisional choices, obtains independent model critique for material decisions, and continues authorized work without routine questions |

AFK agreement is not human approval. Publication, protected-branch merges, destructive changes, and other consequential actions still need the user’s authorization. If one task needs a decision, independent authorized tasks continue. The whole mission stops as blocked only when nothing meaningful can advance.

## Models and parallel work

With the OpenCode task-model plugin installed, specify models in the objective or individual assignments:

```text
Use <provider/model-X> for implementation and <provider/model-Y> for judging.
Run independent tickets in parallel.
```

Use actual IDs from `opencode models`. Mission stays within the active environment’s configured providers and credentials. Profiles are optional bundles of defaults, not a requirement. An independent judge needs a different model, preferably a different family. Mission retains the current model for ordinary work unless the task, user preference, or applicable defaults call for another permitted route.

Workers own separate files or worktrees. Candidate integrations are verified before the integration branch advances. In published `opencode-task-model@1.3.1`, background tasks are read-only; concurrent foreground tasks support editing under their agent permissions.

## Progress, limits, and resumption

1. The ledger contains tasks, dependencies, model choices, and checks. A completed task includes the exact evidence and observed result. Original user features remain linked to their specification, tickets, and acceptance checks.
2. `Needs user:` records a pending decision or approval. `BLOCKED:` records an actual mission-wide blocker; an empty or `none` placeholder is not a blocker.
3. OpenCode’s companion plugin uses the project’s `.loop` file to resume the owning root session on idle. The default cap is 20 continuation rounds; `--max-rounds N` changes it in AFK mode. A round can finish a parallel batch. Two consecutive unchanged rounds stop continuation for lack of progress.
4. To stop, interrupt the current run, then remove that mission’s project `.loop` file. Keep the ledger and results. Reopen the owning session to continue, or start a new mission with the ledger path after the old loop has stopped. Use `--afk` again if unattended judgment is wanted.
5. Leave OpenCode running in a persistent TUI/server session for idle continuation. One-shot `opencode run` is not a persistent mission host. Claude Code and Codex follow the workflow during the active turn; they do not use the OpenCode idle plugin.

## Prerequisites and outputs

Matt’s workflow skills must be available for the phases the objective needs: wayfinder/grilling and domain modeling, to-spec, to-tickets, research/prototype, implementation/TDD, and code review. Mission reads the applicable skill before using its method and reports missing dependencies.

OpenCode additionally needs the bundled mission agent and continuation plugin; per-call model selection uses the separate task-model plugin. See [OPENCODE.md](OPENCODE.md) for runtime setup and [MODEL_ROUTING.md](MODEL_ROUTING.md) for routing details.

The final handoff identifies outputs, tested code or draft status, evidence, provisional decisions, judge results, and remaining user actions. A passing draft or model agreement does not establish a completed product.
