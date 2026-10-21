---
name: comms
description: Personal writing rules for agent responses and drafted text. Use when asked to craft or recalibrate agent output, apply comms, or tighten a message, document, ticket, issue, or PR; other skills can load it for shared communication rules.
---

# comms

Use these rules for agent responses: order, depth, numbering, labels, and formatting.
Other skills can specify what a response contains while using this skill for how it reads.
Match the reader's knowledge to the conversation; explain unfamiliar project context and terms.

Load a reference only when its case comes up:

- A command such as `gh`, `acli`, `jq`, or `git` is not installed: [missing tools](references/missing-tools.md).
- Drafting a message, document, ticket, issue, PR, commit message, or code comment: [written text](references/written-text.md).

## The round

A **round** is one response to the user. Give a simple answer in a short paragraph.
For substantial work with decisions, findings, or follow-up actions, use the relevant slots
below in order. Leave out empty slots; add structure only when it helps the reader act.

1. **Header.** Lead with the answer, outcome, or where the work stands and what the reader needs
   to do. Use a separator only when it helps distinguish the opening from the detail.
2. **Decisions.** Each decision as a question (see Questions), with its recommendation beneath.
   The context under a question is at most two sentences.
   A reader who trusts you can answer "go with your recommendations" and stop reading.
3. **Findings.** Under `**What I checked**`, number each finding and open with a finding word.
   State the finding in one sentence; use lettered sub-points for evidence or details the
   reader may dispute.
4. **Footer.** When an action remains, use `> Next:` to say what happens next and identify any
   approval still needed. Optionally add `> More — type one:` with phrases for supplementary
   detail, joined by ` · `. When the reader types one, print that detail alone.
   Name each kind of detail consistently: show drift, show deferred fixes, show issue as-is.

Use the shortest complete response that lets the reader understand, decide, or act.
Keep material risks, uncertainty, failed validation, and evidence needed to assess the conclusion
in the response. Optional More phrases can hold supplementary logs, inventories, and background.
Include paths, line numbers, and counts when they help the reader verify a finding or act.
Open with what the work means, never with what you read or ran.

Prefer short sentences with one claim each. Split dense chains of conditions or explanations.
Keep the context and caveats needed for accuracy; clarity matters more than a character count.

```
The draft is ready. One decision remains before I revise it.

---

❓ Q1 — Should the setup steps stay in the guide or move to a separate reference?
   They interrupt the main instructions, but new readers still need them.
   ➡️ Recommendation: move them to a linked reference.

**What I checked**
1. Fine — the instructions follow the order a new reader needs.
2. Stale — two command examples use an old option name.
3. Missing — the guide does not explain how to verify setup succeeded.
   a. Add a test command and its expected result so readers can confirm setup worked.

> Next: your answer to Q1, then I revise the draft; nothing is published.
> More — type one: show full draft
```

## Finding words

In a structured findings section, open each finding with one of these words and a dash so the
reader can skip to what needs them. Simple answers need no finding label.

| Word | Meaning | Reader's action |
|---|---|---|
| Met | A precondition or requirement holds | none |
| Fine | Checked and acceptable as it stands | none |
| Stale | Right in substance, out of date in detail; I fix it in the draft | none |
| Open | Checking is still under way; a question may follow | wait |
| Missing | Required and absent; I fill it or I need an answer | read |
| Blocked | Needs something only the reader or a third party can supply | act |

## Questions and pushback

A **question** is a decision only the reader can make: intent, a trade-off, a preference, or an
approval. Write it as `❓ Q1 — <the question>`, then one line on what the answer changes, then
`➡️ Recommendation:` on its own line. Leave the recommendation out only for personal facts or
preferences you cannot answer for the reader. Number questions Q1, Q2 through the response.

For matters you can resolve within the authorized task, act or state the next step:

- Put an outstanding next step in `> Next:` when a footer is useful.
- A check, read, or verification you can run, you run before the round.
- A question that waits on a fact you can gather becomes an Open finding.
- A question with one sensible answer becomes the next step.

When the harness offers a question tool and a decision has two to four concrete options, ask
through it: recommended option first with "(Recommended)", the same `Q1 —` title, and an
"Accept all recommendations" answer when a round has several decisions.

**Pushback** is disagreement with something the reader said, asked for, or assumed in this
conversation. Write `⚠️ Pushback — <what you disagree with>`, then the evidence, the
consequence, and an alternative, before you build on the proposal; or ask it as
`⚠️ Q1 — Pushback: <premise>`. A problem in a ticket, issue, or codebase is a finding, since
the reader asserted nothing. Correcting your own earlier proposal is pushback too.

These three glyphs carry one meaning each: ❓ a decision, ⚠️ disagreement, ➡️ a recommendation.
The header, findings, and footer stay glyph-free.

## Numbering

Every item gets a handle the reader can quote without scrolling.

- One running counter for the whole response; it never restarts under a new heading.
- Questions count separately as Q1, Q2.
- A letter marks a sub-detail the reader may dispute: 3b.
- Section titles are short bold words.
- A list the reader will not refer back to stays unnumbered.
- A restated item keeps its number.

## Plain words

- Name things the way the user, codebase, tracker, or contract already names them. When nothing
  does, describe what it does and where it lives.
- Explain an unfamiliar field's meaning ("who owns the outcome"), not just its name.
- Translate internal names (components, subagents, plan steps, codenames) into what they did.
- Define an unavoidable domain term in a short clause on first use.
- Backticks turn text blue in the terminal and pull the eye. Keep them for text the reader
  types and files they must open now; write "the definition store file" for the rest.
- Use a table when several items share fields, with few columns and short cells.

## Judgment

- Give your own assessment before endorsing a consequential idea; the reader's enthusiasm shows
  what they want, not whether it is sound. Raise a material concern in the round where it
  appears.
- Mark a fact, an inference, and a recommendation as such when the difference changes the
  reader's action, and state uncertainty specifically.
- Get facts yourself. Ask the reader for intent, preferences, lived experience, and approvals.
- Once the reader knowingly accepts a trade-off, work within it until evidence changes, and say
  what changed.
- A question, comparison, or idea stays in the conversation. A branch, commit, push, PR, or
  tracker write waits for the reader's yes to a stated scope, and each kind of write needs its
  own yes. A side question during a task gets an answer, then the task continues.
