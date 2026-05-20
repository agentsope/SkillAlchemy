# R5 · Ecosystem Context — LlamaIndex vs Alternatives

## 1. The landscape map

```
                      Build an LLM app that uses private data
                                       |
                          ┌────────────┴────────────┐
                          ▼                         ▼
                "Retrieval is hard"        "Orchestration is hard"
                          |                         |
                   LlamaIndex / Haystack    LangChain / LangGraph
                          |                         |
                          ▼                         ▼
              Raw vector store              CrewAI / AutoGen
              (Pinecone, Qdrant, ...)       (multi-agent)
```

LlamaIndex's positioning, made explicit by the project itself in 2025: **"the leading document agent and OCR platform"** (`github.com/run-llama/llama_index` README). Note the deliberate framing — *document agent*, not *general agent*. Indexing-quality is the moat; orchestration is a secondary feature.

## 2. LlamaIndex vs LangChain (the canonical comparison)

| Dimension | LlamaIndex | LangChain |
|---|---|---|
| Primary abstraction | **Index** (noun, first-class) | **Chain** / **Graph** (verb, composition) |
| Default mental model | Documents → Nodes → Index → Retriever → QE | LCEL `Runnable`s chained via `|` |
| Best at | RAG quality, ingestion, document parsing | Agent orchestration, tool ecosystem |
| Document parsing | LlamaParse (130+ formats, agentic OCR) | Adequate (Unstructured.io integrations) |
| Agent primitive | FunctionAgent / ReActAgent on Workflows 1.0 | LangGraph (state machines, more granular) |
| Lines of code for "basic RAG" | ~5-line `VectorStoreIndex.from_documents().as_query_engine()` | Higher, more explicit |
| Learning curve | Gentler for RAG, steeper for agents | Steeper for RAG, gentler for orchestration |
| Eval primitives | Built-in Faithfulness/Relevancy/Retriever evaluators | Mostly via LangSmith (separate product) |

Sources: `ibm.com/think/topics/llamaindex-vs-langchain`; `statsig.com/perspectives/llamaindex-vs-langchain-rag`; `latenode.com/blog/.../langchain-vs-llamaindex-2025-...`.

### The community consensus (2025-2026)
> "LlamaIndex shines when querying databases to retrieve relevant information; LangChain's broader flexibility allows for a wider variety of use cases, especially when chaining models and tools into complex workflows." (IBM)

> "Many production systems use both: LlamaIndex as the retrieval layer, LangGraph as the orchestration layer." (Latenode)

The hybrid pattern has become normative — pick LlamaIndex *into* a LangGraph workflow, not as a competitor.

## 3. LlamaIndex vs Haystack

Haystack (deepset) and LlamaIndex overlap most directly — both are RAG-first frameworks.

- **Haystack**: pipeline-oriented (YAML-configurable), strong on classical IR (BM25, dense), opinionated about deployment, more "enterprise IR" flavor.
- **LlamaIndex**: index-oriented (Python-native), better with messy modern documents (LlamaParse, multi-modal), broader index taxonomy (Property Graph, DocumentSummary, etc.), more aggressive on agentic features.

LlamaIndex wins when documents are heterogeneous and LLM-centric workflows dominate. Haystack wins when the system is closer to "classical search with an LLM bolted on" and YAML-configurability is valued by ops teams.

## 4. LlamaIndex vs raw vector store SDK

A common temptation: "just use Pinecone/Qdrant/Weaviate directly, skip the framework". Tradeoffs:

| What you gain by going raw | What you lose |
|---|---|
| Smaller dependency surface | Reimplementing chunking, eval, query routing, document lifecycle, response synthesis |
| Full control | All 13 failure modes become your responsibility |
| No framework lock-in | Hard to swap vector stores later (LlamaIndex abstracts ~25+) |

The pragmatic rule: if you find yourself reimplementing more than 2 of {SentenceSplitter, IngestionPipeline, Reranker, ResponseSynthesizer, RetrieverEvaluator}, you have rebuilt LlamaIndex badly.

## 5. LlamaIndex vs DSPy

DSPy treats prompts as **programs to compile** (signatures + optimizers); LlamaIndex treats prompts as **strings to tune by hand** inside a structured data pipeline. They are orthogonal: a DSPy program can call a LlamaIndex retriever; a LlamaIndex query engine can wrap a DSPy module as its synthesizer. Use DSPy when you want *automatic* prompt optimization; use LlamaIndex when you want *retrieval-shaped infrastructure*.

## 6. LlamaIndex vs LangGraph (for agentic RAG)

LangGraph models agent behavior as an explicit **state machine** with typed state and edges. LlamaIndex's Workflows 1.0 (2025) is **event-driven** (steps subscribe to events). Conceptually similar; LangGraph is more "I want to draw a diagram of all states"; Workflows is more "I want to compose steps with Pythonic events".

For a complex multi-agent system with many tools and dynamic routing, LangGraph's explicit state model usually scales better. For a retrieval-heavy app that needs *some* agency, Workflows is more ergonomic because the retrieval primitives are first-class neighbors.

## 7. LlamaIndex vs CrewAI / AutoGen

Different category. CrewAI and AutoGen are **multi-agent collaboration** frameworks (agents-as-team-members). LlamaIndex provides retrieval *tools* that those agents can use. The integration pattern: expose a `QueryEngineTool` to a CrewAI crew or an AutoGen group chat.

## 8. The pivot: LlamaIndex as "document agent platform" (2025)

The strategic shift in 2025 is visible in:

- README change: tagline became "the leading document agent and OCR platform".
- LlamaParse v2 launch (`llamaindex.ai/blog/announcing-new-llamacloud-sdks-and-parse-api-v2`): 130+ formats, agentic OCR, parse / extract / classify / split / sheets / index.
- LlamaCloud as managed offering for enterprise RAG (`llamaindex.ai/blog/4-ways-llamacloud-scales-enterprise-rag`).
- Workflows 1.0 making agentic logic native.

The framing is moving from "RAG framework" to **"the platform layer between messy documents and document-grounded agents"**. This is consequential for skill alignment: when the choice is "best document parser + RAG infra" vs "best agent orchestration", LlamaIndex is increasingly clearly the first, not the second.

## 9. Decision rubric (for the agent picking a framework)

```
Q1. Do you primarily need to extract knowledge from messy documents (PDFs, slides, tables, scans)?
   YES → LlamaIndex (with LlamaParse) is the lead choice.
   NO  → continue.

Q2. Is the primary challenge orchestrating multi-step agent reasoning with many tools?
   YES → LangGraph (or CrewAI for multi-agent) is the lead choice.
        Embed LlamaIndex retrievers as one tool among many.
   NO  → continue.

Q3. Is the corpus small (<100k tokens) and static?
   YES → No framework needed. Stuff context window with prompt caching.
   NO  → continue.

Q4. Is the data pure structured/tabular?
   YES → Use SQL/DuckDB/BI tooling. LlamaIndex only if hybrid NL2SQL+RAG.
   NO  → LlamaIndex remains lead. Layer LangGraph on top only if agentic logic emerges.
```

## 10. When to combine

The most-praised production pattern (consistent across 2025 comparison blogs):
- **Retrieval & ingestion**: LlamaIndex (LlamaParse + IngestionPipeline + appropriate Index + reranker).
- **Eval**: LlamaIndex evaluators + RAGAS for richer metrics.
- **Orchestration**: LangGraph (or LlamaIndex Workflows if you stay in-ecosystem).
- **Multi-agent**: CrewAI / AutoGen with LlamaIndex retrievers as tools.
- **Observability**: LangSmith or Phoenix (Arize); LlamaIndex emits compatible traces.

## Sources

- `https://github.com/run-llama/llama_index` (README, 2025 tagline)
- `https://www.ibm.com/think/topics/llamaindex-vs-langchain`
- `https://www.statsig.com/perspectives/llamaindex-vs-langchain-rag`
- `https://latenode.com/blog/langchain-vs-llamaindex-2025-complete-rag-framework-comparison`
- `https://www.zenml.io/blog/llamaindex-alternatives`
- `https://www.llamaindex.ai/blog/announcing-new-llamacloud-sdks-and-parse-api-v2`
- `https://www.llamaindex.ai/blog/4-ways-llamacloud-scales-enterprise-rag`
- `https://www.llamaindex.ai/blog/announcing-workflows-1-0-a-lightweight-framework-for-agentic-systems`
- `https://www.morphllm.com/comparisons/langchain-vs-llamaindex`
