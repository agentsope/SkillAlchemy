# R1 — Source Evidence

Primary sources for the **streaming-output** enhancement-overlay skill. Citations
are grouped by claim. Short tags resolve to the URLs below.

---

## Claim 1 — "LangGraph exposes five stream modes: values / updates / messages / custom / debug"

> `values` — full state after each step. `updates` — only the state diffs each
> node produces. `messages` — LLM tokens + metadata, token-by-token. `custom` —
> arbitrary data emitted from inside a node via the stream writer. `debug` — the
> raw firehose.

**Tag**: `[lg/stream]`
**Source**: `https://langchain-ai.github.io/langgraph/how-tos/streaming/` and the
streaming concept page `https://langchain-ai.github.io/langgraph/concepts/streaming/`
**Local cross-ref**: `[[agentsop-langgraph]]` SKILL.md OP-8 ("Stream tokens to the UI
without sacrificing graph observability") and its citation `[lc-docs/streaming]`
(`https://docs.langchain.com/oss/python/langgraph/*`).

**Used in**: Mental model §1–3, Step 2 table, OP-1/2/3/4/8, Case 1, every
cross-framework row.

Load-bearing sub-claims:
- **Modes are composable**: pass a list, e.g. `stream_mode=["messages","updates",
  "custom"]`, and each yielded item is a `(mode, chunk)` tuple — the demux key.
- **`messages` chunks carry metadata** (`langgraph_node`, tags) → enables filtering
  the final-answer LLM from sub-agent LLMs (OP-8).
- **`custom` requires emitting**: `from langgraph.config import get_stream_writer;
  w = get_stream_writer(); w({...})` inside a node (OP-3).
- **`values` is heavy, `updates` is light**: values = full snapshot (good for
  resume), updates = diff (good for live UI).

---

## Claim 2 — "LangChain LCEL streams a typed event taxonomy via astream_events"

> `astream_events(..., version="v2")` yields events like `on_chat_model_stream`
> (token), `on_tool_start` / `on_tool_end`, `on_chain_start` / `on_chain_end`,
> each tagged with run metadata.

**Tag**: `[lc/astream-events]`
**Source**: LangChain docs — Streaming / "How to stream runnables" and the
`astream_events` reference:
`https://python.langchain.com/docs/how_to/streaming/` ,
`https://python.langchain.com/docs/how_to/streaming/#using-stream-events`

**Used in**: Mental model §2–3, Step 2 table, OP-2/3, cross-framework table.

This is the richest *typed* event stream of the four frameworks — one stream,
branch on `event["event"]`. Use when you need fine-grained lifecycle routing
without committing to a full graph.

---

## Claim 3 — "OpenAI streams token deltas with stream=True and supports cancellation"

> With `stream=True` the API returns an iterator of chunks; each
> `chunk.choices[0].delta` carries incremental `content` (and `tool_calls` deltas).
> Closing the stream / aborting the request stops generation server-side.

**Tag**: `[oai/stream]`
**Source**: OpenAI API reference — Streaming:
`https://platform.openai.com/docs/api-reference/streaming` and the streaming guide
`https://platform.openai.com/docs/guides/streaming-responses`

**Used in**: Mental model §1, Step 5 (cancel on disconnect), OP-1/2/6,
cross-framework table, anti-pattern "skip disconnect handling".

Key sub-claim: **steps are not first-class** — to show "which tool", you
reconstruct from `tool_calls` deltas yourself. Cancellation is how you stop
burning tokens when the client disconnects (OP-6, Case 2 stateless branch).

---

## Claim 4 — "Anthropic streams via client.messages.stream with text_stream and content-block events"

> `with client.messages.stream(...) as stream: for text in stream.text_stream:`
> yields incremental text; lower-level `content_block_start` /
> `content_block_delta` / `content_block_stop` events expose tool-use blocks.

**Tag**: `[anthropic/stream]`
**Source**: Anthropic API docs — Streaming Messages:
`https://docs.anthropic.com/en/api/messages-streaming` and the SDK streaming helper
docs.

**Used in**: Mental model §1, OP-1, cross-framework table.

Sub-claim: like OpenAI, **steps are derived** — tool use surfaces as content-block
events, not a separate "updates" stream.

---

## Claim 5 — "Server-Sent Events: server→client only, named events, auto-reconnect, Last-Event-ID, comment heartbeats"

> `EventSource` opens a long-lived `text/event-stream` HTTP response. The server
> can emit named events (`event: token\n data: ...\n\n`). The browser
> auto-reconnects on drop and sends `Last-Event-ID` so the server can resume.
> Lines starting with `:` are comments (used as keep-alive pings).

**Tag**: `[mdn/sse]`
**Source**: MDN — Using server-sent events:
`https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events`
and the `EventSource` reference
`https://developer.mozilla.org/en-US/docs/Web/API/EventSource`

**Used in**: Mental model §2 (stream-as-vanishing-contract), Step 3 (transport),
Step 4 (named events = demux), Step 5/6 (Last-Event-ID replay, heartbeat),
OP-4/5/6/7, both anti-patterns about transport, Case 1 & 2.

Sub-claims used:
- **SSE is receive-only** → if the client must push mid-stream, use WebSocket
  (Step 3, OP-5).
- **Named `event:` field** is exactly the multiplex key for mixing token/step/
  progress on one connection (Step 4, OP-4).
- **`Last-Event-ID`** + monotonic event IDs = resumable reconnect (Step 5 detach
  branch, OP-6, Case 2).
- **Comment lines** (`: ping\n\n`) keep proxies from dropping idle connections
  (Step 6, OP-7).

---

## Claim 6 — "Durability/resume requires a checkpointer (overlay dependency)"

> Detaching a run from a disconnected client so it can be resumed/replayed
> requires the run's state to be persisted after each step.

**Tag**: `[[agentsop-langgraph]]` (local sibling skill)
**Source**: `/Users/5imp1ex/Desktop/Skill-Workplace/output/langgraph-sop-skill/SKILL.md`
Step 6 (checkpointer selection: InMemory / Sqlite / Postgres / Redis) and OP-7
(durable Postgres checkpointing); HITL side-effect ordering in Case 4.

**Used in**: Step 5 (detach + persist branch), OP-6, Case 2.

This overlay deliberately does **not** re-derive checkpointer selection — it defers
to `[[agentsop-langgraph]]`. The streaming skill's contribution is the *disconnect
policy decision* (cancel vs detach) that determines *whether* you need the
checkpointer at all for a given surface.

---

## Source posture notes

- LangGraph stream-mode behavior is the spine; it is the only framework that gives
  token + step + custom as cleanly separable, composable projections on one wire.
- LangChain `astream_events` is the richest typed taxonomy but a different shape
  (one event stream, not N tagged streams).
- OpenAI / Anthropic give a single delta/event stream; "steps" are reconstructed.
- MDN SSE is the transport authority and supplies the disconnect/reconnect/
  heartbeat primitives that the SDKs themselves do not define.
