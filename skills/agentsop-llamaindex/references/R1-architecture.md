# R1 · LlamaIndex Architecture & Mental Model

## 0. One-sentence framing

LlamaIndex is not a "vector DB wrapper" and not a "general agent framework". It is a **data framework whose central abstraction is the Index** — a queryable intermediate representation that sits between raw private data and an LLM. The whole API surface is structured to make every step of that pipeline a swappable, observable object.

> "LlamaIndex helps you ingest, transform, index, retrieve, and synthesize answers from your own data across many sources." — `developers.llamaindex.ai/python/framework/`

## 1. The 5-layer mental model

```
                Documents
                    ↓        (chunking / parsing / metadata extraction)
                  Nodes
                    ↓        (embedding / structuring)
                  Index            ← the first-class object
                    ↓        (retriever mode, top-k, filters, reranker)
                Retriever
                    ↓        (query transformation, fusion, recursion)
              Query Engine
                    ↓        (LLM call, refine / tree_summarize / compact)
            Response Synthesizer
                    ↓
                 Response
```

Source: `developers.llamaindex.ai/python/framework/` and the high-level concepts guide; matches the architecture description repeated in every "Getting Started" doc and reaffirmed by 2025 walkthroughs (e.g., `medium.com/@gautsoni/llamaindex-for-beginners-2025-...`).

### Why 5 layers and not 2?

Most homemade RAGs collapse to "chunk → embed → top-k → LLM". LlamaIndex deliberately splits this into 5 because **each layer has its own failure mode and its own optimization knob** (see `R4-anti-patterns.md` for the failure-mode checklist that maps almost 1:1 onto these layers).

| Layer | Failure when missing | LlamaIndex knob |
|---|---|---|
| Documents | Garbage-in: tables/figures lost, boilerplate kept | `LlamaParse`, custom Readers, metadata extractors |
| Nodes | Wrong chunk granularity | `NodeParser` / `SentenceSplitter` / `HierarchicalNodeParser` |
| Index | Wrong retrieval primitive for the task | `VectorStoreIndex` / `SummaryIndex` / `PropertyGraphIndex` / ... |
| Retriever | Top-k too narrow, no rerank, no hybrid | `top_k`, `BM25Retriever`, `QueryFusionRetriever`, postprocessors |
| Response Synthesizer | Context overflow, "lost in the middle" | `refine` / `tree_summarize` / `compact` modes |

## 2. What is a Node, really?

A `Node` is **not** "a chunk of text". It is a typed object that carries:

- `text` (the chunk)
- `metadata` (filterable key-value, propagated from the parent Document)
- `relationships` (PREVIOUS / NEXT / PARENT / CHILD links to other nodes — this is what enables AutoMergingRetriever and SentenceWindow)
- `embedding` (lazy; filled when the Index requires it)
- `id_` and `ref_doc_id` (lifecycle / deduplication keys)

> "Indexes store data in Node objects, which represent chunks of the original documents." — homepage docs.

The relationships field is the often-missed bit: LlamaIndex's advanced retrievers (Recursive, AutoMerging, Sentence-Window) rely on it. A Node is therefore better thought of as **a node in a graph of chunks**, not a row in a vector table. This is what differentiates LlamaIndex from a pure vector-store SDK.

## 3. Index types: what changes between them

From `developers.llamaindex.ai/python/framework/module_guides/indexing/index_guide/`:

| Index | Storage shape | Retrieval | When |
|---|---|---|---|
| **VectorStoreIndex** | Nodes + embeddings in a vector store | Top-k cosine/dot similarity | Default. Semantic Q&A over chunks. ~90% of use cases. |
| **SummaryIndex** (formerly ListIndex) | Nodes in an ordered list (no embeddings required) | Returns **all** nodes (or top-k via optional embedding) | Summarisation; small corpus; "what does this whole doc say?" |
| **TreeIndex** | Hierarchical LLM-built summaries | Traverses root→leaf with `child_branch_factor` | Tree-structured content, progressive zoom-in |
| **KeywordTableIndex** | Keyword → node mapping (LLM-extracted) | Keyword overlap | Keyword-heavy queries, no embeddings budget |
| **KnowledgeGraphIndex / PropertyGraphIndex** | Triples (subj, pred, obj) ± embeddings | Keyword + synonym + vector hybrid over triples | Multi-hop reasoning, entity relationships |
| **DocumentSummaryIndex** | Per-doc LLM summary + node refs | Summary→doc routing then chunk retrieval | Mixed-collection corpora, document-level routing |

### The strategic implication

These are **not interchangeable** — `SummaryIndex` answers "summarize this report" cheaply (no embeddings to build, but N LLM calls at query time) where `VectorStoreIndex` would be wrong (it can't see the whole doc). Hence `RouterQueryEngine` (R2 / R3) — a router over multiple indices is often the right top-level shape.

## 4. Retriever vs Query Engine vs Response Synthesizer

A confusion source for users. Concretely:

- **Retriever** returns `List[NodeWithScore]`. No LLM call. Pure retrieval.
- **Response Synthesizer** takes nodes + query → string. This is where the LLM lives (refine / tree_summarize / compact / accumulate modes).
- **Query Engine** = Retriever + (optional postprocessors / rerankers) + Response Synthesizer, bundled as one `.query()` interface. It is the "facade".

Why split them? So you can:
1. Test retrieval quality without burning LLM tokens (use Retriever + RetrieverEvaluator).
2. Swap the synthesizer (e.g. `tree_summarize` for long contexts) without touching retrieval.
3. Insert NodePostprocessors (rerankers, time-decay, metadata replacement for sentence-window) between the two cleanly.

Cited at `developers.llamaindex.ai/python/framework/module_guides/deploying/query_engine/` (Streaming guide and Query Engine module guide).

## 5. Settings (the Global Config Singleton)

Since v0.10, the global `Settings` object replaces the deprecated `ServiceContext`:

```python
from llama_index.core import Settings
Settings.llm = Ollama(model="llama2")
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.chunk_size = 1024
```

Crucial property: **lazy instantiation** — modules only load LLM/embed if they need them. Old `ServiceContext` forced eager loading and was a notorious source of double-config bugs (`docs.llamaindex.ai/.../service_context_migration/`). Failure modes #4 and #5 in the official checklist (embedding-model mismatch, config drift) are precisely caused by *not* using a single global Settings.

## 6. Workflows: the 2025 successor to QueryPipeline

LlamaIndex shipped `QueryPipeline` as a declarative DAG in 2024. It was deprecated within a year because **agentic logic needs cycles**, which DAGs forbid. The replacement (`Workflows 1.0`, announced 2025-06-30) is event-driven: every step subscribes to and emits events, naturally supporting loops, branching, retries.

> "A fundamental aspect of DAGs is that they are acyclic with no loops, but in a world that's more agentic, the inability to perform loops in an AI application's logic is simply unacceptable." — `llamaindex.ai/blog/announcing-workflows-1-0-...`

For any new project in 2025+, the canonical orchestration primitive is **Workflows**, not QueryPipeline. Agents (FunctionAgent / ReActAgent) are themselves built on top of Workflows.

## 7. What's the *operating system* under the architecture?

Three principles, abstracted from the docs:

1. **Indices are first-class.** "Index" is a noun in LlamaIndex's grammar, not a verb. You pick the right Index for the task (`VectorStoreIndex` ≠ `SummaryIndex` ≠ `PropertyGraphIndex`). LangChain by contrast treats retrieval as a verb (`.as_retriever()` on a vector store).
2. **Every transform is inspectable.** Documents, Nodes, NodeWithScore, Response — each layer hands off a typed object you can print, log, replay. This is why observability is a tier-1 concern (failure #12) rather than a bolt-on.
3. **Chunking is architecture, not preprocessing.** Node-parsers (Hierarchical, Sentence-Window) build *relationships* between chunks at ingestion time so advanced retrievers can exploit them. The mental flip: don't think "split into chunks", think "build a chunk-graph".

## 8. Source list (R1)

- `https://developers.llamaindex.ai/python/framework/`
- `https://developers.llamaindex.ai/python/framework/module_guides/indexing/index_guide/`
- `https://developers.llamaindex.ai/python/framework/module_guides/deploying/query_engine/`
- `https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/service_context_migration/`
- `https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems`
- `https://github.com/run-llama/llama_index` (README)
- `https://medium.com/@gautsoni/llamaindex-for-beginners-2025-a-complete-guide-to-building-rag-apps-from-zero-to-production-cb15ad290fe0`
