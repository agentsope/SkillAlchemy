---
name: agentsop-streaming-output
description: |
  Enhancement-overlay decision protocol for STREAMING the output of long-running
  LLM / agent runs from the *backend*, not just wiring a typing animation in the
  UI. Activates when a coder agent must stream final tokens to a chat client,
  surface intermediate agent steps (which tool, which node, partial reasoning),
  emit custom tool-progress events, choose a transport (SSE vs WebSocket), or
  decide what to do when the client disconnects mid-stream. The langchain /
  langgraph skills mention stream modes but stop at "you can stream"; this skill
  encodes *what to stream, over what transport, and how to fail safely*.
version: 0.1.0
---

# Streaming Tool/Agent Output · SOP (Enhancement Overlay)

> Source posture: every non-trivial claim is cited inline. Short tags like
> `[lg/stream]`, `[lc/astream-events]`, `[oai/stream]`, `[anthropic/stream]`,
> `[mdn/sse]` resolve against `references/R1-source-evidence.md`.
>
> This is an **ENHANCE overlay**: it sits on top of `[[agentsop-langgraph]]` (which
> names the four stream modes but treats streaming as one of ten operations) and
> `[[langchain]]`. Read those for the orchestration; read this for the
> streaming SOP. Cross-link: `[[agentsop-langgraph]]` OP-8.

---

## 何时激活 (Activation Rules)

Activate when **any** of these fire:

- The run is **long** (multi-second to multi-minute agent loop, RAG over many
  docs, multi-tool chain) and the user is **waiting** — perceived latency, not
  total latency, is the product metric.
- The user asks to "stream the response", "show a typing effect", "show progress",
  "show which tool the agent is running", or "show the chain of thought".
- You are building a **chat** surface (stream final tokens) OR an **agent** surface
  (stream intermediate steps: node entered, tool called, partial state) OR a
  **long task** surface (stream custom progress like "embedded 40/200 docs").
- You must pick a **transport**: Server-Sent Events (SSE) vs WebSocket vs plain
  chunked HTTP, and handle **client disconnect** / cancellation cleanly.
- You're wiring `graph.stream(...)` / `astream_events` / OpenAI `stream=True` /
  Anthropic `client.messages.stream` and need to know *which mode* and *what to
  forward to the client*.

Do **not** activate for: a single fast (<1s) completion, a batch/offline job with
no waiting human, or a pure front-end animation question (that's CSS, not a backend
SOP). Streaming a 300ms call adds protocol overhead for zero UX gain — see
*反模式*.

---

## 核心心智模型 (Core Mental Model)

**Stream what the user needs to *see*, not everything the engine *emits*.** A
backend stream is a curated projection of the run's internal event firehose onto
exactly three audiences:

1. **Chat audience → final tokens.** A human reading prose wants character-by-
   character output of the *final* assistant message. In LangGraph this is
   `stream_mode="messages"` (LLM tokens + metadata); in raw SDKs it's
   `stream=True` / `.messages.stream` `[lg/stream]` `[oai/stream]`
   `[anthropic/stream]`. They do **not** want to see tool JSON or scratch nodes.

2. **Agent audience → intermediate updates.** A developer (or a power-user UI)
   watching an agent work wants "entered node `planner`", "calling tool
   `search`", "got 5 results" — the state diffs *between* steps. LangGraph:
   `stream_mode="updates"` (per-node diffs) `[lg/stream]`. LangChain LCEL:
   `astream_events` (a typed event stream: `on_chat_model_stream`,
   `on_tool_start`, `on_tool_end`) `[lc/astream-events]`.

3. **Progress audience → custom events.** Work happening *inside* one tool/node
   (a loop, a long embed, a download) is invisible to the framework's automatic
   events. You must **emit** progress yourself: LangGraph `stream_mode="custom"`
   via `get_stream_writer()` `[lg/stream]`; LCEL via custom callback / dispatched
   events `[lc/astream-events]`.

The load-bearing insight from the LangGraph docs: **stream modes are composable —
pass a list** (`stream_mode=["messages","updates","custom"]`) and demultiplex on
the client by the tuple tag `[lg/stream]`. So the real design question is never
"can I stream" but **"which projection(s) does this surface need, and how do I tag
them on one wire?"**

Second axiom: **a stream is a contract with a client that can vanish.** Networks
drop, users close tabs, browsers cap connections. The backend must decide, *up
front*, whether a disconnect should **cancel** the run (stop burning tokens) or
**detach** and let it finish (so a reconnect can replay). That decision is part of
the design, not an afterthought — see *困境 Case 2*.

---

## SOP 工作流 (Agentic Protocol)

Walk top-down. Each step has a gate.

### Step 1 · Confirm streaming is warranted
Gate: is a human **waiting** on a run that takes **>~1–2s**? If no (batch job, sub-
second call), **don't stream** — return the whole payload. Streaming a fast call
adds SSE/WebSocket framing, reconnect logic, and partial-parse bugs for no UX win
`[mdn/sse]`. Exit here for fast paths.

### Step 2 · Classify the surface → pick the projection
Map the surface to one (or more) of the three audiences:

| Surface | Primary projection | LangGraph mode | LangChain |
|---|---|---|---|
| Chat / prose | final tokens | `messages` | `astream_events` → `on_chat_model_stream` |
| Agent inspector / dev UI | step updates | `updates` | `astream_events` (`on_tool_*`, `on_chain_*`) |
| Full-state replay / resume | snapshots | `values` | n/a (rebuild from events) |
| Long in-tool work | custom progress | `custom` | dispatched custom events |
| Debug everything | raw firehose | `debug` | `astream_events` (all) |

`values` emits the **full state** after each step (heavy, good for resume);
`updates` emits only the **diff** (light, good for live UI) `[lg/stream]`. Default
a chat agent to `["messages","updates"]` and add `"custom"` only when a tool has
internal progress worth surfacing `[lg/stream]` (= `[[agentsop-langgraph]]` OP-8).

### Step 3 · Pick the transport
Gate questions: does the client only *receive* (server→client), or also need to
*send* mid-stream (interrupt, steer)?

- **Receive-only → SSE.** Simplest correct default: one long-lived HTTP response,
  `text/event-stream`, auto-reconnect + `Last-Event-ID` built into the browser
  `EventSource` `[mdn/sse]`. This is what most "stream the agent" use cases need.
- **Bidirectional → WebSocket.** Only when the client must push during the stream
  (live cancel, mid-run user input, collaborative). Costs you reconnect logic you
  get free with SSE.
- **Server-internal / non-browser → async generator / gRPC stream.** If both ends
  are yours, skip HTTP framing and yield the tuples directly.

### Step 4 · Mix token + step streams on one wire
Use the **multi-mode** form so one connection carries everything; tag each chunk
so the client routes it:
```python
async for mode, chunk in graph.astream(
        inp, stream_mode=["messages", "updates", "custom"], config=cfg):
    if mode == "messages":
        token, meta = chunk
        yield sse("token", token.content)            # → append to bubble
    elif mode == "updates":
        yield sse("step", chunk)                      # → "running tool X"
    elif mode == "custom":
        yield sse("progress", chunk)                  # → progress bar
```
`[lg/stream]`. SSE `event:` field is exactly the demux key; the browser's
`EventSource.addEventListener("token"|"step"|"progress", …)` splits it client-side
`[mdn/sse]`. Never interleave two semantic streams on one untagged channel — the
client can't tell a token from a tool name.

### Step 5 · Decide disconnect policy *before* shipping
For each surface answer: on client disconnect, **cancel** or **detach**?
- **Cancel** (stop the run) when: every step costs money/tokens, output is useless
  without the client, no resume planned. Wire it to the request's cancellation
  signal so the generator is closed and the LLM call aborted `[oai/stream]`.
- **Detach + persist** when: the run has side effects that must complete, OR the
  user may reconnect and wants the result. Pair with a checkpointer
  (`[[agentsop-langgraph]]` Step 6) and a resumable event log so reconnect replays via
  `Last-Event-ID` `[mdn/sse]`.
Default for a chat agent: **cancel** (cheap, stateless). Default for a long
side-effecting pipeline: **detach + persist**.

### Step 6 · Add backpressure + heartbeat before production
- **Heartbeat**: SSE connections die silently behind proxies; emit a comment ping
  (`: keep-alive\n\n`) every ~15s during long quiet stretches `[mdn/sse]`.
- **Backpressure**: if the client reads slower than the model emits, your buffer
  grows. Bound the queue; on overflow either drop intermediate `updates` (keep
  `messages`) or apply flow control. Tokens are the audience-critical stream;
  progress events are droppable.
- **Flush**: disable response buffering (`X-Accel-Buffering: no` for nginx) or the
  proxy batches your tokens and kills the "streaming" feel.

---

## 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**.

### OP-1 · Stream final tokens to a chat client (the 80% case)
- **Trigger**: User-facing chat; want typing effect on the final answer.
- **Action**: LangGraph `graph.astream(inp, stream_mode="messages")` → yield each
  `(token, metadata)`'s `token.content`; filter by `metadata` so you only stream
  the *final* node's LLM, not sub-agent chatter. Raw: OpenAI `stream=True` iterate
  `chunk.choices[0].delta.content`; Anthropic `with client.messages.stream(...) as
  s: for t in s.text_stream`.
- **Output**: Character-by-character final answer; no tool JSON leaks.
- **Evidence**: `[lg/stream]` messages mode; `[oai/stream]`; `[anthropic/stream]`.

### OP-2 · Stream intermediate agent steps
- **Trigger**: Dev/inspector UI; show "which node / which tool, with inputs".
- **Action**: LangGraph `stream_mode="updates"` → each chunk is `{node_name:
  state_diff}`; render as a step log. LCEL: `astream_events(version="v2")` and
  switch on `event["event"]` (`on_tool_start`/`on_tool_end`/`on_chain_*`).
- **Output**: Live step trace without the full state weight of `values`.
- **Evidence**: `[lg/stream]` updates mode; `[lc/astream-events]`.

### OP-3 · Emit custom in-tool progress
- **Trigger**: A tool/node does long internal work (embed 200 docs, paginate an
  API) the framework can't see.
- **Action**: LangGraph — inside the node, `w = get_stream_writer(); w({"progress":
  i/n})`; consume on `stream_mode="custom"`. LCEL — dispatch a custom event /
  callback that `astream_events` surfaces.
- **Output**: A real progress signal instead of a frozen spinner.
- **Evidence**: `[lg/stream]` custom mode + stream writer.

### OP-4 · Multiplex modes on one SSE connection
- **Trigger**: One surface needs tokens *and* steps *and* progress.
- **Action**: `stream_mode=["messages","updates","custom"]`; map each `(mode,
  chunk)` tuple to a distinct SSE `event:` name; client `addEventListener` per
  name (Step 4 snippet).
- **Output**: Single connection, cleanly demuxed; no extra round-trips.
- **Evidence**: `[lg/stream]` (list form returns `(mode, chunk)` tuples);
  `[mdn/sse]` (named events).

### OP-5 · Choose SSE vs WebSocket
- **Trigger**: Deciding the transport.
- **Action**: Receive-only (browser just displays) → **SSE** (free reconnect +
  `Last-Event-ID`). Client must push mid-stream (cancel, steer, collaborate) →
  **WebSocket**. Both ends yours / non-HTTP → async generator.
- **Output**: Right transport; no hand-rolled reconnect for the common case.
- **Evidence**: `[mdn/sse]` (EventSource auto-reconnect, server-push only).

### OP-6 · Handle client disconnect (cancel vs detach)
- **Trigger**: Stream may outlive the client's interest.
- **Action**: Hook the request cancellation token. **Cancel**: close the async
  generator → upstream LLM/agent call aborts; release resources `[oai/stream]`.
  **Detach**: keep running under a checkpointer, log events with monotonic IDs so a
  reconnect replays from `Last-Event-ID`.
- **Output**: No zombie runs burning tokens; or a resumable run, by design.
- **Evidence**: `[oai/stream]` cancellation; `[mdn/sse]` `Last-Event-ID`;
  `[[agentsop-langgraph]]` Step 6 (checkpointer for durability).

### OP-7 · Keep the connection alive (heartbeat + flush)
- **Trigger**: Long quiet gaps (a slow tool) cause proxies to drop the stream, or
  tokens arrive in clumps not smoothly.
- **Action**: Emit `: ping\n\n` comments every ~15s; set `X-Accel-Buffering: no` /
  disable proxy buffering; flush after each event.
- **Output**: Connection survives idle periods; tokens render smoothly.
- **Evidence**: `[mdn/sse]` (comment lines ignored by client, keep socket warm).

### OP-8 · Filter the firehose to the final answer only
- **Trigger**: A multi-agent graph streams *every* LLM's tokens; the chat bubble
  fills with sub-agent noise.
- **Action**: On `messages` mode, inspect `metadata` (`langgraph_node`, tags) and
  forward only tokens whose node is the user-facing responder; route the rest to
  `updates` (dev view) or drop.
- **Output**: Clean final answer; sub-agent reasoning stays in the inspector.
- **Evidence**: `[lg/stream]` (messages chunks carry node metadata for filtering).

---

## 困境决策案例 (Dilemma Cases)

### Case 1 · "Stream the tokens, or stream the steps?" — an agent that thinks then answers
- **困境**: A research agent runs 4 tools over ~40s, then writes a 2-paragraph
  answer. If you stream `messages` only, the user stares at a frozen spinner for
  40s, then sees text. If you stream `updates` only, they see "calling tool X" but
  the final answer dumps all at once, losing the typing feel.
- **约束**: One SSE connection (mobile client). The 40s of tool work is the scary
  part for the user; the final prose is the payoff.
- **决策步骤**:
  1. Reject "pick one mode" — the surface has **two** audiences in one timeline
     (progress during work, prose at the end) `[lg/stream]`.
  2. Use `stream_mode=["updates","messages"]`. During tool work, `updates` chunks
     drive a live step list ("Searching… Reading 5 docs… Synthesizing"). When the
     final responder node starts emitting, `messages` tokens stream into the
     bubble (OP-4 demux).
  3. Filter `messages` to the final node only (OP-8) so the tool-call LLMs don't
     leak into the answer.
  4. If a tool itself is slow (>5s), add `custom` progress from inside it (OP-3)
     so the step list isn't itself frozen.
- **结果**: Continuous feedback for the whole 40s, then a smooth typed answer — on
  one connection, no extra round-trips.
- **可提取的操作**: OP-4 + OP-8. **The answer to "tokens or steps" is almost always
  "both, tagged, on one wire" — the question is which is primary *when*.**

### Case 2 · "Client disconnects mid-stream — cancel the run or let it finish?"
- **困境**: A user kicks off a 90s agent that books a flight (real side effect),
  then closes the tab at second 30. The stream's consumer is gone. Do you kill the
  run (and maybe leave a half-booking) or let it complete (burning tokens for a
  client that may never return)?
- **约束**: The booking step is irreversible; tokens cost money; the user *might*
  reopen the tab.
- **决策步骤**:
  1. Recognize this is the **cancel-vs-detach** decision (Step 5), and it differs
     by *where in the run* the disconnect happens.
  2. Because there's an irreversible side effect, **do not hard-cancel mid-action**
     — that's the half-booking risk. Detach: let the current durable step finish
     under a checkpointer (`[[agentsop-langgraph]]` Step 6 / HITL ordering — side
     effects in their own committed step).
  3. Persist the event log with monotonic IDs. On reconnect, replay from
     `Last-Event-ID` so the user sees the outcome `[mdn/sse]`.
  4. If, instead, this were a *read-only* chat with no side effects, do the
     opposite: cancel immediately on disconnect to stop burning tokens
     `[oai/stream]` — that's the cheaper, correct default for chat.
- **结果**: Side-effecting runs detach + persist + replay; stateless chat runs
  cancel. The policy is chosen by *reversibility and cost*, not by reflex.
- **可提取的操作**: OP-6. **Disconnect policy is a function of side-effect
  reversibility and per-step cost — decide it per surface, before shipping, never
  let it default to "whatever the framework does on socket close".**

---

## 反模式与边界 (Anti-patterns & Boundaries)

- **Don't stream everything.** Forwarding the raw `debug`/`values` firehose to a
  chat UI floods the client with full-state snapshots and sub-agent tokens. Project
  to the audience (Step 2); `values` is heavy by design `[lg/stream]`.
- **Don't stream a sub-second call.** SSE/WebSocket framing + reconnect + partial-
  parse bugs for zero perceived-latency gain. Return the whole payload `[mdn/sse]`.
- **Don't skip disconnect handling.** A stream with no cancel/detach policy leaks
  zombie runs that burn tokens after the client is gone, or half-completes side
  effects. Decide in Step 5 `[oai/stream]`.
- **Don't interleave semantic streams on one untagged channel.** Tokens and tool
  names on the same unnamed wire are unparseable client-side. Tag with SSE `event:`
  / the `(mode, chunk)` tuple (OP-4) `[lg/stream]` `[mdn/sse]`.
- **Don't leak sub-agent tokens into the final answer.** Filter `messages` by node
  metadata (OP-8) `[lg/stream]`.
- **Don't forget the heartbeat.** Long quiet gaps behind a proxy silently kill the
  connection; the user sees a hang, not an error. Ping every ~15s `[mdn/sse]`.
- **Don't assume buffering is off.** A buffering proxy batches your tokens and
  destroys the streaming feel; disable it explicitly (OP-7).
- **Don't reach for WebSocket by default.** If the client only *receives*, SSE is
  simpler and gives reconnect for free `[mdn/sse]`. Reserve WS for true
  bidirectional needs.

**Hard boundaries (streaming is the wrong tool when):**
- Output must be **validated/transformed as a whole** before the user sees any of
  it (structured JSON you parse server-side, content that needs a safety pass) —
  stream nothing until validated, or stream into a parser, never raw to the user.
- The consumer is a **machine** that wants one atomic JSON object — give it the
  whole response; partial JSON tokens are a parsing hazard, not a feature.
- **No human is waiting** (offline batch) — streaming adds cost for no audience.

---

## 跨框架对照 (Cross-framework Context)

| Concern | LangGraph | LangChain (LCEL) | OpenAI SDK | Anthropic SDK |
|---|---|---|---|---|
| **Final tokens** | `stream_mode="messages"` → `(token, meta)` `[lg/stream]` | `astream_events` → `on_chat_model_stream` `[lc/astream-events]` | `stream=True`, iterate `delta.content` `[oai/stream]` | `client.messages.stream(...)`, `text_stream` `[anthropic/stream]` |
| **Intermediate steps** | `stream_mode="updates"` (per-node diff) `[lg/stream]` | `astream_events` (`on_tool_*`, `on_chain_*`) `[lc/astream-events]` | manual: detect `tool_calls` deltas `[oai/stream]` | manual: handle `content_block_*` / tool-use events `[anthropic/stream]` |
| **Full state** | `stream_mode="values"` (snapshot) `[lg/stream]` | rebuild from events | n/a | n/a |
| **Custom progress** | `stream_mode="custom"` + `get_stream_writer()` `[lg/stream]` | dispatch custom event / callback `[lc/astream-events]` | hand-rolled out-of-band | hand-rolled out-of-band |
| **Mix modes** | list form → tagged `(mode, chunk)` tuples `[lg/stream]` | one typed event stream, switch on `event` `[lc/astream-events]` | one delta stream, branch on field | one event stream, branch on type |
| **Granularity** | node-level + token-level + custom | event-level (richest typed taxonomy) | token + tool-call deltas | event + token (typed blocks) |

Heuristics:
- **LangGraph** — best when you already have a graph and want token+step+custom on
  one demuxable wire; `[lg/stream]` modes are the cleanest projection model. See
  `[[agentsop-langgraph]]` OP-8 for the orchestration side.
- **LangChain LCEL** — `astream_events` gives the **richest typed event taxonomy**
  (every `on_*` lifecycle hook); reach for it when you need fine-grained event
  routing without a full graph `[lc/astream-events]`.
- **Raw OpenAI / Anthropic** — you get a single token/delta stream and must derive
  "steps" yourself from tool-call deltas / content-block events. Choose when you
  have no orchestration layer and want zero framework weight `[oai/stream]`
  `[anthropic/stream]`.

Transport is **orthogonal** to all four: SSE (default, receive-only), WebSocket
(bidirectional), or async generator (internal) wraps any of them. Pick the SDK for
*what to stream*, the transport for *how the client consumes it* `[mdn/sse]`.

---

## 附录: 引用速查 (Citation Index)

Short tags → full sources in `references/R1-source-evidence.md`:

- `[lg/stream]` = LangGraph streaming concept (values / updates / messages / custom
  / debug; multi-mode list; `get_stream_writer`) — distilled in
  `[[agentsop-langgraph]]` OP-8 + `references/R1`.
- `[lc/astream-events]` = LangChain LCEL `astream_events` typed event stream.
- `[oai/stream]` = OpenAI streaming (`stream=True`, deltas, cancellation).
- `[anthropic/stream]` = Anthropic Messages streaming (`client.messages.stream`,
  `text_stream`, content-block events).
- `[mdn/sse]` = MDN Server-Sent Events (`EventSource`, named events, auto-reconnect,
  `Last-Event-ID`, comment heartbeats).
