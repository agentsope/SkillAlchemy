# session-state-hygiene

A Phase-D, common-tier, daily-frequency coder-agent skill: **when to `/clear`,
when to keep context, and how to detect "context bleed."**

> One line: context is signal; stale context is noise; clearing restores signal.

## What this is

A multi-turn AI coding session is a sliding window of evidence. Early on it's
pure signal; the longer it runs, the more dead ends, abandoned plans, and
superseded files accumulate — until yesterday's good context becomes today's bad
bias ("context bleed"). This skill is the discipline of noticing that moment and
acting with the smallest correct cut.

Aider (`/clear`), Claude Code (`/clear`), CrewAI (`memory=False`, re-instantiate)
and LangGraph (new `thread_id`, subgraph isolation) each encode this discipline
separately. None names it as a skill. This one does, and maps the single move
onto every tool's command.

## When to activate

- **Topic shift** inside a session (finished A, starting unrelated B).
- **Length warning** — window N% full, or Aider `/tokens` past ~25k (the
  observed point where models start ignoring their system prompt).
- **Weird behavior** — model repeats a corrected mistake, cites a removed
  file/decision, or obeys an older instruction over the newest one.

Do **not** activate for a single call, a one-shot RAG query, or a clean
on-topic window — hygiene on clean context is superstition.

## The SOP, in four steps

1. **Recognize** — name the symptom in one line before touching anything.
2. **Save what's worth** — externalize keepers (commit code, write the plan to a
   note) so they survive the clear.
3. **Clear** — the smallest correct cut: drop one item / trim history / clear
   history / fresh session.
4. **Restart focused** — open the clean window with a one-paragraph summary, not
   the old transcript.

## Files

- `SKILL.md` — the skill. 7 sections: 何时激活 / 核心心智模型 / SOP / 操作模型
  (OP-001..OP-009) / 困境决策案例 (3 cases) / 反模式与边界 / 跨框架对照.
- `references/R1-source-evidence.md` — primary sources, grouped by claim, with
  full URLs for the inline `[tool/topic]` citation tags.
- `references/R2-tool-commands.md` — copy-pastable clear/reset commands for
  Aider, Claude Code, CrewAI, LangGraph, web UIs, and raw SDK loops.
- `intermediate/operation_candidates.json` — machine-readable operations and
  anti-patterns the SKILL.md was distilled from.

## Cross-framework cheat sheet

| Need | Aider | Claude Code | CrewAI | LangGraph |
|---|---|---|---|---|
| Inspect size | `/tokens` | `/context` | trace | `len(state["messages"])` |
| Clear, keep files | `/clear` | `/clear` | re-instantiate `Crew()` | new `thread_id` |
| Hard reset | `/reset` | exit CLI | new process + wipe store | new `thread_id` |
| Partial clear | `/drop <files>` | n/a | trim `context=[...]` | `update_state({"messages":...})` |
| Isolate sub-task | 2nd window | sub-process | separate `Crew`, `memory=False` | subgraph |

Full commands in `references/R2-tool-commands.md`.

## Provenance

Distilled from three local sibling SOPs — `aider-sop`, `crewai-sop`,
`langgraph-sop` — plus vendor docs. Every framework-specific claim is cited
inline and resolved in `references/R1`.
