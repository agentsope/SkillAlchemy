# streaming-output

A Phase-D **enhancement-overlay** coder-agent skill: **T7 — streaming the output
of long-running LLM/agent runs from the backend**, not just animating text in the
UI.

> One line: stream *what the user needs to see* — final tokens for chat,
> intermediate updates for agents, custom events for progress — over the right
> transport, and decide up front what happens when the client disconnects.

## What this is

The `langchain` and `langgraph` skills mention stream modes (`values` / `updates`
/ `messages` / `custom`) but stop at "you can stream." They don't surface the
backend SOP: *which* projection each surface needs, how to mix token + step +
progress streams on **one** demuxable wire, which transport (SSE vs WebSocket) to
pick, and — the part everyone skips — what to do when the client vanishes
mid-stream (cancel the run, or detach and persist for replay).

This overlay names that SOP and maps it across LangGraph stream modes, LangChain
`astream_events`, OpenAI streaming, and Anthropic streaming. It cross-links
`[[agentsop-langgraph]]` (OP-8, checkpointer for durability) for the orchestration it
sits on top of.

## When to activate

- A run is **long** (multi-second to multi-minute) and a human is **waiting** —
  perceived latency is the metric.
- You're asked to "stream the response", "show progress", "show which tool the
  agent is running", or "show the reasoning".
- You must pick a transport (SSE / WebSocket / async generator) and a
  disconnect policy.

Do **not** activate for sub-second calls, offline batch jobs, or pure CSS
typing-animation questions.

## The SOP, in six steps

1. **Confirm** streaming is warranted (human waiting on a >1–2s run).
2. **Classify** the surface → pick the projection(s): tokens / steps / progress.
3. **Pick transport**: SSE (receive-only default) / WebSocket (bidirectional) /
   async generator (internal).
4. **Mix** modes on one wire — tagged `(mode, chunk)` tuples → named SSE events.
5. **Decide disconnect policy** — cancel (cheap/stateless) vs detach+persist
   (side-effecting/resumable) — *before* shipping.
6. **Harden** — heartbeat, backpressure, disable proxy buffering.

## Files

- `SKILL.md` — the skill. 7 sections: 何时激活 / 核心心智模型 / SOP / 操作模型
  (OP-1..OP-8) / 困境决策案例 (2 cases) / 反模式与边界 / 跨框架对照.
- `references/R1-source-evidence.md` — primary sources grouped by claim, with full
  URLs for the inline `[tag]` citations.
- `intermediate/operation_candidates.json` — machine-readable operations and
  anti-patterns the SKILL.md was distilled from.

## Cross-framework cheat sheet

| Need | LangGraph | LangChain | OpenAI | Anthropic |
|---|---|---|---|---|
| Final tokens | `stream_mode="messages"` | `astream_events`→`on_chat_model_stream` | `stream=True` deltas | `messages.stream`→`text_stream` |
| Step updates | `stream_mode="updates"` | `astream_events` `on_tool_*` | tool-call deltas (manual) | content-block events (manual) |
| Full state | `stream_mode="values"` | rebuild from events | n/a | n/a |
| Custom progress | `"custom"` + `get_stream_writer()` | dispatch custom event | out-of-band | out-of-band |
| Mix modes | list → tagged tuples | one typed event stream | one delta stream | one event stream |

Transport is orthogonal: SSE (default) / WebSocket (bidirectional) / async
generator (internal) wraps any SDK. Full evidence in `references/R1`.

## Provenance

Distilled from the local sibling SOP `langgraph-sop` (stream modes,
checkpointer-for-durability) plus vendor docs for LangChain `astream_events`,
OpenAI streaming, Anthropic streaming, and MDN Server-Sent Events. Every
framework-specific claim is cited inline and resolved in `references/R1`.
