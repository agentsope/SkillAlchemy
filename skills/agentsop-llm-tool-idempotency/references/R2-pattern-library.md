# R2 · Pattern Library

Concrete, copy-adaptable idempotency-key patterns referenced by SKILL.md §4.
Each pattern: **when → sketch → the key invariant**. Code is illustrative
pseudocode/Python — adapt the store, error types, and TTLs to your stack.

The one rule that every pattern below obeys:

> The idempotency key is **born in the caller's persisted state before the side
> effect**, and the *same logical operation on retry produces the same key*.
> A key minted inside the tool, or from `now()`, defeats every pattern here.

---

## P1 · HTTP header idempotency key (Stripe pattern) — maps to OP-1

**When**: the downstream API natively supports idempotency keys (Stripe,
Square, modern PayPal, Adyen, Anthropic Files, AWS client tokens).

```python
def charge_card(state, amount, currency, customer):
    # Key from state, generated ONCE, persisted before the call.
    key = state.get("charge_key")
    if key is None:
        key = str(uuid.uuid4())
        state["charge_key"] = key
        persist(state)                      # checkpoint BEFORE the side effect

    # SDK kwarg form (preferred); equivalent to Idempotency-Key header.
    resp = stripe.PaymentIntent.create(
        amount=amount, currency=currency, customer=customer,
        idempotency_key=key,                # <- the whole mechanism
    )
    return {"result": resp, "was_replay": resp.get("livemode") is not None}
```

Raw-HTTP form:

```http
POST /v1/payment_intents HTTP/1.1
Idempotency-Key: 5f3a...uuid4
Content-Type: application/x-www-form-urlencoded

amount=2000&currency=usd
```

**Invariant**: the client retries with the *same* key (do not mint a new key on
each HTTP retry). Same key + different body → server returns a conflict; treat
that as a caller bug, not a duplicate to absorb. Source: `[stripe/idempotency]`.

---

## P2 · Dedup table at the tool-call layer — maps to OP-2

**When**: an internal/own API with no native idempotency, or a multi-step write.

```sql
CREATE TABLE tool_call_dedup (
    key         TEXT PRIMARY KEY,
    tool_name   TEXT NOT NULL,
    args_hash   TEXT NOT NULL,
    result      JSONB,
    status      TEXT NOT NULL,            -- 'pending' | 'completed'
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

```python
def dedup_call(key, tool_name, args, do_side_effect):
    args_hash = sha256(canonical_json(args))
    # Atomic claim: only the first caller inserts a row.
    row = db.execute("""
        INSERT INTO tool_call_dedup(key, tool_name, args_hash, status)
        VALUES (%s, %s, %s, 'pending')
        ON CONFLICT(key) DO NOTHING
        RETURNING key
    """, (key, tool_name, args_hash)).fetchone()

    if row is None:                        # someone already claimed this key
        existing = db.execute(
            "SELECT result, status, args_hash FROM tool_call_dedup WHERE key=%s",
            (key,)).fetchone()
        if existing.args_hash != args_hash:
            raise IdempotencyConflict(key) # same key, different args = bug
        if existing.status == "pending":
            raise InFlight(key)            # caller must back off / poll
        return {"result": existing.result, "was_replay": True}

    result = do_side_effect()             # we won the claim: run it once
    db.execute("UPDATE tool_call_dedup SET result=%s, status='completed' "
               "WHERE key=%s", (Json(result), key))
    return {"result": result, "was_replay": False}
```

**Invariant**: the `ON CONFLICT` insert is the *atomic claim* — no check-then-act
race. `pending` means "in flight, do not call again". Source:
`[stripe/idempotency]` (server-side generalisation), `[aws/idempotency-whitepaper]`.

---

## P3 · Content-hash write-or-update (content-addressed) — maps to OP-3

**When**: the object's identity *is* its content (artifacts, immutable records,
derived files).

```python
def write_artifact(content: bytes, bucket: str):
    key = hashlib.sha256(content).hexdigest()      # identity = content
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=content,
                      IfNoneMatch="*")              # conditional create
        return {"key": key, "was_replay": False}
    except s3.exceptions.PreconditionFailed:        # HTTP 412: already exists
        return {"key": key, "was_replay": True}     # identical bytes already there
```

**Invariant**: identical content → identical key → the second write is a no-op
(412), so no dedup table is needed. This is idempotency-by-construction (the
primitive behind Git and IPFS). Source: `[aws/s3-conditional]`.

---

## P4 · Transaction `INSERT … ON CONFLICT` — maps to OP-4

**When**: the side effect is a single-row insert into a table you own.

```sql
ALTER TABLE messages ADD CONSTRAINT uq_msg_idem UNIQUE (idempotency_key);

INSERT INTO messages (idempotency_key, recipient, body)
VALUES ($1, $2, $3)
ON CONFLICT (idempotency_key) DO NOTHING
RETURNING id;
```

```python
row = db.execute(sql, (key, recipient, body)).fetchone()
inserted = row is not None                # empty result == duplicate no-op
```

**Invariant**: the database's unique constraint does the dedup atomically;
an empty `RETURNING` set is a reliable "this was a duplicate" signal — no
application race window. Equivalents: MySQL `INSERT IGNORE`, SQLite
`INSERT OR IGNORE`. Source: `[pg/insert]`.

---

## P5 · Saga compensation — maps to OP-5

**When**: no native idempotency, but the effect is reversible (refund,
retraction, correction).

```python
def transfer_with_saga(state, key, amount, payee):
    intent = db.upsert_intent(key=key, status="pending",
                              payload={"amount": amount, "payee": payee})
    if intent.status == "completed":
        return {"external_id": intent.external_id, "was_replay": True}
    if intent.status == "pending" and intent.in_flight():
        raise InFlight(key)               # another worker is mid-call; back off

    try:
        ext = bank_api.transfer(amount=amount, payee=payee)   # not idempotent
        db.complete_intent(key, external_id=ext.id)
        return {"external_id": ext.id, "was_replay": False}
    except Timeout:
        # leave status='pending'; reconciler resolves it later
        raise

def reconcile():                          # scheduled job
    for intent in db.pending_past_ttl():
        match = bank_api.lookup(business_ref=intent.business_ref)
        if match:
            db.complete_intent(intent.key, external_id=match.id)   # it happened
        else:
            db.fail_intent(intent.key)                             # safe to retry
        # if duplicate is later discovered: issue compensating refund
```

**Invariant**: intent is recorded transactionally *before* the external call;
duplicates are caught by `status`, and the irreducible timeout-ambiguity is
resolved by a reconciliation job querying a stable business identifier — never
by blindly re-calling. Source: `[microservices/saga]`, `[temporal/idempotency]`.

---

## Choosing between patterns

| Situation | Pattern | OP |
|---|---|---|
| Downstream API has a native idempotency key | P1 | OP-1 |
| Internal/own multi-step write, no native key | P2 | OP-2 |
| Object identity is its content (artifact/blob) | P3 | OP-3 |
| Single-row insert into your DB | P4 | OP-4 |
| No native key, effect is compensatable | P5 | OP-5 |

Cross-cutting (apply on top of any pattern): persist the key to durable agent
state *before* the side effect (OP-6 for LangGraph node bodies, OP-8 for
generic orchestrators), require an `idempotency_key` field on side-effectful
MCP tool schemas (OP-7), and always return `was_replay` so the LM does not
re-attempt a logically-completed action.
