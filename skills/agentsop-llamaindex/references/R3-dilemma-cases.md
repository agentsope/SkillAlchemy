# R3 · Dilemma Cases

Each case is a real hard decision documented in LlamaIndex's blog, official failure-mode checklist, GitHub issues, or production write-ups. Hypothetical / textbook cases are excluded. Structure: **困境 / 约束 / 决策步骤 / 结果 / 可提取的操作**.

---

## Dilemma 1 — "Chunks too small lose context; too big lose precision. Where to set chunk_size?"

### 困境
Every RAG team eventually finds: at `chunk_size=256` embeddings are precise but the LLM gets fragments without enough context to answer. At `chunk_size=2048` chunks have rich context but a single chunk's embedding becomes a "topic average" — the precise sentence answering the query gets buried, recall on specific queries drops.

> "Every chunking strategy trades off context preservation against retrieval precision—smaller chunks match queries more precisely but lose surrounding context, while larger chunks preserve relationships between ideas but dilute relevance in embeddings." (`medium.com/@sayantanmanna840/rag-chunking-strategies-...`)

The official failure-mode checklist documents both poles as separate failures (#2: wrong chunk selection from too-small; #6: context-window overflow from too-large).

### 约束
- Cannot test in production; need a deterministic offline answer.
- Token budget on the synthesis side caps how many chunks can be packed.
- Embedding model has a fixed input window (e.g. 512 tokens for many BGE variants — over-chunking is a hard error).
- Metadata is propagated into each chunk's payload, so very small chunks become "all metadata" (failure #2 manifests as metadata-length warnings — see GitHub `run-llama/llama_index#12200`, `#13792`).

### 决策步骤 (canonical LlamaIndex method)
1. Generate ~20 eval Q&A pairs via `DatasetGenerator.from_documents(...)`.
2. Sweep `chunk_size ∈ {128, 256, 512, 1024, 2048}` with `overlap = 0.1-0.2 × chunk_size`.
3. For each, build a `VectorStoreIndex`, evaluate via `FaithfulnessEvaluator` + `RelevancyEvaluator` + record `avg_response_time`.
4. Plot the three curves; pick the chunk_size on the faithfulness/relevancy frontier where latency is still acceptable.
5. **If the frontier is non-flat** (i.e., no single chunk_size dominates), do not pick a compromise — instead **decouple embed-scope from synthesis-scope** by switching to `HierarchicalNodeParser + AutoMergingRetriever` *or* `SentenceWindowNodeParser`. Embed small (e.g. 128-256), return large (e.g. 1024-2048).

### 结果
LlamaIndex's own published evaluation (`llamaindex.ai/blog/evaluating-the-ideal-chunk-size-...`) on Uber's 10-K: faithfulness peaked at chunk_size **1024**, relevancy maxed at **1024**, response time grew only mildly. 1024 became the framework default for prose. For code, 80-160 tokens is the cited working range (`statsig.com/perspectives/llamaindex-rag-retrieval`).

For corpora where the eval curve does *not* converge on a single chunk_size, the decoupling pattern via Hierarchical/Sentence-Window wins — embed small chunks for precision, then return larger parent chunks (AutoMergingRetriever) or surrounding sentences (SentenceWindow + MetadataReplacementPostProcessor) for synthesis context.

### 可提取的操作
- `OP-02 TuneChunkSize`: always sweep before pinning; default to 1024 for prose, 80-160 for code if no time to sweep.
- `OP-05 DecoupleChunkScope`: when no flat winner emerges, switch to small-embed / large-return; do *not* compromise on a single chunk_size.
- Never let metadata occupy >50% of chunk_size (issue #12200) — strip or shorten metadata before increasing chunk_size.

---

## Dilemma 2 — "Hybrid BM25+dense vs pure dense — is the complexity worth it?"

### 困境
Dense embeddings are the modern default; BM25 looks like "the old keyword thing". Adding hybrid retrieval doubles the index footprint, requires alpha-tuning, and complicates the pipeline. Is the complexity justified?

### 约束
- Pure dense retrieval *silently fails* on exact identifiers, code, error strings, product SKUs, API names, rare jargon.

> "Dense embedding models destroy lexical identity by pooling token representations, so when querying specific error strings, the resulting vector captures something like 'document about SSL errors' rather than 'document containing this specific error string'. BM25 scores against an inverted index of exact tokens." (`tianpan.co/blog/2026-04-12-hybrid-search-production-bm25-dense-embeddings`)

- LlamaIndex's failure mode #5 (embedding-model mismatch) explicitly recommends "combine vector with keyword search (hybrid)" as one of the canonical fixes.
- Alpha tuning (`alpha=0` → pure BM25, `alpha=1` → pure dense) is a per-query-type hyperparameter; one alpha rarely fits all (`llamaindex.ai/blog/llamaindex-enhancing-retrieval-performance-with-alpha-tuning-...`).

### 决策步骤
1. Build a **query-type taxonomy** for your traffic: semantic ("what does X mean?") vs lexical ("find error code ABC-123") vs mixed.
2. If lexical share is <5% → dense-only is fine; skip hybrid.
3. If lexical share is 5-50% → add hybrid via `QueryFusionRetriever([vector_retriever, BM25Retriever])` or vendor hybrid (Qdrant, Milvus, Weaviate) with alpha tuning.
4. If lexical share is >50% (e.g. legal citations, code search, log search) → consider BM25-first with dense as a fallback rerank signal.
5. Evaluate alpha at `{0.0, 0.25, 0.5, 0.75, 1.0}` on a labeled subset of each query type; tune per type, not globally.

### 结果
Production case studies (Tian Pan blog; Statsig perspectives piece) report hybrid lift on the **lexical slice** of traffic with no degradation on the semantic slice — *if alpha is tuned per query type*. A flat global alpha often loses to pure dense on semantic queries, which is why teams sometimes wrongly conclude "hybrid didn't help".

### 可提取的操作
- `OP-04 AddHybridBM25`: trigger is **traffic-driven** (presence of lexical-identity queries), not theoretical.
- Tune alpha per query type, not globally — otherwise hybrid can underperform dense.
- For very lexical corpora (code, logs), invert the default: BM25 first, dense as reranker signal.

---

## Dilemma 3 — "Agent on top of RAG, RAG as a tool, or just a Router?"

### 困境
A team has shipped a working `VectorStoreIndex + as_query_engine`. Users now ask compare/contrast questions, summary questions, and "did you also check doc X?" follow-ups. Three architectural options:
- **A. Router-only**: `RouterQueryEngine` over multiple per-task `QueryEngines`, LLM picks one tool per query.
- **B. RAG-as-tool**: Build a `FunctionAgent` / `ReActAgent` and expose each query engine as a `QueryEngineTool`; agent chooses, can call multiple, can loop.
- **C. SubQuestion decomposition**: `SubQuestionQueryEngine` decomposes the user query into sub-questions and routes each to a sub-engine.

> "The router is the simplest form of agentic RAG ... in the router approach, a router engine with the help of an LLM determines what tool or query engine to use." (`medium.com/aimonks/agentic-rag-with-llama-index-router-query-engine-01-...`)

### 约束
- Latency budget: agents add ≥1 extra LLM round-trip per step.
- Failure surface: agents introduce planning errors that a router cannot make.
- Observability: routers are easy to log; agent loops are harder to debug (failure #12).
- Most queries are *not* multi-hop; over-architecting hurts the median user.

### 决策步骤
1. Measure **what fraction of queries actually need multi-step reasoning** in real traffic. If <20%, do not start with an agent.
2. If query distribution is **heterogeneous-but-single-step** (some summary, some lookup, some compare) → **Option A (Router)**. Cheapest, most predictable.
3. If queries are **compositional and well-shaped** (always "compare X and Y") → **Option C (SubQuestionQueryEngine)**. Deterministic decomposition, no agent state.
4. If queries require **tool calls beyond retrieval** (calculator, web fetch, code exec, follow-up retrieval based on intermediate result) → **Option B (Agent)**, ideally built on Workflows 1.0 so cycles are first-class.
5. Whichever you pick, **wrap retrieval engines as `QueryEngineTool` with rich `description=`** — the description is what the router/agent reads to decide.

### 结果
- DeepLearning.AI's *Building Agentic RAG with LlamaIndex* course uses the explicit progression Router → Tool-using Agent → ReAct, signaling this is the recommended ladder.
- Production guidance (`statsig.com`, `medium.com/aimonks/...`) consistently warns against jumping to Option B prematurely — most "agent failures" trace back to the agent doing what a router could have done, badly.
- The LlamaIndex team's own pivot to **Workflows 1.0** (June 2025) signals that when you need agency, *use the agentic primitive*, don't fake it with QueryPipeline DAGs.

### 可提取的操作
- `OP-06 RouteByQueryType`: default first agentic step is Router, not Agent.
- `OP-07 DecomposeMultiHop`: SubQuestionQueryEngine is the right answer for *fixed-shape* compositional queries.
- `OP-12 AgenticWorkflow`: escalate only when cycles/tools/state are actually required.
- Always tune the `description` on every `QueryEngineTool` — it is the router/agent's only signal.

---

## Dilemma 4 — "Long-context LLM (1M tokens) is here. Do we even need RAG?"

### 困境
With 1M+ token context windows (Gemini, Claude, GPT-4-Turbo class), a tempting take is: "stuff everything in, skip retrieval, skip chunking — RAG was a hack around small context". Is this right?

### 约束 (from `llamaindex.ai/blog/towards-long-context-rag`)
- **Cost**: "Processing 1M tokens takes ~60 seconds and can cost anywhere from $0.50 to $20 with current pricing."
- **Latency**: A user-facing chat at p50 latency >60s is unshippable.
- **Corpus size**: "10M tokens is not enough for large document corpuses — kilodoc retrieval is still a challenge."
- **Lost-in-the-middle**: LLMs weight context-window beginning and end more heavily; relevant info in the middle is empirically downweighted (~30% degradation reported on long contexts).

### 决策步骤
1. Estimate corpus size in tokens. If >1M tokens → RAG is mandatory; long-context cannot help.
2. Estimate per-query latency budget. If <5s p50 → cannot afford full-context stuffing even on small corpora.
3. Estimate per-query cost ceiling. If <$0.05 → cannot afford full-context stuffing.
4. If small corpus + loose latency/cost → consider hybrid: route small/cold corpora to full-context, route large/hot corpora through RAG.
5. Apply LlamaIndex's three "long-context RAG" patterns:
   - **Small-to-Big**: embed small, send large — exactly the same primitive as Dilemma 1's resolution.
   - **Intelligent Routing**: per-query-type pipeline (specific query → RAG; summarize → tree-summarize over full corpus).
   - **Retrieval-Augmented KV Caching**: cache document activations for reuse.

### 结果
LlamaIndex's published position: long-context **does not replace RAG**; it *changes what RAG looks like*. The bottleneck shifts from "fitting context" to "feeding the right context in the right position" — making rerank + position-aware synthesis (`tree_summarize`, `compact`) more important, not less.

### 可提取的操作
- For any corpus >~500k tokens or latency budget <5s: keep RAG.
- Use long-context as a *synthesis-stage* tool (let the LLM see more retrieved chunks) rather than a *retrieval-replacement*.
- Use `tree_summarize` synthesizer to mitigate lost-in-the-middle when packing many chunks (failure #6 fix).

---

## Dilemma 5 — "Sentence-window vs auto-merging — which 'small-embed-large-return' pattern?"

### 困境
Both Sentence-Window (`SentenceWindowNodeParser` + `MetadataReplacementPostProcessor`) and Auto-Merging (`HierarchicalNodeParser` + `AutoMergingRetriever`) implement the same idea — embed small, return large. They are not interchangeable.

### 约束
- Sentence-Window expands **horizontally** (returns N adjacent sentences around the matched sentence).
- Auto-Merging expands **vertically** (returns the parent chunk when ≥threshold child chunks match).
- Source: `medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-...` ; `developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/`.

### 决策步骤
1. Inspect document structure. If documents have **clear hierarchical structure** (sections, headings, tables of contents) → Auto-Merging fits naturally with `HierarchicalNodeParser`.
2. If documents are **flat narrative** (long prose with no clear sectioning) → Sentence-Window is simpler and equally effective.
3. If the query distribution has **bursty multi-chunk relevance** ("this entire section is relevant") → Auto-Merging escalates correctly.
4. If the query distribution is **point-fact with surrounding context needed** ("find this fact, give me the surrounding paragraph") → Sentence-Window.

### 结果
Both consistently beat naive top-k chunk retrieval on faithfulness in published comparisons. Auto-Merging is more "principled" for structured docs, Sentence-Window is more "robust" for unstructured prose. A team that doesn't know their doc structure should start with Sentence-Window (lower setup cost).

### 可提取的操作
- Match the parser/retriever pair to **document structure**, not theoretical elegance.
- Always pair `SentenceWindowNodeParser` with `MetadataReplacementPostProcessor` — otherwise the metadata-stuffed sentence is what reaches the LLM, defeating the point.

---

## Sources

- `https://developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/`
- `https://www.llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`
- `https://www.llamaindex.ai/blog/llamaindex-enhancing-retrieval-performance-with-alpha-tuning-in-hybrid-search-in-rag-135d0c9b8a00`
- `https://www.llamaindex.ai/blog/towards-long-context-rag`
- `https://developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/`
- `https://github.com/run-llama/llama_index/issues/12200`
- `https://github.com/run-llama/llama_index/issues/13792`
- `https://medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-with-llamaindex-f778173bed98`
- `https://tianpan.co/blog/2026-04-12-hybrid-search-production-bm25-dense-embeddings`
- `https://medium.com/aimonks/agentic-rag-with-llama-index-router-query-engine-01-381e83a418af`
- `https://learn.deeplearning.ai/courses/building-agentic-rag-with-llamaindex/`
