---
name: memorywipe
description: "Audit and clean persistent memory, instruction chains, and injected context in Claude Code, Codex, or OpenCode. Use when asked to find stale, duplicate, noisy, fragmented, or unexpectedly loaded agent context, then review cleanup decisions."
---

# /memorywipe — Memory and context audit

Audit persistent and auto-loaded context for staleness, duplication, noise, and
verbosity. Identify the active harness before interpreting files. Present one
batched decision set before changing memory. Apply approved changes directly
when safe; otherwise write exact cleanup commands for the active shell.

## Context location

A **context location** is a user-maintained corpus outside auto-loaded memory.
Use it to verify duplicates when one exists. Hank's is HQ (`$HQ_HOME` or `~/hq`);
for another user, discover their configured location or use canonical project
documentation. Do not assume their store follows HQ's layout.

## Harness discovery

Determine the active harness from runtime metadata, environment variables, executable, and
configuration. Do not infer it from whichever hidden directory happens to exist. Audit the
active harness by default; audit other harnesses only when the user asks or they
are clearly in scope.

Use configured roots rather than hardcoded home paths:

| Surface | Claude Code | Codex | OpenCode (current v1) |
|---|---|---|---|
| Harness home | configured Claude directory, commonly `~/.claude` | `$CODEX_HOME`, otherwise `~/.codex` | configured OpenCode directory, commonly `~/.config/opencode` |
| Generated memory | commonly project memory under `projects/<encoded-project>/memory/`, with `MEMORY.md` as its index | `memories/` under Codex home; generated summaries, durable entries, recent inputs, and evidence | inspect installed plugins or integrations; do not assume a native persistent memory store |
| Global instructions | configured/global `CLAUDE.md` and imports | `AGENTS.override.md` when non-empty, otherwise `AGENTS.md`, under Codex home | global `AGENTS.md`; Claude `CLAUDE.md` fallback when enabled and no OpenCode global file exists; configured `instructions` |
| Project instructions | applicable `CLAUDE.md` chain and imports | one applicable instruction file per directory from project root to cwd: `AGENTS.override.md`, `AGENTS.md`, then configured fallback names | applicable `AGENTS.md`, or `CLAUDE.md` fallback, plus configured instruction files |
| Supported memory controls | use the controls exposed by the installed Claude Code version | `/memories` per chat; Settings > Personalization or `[features] memories` and `[memories]` config for persistent behavior | inspect the installed memory provider's documented controls before proposing a change |

For Codex, read `config.toml` only far enough to resolve `CODEX_HOME`,
`project_doc_fallback_filenames`, `project_doc_max_bytes`, and memory settings. Do not treat
`CLAUDE.md` as Codex-loaded merely because it exists; it applies only when reached through a
symlink or configured fallback name. Codex rebuilds its `AGENTS.md` chain per session, so
there is no instruction cache to clear.

For OpenCode, inspect the installed version, `opencode.json` or `opencode.jsonc`,
its `instructions` entries, project and global rule files, and active plugins.
`CLAUDE.md` is a fallback only when compatibility is enabled and the corresponding
`AGENTS.md` is absent. A plugin's memory is third-party state; establish its
owner and controls before proposing deletion. Do not treat session transcripts
as persistent memory merely because they are stored on disk.

## Scope

Audit the applicable layers in this order:

1. **Persistent memory** — the active harness's memory entries, indexes, and injection controls, if any
2. **Project-scoped memory** — only when the harness maintains project-specific memory
3. **Always-loaded instructions** — the harness-specific chain, imports, size limits, and shadowing/override behavior
4. **Project identity fragmentation** — duplicate encoded project directories caused by symlinks, path spelling, or worktrees; skip when the harness has no such mapping
5. **Third-party injection** — hooks, plugins, or services that inject conversation memory, including Hindsight when installed and active

## Process

### Phase 1: Inventory

Parallelize independent reads when supported; delegate only when the runtime
and current instructions authorize it.

Read each human-readable memory entry and memory index in full. For generated evidence, transcripts,
or databases, inspect metadata first and read underlying content only when needed to verify
provenance or duplication. Record: harness, path, type, injected or on-demand, last modified,
one-line summary, staleness (current / possibly stale / likely stale), and duplication with
always-loaded or canonical context files.

Also record the effective instruction chain in load order. For Codex, account for the first
non-empty global file, root-to-cwd project files, configured fallback names, and the combined
byte limit. For Claude Code, follow imports and distinguish user-, project-, and local-scoped
instructions supported by the installed version. For OpenCode, include active
global and project rules, configured `instructions`, and plugin-injected context;
verify precedence against the installed version before claiming a file is loaded.

### Phase 2: Classify and interview

Group findings by impact and present them to the user as one batched decision set:

1. **Duplication chains** — same content loaded 2+ times. Memory files that repeat a
   verified canonical source are redundant.
2. **Likely stale** — events/plans/statuses >2 months old, probably resolved.
3. **Possibly stale** — time-sensitive content that may have drifted.
4. **Cross-scope leakage** — project memories duplicating global, or vice versa.
5. **Structural issues** — fragmented dirs, orphaned worktrees, symlink splits.

Offer per category: delete all, keep behavioral / delete state, skip, or generate script.
Add harness-native options when applicable: disable memory use, disable future generation,
or purge generated memory.

Use the current runtime's structured user-input mechanism when available; otherwise ask one
concise batched question in ordinary conversation.

### Phase 3: Execute approved deletions

Delete approved files and update a human-maintained memory index when one exists. If direct
deletion is blocked by permissions or runtime policy, accumulate exact commands in a cleanup
script instead of retrying.

Treat Codex `memories/` as generated state. Prefer `/memories`, Settings > Personalization,
or documented config settings for enabling or disabling use and generation. Do not hand-edit
generated entries, evidence, or indexes to simulate compression. If the user approves a
purge, remove only the inventoried Codex memory targets, preserve configuration unless its
change was separately approved, and avoid racing an active background memory update.

### Phase 4: Deep pass (compression)

After bulk cleanup, read every surviving human-maintained memory file in full and assess:

1. **Load every turn?** — Is this worth the tokens on every session start?
2. **Could be a pointer?** — Detailed reference info (people, specs, operational detail)
   that fires rarely should become a 2-line stub pointing to the user's context
   location or canonical project documentation.
3. **Too verbose?** — Can the file be compressed without losing signal?
4. **Redundant with siblings?** — Overlap between remaining files → merge.
5. **No file needed?** — Rule fully captured by one entry in the harness's auto-loaded
   memory index → delete the backing file and keep the inline entry.

Actions for human-maintained memory: KEEP, COMPRESS (rewrite shorter), POINTER (stub +
context ref), MERGE (combine with another), INLINE (delete file, rule lives in a
human-maintained memory index only).

Actions for Codex-generated memory: KEEP, DISABLE_USE, DISABLE_GENERATION, or PURGE.
Do not apply COMPRESS, POINTER, MERGE, or INLINE inside Codex's generated store.

### Phase 5: Execute compression

For each approved action, rewrite or delete the file. When the harness uses a
human-maintained auto-loaded memory index, rebuild it with this logical structure.
`MEMORY.md` is one possible filename; preserve the harness's actual filename and supported
syntax. Do not impose this structure on Codex-generated memory.

```
# Files (loaded every session)
- [Name](file.md) — one-line description

# Inline rules (no backing file needed)
- Rule text that stands alone as a memory-index entry

# Context pointers (load on demand, not every session)
- Topic description → second-brain, project-documentation, or owning-skill location
```

### Phase 6: Script and summary

Write a cleanup script to the user's configured scratch location for anything blocked by
permissions or requiring interactive confirmation (directory merges, orphan removal, or a
memory control available only in the harness UI). For UI-only controls, print exact manual
steps as comments rather than inventing shell commands. If no scratch location is configured,
create a narrowly scoped temporary file and report its path.

Print: files before → after, lines before → after, remaining issues.

## Rules

- **Canonical source**: determine canonical sources from the user's explicit configuration,
  context location, repository documentation, and instruction chain. Memory
  files duplicating a verified canonical source are redundant.
- **Save-at-least-once**: before deleting a duplicate, confirm the content exists in at
  least one canonical location. Default to checking; skip only if user says so.
- **Don't touch canonical context or instruction files**: audit memory only. Report overlap
  with context files, `AGENTS.md`, `CLAUDE.md`, or equivalents, but do not edit
  them unless the user explicitly expands the scope.
- **Respect harness ownership**: human-maintained Claude memory can be compressed after
  approval; Codex-generated memory is inspected, controlled, or purged, not hand-rewritten.
- **Controls are separate from content**: disabling memory use, disabling future generation,
  deleting existing memory, and changing third-party injection are separate decisions.
- **Compress aggressively**: most feedback memories are 1-2 sentences of signal in 15-30
  lines of context. The signal can usually fit in 3-6 lines or one memory-index entry.
- **Pointers over inline detail**: operational references (API keys, 1Password paths, org
  charts, people profiles, technical specs) belong in a context location or
  canonical project documentation, not auto-loaded memory. Memory holds the behavioral
  rule; the context location holds the detail.
