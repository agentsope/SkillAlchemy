# R3: Dilemma Cases (real, from docs/blog/benchmarks)

Each case is grounded in published Aider documentation or Paul Gauthier's benchmark posts. Cases are framed as **trigger -> diagnosis -> decision rule** so a coder-agent can act.

---

## Dilemma 1 — "The model keeps editing the wrong file"

**Trigger**: LLM proposes edits to a file that wasn't the one you wanted; or invents a file path.

**Diagnosis**: The LLM can only **safely edit files added via `/add`**. If you didn't `/add` the target file, it may try to invent or guess. If you `/add`-ed too many files, it may pick the wrong one.

**Decision rule**:
1. Run `/ls` — confirm which files are in chat vs. read-only vs. repo-map only.
2. If target file is missing: `/add path/to/target.py`.
3. If too many files (>4–5 typical, or token count > 25k): `/drop` everything not directly needed.
4. If the LLM can't name the file: `/ask which file implements X?` — the repo-map lets it answer.

**Why this works**: Aider's design treats `/add`-ed files as the write-set. Files only in the repo-map are visible but not writable. This is the safety boundary.

**Cite**: "Just add the files you think need to be edited" [aider.chat/docs/usage/tips.html]; "Adding a bunch of files that are mostly irrelevant to the task at hand will often distract or confuse the LLM" [aider.chat/docs/faq.html].

---

## Dilemma 2 — "Context window overflow on a large repo"

**Trigger**: token count climbing past 25–50k; model truncating responses; obviously degraded quality on a monorepo.

**Diagnosis**: Three sources of bloat — added files, chat history, repo-map.

**Decision rule** (apply in order, cheapest first):

| Step | Action | Source |
|---|---|---|
| 1 | `/tokens` to see where tokens are going | [aider.chat/docs/troubleshooting/token-limits.html] |
| 2 | `/drop` files no longer needed | same |
| 3 | `/clear` chat history (keep files) | same |
| 4 | Cap repo-map: `--map-tokens 1024` (or `0` to disable for weak models) | [aider.chat/docs/faq.html] |
| 5 | For monorepos: `cd` into subdir + `--subtree-only`; add `.aiderignore` | [aider.chat/docs/faq.html] |
| 6 | Break the task: "Break your code into smaller source files" | [aider.chat/docs/troubleshooting/token-limits.html] |

**The repo-map alone vs. selective add tradeoff**:
- Empty `/add` set → repo-map expands to give the LLM enough to navigate.
- `/add` the right 2–4 files → repo-map shrinks; saved budget goes to the actual code.
- **Never** `/add` everything "to be safe" — it degrades quality. SWE-Bench data: aider with **just the repo-map** found the right file 70.3% of the time. [aider.chat/2024/05/22/swe-bench-lite.html]

---

## Dilemma 3 — "Diff format keeps hallucinating / SEARCH block not found"

**Trigger**: Aider prints "SEARCH block not found in file" or repeated edit failures.

**Diagnosis**: The model is producing edits in the requested format but the SEARCH text doesn't byte-match the file (whitespace, an earlier failed edit, a hallucinated chunk).

**Decision rule** (per [aider.chat/docs/troubleshooting/edit-errors.html]):

1. Check token count (`/tokens`) — at >25k context, models "become distracted" and edit format compliance drops.
2. `/drop` and `/clear` to reduce context.
3. Upgrade the model — "weaker models are more prone to disobeying the system prompt instructions."
4. Fall back to a more reliable format: `--edit-format whole`. Yes it's expensive; yes it works.
5. Try `--architect` — "two-step process often produces more reliable edits, especially with models that have trouble following edit format instructions."

**For GPT-4 Turbo specifically** (historical, but the lesson generalizes): unified-diff format raised refactoring benchmark from **20% to 61%** and cut lazy comments 3×. [aider.chat/2023/12/21/unified-diffs.html] Lesson: when a model leaves `// TODO: implement here` comments, the **edit format** can fix it, not the prompt.

---

## Dilemma 4 — "Should I pay for architect mode?"

**Trigger**: Hard reasoning task. You have access to o1/o3 (slow, expensive, good thinking) but they edit poorly.

**Diagnosis**: Architect mode runs **two LLM calls per turn** — architect produces a natural-language plan, editor translates it into edits. It costs more (two calls) and is slower. But it can recover capability you'd otherwise lose.

**Decision rule** (data-driven):

| Your situation | Recommendation |
|---|---|
| Reasoning model edits cleanly (e.g., GPT-4o, Sonnet) | Skip architect. Solo is fine. |
| Reasoning model lazy/sloppy on edits (e.g., o1-preview alone scored 79.7% diff) | Use architect: o1-preview + Sonnet (82.7%, "entirely practical") [aider.chat/2024/09/26/architect.html] |
| Need SOTA, willing to wait | o1-preview + DeepSeek/o1-mini with `whole` (85%, "quite slow, so probably not practical for interactive use") |
| Routine edits | Solo is faster and cheaper. |

**Surprising data point**: Even Sonnet improved with itself as editor (77.4% → 80.5%). Architect is not just for weak editors — the two-pass discipline helps strong models too. But the gain shrinks; only switch if the marginal cost is worth ~3 percentage points.

---

## Dilemma 5 — "Sonnet is writing 4k-token responses and truncating"

**Trigger**: Claude 3.5 Sonnet response cuts off mid-edit; "Sonnet was often writing so much code that it was hitting the 4k output token limit." [aider.chat/2024/07/01/sonnet-not-lazy.html]

**Diagnosis**: Sonnet is the rare LLM that errs on the side of writing **too much** — full file rewrites instead of minimal diffs.

**Decision rule**:
- Aider already handles this: "Aider allows Sonnet to return code in multiple 4k token responses. Aider seamlessly combines them" and "Aider now prompts Sonnet to discourage these long-winded SEARCH/REPLACE operations." Keep an updated Aider version.
- If you see truncation anyway, manually prompt: "Make minimal SEARCH/REPLACE blocks. Do not quote unchanged sections."
- Performance jump from this fix: Sonnet refactoring benchmark went from **55.1% → 64.0%**. The fix is worth real performance.

---

## Dilemma 6 — "JSON tool-call edit format vs. plain text diff"

**Trigger**: You're building an agent that wraps Aider or competes with it, and you wonder whether to use structured tool calls.

**Diagnosis**: Aider explicitly tested this. **JSON-wrapped code performs worse across every model.**

**Decision rule**: Use plain-text diff formats for code. JSON for non-code structured returns (booleans, choices). The hard data:

> "All of the models did worse on the benchmark when asked to return code in a structured JSON response." [aider.chat/2024/08/14/code-in-json.html]

Even with OpenAI's "strict mode" enforcing JSON validity, **the code quality inside the JSON degraded** — more SyntaxErrors and IndentationErrors. Even Sonnet, which avoided syntax errors, scored lower with JSON. Suggested mechanism: "JSON-wrapping may distract or challenge models in a way that reduces their ability to reason about solving coding problems."

For an agent-coder: do not wrap your code edits in tool-call JSON if you can return text. If your harness requires tool calls, put the code in a single string field — but expect a quality hit.

---

## References

- [aider.chat/docs/troubleshooting/edit-errors.html]
- [aider.chat/docs/troubleshooting/token-limits.html]
- [aider.chat/docs/faq.html]
- [aider.chat/docs/usage/tips.html]
- [aider.chat/2024/05/22/swe-bench-lite.html]
- [aider.chat/2024/09/26/architect.html]
- [aider.chat/2024/07/01/sonnet-not-lazy.html]
- [aider.chat/2024/08/14/code-in-json.html]
- [aider.chat/2023/12/21/unified-diffs.html]
