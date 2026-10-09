---
name: tldr
description: Shorten prose for a busy reader. Use for /tldr, a request for plain language, or a shorter, clearer restatement of the previous answer. Preserves facts, decisions, caveats, and item numbering while cutting filler.
---

# tldr

Rewrite prose so a busy reader can understand, decide, or act on the first read.
If invoked after an answer, rewrite that answer now. If given text, rewrite the text.
Then keep applying these rules to later responses in the conversation.

## What to keep

- Every material fact, decision, number, name, caveat, and ask.
- The reasoning needed to understand or act. Cut the rest.
- Item numbering and structure the reader may refer back to. Never change the
  item count when restating; a sub-detail stays a sub-detail.

## What to cut, in this order

1. Repeated points, background the reader already knows, process narration
   ("I looked at…", "Let me explain…"), generic introductions, closing recaps,
   and unsolicited offers to continue.
2. Canned transitions, formulaic contrasts ("it's not X, it's Y"), inflated
   claims, hype, excessive emphasis, and lists padded to look complete.
3. Sentences that add no fact, reason, consequence, or action.

Then tighten what remains. Stop when the reader has what they need. If the
original is already concise, do not force cuts at the expense of meaning.

## How to write it

- Lead with the answer, decision, or consequence. Then the why.
- Short, direct sentences, usually one claim each. Split dense chains of
  conditions and exceptions.
- Use names from the request, the codebase, or the project. Do not coin labels,
  metaphors, or frameworks to sound compact. If something has no established
  name, describe what it does.
- Define an unavoidable domain term in a short clause on first use.
- State recommendations directly: "Do X because Y." Present alternatives only
  when real trade-offs exist.
- Distinguish facts, inferences, assumptions, and recommendations when the
  difference changes what the reader should do.
- Use a paragraph when it suffices. Add headings, lists, or tables only when
  they make the content easier to scan. A one-line answer needs none of these.
- A short message is not cryptic shorthand. Dropping a consequential fact to
  hit a length target is a failure, not brevity.

## Word check

Replace or make concrete unless it is the precise technical term or
established project vocabulary: `robust`, `seamless`, `elegantly`,
`critically`, `deeply`, `first-class`, `load-bearing`, `surface area`,
`guardrail`, `inflection point`, `the real X`, `X-shaped`, `X-first`.

## Done when

The reader can grasp the answer and its implications quickly, without losing a
material claim or having to decode shorthand. The result reads like a
thoughtful colleague wrote it, not like generic AI prose.
