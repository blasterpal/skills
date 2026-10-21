# Subagent brief

Fill this template for one ledger task. Give the worker the task and its done condition verbatim.

- **Task:** `<copy the complete - [ ] line>`
- **Done condition:** `<copy the exact command and expected result>`
- **Read:** `<exact paths needed for this task>`
- **May edit:** `<exact files or narrow directories the worker owns>`
- **Repository rules:** `<links to relevant AGENTS.md or other rules>`
- **Context:** `<only decisions or dependencies needed for this task>`

Return:

1. Files changed.
2. Commands run, with their output.
3. Anything unresolved.

The parent runs the done condition and decides whether the ledger can be ticked.
In AFK mode, the worker gathers facts; the parent records provisional decisions in the ledger.
