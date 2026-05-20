---
name: agentsop-query-routing
version: 0.1.0
description: >-
  Enhancement-overlay SOP for query-type routing — sending a query to the right index / tool
  / engine *before* retrieving, not after. Activate when a calling agent owns a retrieval or
  answering surface that fronts more than one handler (a summary index, a vector index, a
  text-to-SQL engine, a tool) and the inbound queries differ in kind: "summarize this doc"
  vs "find the clause about X" vs "how many orders shipped in Q3". Encodes the one non-
  negotiable insight — **one retriever cannot serve all query types; route first, retrieve
  second** — plus the three router families (LLM/selector, embedding/semantic,
  keyword/rule), confidence-threshold + fallback discipline, and the cross-framework mapping
  (LlamaIndex `RouterQueryEngine` / `SelectorPromptTemplate`, Dify Question Classifier node,
  LangGraph conditional edges). This is an ENHANCE overlay over the per-framework skills —
  cross-link `[[llamaindex]]`, `[[agentsop-dify]]`, `[[agentsop-langgraph]]` for the deep
  API. Search keywords: route query, semantic router, query classification,
  RouterQueryEngine, multi-index routing, pick the right tool for a query.trigger_keywords:
  - "query routing"
  - "route to index"
  - "RouterQueryEngine"
  - "question classifier"
  - "conditional edge router"
  - "text-to-SQL or RAG"
  - "summary vs lookup query"
  - "selector"
  - "intent routing"
when_to_use:
  - "a single answering endpoint fronts >=2 retrieval/answer handlers (summary index, vector index, SQL engine, tool) and queries differ in kind"
  - "users send a mix of lookup ('what is X'), summarize ('digest doc Y'), and compute ('how many Z') queries to one entry point"
  - "a monolithic VectorStoreIndex is being asked to also answer summary or aggregate queries and quality is uneven"
  - "designing the top-level shape of a RAG / agent system and deciding between one index vs a router over per-type engines"
  - "PR review of a router/classifier/conditional-edge that picks a downstream handler from the query"
when_not_to_use:
  - "exactly one index/tool can correctly serve every query — routing is dead weight"
  - "the split is by tenant/permission, not by query kind — that is multi-tenant filtering, use [[agentsop-multi-tenant-rag]]"
  - "the branch is a fixed deterministic step (always A then B) with no query-dependent choice — that is a static edge, not a router"
---

# Query-Type Routing · Enhancement Overlay

> Third-person operating model for a coder agent that owns a multi-handler
> answering surface. Audience is the LLM agent writing/reviewing the routing
> code — not the end user.

> **One sentence**: *A retriever is shaped by the query type it was built for;
> a summary index, a vector index, and a text-to-SQL engine are not
> interchangeable — so classify the query and route first, then retrieve.*

This is an **ENHANCE overlay**. It distills the cross-framework *routing
pattern* from three source skills. For the per-framework API, cross-link the
base skill: `[[llamaindex]]` (`RouterQueryEngine`), `[[agentsop-dify]]` (Question
Classifier node), `[[agentsop-langgraph]]` (conditional edges).

---

## 1. 何时激活 (Activation Rules)

Activate when **any** of the following holds:

1. The system has **multiple indices / tools / engines** behind one entry point,
   and a query must be dispatched to exactly one (or a few) of them.
2. Inbound queries **differ in kind** — at least two of: *lookup* ("what does
   the contract say about termination"), *summarize* ("give me the gist of doc
   Y"), *compute/aggregate* ("how many tickets closed last week"), *compare*
   ("diff the 2024 vs 2025 policy").
3. A `VectorStoreIndex` (or any single retriever) is being stretched to answer
   query types it was not built for, and quality is uneven across the mix.
4. The user names a routing primitive: `RouterQueryEngine`,
   `SelectorPromptTemplate`, `LLMSingleSelector`, Dify *Question Classifier*,
   LangGraph `add_conditional_edges`, "intent classifier", "text-to-SQL or RAG".
5. PR review touches a function that reads a query and returns *which handler*
   to call.

Do **not** activate when:

- One index/tool serves every query correctly — routing adds an LLM hop and a
  failure mode for no benefit (see §6 anti-pattern A1).
- The split is by **who is asking** (tenant / ACL), not **what is asked** — that
  is filtering, route to `[[agentsop-multi-tenant-rag]]`.
- The downstream choice is **fixed** (always retrieve then summarize) — that is
  a static edge / linear pipeline, not a router.

---

## 2. 核心心智模型 (Core Mental Model)

Three principles. Violating any of them produces a router that misroutes
silently or routes when it should not.

### Principle 1 — One retriever cannot serve all query types

The index taxonomy is not cosmetic. From `[[llamaindex]]`: a `SummaryIndex` is
a "small, fan-out synthesis" primitive — it reads *every* node to digest a doc;
a `VectorStoreIndex` is top-k semantic lookup — it reads the *few* most similar
chunks; a text-to-SQL engine answers *aggregate/compute* queries that no chunk
contains the answer to. Ask a vector index to "summarize the whole document" and
it returns 4 arbitrary chunks; ask a summary index "what is the late-fee clause"
and it fans out over the whole corpus wastefully. **The query type names the
correct primitive.** Routing is the act of recovering that name at runtime.

> Operational corollary: `index.as_query_engine()` over a single
> `VectorStoreIndex` answering a heterogeneous query mix is the symptom this
> skill exists to fix. The fix is per-type handlers + a router on top.

### Principle 2 — Route first, retrieve second

Routing is a **classification** step that runs *before* any retrieval. It reads
only the query (and optionally light context) and emits a *destination*, not an
answer. This ordering is what bounds latency and cost: you pay for the router
once, then exactly one downstream handler, instead of fanning out to all of
them and merging. LlamaIndex's `RouterQueryEngine`, Dify's Question Classifier
node feeding IF/ELSE branches, and LangGraph's conditional edge over `state`
are the *same shape* — a selector function `(query) -> handler_id` evaluated up
front. The three frameworks differ only in *how* the selector is implemented
(§7).

### Principle 3 — A router is only as good as its destinations' descriptions

Every router — LLM, embedding, or keyword — picks among destinations described
in words or examples. In LlamaIndex the signal is the
`QueryEngineTool.description`; in Dify it is the class label + instruction; in
LangGraph it is whatever the routing function reads off state plus the node
names. From `[[llamaindex]]` Dilemma 3: *"invest in `QueryEngineTool.description`
— it's the only signal the router/agent sees."* A misroute is, four times out
of five, a **bad description**, not a bad model. Fix the description before
swapping the router type.

> The fourth case is genuinely ambiguous queries — for those, Principle of
> Fallback (§3 Stage 4) applies: route to a safe default, never guess silently.

---

## 3. SOP 工作流 (Agentic Protocol)

Five stages. Each gates the next. Stop and reconsider at the first "no".

### Stage 0 — Confirm routing is warranted

Gate questions:
- Are there genuinely **≥2 handlers** with different query-type fit? If no →
  single index, no router (anti-pattern A1).
- Does real traffic actually **span query kinds**? Sample 50 real queries and
  label them. If >90% are one kind → build that handler well; skip the router.
- Is the choice **query-dependent** (not fixed)? If fixed → static edge.

If all three are yes, continue.

### Stage 1 — Enumerate the query types and their handlers

Build the table *before* writing the router. One row per query kind:

| Query kind | Example | Correct handler | Primitive |
|---|---|---|---|
| Summarize / digest | "summarize the Q3 report" | summary engine | `SummaryIndex` |
| Fact lookup | "what is the late-fee clause" | vector engine | `VectorStoreIndex` + filters |
| Compute / aggregate | "how many orders shipped in Q3" | text-to-SQL engine | NL2SQL over the DB |
| Compare / multi-hop | "diff 2024 vs 2025 policy" | decomposition engine | `SubQuestionQueryEngine` |
| Out of scope | "what's the weather" | default / refuse | fallback handler |

This table is the spec for both the handlers and the router. Mapping mirrors
`[[llamaindex]]` Stage 4 ("Compose for query heterogeneity").

### Stage 2 — Build one handler per type, in isolation

Implement and test each engine **independently** against its own query kind
before wiring the router. A misroute is undebuggable if the handlers
themselves are wrong. Author each handler's **description / label** here
(Principle 3) — the destination metadata is part of the handler, not the router.

### Stage 3 — Write the router (pick the cheapest sufficient family)

Three router families, cheapest to most capable:

| Family | How it decides | Pick when |
|---|---|---|
| **Keyword / rule** | regex / substring / heuristic over the query | destinations are lexically distinct ("SELECT", "summarize", file extensions); latency-critical; cost-critical |
| **Embedding / semantic** | embed query, nearest destination description | destinations semantically distinct but not lexically; no per-call LLM budget; deterministic-ish |
| **LLM / selector** | LLM reads query + descriptions, returns choice (single or multi) | destinations need reasoning to disambiguate; multi-select needed; quality > latency |

Default ladder: **start keyword if the types are lexically separable; else
LLM selector**; reach for embedding when you want a middle point (no LLM hop,
better than keyword). Always emit a **confidence / score**, never just a label.

### Stage 4 — Add the fallback default (non-negotiable)

Every router must define behavior for the **unrouteable** query:
- LLM selector returns low confidence / no match → route to a documented
  default handler (usually the broad vector index) **or** an explicit "I can't
  answer that" path. Never let an ambiguous query silently hit a random branch.
- Set a **confidence threshold**: below it → fallback, not best-guess.
- Log every routing decision `{query_hash, chosen_handler, score, fell_back}`
  so misroutes are observable, not anecdotal.

A router with no fallback is the single most common production failure here
(anti-pattern A2).

---

## 4. 操作模型 (Operation Models)

Format: **Trigger / Action / Output / Evidence**.

### OP-01 EnumerateQueryTypes
- **Trigger**: A single endpoint fronts heterogeneous queries; no type table exists.
- **Action**: Sample ≥50 real queries, label each by kind (summarize / lookup /
  compute / compare / out-of-scope), map each kind to its correct handler +
  primitive (Stage 1 table).
- **Output**: A query-type → handler spec table that drives both handler build
  and router design.
- **Evidence**: `[[llamaindex]]` Stage 0 ("What is the query distribution?") +
  Stage 4 heterogeneity table.

### OP-02 BuildPerTypeHandler
- **Trigger**: Type table exists; handlers not yet built.
- **Action**: Implement one engine per type (`SummaryIndex` for digest,
  `VectorStoreIndex` for lookup, NL2SQL for compute, `SubQuestionQueryEngine`
  for compare). Test each against its own kind in isolation. Author its
  description/label.
- **Output**: N independently-verified handlers, each with a destination
  description (Principle 3).
- **Evidence**: `[[llamaindex]]` OP-06 RouteByQueryType; OP-07 DecomposeMultiHop.

### OP-03 KeywordRouter
- **Trigger**: Destinations are lexically distinct; latency/cost-critical path.
- **Action**: regex/substring rules over the query → handler id; explicit
  default for no-match. No model call.
- **Output**: Sub-millisecond, deterministic, free routing for the separable
  cases.
- **Evidence**: `[[agentsop-dify]]` IF/ELSE node over query; `[[agentsop-langgraph]]` conditional
  edge as a pure Python predicate (`add_conditional_edges`).

### OP-04 EmbeddingRouter
- **Trigger**: Destinations semantically (not lexically) distinct; no LLM budget per call.
- **Action**: Embed the query, cosine-match against pre-embedded destination
  descriptions / few examples per route; pick argmax; threshold for fallback.
- **Output**: Cheap, low-latency semantic routing without an LLM hop.
- **Evidence**: `[[llamaindex]]` `EmbeddingSingleSelector` family; router docs.

### OP-05 LLMSelectorRouter
- **Trigger**: Disambiguation needs reasoning; or a query maps to multiple handlers.
- **Action**: Use an LLM selector (single or multi) reading the query + each
  handler's description; return chosen id(s) + reasoning. In LlamaIndex:
  `RouterQueryEngine(selector=LLMSingleSelector.from_defaults(), query_engine_tools=[...])`.
- **Output**: Highest-accuracy routing including multi-route fan-out; costs one
  LLM round-trip.
- **Evidence**: `[[llamaindex]]` OP-06 + Dilemma 3; `SelectorPromptTemplate`.

### OP-06 ConfidenceThresholdFallback
- **Trigger**: Any router that can be uncertain (LLM/embedding) on ambiguous queries.
- **Action**: Read the selector's score; below threshold → route to documented
  default (broad vector index) or explicit refuse path. Never best-guess silently.
- **Output**: Unrouteable queries land somewhere safe and auditable.
- **Evidence**: `[[agentsop-langgraph]]` conditional edge can return a `"__default__"`
  branch; `[[agentsop-dify]]` Question Classifier has a built-in "other/else" class.

### OP-07 RouteDecisionLogging
- **Trigger**: Any production router.
- **Action**: Log `{ts, query_hash, chosen_handler, selector_score, fell_back}`
  on every decision; surface a misroute dashboard.
- **Output**: Misroutes become observable metrics, not user-reported anecdotes.
- **Evidence**: `[[agentsop-dify]]` 7-class trace incl. routing; `[[agentsop-langgraph]]`
  LangSmith trace of the conditional edge.

### OP-08 DescriptionFirstDebug
- **Trigger**: Router misroutes a known query class.
- **Action**: Before swapping router type, rewrite the destination description /
  add 1-2 disambiguating examples; re-evaluate on a labeled routing eval set.
- **Output**: Most misroutes fixed at the description layer, no model change.
- **Evidence**: `[[llamaindex]]` Dilemma 3 ("the only signal the router sees").

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — Router misroutes: improve the classifier or add a fallback?

**困境**: A 3-way router (summary / lookup / SQL) misroutes ~12% of queries —
some lookup queries land on the SQL engine and error out. The team is split:
fine-tune / swap to a bigger LLM selector, vs. add a catch-all fallback.

**约束**:
- Bigger LLM selector adds latency + cost to *every* query to fix 12%.
- A pure fallback masks the misroute but still sends those queries somewhere
  generic, lowering answer quality for the 12%.
- The misroutes cluster: most are lookup queries phrased like questions the SQL
  engine "thinks" it can answer.

**决策步骤**:
1. **Diagnose before fixing** — pull the routing log (OP-07); cluster the 12%.
   The clustering reveals it's a *description* problem, not a model problem
   (the SQL engine's description over-claims).
2. **Fix descriptions first** (OP-08) — tighten the SQL handler's description to
   "aggregate/count/sum over the orders table only"; add 2 negative examples.
   Re-run the routing eval set. Misroute drops to ~4%.
3. **Then add fallback** (OP-06) for the residual ambiguous tail — low-confidence
   → broad vector index, not SQL.
4. **Only if still bad** consider the bigger selector — but now on 4%, the
   cost/benefit usually says no.

**结果**: Description fix + fallback, no model change. The two moves are
complementary, not either/or: improve the classifier *signal* (descriptions)
*and* add a fallback for the irreducible ambiguity. Mirrors `[[llamaindex]]`
Dilemma 3's "fix the supervisor before switching paradigms" logic and
`[[agentsop-langgraph]]`'s "hitting the limit means the logic is wrong" stance.

**可提取的操作**: OP-08, OP-06, OP-07.

### Dilemma 2 — LLM router latency vs cheap keyword router

**困境**: An LLM selector routes correctly but adds ~600ms + a token cost to
every query. Traffic is high-QPS and most queries are lexically obvious
("summarize…", SQL-shaped, or a plain question). Is the LLM hop worth it?

**约束**:
- The LLM selector is accurate but is now the p95 latency bottleneck and a
  per-query cost line.
- A keyword router is free and instant but brittle on the genuinely ambiguous
  tail.
- `[[agentsop-dify]]`'s known per-node latency overhead and `[[agentsop-langgraph]]`'s
  "checkpoint serialisation adds overhead, latency budget <200ms" boundary both
  argue against an LLM hop on every request.

**决策步骤**:
1. **Measure the separable fraction** — what % of queries a cheap keyword/regex
   router classifies with high confidence? Sample says ~80%.
2. **Tier the router**: cheap keyword/embedding router first; only the residual
   ~20% (no confident keyword match) escalates to the LLM selector. This is the
   routing analog of `[[llamaindex]]`'s "exhaust cheap knobs first" and
   `[[agentsop-langgraph]]`'s "promote upward only as needed" ladder.
3. **Set the keyword-confidence bar high** — a wrong cheap route is worse than a
   slow correct one; when in doubt, escalate.
4. **Re-measure p95 and cost**; the LLM hop now runs on 20% of traffic.

**结果**: A two-tier (cascade) router — cheap router handles the obvious
majority instantly, LLM selector handles the ambiguous minority. Cost and p95
drop ~5×; accuracy is preserved because the cheap tier only acts when confident.
Reserve the LLM selector for where reasoning is actually required (Principle 2 +
the §3 Stage 3 ladder).

**可提取的操作**: OP-03, OP-04, OP-05, OP-06.

### Dilemma 3 — Route to one handler vs multi-select fan-out

**困境**: Some queries legitimately need two handlers ("summarize the contract
*and* tell me the late-fee clause"). A single-select router forces a wrong
binary choice.

**约束**:
- Multi-select doubles downstream cost and needs a synthesis step to merge.
- Most queries are single-intent; defaulting to multi-select wastes spend.

**决策步骤**:
1. Quantify the multi-intent fraction from the routing log. If <10% → keep
   single-select + fallback; accept occasional follow-up.
2. If material → use a **multi-selector** (LlamaIndex `LLMMultiSelector` /
   Dify branching to multiple nodes / LangGraph `Send` fan-out to multiple
   handlers) and add a synthesis node to merge results.
3. Never make multi-select the default — it converts a routing problem into a
   fan-out + merge problem with the cost of both.

**结果**: Single-select by default; multi-select only on the measured
multi-intent slice, paired with explicit synthesis. Mirrors `[[agentsop-langgraph]]`
"don't fan out with `Send` for fixed-cardinality work."

**可提取的操作**: OP-05, OP-07.

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Top anti-patterns (red flags in code review)

| # | Anti-pattern | Why it's wrong | Correct move |
|---|---|---|---|
| A1 | Adding a router when one index already serves every query | Pure overhead: an extra hop + a new failure mode for zero benefit | Single index; route only when ≥2 handlers differ in fit (Stage 0) |
| A2 | Router with no fallback / default branch | Ambiguous or out-of-scope queries hit a random or erroring handler | Confidence threshold → documented default / refuse (OP-06) |
| A3 | LLM selector on every query when keyword would do | p95 latency + per-query token cost for separable traffic | Tier: cheap router first, LLM only for the ambiguous tail (Dilemma 2) |
| A4 | Vague destination descriptions | Router can't disambiguate; misroutes blamed on the model | Author precise descriptions + examples; fix here first (OP-08) |
| A5 | No routing decision logging | Misroutes surface as user complaints, not metrics | Log `{query, chosen, score, fell_back}` per decision (OP-07) |
| A6 | Routing by tenant/permission instead of query kind | That's access control, not query routing | Use `[[agentsop-multi-tenant-rag]]` filter at the store; route by *kind* only |
| A7 | Multi-select as the default | Doubles cost + needs merge for mostly single-intent traffic | Single-select default; multi only on measured multi-intent slice (Dilemma 3) |
| A8 | Best-guess on low confidence | Silent wrong route degrades the answer with no signal | Below threshold → fallback, never guess (OP-06) |
| A9 | Tuning the router before the handlers work | A misroute is undebuggable atop broken handlers | Build + verify each handler in isolation first (Stage 2) |

### Boundaries — when query routing is **not** the move

- **B1** One index/tool answers everything correctly → no router (A1).
- **B2** The split is by *who asks* (tenant, ACL) → `[[agentsop-multi-tenant-rag]]`.
- **B3** The downstream is a *fixed* sequence (always retrieve→summarize) →
  static edge / linear pipeline, no selector.
- **B4** Hard real-time (<200ms) and an LLM selector is the only correct router
  → measure first; tier to a keyword/embedding front, escalate rarely (Dilemma 2).
- **B5** The choice is *agentic/iterative* (retrieve→reflect→re-query in a loop)
  → that's an agent loop, not a one-shot router; use `[[agentsop-langgraph]]` cycles.

### PR review smells

- A `RouterQueryEngine` / classifier with no `default` / `other` branch.
- An LLM selector in a high-QPS hot path with no cheap pre-filter.
- `QueryEngineTool(description="index")` — uselessly vague description.
- Routing logic that reads `tenant_id` — that's filtering, not routing.
- A router whose handlers were never tested independently.
- No eval set of labeled `(query, expected_handler)` pairs gating router changes.

---

## 7. 跨框架对照 (Cross-Framework Reference)

The same selector `(query) -> handler_id` surface across the three base skills.
All verified against the source SKILLs (May 2026). Cross-link the base skill for
the full API.

### 7.1 LlamaIndex — `RouterQueryEngine` + selectors → `[[llamaindex]]`

```python
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector  # or LLMMultiSelector,
                                                           #    EmbeddingSingleSelector
from llama_index.core.tools import QueryEngineTool

tools = [
    QueryEngineTool.from_defaults(
        query_engine=summary_engine,
        description="Useful for SUMMARIZING or digesting an entire document."),
    QueryEngineTool.from_defaults(
        query_engine=vector_engine,
        description="Useful for LOOKING UP a specific fact or clause."),
]
router = RouterQueryEngine(
    selector=LLMSingleSelector.from_defaults(),   # LLM selector family
    query_engine_tools=tools,                     # descriptions are the routing signal
)
```

The selector reads each `QueryEngineTool.description` (the only routing signal —
Principle 3). Selector families: `LLMSingleSelector`, `LLMMultiSelector`,
`EmbeddingSingleSelector`, `PydanticSingleSelector`. `SelectorPromptTemplate`
customizes the LLM prompt. `RouterQueryEngine` over per-task indices is "often
the correct top-level shape, not a single monolithic `VectorStoreIndex`"
(`[[llamaindex]]` Principle 3 + OP-06).

### 7.2 Dify — Question Classifier node → `[[agentsop-dify]]`

The **Question Classifier** node (an LLM node) takes the query and emits one of
N declared classes; each class wires to a downstream branch (Knowledge
Retrieval / LLM / Code / HTTP / SQL-via-Code). It is the visual analog of an
LLM selector. The built-in "other" class is the fallback (OP-06). Routing logic
that doesn't need an LLM uses the **IF/ELSE** node (keyword/rule router, OP-03).
Node taxonomy: `Question Classifier`, `Parameter Extractor`, `IF/ELSE`. The
classifier's class label + instruction is the routing signal (Principle 3).

### 7.3 LangGraph — conditional edges as routers → `[[agentsop-langgraph]]`

```python
def route(state) -> str:                          # the selector function
    q = state["query"]
    if looks_like_sql(q):     return "sql"        # keyword tier (OP-03)
    if score := classify(q):  return score.label  # LLM/embedding tier (OP-04/05)
    return "vector_default"                        # fallback (OP-06)

graph.add_conditional_edges("router", route,
                            {"sql": "sql_node",
                             "summary": "summary_node",
                             "vector_default": "vector_node"})
```

"Graph topology is just routing logic over state… a conditional edge reads
state and picks a next node" (`[[agentsop-langgraph]]` Principle 3). The mapping dict's
keys are the destinations; the `route` function is the selector — it can be
keyword, embedding, or LLM, or a tier of all three (Dilemma 2). For genuine
multi-route fan-out, return a list of `Send(...)` instead of one label.

### 7.4 Side-by-side

| | LlamaIndex | Dify | LangGraph |
|---|---|---|---|
| Router primitive | `RouterQueryEngine` | Question Classifier node | `add_conditional_edges` |
| Selector impl | LLM / Embedding / Pydantic selector | LLM classifier (or IF/ELSE for rules) | any Python fn (keyword/embed/LLM) |
| Routing signal | `QueryEngineTool.description` | class label + instruction | node names + what `route()` reads |
| Fallback | selector default / catch-all tool | "other" class | a `"__default__"` branch |
| Multi-route | `LLMMultiSelector` | branch to multiple nodes | list of `Send(...)` |
| Deep skill | `[[llamaindex]]` | `[[agentsop-dify]]` | `[[agentsop-langgraph]]` |

The three are the **same pattern** — classify the query up front, dispatch to
the structurally-correct handler, fall back when uncertain. Pick the framework
your stack already uses; the routing discipline (Principles 1-3, Stages 0-4) is
identical.

---

## References

- `references/R1-source-evidence.md` — every cited claim resolved to its source
  SKILL line.
- `intermediate/operation_candidates.json` — machine-readable operation list.

### Source skills (cited inline as `[[name]]`)

- `[[llamaindex]]` — `llamaindex-sop-skill/SKILL.md` (`RouterQueryEngine`,
  selectors, OP-06 RouteByQueryType, Dilemma 3, Index taxonomy).
- `[[agentsop-dify]]` — `dify-sop-skill/SKILL.md` (Question Classifier / IF-ELSE nodes,
  node taxonomy, per-node latency boundary).
- `[[agentsop-langgraph]]` — `langgraph-sop-skill/SKILL.md` (conditional edges as
  routers, Principle 3 topology-as-routing, `Send` fan-out, latency boundary).
