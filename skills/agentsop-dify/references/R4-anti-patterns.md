# R4 — Anti-patterns & Boundaries

## Anti-pattern Catalog

| Anti-pattern | Symptom | Root cause | Fix |
|---|---|---|---|
| **Mega-workflow (30+ nodes single graph)** | Canvas lags, hard to debug  [issue #28245] | Trying to express everything visually | Split into sub-workflows; package as tools; or move logic out |
| **Code node carrying business logic** | Code nodes with 100+ lines of Python | Treating Dify as a Python IDE | Move to external microservice, call via HTTP Request node |
| **Legacy Chatbot/Agent app for long-term project** | Hits expressivity ceiling later, forced migration | Underestimating future complexity | Start with Chatflow / Workflow from day 1 |
| **No version control on DSL** | Cannot rollback, configurations drift | Trusting in-app version history alone | Export DSL → commit to git; use `dify-dsl-exporter` for batch  [github.com/linhai0872/dify-dsl-exporter] |
| **No external LLMOps wired** | Production bad cases go unnoticed | Relying only on Dify's internal logs | Wire Langfuse / Phoenix / LangSmith / Opik |
| **Workspace-shared model API keys** | Cost accounting nightmare | API keys are workspace-level, not per-app  [issue #32167] | Split into multiple workspaces; or use external billing layer |
| **No retrieval testing on KB** | RAG returns garbage, you find out from users | Skipping the Retrieval Testing UI | Always run real queries through Retrieval Testing before publishing |
| **Long agent streams (>120s) without timeout tuning** | Agent node randomly disconnects  [issue #27053] | Default timeouts + reverse proxy timeouts | Tune `WORKFLOW_MAX_EXECUTION_TIME`, `HTTP_REQUEST_MAX_READ_TIMEOUT`, NGINX `proxy_read_timeout` |
| **Beta upgrade without backup** | Data loss on 1.9 upgrade of beta KB pipelines  [discussions/26138] | Skipping release notes | Always read release notes; pin versions; test in staging |
| **Direct port exposure to internet** | Credentials leaked in plaintext | Skipping reverse proxy | Always Caddy/Nginx + HTTPS in front |
| **Container-internal PostgreSQL in production** | Data loss on container restart | Following docker-compose blindly | Externalize PostgreSQL (managed / dedicated VM); same for Redis and Vector DB |
| **Agent app for tasks with predictable path** | Lost observability, harder debugging | Over-using autonomy | Use explicit Workflow with deterministic branches |
| **One workflow doing 10 jobs** | God-workflow problem | Premature consolidation | Split by domain / responsibility; cross-call via Tool |
| **Skipping annotation reply** | Repeated expensive LLM calls for FAQ-shaped queries | Not knowing the feature exists | Enable Annotation Reply for chat apps; mark golden answers |

## Performance Boundaries (hard constraints)

[memo.d.foundation/breakdown/dify], [github.com/langgenius/dify/discussions/27346]

| Limit | Value | Why |
|---|---|---|
| Per-pod QPS | ~10 (1 CPU 2GB) | Per-node DB queries are the bottleneck |
| Plugin daemon timeout | 300s default (`PLUGIN_DAEMON_TIMEOUT`) | Plugins are out-of-process; long calls killed |
| Agent streaming with logs | 120s before disconnect | Log I/O interacts with reverse-proxy timeouts |
| Workflow max execution time | configurable (`WORKFLOW_MAX_EXECUTION_TIME`) | DAG-level guard |
| Knowledge storage on Cloud | tier-dependent (5MB/5GB/20GB) | Once over quota, blocked from changes  [discussions/32013] |
| Workspace members / apps | Community: no built-in limits | Capacity-bound only |

## What NOT to use Dify for

[memo.d.foundation/breakdown/dify], [issue #21455]
- **Model training / fine-tuning** — Dify is inference + orchestration only. Use Axolotl, LLaMA-Factory, Unsloth.
- **General workflow automation** (Salesforce sync, email triage with no LLM) — n8n has 400+ integrations; Dify's non-AI integrations are sparse.
- **Extreme RAG quality** (KG-RAG, deep doc parsing, late interaction) — RAGFlow or roll-your-own with LlamaIndex.
- **Pause-and-wait-for-user approval flows** — not supported (issue #21455 closed); use LangGraph interrupts or Temporal workflows.
- **High-frequency real-time inference router** — vLLM + custom gateway, not Dify.
- **Heavy-state agent runtime** (long-running, time-travel, recoverable) — LangGraph or custom.
- **Code node as microservice** — externalize.
- **Sub-second latency endpoints** — workflow engine overhead dominates.

## Operational Gotchas

### Upgrade hazards
- **1.9 upgrade is destructive** for beta knowledge pipelines & dataset credentials — re-run mandatory credential transformation  [github.com/langgenius/dify/discussions/26138]
- API/DSL compatibility may break across major versions — test imports in staging
- Plugin signature requirements changed in 1.0 — older plugins may need re-publishing

### Licensing
- Apache 2.0-like but with restrictions ("not really pure Apache 2.0") — confirm terms before commercial heavy use  [memo.d.foundation/breakdown/dify]
- Commercial license offered by LangGenius for SaaS resellers

### Security
- Plugins are sandboxed but signed
- Cryptographic verification rather than restrictive sandboxing  [memo.d.foundation/breakdown/dify]
- Code node is Python/Node.js sandbox — don't rely on it for security boundaries (it's a feature, not a fence)

### Cloud quotas
- Hard-locked, cannot reindex when over storage cap — must delete first  [github.com/langgenius/dify/discussions/32013]

### Multi-app credential isolation
- Model provider configs are workspace-level — same key used by every app in workspace
- Workaround: split into multiple workspaces, or external billing/key-rotation layer  [github.com/langgenius/dify/issues/32167]

## "Smell Tests" That Mean Dify Is No Longer Right

If you observe **two or more**, escalate to architecture review:

1. Workflow has > 40 nodes
2. Multiple Code nodes each > 100 lines
3. You need pause-and-wait
4. QPS > 10 per pod sustained
5. Canvas dragging/zooming is unusably laggy
6. Most logic lives in HTTP Request → external service (Dify is just a UI)
7. You're using `print()` and grep'ing logs more than the visual debugger
8. Engineers spend more time exporting/importing DSL than building
9. Your team is 100% engineers and nobody reads the canvas

Escalation paths:
- Light: keep Dify as frontend; move logic to external service
- Heavy: LangGraph / Temporal / custom for orchestration
- RAG-heavy: RAGFlow for retrieval, Dify for UI
- Pure code: drop Dify, use LangGraph or LlamaIndex frameworks
