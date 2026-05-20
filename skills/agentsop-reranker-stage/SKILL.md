---
name: agentsop-reranker-stage
version: 0.1.0
description: >-
  Enhancement-overlay SOP for the reranker stage of a RAG pipeline — the "retrieve wide,
  rerank narrow" discipline. Activate when a calling agent owns a retrieval pipeline whose
  answers have plateaued: top-k contains the right document but it is buried below noise, or
  the context window is under pressure from too many marginal chunks. Encodes the one non-
  negotiable insight — a cheap bi-encoder retrieves *wide* for recall, then a more expensive
  cross-encoder (which reads query + document *together*) reranks *narrow* for precision;
  keep top-N=20-50, rerank to top-k=3-5. Covers when to add a reranker (and when not to),
  N-vs-k tuning, model choice (Cohere/Voyage API vs bge-reranker local vs
  SentenceTransformer cross-encoder), latency/cost budgeting, and the cross-framework
  mapping (LlamaIndex node postprocessors, LangChain ContextualCompressionRetriever,
  Cohere/Voyage rerank APIs, local cross-encoders). This is an ENHANCE overlay over the per-
  framework skills — cross-link `[[llamaindex]]` and `[[agentsop-hybrid-retrieval]]` for the
  deep API. Search keywords: cross-encoder, Cohere rerank, bge reranker, rerank RAG,
  ColBERT, retrieval reranking, improve RAG precision, retrieve wide rerank narrow.trigger_keywords:
  - "reranker"
  - "rerank"
  - "cross-encoder"
  - "CohereRerank"
  - "bge-reranker"
  - "SentenceTransformerRerank"
  - "node postprocessor"
  - "ContextualCompressionRetriever"
  - "voyage rerank"
  - "top_n after retrieval"
  - "retrieve wide rerank narrow"
when_to_use:
  - "a RAG pipeline's answer quality has plateaued and the relevant doc is present in top-k but not ranked first"
  - "the LLM context window is pressured by too many marginal chunks and you want fewer, higher-precision chunks"
  - "retrieval recall is already good (hit-rate high) but MRR / top-1 precision is low"
  - "a user asks where to add a reranker, how to tune N vs k, or which rerank model to use (API vs local)"
  - "reviewing a pipeline with `similarity_top_k=20` and no postprocessor — a reranker is missing"
when_not_to_use:
  - "retrieval RECALL is the problem (the right doc is NOT in top-N at all) — fix retrieval/chunking/hybrid first"
  - "top-k already small (<=5) and answers are correct — no plateau, no lever to pull"
  - "hard real-time path where the extra rerank round-trip blows the latency budget and quality is already acceptable"
overlay: true
cross_links: [llamaindex, hybrid-retrieval]
---

# Reranker Stage · SOP

> Third-person analytical view of how a mature RAG pipeline *thinks* about the
> reranker. The skill is for an LLM agent that writes / reviews / debugs
> retrieval code — it teaches the cross-framework reranking discipline, not one
> vendor's API. For the per-framework API, descend to `[[llamaindex]]`
> (node postprocessors) or `[[agentsop-hybrid-retrieval]]` (the recall stage that feeds
> the reranker).

This is the **C4 gap skill** in the Phase-D enhance pass. The reranker SOP
existed only buried inside `[[llamaindex]]` (`OP-03 AddReranker`, Stage 3 step 7,
anti-pattern A6). It is the **highest-ROI single addition** to a naive RAG
pipeline, so it earns a standalone overlay.

---

## 1 · 何时激活 (Activation Rules)

Activate when **any** holds:

1. A RAG pipeline's answer quality has **plateaued** after the cheap knobs
   (prompt, embedding model, chunk size) are exhausted — `[[llamaindex]]` Stage 3
   lists reranking as the **last** optimization step, deliberately.
2. Diagnostics show the **relevant document is in top-k but buried** — high
   hit-rate, low MRR, wrong top-1. This is LlamaIndex failure modes **#1 / #10**
   ([[llamaindex]] `OP-03`).
3. The LLM **context window is under pressure** — too many marginal chunks
   inflate cost, latency, and "lost-in-the-middle" degradation. A reranker lets
   you retrieve 50 and feed 5.
4. A user asks **where to add a reranker, how to tune N vs k, or API vs local**.

Do **not** activate (boundary — see §6):

- **Recall is the bottleneck**: the right doc is *not in top-N at all*. A
  reranker can only reorder what retrieval already found — fix retrieval,
  hybrid (`[[agentsop-hybrid-retrieval]]`), or chunking first.
- top-k is already small (≤5) and answers are correct — no plateau.
- A hard sub-100ms path where the extra round-trip is unaffordable and quality
  is already acceptable.

---

## 2 · 核心心智模型 (Core Mental Model)

### The one sentence

> **Retrieve wide for recall with a cheap bi-encoder; rerank narrow for
> precision with an expensive cross-encoder that sees query + document
> together — something the bi-encoder structurally could not do.**

### Why two stages exist at all

The retriever (bi-encoder / vector search) embeds the query and every document
**separately, offline**. Similarity is a dot product of two vectors that never
met. This is *fast* (vectors are precomputed; ANN search is sub-linear) but
*lossy*: the document's vector is a single "topic average" computed without
knowledge of the query.

A **cross-encoder** takes `[query, document]` as a **single joint input** and
runs full attention across both, emitting one relevance score. It sees exactly
which query token matches which document token. This is far more accurate — and
far more expensive: it cannot be precomputed, so it runs **once per
(query, candidate) pair at query time**. Scoring 1M docs this way is infeasible;
scoring **20-50** is cheap.

```
  query ─┐                               query ─┐
         ├─ dot product (precomputed)            ├─► [CROSS-ENCODER] ─► score
  doc  ─┘   ← bi-encoder, FAST, lossy     doc  ─┘   joint attention, SLOW, sharp
       RECALL stage (retrieve top-50)         PRECISION stage (rerank → top-5)
```

The reranker is the bridge: it spends cross-encoder accuracy on a small
candidate set the bi-encoder produced cheaply. **Wide net, sharp knife.**

### The order law (inherited from `[[llamaindex]]` Stage 3)

> Prompts first, reranking last. Reranking is high-impact but expensive —
> exhaust the cheap knobs (prompt, embed model, chunk size, hybrid) before
> spending per-query cross-encoder latency. But once those are spent, the
> reranker is usually the **single biggest remaining lever** (5-15pp
> faithfulness lift on noisy corpora — [[llamaindex]] `OP-03`).

### What a reranker is NOT

- Not a recall fix — it reorders, never retrieves (§6).
- Not a chunking fix — it scores whole candidates, it does not resize them.
- Not free — every reranked candidate is an inference (local) or a billed unit
  (API).

---

## 3 · SOP 工作流 (Agentic Protocol)

Each stage gates the next. Never skip the baseline measurement.

### Stage 0 — Confirm the lever is real

Before adding anything, prove the symptom is *precision*, not *recall*:

1. Run the existing pipeline against ~30-50 labeled QA pairs.
2. Record **hit-rate@N** (is the gold doc in top-N?) and **MRR** (how high?).
3. **If hit-rate is low** → recall problem → STOP, fix retrieval / hybrid
   (`[[agentsop-hybrid-retrieval]]`) / chunking. A reranker will not help.
4. **If hit-rate is high but MRR is low** → precision problem → the gold doc is
   buried → a reranker is the right lever. Proceed.

### Stage 1 — Retrieve wide

Raise the retriever's `top_k` (or `top_n`) to **20-50**. This is the "recall"
stage: cast a wide net so the reranker has the gold doc to find. Hybrid
retrieval (`[[agentsop-hybrid-retrieval]]`) feeds the reranker an even better candidate
pool because it adds lexical recall the dense retriever misses.

### Stage 2 — Insert the reranker

Add a reranker as a post-retrieval step (LlamaIndex node postprocessor;
LangChain `ContextualCompressionRetriever` — §7). Pick the model per §4 OP-03.
It consumes the wide candidate list and re-scores every candidate against the
query with a cross-encoder.

### Stage 3 — Keep narrow

Truncate to **top-k = 3-5** after rerank. This is what reaches the synthesizer.
The whole point: the LLM now sees a *small, high-precision* context instead of a
large noisy one.

### Stage 4 — Measure the lift, gate the change

Re-run the same eval set. Compare **before vs after** on {MRR, faithfulness,
relevancy, **p95 latency**, **per-query cost**}. Keep the reranker **only if**
the precision lift justifies the added latency/cost (§5). A reranker that adds
300ms for +1pp is not always worth shipping. Pin N and k as tuned constants.

---

## 4 · 操作模型 (Operation Models)

Each operation: **Trigger / Action / Output / Evidence**. Full machine-readable
list in `intermediate/operation_candidates.json`.

### OP-01 ConfirmPrecisionNotRecall
- **Trigger**: Considering a reranker; haven't proven the symptom is precision.
- **Action**: Measure hit-rate@N and MRR on labeled QA. High hit-rate + low MRR
  ⇒ precision problem ⇒ reranker is right. Low hit-rate ⇒ recall problem ⇒ STOP.
- **Output**: Go/no-go decision backed by a number, not a hunch.
- **Evidence**: [[llamaindex]] `OP-03` (#1/#10 = right doc in top-k, wrong top-1);
  [[agentsop-hybrid-retrieval]] for the recall path.

### OP-02 WidenThenNarrow
- **Trigger**: Reranker confirmed; pipeline still on naive `top_k=4`.
- **Action**: Retrieve **top-N = 20-50**, rerank, keep **top-k = 3-5**. Embed the
  two numbers as named, evaluated constants.
- **Output**: A two-stage retrieve→rerank pipeline with a high-precision tail.
- **Evidence**: [[llamaindex]] Stage 3 step 7 ("widen top_k to 20-50, rerank to
  3-5"); `OP-03`.

### OP-03 ChooseRerankerModel
- **Trigger**: Reranker stage exists; model not yet chosen.
- **Action**: Pick by constraint:
  - **Cohere Rerank / Voyage rerank (API)** — fastest to ship, no GPU, strong
    multilingual; cost per 1k searches, data leaves your boundary.
  - **bge-reranker (bge-reranker-v2-m3 / large) — local** — open-weights,
    self-hosted, no per-call fee, strong on multilingual; needs a GPU for low
    latency, you own ops.
  - **SentenceTransformer cross-encoder (e.g. ms-marco-MiniLM)** — light,
    CPU-runnable for small N, the lowest-dependency local option; weaker than
    bge-large but cheap.
  - **ColBERT (late-interaction)** — middle ground: token-level interaction,
    precomputable, scales to larger N than a full cross-encoder.
- **Output**: A model justified by latency budget, cost ceiling, data-residency,
  and language mix.
- **Evidence**: [[llamaindex]] `OP-03` (CohereRerank / SentenceTransformerRerank /
  ColBERT named); external: "cohere rerank", "bge-reranker", "cross-encoder
  rerank RAG".

### OP-04 BudgetLatencyAndCost
- **Trigger**: Before shipping; reranker adds a per-query inference/billing unit.
- **Action**: Measure p95 added by the rerank call at the chosen N. API rerankers
  add a network round-trip (~tens-hundreds ms) + per-search cost; local models
  add GPU/CPU inference time. Latency scales with **N**, not k — so over-large N
  is the latency killer (§6).
- **Output**: p95 and $/query deltas attached to the change; ship only if the
  precision lift clears the bar.
- **Evidence**: [[llamaindex]] Stage 3 ("high-impact but expensive — exhaust
  cheap knobs first"); §5 Dilemma 1.

### OP-05 TuneNvsK
- **Trigger**: Reranker live; N/k still at defaults; want to optimize the
  precision/latency frontier.
- **Action**: Sweep **N ∈ {20, 30, 50}** holding k fixed (recall ceiling of the
  candidate pool), then sweep **k ∈ {3, 5, 8}** holding N fixed (how much
  context the LLM sees). Pick the smallest N that saturates hit-rate and the
  smallest k that saturates faithfulness.
- **Output**: Tuned (N, k) on the cost/quality frontier, not guessed.
- **Evidence**: [[llamaindex]] `OP-02 TuneChunkSize` (same sweep-and-pin
  discipline applied to N/k); Stage 3 step 7.

### OP-06 RerankAfterHybrid
- **Trigger**: Traffic has lexical-identity queries (codes, SKUs, symbols) AND a
  precision plateau.
- **Action**: Use hybrid retrieval (`[[agentsop-hybrid-retrieval]]`, BM25 + dense) for the
  wide stage, then rerank its fused candidate list. Hybrid maximizes recall into
  the pool; rerank maximizes precision out of it. They **compose**.
- **Output**: Best-of-both — lexical recall + cross-encoder precision.
- **Evidence**: [[agentsop-hybrid-retrieval]] (recall stage); [[llamaindex]] `OP-04`
  AddHybridBM25 + `OP-03` AddReranker (sequential in Stage 3).

### OP-07 GateOnEval
- **Trigger**: Any reranker add/change.
- **Action**: Compare before/after on {MRR, faithfulness, relevancy, p95,
  $/query}. Keep only on net-positive. Treat as a regression test for future
  retriever changes.
- **Output**: Quantitative justification; the reranker is now eval-gated.
- **Evidence**: [[llamaindex]] `OP-10 EvalLoop`, Stage 2 ("eval loop before
  optimizing anything"), Stage 4.

---

## 5 · 困境决策案例 (Dilemma Cases)

### Dilemma 1 — Rerank latency vs answer quality

**困境**: A reranker reliably lifts precision but adds a per-query stage:
network round-trip (API) or GPU inference (local). On a latency-sensitive
surface (chat, autocomplete) the added p95 may violate the SLA even when quality
improves.

**约束**: Cross-encoder cost is **per (query, candidate) pair** and scales with N
([[llamaindex]] Stage 3: reranking is "high-impact but expensive"). Latency is
dominated by N, not k. The bi-encoder stage was chosen precisely because it is
fast; the reranker reintroduces query-time compute.

**决策步骤**:
1. Measure baseline p95 and the SLA headroom.
2. Measure rerank-stage p95 at the smallest viable N (start N=20).
3. If it fits headroom and quality lifts ≥ a meaningful threshold → ship.
4. If it does not fit → shrink N (OP-05), switch to a lighter model
   (MiniLM cross-encoder, ColBERT), or rerank async/cache for repeat queries.
5. If still over budget and quality is already acceptable → **do not rerank**
   (§6 boundary).

**结果**: Reranking is the highest-ROI lever *only when latency headroom exists*.
The decision is SLA-driven, not quality-driven in isolation. Smaller N often
recovers most of the lift at a fraction of the latency.

**可提取的操作**: `OP-04`, `OP-05`. Anti-pattern A3 (over-large N).

### Dilemma 2 — API reranker (Cohere/Voyage) vs local model (bge / cross-encoder)

**困境**: The hosted API ships in an afternoon, needs no GPU, and tracks SOTA —
but bills per search and sends query + candidates to a third party. A local
bge-reranker has zero per-call fee and keeps data in-boundary — but needs a GPU,
ops ownership, and model-update discipline.

**约束**: Per-query cost (API) vs fixed infra cost + ops (local); data-residency
/ compliance; latency (API adds network hop, local adds inference); team's
GPU/MLOps capacity.

**决策步骤**:
1. **Data residency** hard constraint (PII, regulated)? → local (bge / ColBERT),
   decision over.
2. Estimate query volume × API price vs GPU rental. Low/spiky volume → API
   usually cheaper; high steady volume → local amortizes.
3. No GPU and no MLOps appetite? → API (or CPU MiniLM for tiny N).
4. Multilingual corpus? Both Cohere and bge-reranker-v2-m3 are strong — let
   cost/residency decide.
5. Whichever: wrap the call behind a single `rerank(query, nodes) -> nodes`
   seam so swapping API↔local is a one-line change.

**结果**: Default to the **API to validate the lift cheaply** (prove the reranker
helps before investing in infra), then migrate to **local** once volume,
cost, or residency justify it. The abstraction seam makes the migration safe.

**可提取的操作**: `OP-03`, `OP-04`. Anti-pattern A5 (vendor lock-in, no seam).

---

## 6 · 反模式与边界 (Anti-patterns & Boundaries)

### Anti-patterns

| # | Anti-pattern | Correct move |
|---|---|---|
| A1 | Reranking to fix **recall** — gold doc isn't in top-N | Fix retrieval / hybrid (`[[agentsop-hybrid-retrieval]]`) / chunking; a reranker only reorders what's already retrieved |
| A2 | Naive `similarity_top_k=N` then feed all N to the LLM, no rerank | Widen N **and** rerank to top-3-5 ([[llamaindex]] A6) |
| A3 | Over-large N (rerank 200+ candidates) | Latency scales with N; pick the smallest N that saturates hit-rate (OP-05) |
| A4 | Add reranker first, before prompt/embed/chunk/hybrid | Order law: reranking is **last** ([[llamaindex]] Stage 3); cheapest knobs first |
| A5 | Hard-wire one vendor SDK throughout the pipeline | Hide behind a `rerank(query, nodes)` seam so API↔local swaps in one line (Dilemma 2) |
| A6 | Ship reranker without before/after eval | Gate on {MRR, faithfulness, p95, $/query} (OP-07); a reranker that costs latency for no lift is removed |
| A7 | Keep N=k (rerank n candidates, return n) | Reranking only helps when k < N — you must discard the low-scored tail |
| A8 | Re-embed / re-chunk hoping to fix "wrong top-1" | If the right doc is *present but buried*, that's a rerank job, not a re-ingest |

### Boundaries — when **not** to add a reranker

- **B1 — Recall is the bottleneck**: hit-rate@N low ⇒ the answer isn't in the
  pool. Reranking is a no-op. Fix retrieval first (OP-01, `[[agentsop-hybrid-retrieval]]`).
- **B2 — Already narrow & correct**: top-k ≤ 5 and answers right ⇒ no plateau,
  no lever.
- **B3 — Hard real-time / sub-100ms**: the extra round-trip blows the budget and
  quality is acceptable ⇒ skip (Dilemma 1).
- **B4 — Tiny static corpus** (prompt-stuffable, <100k tokens): no retrieval
  stage to rerank ([[llamaindex]] B1).

### PR-review smells (instant red flags)

- `index.as_query_engine(similarity_top_k=20)` with **no** node postprocessor →
  A2 ([[llamaindex]] PR-smell).
- Reranker added but `top_k` still 4 → A7 (N=k, reranker is a no-op).
- A vendor rerank SDK imported in >1 module → A5 (no seam).
- A reranker PR with no eval delta in the description → A6.
- "Added reranker to improve recall" in a commit message → A1 (category error).

---

## 7 · 跨框架对照 (Cross-framework Mapping)

The reranker is **one stage** with the same shape everywhere: consume a wide
candidate list, re-score with a cross-encoder, truncate to top-k.

| Framework / vendor | Reranker primitive | Notes |
|---|---|---|
| **LlamaIndex** (`[[llamaindex]]`) | **Node postprocessor**: `CohereRerank`, `SentenceTransformerRerank`, `ColbertRerank`, `LLMRerank` passed as `node_postprocessors=[...]` to the query engine; widen `similarity_top_k`, set `top_n` on the reranker | The canonical reference; `OP-03 AddReranker`, Stage 3 step 7, A6 |
| **LangChain** | **`ContextualCompressionRetriever`** wrapping a base retriever with a `CohereRerank` / `CrossEncoderReranker` / `LLMChainExtractor` compressor | Base retriever returns N, compressor reranks/filters to k |
| **Cohere Rerank API** | `cohere.rerank(query, documents, top_n, model="rerank-v3.5")` | Hosted cross-encoder; multilingual; per-search billing |
| **Voyage rerank API** | `voyageai.rerank(query, documents, model="rerank-2", top_k)` | Hosted; pairs well with Voyage embeddings |
| **bge-reranker (local)** | `FlagReranker("BAAI/bge-reranker-v2-m3")` / via `sentence-transformers` `CrossEncoder` | Open-weights, self-hosted, no per-call fee, GPU recommended |
| **SentenceTransformers cross-encoder** | `CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2").predict([(q, d), ...])` | Lightest local option; CPU-viable for small N |
| **ColBERT / RAGatouille** | Late-interaction reranker; token-level scoring, precomputable | Scales to larger N than a full cross-encoder |
| **Haystack** | `TransformersSimilarityRanker` / `CohereRanker` component in the pipeline | Same wide→narrow shape, pipeline-component form |

> Activate **this skill** for the *reranking decision* (whether, where, how wide,
> which model, what it costs). Descend to `[[llamaindex]]` for node-postprocessor
> wiring, and to `[[agentsop-hybrid-retrieval]]` for the recall stage that feeds it.

---

## References

- `references/R1-source-evidence.md` — every cited claim resolved to a source line.
- `intermediate/operation_candidates.json` — machine-readable operation list.

### Primary sources (cited inline above)

- `[[llamaindex]]` SKILL — `OP-03 AddReranker`, `OP-02 TuneChunkSize`,
  `OP-04 AddHybridBM25`, `OP-10 EvalLoop`; Stage 2/3/4; anti-patterns A6/A3;
  failure modes #1/#10; the "prompts first, reranking last" order law.
- `[[agentsop-hybrid-retrieval]]` — the wide/recall stage (BM25 + dense) that feeds the
  reranker; lexical-identity recall.
- External: "cohere rerank" (rerank-v3.5, hosted cross-encoder, per-search
  billing, multilingual); "bge-reranker" (BAAI bge-reranker-v2-m3 / large,
  open-weights local cross-encoder); "cross-encoder rerank RAG" (bi-encoder
  retrieve → cross-encoder rerank, joint query+doc attention, the two-stage
  recall→precision pattern).
