# R1 — Source Evidence (context-scope-discipline)

Verbatim quotes backing the load-bearing claims in `SKILL.md`. Each entry gives
the quote, the citation, and how the skill uses it.

---

## E1 — The ~25k token distraction threshold (the core rule)

> "Above about 25k tokens of context, most models start to become distracted."

Source: [aider.chat/docs/troubleshooting/edit-errors.html]

Used in: §1 (activation — context window filling), §2.1/§2.3 (mental model — the
dilution threshold, "more context ≠ better edits"), §3 Phase 4 (budget watch),
§5 case 2 (budget full mid-task), §6 (boundary — empirical not physical limit).
This is the single figure the whole skill is built around. It is a *signal
threshold* (accuracy starts dropping), not a hard ceiling.

---

## E2 — Weaker models are more sensitive to context distraction

> Weaker models are "more likely to disobey the system prompt instructions"
> (from the same edit-errors troubleshooting guidance on why edits fail).

Source: [aider.chat/docs/troubleshooting/edit-errors.html]

Used in: §2.3 (the 25k threshold bites harder on weaker models).

---

## E3 — Repo-map alone identifies the correct file 70.3% of the time

> Aider's repo-map "successfully identified the correct file to edit in 70.3% of
> the benchmark tasks" (SWE-Bench Lite), with no embeddings, no code execution,
> no network.

Source: [aider.chat/2024/05/22/swe-bench-lite.html]

Used in: §2.4 ("full-add to be safe" is an illusion — locating files does NOT
require loading them into the working set), §4 Op 2 (locate-then-add), §5 case 1
(edit 2 of 10 — lean on the map for the other 8), §6 (the residual ~30% needs
human backstop). This figure is what licenses the "breadth lives in the read-only
map, not the write-set" split.

---

## E4 — Repo-map budget is dynamic and shrinks as files are added

> "Aider adjusts the size of the repo map dynamically based on the state of the
> chat."

Source: [aider.chat/docs/repomap.html]

Used in: §2.5 (dynamic budget — working set grows, map shrinks), §3 Phase 4 /
§4 Op 6 (dropping a file lets the map re-expand to fill the freed budget),
§5 case 2 (shrink map to free budget once targets are locked). Establishes that
the read-only and read-write layers share one budget rather than independent pools.

---

## E5 — Read-only vs read-write context is a hard editing boundary

> The LLM may only edit files that have been added to the chat (the write-set);
> read-only context (repo-map, `/read` files, CONVENTIONS) is visible but not
> editable.

Source: [aider.chat/docs/more/edit-formats.html], [aider.chat/docs/usage/conventions.html]

Used in: §2.2 (three-layer context table), §3 Phase 3 (`/add` for edits, `/read`
for references), §4 Op 1/Op 4 (classify; read), §7 (Aider's hard write boundary
vs the soft "read-equals-editable" model in Claude Code/Cursor/Cline). This is
why the read/edit distinction can be expressed concretely in Aider and must be
expressed as self-discipline elsewhere.

---

## E6 — Wrong-file edits come from a mis-sized working set

> A model editing the wrong file "is almost always because that file was not
> `/add`-ed, or you `/add`-ed too many unrelated files."

Source: [aider.chat/docs/usage] (and the edit-errors troubleshooting guidance)

Used in: §1 (activation — agent making changes to wrong files), §4 Op 3 (add,
sparingly), §5 case 3 (don't fix wrong-file edits by adding MORE files —
add the target or drop the noise). Grounds the "less /add, braver /drop" rule.

---

## E7 — Command surface: /add, /read, /drop, /tokens

> `/add <files>` adds files to the chat (editable); `/read <file>` adds read-only;
> `/drop <files>` removes from chat; `/tokens` reports current token usage.

Source: [aider.chat/docs/usage/commands.html]

Used in: §3 (all phases), §4 (Ops 3/4/5/6), §7 (cross-framework interface row).
The concrete operation names; behaviors are framework-agnostic.

---

## E8 — Context overflow on monorepos is mitigated by scoping/splitting

> Token-limit troubleshooting recommends narrowing scope (subtree-only, ignore
> files) and breaking large tasks into smaller sessions when context overflows.

Source: [aider.chat/docs/troubleshooting/token-limits.html]

Used in: §3 Phase 6 (split, don't stuff), §4 Op 8 (split-task), §5 case 2 step 5.
Backs the "task too wide" diagnosis when budget can't be recovered by drop/shrink.

---

## Cross-skill consistency notes

- The 25k figure (E1) is shared verbatim with [[agentsop-repo-map]] §2.4 and underpins
  [[agentsop-session-state-hygiene]]'s clear/keep decisions. The three skills must cite the
  same number; they do.
- The 70.3% figure (E3) is the same one [[agentsop-repo-map]] uses as its baseline metric.
  Here it is repurposed to justify *not* loading files into the write-set merely
  to understand them.
- The `/drop` (file axis) vs `/clear` (history axis) split (E4/E7) is the explicit
  seam between this skill and [[agentsop-session-state-hygiene]]; both share the E1 budget.
