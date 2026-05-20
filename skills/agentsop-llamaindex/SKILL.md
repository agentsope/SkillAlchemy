---
name: agentsop-llamaindex
description: |
  Operating-system distillation of LlamaIndex — the leading RAG / document-agent
  framework. Activate when the calling agent must build, debug, harden, or evaluate
  a Retrieval-Augmented Generation pipeline over unstructured/private data, decide
  between RAG primitives (Index types, retrievers, query engines, routers, agents),
  or pick LlamaIndex vs LangChain / Haystack / raw vector store for a coding task.
  Encodes the 5-layer mental model (Documents → Nodes → Indices → Retrievers →
  Query Engines / Response Synthesizers), the canonical RAG bootstrap SOP from
  baseline `VectorStoreIndex` through hybrid + reranker + eval-loop hardening,
  the official 13-failure-mode checklist, and 5 dilemma cases distilled from docs,
  GitHub issues, and 2025 production post-mortems.
version: 0.1.0
---

# LlamaIndex · SOP

> Third-person analytical view of how LlamaIndex *thinks* about turning private
> documents into a grounded answering system. The skill is for an LLM agent that
> writes / reviews / debugs RAG code — not for an end user reading docs.

---

## 何时激活 (Activation Rules)

Activate this skill when any of the following holds:

1. The user's request involves building, modifying, or debugging a **RAG pipeline** (retrieval over private/unstructured data + LLM synthesis).
2. The user mentions **LlamaIndex** (`from llama_index...`), **LlamaParse**, **LlamaCloud**, or a LlamaIndex-style primitive (`VectorStoreIndex`, `SummaryIndex`, `IngestionPipeline`, `QueryEngine`, `SubQuestionQueryEngine`, `RouterQueryEngine`, `Settings`, `Workflows`).
3. The user is **comparing RAG frameworks** (LlamaIndex vs LangChain vs Haystack vs raw vector store).
4. The user is choosing between **stuffing context, RAG, or an agent** for a knowledge task.
5. The user is debugging retrieval quality (hallucinations, wrong chunks, stale data, embedding drift) — even if the codebase predates LlamaIndex, the failure-mode taxonomy applies.
6. The user is **evaluating** a RAG system (faithfulness, relevancy, MRR, hit-rate).

Do **not** activate when:
- The task is pure agent orchestration with no retrieval (use LangGraph/CrewAI skill instead).
- The corpus is tiny (<100k tokens, static) and prompt-stuffing is the correct answer.
- The data is pure SQL/tabular with no unstructured component.

---

## 核心心智模型 (Core Mental Model)

LlamaIndex's design rests on three principles that distinguish it from "vector DB SDK + custom glue":

### Principle 1 — The Index is a noun, not a verb

> In LangChain, "indexing" is something you do to a vector store. In LlamaIndex, an `Index` is a first-class typed object with its own retrieval semantics. Picking the right Index is half the architecture decision.

The 5-layer pipeline:

```
Documents → Nodes → Index → Retriever → Query Engine → Response
   ↓         ↓        ↓         ↓             ↓
parsing   chunking  storage   filters    synthesis
metadata  graph     primitive  rerank    (refine/tree_sum/compact)
```

Each layer has a **distinct failure mode** and a **distinct optimization knob**. See `references/R1-architecture.md` for the layer-failure-knob mapping.

### Principle 2 — A Node is a graph node, not a chunk

A `Node` carries: `text`, `metadata`, `embedding`, **`relationships`** (PREV/NEXT/PARENT/CHILD links), and lifecycle ids. The `relationships` field is what enables Hierarchical, Auto-Merging, and Sentence-Window retrieval. The mental flip: **don't think "split into chunks", think "build a chunk-graph"**.

### Principle 3 — Indices are not interchangeable

| Index | Pick when |
|---|---|
| `VectorStoreIndex` | Default; semantic Q&A over chunks; ~90% of RAG cases |
| `SummaryIndex` | "Summarize this whole doc" — small, fan-out synthesis |
| `TreeIndex` | Hierarchical content with progressive zoom-in |
| `KeywordTableIndex` | Keyword-heavy queries, no embeddings budget |
| `PropertyGraphIndex` | Multi-hop reasoning over entities |
| `DocumentSummaryIndex` | Mixed corpora needing document-level routing first |

A `RouterQueryEngine` over multiple per-task indices is often the correct top-level shape, not a single monolithic `VectorStoreIndex`.

### The 2025 shift

LlamaIndex now positions as **"the leading document agent and OCR platform"** (README). `LlamaParse v2` + `Workflows 1.0` (June 2025) + `LlamaCloud` mark a strategic move from "RAG framework" to "platform between messy documents and document-grounded agents". For a coder agent: assume Workflows for any new agentic code (QueryPipeline is deprecated).

---

## SOP 工作流 (Agentic Protocol)

The protocol every RAG implementation must walk through. Each stage gates on the next.

### Stage 0 — Frame the problem

Before code, answer:

1. Is the corpus **unstructured + non-trivial size (>100k tokens) + growing**? If not → see `R4` boundaries; LlamaIndex may be the wrong tool.
2. Is **retrieval quality** the bottleneck (not orchestration)? If orchestration dominates → LangGraph leads, LlamaIndex becomes a retrieval tool *inside* it.
3. What is the **query distribution**? (lookup-only / summary / compare-contrast / mixed). This decides whether a single Index or a Router is needed.

### Stage 1 — Baseline (cheap, fast, observable)

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter

Settings.llm        = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

docs  = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(docs)
qe    = index.as_query_engine(similarity_top_k=4)
```

Pin `Settings` **once at app boot**, never inline. This eliminates the entire embedding-mismatch failure class (failure #4).

### Stage 2 — Build the eval loop **before** optimizing anything

```python
from llama_index.core.evaluation import (
    DatasetGenerator, FaithfulnessEvaluator,
    RelevancyEvaluator, RetrieverEvaluator,
)
qa = DatasetGenerator.from_documents(docs).generate_dataset_from_nodes(num=50)
```

Track {MRR, hit-rate, faithfulness, relevancy, p95 latency}. **Every** subsequent change must be gated on these numbers.

> Most RAG failures in production trace to weak retrieval or sloppy ingestion — not the LLM. The eval loop is what surfaces them.

### Stage 3 — Optimize in LlamaIndex's recommended order

From the official `basic_strategies` guide:

1. **Prompt engineering** (cheapest)
2. **Embedding model** (pick from MTEB; full re-embed if you change it)
3. **Chunk size sweep** ({256, 512, 1024, 2048}; default 1024 for prose, 80-160 for code)
4. **Hybrid search** (BM25 + dense) — *only if traffic contains lexical-identity queries*
5. **Metadata filters** — for multi-tenant / multi-collection corpora
6. **Document/chunk decoupling** — `HierarchicalNodeParser`+`AutoMergingRetriever` *or* `SentenceWindowNodeParser`
7. **Reranking** (Cohere / SentenceTransformer / ColBERT) — widen top_k to 20-50, rerank to 3-5

Note the order: **prompts first, reranking last**. Reranking is high-impact but expensive — exhaust cheap knobs first.

### Stage 4 — Compose for query heterogeneity

| Query shape | Right primitive |
|---|---|
| "Summarize doc X" | `SummaryIndex` per doc, routed |
| "Find the clause about X" | `VectorStoreIndex` + metadata filters |
| "Compare X and Y across docs" | `SubQuestionQueryEngine` |
| "What entities relate to X?" | `PropertyGraphIndex` |
| Mixed | `RouterQueryEngine` over per-task engines |

### Stage 5 — Production hardening

Apply the failure-mode checklist (`R4`). Top 5 non-negotiables:

- `IngestionPipeline` with `docstore` + `UPSERTS_AND_DELETE` for any live corpus.
- `Settings.embed_model` pinned at boot; embedding model name in index metadata.
- `tree_summarize` synthesizer when packing many chunks (mitigates lost-in-the-middle).
- Tracing/observability captures `query + retrieved_nodes + scores + index_id + LLM prompt` for every failure.
- Indices versioned as deployment artifacts; ingestion completes before traffic routing.

### Stage 6 — Escalate to Workflows / Agents (only when justified)

Escalate when at least one of:
- A retrieval loop is needed ("retrieve → check → re-query").
- Tool calls beyond retrieval (calculator, web, code-exec).
- State surviving across query turns.
- Multiple specialized retrievers chosen at runtime.

Use **Workflows 1.0** (event-driven), not deprecated `QueryPipeline`. Wrap query engines as `QueryEngineTool`s and tune the `description=` carefully — it is the only signal the router/agent reads.

---

## 操作模型 (Operation Models)

Each operation: **Trigger / Action / Output / Evidence**.

### OP-01 BaselineVectorIndex
- **Trigger**: First-pass RAG over a new corpus; retrieval-quality baseline unknown.
- **Action**: `VectorStoreIndex.from_documents()` with `SentenceSplitter(1024, 20)`, `top_k=4`, default synthesizer. Ship to eval bench *before* tuning.
- **Output**: Working RAG endpoint + baseline {MRR, hit-rate, faithfulness, relevancy, p95}.
- **Evidence**: `developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/`

### OP-02 TuneChunkSize
- **Trigger**: Faithfulness below target OR retrieved chunks visibly truncated/incomplete.
- **Action**: Sweep `chunk_size ∈ {256, 512, 1024, 2048}` with overlap at ~10-20%; re-evaluate faithfulness + relevancy + latency. Default land: **1024 for prose, 80-160 for code**.
- **Output**: Optimal `chunk_size` pinned + embedding model version locked in index metadata.
- **Evidence**: `llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5` (faithfulness peaked at 1024 in LlamaIndex's own eval on Uber 10-K).

### OP-03 AddReranker
- **Trigger**: Top-1 wrong but relevant docs appear in top-k (failure #1 / #10).
- **Action**: Add `CohereRerank` or `SentenceTransformerRerank` as a NodePostprocessor; widen retrieval top_k to 20-50, narrow to `top_n=3-5` after rerank.
- **Output**: Faithfulness lift typically 5-15pp on noisy corpora; lower context-window pressure.
- **Evidence**: `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/` (#1, #10).

### OP-04 AddHybridBM25
- **Trigger**: Traffic contains exact identifiers, error codes, SKUs, code symbols, rare jargon — pure dense silently misses them.
- **Action**: `QueryFusionRetriever([vector_retriever, BM25Retriever])` *or* vendor hybrid (Qdrant/Milvus alpha). Tune alpha **per query type**, not globally.
- **Output**: Recall lift on lexical-identity queries with no degradation on semantic queries.
- **Evidence**: `llamaindex.ai/blog/llamaindex-enhancing-retrieval-performance-with-alpha-tuning-in-hybrid-search-in-rag-135d0c9b8a00`; BM25Retriever docs.

### OP-05 DecoupleChunkScope
- **Trigger**: Chunk-size sweep produces no single winner (small wins precision, large wins context).
- **Action**: `HierarchicalNodeParser` + `AutoMergingRetriever` (for structured docs) *or* `SentenceWindowNodeParser` + `MetadataReplacementPostProcessor` (for flat prose). Embed small, return large.
- **Output**: Precision-recall pareto improvement; LLM gets surrounding context that small chunks alone lost.
- **Evidence**: AutoMergingRetriever / Hierarchical / SentenceWindow docs on `developers.llamaindex.ai`.

### OP-06 RouteByQueryType
- **Trigger**: Corpus serves heterogeneous tasks (summary / lookup / compare) from one entry point.
- **Action**: Build per-task `QueryEngines` (`SummaryIndex` for digest, `VectorStoreIndex` for lookup, `SubQuestionQueryEngine` for compare) + a `RouterQueryEngine` with LLM or Pydantic selector. Carefully author each `QueryEngineTool.description`.
- **Output**: Each query lands on the structurally-correct retrieval primitive; latency stays bounded.
- **Evidence**: DeepLearning.AI *Building Agentic RAG with LlamaIndex*; router docs.

### OP-07 DecomposeMultiHop
- **Trigger**: Compare/contrast queries; queries needing facts from >1 document; "what changed between X and Y?".
- **Action**: `SubQuestionQueryEngine` decomposes query → dispatches sub-questions to sub-engines → synthesizes.
- **Output**: Multi-hop answers a single retrieval cannot assemble.
- **Evidence**: `developers.llamaindex.ai` sub-question query engine docs.

### OP-08 IngestionWithDocstore
- **Trigger**: Documents will update/delete over time (any production system).
- **Action**: `IngestionPipeline(transformations=..., docstore=..., vector_store=..., docstore_strategy=UPSERTS_AND_DELETE)`. Run on a schedule, not manually.
- **Output**: Idempotent re-ingestion; no duplicate vectors; deletes propagate.
- **Evidence**: `developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/`; failure #3.

### OP-09 MetadataFilters
- **Trigger**: Multi-tenant corpus; cross-contamination between sub-collections; access control needed.
- **Action**: Inject structured metadata at ingestion (`tenant`, `doc_type`, `date`); apply `MetadataFilters` at query time OR enable auto-retrieval to let an LLM emit filters.
- **Output**: Hard isolation between tenants; targeted retrieval without expensive rerank.
- **Evidence**: Failure #7; `basic_strategies` metadata filters section.

### OP-10 EvalLoop
- **Trigger**: Any non-trivial RAG, pre-deploy AND continuously in production.
- **Action**: `DatasetGenerator` → labeled QA pairs; run `FaithfulnessEvaluator` + `RelevancyEvaluator` + `RetrieverEvaluator(["mrr","hit_rate"])`. Gate every change.
- **Output**: Quantitative regression test for every chunking / embedding / retriever / prompt change.
- **Evidence**: `developers.llamaindex.ai/python/framework-api-reference/evaluation/`; `cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex`.

### OP-11 LockGlobalSettings
- **Trigger**: Multiple modules each instantiate LLM/embed independently — drift risk.
- **Action**: Set `Settings.llm` and `Settings.embed_model` once in app bootstrap. Forbid inline overrides in PR review.
- **Output**: Eliminates failure #4 (config drift) and #5 (embedding mismatch).
- **Evidence**: `docs.llamaindex.ai/en/stable/module_guides/supporting_modules/service_context_migration/`.

### OP-12 AgenticWorkflow
- **Trigger**: Need loops, tool calls beyond retrieval, multi-step reasoning, or state across turns.
- **Action**: Build a Workflows 1.0 event-driven workflow OR a `FunctionAgent`/`ReActAgent` with `QueryEngineTool`s. Do NOT use the deprecated `QueryPipeline`.
- **Output**: Cycle-capable agentic system with retrieval as one tool among many.
- **Evidence**: `llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems`.

---

## 困境决策案例 (Dilemma Cases)

(Full text in `references/R3-dilemma-cases.md`. Summarized here.)

### Dilemma 1 — Chunk size: precision vs context

**困境**: Small chunks → precise embeddings, fragmented context for the LLM. Large chunks → rich context, embeddings become "topic averages", recall on specific queries drops. Failure modes #2 and #6 are the two poles.

**约束**: Embedding model has a fixed input window; metadata is propagated into payload (so very small chunks become all-metadata — GitHub `#12200`, `#13792`); token budget caps how many chunks fit downstream.

**决策步骤**:
1. Generate ~20 eval QA pairs.
2. Sweep `chunk_size ∈ {128, 256, 512, 1024, 2048}` with overlap = 10-20%.
3. Build a VectorStoreIndex per config; record faithfulness, relevancy, latency.
4. If a single winner emerges → pin it.
5. If the frontier is non-flat → **do not compromise**; switch to small-embed/large-return via Hierarchical+AutoMerging *or* SentenceWindow.

**结果**: LlamaIndex's own published study (Uber 10-K) peaked at **1024** on both faithfulness and relevancy → 1024 became the framework default for prose. For code: 80-160 tokens. When the eval doesn't converge, decoupling wins; never average two bad chunk_sizes.

**可提取的操作**: `OP-02 TuneChunkSize`, `OP-05 DecoupleChunkScope`. Anti-pattern A1.

### Dilemma 2 — Hybrid (BM25+dense) vs pure dense

**困境**: Adding hybrid doubles index footprint, requires per-query-type alpha tuning, complicates the pipeline. Worth it?

**约束**: Dense embeddings *silently fail* on identifiers, error strings, code, SKUs — they "destroy lexical identity by pooling token representations" (TianPan, 2026). BM25 scores against an inverted token index.

**决策步骤**:
1. Build a query-type taxonomy from real traffic: semantic / lexical / mixed.
2. If lexical share <5% → dense-only.
3. 5-50% → add hybrid; tune alpha per query type.
4. >50% (legal, code, logs) → invert: BM25-first, dense as reranker signal.
5. Evaluate alpha at {0, 0.25, 0.5, 0.75, 1.0} on labeled subsets.

**结果**: Hybrid lifts the lexical slice without hurting the semantic slice — *if alpha is tuned per type*. A single global alpha often underperforms dense, which is why some teams wrongly conclude "hybrid didn't help".

**可提取的操作**: `OP-04 AddHybridBM25`. Decision is traffic-driven, not theoretical.

### Dilemma 3 — Agent on top of RAG, RAG as tool, or just a Router?

**困境**: User adds compare/summary/lookup queries to a basic RAG. Three options:
- A. `RouterQueryEngine` over per-task engines.
- B. `FunctionAgent`/`ReActAgent` with engines as tools.
- C. `SubQuestionQueryEngine` to decompose.

**约束**: Agents add ≥1 LLM round-trip per step (latency); introduce planning errors a router cannot make; harder to debug (failure #12); most queries aren't multi-hop in practice.

**决策步骤**:
1. Measure: what fraction of queries actually need multi-step reasoning?
2. <20% multi-step + heterogeneous-but-single-step → **Router (A)**.
3. Compositional/well-shaped queries ("compare X and Y") → **SubQuestion (C)**.
4. Tool calls beyond retrieval, or cycles, or state → **Agent on Workflows (B)**.
5. Whichever you pick: invest in `QueryEngineTool.description` — it's the only signal the router/agent sees.

**结果**: DeepLearning.AI's official course ladder is Router → Agent. Production guidance consistently warns against premature agentization. Workflows 1.0 (2025) signals: when you need agency, use the agentic primitive, don't fake it with DAG pipelines.

**可提取的操作**: `OP-06 RouteByQueryType`, `OP-07 DecomposeMultiHop`, `OP-12 AgenticWorkflow`. Anti-pattern A9.

### Dilemma 4 — Long-context LLM (1M tokens) vs RAG

**困境**: Does a 1M-token context window eliminate the need for RAG?

**约束** (from `llamaindex.ai/blog/towards-long-context-rag`): 1M tokens ~60s latency + $0.50-$20/query; 10M tokens still doesn't cover large corpora; "lost in the middle" degrades quality by ~30%.

**决策步骤**:
1. Corpus >1M tokens → RAG mandatory.
2. p50 latency budget <5s → cannot afford full-context stuffing.
3. Per-query cost ceiling <$0.05 → same.
4. Apply LlamaIndex's three long-context patterns: Small-to-Big, Intelligent Routing, Retrieval-Augmented KV Caching.

**结果**: Long context does **not** replace RAG; it changes what RAG looks like. The bottleneck shifts from "fitting context" to "feeding right context in the right position" — making rerank + position-aware synthesis (`tree_summarize`) more important, not less.

**可提取的操作**: For any corpus >500k tokens or latency <5s: keep RAG. Use long-context as synthesis-stage capacity.

### Dilemma 5 — Sentence-Window vs Auto-Merging

**困境**: Both implement "embed small, return large". Not interchangeable.

**决策步骤**:
1. Docs have clear hierarchy (sections/headings) → Auto-Merging.
2. Docs are flat prose → Sentence-Window.
3. Queries are bursty multi-chunk → Auto-Merging escalates correctly.
4. Queries are point-fact with surrounding context → Sentence-Window.

**结果**: Both beat naive top-k on faithfulness. Match parser/retriever pair to document structure, not theoretical elegance. Always pair `SentenceWindowNodeParser` with `MetadataReplacementPostProcessor`.

---

## 反模式与边界 (Anti-patterns & Boundaries)

### Top 10 anti-patterns (full list in `references/R4-anti-patterns.md`)

| # | Anti-pattern | Correct move |
|---|---|---|
| A1 | Bump chunk_size when answers feel incomplete | Decouple embed-scope from synthesis-scope (Hierarchical / SentenceWindow) |
| A2 | Swap embedding model without re-embed | Rebuild index; tag artifact with embed model name+version |
| A3 | No eval loop; debug by anecdote | Stand up `RetrieverEvaluator` + `FaithfulnessEvaluator` + `RelevancyEvaluator` first |
| A4 | `ServiceContext` + manual config in every module | Pin `Settings.llm` and `Settings.embed_model` once at boot |
| A5 | `QueryPipeline` DAG for agentic logic | Use Workflows 1.0 (event-driven, supports cycles) |
| A6 | Naive `top_k=N`, no reranker | Widen top_k + add CohereRerank / SentenceTransformerRerank |
| A7 | Metadata not propagated to chunks; or metadata > 50% of chunk_size | Design metadata schema before ingestion; budget metadata tokens |
| A8 | Multi-modal RAG by base64-stuffing images into text | Use LlamaParse + multi-modal retrieval primitives |
| A9 | Wrap retrieval in a custom agent when a Router suffices | Default to `RouterQueryEngine`; escalate to Agent only with justification |
| A10 | Ingest once at deploy, never reconcile | `IngestionPipeline` + `docstore` + `UPSERTS_AND_DELETE` |

### Boundaries — when **not** to use LlamaIndex

- **B1**: Tiny static corpus (<100k tokens) → prompt-stuff with caching.
- **B2**: Pure structured/tabular data → DuckDB/SQL/BI. (LlamaIndex only when NL2SQL+RAG hybrid.)
- **B3**: Hard real-time / sub-100ms retrieval → raw vector store SDK, not a RAG framework.
- **B4**: Complex multi-agent orchestration → LangGraph or CrewAI leads; embed LlamaIndex retrievers as tools.
- **B5**: Highly specialized parsing requirements + team has engineering budget → custom stack (Unstructured.io + pgvector + custom retriever) gives more control.

### PR-review smells (instant red flags)

- `from llama_index import ServiceContext` → A4.
- `index.as_query_engine(similarity_top_k=20)` without a rerank postprocessor → A6.
- `SentenceSplitter(chunk_size=4096)` → likely A1.
- `Settings.embed_model = ...` in >1 file → A4 drift.
- `IngestionPipeline(...)` without `docstore=` → A10.
- A `Workflow` with no events or loops → over-engineered; should be a QueryEngine.
- An agent with a single retrieval tool → A9; should be a QueryEngine or RouterQueryEngine.

---

## 生态对照 (Ecosystem Context)

### Decision rubric

```
Q1. Primarily extracting from messy documents (PDFs, slides, tables, scans)?
   YES → LlamaIndex (+ LlamaParse) leads.
Q2. Primary challenge is multi-step agentic orchestration with many non-retrieval tools?
   YES → LangGraph / CrewAI leads; use LlamaIndex retrievers as tools.
Q3. Corpus small (<100k tokens) and static?
   YES → No framework; prompt-stuff with caching.
Q4. Pure structured/tabular data?
   YES → SQL/DuckDB/BI. Use LlamaIndex only for hybrid NL2SQL+RAG.
DEFAULT → LlamaIndex remains lead; layer LangGraph only if agentic logic emerges.
```

### Head-to-head highlights

| Vs | LlamaIndex wins when | Other wins when |
|---|---|---|
| **LangChain** | Retrieval quality and ingestion are the bottleneck; document-heavy | Orchestration is complex; many non-retrieval tools |
| **Haystack** | Modern LLM-centric docs; multi-modal; broader index taxonomy | YAML-configurable pipelines; classical IR feel |
| **Raw vector store** | Need >2 of {SentenceSplitter, IngestionPipeline, Reranker, Eval, Synthesizer} | Truly minimal RAG; team wants no framework |
| **DSPy** | Want structured retrieval infrastructure | Want automatic prompt optimization |
| **LangGraph (for agents)** | Retrieval-heavy with light agency (Workflows ergonomic here) | Many states, complex multi-agent state machines |
| **CrewAI / AutoGen** | (different category) | Multi-agent collaboration is the goal |

### The normative hybrid (2025-2026)

> Most production teams converge on: **LlamaIndex for retrieval & ingestion; LangGraph (or LlamaIndex Workflows) for orchestration; LangSmith / Phoenix for observability**.

---

## References

- `references/R1-architecture.md` — 5-layer model deep dive, Index taxonomy, Settings/Workflows
- `references/R2-sop-workflow.md` — full 8-stage RAG bootstrap protocol
- `references/R3-dilemma-cases.md` — 5 dilemma cases in full
- `references/R4-anti-patterns.md` — 13 official failure modes + 10 anti-patterns + boundaries
- `references/R5-ecosystem-context.md` — comparison matrix, hybrid patterns
- `intermediate/operation_candidates.json` — machine-readable operation list

### Primary sources (cited inline above)

- `developers.llamaindex.ai/python/framework/` (architecture homepage)
- `developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/`
- `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/` (official 13 failure modes)
- `developers.llamaindex.ai/python/framework/module_guides/indexing/index_guide/`
- `developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/`
- `llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`
- `llamaindex.ai/blog/llamaindex-enhancing-retrieval-performance-with-alpha-tuning-in-hybrid-search-in-rag-135d0c9b8a00`
- `llamaindex.ai/blog/towards-long-context-rag`
- `llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems`
- `docs.llamaindex.ai/en/stable/module_guides/supporting_modules/service_context_migration/`
- `github.com/run-llama/llama_index` (README, issues `#12200`, `#13792`, `#6465`)
- `cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex`
- `learn.deeplearning.ai/courses/building-agentic-rag-with-llamaindex/`
- `ibm.com/think/topics/llamaindex-vs-langchain`
- `statsig.com/perspectives/llamaindex-rag-retrieval`
- `tianpan.co/blog/2026-04-12-hybrid-search-production-bm25-dense-embeddings`
