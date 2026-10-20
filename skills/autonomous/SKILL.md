---
name: autonomous
description: Run a multi-step task without routine interruptions when the user requests an autonomous sweep, refactor, audit, or implementation. Record judgment calls in one file for later human review while preserving required approval boundaries.
---

# Autonomous

Complete the user's goal without stopping for routine clarification. Make reasonable,
reversible choices within the authorized scope, and leave the user a reviewable record
of decisions you would otherwise have asked them to make.

## Start

1. Use the invocation arguments or current request as the goal. If neither supplies
   one, ask: "What's the goal?"

2. Read the applicable project instructions. Derive scope and checkable completion
   criteria from the goal. Resolve routine ambiguity from available evidence.

3. Select one decision file: use the user's specified path, otherwise
   `AUTONOMOUS-DECISIONS.md` in the task's project root, or the starting working
   directory when there is no project. Resolve the absolute path once and keep it
   for the whole task, including after directory changes. All workers, if delegation
   is separately authorized, report decisions to the coordinating agent for writing
   to this same file.

4. State the contract before starting:
   > `Goal: [goal] | Scope: [scope] | Done: [criteria] | Decisions: [absolute path]`

## Execute

Keep working until the completion criteria are met or the remaining work is blocked.
Give brief updates after significant chunks: what finished and what comes next.
Investigate failed checks; keep independent work moving when one item is blocked.
Use background execution only when the harness supports it and it helps the task.

For each decision you would normally put to the user:

1. **Decide and record** when the choice is within the authorized goal, reasonably
   supported, and reversible at acceptable cost. Prefer the smaller change that
   preserves existing behavior. Record the choice before acting on it, then proceed.
2. **Defer the affected action** when the choice needs authority you do not have,
   has irreversible or costly consequences outside the authorization, or lacks a
   reasonable safe default. Record what is blocked and the approval or information
   needed. Continue independent work. Ask a focused question if no useful work remains.

An uninterrupted run does not grant permission to expand scope, spend money, publish,
send messages, delete data, weaken security, or bypass explicit review requirements.
Perform such actions only when the user has authorized them and applicable rules
allow them. A decision-file entry is not approval. Missing credentials remain a
blocker; never seek them through an unauthorized route.

## Decision file

Create the file on the first review-worthy decision. Append to an existing file;
preserve earlier entries and human review notes. Use a dated task heading for each
run. Keep all decisions for this task in this file rather than creating one file per
decision or chunk. Do not create an empty file when no such decisions arise.

Record material assumptions, competing interpretations, meaningful trade-offs,
substituted approaches, and deferred approvals. Routine implementation details
with a clear project convention need no entry. Store concise reasons and evidence,
not private deliberation, secrets, or unnecessary personal information.

Use this entry format, with a unique ID within the file:

```markdown
## [Timestamp with timezone] — [Task goal]

### [ID] — [Decision title]
- Review: pending
- Action: proceeded | deferred
- Question: What would normally have been asked?
- Choice: What was chosen, or which action is blocked?
- Reason: Relevant evidence, assumptions, and the main alternative rejected.
- Consequences: Affected behavior/files, risks, and how to reverse the choice.
- Validation: Check to run, then its actual result or why it remains unverified.
- Human follow-up: What to confirm or supply, and what would change if rejected.
```

Update validation after acting. If a choice changes, append a superseding entry
referencing the original ID; retain the original record. Only the user can mark a
decision reviewed or approved. If the file cannot be written, report the failure
and defer decisions that require recording rather than proceeding without a record.

## Finish

Check the completion criteria. Report what completed, checks actually run, and
remaining blockers. Link the decision file and identify pending review items by ID,
especially choices that changed behavior or left work deferred. If there were no
review-worthy decisions, say so without claiming a file was created. Do not claim
completion for blocked or unverified work.
