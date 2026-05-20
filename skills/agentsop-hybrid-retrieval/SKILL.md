---
name: agentsop-hybrid-retrieval
version: 0.1.0
description: |
  Enhancement-overlay SOP for adding sparse (BM25 / keyword) retrieval alongside
  dense (embedding) retrieval. Activate when a calling agent is building, reviewing,
  or debugging a retrieval pipeline whose corpus contains exact-match tokens —
  identifiers, error codes, SKUs, API/function names, proper nouns, citations, rare
  jargon — that pure dense embedding silently misses. Encodes the single decision
  rule (**hybrid is traffic-driven, not theoretical: add sparse only when the query
  share that depends on exact tokens is non-trivial**), the wiring of
  QueryFusionRetriever-style fusion (RRF vs alpha-weighted), and per-query-type alpha
  tuning. Frame the work as recovering lexical identity that dense pooling destroys,
  not as "add keyword search for completeness". Cross-links [[llamaindex]].
overlay: true
cross_links: [llamaindex, langchain]
trigger_keywords:
  - "hybrid search"
  - "hybrid retrieval"
  - "BM25"
  - "sparse retrieval"
  - "dense plus sparse"
  - "QueryFusionRetriever"
  - "EnsembleRetriever"
  - "RRF"
  - "reciprocal rank fusion"
  - "alpha tuning"
  - "keyword search RAG"
when_to_use:
  - "the corpus contains exact-match tokens: identifiers, error codes, SKUs, part numbers, API/function names, proper nouns, legal/medical citations, rare jargon"
  - "users report 'I searched the exact code/name and got nothing / the wrong doc' on a dense-only retriever"
  - "reviewing a retriever where traffic includes lexical-identity lookups but only embeddings are wired"
  - "tuning recall on a corpus where both meaning AND exact strings matter"
  - "deciding between pure dense, hybrid, or sparse-first for a new RAG corpus"
when_not_to_use:
  - "traffic is purely semantic / conceptual with <5% lexical-identity queries — hybrid is over-engineering"
  - "the corpus has no stable identifiers and queries never reference exact strings"
  - "pre-baseline: ship dense-only and measure first; hybrid is a Stage-3 optimization (see [[llamaindex]])"
---

# Hybrid Retrieval · Dense + Sparse SOP

> Third-person operating model for a coder agent that owns retrieval recall on a
> corpus where *both* meaning and exact tokens matter. The audience is the LLM
> agent writing or reviewing retrieval code — not an end user.

> **One sentence**: *Dense captures meaning, sparse captures exact tokens; hybrid
> wins when both matter — but only fuse them when traffic actually carries
> exact-match queries, and tune the blend per query type or hybrid loses to dense.*

---

## 1. 何时激活 (Activation Rules)

Activate this skill when **any** of the following holds:

1. The corpus contains **exact-match tokens** that a query may reference verbatim:
   error codes (`ERR_SSL_PROTOCOL`), SKUs / part numbers (`A1-2293-X`), API or
   function names (`as_query_engine`), proper nouns, legal/medical citations
   (`42 U.S.C. § 1983`), version strings, rare jargon, ticket IDs.
2. A bug report says **"I searched the exact code/name/string and got nothing"**, or
   "the right document exists but dense retrieval ranks it below fuzzy near-misses".
3. PR review surfaces a retriever serving lexical-identity traffic but wired
   **dense-only** (`index.as_retriever(...)` / `similarity_search(...)` with no
   sparse leg).
4. You are tuning recall and have already exhausted the cheap dense knobs (prompt,
   embedding model, chunk size) per the [[llamaindex]] optimization ladder — hybrid
   is the next rung.
5. The user mentions hybrid search, BM25, sparse retrieval, RRF, `QueryFusionRetriever`,
   `EnsembleRetriever`, or vector-store-native hybrid (Qdrant/Weaviate/Pinecone).

Do **not** activate when:

- Traffic is purely semantic ("what does X mean?", "summarize the policy") with a
  lexical-identity share **<5%** — adding BM25 doubles index footprint for no gain.
- The corpus has no stable identifiers and no query ever quotes an exact string.
- No dense baseline + eval loop exists yet. Hybrid is a **Stage-3** optimization
  ([[llamaindex]] Stage 3 step 4): baseline and measure before fusing.

---

## 2. 核心心智模型 (Core Mental Model)

Three principles. Violating any of them is why teams "try hybrid and conclude it
didn't help".

### Principle 1 — Dense and sparse fail in opposite directions

Dense embedding models **destroy lexical identity by pooling token representations**:
querying a specific error string yields a vector that captures *"document about SSL
errors"* rather than *"document containing this exact string"*. BM25 does the
inverse — it scores against an **inverted index of exact tokens** and is blind to
synonyms and paraphrase. (TianPan, *Hybrid search in production*, 2026; cited in
[[llamaindex]] Dilemma 2.)

> **Operational corollary**: the symptom "I pasted the exact code and got nothing"
> is not a bug in the embedding model — it is the embedding model working as
> designed. The fix is a second retriever that indexes tokens, not a better
> embedding.

### Principle 2 — Hybrid is traffic-driven, not theoretical

Whether to add sparse is decided by the **query-type distribution of real traffic**,
not by a belief that "more retrievers = better". The decision threshold is the
**lexical share**: the fraction of queries whose correct answer hinges on an exact
token. Below ~5% → dense-only. 5–50% → hybrid. Above ~50% (code, logs, legal) →
invert to sparse-first with dense as a rerank signal. (Cited in [[llamaindex]]
OP-04 / Dilemma 2.)

### Principle 3 — One global alpha underperforms; tune per query type

`alpha` is the dense↔sparse blend (`alpha=1` → pure dense, `alpha=0` → pure sparse).
A semantic query wants high alpha; a lexical-identity query wants low alpha. A single
**global** alpha picked to help lexical queries *hurts* the semantic slice — which is
exactly why a flat alpha "loses to pure dense" and teams wrongly conclude hybrid
failed. Tune alpha **per query type**, or route per type and pick alpha per route.
(LlamaIndex alpha-tuning blog; [[llamaindex]] Dilemma 2 结果.)

> The fusion *method* (RRF vs weighted) and the fusion *parameter* (alpha) are two
> separate decisions. RRF is score-scale-robust and parameter-light; weighted fusion
> is tunable but requires score normalization. Choosing neither deliberately is the
> third silent failure.

---

## 3. SOP 工作流 (Agentic Protocol)

Four stages. Each gates the next. This overlay assumes a working dense baseline +
eval loop already exists (see [[llamaindex]] Stages 1–2); do not start here.

### Stage 0 — Decide if the corpus needs sparse at all

1. Sample **≥50 real queries** (or representative synthetic ones if pre-launch).
2. Label each: **semantic** ("what does X mean?") / **lexical** ("find error code
   ABC-123", "the function named `foo_bar`") / **mixed**.
3. Compute the **lexical share**:
   - `< 5%` → **dense-only**. Stop; hybrid is over-engineering. Record the decision.
   - `5–50%` → **add hybrid** (Stages 1–3).
   - `> 50%` (code search, log search, legal citation lookup) → **invert**: BM25-first,
     dense as a fallback / rerank signal.
4. Confirm the corpus actually *carries* the tokens queries reference (an identifier
   that never appears verbatim in any chunk can't be recovered by BM25 either).

Artifact: a 3-line decision note co-located with the retriever recording the lexical
share and the chosen shape.

### Stage 1 — Wire BM25 + dense as two retrievers

```python
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

dense  = index.as_retriever(similarity_top_k=10)            # embedding leg
sparse = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=10)
```

Hard rules:
- **Both legs index the same node set.** A BM25 leg built over a different/stale node
  set silently drops recall (it can only return tokens it has).
- Retrieve **wider per leg** (top_k 10–20 each) than the final cut — fusion needs
  candidates to combine. Narrow *after* fusion (and after any reranker).
- BM25 needs the raw nodes/corpus, not just the vector store — persist or rebuild it
  alongside the index, or use a vector store with native hybrid (Stage 1-alt).

**Stage 1-alt — vector-store-native hybrid.** If the vector store does sparse
internally (Qdrant `sparse_vectors`, Weaviate `hybrid(alpha=...)`, Pinecone sparse-dense,
pgvector + `ts_rank`), prefer it: one round-trip, one consistency domain, no separate
BM25 index to keep in sync. Use the framework fusion path only when the store has no
native hybrid.

### Stage 2 — Fuse (RRF or alpha-weighted)

Pick the fusion method deliberately (OP-02):

```python
# Reciprocal Rank Fusion — score-scale-robust, parameter-light. Good default.
fused = QueryFusionRetriever(
    [dense, sparse],
    mode="reciprocal_rerank",   # RRF: combine by rank, ignore raw score scales
    similarity_top_k=8,
    num_queries=1,              # set >1 to also fan out query rewrites
    use_async=True,
)

# Relative-score / weighted fusion — tunable blend; requires score normalization.
fused = QueryFusionRetriever(
    [dense, sparse],
    mode="relative_score",
    retriever_weights=[0.6, 0.4],   # ~ alpha=0.6 toward dense
    similarity_top_k=8,
)
```

Default to **RRF** unless you have a labeled set to tune weights on — RRF sidesteps
the dense-cosine vs BM25-score scale mismatch that breaks naive weighted sums.

### Stage 3 — Tune alpha by query type (the gate)

1. Build a small labeled set per query type (semantic / lexical / mixed) — reuse the
   Stage-0 sample.
2. Evaluate alpha (or `retriever_weights`) at `{0.0, 0.25, 0.5, 0.75, 1.0}` on **each
   type separately**, scoring recall / MRR / hit-rate per type.
3. Expect: lexical queries peak near low alpha (sparse-leaning), semantic near high
   alpha (dense-leaning), mixed in between.
4. If a single global alpha cannot satisfy both types without regressing one →
   **route by query type and apply per-route alpha** (hand off classification to
   [[agentsop-query-routing]] if present), or split into two retrievers selected per query.
5. Gate: hybrid must lift the lexical slice **with no regression** on the semantic
   slice vs the dense baseline. If it regresses semantic, the alpha is wrong, not
   hybrid.

> The most common false negative: tuning one global alpha, watching semantic recall
> drop, and reverting to dense. The correct read is "alpha was global; tune per type".

---

## 4. 操作模型 (Operation Models)

Format: **Trigger / Action / Output / Evidence**.

### OP-01 WhenHybridChecklist
- **Trigger**: Deciding whether to add sparse to a dense pipeline.
- **Action**: Run the Stage-0 lexical-share checklist. Confirm: (a) corpus has
  exact-match tokens, (b) traffic references them, (c) lexical share ≥5%, (d) those
  tokens appear verbatim in chunks. All four must hold.
- **Output**: A go/no-go with the lexical share recorded; "no" is a valid, common
  outcome.
- **Evidence**: [[llamaindex]] Dilemma 2 决策步骤; OP-04 ("trigger is traffic-driven,
  not theoretical").

### OP-02 ChooseFusionMethod
- **Trigger**: Two legs wired; need to combine their result lists.
- **Action**: Default **RRF** (`mode="reciprocal_rerank"`) — rank-based, robust to the
  dense-cosine vs BM25-score scale gap, no weight to tune. Use **weighted /
  relative-score** only when you have a labeled set to fit weights and have normalized
  scores. Never naive-sum un-normalized scores.
- **Output**: One deliberate fusion method + the reason it was chosen.
- **Evidence**: RRF (Cormack et al., 2009); LlamaIndex `QueryFusionRetriever` modes;
  LangChain `EnsembleRetriever` (RRF default).

### OP-03 WireBM25Leg
- **Trigger**: Hybrid approved; sparse leg not yet built.
- **Action**: Build `BM25Retriever.from_defaults(nodes=...)` over the **same** node
  set as the dense index; persist/rebuild it as a deployment artifact alongside the
  vector index. Set per-leg `similarity_top_k` wide (10–20).
- **Output**: A sparse retriever consistent with the dense index, returning enough
  candidates to fuse.
- **Evidence**: LlamaIndex `BM25Retriever` docs; [[llamaindex]] OP-04 AddHybridBM25.

### OP-04 PreferNativeHybrid
- **Trigger**: The vector store supports sparse internally.
- **Action**: Use the store's native hybrid (Qdrant sparse vectors / `Prefetch` +
  fusion, Weaviate `hybrid(query, alpha=...)`, Pinecone sparse-dense vectors, pgvector
  full-text + vector) instead of a separate BM25 index. One round-trip, one
  consistency domain.
- **Output**: Hybrid with no second index to keep in sync; lower operational surface.
- **Evidence**: Qdrant hybrid queries docs; Weaviate hybrid search docs; Pinecone
  sparse-dense docs; [[llamaindex]] OP-04 ("or vendor hybrid (Qdrant/Milvus alpha)").

### OP-05 AlphaTunePerType
- **Trigger**: Fusion wired; recall not yet optimized; or hybrid "loses to dense".
- **Action**: Evaluate alpha / weights at `{0, 0.25, 0.5, 0.75, 1.0}` on labeled
  subsets **per query type**, not globally. Lexical → low alpha, semantic → high.
- **Output**: Per-type alpha curve; the alpha that lifts lexical without regressing
  semantic.
- **Evidence**: LlamaIndex *alpha-tuning in hybrid search* blog; [[llamaindex]]
  Dilemma 2 ("tune per type, not globally — otherwise hybrid underperforms dense").

### OP-06 RouteThenAlpha
- **Trigger**: No single global alpha satisfies both query types without regression.
- **Action**: Classify the query type first, then dispatch to a retriever configured
  with the per-type alpha (or pure dense / pure sparse). Hand classification to a
  router ([[agentsop-query-routing]] if available).
- **Output**: Each query gets its optimal blend; semantic and lexical slices both peak.
- **Evidence**: [[llamaindex]] Dilemma 2 结果 (per-type tuning); routing as the
  mechanism to apply it.

### OP-07 InvertForLexicalCorpus
- **Trigger**: Lexical share **>50%** (code search, log search, legal/medical citation
  lookup).
- **Action**: Make **BM25 the primary** retriever; use dense as a fallback / rerank
  signal to catch paraphrase, not as the lead leg. Equivalent to alpha pinned low.
- **Output**: Recall dominated by exact-token matching where that is what users want;
  dense recovers the semantic minority.
- **Evidence**: [[llamaindex]] Dilemma 2 step 4 ("BM25-first, dense as fallback rerank
  signal"); TianPan production write-up.

### OP-08 HybridEvalGate
- **Trigger**: Before merging any hybrid change.
- **Action**: Run the eval loop on **both** slices: assert lexical-slice recall/MRR
  rises vs dense baseline AND semantic-slice metrics do not regress. Gate merge on
  both. A lexical lift bought with a semantic regression is not a win.
- **Output**: Quantitative proof hybrid helped where intended and harmed nothing else.
- **Evidence**: [[llamaindex]] Stage 2 eval loop ("gate every change"); OP-10 EvalLoop.

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — Hybrid (BM25 + dense) vs pure dense: worth the complexity?

**困境**: Dense is the modern default; BM25 looks like "the old keyword thing". Adding
hybrid doubles the index footprint, adds a BM25 index to keep in sync, and introduces
alpha tuning. Is the complexity justified, or is a better embedding model enough?

**约束**:
- Pure dense **silently fails** on exact identifiers, code, error strings, SKUs, API
  names, rare jargon (TianPan 2026, quoted in Principle 1) — and a better embedding
  model does **not** fix it; lexical loss is a property of pooled representations.
- Hybrid adds a second index, a fusion step, and a tuning parameter — real ops cost.

**决策步骤**:
1. Build the query-type taxonomy from real traffic: semantic / lexical / mixed
   (Stage 0).
2. Lexical share `<5%` → **dense-only**; the complexity is not justified.
3. `5–50%` → **add hybrid**; tune alpha per type.
4. `>50%` (legal, code, logs) → **invert**: BM25-first, dense as rerank signal.
5. Evaluate alpha at `{0, 0.25, 0.5, 0.75, 1.0}` on labeled per-type subsets.

**结果**: Hybrid lifts the **lexical slice** with no degradation on the semantic
slice — *if alpha is tuned per type*. A single global alpha often loses to pure dense
on semantic queries, which is why teams sometimes wrongly conclude "hybrid didn't
help". The decision is **traffic-driven, not theoretical**. (Verbatim from
[[llamaindex]] Dilemma 2.)

**可提取的操作**: OP-01, OP-05, OP-07, OP-08.

### Dilemma 2 — Alpha for keyword-heavy vs semantic queries: one knob, two demands

**困境**: After wiring hybrid, a single alpha must serve both a user pasting
`ERR_TLS_CERT_INVALID` (wants exact-token match, low alpha) and a user asking "why is
my connection failing?" (wants meaning, high alpha). Picking alpha=0.5 helps neither
fully; picking alpha to win lexical regresses semantic, and vice versa.

**约束**:
- `alpha=1` = pure dense, `alpha=0` = pure sparse; the optimum differs **by query
  type**, not by corpus.
- Choosing alpha to maximize average recall across mixed traffic can land in a valley
  that underperforms pure dense on the semantic majority — the classic "hybrid hurt
  us" report.
- RRF reduces but does not eliminate the tension: it still implicitly weights the two
  rankings.

**决策步骤**:
1. Split the labeled set by query type (semantic / lexical / mixed).
2. Sweep alpha per type; observe lexical peaks low, semantic peaks high.
3. If one global alpha exists that lifts lexical with **zero** semantic regression →
   pin it (cheapest).
4. Else **route by query type** and apply per-route alpha / pure-leg selection
   (OP-06) — classify first, blend second.
5. For `>50%` lexical corpora, skip the balancing act: invert to BM25-first (OP-07).

**结果**: Per-type alpha (or per-type routing) makes both slices peak simultaneously.
The error to avoid is treating alpha as a single global hyperparameter — that is the
documented cause of "hybrid underperforms dense". (LlamaIndex alpha-tuning blog;
[[llamaindex]] Dilemma 2.)

**可提取的操作**: OP-05, OP-06, OP-08.

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Top anti-patterns (instant red flags in code review)

| # | Anti-pattern | Why it's wrong | Correct move |
|---|---|---|---|
| A1 | Adding hybrid by default on a corpus that is purely semantic | Doubles index footprint and ops surface for no recall gain; <5% lexical traffic | OP-01: gate on lexical share; dense-only is the right answer for semantic corpora |
| A2 | Picking a **single global alpha** for mixed traffic | Helps lexical, regresses semantic (or vice versa) → "hybrid hurt us" | OP-05/OP-06: tune alpha per query type, or route per type |
| A3 | Ignoring the fusion method — naive-summing dense cosine + BM25 score | Score scales are incomparable; the larger-scale leg dominates arbitrarily | OP-02: use RRF (rank-based) or normalize before weighting |
| A4 | BM25 leg built over a different/stale node set than the dense index | Sparse can only return tokens it indexed; silent recall loss | OP-03: build both legs over the same nodes; version them together |
| A5 | "We added hybrid, recall on semantic dropped, hybrid is bad" | The conclusion is wrong; the alpha was global | OP-05: re-evaluate per type before reverting |
| A6 | Final cut taken before fusion (narrow per-leg top_k=3) | Fusion has too few candidates to combine; near-misses never surface | Retrieve wide per leg (10–20), narrow after fusion / rerank |
| A7 | Separate BM25 index when the vector store has native hybrid | Extra index to keep in sync; two consistency domains | OP-04: prefer native hybrid (Qdrant/Weaviate/Pinecone/pgvector) |
| A8 | Hybrid as a substitute for a reranker (or vice versa) | Different jobs: hybrid widens candidate recall, rerank reorders | Hybrid then rerank ([[llamaindex]] OP-03); they compose, don't replace |
| A9 | Shipping hybrid with no per-slice eval | A lexical lift can hide a semantic regression | OP-08: gate on both slices vs the dense baseline |

### Boundaries — when this skill is **not** the right move

- **B1** Purely semantic corpora (<5% lexical traffic) — dense-only; skip hybrid.
- **B2** No dense baseline + eval loop yet — baseline first; hybrid is a Stage-3
  optimization, not a starting point ([[llamaindex]] Stage 3).
- **B3** The recall problem is actually chunking, embedding-model mismatch, or missing
  metadata filters — fix the cheaper knob first ([[llamaindex]] optimization ladder).
- **B4** The exact tokens users query don't appear verbatim in any chunk — BM25 can't
  recover what isn't indexed; fix ingestion, not retrieval.
- **B5** Top-1 is wrong but the right doc is *in* top-k — that's a reranking problem,
  not a recall problem ([[llamaindex]] OP-03 AddReranker).

### PR review smells

- `QueryFusionRetriever([...])` with no `mode=` set and no comment on fusion choice.
- A single hard-coded `alpha` / `retriever_weights` with no per-type eval behind it.
- `BM25Retriever.from_defaults(nodes=other_nodes)` where `other_nodes` differs from
  the dense index's node set.
- Per-leg `similarity_top_k` equal to the final desired count (no headroom for fusion).
- Hybrid added but the eval suite only reports a single aggregate recall number.
- Hybrid hand-rolled with `dense_scores + bm25_scores` summed without normalization.

---

## 7. 跨框架对照 (Cross-Framework Reference Table)

How "dense + sparse, fused" looks across the common stacks. Cross-links [[llamaindex]].

### 7.1 LlamaIndex — `QueryFusionRetriever`

```python
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.retrievers.bm25 import BM25Retriever

dense  = index.as_retriever(similarity_top_k=10)
sparse = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=10)

fused = QueryFusionRetriever(
    [dense, sparse],
    mode="reciprocal_rerank",     # or "relative_score" / "dist_based_score"
    retriever_weights=[0.6, 0.4], # used by weighted modes; ~alpha toward dense
    similarity_top_k=8,
    num_queries=1,                # >1 also fans out query rewrites
)
```
Fusion modes: `reciprocal_rerank` (RRF, default-recommended), `relative_score`,
`dist_based_score` (the latter two are weighted). ([[llamaindex]] OP-04.)

### 7.2 LangChain — `EnsembleRetriever`

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

bm25 = BM25Retriever.from_texts(texts); bm25.k = 10
dense = vectorstore.as_retriever(search_kwargs={"k": 10})

ensemble = EnsembleRetriever(
    retrievers=[bm25, dense],
    weights=[0.4, 0.6],   # weighted RRF blend
)
```
`EnsembleRetriever` fuses with **Reciprocal Rank Fusion** under the hood; `weights`
biases the RRF contribution per retriever (the LangChain analogue of alpha).

### 7.3 Raw RRF (framework-agnostic)

```python
def rrf(result_lists, k=60, top_k=8):
    scores = {}
    for results in result_lists:           # each = ranked list of doc ids
        for rank, doc_id in enumerate(results):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
    return sorted(scores, key=scores.get, reverse=True)[:top_k]

fused = rrf([dense_ids, bm25_ids])          # rank-based, no score normalization
```
RRF combines by **rank**, so dense-cosine and BM25 raw scores never need to share a
scale — the reason it is the safe default (OP-02). `k≈60` is the canonical constant
(Cormack et al., 2009).

### 7.4 Vector-store native hybrid

| Store | Mechanism | Alpha knob |
|---|---|---|
| **Qdrant** | sparse + dense vectors, `Prefetch` + `FusionQuery(fusion=RRF)` | server-side fusion (RRF/DBSF) |
| **Weaviate** | `collection.query.hybrid(query=..., alpha=0.5)` | `alpha` (0=BM25, 1=dense) — the canonical alpha |
| **Pinecone** | sparse-dense vectors in one index | `alpha` weighting on the sparse/dense split |
| **pgvector** | `tsvector` full-text + vector distance, combined in SQL | hand-weighted in the `ORDER BY` expression |
| **Milvus** | hybrid search with `WeightedRanker` / `RRFRanker` | ranker choice + weights |

Prefer native hybrid when available (OP-04): one round-trip, one consistency domain,
no separate BM25 index to keep in sync. Weaviate's `alpha` is the literal parameter the
[[llamaindex]] alpha-tuning blog generalizes.

---

## References

### Primary sources (cited inline)

- LlamaIndex — *Enhancing retrieval with alpha tuning in hybrid search in RAG*:
  https://www.llamaindex.ai/blog/llamaindex-enhancing-retrieval-performance-with-alpha-tuning-in-hybrid-search-in-rag-135d0c9b8a00
- LlamaIndex — `QueryFusionRetriever` / `BM25Retriever` module guides:
  https://developers.llamaindex.ai/python/framework/
- LlamaIndex — *Basic strategies* (hybrid as Stage-3 optimization, step 4):
  https://developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/
- TianPan — *Hybrid search in production: BM25 + dense embeddings* (2026):
  https://tianpan.co/blog/2026-04-12-hybrid-search-production-bm25-dense-embeddings
- LangChain — `EnsembleRetriever` (RRF) docs:
  https://python.langchain.com/docs/how_to/ensemble_retriever/
- Qdrant — *Hybrid queries* (Prefetch + RRF/DBSF fusion):
  https://qdrant.tech/documentation/concepts/hybrid-queries/
- Weaviate — *Hybrid search* (`alpha`):
  https://docs.weaviate.io/weaviate/search/hybrid
- Pinecone — *Sparse-dense vectors*:
  https://docs.pinecone.io/guides/data/understanding-hybrid-search
- Cormack, Clarke, Büttcher — *Reciprocal Rank Fusion outperforms Condorcet…* (2009).

### Companion files

- `references/R1-source-evidence.md` — extraction provenance: which [[llamaindex]]
  SKILL / R3 passages each section, OP, and dilemma derive from.
- `intermediate/operation_candidates.json` — machine-readable operation list.

### Cross-linked skills

- `[[llamaindex]]` — parent RAG SOP; this overlay extracts and standalone-izes its
  Stage-3 step-4 hybrid recipe + Dilemma 2 (alpha tuning per query type).
- `[[langchain]]` — `EnsembleRetriever` equivalent.
- `[[agentsop-query-routing]]` — mechanism for per-query-type alpha (OP-06).
