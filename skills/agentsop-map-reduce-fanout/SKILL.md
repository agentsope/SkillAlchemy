---
name: agentsop-map-reduce-fanout
version: 0.1.0
description: |
  Decision protocol for the map-reduce / dynamic fan-out pattern in LM
  pipelines — "given list L, run f(item) for each item in parallel, then
  combine". Activates when the coder agent is about to process N items with N
  LM calls (per-doc summarize, per-query retrieve, per-candidate rank,
  parallel tool fan-out). Encodes the *when*, *how many at once*, *what to
  do when one fails*, and *how to reduce* — not the API of any single
  framework. Cross-framework: LangGraph `Send`, CrewAI parallel tasks /
  Flow, `asyncio.gather`, `ThreadPoolExecutor`, LlamaIndex batch retrieval.
---

# Map-Reduce / Dynamic Fan-Out · SOP

> Pattern: `results = reduce(combine, parallel_map(f, L))` where `f` is one
> or more LM calls. The *only* reason to fan out is that latency or
> throughput matters more than the cost of doing it. The *only* reason to
> fan in is that the consumer wants one answer, not N.

> Source posture: claims grounded in primary docs and 2026 production
> write-ups, cited inline with short tags resolved in the citation index.

---

## 1. 何时激活 (Activation Rules)

Activate this skill when **any** of these is true:

- The task description contains "for each X, do Y" where Y involves an LM
  call, a retriever hit, or any I/O-bound step costing >100ms.
- The coder is about to write a `for item in items: result = llm(item)` loop
  and the items are independent (no item depends on the previous result).
- The codebase already has `asyncio.gather(...)`, `ThreadPoolExecutor(...)`,
  `Send(...)`, `Process.hierarchical` parallel branches, or
  `crew.kickoff_for_each(...)` and the question is *how* to use them safely.
- The user mentions any of: "summarize N docs", "rank top-K candidates",
  "vote across M models", "ensemble", "parallel agents", "multi-query
  retrieval", "scatter-gather", "fan out".
- A LangGraph graph is throwing `InvalidUpdateError` on a key two parallel
  branches write to (see OP-3 cross-link in skill `O5 state-reducer`).
- A LangGraph `Send`-based fan-out is hitting `GRAPH_RECURSION_LIMIT` or
  rate-limit 429s because all N workers fired at once
  `[aipractitioner/scaling]`.

Do **not** activate when:

- N is statically 1 or 2 (just write the calls inline; setup cost ≥ win).
- Items depend on each other (sequential reasoning, chain-of-thought
  across docs) — fan-out destroys the dependency.
- The downstream code only needs the *first* successful answer — use
  `asyncio.wait(..., return_when=FIRST_COMPLETED)`, not gather.
- The "fan-out" is into a single batched API call (e.g., embedding 100
  strings in one OpenAI request). That's a batched single call, not
  map-reduce. Use it; it's cheaper.

---

## 2. 核心心智模型 (Core Mental Model)

**Fan out for latency, fan in for coherence.**

The whole protocol is two questions: *what runs concurrently?* and *how do
the answers merge?* Everything else — `Send`, `gather`, `Semaphore`,
reducers — is mechanics.

Three load-bearing concepts:

1. **The unit of fan-out is the item, not the call.** `f(item)` may itself
   be a multi-step LM workflow (retrieve → rerank → synthesize) — that is
   fine. What you parallelise is the *per-item function*. Don't confuse
   "parallel LM calls" with "parallel workflow instances". The latter is
   what `Send` and `gather(f(x) for x in L)` actually do
   `[deepwiki/mapreduce]`.

2. **Concurrency is bounded, never infinite.** Every external dependency
   (OpenAI/Anthropic API, your vector DB, your KV cache) has at least one
   of: RPM limit, TPM limit, connection-pool limit, GPU KV-cache budget.
   `asyncio.gather(*[call(x) for x in 100_items])` will *not* call 100
   things — it will fire 100, the API will 429 most, and you'll spend the
   next 20 minutes in retry-storm hell `[newline/asyncio-llm]`
   `[tianpan/structured-concurrency]`. The first thing you choose, before
   any code, is **N_concurrent**.

3. **The reducer determines the shape of the answer.** `concatenate` keeps
   all evidence (large output, no judgment); `summarize` collapses
   (information loss, smaller output); `vote / majority` picks one (lossy
   but decisive); `rank-top-K` selects the best few. Pick the reducer
   *before* you write the map — because the map's `expected_output` shape
   is dictated by the reduce.

The Pregel-lineage version of the same point: **a fan-out / fan-in is one
superstep**. Either it all succeeds and the reduce node runs, or one branch
fails and (in LangGraph) the whole superstep is discarded
`[aipractitioner/scaling]`. Your code must decide *before* fan-out which
semantics you want: atomic-or-nothing, or best-effort-with-holes.

---

## 3. SOP 工作流 (Standard Operating Protocol)

Walk this top-down. Each step has a decision gate.

### Step 1 · Confirm items are independent

Gate: can `f(item_i)` run without seeing `f(item_j)` for any `j ≠ i`?

If **no**, stop. You have a sequential or recursive problem masquerading
as map-reduce. Use a chain, or model the dependency explicitly (DAG,
beam search, etc.). Fan-out will silently drop the cross-talk.

### Step 2 · Estimate cost honestly

Before any code, multiply:

```
cost = N · cost_per_item   (in $, tokens, AND seconds_wall)
peak_rps = N_concurrent / mean_latency_per_item
```

Three numbers must fit inside three budgets:
- `cost_$` ≤ task budget
- `peak_rps` ≤ min(API RPM/60, vector-DB QPS, GPU concurrency)
- `peak_tps` ≤ API TPM / 60 — TPM is the silent killer: 50 parallel calls
  each with a 4k-token prompt instantly exceeds most providers' TPM even
  if RPM is fine `[newline/asyncio-llm]`.

If any budget is tight, **fan-out is the wrong tool**. Options: batch
calls into single API request (embeddings, reranking), reduce N (pre-filter
items), or accept sequential.

### Step 3 · Pick N_concurrent (the most important number in the file)

Default rubric:

| Constraint | Pick |
|---|---|
| API-bound (OpenAI/Anthropic) | `min(10, RPM/60 · target_latency_s)` — keep at most one "request-second" of headroom |
| Self-hosted vLLM/SGLang | Start at `num_kv_blocks / mean_prompt_blocks`; for most setups 8–32 |
| Vector DB retrieval | Provider QPS limit / 2 (leave headroom for other paths) |
| Mixed (LM + tool calls) | Constrain by the slowest dependency |
| No instrumentation yet | **Start at 5**. Always. Then measure. |

`N_concurrent` is enforced with `asyncio.Semaphore(N)` for asyncio,
`ThreadPoolExecutor(max_workers=N)` for sync, `max_concurrency` config in
LangGraph, `max_rpm` in CrewAI. Never rely on the framework's defaults.

### Step 4 · Decide the failure policy *before* writing the fan-out

Four canonical policies — pick one explicitly:

| Policy | When to use | How |
|---|---|---|
| **Abort-all** | One missing item invalidates the answer (legal review, regulated workflows) | `asyncio.gather(*, return_exceptions=False)` — first exception cancels siblings. In LangGraph this is the *default* superstep semantic `[aipractitioner/scaling]`. |
| **Best-effort** | Concatenate / summarize use cases — partial is OK | `asyncio.gather(*, return_exceptions=True)` then filter; or per-task `try/except` returning a sentinel |
| **Retry-then-skip** | API flakiness is the main failure | Wrap `f` with tenacity / backoff: 3 attempts × exponential, then sentinel |
| **Quorum** | Vote / ensemble — need at least K of N | `asyncio.as_completed`, collect K, cancel the rest |

Anti-pattern: making this decision implicitly. The single most common
production bug in this pattern is "I assumed `gather` would skip failures"
or "I assumed one failed branch wouldn't kill the rest" — both are wrong
defaults `[aipractitioner/scaling]` `[newline/asyncio-llm]`.

### Step 5 · Pick the reducer

| Reducer | Shape change | Cost | When to use |
|---|---|---|---|
| `concatenate` | `[A, B, C]` → `"A\nB\nC"` | None | Downstream LM can handle big context; you want full evidence |
| `summarize` (LM call) | `[A, B, C]` → `"abc"` | +1 LM call | Output must fit in a final prompt; lossy by design |
| `vote / majority` | `[A, B, A]` → `A` | None | Self-consistency / ensemble agreement |
| `rank-top-K` | `[(a,0.9), (b,0.4), (c,0.7)]` → `[a, c]` | None | Multi-query retrieval, reranking |
| `merge-dedupe` | overlapping lists → set | Cheap | Multi-query retrieval, multi-source enrichment |
| `tree-reduce` | binary `combine(x, y)` recursively | log₂(N) LM calls | When pairwise merging is meaningful (summary-of-summaries) |

Choose by asking: *what does the next node consume?* The reducer is just
"adapt the fan-out shape to the consumer's input shape."

### Step 6 · Set per-call timeout *and* total wall-clock budget

Two independent timeouts:

- **Per-call**: `asyncio.wait_for(call, timeout=30)` — protects against
  one stuck call holding a semaphore slot forever (the canonical "100 items,
  99 done in 5s, the whole job blocked 5 min on item 73"). Default 30s.
- **Total wall**: `asyncio.wait_for(gather(...), timeout=N · mean + 3σ)`
  — protects against pathological N. Default 2× the optimistic wall
  estimate.

In LangGraph, `recursion_limit` is *not* a timeout — set both, plus
node-level `RetryPolicy` `[lc-docs/errors]`. In CrewAI, `max_rpm` rate-
limits but does not timeout — wrap `kickoff()` in `asyncio.wait_for`.

### Step 7 · Reduce, then verify the reduction is sane

After the reducer runs, do one cheap LLM-free check:

- `concatenate` → assert `len(merged)` is within expected bounds; raise if
  one branch returned a 50KB blob.
- `vote` → log the vote distribution; if it's near-uniform, the items
  weren't actually deciding the same question — go back to Step 1.
- `rank-top-K` → assert scores are not all identical (failure mode of a
  broken reranker).

These cheap checks catch the "fan-out succeeded but the answer is garbage"
bug class that no exception will surface.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**.

### OP-1 · `asyncio.gather` with bounded concurrency (Python baseline)
- **Trigger**: Pure Python, no graph framework, async LM client (Anthropic
  / OpenAI), N items, you want a list back.
- **Action**:
  ```python
  sem = asyncio.Semaphore(N_CONCURRENT)
  async def bounded(item):
      async with sem:
          return await asyncio.wait_for(f(item), timeout=PER_CALL_S)
  results = await asyncio.gather(
      *[bounded(i) for i in items],
      return_exceptions=True,        # explicit best-effort
  )
  ok = [r for r in results if not isinstance(r, Exception)]
  ```
- **Output**: A list (or list-with-holes) ready to reduce. Semaphore is
  the rate limiter; `return_exceptions=True` is the failure policy;
  `wait_for` is the per-call timeout.
- **Evidence**: `[newline/asyncio-llm]`, `[soumendrak/semaphore]`,
  `[superfastpython/gather]`.

### OP-2 · `asyncio.as_completed` for quorum / first-K
- **Trigger**: You only need K-of-N successful results (vote with
  early-exit, "first 3 of 10 retrieve hits").
- **Action**:
  ```python
  tasks = [asyncio.create_task(f(i)) for i in items]
  done = []
  for fut in asyncio.as_completed(tasks):
      try: done.append(await fut)
      except Exception: pass
      if len(done) >= K:
          for t in tasks: t.cancel()
          break
  ```
- **Output**: First K successful results; remaining cancelled to save cost.
- **Evidence**: `[instructor/learn-async]`.

### OP-3 · LangGraph `Send` for dynamic fan-out
- **Trigger**: Inside a LangGraph state graph, the number of parallel
  branches is decided at runtime from state.
- **Action**:
  ```python
  from langgraph.types import Send
  def route_fanout(state):
      return [Send("worker", {"item": x}) for x in state["items"]]
  graph.add_conditional_edges("planner", route_fanout, ["worker"])
  ```
  The worker writes to a list-typed state key with a reducer
  (see OP-4). Cap concurrency at `.compile()` time via
  `compile(...).with_config({"max_concurrency": N})` or
  `graph.invoke(..., {"max_concurrency": N})`.
- **Output**: True per-invocation map-reduce. Each `Send` is its own trace
  segment in LangSmith.
- **Evidence**: `[deepwiki/mapreduce]`, `[mlplus/langgraph-mr]`,
  `[medium/send-api]`. Skill `langgraph-sop` OP-4 is the canonical entry.

### OP-4 · Add a reducer for parallel writes (cross-link `O5`)
- **Trigger**: Two or more `Send`-spawned workers (or any parallel
  branches) write to the same state key. Without a reducer, LangGraph
  raises `InvalidUpdateError`.
- **Action**: `summaries: Annotated[list[str], operator.add]` for
  concatenate, `add_messages` for chat, or a custom reducer for dedupe/top-K.
- **Output**: Parallel writes merge per the reducer's algebra.
- **Evidence**: `[cheatsheet/gotchas]` "Reducers are mandatory, not
  optional, for parallel execution"; `[lc-docs/persistence]`.

### OP-5 · CrewAI `kickoff_for_each` (parallel crew invocations)
- **Trigger**: Same crew, N independent inputs (e.g., one report per
  topic).
- **Action**:
  ```python
  results = crew.kickoff_for_each(inputs=[{"topic": t} for t in topics])
  # async variant: kickoff_for_each_async
  ```
  Rate-limit at crew creation: `Crew(..., max_rpm=30)`. Wrap calls in
  `asyncio.wait_for` for total wall budget.
- **Output**: Parallel crew runs, one result per input.
- **Evidence**: `[crewai-docs/kickoff]`. Note: CrewAI's hierarchical
  process is *not* a fan-out primitive — see DC-3.

### OP-6 · `ThreadPoolExecutor` for sync LM clients
- **Trigger**: The LM client is synchronous (legacy SDK, no async
  variant), but the workload is I/O-bound.
- **Action**:
  ```python
  from concurrent.futures import ThreadPoolExecutor
  with ThreadPoolExecutor(max_workers=N_CONCURRENT) as ex:
      results = list(ex.map(f, items, timeout=PER_CALL_S))
  ```
  `as_completed(futures, timeout=...)` for failure isolation. Avoid for
  CPU-bound `f` — use `ProcessPoolExecutor` or a job queue.
- **Output**: Bounded-concurrency parallel sync calls.
- **Evidence**: Python stdlib `concurrent.futures` docs.

### OP-7 · LlamaIndex multi-query / batch retrieval
- **Trigger**: One user question → N rephrased queries → retrieve over
  each → reduce.
- **Action**: `MultiQueryRetriever` or `QueryFusionRetriever` with
  `num_queries=N`; let LlamaIndex parallelise internally. Combine with
  `RRF` (reciprocal rank fusion) as the reducer, not naive concat.
- **Output**: Single ranked node list; recall improves vs. one query.
- **Evidence**: LlamaIndex retriever modules; skill `llamaindex-sop`.

### OP-8 · Tree-reduce for big-N summarisation
- **Trigger**: N items too many to summarise in one LM context, but
  pairwise `summarize(a, b) → c` is meaningful.
- **Action**: Recursive pairwise fan-out: layer 1 reduces N → N/2,
  layer 2 N/2 → N/4, until 1. Each layer is its own bounded fan-out.
  In LangGraph, model as repeated `Send` rounds; in plain Python,
  recursive `gather`.
- **Output**: Single summary; total LM cost `O(N)`, latency `O(log N)`.
- **Evidence**: classical MapReduce; LangChain's "map-reduce chain"
  predecessor used the same shape.

### OP-9 · Retry wrapper per item (decouple from `gather`)
- **Trigger**: API flakiness causes intermittent 5xx / 429.
- **Action**: Wrap `f` *not* the gather:
  ```python
  @tenacity.retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential(multiplier=1, max=10),
      retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
  )
  async def f_retry(item): return await f(item)
  ```
  Retry inside the semaphore (slot held during backoff is intentional —
  it spaces out load).
- **Output**: Transient failures absorbed; permanent failures still
  bubble up to the failure-policy layer.
- **Evidence**: provider rate-limit guides; tenacity docs.

### OP-10 · Observability: per-item trace + reduce-step trace
- **Trigger**: Production fan-out — must be debuggable when one item
  produces a wrong answer.
- **Action**: Tag each fan-out call with `item_id` in the LangSmith /
  OTel / Logfire trace. Log `len(items)`, `len(ok)`, `len(failed)`,
  `wall_time_s` on the reduce step. For LangGraph, each `Send` is
  already a distinct trace segment — name the worker node descriptively
  (`summarize_doc` not `worker`).
- **Output**: Per-item drill-down; reduce-step aggregate metrics.
- **Evidence**: `[swarnendu/best]`; LangSmith Send-tracing docs.

---

## 5. 困境决策案例 (Dilemma Cases)

### DC-1 · "100 items × 5s each, fan out gets 429-storm"
- **困境**: Coder wrote `await asyncio.gather(*[summarize(d) for d in
  100_docs])` against the Anthropic API. First 50 fire instantly, the rest
  queue inside the client; provider returns 429 for half; tenacity retries
  pile on; nothing finishes. Wall time worse than sequential.
- **约束**:
  - Provider RPM = 50; TPM = 200k; each prompt ≈ 3k tokens (300k TPM
    if all fire) → TPM is the binding constraint, not RPM.
  - Cannot pre-batch (per-doc tools differ).
  - SLA = 90s.
- **决策步骤**:
  1. **Compute the real ceiling**: `N_concurrent = TPM / (60 · tokens_per_call)
     = 200_000 / (60 · 3000) ≈ 1.1` → round to **2 in-flight**, *not* 10.
     RPM said 50 — TPM said 2. Bind to the tighter one.
  2. **Add a semaphore at 2**. Now expected wall is `100 · 5s / 2 = 250s`
     — exceeds SLA.
  3. **Reduce N before fan-out**: pre-filter docs with a cheap embedding
     similarity to the query → drop to 20 relevant docs.
  4. **Re-compute**: `20 · 5s / 2 = 50s` ✓ under SLA.
  5. **Add `return_exceptions=True`** and a 30s per-call `wait_for`. If
     one doc hangs, the others still finish.
- **结果**: Throughput drops nominally (2 in-flight vs. 50 attempted), but
  *actual* completed-per-second goes up because no retry-storm. SLA met.
- **可提取的操作**: **The semaphore size is set by the tighter of RPM
  and TPM, not the looser. When the math says SLA can't be met at the
  safe concurrency, reduce N before fan-out — never raise concurrency
  past the real ceiling.** `[newline/asyncio-llm]`

### DC-2 · "LangGraph `Send` fans out 50 workers, all write `state['summaries']`, get `InvalidUpdateError`"
- **困境**: A research agent uses `Send` to spawn one summarizer per
  retrieved doc. State has `summaries: list[str]`. LangGraph crashes on
  the first run with `InvalidUpdateError: At key 'summaries': Can receive
  only one value per step. Use an Annotated key to handle multiple
  values.` Skill `langgraph-sop` flags this `[cheatsheet/gotchas]`.
- **约束**:
  - Cannot serialise the workers — that defeats the fan-out.
  - Need order preservation (each summary tagged with its source).
- **决策步骤**:
  1. **Cross-link to skill `O5 state-reducer`**: parallel writes require
     an explicit reducer.
  2. Change schema: `summaries: Annotated[list[dict], operator.add]`
     where each worker returns `[{"doc_id": ..., "summary": ...}]`.
  3. If order matters, do *not* rely on `operator.add` order (Python list
     concat is in completion order); sort by `doc_id` in the reduce node.
  4. If dedupe matters, use a custom reducer that drops duplicates by
     `doc_id`.
  5. Add a regression test that fan-outs ≥2 workers and asserts the
     merged list length and order.
- **结果**: Fan-out works; the reducer makes the merge deterministic
  regardless of completion order.
- **可提取的操作**: **In LangGraph, *every* state key written by a `Send`
  worker must have a reducer. Pick `operator.add` for concat,
  `add_messages` for chat, a custom function for dedupe / top-K. Order
  is completion order, not Send order — sort in the reduce node if you
  need stability.** `[cheatsheet/gotchas]`, `[deepwiki/mapreduce]`

### DC-3 · "One of N is going to fail — abort, skip, or retry?"
- **困境**: An enrichment pipeline fans out 30 LM calls (one per CRM
  record). One record has malformed input → call returns 4xx. Coder
  doesn't know whether to abort the whole batch, drop the bad record,
  or retry it.
- **约束**:
  - Downstream consumer is a CSV writer — partial OK if rows are tagged.
  - Cost of re-running the whole batch ≈ $5; cost of one record ≈ $0.15.
  - Some 4xx are transient (rate-limit), some are permanent (bad input).
- **决策步骤**:
  1. **Classify failures**: distinguish *transient* (429, 500, 503,
     timeout) from *permanent* (400 bad input, 401, 422).
  2. **Apply OP-9 retry only to transient**: `retry_if_exception_type((
     RateLimitError, APITimeoutError, APIConnectionError))`. Permanent
     errors fall through immediately.
  3. **Set policy to best-effort** (`return_exceptions=True`): permanent
     failures land as exceptions in the result list, tagged with the
     input id.
  4. **Reduce step writes a `failed_records` list alongside `ok_records`**
     — never lose the failure metadata.
  5. **Decision in the reduce node**: if `len(failed) / N > threshold`,
     surface a louder failure (e.g., refuse to emit the CSV). Otherwise
     emit partial + a sidecar errors file.
- **结果**: Transient blips disappear; permanent issues surface as
  structured failures, not a 30-call atomic abort.
- **可提取的操作**: **There is no single "right" failure policy. Pick by:
  (a) is the consumer OK with holes? (b) can you classify transient
  vs. permanent? (c) what % failure makes the result useless? Encode
  those answers as code — not as hope.** `[aipractitioner/scaling]`

### DC-4 · "Vote / majority disagrees — pick the mode, or surface the disagreement?"
- **困境**: Self-consistency ensemble: same question, 5 LM calls with
  `temperature=0.7`, vote on the answer. Three say "A", two say "B".
  Coder is about to `return mode(answers)`.
- **约束**:
  - Stakes high: incorrect "A" is much worse than "I'm not sure".
  - Downstream caller is another agent that can handle uncertainty.
- **决策步骤**:
  1. **Don't collapse silently**: a 3/5 vote is *weaker* than a 5/5 vote.
     Return both the mode and the agreement ratio.
  2. **Threshold**: define `confident_if agreement_ratio ≥ 0.8`. Below
     that, return `("unknown", {"votes": Counter(...)})`.
  3. **Tiebreak strategy** for high-stakes: re-fan-out with N=11 (cost
     more) or escalate to a stronger model — never random tiebreak.
  4. **Log the vote distribution always**, even on confident answers —
     a near-tie is your early-warning signal for prompt drift.
- **结果**: Caller sees "A" with confidence 0.6 instead of "A" with
  false certainty; can choose to escalate.
- **可提取的操作**: **A reduce that hides disagreement is a lossy reduce.
  Preserve the distribution as metadata; let the caller decide what
  "confident enough" means. Default threshold: 0.8 agreement for high
  stakes, 0.6 for low.**

### DC-5 · "Tree-reduce vs. flat-concat for 200 doc summaries"
- **困境**: 200 docs, each `summarize_doc` returns ~400 tokens. Flat
  concat = 80k tokens → exceeds context for the final synthesis step.
- **约束**: cannot reduce N (legal requirement to consider all docs);
  budget allows extra LM calls.
- **决策步骤**:
  1. **Reject flat-concat** — context overflow.
  2. **Reject single-call summary-of-summaries** — even if it fits, one
     LM call summarising 80k tokens loses too much detail.
  3. **Tree-reduce (OP-8)**: layer 1 groups of 10 → 20 mid-summaries;
     layer 2 groups of 5 → 4 quarter-summaries; layer 3 → 1 final.
     Each layer is its own bounded fan-out (concurrency cap re-applies).
  4. **Verify after each layer**: log the count and a sample. Stop the
     chain on suspicious shrinkage (one layer dropping >70% of content
     is usually a prompt bug).
  5. Total cost ≈ `200 + 20 + 4 + 1 = 225 calls` (vs. flat-concat's
     impossible 1 call); latency `O(log_10 200) ≈ 3` layers.
- **结果**: All 200 docs influence the final answer; context never
  overflows; latency stays roughly constant in N.
- **可提取的操作**: **When flat-concat overflows, tree-reduce is the
  answer — but each layer is itself a bounded fan-out, with its own
  concurrency cap, failure policy, and verification. Treat each layer
  as a separate superstep.** `[langchain/map-reduce-chain]`

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

Concrete don'ts:

- **Don't use unbounded `asyncio.gather`.** "100 tasks at once" is not
  parallelism — it's a denial-of-service against your own dependencies.
  Always wrap in a semaphore, even if you think N is small
  `[newline/asyncio-llm]`.

- **Don't omit per-call timeout.** Without `wait_for`, a single stuck
  call holds a semaphore slot forever and silently lowers your effective
  concurrency to N−1, then N−2, etc.

- **Don't ignore the failure policy.** Decide *before* coding: abort,
  best-effort, retry-then-skip, or quorum. Implicit defaults are wrong
  half the time: `gather(...)` aborts on first failure (surprise to
  most), but LangGraph parallel branches *also* abort the entire
  superstep — not the same level but the same shape of surprise
  `[aipractitioner/scaling]`.

- **Don't `Send` for fixed-cardinality work.** If N is always 3,
  static parallel edges are simpler, more readable, and easier to
  trace `[aipractitioner/scaling]`. `Send` is for runtime-variable N.

- **Don't write to a state key from parallel branches without a
  reducer.** This is the canonical `InvalidUpdateError`
  (cross-link skill `O5 state-reducer`) `[cheatsheet/gotchas]`.

- **Don't use the same model on every branch when self-consistency is
  the goal.** Self-consistency requires *diversity* — sample with
  `temperature > 0`, vary the prompt, or vary the model. Same prompt
  + temperature 0 + N parallel calls = N identical answers and a
  meaningless vote.

- **Don't fan out a CPU-bound `f`.** `asyncio.gather` and
  `ThreadPoolExecutor` parallelise I/O, not CPU. CPU-bound `f`
  (heavy local tokenisation, image preprocessing) needs
  `ProcessPoolExecutor` or a job queue.

- **Don't reduce by "let the next LM call see everything".** That's
  flat-concat dressed up; the context-overflow failure mode is
  identical. See DC-5: tree-reduce when N is large.

- **Don't trust the framework's default `max_concurrency`.** LangGraph,
  CrewAI, and LlamaIndex all default to "as many as you ask for". Set
  the cap explicitly, in code, near the fan-out.

- **Don't fan out when latency is dominated by network, not compute.**
  A 50ms function fanned 100-wide over a 200ms-RTT network finishes in
  ~250ms regardless of N — the win evaporates. Profile first.

**Hard boundaries — when this skill is the wrong tool:**

- Items are sequentially dependent (chain-of-thought across docs, beam
  search). Use a chain or a DAG.
- N is statically 1–2. Just inline the calls.
- The "fan-out" is into one batched API call. That's batching, not
  map-reduce. Use it.
- You need strict ordering with side effects (each call must observe
  the previous call's writes). That's a state machine, not map-reduce.

---

## 7. 跨框架对照 (Cross-framework Cheat-sheet)

| Framework | Primitive | Concurrency cap | Failure default | Reduce mechanism |
|---|---|---|---|---|
| **asyncio** | `gather(*coros)` / `as_completed` | `Semaphore(N)` | `return_exceptions=False` aborts on first | Post-gather list comprehension; manual |
| **threads** | `ThreadPoolExecutor(max_workers=N)` | `max_workers` arg | Per-future `result()` raises | `as_completed`; manual aggregation |
| **LangGraph** | `Send("worker", state)` from conditional edge | `config={"max_concurrency": N}` | **Atomic superstep — one fails, all discarded** `[aipractitioner/scaling]` | State reducer (`operator.add`, `add_messages`, custom) — **mandatory** for parallel writes `[cheatsheet/gotchas]` |
| **CrewAI** | `crew.kickoff_for_each(inputs=[...])`, Flow `@listen` | `Crew(max_rpm=N)` | Per-kickoff; not atomic | Caller-side merge; or downstream task with `context=[...]` |
| **LlamaIndex** | `MultiQueryRetriever`, `QueryFusionRetriever`, `async_aggregate=True` on `QueryEngine` | Internal; configurable in retriever | Per-retriever | RRF / dedupe / score-merge built into the retriever |
| **OpenAI/Anthropic batch APIs** | Native batch endpoint | Provider-managed | Per-item | One sync API call returns the list |

Quick chooser:

- **Plain Python, no graph state** → asyncio + Semaphore (OP-1).
- **Already in LangGraph** → `Send` + reducer (OP-3 + OP-4).
- **Already in CrewAI** → `kickoff_for_each` (OP-5); for conditional
  routing → CrewAI Flow with parallel `@listen` branches.
- **Retrieval over multi-query** → LlamaIndex retriever modules (OP-7).
- **Embedding or rerank N items** → use the provider's batch endpoint
  (1 call), not fan-out.

The general rule: prefer the lowest abstraction that lets you set
**concurrency cap**, **per-call timeout**, and **failure policy**
explicitly. If a framework hides any of the three, wrap it.

---

## Appendix A · Minimal reference snippet (asyncio baseline)

```python
import asyncio
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T"); R = TypeVar("R")

async def map_reduce(
    items: list[T],
    f: Callable[[T], Awaitable[R]],
    reduce: Callable[[list[R]], R],
    *,
    n_concurrent: int = 5,
    per_call_timeout_s: float = 30.0,
    fail_policy: str = "best_effort",  # "abort" | "best_effort"
) -> R:
    sem = asyncio.Semaphore(n_concurrent)

    async def bounded(x: T):
        async with sem:
            return await asyncio.wait_for(f(x), timeout=per_call_timeout_s)

    raw = await asyncio.gather(
        *(bounded(x) for x in items),
        return_exceptions=(fail_policy == "best_effort"),
    )
    if fail_policy == "best_effort":
        ok = [r for r in raw if not isinstance(r, BaseException)]
        failed = [r for r in raw if isinstance(r, BaseException)]
        if not ok:
            raise RuntimeError(f"all {len(items)} branches failed: {failed[:3]}")
        return reduce(ok)
    return reduce(raw)
```

Use this when there's no graph framework already in the codebase. Replace
`reduce` with `lambda xs: "\n".join(xs)` (concat), `Counter(xs).most_common(1)[0][0]`
(vote), or a follow-up LM call (summarize). The same three knobs —
`n_concurrent`, `per_call_timeout_s`, `fail_policy` — show up in every
framework variant; this snippet just makes them explicit.

---

## Appendix B · LangGraph `Send` reference

```python
import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

class State(TypedDict):
    items: list[str]
    summaries: Annotated[list[dict], operator.add]   # reducer is mandatory

class WorkerState(TypedDict):
    item: str

def fanout(state: State):
    return [Send("worker", {"item": x}) for x in state["items"]]

async def worker(s: WorkerState):
    # one LM call per item; state writes are merged via the reducer above
    text = await llm.ainvoke(f"Summarize: {s['item']}")
    return {"summaries": [{"item": s["item"], "summary": text.content}]}

def reduce_node(state: State):
    ordered = sorted(state["summaries"], key=lambda d: state["items"].index(d["item"]))
    return {"final": "\n".join(d["summary"] for d in ordered)}

g = StateGraph(State)
g.add_node("worker", worker)
g.add_node("reduce", reduce_node)
g.add_conditional_edges(START, fanout, ["worker"])
g.add_edge("worker", "reduce")
g.add_edge("reduce", END)
app = g.compile()
result = await app.ainvoke({"items": docs}, {"max_concurrency": 5})
```

Cross-references: skill `langgraph-sop` (OP-4 `Send`, OP-3 reducers),
skill `O5 state-reducer` (deeper on parallel-write semantics).

---

## 引用速查 (Citation Index)

- `[deepwiki/mapreduce]` = deepwiki.com/langchain-ai/langchain-academy/7.1-map-reduce-pattern
- `[medium/send-api]` = medium.com/@vishy2k5/langgraph-send-api-7aaab56bc6b8
- `[mlplus/langgraph-mr]` = machinelearningplus.com/gen-ai/langgraph-map-reduce-parallel-execution/
- `[aipractitioner/scaling]` = aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization
- `[cheatsheet/gotchas]` = sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/
- `[lc-docs/persistence]` = docs.langchain.com/oss/python/langgraph/persistence
- `[lc-docs/errors]` = docs.langchain.com/oss/python/langgraph/errors
- `[newline/asyncio-llm]` = newline.co/@zaoyang/python-asyncio-for-llm-concurrency-best-practices
- `[soumendrak/semaphore]` = soumendrak.com/blog/semaphores-python-async-programming/
- `[superfastpython/gather]` = superfastpython.com/asyncio-gather-limit-concurrency/
- `[instructor/learn-async]` = python.useinstructor.com/blog/2023/11/13/learn-async/
- `[tianpan/structured-concurrency]` = tianpan.co/blog/2026-04-09-structured-concurrency-ai-pipelines-parallel-tool-calls
- `[crewai-docs/kickoff]` = docs.crewai.com/en/concepts/crews (kickoff_for_each)
- `[swarnendu/best]` = swarnendu.de/blog/langgraph-best-practices/
- `[langchain/map-reduce-chain]` = python.langchain.com/docs/versions/migrating_chains/map_reduce_chain/
