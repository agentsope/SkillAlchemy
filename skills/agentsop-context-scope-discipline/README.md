# context-scope-discipline skill

Phase D / A5 of the 7-SOP coder-agent skill landscape. **Enhancement overlay.**

This skill distills a single coding-agent-specific rule on top of generic
token-budget advice: **only put files you will actually edit into the working
set, and keep that working-file budget under ~25k tokens.** Past that threshold,
"more context ≠ better edits" — the model loses focus, edits the wrong files,
and misses targets you just added. Breadth (finding files) is delegated to the
sibling [[agentsop-repo-map]] skill (read-only signature map); the working set is reserved
for depth (the files you're changing this turn).

The canonical evidence is Aider's measured distraction threshold:

> "Above about 25k tokens of context, most models start to become distracted."
> — aider.chat/docs/troubleshooting/edit-errors.html

## Why this is an enhancement overlay, not a standalone skill

Generic "manage your token budget" advice exists everywhere. This overlay adds
the part that's specific to coding agents:

- The **read vs edit distinction** — two different context layers with two
  different budgets. Read-only context (repo-map signatures, `/read` files) buys
  breadth cheaply; the write-set (`/add`-ed files) is where depth and cost live.
- The **"don't add to feel safe" correction** — Aider's data shows repo-map
  *alone* hits the correct file 70.3% of the time on SWE-Bench Lite, so locating
  files never requires loading them into the editable working set.
- A concrete **~25k working-file budget** with monitor/drop/split operations.

## Relationship to sibling skills

- **[[agentsop-repo-map]]** — the breadth partner. Repo-map gives "where" (signatures,
  cheap, whole-repo); this skill governs "which files enter the write-set" (full
  text, expensive, ≤5 files). Read both before a multi-file edit.
- **[[agentsop-session-state-hygiene]]** — the history partner. Both draw on the same ~25k
  budget. `/drop` reclaims budget on the *file* axis (this skill); `/clear`
  reclaims it on the *conversation-history* axis (session-state-hygiene).

## Files

- `SKILL.md` — 7-section operational skill. Front-matter `name: context-scope-discipline`, `version: 0.1.0`.
- `references/R1-source-evidence.md` — verbatim source quotes with citations.
- `intermediate/operation_candidates.json` — operation-extraction working notes.

## How to use

Read `SKILL.md` end-to-end before your first multi-file edit task. For day-to-day
reference jump to:

- §2 mental model — read vs edit, the two-budget split, the 25k dilution threshold.
- §3 SOP — classify → locate-then-add → add/read → watch → drop → split.
- §4 operations — 8 named ops with Trigger/Action/Output/Evidence.
- §5 dilemmas — "understand 10, edit 2" and "budget full mid-task" decision trees.
- §7 cross-framework — `/add` (Aider) vs `Read` (Claude Code) vs `@file` (Cursor)
  vs `read_file` (Cline).

## Citation policy

Inline bracketed citations point to aider.chat docs/blog where a specific claim
or figure (the 25k threshold, the 70.3% file-hit rate) is load-bearing.
`references/R1-source-evidence.md` carries the verbatim quotes.
