---
name: agentsop-state-reducer
description: |
  Tool skill for declaring reducers on LangGraph state keys so parallel writes
  merge instead of crashing. Activates whenever a coder agent designs a
  StateGraph with parallel branches, fan-out via Send, multi-agent topologies,
  or whenever a run raises `InvalidUpdateError: At key '<k>': Can receive only
  one value per step`. Encodes the rule "every state key is single-writer or
  has a reducer — nothing in between."
version: 0.1.0
---

# State Reducer · Tool Skill

> Scope: a single decision — for each state key, declare a reducer or
> guarantee single-writer. Out of scope: checkpointers, HITL, supervisor vs.
> swarm — see `langgraph-sop` for those.

---

## 1. 何时激活 (Activation Rules)

Activate when **any** trigger fires:

- The task involves a LangGraph `StateGraph`, `TypedDict`/`BaseModel` schema,
  or `Annotated[..., <reducer>]` typing.
- The graph has ≥1 of: parallel branches via static fan-out, `Send` API,
  multiple agents writing shared state, or a supervisor pattern where workers
  return concurrently.
- The run raises `langgraph.errors.InvalidUpdateError` — message looks like
  `At key 'messages': Can receive only one value per step. Use an Annotated key to handle multiple values.`
- The user pastes a state schema and asks "why does this crash on parallel?"
  or "do I need a reducer here?".
- The user is migrating a linear chain to a fan-out / map-reduce shape.

Do **not** activate if every key is written by exactly one node per superstep
(see §6: over-reducing single-writer keys is an anti-pattern).

---

## 2. 核心心智模型 (Core Mental Model)

**LangGraph state is either single-writer or has a reducer. Nothing in
between.**

When a node returns `{"k": v}`, LangGraph must decide how to merge `v` into
existing `state["k"]`. There are exactly two legal regimes:

1. **Single-writer / "set" semantics** (default, no `Annotated`). At most one
   node writes the key per superstep. The new value *replaces* the old.
   Two concurrent writers → `InvalidUpdateError`.
2. **Reducer / "merge" semantics**
   (`Annotated[T, reducer_fn]`). Any number of writers may write per
   superstep; LangGraph folds them via `reducer_fn(current, new)`.

The reducer is *commutative-enough* algebra that lets the engine schedule
parallel writes without you reasoning about interleavings. Three canonical
reducers cover ~90% of real graphs:

| Reducer | Type | Behaviour |
|---|---|---|
| `add_messages` (from `langgraph.graph.message`) | `list[BaseMessage]` | Append; **dedupe-and-update by message `id`** (in-place edit when IDs match) |
| `operator.add` | `list`, `int`, `float`, `str` | List concat / numeric sum |
| Custom `(curr, new) -> merged` | anything | Domain-specific merge (keep-latest, dedupe-by-id, LLM-summarise) |

> "Reducers are mandatory, not optional, for parallel execution."
> — `[cheatsheet/gotchas]`

The `add_messages` quirk that beginners miss: it is **not** plain append. If
a new message shares an `id` with one in state, it overwrites in place. This
is what makes HITL `interrupt() + edit-state` work — a human can edit the
last AI turn and resume.

The decision is per-key, not per-schema. A schema can mix freely: one key
single-writer, another with `add_messages`, another with `operator.add`.

---

## 3. SOP 工作流 (Agentic Protocol)

Run top-down for every new or modified state schema.

### Step 1 · Enumerate writers per key

For each key `k` in the state schema, list every node that returns `k` in its
update dict. Be paranoid: include nodes spawned via `Send`, subgraphs whose
output schema overlaps the parent, and any conditional branches.

### Step 2 · Classify each key

- **Single-writer-per-superstep** → leave un-annotated. Plain `k: T`.
- **Multi-writer in the same superstep** (parallel branches, fan-out workers,
  swarm handoffs) → **must** declare a reducer. Plain `k: T` will crash.
- **Sequential multi-writer** (different supersteps) — a reducer is
  *optional*: without one, each later write overwrites; with one, each write
  folds in. Choose based on intent.

> Decision gate: if you cannot answer "which nodes write this key?" in one
> sentence per key, stop and redraw the graph before continuing.

### Step 3 · Pick the reducer

Use the OP table in §4. Default ladder:

1. List of `BaseMessage` → `add_messages`.
2. Append-only list of anything else → `operator.add`.
3. Counter / accumulator → `operator.add`.
4. Anything weirder → write a custom reducer (§4 OP-5).

### Step 4 · Probe-test the parallel update

Before shipping, write a unit test that invokes the graph along the parallel
path with deterministic node outputs and asserts state matches expectation.
If the reducer is wrong (e.g., `operator.add` on dicts), this is where you
find out — not in production.

```python
def test_parallel_merge():
    out = graph.invoke({"items": []})
    assert sorted(out["items"]) == ["a", "b"]  # both workers' contributions present
```

### Step 5 · Document the contract

In a docstring on the TypedDict / Pydantic model, note for each non-default
key *why* it has a reducer. Future maintainers will thank you when they
refactor.

---

## 4. 操作模型 (Operation Models)

Each op: **Trigger → Action → Output**.

### OP-1 · Declare `add_messages` for a chat history key
- **Trigger**: state has a `messages: list[BaseMessage]` field; ≥1 of (HITL
  edit-state, multi-agent that all append turns, ReAct loop).
- **Action**:
  ```python
  from typing import Annotated, TypedDict
  from langchain_core.messages import AnyMessage
  from langgraph.graph.message import add_messages

  class S(TypedDict):
      messages: Annotated[list[AnyMessage], add_messages]
  ```
- **Output**: Concurrent message writes append; same-id writes overwrite
  in-place (enables HITL state edits).

### OP-2 · Declare `operator.add` for an accumulating list
- **Trigger**: parallel workers each emit zero or more items into a shared
  list (e.g., one chunk per worker in a map step).
- **Action**:
  ```python
  import operator
  from typing import Annotated, TypedDict

  class S(TypedDict):
      chunks: Annotated[list[str], operator.add]
  ```
- **Output**: Worker outputs concatenate in arbitrary order. Order is **not
  guaranteed** — if you need ordering, attach an index to each item and sort
  downstream.

### OP-3 · Declare `operator.add` for a counter
- **Trigger**: tracking retries, tool calls made, tokens spent across parallel
  branches.
- **Action**: `retries: Annotated[int, operator.add]`. Each node returns the
  *delta* (`{"retries": 1}`), not the new total.
- **Output**: Summed across writers.
- **Watch out**: returning the *new total* (`{"retries": state["retries"]+1}`)
  with `operator.add` double-counts. Always return deltas under `operator.add`.

### OP-4 · Single-writer key (no reducer)
- **Trigger**: exactly one node — usually the supervisor or a planner — owns
  the key.
- **Action**: leave it un-annotated: `current_task: str`.
- **Output**: Last (only) writer's value wins. If a second writer ever
  appears in the same superstep, the graph crashes loudly — which is the
  desired safety signal.

### OP-5 · Custom reducer — keep latest by timestamp
- **Trigger**: two parallel agents both write a `summary` field; you want
  whichever was generated more recently to win.
- **Action**:
  ```python
  from datetime import datetime

  Summary = dict  # {"text": str, "ts": datetime}

  def keep_latest(curr: Summary | None, new: Summary) -> Summary:
      if curr is None or new["ts"] >= curr["ts"]:
          return new
      return curr

  class S(TypedDict):
      summary: Annotated[Summary, keep_latest]
  ```
- **Output**: Newer timestamp survives regardless of which branch finished
  first.

### OP-6 · Custom reducer — dedupe by id
- **Trigger**: parallel retrievers each return a list of `{"id": ..., ...}`
  documents and the union should be de-duplicated.
- **Action**:
  ```python
  def dedupe_by_id(curr: list[dict], new: list[dict]) -> list[dict]:
      seen = {d["id"]: d for d in (curr or [])}
      for d in new:
          seen[d["id"]] = d   # later wins on collision
      return list(seen.values())

  class S(TypedDict):
      docs: Annotated[list[dict], dedupe_by_id]
  ```
- **Output**: Union without duplicates; collision policy is explicit and
  testable.

### OP-7 · Fix `InvalidUpdateError` post-mortem
- **Trigger**: error message
  `InvalidUpdateError: At key '<k>': Can receive only one value per step. Use an Annotated key to handle multiple values.`
- **Action**: locate the key `<k>` in the schema, identify the concurrent
  writers, then pick OP-1/2/3/5/6 based on key semantics.
- **Output**: Crash gone; merges behave as designed (verify with the §3
  Step 4 probe test).

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 · "Two agents write `messages` — what reducer?"
- **困境**: Supervisor pattern. Both the retrieval agent and the calculator
  agent emit `{"messages": [AIMessage(...)]}` in the same superstep when the
  supervisor fans out. Without a reducer → `InvalidUpdateError`. Naive
  `operator.add` works but loses HITL edit-in-place semantics.
- **约束**:
  - Need both concurrent appends *and* later HITL edits.
  - Message order across branches doesn't matter (each carries its
    own timestamp), but duplicates from retries must collapse.
- **决策步骤**:
  1. Reject `operator.add` — it concatenates blindly; retried messages with
     the same `id` would appear twice and break the chat UI.
  2. Use `add_messages` — explicitly designed for this. Append by default,
     overwrite in place when `id` matches `[lc-docs/messages]`.
  3. Generate stable `id`s in each agent (e.g., `uuid4()`) so dedupe is
     deterministic. If an agent retries, reuse the previous attempt's id.
- **结果**: Concurrent appends work, HITL "edit the last AI message and
  resume" works, retried turns dedupe themselves.
- **可提取的操作**: OP-1. **Whenever the key is a message list, `add_messages`
  is almost always the right answer — `operator.add` is a code smell on
  message lists.**

### Case 2 · "Two agents write `summary` — append-merge-or-replace?"
- **困境**: A research agent and a critic agent both produce a `summary`
  string for the same document, in parallel. With no reducer → crash. With
  `operator.add` on strings → concatenation glues them edge-to-edge (`"A.B."`
  not `"A. B."`). Neither is semantically right.
- **约束**:
  - Output must be a single coherent paragraph downstream.
  - Both agents have signal; neither is strictly authoritative.
  - Cost-sensitive: an extra LLM call is acceptable only once per document.
- **决策步骤**:
  1. Identify the *semantic* merge: not "concat", not "pick one", but
     "synthesise into one paragraph".
  2. Write a custom reducer that buffers contributions, then a downstream
     **single-writer** node calls the LLM once to merge:
     ```python
     def collect(curr: list[str] | None, new: str) -> list[str]:
         return (curr or []) + [new]

     class S(TypedDict):
         summary_drafts: Annotated[list[str], collect]
         summary: str   # single-writer, set by merge_node
     ```
  3. After the parallel branches join, a `merge_node` reads
     `state["summary_drafts"]`, runs one LLM call, writes
     `{"summary": "..."}` (single-writer, no reducer needed).
- **结果**: Crash gone; merge logic is explicit, testable, costs exactly one
  extra LLM call.
- **可提取的操作**: **When parallel writers don't produce algebraically
  mergeable values, don't force a reducer — collect into a list with
  `operator.add` / a custom collector, then merge in a single-writer node
  downstream.** Reducers are for trivial folds; LLM merges belong in nodes.

### Case 3 · "Fan-out via `Send` — do I still need a reducer?"
- **困境**: Routing function returns `[Send("worker", {"chunk": c}) for c in chunks]`.
  Each worker writes `{"results": [...]}`. Schema is
  `results: list[dict]` — does `Send` change reducer requirements?
- **约束**: Worker count is runtime-variable (1 to ~50).
- **决策步骤**:
  1. Recognize: `Send` IS parallel writing. All workers complete in the same
     superstep and merge back into parent state.
  2. Without `Annotated[list[dict], operator.add]` on `results` → crash on
     the *first* run where >1 worker is spawned. (Schema looks fine in tests
     with chunks=[c1] — fails in prod with chunks=[c1,c2].)
  3. Apply OP-2: `results: Annotated[list[dict], operator.add]`.
- **结果**: Map-reduce works at any cardinality.
- **可提取的操作**: **`Send` ≡ parallel writers, always. Any state key a
  Send-target worker writes must have a reducer, even if the static graph
  topology "looks" sequential.**

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

- **AP-1 · Ignoring the reducer until it crashes in prod.** The schema looks
  fine; tests pass with 1 worker; the first 2-chunk request in production
  raises `InvalidUpdateError`. *Fix*: enumerate writers per key during
  design (§3 Step 1), not after the page.

- **AP-2 · `add_messages` on non-message lists.** It calls `convert_to_messages`
  internally and will either raise or silently corrupt your data when items
  aren't `BaseMessage` subclasses. *Use `operator.add` or a custom reducer
  for `list[dict]`, `list[str]`, `list[Document]`.*

- **AP-3 · Over-reducing single-writer keys.** Declaring
  `Annotated[str, lambda a,b: b]` "just in case" on a key only the supervisor
  writes is noise — and worse, it *hides* future bugs by silently accepting
  a second writer that should have raised. *Leave single-writer keys
  un-annotated; let the engine surface accidental concurrency.*

- **AP-4 · Returning the new total under `operator.add`.** With
  `retries: Annotated[int, operator.add]`, returning
  `{"retries": state["retries"] + 1}` adds the *new total* to the old —
  double-counting. *Return the delta (`{"retries": 1}`).*

- **AP-5 · Forgetting that `Send` is parallel.** See Case 3. Any key written
  by a Send-target is a parallel-write key.

- **AP-6 · Relying on reducer order.** Reducers see writes in implementation-
  defined order. `add_messages` and `operator.add` are order-insensitive for
  the *set* of items but the resulting list order is not guaranteed across
  runs. *If you need a canonical order, sort downstream with an explicit key
  (timestamp, branch index, etc.).*

- **AP-7 · Stateful / non-pure reducers.** Reducers must be pure functions
  of `(current, new)`. Reading external state (DB, time.now() inside the
  reducer) breaks checkpoint replay and time-travel debugging. *Push side
  effects into nodes, never reducers.*

- **AP-8 · Mutating `curr` in place inside a custom reducer.** Return a new
  value. Mutating the existing object can corrupt earlier checkpoints that
  share the reference. *Always construct and return a fresh container.*

**Hard boundary**: reducers are a *write-merge* mechanism, not a
*read-consistency* mechanism. If you need transactional read-modify-write
across parallel nodes (e.g., "increment counter only if branch A succeeded"),
that's a routing problem — sequence the nodes, don't smuggle it into a
reducer.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

The reducer pattern is not LangGraph's invention — it's a re-application of
two well-known patterns. Recognizing the lineage helps onboard fast.

| Framework | Analog | Same idea | Different |
|---|---|---|---|
| **LangGraph** | `Annotated[T, reducer]` | Pure `(curr, new) -> merged` fold over parallel writes per superstep | Per-key declaration; runs inside a checkpointable state machine |
| **Redux / Elm** | `reducer(state, action) -> state` | Pure fold over an action stream, single source of truth | Single root reducer over a stream; LangGraph has per-key reducers over a superstep set |
| **CRDTs (Conflict-Free Replicated Data Types)** | G-Counter, OR-Set, LWW-Register | Commutative+associative merge of concurrent writes from distributed replicas | CRDTs assume eventually-consistent replicas; LangGraph reducers run inside one process at superstep boundaries — no network partitions, but the algebra rhymes |
| **Pregel / BSP** | message combiners between supersteps | Merge multiple incoming messages per vertex per superstep | LangGraph's direct ancestor — `add_messages` is literally a combiner |
| **CrewAI** | none (no shared typed state) | — | Task outputs flow sequentially via context; no parallel write merge to declare. *That's why CrewAI is simpler — and why it can't express what LangGraph reducers express.* |
| **AutoGen** | conversation log | Append-only message history | Single ordered log, not a typed multi-key state — no need for per-key reducers, but no parallel-write-on-typed-fields either |

The Redux insight that transfers cleanly: **reducers must be pure, and that
purity is what enables replay/time-travel.** LangGraph's checkpoint replay
relies on exactly this. If you've internalised Redux discipline, the
LangGraph reducer rules are the same rules with a graph-shaped scope.

The CRDT insight that transfers cleanly: **commutative merge frees you from
reasoning about order.** `operator.add` on lists isn't strictly commutative
(`[a]+[b] != [b]+[a]` as lists), but you should *treat it as if it were* and
sort downstream when order matters. Designing reducers to be
order-insensitive is the cheapest way to keep parallel graphs sane.

---

## 附录: 关键引用 (Key Citations)

- `[cheatsheet/gotchas]` = sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/
  — "Reducers are mandatory, not optional, for parallel execution."
- `[lc-docs/messages]` = docs.langchain.com/oss/python/langgraph/ — `add_messages` "If a message with the same ID already exists, it updates that message in place rather than duplicating it."
- `[aipractitioner/scaling]` = aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization
  — parallel branch failure semantics.
- Sibling skill: `langgraph-sop` for the full LangGraph SOP (state schema
  design, checkpointers, HITL, multi-agent topologies). This skill is the
  zoom-in on reducers only.
