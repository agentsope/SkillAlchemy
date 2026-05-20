# R2 — SOP Workflow: Idea → Production

## Phase 0: Choose App Type (5-minute gate)

Decision questions:
1. **Conversation context needed?** → Chatflow / Chatbot / Agent vs Workflow / Text-Gen
2. **Logic deterministic, or LLM must autonomously pick tools?** → explicit DAG vs Agent (app or node)
3. **Non-engineers co-authoring?** → visual app preferred; otherwise consider code
4. **MVP throwaway, or long-lived?** → long-lived ⇒ Chatflow/Workflow (not legacy types)

Recommendation per official docs  [docs.dify.ai/en/use-dify/getting-started/key-concepts]:
> "Workflow/Chatflow are recommended for most use cases. Use the legacy basic types only if preferring simplified interfaces over advanced features."

Decision tree:
```
context across turns?
├─ yes ─→ Chatflow (complex) or Chatbot/Agent (simple)
└─ no  ─→ Workflow (complex) or Text-Gen (single prompt)

LLM auto-tool-use needed?
├─ yes ─→ Agent app  OR  Workflow + Agent Node (preferred from v1.9+)
└─ no  ─→ explicit DAG nodes
```

## Phase 1: Deploy (30 min)

### Cloud (start here)
Tiers  [architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host]:
- Sandbox (free): 200 credits / 10 apps / 5MB
- Pro $59/mo: 5k credits / 50 apps / 5GB
- Team $159/mo: 10k credits / 20GB / SSO
- Enterprise: custom

### Self-host (Docker Compose, the common path)
```bash
git clone https://github.com/langgenius/dify
cd dify/docker
cp .env.example .env
# edit .env: VECTOR_STORE, secrets, ...
docker compose up -d
```
Requirements: 2 vCPU / 4GB RAM min; 40GB SSD prod.  [docs.dify.ai/en/self-host/quick-start/docker-compose]

Production hardening:
- Reverse proxy (Caddy/Nginx) + HTTPS — never expose internal port directly
- Externalize PostgreSQL / Redis / Vector DB (don't use container defaults in prod)
- Set timeouts: `PLUGIN_DAEMON_TIMEOUT`, `WORKFLOW_MAX_EXECUTION_TIME`, `HTTP_REQUEST_MAX_READ_TIMEOUT`
- Backups for PostgreSQL + vector store
- Reverse proxy timeouts must match Dify timeouts (NGINX 60s default kills long agents)  [issue #27053]

## Phase 2: Prompt Engineering in Studio (1 hour)

1. Open Prompt IDE for a single LLM call **before** building any workflow
2. Use multi-model comparison side-by-side (GPT-4, Claude, your model)
3. Extract `{{var}}` placeholders — these become workflow inputs
4. Save best prompt as starting point for workflow LLM node

## Phase 3: Knowledge Base / RAG (half day)

Steps:
1. Create Knowledge → upload docs (PDF, MD, DOCX, …)
2. Pick **High-Quality** (embed-based) vs **Economical** (BM25)
3. Tune chunk size / overlap — defaults 500/50; for long-form docs go 1000+
4. **Critical**: run **Retrieval Testing** with real queries — observe top-k chunks
5. Set retrieval mode: Semantic / Full-text / **Hybrid (recommended)**
6. Attach a **Rerank model** (jina-rerank, cohere-rerank, BGE-rerank-v2)
7. For complex ingestion (multi-format, image OCR, Q&A pairs) use **Knowledge Pipeline** (v1.9+) with parser plugins

> "Dify provides a comprehensive RAG pipeline handling the full lifecycle of document ingestion: from raw file upload through extraction, cleaning, segmentation, embedding, indexing, retrieval, and reranking."  [pyshine.com/2026/04/20/Dify-Open-Source-LLM-App-Development-Platform]

## Phase 4: Tools & Plugins (half day)

Three paths:
1. **HTTP Request node** — one-off REST call, zero code, no marketplace round-trip
2. **Tool plugin** — reusable across apps / shared across team / marketplace publishing
3. **Code node** (Python/Node.js sandbox) — custom transform logic between nodes

Built-in tool count: **50+** including Google Search, DALL·E, WolframAlpha, Stable Diffusion…  [github.com/langgenius/dify]

Decision: one-time = HTTP node; reusable = Tool plugin; logic-heavy reasoning loop = Agent Strategy plugin.

## Phase 5: Build the Workflow (1-3 days)

**Construction order (counter-intuitive but critical)**:
1. Get **linear path** working first — Start → LLM → Knowledge → LLM → End
2. Add **IF/ELSE** branches only where truly needed
3. Add **Iteration / Loop** for list processing
4. Add **Agent Node** (v1.9+) for autonomous tool-use segments
5. Add **Code node** last — only to bridge what can't be expressed

Anti-pattern: starting with a 30-node diagram. Linear-first, branch-second.

## Phase 6: Test & Publish (1 day)

1. **Step debugging** — run each node individually
2. **Test run from any node** (v1.9+) — partial runs and resumptions
3. **Annotation Reply** (chat apps) — mark good answers → next time bypass LLM, return cached  [dify.ai/blog/boosting-chatbot-quality-cutting-costs-with-dify-annotation-replies]
4. **Version control** — publish version with custom name + release notes; rollback available  [legacy-docs.dify.ai/guides/management/version-control]
5. **Export DSL (YAML)** → commit to git → CI/CD  [github.com/langgenius/dify-docs/blob/main/en/guides/workflow/export_import.md]
6. **Publish as**: Web App / API endpoint / MCP Server / Tool-for-other-apps

## Phase 7: Wire Observability (half day)

1. Internal logs sufficient for solo dev
2. Production: pick one external LLMOps
   - LangSmith — LangChain ecosystem
   - Langfuse — open-source, self-host
   - Arize Phoenix — eval-first  [dify.ai/blog/dify-arize-how-to-evaluate-monitor-and-improve-agents]
   - Opik — fastest tracing
3. Configure project name to match Dify Monitoring settings
4. Track 7 trace types: Workflows, Messages, Moderation, Suggested Questions, Dataset Retrieval, Tools, Generated Names

## Phase 8: Iterate

Loop:
1. Watch monitoring for **bad cases**
2. Either: annotation reply, edit prompt, fix workflow branch, or add Code node
3. Collect traces → build eval datasets in Phoenix/Langfuse
4. Run prompt/model variations against dataset, compare deltas
5. On performance issues:
   - Profile per-node latency
   - Move heavy logic out to external service
   - Split into sub-workflows
   - Tune `WORKFLOW_MAX_EXECUTION_TIME` if hitting cliff at long streams

## Phase 9: Scale

When self-hosted load exceeds ~10 QPS  [memo.d.foundation/breakdown/dify]:
- Add API server replicas
- Add Celery worker replicas
- Scale Vector DB independently
- Switch to Kubernetes + Helm chart
- Externalize PostgreSQL (HA RDS / managed)
- Add CDN in front of static frontend
- Consider regional sharding for multi-tenant SaaS

## SOP Checklist (paste into project doc)

```
[ ] App type chosen (Workflow / Chatflow / etc.)
[ ] Cloud or Self-host decision made (see R3 Case 3)
[ ] Single-LLM prompt validated in Prompt IDE
[ ] Knowledge base created (if RAG): chunks tuned, retrieval testing run, rerank on
[ ] Workflow linear path working
[ ] Branching added only where needed
[ ] Agent Node used only for genuinely uncertain paths
[ ] Code node logic < 50 lines (else externalize)
[ ] DSL exported to git
[ ] Version published with release notes
[ ] External LLMOps wired (Langfuse/Phoenix/LangSmith/Opik)
[ ] Annotation Reply enabled for chat apps
[ ] Reverse proxy timeouts match Dify timeouts
[ ] Backups configured for PostgreSQL + vector store
```
