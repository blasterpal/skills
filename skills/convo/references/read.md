# Reading snapshots

The helper emits JSON for `list` and `recent`, with date, slug, title, project, and absolute path. Show a compact table with date, ref (the slug), and summary; include project when useful. These are saved snapshots, not a record of the unsaved session. If a topic matches no title, search Markdown contents under the configured root, excluding `memos/` and `plans/`, and show relevant matches.

With `--episodic`, use the current agent's available history-search capability. For `list`, request the past 30 days; for `recent`, request the newest 15. Merge with local results by date, label transcript results as episodic, and retain only the newest 15 for `recent`. If unavailable, show local results and mention that archived history is unavailable. A UUID reference explicitly identified as episodic goes through that capability, not the local helper.

`show` prints `CONVO=<absolute-path>` and the snapshot in one call. Summarize its objective, current state, decisions, and next actions. Opening a snapshot supplies context; it does not itself authorize executing those actions. If the helper reports ambiguity, show its candidates and ask the user to choose. Distinguish a missing local snapshot from unavailable transcript access.

Resolve a literal `Memo:` path relative to the snapshot's parent. Show the pointer without automatically loading it. Read the memo when the user asks for current rationale, evidence, alternatives, or uncertainty; when the snapshot routes the current question there; or when the memo could resolve a specific missing or conflicting fact. A bare pointer is not a request to read it. For the sequence of thought or work that led here, search episodic history when available; a compressed snapshot or memo may not retain that sequence. If history is unavailable, state the gap rather than reconstructing it as fact.

Search headings first. With `Heading:`, read that exact section through the next heading of the same or higher level. Otherwise read the relevant sections, including dated sections in older memos. A snapshot without a pointer stands alone; do not infer a memo from its filename.
