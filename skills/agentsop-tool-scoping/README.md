# tool-scoping (enhancement overlay)

**T1 — Tool definition + per-agent binding (scoping discipline).**

An enhancement overlay for coder agents building tool-using, multi-agent systems.
It surfaces the per-agent tool-scoping rubric that the base `crewai` and
`langchain` skills only mention in passing: **which agent gets which tool, and why
blanket-sharing every tool to every agent is a correctness and blast-radius
risk.**

## The gap it fills

Role-based frameworks define tools and bind them, but treat scoping as a one-line
footnote ("assign tools to the agent that needs them"). Production failures —
wrong-tool selection, an agent running a destructive op outside its role, a
double-charge on retry — come from skipping the binding decision and defaulting to
"give everyone everything." This overlay makes the rubric first-class.

## Core mental model

> A tool is a **capability grant**, not a convenience. Scope by least-privilege:
> an agent should hold only the tools its role actually needs. Tool *definition*
> (write once, reuse) and tool *binding* (per-agent, minimal) are two separate
> decisions.

## What's inside `SKILL.md`

1. 何时激活 — multi-agent + tools; one agent with too many tools; tempted to share all.
2. 核心心智模型 — capability grant / least-privilege; definition ≠ binding.
3. SOP — inventory → role→minimal-set map → guard side-effects → count limit → audit.
4. 操作模型 — OP-1..OP-7 (least-privilege mapping, side-effect guarding,
   shared-vs-scoped, tool-count limit, zero-tool synthesis agents, audit, tighten-as-fix).
5. 困境决策案例 — shared registry vs per-agent; the 20-tool wrong-pick agent;
   sharing a destructive tool.
6. 反模式与边界 — blanket sharing, unguarded destructive tools, mega-agent.
7. 跨框架对照 — CrewAI `agent.tools`, LangGraph per-node `bind_tools`,
   OpenAI Assistants, Claude `tool_use`.

## Cross-links

- `[[crewai]]` — base multi-agent framework (role/goal/backstory, processes).
- `[[agentsop-http-tool-wrapping]]` — how to implement a tool's I/O safely.
- `[[agentsop-llm-tool-idempotency]]` — how to make a side-effectful tool safe to retry.

## Files

- `SKILL.md` — the overlay (sections above).
- `references/R1-source-evidence.md` — quoted evidence from source skills.
- `intermediate/operation_candidates.json` — extracted operation candidates.

## Status

`version: 0.1.0` — overlay type `enhancement`, enhances `crewai` / `langchain` /
`langgraph`.
