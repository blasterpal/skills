# Saving a conversation

## Choose the target

Use the supplied topic or infer a short title from the current conversation. Choose a distinctive lowercase kebab-case slug. A preload already supplies `CREATED_AT`, `SESSION_REF`, `CONVO_ROOT`, `TODAY`, today's snapshots as `TODAY_CONVO=slug|path|title|project` rows, and any `save_hook` output; otherwise run `prepare-save <slug>` once. Retain the creation instant, local date, store root, session reference, and candidate snapshots across tool calls. Apply any profile instructions appended to the preload; they take precedence over this file where they differ.

Amend the snapshot already saved for this subject in this session, or a clear matching snapshot from today. Read it and any linked memo before writing. If several candidates fit, ask which to amend. An older exact slug match may be amended for a continuation; choose a different slug for a distinct subject. `save new` always creates a new snapshot with a unique slug. A save captures the current conversation; reading another profile's material does not authorize copying it into this one.

For a new snapshot use `<root>/YYYY-MM/YYYY-MM-DD-<slug>.md`. For amendments retain its filename, slug, original date, creation instant, and project. Keep its title unless the user requests a rename.

## Compress to current state

Keep the smallest amount of context that lets another session continue correctly. Remove repeated explanations, superseded state, resolved blockers, and completed steps whose result is already captured. Combine overlapping points. Summarize evidence with source pointers rather than reproducing it. Preserve exact identifiers, commands, constraints, and uncertainty when they affect the next action.

Record current decisions with brief rationale. Retain an earlier decision, rejected alternative, or failed approach only when omitting it could cause a wrong decision or repeated work. Replace superseded reasoning rather than accumulating a chronology. Detailed thought and work history belongs in episodic transcripts when available; do not claim a transcript was archived without evidence. Missing transcript access does not change these briefs into uncompressed histories.

Create or update a memo only when supporting evidence, trade-offs, or unresolved uncertainty materially helps revisit current decisions and would burden the continuation brief. If the snapshot already contains what is needed, omit the memo and its pointer. Keep each fact in one artifact, with a short pointer where needed.

Use an existing project context file as the memo only when that file is already established for this work and updates are authorized. Otherwise use `<root>/YYYY-MM/memos/<snapshot-filename>`. Reuse a valid pointer when its memo is still needed; resolve broken pointers when retaining a memo. Rewrite a standalone memo around reasoning relevant now. Preserve unrelated sections of shared context files. A standalone memo names its snapshot with `Convo: ../<snapshot-filename>` and records its latest update date; dated history is not required. If a memo becomes unnecessary, remove its snapshot pointer and leave the existing file in place.

## Preserve plans

Preserve plans authored or edited in the conversation verbatim as separate files. Link existing plan files in place. For plans still only in conversation, use `<root>/YYYY-MM/plans/YYYY-MM-DD-<slug>.md`; keep exact code, steps, and wording. Do not paraphrase a plan into the snapshot or memo.

## Write and verify

When a memo is needed, write it first, then a self-sufficient snapshot with this shape. Use JSON-style double-quoted strings for title and project; this keeps punctuation valid in YAML and readable by the helper. Omit `session_ids` when unavailable, omit `Deeper context` without a memo, and omit empty sections, plans, or references.

```markdown
---
title: "Topic name"
slug: topic-name
date: YYYY-MM-DD
created: <captured ISO-8601 instant>
updated: YYYY-MM-DD
project: "general"
tags: []
session_ids:
  - <captured harness-qualified session ref>
---

# Topic name

## Objective
<Intended outcome.>

## Current state
<What is true now, including completed work.>

## Decisions
<Settled decisions with brief rationale, or none.>

## Constraints and blockers
<Active constraints, or none.>

## Next actions
<Executable next steps, or none.>

## Deeper context
Memo: memos/<snapshot-filename>
Heading: <exact heading, only when targeting a project context section>

## Plans and references
<Literal paths, URLs, and one-line descriptions.>
```

For an amendment, update `updated`, merge relevant tags, append a known session ref only if absent, and recompress the snapshot and any retained memo using the rules above. Do not invent session IDs, creation dates, verification claims, or project scope. Check current evidence before recording an uncertain next action as not started.

Run `register <absolute-snapshot-path>` after writing. It validates the store layout and unique slugs and rebuilds `index.tsv`. Then verify retained memo and plan pointers resolve, and any `Heading:` matches literally. Check that another session can continue correctly from the snapshot and that each retained detail affects continuation or a consequential decision. Compress further where removing a detail changes neither. Use this check rather than a fixed word limit.

On failure, report an incomplete save and the files written; preserve pre-existing artifacts. Finish with `Saved <path>` or `Amended <path>`, adding `(memo: <path>)` only when a memo is linked.
