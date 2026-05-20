# R1: Aider Architecture & Mental Model

## Core insight

Aider is **a REPL loop wrapped around four primitives**: a git working tree, a tree-sitter repo-map, a chosen edit format, and a human (or agent) at the prompt. Every other feature is plumbing for these four. Understand them and you understand Aider.

```
+--------------------------------------------------------------+
|  Terminal REPL  (the human/agent is in the loop)            |
|                                                              |
|   prompt  --->  LLM(system + repo-map + chat + files)        |
|                       |                                      |
|                       v                                      |
|                   edit format (diff / udiff / whole / patch) |
|                       |                                      |
|                       v                                      |
|                   apply to working tree                      |
|                       |                                      |
|                       v                                      |
|                   git auto-commit (per turn)                 |
+--------------------------------------------------------------+
```

## The four primitives

### 1. The git-native working tree

> "Whenever aider edits a file, it commits those changes with a descriptive commit message. This makes it easy to undo or review aider's changes." [aider.chat/docs/git.html]

- One LLM turn -> one (or a few) commits. Granularity matches conversational granularity.
- Pre-existing dirty files are committed **first** with a separate message — "this keeps your edits separate from aider's edits, and makes sure you never lose your work." [aider.chat/docs/git.html]
- `/undo` reverts the most recent aider commit. `git log` is the audit trail. `git branch` is the experiment isolation.
- Auto-commit can be disabled (`--no-auto-commits`, `--no-dirty-commits`, `--no-git`) but disabling it forfeits the safety story.

**Why git-native (not snapshots / not a custom undo stack):** developers already trust git. Reusing it gives Aider durable history, free branching, free diffing tools, and free integration with code review without inventing new abstractions.

### 2. The repo-map (tree-sitter, not embeddings)

> "A concise map of your whole git repository that includes the most important classes and functions along with their types and call signatures." [aider.chat/docs/repomap.html]

Three deliberate design choices:

| Choice | Alternative rejected | Reason |
|---|---|---|
| Tree-sitter symbol extraction | Raw file dump | Token-efficient, scales to large repos |
| PageRank-style graph over symbols | Vector embeddings (RAG) | Interpretable, deterministic, no embedding index to maintain, LLM sees real signatures |
| Dynamic budget based on chat state | Fixed slice | Expands when no files are added; shrinks when files cover the territory |

> "Aider successfully identified the correct file to edit in **70.3%** of the benchmark tasks." [aider.chat/2024/05/22/swe-bench-lite.html]

The repo-map is *not* a retriever — it is a **navigation aid handed to the LLM** so it can ask for the right files. The LLM is "free to ask to see these specific files." [aider.chat/docs/repomap.html]

**Why not embeddings?**
- Embeddings give the model opaque vectors; the LLM cannot reason over a vector. The repo-map gives it real signatures.
- No index to build, refresh, or invalidate when code changes.
- Deterministic & inspectable via `/map`.

### 3. The edit format (the wire protocol between LLM and disk)

> "Aider is configured to use the optimal format for most popular, common models." [aider.chat/docs/more/edit-formats.html]

Formats, ordered from cheapest to most reliable:

| Format | Wire format | Strengths | Weaknesses | Default for |
|---|---|---|---|---|
| `whole` | Full file content | Most reliable parsing, no merge errors | Expensive on large files; output-token-limited | Weak models, GPT-3.5 |
| `diff` | SEARCH/REPLACE blocks (merge-conflict style) | Token-efficient, surgical | Search block must match exactly | GPT-4o, Sonnet, most strong models |
| `diff-fenced` | Same but path inside the fence | Helps models that confuse fence/path order | Niche | Gemini family |
| `udiff` | Simplified unified diff (no line numbers) | "Encourages rigor, making GPT less likely to leave informal editing instructions in comments or be lazy" [aider.chat/2023/12/21/unified-diffs.html] | Heavier prompting | GPT-4 Turbo (1106) |
| `patch` | OpenAI patch protocol | Robust multi-action per file | Model-specific | GPT-4.1 [HISTORY v0.82.0] |
| `editor-diff` / `editor-whole` | Same as above but "intended to be used with `--editor-edit-format` when using architect mode" [aider.chat/docs/more/edit-formats.html] | Tight prompt, edit-only | Only sensible in architect mode | Editor sub-model |

> "JSON-wrapping may distract or challenge models in a way that reduces their ability to reason about solving coding problems." [aider.chat/2024/08/14/code-in-json.html]

Implication: **never wrap code in JSON tool-calls if you can avoid it.** Aider's hard-won lesson is that plain-text diff formats outperform structured JSON for code editing — across every model tested.

### 4. The REPL loop (human/agent in control)

Aider is intentionally **not** an autonomous agent. The blog post on SWE-Bench Lite explicitly called this out:

> "Aider's interactive approach outperforming complex agentic systems… the pragmatic, user-controlled design was unexpectedly effective without specialized tools, web access, or code execution capabilities during reasoning." [aider.chat/2024/05/22/swe-bench-lite.html]

The REPL gives you tight, human-paced cycles: `/ask` (read-only think), `/code` (edit), `/architect` (think with one model, edit with another), `/run` (feed shell output back), `/test` (feed failing tests back), `/undo` (rollback). Every command keeps a human in the steering position.

## Mental model an agent-coder should hold

1. **Think of the repo as the source of truth, not the chat.** Files + git history persist; chat is ephemeral.
2. **The LLM sees three layers of context**, in priority order:
   - System prompt + edit-format instructions (fixed).
   - Read-only context: repo-map + `/read` files + CONVENTIONS.md.
   - Read-write context: files added via `/add` (these are the **only** files the LLM is allowed to edit).
3. **Every edit is a commit.** Branch before risky changes; `/undo` for one-step rollback; `git reset` for deeper.
4. **Edit format is a model-fit problem, not a user preference.** Pick what your model can produce reliably; Aider already chose a default — only override if you see edit errors.
5. **Repo-map is a budget.** It expands when no files are added (so the LLM can navigate) and shrinks when you `/add` the right files (so context goes to the real code).

## References

- [aider.chat/docs/repomap.html]
- [aider.chat/docs/more/edit-formats.html]
- [aider.chat/docs/git.html]
- [aider.chat/2023/12/21/unified-diffs.html]
- [aider.chat/2024/05/22/swe-bench-lite.html]
- [aider.chat/2024/08/14/code-in-json.html]
- [aider.chat/HISTORY.html]
