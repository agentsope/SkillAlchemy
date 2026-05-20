---
name: agentsop-llm-tool-idempotency
version: 0.1.0
description: >-
  Decision protocol for making side-effectful agent tools idempotent — so when an LLM tool
  call is retried (timeout, framework resume, user re-run, model duplicate emit), the second
  call is a no-op instead of a double-send. The load-bearing premise: the LM cannot promise
  it'll call exactly once; the tool must promise the second call is safe. Framework-agnostic
  — applies to LangGraph node bodies that re-run on resume, MCP tools, OpenAI tool-calling
  retries, CrewAI delegated tool invocations, and direct HTTP wrappers. Search keywords:
  duplicate email sent, charged twice, exactly-once, idempotency key, tool called twice,
  retry side effect, double-send, at-least-once delivery.
domain: coder-agent / tool-execution-safety
audience: engineers wiring LLM agents whose tools have side effects (email,
  payment, DB writes, message posting, file creation, API calls)
trigger_keywords:
  - "idempotency key"
  - "double send"
  - "tool retry"
  - "exactly-once"
  - "at-least-once"
  - "duplicate side effect"
  - "node body re-runs on resume"
  - "interrupt resumed twice"
when_to_use:
  - "any agent tool that performs a side effect: send_email, create_record,
    charge_card, post_message, write_file, publish_event, transfer_funds"
  - "LangGraph node containing both an interrupt and a side effect"
  - "tool that wraps a non-idempotent third-party API (SendGrid, Twilio, S3 PUT
    of a generated id)"
  - "model-orchestrated workflow where the LM may emit the same tool_call_id
    twice due to streaming retries or compaction"
  - "MCP server exposing tools to a client that may re-invoke on transport
    failure"
when_not_to_use:
  - "pure read tools (search, get, list) — already idempotent by HTTP semantics"
  - "the side effect is intrinsically commutative (incrementing a counter where
    duplicates are acceptable — but verify this; usually they aren't)"
  - "single-call manual scripts with no retry layer above"
---

# LLM Tool Idempotency · SOP

> One-liner: **The LM is at-least-once; the tool must be at-most-once.**
> Every framework that promises "durable execution" still re-runs node bodies
> on resume. Every HTTP client retries on timeout. Every model occasionally
> emits the same tool_call twice. Idempotency belongs in the tool, not in a
> wish.

---

## 1. 何时激活 (Activation Rules)

Activate this skill when **any** of the following triggers fire:

- You're defining a tool whose name contains `send_`, `create_`, `charge_`,
  `post_`, `write_`, `publish_`, `transfer_`, `delete_`, `update_`, or
  `notify_`.
- The tool wraps a third-party API call (Stripe, SendGrid, Twilio, Slack,
  Discord webhook, S3 PUT, payment gateway, internal write API).
- You're inside a LangGraph node that contains an `interrupt(...)` call AND a
  side effect in the same function body — the resume re-runs the body from the
  top `[langgraph/gotchas]`.
- The tool is invoked through MCP, OpenAI tool-calling, Anthropic tool use,
  CrewAI delegation, or any layer where a transport timeout could be
  interpreted as "retry" even though the operation succeeded server-side.
- The user reports "the agent sent it twice" / "charge appeared twice" /
  "duplicate row" / "got two emails".
- Your test harness records the same `(tool_name, args_hash)` invoked more
  than once within a single user turn.

**Do not activate** when the tool is read-only (GET-equivalent), or when the
side effect is genuinely commutative AND verified safe under duplication.

---

## 2. 核心心智模型 (Core Mental Model)

### 2.1 The fundamental asymmetry

```
   LM tool-call semantics       Tool side-effect semantics
   ─────────────────────        ─────────────────────────
   At-least-once delivery       Must be at-most-once
   (network retry, framework    (one charge, one email,
    resume, model dup-emit,      one record)
    user re-prompt)
        │                                │
        └────── gap to bridge ───────────┘
                       ↓
              IDEMPOTENCY KEY
       (a stable identifier the LM
        commits to BEFORE the call,
        which the tool dedupes on)
```

**The LM cannot promise it'll call exactly once.** Four independent retry
sources stack here:

1. **Transport retry**: HTTP client (or MCP transport) sees a timeout, the
   server actually completed the operation, the client retries. Stripe's
   docs call this out as the canonical case `[stripe/idempotency]`.
2. **Framework resume**: LangGraph re-runs the *entire node body* on resume
   from an interrupt. Code before the interrupt re-executes on every resume
   `[langgraph/gotchas]`. Same applies to Temporal-style workflows on replay.
3. **Model duplicate emission**: Streaming sometimes yields the same
   `tool_call_id` twice (rare but documented in OpenAI tool-calling); model
   may re-emit on context-compaction round-trips.
4. **User-level retry**: The user clicks "send" twice, or re-runs the agent
   after timeout, with the same instructions.

Any one of these turns a single-intent action into multiple side effects
unless the tool itself dedupes.

### 2.2 The promise inversion

Naive design says: "I'll make the LM call the tool exactly once."

Mature design says: "I'll make the tool ignore the second call."

The inversion matters because the LM is in the *control* path; the tool is in
the *execution* path. Execution-path guarantees are the only ones that hold
under failure.

### 2.3 The idempotency key has to come from the agent, not the tool

A common bug: the tool generates a UUID *inside* itself, then dedupes on that
UUID. This breaks because retry creates a *new* UUID. The key has to:

- Be **chosen by the caller** (the agent / orchestrator).
- Be **deterministic for a single logical operation** — same input → same
  key on retry.
- Be **persisted into agent state** before the tool call, so a resume picks
  up the same key.

Stripe's pattern (the industry reference): client generates an idempotency key
(typically UUIDv4), sends it as `Idempotency-Key: <uuid>` HTTP header. Server
caches the response for 24 hours keyed by that header `[stripe/idempotency]`.
A retry with the same key returns the cached response — no second charge.

### 2.4 Three classes of side effect, three idempotency strategies

| Side-effect class | Examples | Idempotency mechanism |
|---|---|---|
| **Non-replayable external API** | Stripe charge, Twilio SMS, SendGrid email | Caller-supplied idempotency key passed to API (header or body field) |
| **Internal write to a store you own** | `INSERT` into your DB, `PUT` to your S3 bucket, append to your queue | Dedup table keyed on `(operation_id, args_hash)` with unique constraint, OR `INSERT … ON CONFLICT DO NOTHING`, OR content-addressed write |
| **Compensatable operation** (no native idempotency, must undo on duplicate) | Bank wire to a counterparty, physical device actuation | Saga pattern: record intent, perform, compensate-on-duplicate-detection; or a reservation token (two-phase) |

The SOP in §3 walks you through classifying first, then picking the mechanism.

---

## 3. SOP 工作流 (Agentic Protocol)

### Step 1 · Classify the side effect

Ask three questions, in order:

1. **Does the downstream API accept an idempotency key?**
   - Yes (Stripe, Square, modern PayPal, AWS SDK with client tokens,
     Anthropic Files API): use the native key. Stop here.
   - No: continue.
2. **Do I own the store being written to?**
   - Yes (my Postgres, my S3 bucket, my Kafka topic): build a dedup layer.
     Go to Step 2.
   - No: continue.
3. **Is the effect compensatable?**
   - Yes (can issue a refund / send a correction): saga / compensation.
   - No (irreversible physical action, sent SMS): the only safe option is
     **block the second call** — fail-closed dedup table, no fallback.

### Step 2 · Choose the idempotency mechanism

Decision tree:

```
Side effect classified above.
│
├─ Native idempotency-key API (Stripe et al.)
│  → OP-1: pass key in HTTP header / SDK kwarg
│
├─ Internal write you own
│  ├─ Operation has natural content identity (file hash, message dedup id)
│  │  → OP-3: content-addressed write (PUT key = sha256(content))
│  ├─ Single-row insert
│  │  → OP-4: INSERT ... ON CONFLICT (idempotency_key) DO NOTHING RETURNING *
│  └─ Multi-step write
│     → OP-2: dedup table + transaction at the tool boundary
│
└─ Compensatable, non-idempotent external call
   → OP-5: saga (record intent → call → compensate on duplicate)
```

### Step 3 · Decide where the key is generated and how it's named

| Source of key | When to use | Pitfall |
|---|---|---|
| `uuid4()` in agent state, persisted before call | Default for one-shot operations | Lost if state isn't persisted before the side effect |
| `hash(user_id, intent, day)` | Idempotency per-user-per-intent-per-day (e.g., daily digest email) | Too coarse → blocks legitimate second sends |
| `hash(canonicalized_args)` | Content-determined (same email body to same address) | Blocks legitimate "send the same message again later" |
| `hash(thread_id, node_id, run_id)` | LangGraph node-level dedup | Doesn't help across thread resumes that re-enter the same node |
| **Composite**: `hash(thread_id, node_id, attempt_args)` | Recommended for LangGraph node bodies that re-run on resume | One more arg to wire |

**Naming convention**: store the key in agent state as
`{tool_name}_idempotency_key`, persist it **before** the tool call. On
resume, check if state already has a key — if yes, reuse; if no, generate.

### Step 4 · Pass the key through every layer

```
Agent state ──→ Tool wrapper ──→ HTTP client ──→ External API
   (uuid)        (header)        (transport)      (server)
```

Verify each layer:

- Agent state stores the key in a serialized, checkpointed field (not in-memory
  only).
- Tool wrapper reads from state, not from a fresh `uuid4()` call.
- HTTP client uses the key as `Idempotency-Key` header *and* propagates it on
  client-side retries (don't generate a new key per HTTP retry).
- Server caches the response keyed on that header for a documented TTL
  (Stripe: 24 h; AWS SQS dedup: 5 min default; design your own to ≥ 1 h).

### Step 5 · Handle the conflict response

A successful idempotent retry returns the **original** response. A *conflict*
(same key, different args) usually returns 4xx — Stripe returns
`HTTP 409 Conflict` with code `idempotency_key_in_use` if the request payload
mismatches `[stripe/idempotency]`. Decision rules:

- **Same key, same args, cached response** → return to LM as if first call;
  surface a `was_replay: true` flag for observability.
- **Same key, different args** → bug in the caller. Fail loudly, do not
  fall back to "just send again". This catches "agent re-prompted with new
  message content but reused old key" bugs.
- **Key in flight** (server still processing first call) → either block
  (server-side wait) or return 409 / 425 Too Early. Caller must back off.

### Step 6 · Persist the dedup record on the *commit* side, atomically

The classic race: tool calls API, API succeeds, tool crashes before recording
the dedup row. Retry now duplicates because the dedup row is missing.

Two safe patterns:

- **Database transaction encloses both**: insert dedup row AND record of API
  call in the same transaction; commit. If external API is the side effect,
  the dedup row goes in *before* the external call, with a `status: pending`
  flag, then updated to `status: completed` after. On retry, `pending` means
  "wait or fail" — not "go ahead and call again".
- **Use the external API's idempotency** as the source of truth (OP-1) — skip
  your own dedup table entirely; trust Stripe's. Recommended when available.

### Step 7 · Expose `was_replay` in the tool result

The LM should know it didn't actually re-send. Return:

```json
{
  "result": { /* original response payload */ },
  "was_replay": true,
  "original_called_at": "2026-05-19T10:11:12Z"
}
```

Why: prevents the agent from thinking "send failed, let me try a different
phrasing" and producing a logical (not technical) duplicate.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**.

### OP-1 · Idempotency-key HTTP header (Stripe pattern)
- **Trigger**: Wrapping a third-party API that supports idempotency keys
  (Stripe, Square, modern PayPal, Adyen, Anthropic Files, AWS with client
  tokens).
- **Action**: Before the call, read or generate
  `key = state.get("charge_key") or uuid4()`; persist to state; pass as
  `Idempotency-Key: <key>` header (or SDK kwarg, e.g.
  `stripe.PaymentIntent.create(..., idempotency_key=key)`).
- **Output**: At most one server-side execution per key; retries return cached
  response. TTL ~24 h for Stripe.
- **Evidence**: `[stripe/idempotency]` "Stripe's idempotency works by saving
  the resulting status code and body of the first request made for any given
  idempotency key, regardless of whether it succeeded or failed."

### OP-2 · Dedup table at the tool-call layer
- **Trigger**: Internal API with no native idempotency, multi-row write,
  or aggregation that doesn't fit content-addressing.
- **Action**: Create table `tool_call_dedup(key TEXT PRIMARY KEY,
  tool_name TEXT, args_hash TEXT, result JSONB, status TEXT,
  created_at TIMESTAMPTZ)`. On call: `INSERT … ON CONFLICT(key) DO NOTHING
  RETURNING …`. If insert succeeds, perform side effect, then
  `UPDATE … SET result=…, status='completed'`. If conflict, read row, return
  its `result`.
- **Output**: Single execution per key across all retries; replayable result.
- **Evidence**: This is the generalised form of Stripe's server-side
  implementation `[stripe/idempotency]`; appears in PayPal, AWS SDK
  whitepapers as the standard "dedup table" pattern
  `[aws/idempotency-whitepaper]`.

### OP-3 · Content-addressed write
- **Trigger**: Writing a file, blob, or message whose identity *is* its
  content (build artifact, immutable record, derived data).
- **Action**: Compute `key = sha256(canonical_content)`; write to
  `PUT /bucket/{key}`. S3 conditional put (`If-None-Match: *`, available
  since 2024) returns 412 on second write.
- **Output**: Repeated writes are no-ops (same key → same content). No dedup
  table needed.
- **Evidence**: `[aws/s3-conditional]` S3 conditional writes documentation;
  this is the underlying primitive in Git, IPFS, content-addressable storage
  generally.

### OP-4 · Database `INSERT … ON CONFLICT … DO NOTHING`
- **Trigger**: The side effect is a single row insert into a table you own
  (audit log, message record, user-generated record).
- **Action**: Add a unique constraint on
  `(idempotency_key)` or `(user_id, intent, request_id)`. Use
  `INSERT … ON CONFLICT(idempotency_key) DO NOTHING RETURNING id`.
- **Output**: Empty result set means "duplicate, no-op". Non-empty means
  "first call, inserted".
- **Evidence**: PostgreSQL `ON CONFLICT` semantics `[pg/insert]`; MySQL
  `INSERT IGNORE`; SQLite `INSERT OR IGNORE`. The database does the dedup;
  no application race window.

### OP-5 · Saga / compensation for non-idempotent compensatable APIs
- **Trigger**: The downstream system has no idempotency API but the effect
  can be undone (refund, retraction, correction email).
- **Action**:
  1. Record intent in your DB with `status='pending', key=<id>` in a
     transaction.
  2. Call the external API.
  3. Update to `status='completed', external_id=<their_id>`.
  4. On retry detected (key already present, status='completed'): return the
     stored `external_id`, do not call again.
  5. On retry detected (status='pending', call in flight): wait + poll, do
     not call again.
  6. On reconciliation job finding a `pending` past TTL: investigate; possibly
     compensate the now-known external_id.
- **Output**: At-most-once semantics with a recovery path.
- **Evidence**: Saga pattern `[microservices/saga]`; Temporal workflow
  `[temporal/idempotency]` uses the same shape under the hood.

### OP-6 · LangGraph: pull key from state before `interrupt()`
- **Trigger**: A LangGraph node both calls `interrupt()` and performs a side
  effect.
- **Action**:
  ```python
  def send_email_node(state):
      # Step 1: derive a stable key BEFORE interrupt
      key = state.get("email_key") or str(uuid4())
      state["email_key"] = key   # persist via reducer
      decision = interrupt({"to": state["to"], "body": state["body"]})
      if decision != "approve":
          return {"status": "rejected"}
      # Step 2: side effect uses the key — safe under resume
      result = send_email_api(to=state["to"], body=state["body"],
                              idempotency_key=key)
      return {"email_sent": True, "email_key": key, "result": result}
  ```
- **Output**: Resume re-runs the node body but the key is stable, so the
  external send is a no-op on the second pass.
- **Evidence**: `[langgraph/gotchas]` "Side effects after interrupt() will
  re-run on resume — wrap them with an idempotency key drawn from state."
  See LangGraph payment-double-charge Case Study 4 in
  `output/langgraph-sop-skill/SKILL.md`.

### OP-7 · MCP / tool-boundary dedup window
- **Trigger**: MCP server exposing a side-effectful tool to a client that may
  retry on transport timeout.
- **Action**: In the MCP tool implementation, accept an
  `idempotency_key` argument as part of the tool schema; require it for
  side-effectful tools. Maintain a server-side dedup window (e.g., 5-minute
  in-memory LRU + persistent backing for cross-restart safety).
- **Output**: Transport-level retries (which MCP clients do) hit the dedup
  cache; only one execution.
- **Evidence**: MCP spec does not mandate idempotency, so this is a
  *server* responsibility — analogous to Stripe's server-side dedup. Surface
  the requirement explicitly in the tool's input schema.

### OP-8 · Pre-call state checkpoint (works for any framework)
- **Trigger**: Working in a framework without first-class durable execution
  (plain Python loop, CrewAI task, custom orchestrator).
- **Action**: Before calling a side-effectful tool, persist
  `(intent_id, args_hash, key, status='in_progress')` to a local sqlite or
  durable store. After call: update to `status='completed'` with result.
  Wrap in a context manager so a crash leaves `in_progress`, and a retry
  reads that state and either polls or fails-closed.
- **Output**: At-most-once across process crashes, not just within-process.
- **Evidence**: Generalisation of OP-5 for any orchestration layer; equivalent
  to Temporal's activity-level idempotency `[temporal/idempotency]`.

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 · "LangGraph node body re-runs on resume, sending two emails"
- **困境**: Team builds a customer-support agent. The flow is: classify issue
  → propose response → `interrupt()` for human review → if approved, call
  `send_email(...)` in the same node. They notice that after a resume, the
  customer sometimes gets two emails. The cheatsheet warns that on resume
  "the entire node function re-runs from the top" `[langgraph/gotchas]`, so
  the proposal-classification *and* the email-send both re-execute.
- **约束**:
  - Cannot disable HITL — compliance requires the human approval.
  - SendGrid (their email provider) does not natively support idempotency
    keys on the v3 mail send endpoint.
  - Cannot tolerate even a 1% duplicate rate — customers complain.
- **决策步骤**:
  1. **Refactor the node topology first**: move `send_email` into a
     downstream node that runs *only after* the interrupt-bearing node
     returns approval into state. (LangGraph SOP "side effects after
     interrupt" rule.)
  2. **Belt-and-braces idempotency** at the tool layer: generate
     `email_key = uuid4()` *before* the interrupt, persist to state. The
     send-tool checks a local Postgres `email_dedup` table keyed on
     `email_key`. (OP-4)
  3. The send-tool flow:
     - `INSERT INTO email_dedup(key, status) VALUES($1, 'sending')
       ON CONFLICT(key) DO NOTHING RETURNING key`
     - If empty rows returned → another invocation in flight or completed;
       fetch row, return its cached result.
     - If insert succeeded → call SendGrid; on success, update row to
       `status='sent', message_id=<sg_id>`.
  4. **Crash-safety check**: if status remains `'sending'` past a 5-minute
     TTL, the reconciler queries SendGrid's API by sender+recipient+time
     window and reconciles.
- **结果**: Duplicates drop to zero in production. The node-topology fix
  alone reduces the rate; the dedup table closes the residual race.
- **可提取的操作**: OP-4 + OP-6. **The fix is two-layer: framework topology
  AND tool-layer dedup. Either alone leaks.**

### Case 2 · "User says 'send the email to Alice' twice — block or allow?"
- **困境**: A user issues the same instruction twice in two turns:
  "Send Alice the meeting summary." The first call succeeds. The second call
  comes 20 seconds later. Should the tool block (idempotency!) or allow
  (legitimate re-send!)?
- **约束**:
  - The user genuinely sometimes wants to re-send (Alice didn't get it).
  - The user sometimes accidentally repeats themselves (UI lag).
  - You can't ask the user every time without ruining the agent UX.
- **决策步骤**:
  1. **Idempotency is per-intent, not per-content.** The key for this tool
     should derive from `(user_turn_id, intended_recipient, intended_subject)`
     — not from the message content. Two *turns* → two intents → two keys
     → two sends.
  2. Within a single turn, if the agent emits `send_email(...)` twice (model
     dup-emission), the `user_turn_id` is the same → key collision → second
     call is a no-op. This catches the failure we care about.
  3. Across turns, if the user genuinely re-requests "send Alice", the
     `user_turn_id` is new → new key → second send happens.
  4. **Add a soft guard**: when the agent is about to call `send_email`
     within 60 seconds of a successful previous call to the same recipient
     with similar content, the *agent* prompt should ask the user "I sent
     this 20 seconds ago — re-send?" — a UX rail, not a technical one.
- **结果**: Tool-layer dedup catches the technical bug class
  (model/framework duplication). UX rail catches the human-intent bug class.
  They're separate; both needed.
- **可提取的操作**: **Key on user-intent boundary, not content. Add a UX-level
  "you just did this" prompt for cross-turn near-duplicates.**

### Case 3 · "Agent retries with new args after timeout — same key, conflict"
- **困境**: Agent calls `create_record(name='Alice')`. The HTTP client times
  out. The agent (different turn, longer context) retries:
  `create_record(name='Alice Smith')`. It reuses the same idempotency key
  from state because the key is keyed on `(thread_id, tool_name)`. Stripe-
  style: returns 409 `idempotency_key_in_use`. Agent sees an error.
- **约束**:
  - The first call may or may not have completed server-side (we timed out
    before getting a response).
  - The agent corrected the name — the second call has different intent.
- **决策步骤**:
  1. **The key is wrong.** Keys must be specific to the args, not just
     `(thread, tool)`. Either:
     - Hash the canonical args into the key, OR
     - Generate a new key per logical operation (every `propose to call
       tool` event), not per `(thread, tool)` pair.
  2. **Handle the conflict response explicitly**: a 409 with
     `idempotency_key_in_use` is a *programmer bug*, not a recoverable
     state. Surface to the operator with full diagnostics; do not let the
     agent retry with yet another args change.
  3. **Reconcile the original timed-out call**: query the API by a stable
     business identifier (e.g., natural unique on `name`) and check whether
     the record was created. If yes, decide: update vs. delete-and-recreate.
- **结果**: Better keying convention. 409 becomes a loud signal of caller
  bug, not a silent dedup.
- **可提取的操作**: OP-1 + Step 5. **Key on `(intent + args_hash)`, treat
  same-key-different-args as a bug to surface, not a duplicate to absorb.**

### Case 4 · "MCP tool, transport retries, no idempotency in the protocol"
- **困境**: An MCP server exposes `send_slack_message(channel, text)` to an
  agent. The MCP client uses a transport with retry-on-timeout. Slack
  messages duplicate.
- **约束**:
  - Slack's `chat.postMessage` does not have native idempotency (it
    accepts a `client_msg_id` but doesn't enforce uniqueness server-side).
  - MCP protocol itself does not guarantee at-most-once delivery — the spec
    treats it as request/response; retries are the client's call.
- **决策步骤**:
  1. **The MCP tool boundary is where dedup lives** (OP-7). Update the tool
     schema:
     ```json
     {
       "name": "send_slack_message",
       "input_schema": {
         "properties": {
           "channel": {"type": "string"},
           "text": {"type": "string"},
           "idempotency_key": {"type": "string",
             "description": "Unique per send-intent. Server dedupes within
             5 min. Reuse the same key to retry safely."}
         },
         "required": ["channel", "text", "idempotency_key"]
       }
     }
     ```
  2. Server maintains a 5-minute LRU keyed on
     `idempotency_key → previous_response`. Retry within window → cached
     response. Outside window → new send.
  3. The agent (LM caller) generates the key from agent state, persists
     before call. (OP-8 if the agent has no first-class durable execution.)
- **结果**: Slack duplicates eliminated; the contract is now explicit at the
  tool schema layer.
- **可提取的操作**: OP-7. **Make `idempotency_key` a required schema field
  on every side-effectful MCP tool. Document the dedup window in the
  description.**

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Concrete don'ts

- **Don't assume the LM "won't retry".** It will. Streaming dup-emission,
  framework resume, HTTP client retry, user re-prompt — at least one will
  fire in production. The cheatsheet warning is unambiguous: every node body
  re-runs on resume `[langgraph/gotchas]`.
- **Don't generate the idempotency key *inside* the tool.** A `uuid4()` call
  on each tool invocation defeats the entire mechanism — the retry generates
  a *new* UUID and the dedup table sees no collision.
- **Don't key on `now()` or any time-varying value.** Same logical operation
  retried 30 seconds later must produce the same key. Time-based keys
  guarantee duplicates.
- **Don't dedup on natural keys *post hoc* without a unique constraint.** A
  "check then insert" pattern has a race window. Use database-enforced
  unique constraint + `ON CONFLICT` (OP-4) so the dedup is atomic.
- **Don't conflate "same args" with "same intent".** A user can legitimately
  ask "send Alice the same message" tomorrow — the args are identical but
  the intent is new. Key on a turn-level or run-level identifier.
- **Don't return success on a duplicate without flagging it.** Set
  `was_replay: true` in the tool result so the LM (and observability) knows
  the second call was absorbed.
- **Don't store the dedup key only in memory.** A process restart wipes it.
  Persist to the same durable store as your agent state (checkpointer,
  workflow log, sqlite).
- **Don't put external side effects *before* `interrupt()` in a LangGraph
  node.** The interrupt-resume pattern re-runs the body from the top
  `[langgraph/gotchas]`. Move side effects to a downstream node OR use
  OP-6.
- **Don't trust HTTP 2xx as "the operation happened".** A 504 (gateway
  timeout) could mean either "didn't happen" or "happened but you can't
  read the response". Idempotency keys turn this from an error case to a
  retry case.
- **Don't skip idempotency on "internal" APIs.** Your internal microservice
  call has the same network properties as Stripe's — if it has side effects,
  it needs an idempotency key.

### Hard boundaries (idempotency-key alone won't save you)

| Scenario | Why a key isn't enough | What to do |
|---|---|---|
| Physical actuation (open valve, fire missile) | No way to "undo"; second activation has new physical effect | Two-phase commit; explicit human confirm; never auto-retry |
| Cash wire to a third-party bank | Some networks don't have idempotency; some have but with 24 h windows | Saga (OP-5) + reconciliation job + manual review |
| Cross-service distributed transaction | Each service has its own dedup window | Choreographed saga with compensation; not a single key |
| External service ignores idempotency key | They claim to support it but don't dedup | Wrap in your own OP-2 table; never trust unverified claims |
| Streaming side effect (Kafka producer) | Producer at-least-once by default | Use Kafka's idempotent producer + transactional writes; not just a key |

### Specific framework pitfalls

- **LangGraph**: Resume re-runs the node body — every line, from the top, on
  every resume `[langgraph/gotchas]`. Idempotency key MUST be drawn from
  *checkpointed state*, not generated inside the node.
- **CrewAI**: Tools shared across agents can be invoked multiple times by
  different agents in a single crew run. Per-agent tool binding + dedup at
  the tool layer prevents one agent from undoing another's work
  `[crewai/tools]`.
- **OpenAI tool-calling**: Streaming responses occasionally yield the same
  `tool_call_id` twice during compaction; treat `tool_call_id` as a useful
  *signal* but not as the idempotency key itself — the model can synthesise
  new ids on retry.
- **MCP**: The protocol does not mandate idempotency; you must build it into
  the tool schema (OP-7).
- **Anthropic tool use**: Same as OpenAI — model can re-emit; the
  `tool_use_id` is per-emission, not per-intent.

---

## 7. 跨框架对照 (Ecosystem Context)

| | Stripe API | AWS SQS (FIFO) | Temporal | LangGraph | MCP | Plain HTTP/Python |
|---|---|---|---|---|---|---|
| Idempotency unit | HTTP request | Message | Workflow activity | Node body | Tool call | Caller-managed |
| Key carrier | `Idempotency-Key` header | `MessageDeduplicationId` | Activity ID + input hash | State field | Tool input arg | Custom |
| Dedup window | 24 hours | 5 minutes (default) | Until workflow completes | Until checkpoint expires | Implementation-defined | None by default |
| Storage | Stripe-side | SQS-side | Temporal cluster | Checkpointer (Postgres/SQLite/Redis) | Your server | Your code |
| What replays on retry | Cached response returned | Message acknowledged silently | Activity skipped, result returned | Node body re-runs! | Depends on server | Whatever you wrote |
| Where bugs typically hit | Caller reuses key on different args (409) | Window expires under load | Non-deterministic activity code | Side effect inside re-running body | Missing key arg | All of the above |

### Decision heuristics

- **Wrapping a payment / messaging API**: use the provider's idempotency key
  (OP-1). Don't reinvent — Stripe's 24-hour window and 409-on-mismatch
  semantics are battle-tested.
- **Writing to your own database**: prefer OP-4 (`INSERT … ON CONFLICT`)
  for single-row; OP-2 (dedup table + transaction) for multi-step.
- **Writing immutable content (artifacts, derived files)**: use OP-3
  (content-addressed). It is idempotency-by-construction; no key needed.
- **Inside LangGraph with HITL**: OP-6 (key from state, side effect after
  resume) is non-negotiable. Skipping it is the #1 source of duplicate-charge
  bug reports in LangGraph production.
- **Exposing tools via MCP**: OP-7 — bake `idempotency_key` into the input
  schema for any side-effectful tool. The protocol won't enforce it; your
  server must.
- **Custom orchestration, no first-class durable execution**: OP-8 — write
  a pre-call checkpoint to sqlite; treat `in_progress` rows as
  "do not retry without reconciliation".

### Lessons that travel across frameworks

1. **At-least-once is the default; at-most-once is engineered.** Every
   transport layer you traverse is at-least-once. The only way out is a
   per-operation key + dedup at the execution boundary.
2. **The key must be born before the side effect, not with it.** Generate it
   in the caller's persistent state. The retry must produce the *same* key.
3. **Frameworks that promise "durable execution" still re-run code on
   resume.** LangGraph's official cheatsheet says it explicitly
   `[langgraph/gotchas]`; Temporal docs likewise warn about
   non-determinism in activities `[temporal/idempotency]`. Idempotency is
   the orthogonal axis.
4. **Surface replay status to the LM.** Without `was_replay: true`, the
   model can't reason about its own action history; it'll loop or "fix"
   non-bugs.
5. **A 409 on idempotency-key reuse is a caller bug, not a duplicate to
   absorb.** Treat it loudly. The bug is almost always "key isn't specific
   enough" — fix the key generation, don't suppress the error.

---

## 附录: 引用速查 (Citation Index)

Short tags used inline → full sources in `references/`:

- `[stripe/idempotency]` = https://docs.stripe.com/api/idempotent_requests
- `[aws/idempotency-whitepaper]` = AWS Architecture Blog: "Building idempotent
  APIs" (2023) and Powertools-Lambda idempotency module docs.
- `[aws/s3-conditional]` = https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html
- `[pg/insert]` = https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT
- `[temporal/idempotency]` = https://docs.temporal.io/develop/activities#idempotency
- `[microservices/saga]` = https://microservices.io/patterns/data/saga.html
- `[langgraph/gotchas]` = LangGraph cheatsheet / FAQs — side-effects on
  resume; mirror in `output/langgraph-sop-skill/SKILL.md` Case 4.
- `[crewai/tools]` = https://docs.crewai.com/en/concepts/tools — per-agent
  tool binding pattern.
