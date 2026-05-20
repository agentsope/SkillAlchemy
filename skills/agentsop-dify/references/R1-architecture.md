# R1 — Dify Architecture & Mental Model

## Identity
Dify positions itself as **"a production-ready platform for agentic workflow development"** — open-source, self-hostable, with a visual Studio and a marketplace of plugins.  [github.com/langgenius/dify], [dify.ai/]

Key numbers (May 2026):
- ~142k GitHub stars, 10,686+ commits
- Current stable: v1.14.x
- ~50% TypeScript (Next.js frontend), ~42% Python (backend)

## The 5-layer Stack

```
┌─────────────────────────────────────────────────────────────┐
│ Studio (visual canvas: workflow / chatflow / app types)      │
├─────────────────────────────────────────────────────────────┤
│ Apps: Chatbot · Agent · Text-Gen · Workflow · Chatflow       │
│        (all run on the unified Graph Engine "graphon")       │
├─────────────────────────────────────────────────────────────┤
│ Knowledge Base (RAG pipeline) + Tools/Plugins (Marketplace) │
├─────────────────────────────────────────────────────────────┤
│ Model Providers (100+ via Models plugin)                     │
├─────────────────────────────────────────────────────────────┤
│ Monitoring (internal logs + LangSmith/Langfuse/Phoenix/Opik)│
└─────────────────────────────────────────────────────────────┘
```

Sources: [docs.dify.ai/en/introduction], [pyshine.com/2026/04/20/Dify-Open-Source-LLM-App-Development-Platform], [memo.d.foundation/breakdown/dify].

## Five App Types

| App | Trigger | Memory | When to use |
|---|---|---|---|
| Chatbot (legacy) | per-turn | yes | simple FAQ bot |
| Agent (legacy) | per-turn | yes | autonomous tool use |
| Text Generator (legacy) | one-shot | no | content gen |
| **Workflow** | one-shot / batch | **no** | API backend, batch jobs |
| **Chatflow** | per-turn (whole DAG runs each turn) | **yes** (conversation vars) | complex conversational logic |

Official: "Workflow/Chatflow are recommended for most use cases. Legacy types only if preferring simplified interfaces."  [docs.dify.ai/en/use-dify/getting-started/key-concepts]

Critical distinction Workflow vs Chatflow:
- Workflow: each run a fresh start, no conversation context
- Chatflow: graph runs each turn, conversation variables persist, LLM nodes have memory windows
[hellodify.com/en/docs/workflow/workflow-chatflow-difference]

## Graph Engine = "graphon"

- Unified DAG runtime under every app type
- v1.9+ redesigned as **queue-based scheduler** — all tasks enter a unified queue; scheduler manages dependencies and parallelism  [github.com/langgenius/dify/discussions/26138]
- Enables: partial run, start-from-any-node debugging, pause/terminate, streaming coordination across nodes

## Node Taxonomy

| Category | Nodes |
|---|---|
| Flow | Start, End, Answer |
| LLM | LLM, Question Classifier, Parameter Extractor |
| RAG | Knowledge Retrieval |
| Logic | IF/ELSE, Iteration, Loop, Variable Assigner, Variable Aggregator |
| Code | Code (Python/Node.js sandboxed), Template (Jinja2) |
| External | HTTP Request, Tool, Agent Node |
| Data | List Operator, Document Extractor |

[legacy-docs.dify.ai/guides/workflow/node], [legacy-docs.dify.ai/guides/workflow/node/ifelse]

## Variable System
- Start-node inputs (text / number / file / select)
- Node outputs referenced as `{{node_id.var}}`
- Environment variables (secrets)
- Conversation variables (Chatflow only — persist across turns)
- System variables: `sys.user_id`, `sys.conversation_id`, etc.
[docs.dify.ai/en/use-dify/getting-started/key-concepts]

## Knowledge Base / RAG Architecture

3-step model: **Retrieval → Augmentation → Generation**  [docs.dify.ai/en/guides/knowledge-base/readme]

Three creation paths:
1. **Quick create** — upload + auto-process
2. **Knowledge pipelines** (v1.9+) — visual ingest workflow, with plugins for parsers
3. **External integration** — point to external RAG service

Indexing modes:
- **High-Quality** — embeddings + vector index (best quality, costs embed tokens)
- **Economical** — keyword/BM25 only (no embed cost, less semantic)

Retrieval strategies:
- N-to-1 Recall (LLM picks one dataset)
- Multi-way Recall (parallel + rerank — recommended for multi-dataset apps)

Vector store support: **13+** backends — Qdrant (default recommended), Weaviate, Milvus, Pinecone, PGVector, TiDB, Chroma…  [deepwiki.com/langgenius/dify-docs/8.3-vector-database-configuration]

## Plugin System (v1.0+)

Five plugin types  [dify.ai/blog/introducing-dify-plugins], [docs.dify.ai/en/plugins/introduction]:

| Type | Purpose |
|---|---|
| **Models** | new model providers |
| **Tools** | reusable capabilities for agents/workflows |
| **Agent Strategies** | custom reasoning loops (CoT, ToT, ReAct, FC, …) |
| **Extensions** | lightweight HTTP webhook integrations |
| **Bundles** | curated plugin sets |

Decoupled architecture — each plugin is independent package, signed before marketplace distribution. Multiple runtimes: local, debug, serverless, enterprise.  [memo.d.foundation/breakdown/dify]

## Deployment Architecture

Self-host components:
- API server (FastAPI / Flask)
- Worker (Celery + Redis queue)
- Web frontend (Next.js)
- PostgreSQL (relational state)
- Redis (queue + cache)
- Vector DB (one of 13)
- Object storage (S3-compatible)
- Plugin daemon (separate process for plugin isolation)

Min: 2 CPU / 4GB RAM. Production: 2 vCPU / 4GB / 40GB SSD + reverse proxy.  [docs.dify.ai/en/self-host/quick-start/docker-compose]

Single docker images (`langgenius/dify-api`, `langgenius/dify-web`) for all editions; Community/Premium/Enterprise distinguished by env vars (`ENTERPRISE_ENABLED`, `ENTERPRISE_API_URL`, `ENTERPRISE_API_SECRET_KEY`).  [github.com/langgenius/dify/discussions/32254]

## Monitoring & Evaluation

Internal: per-request logs (input/output, tokens, latency, errors).

External LLMOps integration  [docs.dify.ai/guides/monitoring/integrate-external-ops-tools], [dify.ai/blog/dify-integrates-langsmith-langfuse]:
- **LangSmith** — LangChain ecosystem
- **Langfuse** — open-source, self-host friendly
- **Arize Phoenix** — eval-first  [dify.ai/blog/dify-arize-how-to-evaluate-monitor-and-improve-agents]
- **Opik** — fastest tracing benchmarks (~23s vs Phoenix ~170s vs Langfuse ~327s in published tests)

Trace types: Workflows / Messages / Moderation / Suggested Questions / Dataset Retrieval / Tools / Generated Names.

## Why "Platform, not Framework"

Dify's design choice  [memo.d.foundation/breakdown/dify], [learnwithparam.com/blog/batteries-included-rag-platforms-dify-ragflow-onyx]:
- Unify auth, API, UI, vector store, model providers, logs, versioning in one box
- Trade some expressive ceiling for **enormous reduction in scaffolding time**
- Target audience: cross-functional teams shipping LLM apps (not pure ML engineering teams)
- Beehive architecture: modules stand alone, communicate via well-defined contracts → enables multi-runtime (local, serverless, enterprise)

This explains: 50k+ stars (broad reach), but also the well-documented ceiling (perf, expression depth).
