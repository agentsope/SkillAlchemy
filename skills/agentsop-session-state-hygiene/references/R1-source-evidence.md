# R1 — Source Evidence

Primary sources for the **session-state-hygiene** skill. Citations are grouped by claim.

---

## Claim 1 — "Context above ~25k tokens degrades model behaviour"

> "Above about 25k tokens of context, most models start to become distracted and become less likely to conform to their system prompt."

**Source**: `aider.chat/docs/troubleshooting/edit-errors.html`
**Used in**: Mental model §2, OP-005 trigger threshold, AP-001 fix cadence.

This is the load-bearing empirical claim. Aider's tooling (`/tokens`, `/clear`, `/drop`) is designed around this threshold. Other frameworks lack a published threshold but the heuristic transfers.

---

## Claim 2 — "Aider `/clear` resets chat history, preserves files"

**Source**: `aider.chat/docs/usage/commands.html`

```
/clear            清 chat 历史（保留文件）
/reset            丢文件 + 清历史
/drop <files>     从 chat 移除
/tokens           当前 token 占用
```

**Used in**: OP-005, cross-framework table §7.

Note the distinction: `/clear` keeps the `/add`-ed working set so the model still knows *what* it can edit; `/reset` starts from zero. This pair is the cleanest example of "partial clear" vs "fresh thread" across the surveyed tools.

---

## Claim 3 — "Claude Code `/clear` resets conversation history"

**Source**: `docs.anthropic.com/en/docs/claude-code/slash-commands`

The official slash-commands reference lists `/clear` as the conversation-reset action. The working directory and any files on disk are unaffected — Claude Code's "session state" is the in-memory transcript, not the filesystem.

**Used in**: OP-006, cross-framework table §7.

---

## Claim 4 — "CrewAI memory is opt-in; debug with memory=False"

**Source**: `docs.crewai.com/en/concepts/memory`
**Cross-reference**: `crewai-sop-skill/SKILL.md` DC-4

Key facts:
- Default `memory=False`. Setting `memory=True` enables short-term + entity memory, which **runs additional LLM calls** to summarise and recall.
- When memory is wrong (mis-recall, stale facts), traces become hard to read.
- Recommended SOP: *debug with `memory=False`*; only enable `memory=True` for genuine cross-kickoff persistence; for production, plug in Mem0 instead of the default LanceDB store.

**Used in**: OP-007, AP-005.

---

## Claim 5 — "LangGraph thread_id scopes durable state"

**Source**: `langchain-ai.github.io/langgraph/concepts/persistence/`
**Cross-reference**: `langgraph-sop-skill/SKILL.md` §2

A LangGraph thread is identified by `config={"configurable": {"thread_id": "..."}}`. Two different `thread_id`s = two completely separate conversations, even on the same compiled graph and same checkpointer. Reusing a `thread_id` resumes from the last checkpoint.

**Used in**: OP-008(a), cross-framework table §7. This is the cleanest "fresh thread" primitive in any framework — explicit, named, and durable.

---

## Claim 6 — "LangGraph supports surgical message-list edits"

**Source**: `langchain-ai.github.io/langgraph/how-tos/manage-conversation-history/`

`graph.update_state(config, {"messages": trimmed_list})` overwrites the `messages` key. Combined with `RemoveMessage` you can delete specific entries. This is the most fine-grained "partial clear" primitive across surveyed tools.

**Used in**: OP-004 (partial-clear), OP-008(b).

---

## Claim 7 — "Subgraph state is isolated unless keys overlap"

**Source**: `langchain-ai.github.io/langgraph/concepts/subgraphs/`
**Cross-reference**: `langgraph-sop-skill/SKILL.md` OP-6

A subgraph compiled separately and added as a node has its **own state schema**. Parent state and child state intersect only on shared keys. This is the architecture-level analogue of a `/clear`: structurally prevent context bleed by giving each logical unit its own state.

**Used in**: OP-008(c), Dilemma Case 2.

---

## Claim 8 — "Stale chat history causes 'SEARCH block not found' in Aider"

**Source**: `aider.chat/docs/troubleshooting/edit-errors.html`
**Cross-reference**: `aider-sop-skill/SKILL.md` §5 Case 3

Aider's documented remediation order for repeated edit-format failures explicitly includes `/clear` to reduce chat-history noise *before* swapping models or edit formats. This is the strongest published case for "session hygiene as a first-line debugging move."

**Used in**: Mental model §2, Dilemma Case 1.

---

## Claim 9 — Cross-framework universality of the SOP

All four surveyed code-tool frameworks expose a single command (or one explicit config knob) for resetting session state:

| Framework | Command | Scope |
|---|---|---|
| Aider | `/clear`, `/reset`, `/drop` | Chat history / file set |
| Claude Code | `/clear` | Conversation history |
| CrewAI | `memory=False`, re-instantiate Crew | In-memory + persistent stores |
| LangGraph | New `thread_id`, `update_state` | Thread / specific keys |
| ChatGPT / Gemini web | "New chat" | Whole conversation |

The fact that every framework converges on a one-command primitive is the strongest signal that this SOP belongs surfaced as a skill, not buried inside each framework's docs.

---

## Cross-references within the local skill workspace

- `aider-sop-skill/SKILL.md` — §6 "Context hygiene" table; §5 Case 3 cites `/clear` as a debugging move.
- `crewai-sop-skill/SKILL.md` — DC-4 `Memory 默认关 vs 全开`; OP-5 "启用 Memory" guidance; AP-1 ("agent 数量爆炸") implicates state bloat as a failure mode.
- `langgraph-sop-skill/SKILL.md` — OP-6 subgraph isolation; OP-10 time-travel debug uses checkpoint history to fork cleanly; §1 §2 establish `thread_id` as the unit of session identity.

These three SOPs all point at the same underlying discipline. This skill surfaces it.
