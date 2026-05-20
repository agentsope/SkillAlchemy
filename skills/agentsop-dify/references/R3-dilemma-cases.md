# R3 — Dilemma Cases

## Case 1: "The workflow has become unmaintainable — split or rewrite?"

### Symptoms
- Canvas has 30+ nodes; dragging/zooming lags  [github.com/langgenius/dify/issues/28245]
- Nested branches are visually unreadable
- Engineer afraid to change anything — fearful of breaking other branches
- Multiple Code nodes with >100 lines of Python each

### Decision Tree
```
Node count < 20, flat branching
   → Stay in Dify; rename nodes, add Note nodes, document inputs/outputs

Node count 20-40, identifiable sub-procedures
   → Extract sub-workflows; package each as a Tool callable from the main workflow
   → Dify allows workflow apps to be used as tools in other apps
   [hellodify.com/en/docs/workflow/workflow-chatflow-difference]

Node count > 40, OR heavy reliance on Code nodes (>100 LOC per node)
   → Signal: business logic has outgrown the visual paradigm
   → Move core logic to external Python microservice
   → Dify becomes orchestrator + RAG + frontend only
   → HTTP Request nodes call out to your service
```

### Practical Anti-pattern
Writing 200 lines of Python inside a Code node. This is **the signal** that Dify is no longer the right abstraction for that piece. Externalize the service; let Dify route to it.

### Quoted analysis
> "Designing workflows with parallel branches has led to difficulty managing branch states and reproducing errors, reducing the usability of complex workflows."  — Dify breakdown analysis [memo.d.foundation/breakdown/dify]

> "The execution engine was redesigned around queue scheduling to improve management of parallel tasks" — Dify team response in v1.9 [github.com/langgenius/dify/discussions/26138]

---

## Case 2: "Hit the visual ceiling — keep Dify or move to LangGraph / code?"

### Symptoms
- Need **pause-and-wait-for-user** semantics (approval flow, multi-step user choice) — confirmed not supported, issue #21455 closed "not planned"  [github.com/langgenius/dify/issues/21455]
- Need stateful loops, time-travel debugging, mid-run intervention
- Sub-second latency required
- QPS > 10 per pod sustained — Dify per-node DB queries become the bottleneck  [memo.d.foundation/breakdown/dify]
- Need conditional execution that skips downstream optional nodes after a fallible step's fail branch — workflow flow has issues here  [github.com/langgenius/dify/issues/24791]

### Decision Matrix
| Signal | Stay in Dify | Move to code (LangGraph / raw) |
|---|---|---|
| Team mix includes non-engineers | ✓ | ✗ |
| Need quick UI / API / auth / multi-tenant | ✓ | ✗ (rebuild yourself) |
| Pause-and-wait-for-user | ✗ | ✓ (LangGraph interrupt nodes native) |
| QPS > 10 sustained | ✗ | ✓ |
| Complex state machine + rollback | ✗ | ✓ |
| RAG + light orchestration | ✓ | — |
| Already deep in LangChain | — | LangFlow/LangGraph preferred |

### Recommended Hybrid (most common in practice)
- **Dify** = frontend + RAG + user management + monitoring + simple orchestration
- **External service** = core agent / state-machine logic (LangGraph, custom)
- **Bridge** = Dify HTTP Request nodes call the external service

### Quoted
> "Dify wins when you're building an LLM-powered SaaS, an internal product with multiple teams, or anything that will outlive a single quarter. Langflow is for teams that need power now and will need more later."  [blog.elest.io/dify-vs-langflow-vs-flowise]

> "The current Workflow system does not support a 'pause-and-wait-for-user' mechanism… closed as not planned."  [github.com/langgenius/dify/issues/21455]

---

## Case 3: "Self-host or Cloud — when is ops cost worth it?"

### Decision Matrix
[architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host]

| Condition | Cloud | Self-host |
|---|---|---|
| Team ≤3, small usage | ✓ (cheaper than DevOps salary) | ✗ |
| Compliance / data residency (finance, healthcare) | ✗ | ✓ |
| Air-gapped / on-prem only | ✗ | ✓ |
| Heavy volume (millions of API calls) | ✗ (subscription dwarfs infra) | ✓ |
| Custom vector store, custom models, custom networking | partial | ✓ (full control) |
| Want zero ops overhead | ✓ | ✗ |
| Long-term lock-in concern | ✗ (open source — never locked) | ✓ |

### Quoted
> "If you want to focus on product and leave infrastructure to Dify, or when your usage is small to medium, the managed service makes financial sense. Small teams typically save money — three developers on Professional costs roughly $708 annually, often cheaper than hiring DevOps staff."  [architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host]

> "You are not locked in — since Dify is open source, you can migrate between cloud and self-hosted approaches as circumstances evolve."  [ibid.]

### Operational Reality
- Self-hosting is **not** "docker compose up done." Production needs:
  - Reverse proxy + HTTPS
  - PostgreSQL backups (RPO/RTO defined)
  - Redis HA
  - External Vector DB with backups
  - Upgrade strategy (test in staging — v1.9 upgrade *destroys* beta Knowledge Pipelines [discussions/26138])
  - Monitoring stack (Prometheus / external LLMOps)
- All Dify editions (Community / Premium / Enterprise) use the **same Docker images**; differences are env-var flags  [github.com/langgenius/dify/discussions/32254]

---

## Case 4: "Dify Knowledge vs separate vector store — where's the line?"

### Symptoms
- Existing Pinecone / Weaviate / Milvus cluster the team already uses
- Multiple Dify apps + non-Dify apps sharing the same KB
- Need fine-grained control over chunking / embedding pipeline
- Want experimental retrieval (graph RAG, late interaction, hybrid + rerank chains)

### Decision Matrix
| Scenario | Use Dify built-in KB | Use External Knowledge API |
|---|---|---|
| Single app, single dataset | ✓ | ✗ over-kill |
| Multiple Dify apps share same KB | ✓ (Dify KB is multi-app referenceable) | — |
| Extreme chunking / experimental retrieval | ✗ (Dify abstraction limited) | ✓ |
| Existing self-built RAG service | ✗ | ✓ (point Dify at it) |
| Data > 100M chunks | ✗ (memory leak reports for large bases  [memo.d.foundation/breakdown/dify]) | ✓ |
| Need KG-RAG / deep parsing | ✗ → use RAGFlow instead  [sider.ai/blog/ai-tools/dify-vs-ragflow] | ✓ |

### Hybrid Pattern
- **Dify built-in KB** for common documents (FAQs, product docs) — fast ingestion, retrieval testing UI
- **External Knowledge API** for specialized domains where you have custom retrieval

### Vector DB Selection (when using built-in KB)
[deepwiki.com/langgenius/dify-docs/8.3-vector-database-configuration]
- **Qdrant** — Dify's recommended default
- **Weaviate** — graph-based, strong semantic search
- **Milvus** — large-scale
- **Pinecone** — fully managed (cloud spend)
- **PGVector** — already have Postgres, want simplicity
- **TiDB Vector** — distributed Postgres-compatible, large-scale  [dify.ai/blog/dify-x-tidb]

Configured via `VECTOR_STORE` env variable before deployment. Cannot easily switch after data is ingested.

---

## Case 5: "Agent app vs Workflow + Agent Node vs explicit Workflow — which?"

### Symptoms
Three viable implementations of the same task; team divided.

### Decision Principles
[zediot.com/blog/dify-difference-between-agent-and-workflow], [dify.ai/blog/dify-agent-node-introduction-when-workflows-learn-autonomous-reasoning]

```
Path is predictable, debuggability is the priority
  → Explicit Workflow (write down the branches)

Path is unpredictable, LLM must select tools dynamically
  → Workflow + Agent Node (v1.9+)
     [RECOMMENDED hybrid — autonomy where needed, control elsewhere]

Pure dialogue + tool calls, no complex orchestration
  → Agent app (legacy)

Mostly predictable but a few uncertain steps
  → Main DAG explicit + Agent Node embedded for uncertain segments
```

### Hybrid Wisdom
> "The best systems combine both — workflows as orchestrators that delegate reasoning tasks to agents. This hybrid model provides both predictability and intelligence, leveraging each tool's strengths while minimizing weaknesses."  [zediot.com/blog/dify-difference-between-agent-and-workflow]

### Anti-patterns
- **Agent app for everything** — loses workflow's observability
- **Workflow forcing fully unpredictable tasks** — branch explosion, brittle
- **Mixing two agent strategies in one workflow** — debugging hell

### Agent Strategy Choices  [docs.dify.ai/en/use-dify/nodes/agent]
- **Function Calling** — modern models (GPT-4, Claude 3.5+, Gemini) with native tool-use
- **ReAct** — older / smaller models without function calling
- **Custom (CoT, ToT, GoT, …)** — via Agent Strategy plugin
- `max_iterations` param prevents runaway loops

---

## Case 6: "Visual builder feels too constrained — is Dify still the right tool?"

### Symptoms (Chinese community critique)
[zhuanlan.zhihu.com/p/1947389040702781389]

> 表面上可以脱离编程语言，通过拖拽连接搭建业务流程，但实际上如果不会写 Python 代码，很难用 Dify 实现智能体。
> (Translation: On the surface it lets you build flows without code via drag-and-drop, but in practice if you can't write Python, you can't really build an agent on Dify.)

> 既然都要在 Dify 里写代码，为何不直接用 Python 写代码呢？
> (Translation: If you're writing Python inside Dify anyway, why not just write Python directly?)

### Honest answer
Dify's value is **NOT** "no code." It's:
- Auth, web UI, API, monitoring, version control, knowledge base management, model provider abstraction
- A **shared visual artifact** that PMs, ops, and engineers can read together
- A **deployment story** (one-click web app, API key management, multi-tenant)

If your team is:
- 100% engineers, no PM/ops involvement → Dify's value drops sharply
- Already running LangChain/LangGraph successfully → don't migrate; integrate

If your team is:
- Mixed roles needing a common artifact → Dify is exactly right
- Wants to ship LLM features without building a webapp + admin + monitoring from scratch → Dify is exactly right
