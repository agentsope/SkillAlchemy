# R2 · SOP Workflow — From Raw Data to Production RAG

This is the canonical "RAG bootstrap" sequence as encoded in LlamaIndex's own optimization guide (`developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/`), the failure-mode checklist, and the long-context blog (`llamaindex.ai/blog/towards-long-context-rag`). It is intentionally **iterative**: every stage gates on an eval result before adding complexity.

## Stage 0 — Decide if you should use LlamaIndex at all

Before writing any code, answer (see `R4` and `R5` for full rules):

- Is the data **unstructured** (PDF / HTML / Markdown / code / mixed)? If purely tabular SQL → skip LlamaIndex, use text-to-SQL or DuckDB.
- Is the corpus **>100k tokens total** OR will it grow? If <100k and static → just stuff into the context window.
- Is **retrieval quality the bottleneck** vs orchestration complexity? If you mainly need multi-agent orchestration → LangGraph/CrewAI lead; LlamaIndex can be a tool *inside* them.

If yes/yes/yes → proceed.

## Stage 1 — Ingestion baseline (cheap, fast, observable)

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.node_parser import SentenceSplitter

Settings.llm = OpenAI(model="gpt-4o-mini")           # default LLM
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=20)

docs  = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(docs)
qe    = index.as_query_engine(similarity_top_k=4)
```

**Defaults LlamaIndex chose for you** (and why):
- `chunk_size=1024` — empirically optimal in the team's own evaluation across {128, 256, 512, 1024, 2048} (`llamaindex.ai/blog/evaluating-the-ideal-chunk-size-...`).
- `chunk_overlap=20` — small but nonzero so concepts cross boundaries.
- `similarity_top_k=2` (or 4 in many examples) — start small to surface retrieval bugs early.

> Cited findings from the chunk-size evaluation: faithfulness **peaked at 1024**, relevancy **also maxed at 1024**, response time grew only mildly.

**Gate before moving on:** can you `index.as_retriever().retrieve("test query")` and see the right chunks? If not, the bug is upstream (parsing / metadata), not in retrieval.

## Stage 2 — Stand up the eval loop (the single most-skipped step)

> "Most failures trace back to weak retrieval or sloppy ingestion, not the LLM" — production RAG post-mortem (`statsig.com/perspectives/llamaindex-rag-retrieval`).

```python
from llama_index.core.evaluation import (
    DatasetGenerator, FaithfulnessEvaluator, RelevancyEvaluator,
    RetrieverEvaluator,
)

qa = DatasetGenerator.from_documents(docs).generate_dataset_from_nodes(num=50)
ret_eval = RetrieverEvaluator.from_metric_names(["mrr","hit_rate"], retriever=index.as_retriever())
```

Track 4 metrics:
1. **Hit-rate / MRR** — retriever-only, no LLM cost.
2. **Faithfulness** — does the answer stay grounded in retrieved context? (no ground truth needed)
3. **Relevancy** — does the answer address the query?
4. **Latency** — p50 / p95.

Cited at `developers.llamaindex.ai/python/framework-api-reference/evaluation/` and `cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex`. **Every subsequent change must be gated on these numbers**.

## Stage 3 — Optimization priority order (LlamaIndex's own playbook)

From `basic_strategies/basic_strategies/`, in the order LlamaIndex recommends:

1. **Prompt engineering** — cheapest, fastest. Customize QA prompt template, add few-shots.
2. **Embedding model** — pick from MTEB leaderboard; `bge-large` or domain-tuned for jargon-heavy corpora; **re-embed entire index if you change it** (failure #4).
3. **Chunk size customization** — sweep 256/512/1024/2048; pick by faithfulness × latency frontier.
4. **Hybrid search** — add BM25 when corpus contains identifiers, code, error strings (see R3 Dilemma 2).
5. **Metadata filters** — for multi-tenant or multi-collection corpora.
6. **Document/chunk decoupling** — Hierarchical or Sentence-Window (embed small, return large; see R3 Dilemma 1).
7. **Reranking** — Cohere / SentenceTransformer / ColBERT cross-encoder; widen top_k to 20-50, rerank to 3-5.

Note the order: **prompts first, reranking last**. Reranking is high-impact but expensive; you want to exhaust the cheap knobs first.

## Stage 4 — Compose for query heterogeneity

Once retrieval-quality is acceptable on simple queries, audit your *query distribution*:

| Query shape | Right primitive |
|---|---|
| "Summarize doc X" | `SummaryIndex` per doc, routed |
| "Find the clause about X" | `VectorStoreIndex` + filters |
| "Compare X and Y across docs" | `SubQuestionQueryEngine` (decompose → per-sub-engine → synthesize) |
| "What entities relate to X?" | `PropertyGraphIndex` |
| Mixed of the above | `RouterQueryEngine` over per-task engines (LLM or Pydantic selector) |

Source: DeepLearning.AI's *Building Agentic RAG with LlamaIndex* course; `developers.llamaindex.ai` sub-question and router docs. The progression is: **single engine → router → agent**.

## Stage 5 — Production hardening (the failure-mode checklist)

From `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/`:

| # | Failure | Production fix |
|---|---|---|
| 3 | Index fragmentation (stale docs, dupes) | `IngestionPipeline` with `docstore` + `UPSERTS_AND_DELETE` strategy |
| 4 | Config drift (embedding mismatch) | Pin `Settings.embed_model` once; store model name/version in index metadata |
| 6 | Context overflow | `tree_summarize` synthesizer; rerank to drop to top-3 |
| 11 | Session/cache memory breaks | Consistent session keys; separate long-term vs short-term store; regression tests for conversation sequences |
| 12 | Observability gaps | Enable tracing; log query + nodes + scores + index_id + LLM prompt for every failure |
| 13 | Deployment ordering | Version indices as artifacts with snapshot IDs; ingestion must complete before traffic routing; health-check with known-good queries |

## Stage 6 — When to escalate to agentic / Workflows

You escalate from `QueryEngine` → `Workflow`/`Agent` when you need **at least one of**:

- A loop (e.g., "retrieve → check → re-query if insufficient").
- Tool calls beyond retrieval (calculator, web search, code exec).
- State that survives across query turns.
- Multiple specialized retrievers chosen at runtime.

The 2025 canonical pattern is: wrap each query engine as a `QueryEngineTool`, hand the toolbox to a `FunctionAgent` or build a `Workflow` with explicit retrieval / synthesis / verification steps. Citation: `developers.llamaindex.ai/python/llamaagents/workflows/`, `llamaindex.ai/blog/announcing-workflows-1-0-...`.

## Stage 7 — Production data lifecycle

```python
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy

pipeline = IngestionPipeline(
    transformations=[SentenceSplitter(chunk_size=1024, chunk_overlap=20),
                     OpenAIEmbedding()],
    docstore=SimpleDocumentStore(),
    vector_store=QdrantVectorStore(...),
    docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
)
pipeline.run(documents=docs)
```

Cited at `developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/`. Three strategies:

- `DUPLICATES_ONLY` — skip if hash exists.
- `UPSERTS` — update if doc_id exists & hash changed.
- `UPSERTS_AND_DELETE` — also propagate deletes (default for live corpora).

Without a docstore, deduplication is impossible — you will silently re-ingest and corrupt retrieval scores.

## Stage 8 — The full SOP, compressed

```
[Stage 0] Verify LlamaIndex is the right tool (unstructured, retrieval-bottleneck, growing corpus)
[Stage 1] VectorStoreIndex baseline @ chunk_size=1024, top_k=4 — ship to eval bench
[Stage 2] Stand up eval loop (MRR, hit-rate, faithfulness, relevancy, latency)
[Stage 3] Optimize in order: prompts → embed model → chunk sweep → hybrid → metadata → small-to-big → rerank
[Stage 4] Audit query distribution; introduce SubQuestion / Router for heterogeneity
[Stage 5] Apply failure-mode checklist (esp. IngestionPipeline + Settings pinning + observability)
[Stage 6] Escalate to Workflows/Agent only when cycles or tools are needed
[Stage 7] Encode ingestion as IngestionPipeline artifact with docstore lifecycle
```

## Sources

- `https://developers.llamaindex.ai/python/framework/optimizing/basic_strategies/basic_strategies/`
- `https://developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/`
- `https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`
- `https://www.llamaindex.ai/blog/towards-long-context-rag`
- `https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/`
- `https://cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex`
- `https://learn.deeplearning.ai/courses/building-agentic-rag-with-llamaindex/`
- `https://www.statsig.com/perspectives/llamaindex-rag-retrieval`
