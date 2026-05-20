# R4 · Anti-patterns & Boundaries

This file is the negative-space companion to R2. Sources: LlamaIndex's own `rag_failure_mode_checklist` (the authoritative list of 13 failure modes, each with symptoms + fixes), GitHub issues, production post-mortems, and the LlamaIndex team's deprecation history (ServiceContext, QueryPipeline).

## 1. The official 13 failure modes (with one-line digest)

From `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/`:

| # | Failure | Symptom | Minimal fix |
|---|---|---|---|
| 1 | **Retrieval hallucination** | Answers sound confident but factually wrong; retrieved chunks share keywords with query but discuss different topic | Add reranker; raise top_k with pruning; hybrid search; relevance threshold |
| 2 | **Wrong chunk selection (poor chunking)** | Partial/incomplete answers; correct info exists but chunks don't contain it fully | Tune chunk_size (1024+) / overlap (10-20%); SentenceSplitter; try Hierarchical or SentenceWindow |
| 3 | **Index fragmentation** | Different answers for same question across runs; contradictory chunks; stale data | IngestionPipeline with docstore dedup; version metadata; periodic rebuild |
| 4 | **Config drift (embedding mismatch)** | Sudden quality drop after code change; abnormally low similarity scores | Pin Settings.embed_model; store model name in metadata; full re-embed on change |
| 5 | **Embedding model mismatch** | Good general results, poor domain results; keyword search outperforms vector | Domain-adapted embedding; hybrid; pre-deploy eval on synthetic QA |
| 6 | **Context window overflow** | Truncated responses; token errors; quality degrades with higher top_k | tree_summarize / refine synthesizer; reduce top_k after rerank; max_tokens cap |
| 7 | **Missing metadata filtering** | Cross-contamination between categories; unrelated content | Structured metadata at ingestion; MetadataFilters at query; auto-retrieval; separate indices |
| 8 | **Poor query understanding** | Simple rephrasing changes results; short queries fail | HyDEQueryTransform; SubQuestionQueryEngine; LLM-based query rewriting; few-shots |
| 9 | **LLM synthesis failures** | Retrieved chunks correct but answer wrong; LLM ignores context | Stronger LLM; customize QA prompt to enforce context-only; Refine mode; system prompt |
| 10 | **Embedding metric mismatch** | Top-1 wrong but right docs in top-k; tight similarity clustering | Inspect full top-k; normalize/trim chunks; reranking with different scoring |
| 11 | **Session/cache memory breaks** | Same questions return different answers across days; vector store sometimes empty | Consistent session/user keys; separate long-term vs short-term store; regression tests |
| 12 | **Observability gaps** | Cannot inspect retrieved nodes / scores / prompts | Full tracing; log query+nodes+scores+index_id+LLM prompt for every failure |
| 13 | **Index lifecycle / deployment ordering** | Works locally, fails in prod; half-built indices | Version indices as artifacts; snapshot IDs; ingestion completes before traffic routing; ingestion-as-script not manual |

## 2. The most common anti-patterns (distilled from the 13 + community)

### A1 — "Just bump the chunk_size when answers feel incomplete"
The lazy fix. Causes failure #6 (context overflow) on the synthesis side and metadata-starvation warnings (GitHub `#12200`, `#13792`) when chunk_size collides with the embedding model's input window. **Correct move**: introduce decoupled small-embed/large-return (Hierarchical / Sentence-Window) — see R3 Dilemma 1.

### A2 — "Swap embedding model in place without re-embed"
Mixes vectors from two embedding spaces; cosine similarity becomes meaningless; retrieval quality silently degrades. Failure #4 explicitly: *"Sudden quality drop after code changes; abnormally low similarity scores."* **Correct move**: rebuild index *and* tag the index artifact with the embedding model name + version.

### A3 — "No eval loop, ship to prod, debug by anecdote"
The single highest-cost anti-pattern. Without `RetrieverEvaluator`/`FaithfulnessEvaluator`/`RelevancyEvaluator`, every later change is a guess. Cited universally — failure #2/#5/#9 all become non-recoverable without an offline eval set.

### A4 — "ServiceContext + manual config in every module"
ServiceContext was deprecated in v0.10 (Feb 2024). Continuing to use it forces eager loading of every component and creates the conditions for config drift (failure #4). **Correct move**: pin `Settings.llm` and `Settings.embed_model` once at app boot; never inline-construct (`docs.llamaindex.ai/.../service_context_migration/`).

### A5 — "QueryPipeline DAG for agentic logic"
QueryPipeline was deprecated in favor of Workflows in 2025 precisely because DAGs cannot loop. Teams that built loops by re-running a DAG in a Python `while` were hitting an architectural smell — the framework's own response was to ship `Workflows 1.0` (`llamaindex.ai/blog/announcing-workflows-1-0-...`). **Correct move**: use Workflows for any logic needing cycles, retries, or branching.

### A6 — "Naive top_k=N for everything, no reranker"
Causes failure #1 (retrieval hallucination — top results share keywords but not topic) and #10 (top-1 wrong but right docs lower in list). Reranking is *the* highest-leverage retrieval intervention after chunking — the LlamaIndex playbook explicitly states "chunk size, overlap, reranking, and query reformulation have an outsized effect on accuracy" (`developers.llamaindex.ai` advanced strategies).

### A7 — "Treat metadata as decoration; don't propagate to chunks"
Loses the ability to filter (failure #7), and worse, lets metadata bloat fill chunks when chunk_size is small (GitHub `#12200`, `#13792` — *"Metadata length (1527) is longer than chunk size (1024)"*). **Correct move**: design metadata schema before ingestion; budget metadata token-count relative to chunk_size.

### A8 — "Try multi-modal RAG by stuffing image base64 into text fields"
Causes garbage embeddings. LlamaIndex's multi-modal RAG pattern is text+image hybrid chunks via LlamaParse, with image links and text embeddings retrieving in parallel (`llamaindex.ai/blog/multimodal-rag-in-llamacloud`). **Correct move**: use LlamaParse for parsing, multi-modal retrieval primitives, not text-only retrieval.

### A9 — "Wrap LlamaIndex in a custom agent framework when a Router would do"
See R3 Dilemma 3. RouterQueryEngine handles >80% of "agentic routing" needs at a fraction of the complexity. Reach for FunctionAgent/ReActAgent only when cycles or non-retrieval tools are required.

### A10 — "Ingest once at deploy, never reconcile"
Failure #3 + #13. Without `IngestionPipeline` + `docstore` + an upsert strategy, document deletes never propagate and updates create duplicates. **Correct move**: encode ingestion as an `IngestionPipeline` with `UPSERTS_AND_DELETE` strategy run on a schedule.

## 3. Boundaries — when *not* to use LlamaIndex

### B1 — Tiny static corpus (< ~100k tokens)
If the entire knowledge base fits in a single context window and never changes, the right answer is **prompt stuffing** (with prompt caching) — not RAG. The overhead of building an index, an eval loop, and an ingestion pipeline is not justified.

### B2 — Pure structured / tabular data
LlamaIndex *can* do text-to-SQL (`developers.llamaindex.ai/.../structured_data/`), but it is not the right tool for "select / group / aggregate over a clean relational table". Use DuckDB, Pandas, or a real BI tool. Use LlamaIndex when **structured + unstructured live in the same query** (NL2SQL + RAG hybrid).

### B3 — Hard real-time / sub-100ms retrieval
Top-1 vector retrieval can hit single-digit ms, but the full LlamaIndex query path (retrieval + rerank + synthesis) is dominated by the LLM call (hundreds of ms minimum). For real-time signals (autocomplete, ad ranking), use a raw vector store SDK or a search engine, not a RAG framework.

### B4 — Single-agent orchestration with rich tool ecosystem
For complex multi-step agentic workflows with many non-retrieval tools (browser, code, memory), **LangGraph** has finer-grained control (`zenml.io/blog/llamaindex-alternatives`; `ibm.com/think/topics/llamaindex-vs-langchain`). The recommended hybrid: **LlamaIndex as retrieval layer, LangGraph as orchestration layer**.

### B5 — Highly proprietary parsing requirements
If documents need extreme custom parsing (e.g., specific scientific notation, custom table semantics), and your team has the engineering budget, building on a lower-level stack (Unstructured.io + pgvector + custom retriever) gives you more control. LlamaIndex is opinionated; opinions are usually right; sometimes they aren't.

## 4. Spotting an anti-pattern at PR-review time

Quick smells in code reviews:

- `from llama_index import ServiceContext` → A4.
- `index.as_query_engine(similarity_top_k=20)` without a rerank postprocessor → A6.
- `SentenceSplitter(chunk_size=4096)` → likely A1.
- `Settings.embed_model = ...` appearing in multiple files → A4 (drift risk).
- `IngestionPipeline(...)` without `docstore=` → A10.
- Inline `OpenAIEmbedding(...)` constructor in retrieval code instead of using global Settings → A4.
- A `Workflow` that doesn't use any events / loops → over-engineering; could be a `QueryEngine`.
- Agent with a single retrieval tool → A9; should be a `QueryEngine` or `RouterQueryEngine`.

## Sources

- `https://developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/`
- `https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/service_context_migration/`
- `https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems`
- `https://github.com/run-llama/llama_index/issues/12200`
- `https://github.com/run-llama/llama_index/issues/13792`
- `https://github.com/run-llama/llama_index/issues/6465`
- `https://www.llamaindex.ai/blog/multimodal-rag-in-llamacloud`
- `https://www.zenml.io/blog/llamaindex-alternatives`
- `https://www.ibm.com/think/topics/llamaindex-vs-langchain`
- `https://markaicode.com/architecture/rag-architecture-with-llamaindex/`
