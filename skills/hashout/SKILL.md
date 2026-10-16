---
name: hashout
description: Two to five agents in different harnesses (Claude Code, Codex, OpenCode, or any with a shell) debate an architecture choice, design, or idea in turns through one shared Markdown file until they agree or deadlock, optionally applying another skill and acting on the agreed decision. Use for /hashout or $hashout, to start a debate, join one from a pasted /hashout join line, or settle a disagreement with another agent.
---

# hashout

Agents take turns in seat order (1, 2, 3, ...) in one append-only file under
`/tmp/hashout/`. Use it for architecture decisions, design reviews, and
brainstorming that should end in a decision. The script
`<skill-dir>/scripts/hashout` (`<skill-dir>` is the folder holding this file) hands
out seats, enforces turns, and writes every marker line. Write to the file only
through the script. POSIX `sh` and core tools; no other dependencies.

Shell state does not carry between your commands, so pass the file path and your
`--seat` on every call. Run `hashout --help` for all options.

## Start a debate: `/hashout init ['topic']`

1. If no topic was given, ask the user to paste it.
2. Rewrite it into a debate prompt with these parts, using only what the user gave:
   - **Question:** one decision, answerable yes/no or pick-one. For brainstorming, the question is which idea or ideas to pursue.
   - **Context:** facts, links, files, and constraints from the paste. Add nothing.
   - **Method:** optional. A skill every seat applies in its rounds, such as `/grill` or `/wayfinder`, named exactly as the user gave it.
   - **Decide by:** unanimous (default) or majority.
   - **Deliverable:** what the final Outcome must contain.
   - **After agreement:** optional. What the agents may do with the decision and which seat does it, for example "seat 1 writes the ADR to docs/adr/". Without this line, agents only report the Outcome.
   - **Out of scope:** anything the user ruled out.
3. Show the prompt, a short title, and the number of participants (default 2). Create nothing until the user approves.
4. Write the approved prompt to a temporary file and run:
   `hashout init --title "<title>" --topic-file <file> --participants <N> [--rule majority]`
5. Join as seat 1 (below), then give the user the printed `join:` line to paste into each other harness.

## Join: `/hashout join <file>`

Run `hashout join <file> --harness <your harness> --model <your model id>`. It
prints your seat. Then loop.

## The loop

1. `hashout wait <file> --seat <N>`. Keep `--timeout` (default 90 seconds) under
   your harness's command time limit.
   - `0` your turn: read the whole file, then post. The output lists open claim IDs.
   - `3` timed out: run wait again.
   - `4` the seat whose turn it is went silent: run `hashout skip <file> --seat <N>`, then wait.
   - `2` deadline or round limit: close (below).
   - `1` closed, or `5` you are marked absent: stop and report to the user.
2. Post your round with `hashout post <file> --seat <N>` and the body on stdin
   (a heredoc) or `--body-file`. The script adds the heading and end marker.
3. Repeat.

## Round body

```
Position: one or two sentences.

C1.1 [open] A new claim. Evidence: what supports it. Checked: what you opened or ran.
C2.3 [accepted] Checked: ran the test it cites; it passes.
```

- A new claim's ID is `C<your seat>.<next number>`.
- To change any claim's status, including another seat's, start a line with **that claim's existing ID** and the new status. Do not create a new ID to agree with a claim; the old one stays open.
- Statuses: `open`, `accepted`, `refuted`, `retracted`. The latest line for an ID wins.
- Check evidence before accepting a claim and say what you checked. Do not agree to be agreeable, and do not hold out without evidence.
- If the prompt names a Method skill, apply it in your rounds and record its findings as claims.
- To propose a result, add a `#### Outcome` section with the deliverable and `[ACCEPT <your seat>]` on its own line.
- To accept the latest proposal, put `[ACCEPT <your seat>]` on its own line in your round. A new `#### Outcome` resets all accepts.

## Close

- `hashout close <file> agreed --seat <N>` succeeds only when no claim is open and the rule is met: every present seat (unanimous) or more than half (majority) accepted the latest Outcome.
- At the deadline or round limit without agreement: `hashout close <file> deadlocked --seat <N>`.
- After an agreed close, the seat named in **After agreement** does that work and nothing more. Then each agent reports the result, the Outcome, and the file path to its user.

A seat skipped twice in a row is marked absent; agreement is then counted among the seats still present.
