# R1 · Source Evidence

Every load-bearing claim in `SKILL.md` traced to its source. Format:
**Claim → Source → Quote** (or paraphrase where the source is structural, not
a literal sentence). Citation tags match the inline tags in SKILL.md §附录.

> Verification note: the quotes below are reproduced from the cited sources as
> referenced by SKILL.md. Where a tag points at a structural fact (an API's
> behaviour, a SQL clause's semantics) rather than a quotable sentence, the
> entry says so and points at the canonical doc page. Verify against the live
> URL before acting on a high-blast-radius change.

---

## C1 · "Framework resume re-runs the *entire* node body" (`[langgraph/gotchas]`)

- **Claim** (SKILL.md §2.1 #2, §3 Step-anchor, §5 Case 1, §6, §7): LangGraph,
  on resume from an `interrupt()`, re-executes the whole node function from the
  top — so code *before* the interrupt (including side effects) runs again.
- **Source**: LangGraph cheatsheet / FAQs-gotchas —
  `https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/`
  Mirrored in the sibling skill `output/langgraph-sop-skill/SKILL.md` Case 4.
- **Quote (sibling SOP, Case 4, sourced from the cheatsheet)**:
  > "On resume, the card was charged *twice* because resuming a thread
  > 're-runs the entire node function'."
  > — `output/langgraph-sop-skill/SKILL.md` §困境决策案例 Case 4
- **Quote (sibling SOP anti-pattern, same source tag `[cheatsheet/gotchas]`)**:
  > "Don't put side effects before `interrupt()`. On resume, the node body
  > re-runs from the top."
  > — `output/langgraph-sop-skill/SKILL.md` §反模式与边界
- **Cross-check**: the sibling skill's `intermediate/operation_candidates.json`
  records this under DC-4 ("Side effects before interrupt() re-execute on
  resume", source = the cheatsheet URL) and OP-12 ("Idempotency belt for
  resumable nodes"). Internally consistent.

---

## C2 · "Stripe caches the first response keyed by the idempotency key" (`[stripe/idempotency]`)

- **Claim** (SKILL.md §2.1 #1, §2.3, §3 Step 4, OP-1, OP-2): A client generates
  an idempotency key (typically a UUIDv4), sends it as the `Idempotency-Key`
  HTTP header; the server saves the first response and returns it on retry —
  no second charge. Window is ~24 hours.
- **Source**: Stripe API docs — Idempotent requests —
  `https://docs.stripe.com/api/idempotent_requests`
- **Quote (as cited in SKILL.md OP-1 Evidence)**:
  > "Stripe's idempotency works by saving the resulting status code and body
  > of the first request made for any given idempotency key, regardless of
  > whether it succeeded or failed."
- **Supporting facts from the same page** (paraphrase): keys are passed via the
  `Idempotency-Key` header; Stripe recommends V4 UUIDs; results are stored for
  24 hours; a request reusing a key with a *different* payload returns an error.

---

## C3 · "Reusing a key with different args returns 409 `idempotency_key_in_use`" (`[stripe/idempotency]`)

- **Claim** (SKILL.md §3 Step 5, §5 Case 3): Same key + different request
  payload is a caller bug; Stripe surfaces it rather than silently deduping.
- **Source**: Stripe API docs — Idempotent requests (same page as C2).
- **Paraphrase of documented behaviour**: Stripe returns an error when an
  idempotency key is reused with request parameters that do not match the
  original request; concurrent requests with the same key while the first is
  in flight also error. SKILL.md labels this `409 Conflict` /
  `idempotency_key_in_use` — the load-bearing point (same-key-different-args =
  surface-as-bug, do not absorb) is faithful to the doc.
- **Note for verifier**: Stripe's docs are the authority on the exact HTTP
  status and error code string; confirm against the live page before encoding
  the literal `409` / `idempotency_key_in_use` into production error handling.

---

## C4 · "AWS SQS FIFO dedup window default is 5 minutes" (`[aws/idempotency-whitepaper]`)

- **Claim** (SKILL.md §3 Step 4, §7 table): SQS message deduplication uses a
  ~5-minute window by default; key carrier is `MessageDeduplicationId`.
- **Source**: AWS SQS FIFO documentation — Amazon SQS message deduplication.
  Canonical page:
  `https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html`
  (referenced in SKILL.md under the broader `[aws/idempotency-whitepaper]` tag).
- **Paraphrase of documented behaviour**: For FIFO queues, the deduplication
  interval is 5 minutes — a message with a `MessageDeduplicationId` seen within
  the prior 5 minutes is accepted but not delivered again. This grounds the
  "5 minutes (default)" cell in SKILL.md §7 and the "AWS SQS exactly-once"
  reference.
- **General idempotency-API guidance**: AWS Architecture Blog "Building
  idempotent APIs" and the Powertools-for-Lambda idempotency module document
  the server-side dedup-table pattern (persist key → cached response), which
  SKILL.md generalises as OP-2.

---

## C5 · "S3 conditional writes (`If-None-Match: *`) make a PUT a no-op-or-412" (`[aws/s3-conditional]`)

- **Claim** (SKILL.md §2.4 table, OP-3): Content-addressed write — compute
  `sha256(content)` as the object key, conditional PUT returns 412 on a second
  write of the same key.
- **Source**: AWS S3 User Guide — Conditional writes —
  `https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html`
- **Paraphrase of documented behaviour**: S3 supports conditional PUT using
  `If-None-Match: *`, which fails the request (HTTP 412 Precondition Failed) if
  an object already exists at that key — enabling write-once / idempotent-create
  semantics without a dedup table.

---

## C6 · "PostgreSQL `INSERT … ON CONFLICT … DO NOTHING` deduplicates atomically" (`[pg/insert]`)

- **Claim** (SKILL.md §2.4 table, §3 Step 2/Step 6, OP-2, OP-4, §6
  anti-pattern "check-then-insert has a race"): A DB-enforced unique constraint
  plus `ON CONFLICT DO NOTHING` removes the application-side race window.
- **Source**: PostgreSQL docs — INSERT, ON CONFLICT clause —
  `https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT`
- **Paraphrase of documented behaviour**: `ON CONFLICT DO NOTHING` causes the
  insert to do nothing (no error) when it would violate a unique or exclusion
  constraint; `RETURNING` yields rows only for rows actually inserted — so an
  empty result reliably signals "duplicate". Equivalents: MySQL `INSERT IGNORE`,
  SQLite `INSERT OR IGNORE`.

---

## C7 · "Temporal warns about non-determinism / activity idempotency on replay" (`[temporal/idempotency]`)

- **Claim** (SKILL.md §2.1 #2, OP-5, OP-8, §7 lesson 3): Durable-execution
  frameworks still replay/re-run code; activities must be idempotent. Temporal
  is the canonical reference for activity-level idempotency.
- **Source**: Temporal docs — Develop / Activities — Idempotency —
  `https://docs.temporal.io/develop/activities#idempotency`
- **Paraphrase of documented guidance**: Temporal Activities can execute more
  than once (retries, worker failures), so Activity code should be idempotent;
  Temporal recommends an idempotency key derived from deterministic Workflow
  inputs. This supports SKILL.md's claim that "frameworks promising durable
  execution still re-run code" and that idempotency is an orthogonal axis.

---

## C8 · "The saga pattern handles compensatable, non-idempotent operations" (`[microservices/saga]`)

- **Claim** (SKILL.md §2.4 table row 3, OP-5, §6 hard-boundaries table): When a
  downstream API has no native idempotency but the effect can be undone, use a
  saga: record intent → perform → compensate-on-duplicate / reconcile.
- **Source**: microservices.io — Saga pattern —
  `https://microservices.io/patterns/data/saga.html`
- **Paraphrase**: A saga is a sequence of local transactions where each step
  has a compensating transaction that undoes its effect, used to maintain data
  consistency across services without distributed locks. SKILL.md adapts the
  "record intent, then perform, then compensate" shape to single-tool dedup.

---

## C9 · "CrewAI tools shared across agents can be invoked multiple times" (`[crewai/tools]`)

- **Claim** (SKILL.md §6 framework pitfalls): Tools shared across agents in a
  crew can be invoked by multiple agents in one run; per-agent tool binding +
  tool-layer dedup prevents one agent undoing another's work.
- **Source**: CrewAI docs — Tools — `https://docs.crewai.com/en/concepts/tools`
- **Paraphrase**: CrewAI lets agents share or be individually assigned tools;
  the per-agent tool binding pattern is documented. The duplication risk
  (multiple agents → multiple invocations) is the operational inference
  SKILL.md draws; the dedup remedy is OP-8.

---

## C10 · "MCP does not mandate at-most-once / idempotency" (no external tag; spec-level)

- **Claim** (SKILL.md §5 Case 4, §6 pitfalls, OP-7): The Model Context Protocol
  treats tool invocation as request/response and does not guarantee
  at-most-once delivery; retries are the client's decision, so dedup must be
  built into the tool boundary (server side).
- **Source**: Model Context Protocol specification —
  `https://modelcontextprotocol.io/specification`
- **Status**: This is an *absence* claim — the protocol does not specify
  idempotency, therefore the server must. SKILL.md states this explicitly and
  does not over-claim a built-in guarantee. Treat as a design inference from
  the spec's request/response framing, not a quoted sentence.

---

## C11 · Model duplicate-emission of `tool_call_id` / `tool_use_id` (OpenAI / Anthropic)

- **Claim** (SKILL.md §2.1 #3, §6 framework pitfalls): Streaming responses can
  occasionally surface the same tool-call id twice, and a model may re-emit a
  tool call after context compaction; therefore the provider's per-emission id
  is a *signal*, not a safe idempotency key.
- **Source**: OpenAI tool-calling docs
  (`https://platform.openai.com/docs/guides/function-calling`) and Anthropic
  tool-use docs (`https://docs.anthropic.com/en/docs/build-with-claude/tool-use`).
- **Status**: SKILL.md flags duplicate emission as "rare but documented" and
  draws the safe conclusion (do not use `tool_call_id` / `tool_use_id` as the
  idempotency key). This is a conservative design stance; the load-bearing
  recommendation (caller-owned key, not provider id) does not depend on the
  exact frequency of duplicate emission.

---

## Cross-skill consistency check

The premise that anchors this skill — "frameworks that promise durable
execution still re-run node bodies on resume" — is the same fact the sibling
LangGraph SOP documents independently (Case 4, OP-12, DC-4). Both skills cite
the identical source (`sumanmichael.github.io/langgraph-cheatsheet`). The two
skills are mutually reinforcing and use the same idempotency-key-from-state
remedy. No contradiction found between this skill's OP-6 and the sibling's
OP-12.
