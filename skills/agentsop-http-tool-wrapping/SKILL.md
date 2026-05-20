---
name: agentsop-http-tool-wrapping
version: 0.1.0
description: |
  Decision protocol for wrapping a REST / GraphQL / RPC API as a tool an LLM
  agent can call. The load-bearing premise: the *tool surface* is an
  LM-friendly subset of the *API surface* — one tool per user intent, not one
  per endpoint. Activates when a coder agent must expose an external HTTP API
  to a model (function calling, tool_use, MCP, LangChain `@tool`, CrewAI
  `BaseTool`). Encodes the *what to surface, how to name, how to shape, how to
  fail* — not any single framework's API. ~80% of agent tools in production are
  HTTP wrappers; this is the SOP for getting them right.
domain: coder-agent / tool-construction
audience: engineers wiring external APIs into LLM agents
trigger_keywords:
  - "wrap an API as a tool"
  - "expose REST endpoint to agent"
  - "function calling for my API"
  - "MCP server for existing API"
  - "tool returns too much JSON"
  - "agent rate limited / 429"
  - "GraphQL / RPC as agent tool"
when_to_use:
  - "exposing a third-party or internal HTTP API to an LLM agent"
  - "deciding which of N endpoints deserve to become tools"
  - "an existing tool dumps raw JSON and the model hallucinates fields"
  - "tool calls fail on rate limits, timeouts, or pagination"
  - "porting the same tool across OpenAI / Anthropic / MCP / LangChain / CrewAI"
when_not_to_use:
  - "the API is already an MCP server you only consume (just connect)"
  - "no external I/O — pure local computation (write a plain function tool)"
  - "designing the upstream API itself (that's API design, not tool wrapping)"
---

# HTTP / External API → Agent Tool · SOP

> Source posture: every non-trivial claim is cited inline with short tags like
> `[oai/fc]`, `[anthropic/tooluse]`, `[lc/tools]`, `[mcp/spec]`, `[apxml/schema]`.
> Resolve them against `references/R1-source-evidence.md` for full URLs. Reusable
> code shapes live in `references/R2-pattern-library.md`.

---

## 1. 何时激活 (When to Activate)

Activate when a coder agent must make an **external HTTP API callable by an LLM**.
Concrete triggers:

- The task says "give the agent access to <some API>", "add a tool that calls
  <service>", "wrap our REST/GraphQL/RPC endpoint as a function the model can use".
- You are choosing which of N endpoints become tools, or how to name them.
- An existing tool returns a huge JSON blob and the model hallucinates field
  names, or burns context re-reading it.
- Tool calls die on `429`, timeouts, or unpaginated list endpoints.
- You need the *same* tool to run under OpenAI function calling, Anthropic
  `tool_use`, an MCP server, LangChain `@tool`, and CrewAI `BaseTool`.

**Do not activate** when: the API is already exposed as an MCP server you merely
consume (just connect it); the "tool" is pure local computation with no network
I/O (write a plain typed function); or you are designing the upstream API itself.

This is a **tool-construction** skill — sibling to the framework SOPs
(`langgraph-sop`, `crewai-sop`) which decide *whether/where* tools run. Once you
know you need a tool, this skill decides *what shape it takes*.

---

## 2. 核心心智模型 (Core Mental Model)

**The tool surface is an LM-friendly subset of the API surface. One tool per
intent, not one per endpoint.**

A REST API is designed for *programmers* who read docs, hold a mental model of
resources, and compose calls. An agent tool is designed for a *language model*
that sees only a name, a description, and a JSON schema — and must decide,
mid-reasoning, whether this is the thing to call. These are different audiences,
so the surface must be *re-cut*, not *mirrored*.

> "Tool descriptions are often more important than code comments because the LLM
> directly uses them for reasoning." `[apxml/schema]`

Four load-bearing consequences:

1. **Intent, not CRUD.** The unit of a tool is a *thing the agent wants to
   accomplish* (`cancel_order`, `find_customer_by_email`), not an HTTP verb on a
   resource (`DELETE /orders/{id}`). One intent may compose several endpoints;
   one endpoint may serve zero intents (admin/batch/webhook-out endpoints get
   dropped). Surface intent, not the verb table `[zuplo/agent-ready]`.

2. **The schema is the prompt.** The model never sees your code. It sees the
   tool name, the description, and each field's `description=`. Every field
   needs units, format, enum values, and an example *aimed at the model* — "if a
   field is a date, specify ISO 8601 vs Unix timestamp" `[apxml/schema]`. A
   typed schema (Pydantic / JSON Schema) is non-negotiable because it is *both*
   the validation layer and the documentation the model reads `[lc/tools]`.

3. **The response is context, and context is scarce.** A 10 MB JSON payload is
   not "data the agent has" — it is tokens the agent must pay for, re-read, and
   can misquote. Shape the response down to the fields the agent needs to
   *reason or act* on. Returning raw upstream JSON is the second most common
   anti-pattern after 1:1 mapping.

4. **The model cannot promise call discipline.** It may emit zero, one, or
   several calls — "best practice [is] to assume there are several"
   `[oai/fc]` — retry on its own, or be resumed by the framework. So the
   *wrapper* owns reliability (timeout, retry, rate-limit) and *safety*
   (idempotency on mutations). You cannot prompt these guarantees into existence;
   you build them into the tool. (Side-effect safety is deep enough to be its
   own skill — cross-link **`llm-tool-idempotency`** for any mutating tool.)

The pre-LLM analog: you are writing an **SDK for a non-deterministic, amnesiac
junior dev who reads only the function signature** — generous docstrings, narrow
typed inputs, small clean returns, and total robustness to being called wrong.

---

## 3. SOP 工作流 (Standard Operating Procedure)

Walk top-down. Each step has a gate — if it fails, fix it before adding surface.

### Step 1 · Triage: which endpoints deserve to be tools?

List every endpoint × verb. For each, ask: **"what user/agent intent does this
serve?"** Drop endpoints with no agent-facing intent (internal admin, batch
jobs, outbound webhooks). The MCP guidance is a useful first cut: GET-style
data reads often map to *resources*; create/update/delete map to *tools*
`[gun/mcp]`. Target **≤10 surfaced operations** for a first pass.

> Gate: if you are about to create one tool per endpoint, stop — that is AP-1.
> Auto-generated 1:1 servers from an OpenAPI spec "routinely under-perform
> hand-curated tools" `[stainless/mcp]`.

### Step 2 · Name from intent

Tool name = `verb_object` describing intent: `search_orders`, `cancel_order`,
`get_order_status`. **Not** `post_orders_v2`, `delete_orders_id`. Test: a model
that has never seen your API, reading *only the name*, should guess when to call
it. The name should be a verb; the description should explain *when* to call,
not *how* `[oai/prompting]`.

### Step 3 · Flatten params into a typed schema

Define a Pydantic model (or JSON Schema). Rules:

- Type-annotated fields, each with a model-facing `description=` (units, format,
  enum, example) `[lc/tools]` `[apxml/schema]`.
- Flatten the API's wire format: `filter[status]=open` → `status:
  Literal["open","closed"]`. The model should never construct a query-string
  fragment.
- Explicit required vs optional. Defaults where the API has sensible ones.
- Hide pagination/auth/internal knobs from the schema (Steps 5–6).

> Gate: every field the model can set has a `description=`. Untyped `**kwargs` or
> a free-form `body: str` is a smell — the model will fill it wrong.

### Step 4 · Error handling: translate, never leak

Catch `HTTPStatusError` / `ValidationError` / network errors. Return a
**structured, LM-readable** error, never a raw stack trace:

```json
{"error": "rate_limited", "message": "...", "retryable": true, "hint": "wait and retry"}
```

Use a small closed set of `error` codes (`not_found`, `invalid_input`,
`auth_failed`, `rate_limited`, `server_error`). LangChain's `ToolException`
converts a raised error into an LM-visible string for the same reason
`[lc/structured]`. The model reasons over the error like any other tool output —
give it something it can act on.

### Step 5 · Shape the output

Define an **output** model with only the fields the agent needs. Drop audit
timestamps, internal mirrors, deprecated fields, ETags. Summarize blobs into
strings. Aim for a compact payload per call (rule of thumb: keep it small enough
that re-reading it 5 times in a loop is cheap). For lists, return items + a
`next_cursor`, not the whole dataset (Step 5b).

**Step 5b · Pagination.** Default: fetch *one* page, return `items +
next_cursor`, let the agent decide to continue. Prefer cursor over offset —
"cursor-based pagination is more reliable than offset/limit for agentic
scrolling" `[techops/rest]`. Auto-loop only when total is small and bounded
(≤200); never loop unbounded — a single agent can "burst 20 sequential API
calls to complete one task" `[zuplo/agent-ready]` (cross-link bounded-loop skill).

### Step 6 · Auth & secrets at the wrapper boundary

Read the key/token from env or a secret store **inside** the wrapper. **Never**
expose `api_key` as a tool parameter and never put a secret in the description —
the model doesn't need it and traces would leak it. Per-tenant tokens flow via a
closure or context object, not via tool args `[northflank/mcp]`.

> Gate: grep your tool schema and description for `key`, `token`, `secret`,
> `password`. Zero hits.

### Step 7 · Idempotency on mutations

If the tool does POST/PUT/DELETE, it *will* be retried by the model or the
framework. Generate an idempotency key per logical operation and pass it
(`Idempotency-Key` header) when the API supports it — the canonical Stripe
pattern `[stripe/idem]`. Tag the tool metadata `mutating=True`. For the full
decision tree (key derivation, dedup store, at-least-once vs exactly-once),
**defer to the `llm-tool-idempotency` skill** — that is its entire domain.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**. (Full JSON in
`intermediate/operation_candidates.json`.)

### OP-1 · Endpoint triage
- **Trigger**: New API, >3 endpoints.
- **Action**: Enumerate endpoint × verb; label each with the agent intent it
  serves; drop the intent-less ones. Cap at ~10.
- **Output**: Triaged candidate list with intent labels.
- **Evidence**: `[zuplo/agent-ready]` `[stainless/mcp]`.

### OP-2 · Name by intent
- **Trigger**: Naming a surfaced operation.
- **Action**: `verb_object`; name-only readability test.
- **Output**: Intent-named tool.
- **Evidence**: `[oai/prompting]`.

### OP-3 · Typed input schema
- **Trigger**: Each surfaced tool.
- **Action**: Pydantic model; per-field model-facing `description=`; flatten wire
  params; explicit required/optional.
- **Output**: `args_schema` on the tool.
- **Evidence**: `[lc/tools]` `[oai/fc]` `[anthropic/tooluse]` `[apxml/schema]`.

### OP-4 · Inject auth at boundary
- **Trigger**: Tool needs a key/token.
- **Action**: Read secret inside the wrapper from env/secret store; never a tool
  param; per-tenant via closure/context.
- **Output**: Tool that authenticates with no secret in schema.
- **Evidence**: `[northflank/mcp]`.

### OP-5 · Timeout + retry + jittered backoff
- **Trigger**: Any outbound HTTP from a tool.
- **Action**: Explicit per-attempt `timeout=`. Retry only on 429/5xx/network,
  max 3–5, exponential backoff **with jitter**, honor `Retry-After`. Never retry
  other 4xx.
- **Output**: Resilient client inside the tool.
- **Evidence**: `[apxml/rate]` `[boldsign/retry]` `[getknit/rate]`.

### OP-6 · Pagination — cursor first
- **Trigger**: List endpoint with `next`/`cursor`/`Link`.
- **Action**: Return one page + `next_cursor`; agent decides to continue;
  bounded auto-loop only for small totals.
- **Output**: Paginated tool with explicit cursor surface.
- **Evidence**: `[techops/rest]` `[zuplo/agent-ready]`.

### OP-7 · Response shaping
- **Trigger**: API returns large/deep JSON.
- **Action**: Output Pydantic model with only reason/act-relevant fields; drop
  audit/internal/deprecated; summarize blobs.
- **Output**: Trimmed structured output.
- **Evidence**: `[apxml/schema]` `[gun/mcp]`.

### OP-8 · Error → readable feedback
- **Trigger**: Non-2xx or local exception.
- **Action**: Catch; return `{error, message, retryable, hint}` from a closed
  code set; never raw traces.
- **Output**: LM-readable error contract.
- **Evidence**: `[lc/structured]` `[mighty/fault]`.

### OP-9 · Idempotency key on mutations
- **Trigger**: POST/PUT/DELETE side effect.
- **Action**: Per-operation idempotency key via header; tag `mutating=True`.
  Defer full protocol to `llm-tool-idempotency`.
- **Output**: Mutation-safe tool with idempotency contract.
- **Evidence**: `[stripe/idem]` `[techops/rest]` `[mighty/fault]`.

### OP-10 · Framework binding
- **Trigger**: Implementation done; deploy into an agent.
- **Action**: One Pydantic schema → all targets. LangChain/LangGraph: `@tool`
  with `args_schema`. CrewAI: subclass `BaseTool._run`. OpenAI: `tools=[{type:
  "function", function:{...}}]`. Anthropic: `{name, description, input_schema}`.
  MCP: `@mcp.tool()`. Derive each via `Model.model_json_schema()`.
- **Output**: Framework-bound tool.
- **Evidence**: `[lc/tools]` `[crewai/tools]` `[mcp/spec]` `[oai/fc]`
  `[anthropic/tooluse]`.

---

## 5. 困境决策案例 (Dilemma Cases)

### DC-1 · Wide API (50+ endpoints): one mega-tool or many?

**Scenario**: A CRM API has 60 endpoints. Do you ship 60 tools, or one
`crm_operation(operation: str, params: dict)` mega-tool?

**Trap (mega-tool)**: A single tool with a free-form `operation` string and a
`dict` of params pushes all routing into the model with no schema help. "A
mega-tool with a single instructions string invites hallucinations"
`[medium/velorum]` — the model invents operation names and param shapes, and the
wrapper can't validate them.

**Trap (1:1, 60 tools)**: Flat catalogs degrade selection accuracy at scale —
beyond ~50 tools, "flat tool-list catalogs degrade selection accuracy;
hierarchical / graph organization helps" `[arxiv/toolnet]`. The model spends
reasoning budget scanning a wall of near-identical names.

**Decision rule**:
1. Triage to the ~10 endpoints with real agent intent (OP-1). Most wide APIs
   collapse hard — 60 endpoints, ~8 intents.
2. If still >~15 after triage, **group by sub-domain into a few medium tools**,
   each with a *typed* `action: Literal[...]` enum (not a free string) plus a
   discriminated-union params model. The enum keeps schema validation; the
   grouping keeps the catalog short. This is the middle path between 1:1 and
   one mega-blob.
3. Only consider a true mega-tool if the API is genuinely uniform (e.g. a
   GraphQL endpoint where the single tool is `graphql_query(query, variables)`
   with a documented schema) — and even then, constrain it.

**Verdict**: Neither extreme. Triage first, then *typed grouping*. The win is a
short catalog of validated tools, not raw endpoint count in either direction.

### DC-2 · API returns 10 MB JSON: what to expose?

**Scenario**: `get_customer_360` returns a 10 MB document — full order history,
event logs, nested addresses, internal flags.

**Trap**: Return it whole. The model pays ~2–3M tokens, can't fit it, and will
quote fields that aren't there. Truncating blindly loses the field the agent
needed.

**Decision rule**:
1. Ask *what the agent will do with this*. Usually it needs 5–15 fields, not
   2,000. Define a thin output model of exactly those (OP-7).
2. For the long tails (order history, logs), don't inline them — return a
   **count + a summary + a follow-up tool**: `recent_orders_count: int`,
   `last_order_summary: str`, and a separate `list_customer_orders(cursor)` the
   agent calls only if it needs more (OP-6 pagination).
3. For genuinely large text blobs the agent must read, store them and return a
   reference/handle the agent can fetch on demand, rather than inlining.
4. Set a hard per-call byte budget in the wrapper; if the shaped output still
   exceeds it, that's a signal the tool is doing too much — split it.

**Verdict**: Expose a thin reason/act slice; demote bulk to follow-up paginated
tools or references. The tool's job is to give the model *enough to decide the
next step*, not the whole record.

### DC-3 · Async / long-running API (submit job → poll): one tool or two?

**Scenario**: A report API: `POST /reports` returns a `job_id`; you poll
`GET /reports/{job_id}` until `status=done` (can take minutes).

**Options**:
- **A. One tool that blocks** — `generate_report()` submits then polls
  internally until done. Simple mental model for the model, but holds the agent
  (and its timeout) hostage for minutes, and a single per-attempt HTTP timeout
  can't cover it.
- **B. Two tools** — `submit_report() -> job_id` and
  `check_report(job_id) -> status|result`. The agent submits, does other work,
  polls. Robust to long waits; matches the agent loop; but the model must
  remember to poll.

**Decision rule**:
1. If the job reliably finishes in **seconds** and well under one HTTP timeout →
   one blocking tool (A) with internal bounded poll + jittered backoff (OP-5).
2. If it can run **minutes+**, or you need the agent to stay responsive →
   two tools (B). Make `check_report` return a clear `status` enum so the model
   knows whether to wait, and bound the agent's poll count (bounded-loop skill).
3. Either way, the *submit* call is a mutation — give it an idempotency key
   (OP-9) so a retried submit doesn't queue two jobs.

**Verdict**: Match the tool shape to the latency. Sub-second → hide the poll
inside one tool; minutes → split, and make the agent's polling explicit and
bounded.

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

| # | Anti-pattern | Symptom | Fix |
|---|---|---|---|
| AP-1 | **1:1 endpoint→tool mapping** | 40+ near-identical tools; model picks wrong one | Triage to intents (OP-1); auto-gen 1:1 "under-performs hand-curated" `[stainless/mcp]` |
| AP-2 | **Raw JSON dump to the LM** | Context bloat, hallucinated field names | Output model with only reason/act fields (OP-7) |
| AP-3 | **Secrets in description or args** | API key leaks into traces/logs | Auth inside wrapper from env/secret store (OP-4) |
| AP-4 | **No rate-limit / retry handling** | One `429` or blip kills the whole run | Timeout + jittered retry, honor `Retry-After` (OP-5) |
| AP-5 | **Unbounded pagination auto-loop** | Token blowout / OOM on big lists | Return page + cursor; bounded loop only (OP-6) |
| AP-6 | **Procedural description** ("first call X, then Y") | Model treats the tool as a script, mis-sequences | Describe *when* to call, not *how*; one intent per tool `[oai/prompting]` |
| AP-7 | **Free-form `body: str` / `params: dict`** | Model fills the wire format wrong | Typed flattened schema (OP-3) |
| AP-8 | **Raising stack traces to the model** | Model parrots Python tracebacks at the user | Structured `{error, retryable, hint}` (OP-8) |

**Hard boundaries — this skill is the wrong frame when:**
- The API is already an MCP server / first-class SDK with model-friendly
  surface — just connect it; don't re-wrap.
- The "tool" has no network I/O — write a plain typed function tool.
- You own and can change the upstream API — fix the *API* to be agent-ready
  (intent endpoints, machine-readable errors `[serghei/agent-ready]`) rather than
  papering over it in a wrapper.
- Side-effect safety is the *core* problem (exactly-once, dedup store) — that's
  the **`llm-tool-idempotency`** skill; this skill only flags the hook (OP-9).

---

## 7. 跨框架对照 (Cross-Framework Mapping)

The wrapper logic — triage, naming, typed schema, auth, retry, pagination,
shaping, errors — is **framework-independent**. The only framework-specific layer
is the *registration* call. One Pydantic v2 model feeds all five targets via
`model_json_schema()` and `model_validate()`.

| Framework | Definition shape | Schema source | Error surface | Notes |
|---|---|---|---|---|
| **OpenAI function calling** | `tools=[{type:"function", function:{name, description, parameters}}]` | `parameters` = JSON Schema | Return error JSON as the tool result | "Assume there are several [calls]" — wrappers must be parallel-safe `[oai/fc]` |
| **Anthropic `tool_use`** | `tools=[{name, description, input_schema}]` | `input_schema` = JSON Schema | `tool_result` with `is_error:true` keyed by `tool_use_id` | Correlate response to request via `tool_use_id` `[anthropic/tooluse]` |
| **MCP HTTP server** | `@mcp.tool()` (FastMCP) | Inferred from type hints / Pydantic | Return structured error content | GET→resource, mutate→tool split `[gun/mcp]`; don't auto-gen 1:1 `[stainless/mcp]` |
| **LangChain / LangGraph** | `@tool` or `StructuredTool` with `args_schema` | Pydantic `args_schema` | `ToolException` → LM-visible string `[lc/structured]` | Type hints required; docstring is the description `[lc/tools]` |
| **CrewAI** | subclass `BaseTool`, implement `_run`, set `args_schema` | Pydantic `args_schema` | Return string; weak built-in error capture | Per-agent scoping: shared *definition*, per-agent *binding* `[crewai/tools]` |

Two cross-framework heuristics carried in from the sibling SOPs:

- **Per-step / per-agent tool scoping** (from CrewAI + OpenAI `allowed_tools`):
  give each agent/step only the tools its role needs. Fewer tools = better
  selection and less context `[oai/tools]` `[crewai/tools]`. A wide wrapped API
  should still be *scoped* per agent, not bound wholesale.
- **Tools are functions, not chains** (from LangGraph): the wrapper does one
  thing and returns; orchestration (retries across tools, branching, HITL) lives
  in the graph/crew, not inside the tool. Keep the wrapper pure and bounded.

---

## 附录: 引用速查 (Citation Index)

Short tags → full sources in `references/R1-source-evidence.md`:

- `[oai/fc]` = developers.openai.com/api/docs/guides/function-calling
- `[oai/tools]` = developers.openai.com/api/docs/guides/tools (`allowed_tools`)
- `[oai/prompting]` = community.openai.com/t/prompting-best-practices-for-tool-use-function-calling/1123036
- `[anthropic/tooluse]` = docs.anthropic.com/en/docs/build-with-claude/tool-use
- `[lc/tools]` = docs.langchain.com/oss/python/langchain/tools
- `[lc/structured]` = blog.langchain.com/structured-tools/
- `[crewai/tools]` = docs.crewai.com/en/concepts/tools
- `[mcp/spec]` = modelcontextprotocol.io/specification
- `[gun/mcp]` = gun.io/ai/2025/05/wrap-existing-api-with-mcp/
- `[stainless/mcp]` = stainless.com/mcp/from-rest-api-to-mcp-server/
- `[northflank/mcp]` = northflank.com/blog/how-to-build-and-deploy-a-model-context-protocol-mcp-server
- `[apxml/schema]` = apxml.com/.../tool-input-output-schemas
- `[apxml/rate]` = apxml.com/.../api-rate-limits-retries-tools
- `[boldsign/retry]` = boldsign.com/blogs/api-retry-mechanism-how-it-works-best-practices/
- `[getknit/rate]` = getknit.dev/blog/10-best-practices-for-api-rate-limiting-and-throttling
- `[techops/rest]` = techopsasia.com/blog/rest-api-design-idempotency-pagination-security
- `[stripe/idem]` = stripe.com/docs/api/idempotent_requests
- `[mighty/fault]` = mightybot.ai/blog/fault-tolerant-ai-agent-pipelines/
- `[zuplo/agent-ready]` = zuplo.com/learning-center/api-readiness-gap-agent-callable-apis
- `[serghei/agent-ready]` = sergheipogor.medium.com/how-to-make-your-api-agent-ready-...
- `[medium/velorum]` = medium.com/@1nick1patel1/tool-schemas-the-quiet-superpower-of-agents
- `[arxiv/toolnet]` = arxiv.org/pdf/2403.00839 (ToolNet, Liu et al. 2024)
