---
name: agentsop-dify
version: 1.0.0
description: SOP for building LLM applications on Dify — visual workflow + chatflow + agent + RAG knowledge base + plugin marketplace + observability, self-hostable. Use when shipping LLM apps fast with a "no-code to pro-code" gradient, especially when non-engineers need to co-author the flow.
domain: llm-application-platform
framework: Dify
framework_version: ">=1.0, current 1.14.x (May 2026)"
trigger_keywords:
  - "Dify workflow"
  - "Dify chatflow"
  - "Dify agent"
  - "Dify knowledge base"
  - "visual LLM workflow"
  - "self-host LLM platform"
  - "low-code AI app"
  - "Dify plugin"
  - "Dify DSL"
  - "LLMOps platform"
when_to_use:
  - "shipping an internal LLM app (Q&A bot, doc-grounded copilot, content pipeline) in days not weeks"
  - "team has a mix of PMs / ops / engineers and needs a shared visual artifact (chatflow / workflow canvas)"
  - "need RAG + tools + monitoring + auth + web UI + API in one box (vs. assembling from libraries)"
  - "enterprise asks for self-hostable, on-prem, air-gapped LLM platform with multi-tenant workspaces"
  - "prototype-to-production gradient: start visual, drop into Code/Python nodes when needed"
when_not_to_use:
  - "high-throughput production (>10 QPS per pod) — Dify hits a known per-node DB-query bottleneck [memo.d.foundation/breakdown/dify]"
  - "sub-second latency / real-time streaming pipelines — workflow engine overhead dominates"
  - "human-in-the-loop with pause-and-wait-for-user semantics — not supported as of v1.14 [github.com/langgenius/dify/issues/21455]"
  - "model training / fine-tuning workflows — Dify is inference + orchestration only"
  - "your team is 100% engineers already shipping LangChain/LangGraph in code — Dify's visual layer is overhead, not leverage"
  - "deeply custom retrieval (graph RAG, late interaction, hand-tuned chunking) — RAGFlow or a raw stack wins [sider.ai/blog/ai-tools/dify-vs-ragflow]"
---

# Dify SOP — LLM Application Platform, Visual-First with Code Escape Hatches

> 框架定位: "An open-source platform for building agentic workflows" — visual workflow + RAG + agent + monitoring + deploy in one box, self-hostable.  [docs.dify.ai/en/introduction], [github.com/langgenius/dify]

> "Dify is the only tool that gives you data ingestion, RAG, an API, and a polished, shareable web UI in one click."  [learnwithparam.com/blog/batteries-included-rag-platforms-dify-ragflow-onyx]

---

## 1. 何时激活 (When to Activate)

### 1.1 直接信号 (Direct triggers)
- 用户说 "我需要个 LLM 应用 / 客服 bot / 知识库问答 / 文档处理流"，且**希望几天内交付**
- 用户说 "我们在用 Dify / 自己部署了 Dify / 想自己 host LLM 平台"
- 团队**有非工程师参与**编排逻辑（PM / 运营 / 业务方画 chatflow）
- 需要**一站式**：模型管理 + RAG + 工具调用 + 用户访问 + API + 监控 + 评估
- 需要**多租户 / workspace 权限**（典型 SaaS / 企业内多团队场景）  [blog.elest.io/dify-vs-langflow-vs-flowise]

### 1.2 反向信号 (Skip Dify when)
- **高吞吐**: 单 pod ~10 QPS 上限，每个 workflow 节点单独打 DB  [memo.d.foundation/breakdown/dify]
- **实时低延迟**: workflow 引擎开销 + 同步 DB 调用，sub-second 场景不适用
- **需要 pause-and-wait-for-user**: 审批流 / 用户多步交互 → Dify workflow 不支持，issue #21455 已关 "not planned"
- **纯工程团队 + 已有 LangChain/LangGraph 投入**: Dify 的可视化层成为负担而非杠杆
- **训练 / 微调 workflow**: Dify 是 inference + orchestration，不碰训练
- **极致 RAG**: 需要 KG-RAG、deep parsing、混合检索调优 → **RAGFlow** 更专  [sider.ai/blog/ai-tools/dify-vs-ragflow]
- **AI 代码已经能写**: 业内已有声音 "既然在 Dify 里也要写 Python，何不直接 Python？"  [zhuanlan.zhihu.com/p/1947389040702781389]

### 1.3 心智门槛 (Mental check)
> Dify 的核心价值是 **"把 LLM 应用工程的脚手架打平"**——auth、API、UI、向量库、模型 provider、日志、版本——而不是替代 LLM 编排框架本身的表达力。

判断公式:
- 如果你的瓶颈是 **"组装周边设施"** → 用 Dify
- 如果你的瓶颈是 **"逻辑表达力 / 状态管理 / 极致性能"** → 用 LangGraph / 直接代码

---

## 2. 核心心智模型 (Mental Model)

### 2.1 五层架构 (The 5-layer stack)
```
[Studio]        ← Visual canvas (workflow / chatflow / agent / chatbot / text-gen)
   ↓ 编排
[Apps]          ← 5 种 app 类型，全部跑在统一 Graph Engine 上
   ↓ 依赖
[Knowledge]     ← RAG pipeline (ingest → chunk → embed → index → retrieve → rerank)
   ↓ + 调用
[Tools/Plugins] ← Marketplace: Models / Tools / Agent Strategies / Extensions / Bundles
   ↓ 观察
[Monitoring]    ← 内建 logs + 外接 LangSmith / Langfuse / Arize Phoenix / Opik
```
参考: [docs.dify.ai/en/introduction], [dify.ai/blog/dify-plugin-system-design-and-implementation]

### 2.2 五种 App 类型 — 选哪个？

| App Type | 触发模型 | 记忆 | 编排方式 | 典型场景 |
|---|---|---|---|---|
| **Chatbot** (legacy) | 多轮对话 | 内置 | 单 prompt + tools | 简单客服、FAQ bot |
| **Agent** (legacy) | 多轮对话 | 内置 | ReAct / FC 自主决策 | 自治工具使用、多步推理 |
| **Text Generator** (legacy) | 单次调用 | 无 | 单 prompt | 文案生成、翻译 |
| **Workflow** | 单次调用 / 批处理 | **无** | 可视化 DAG | API 后端、批量任务、ETL |
| **Chatflow** | 每轮对话触发整图 | **有** (conversation vars) | 可视化 DAG + 对话状态 | 复杂对话流、guided dialogue |

**核心决策树**:
```
有对话上下文需求？
├─ 是 ─→ Chatflow (复杂逻辑) 或 Chatbot/Agent (简单)
└─ 否 ─→ Workflow (复杂逻辑) 或 Text Generator (单 prompt)

需要 LLM 自主选择工具 / 多步推理？
├─ 是 ─→ Agent app  或  Workflow + Agent Node (推荐, 1.9+)
└─ 否 ─→ Workflow / Chatflow + 显式节点编排
```
参考: [docs.dify.ai/en/use-dify/getting-started/key-concepts], [hellodify.com/en/docs/workflow/workflow-chatflow-difference], [zediot.com/blog/dify-difference-between-agent-and-workflow]

> "Workflow behaves more like a script… each Workflow run is a completely fresh start. Chatflow… is a robot that can interact with users in a loop."  [hellodify.com/en/docs/workflow/workflow-chatflow-difference]

### 2.3 Graph Engine = "graphon"
- 自研 DAG 执行引擎，所有 app 类型底层一套
- v1.9+ 重写为 **queue-based scheduling**: 任务统一入队、调度器管依赖与并行  [github.com/langgenius/dify/discussions/26138]
- 节点有标准签名：输入变量 → 处理 → 输出变量
- 支持：partial run、step debugging、stream-stitch across nodes、pause/terminate commands

### 2.4 节点目录 (Node taxonomy)
| 类别 | 节点 | 用途 |
|---|---|---|
| **基础** | Start, End, Answer | 入口 / 出口 |
| **LLM** | LLM, Question Classifier, Parameter Extractor | 调模型 |
| **RAG** | Knowledge Retrieval | 查知识库 |
| **逻辑** | IF/ELSE, Iteration, Loop, Variable Assigner, Variable Aggregator | 控制流 |
| **代码** | Code (Python/Node.js), Template (Jinja2) | 自定义逻辑 |
| **外部** | HTTP Request, Tool, Agent Node | 调外部 / 子 agent |
| **数据** | List Operator, Document Extractor | 处理结构化数据 |

> "Dify's canvas includes LLM calls, knowledge retrieval, conditionals, HTTP requests, code nodes (Python/Node), Jinja transforms, iterators/loops, and aggregators."  [legacy-docs.dify.ai/guides/workflow/node]

### 2.5 Plugin 系统 (五元类型)
v1.0+ 引入插件系统，从 monolith → marketplace。  [dify.ai/blog/introducing-dify-plugins]

| 类型 | 用途 | 何时选它 |
|---|---|---|
| **Models** | 接入新模型 provider | 内置不支持的模型 |
| **Tools** | 给 agent / workflow 加能力 | 需要复用的领域工具 (Slack, Notion, 自家 API) |
| **Agent Strategies** | 自定义 reasoning loop | 想用 ToT / GoT / 自研推理 |
| **Extensions** | 轻量 HTTP webhook | 简单 API 接入，不需打包 |
| **Bundles** | 多插件打包 | 整套行业解决方案 |

**决策**: 一次性 = HTTP Request 节点；可复用 = Tool plugin；逻辑深 = Agent Strategy plugin。

### 2.6 Knowledge Base (RAG) 心智
RAG 流程: **Ingest → Extract → Clean → Chunk → Embed → Index → Retrieve → Rerank → Augment**  [docs.dify.ai/en/guides/knowledge-base/readme]

三种构建方式:
1. **Quick create** — 上传即用，自动处理
2. **Knowledge pipelines** (v1.9+) — 可视化定义 ingest 流程，类似 workflow but for data
3. **External integration** — 接外部知识库 API (Pinecone / Weaviate / 自有 RAG 服务)

向量库支持: **13+** (Qdrant 默认推荐, Weaviate, Milvus, Pinecone, PGVector, TiDB, Chroma…)  [deepwiki.com/langgenius/dify-docs/8.3-vector-database-configuration]

检索策略:
- **N-to-1 Recall** (需 reasoning model 选库)
- **Multi-way Recall** (并行检索 + Rerank model 合并)

---

## 3. SOP 工作流 (Standard Operating Procedure)

### Phase 0: 选定 App 类型 (5 分钟决策)
1. 问：**对话还是一次性任务？** → Chatflow 系 vs Workflow 系
2. 问：**逻辑能写死，还是要 LLM 自主决策？** → 显式 workflow vs Agent (app or node)
3. 问：**会不会跟 PM/业务方共编？** → 是 → 优先 visual app；否 → 考虑直接代码
4. 问：**是 MVP 还是会长期演进？** → 长期 → 强烈建议 Workflow/Chatflow（legacy 三件套不推荐）

> 官方建议: "Workflow/Chatflow are recommended for most use cases. Use the legacy basic types (Chatbot/Agent/Text Generator) only if preferring simplified interfaces over advanced features."  [docs.dify.ai/en/use-dify/getting-started/key-concepts]

### Phase 1: 部署 (Deploy) — 30 分钟
**Cloud (推荐起步)**:
- Sandbox (Free): 200 credits / 10 apps / 5MB storage
- Professional ($59/mo): 5k credits / 50 apps / 5GB
- Team ($159/mo): 10k credits / 20GB / SSO
- Enterprise: 自定义  [architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host]

**Self-host (Docker Compose)** — 最常用:
```bash
git clone https://github.com/langgenius/dify
cd dify/docker
cp .env.example .env
docker compose up -d
```
- 最低: 2 vCPU / 4GB RAM
- 生产建议: 2 vCPU / 4GB / 40GB SSD + 反向代理 (Caddy/Nginx) + HTTPS
- 切勿直接暴露内部端口到公网  [docs.dify.ai/en/self-host/quick-start/docker-compose]

**关键环境变量**:
- `VECTOR_STORE` — 选 Qdrant / Weaviate / Milvus / Pinecone…
- `PLUGIN_DAEMON_TIMEOUT=300` — 插件超时
- `WORKFLOW_MAX_EXECUTION_TIME` / `HTTP_REQUEST_MAX_READ_TIMEOUT` — 长链路必调

### Phase 2: Prompt + 单节点 (Prompt Studio) — 1 小时
1. **先在 Prompt IDE 调通单个 LLM 调用**——别上来就堆 workflow
2. 在 Prompt IDE 多模型对比 (GPT-4 / Claude / 自有模型)
3. 把变量 `{{var}}` 抽出来——后续会成为 workflow 输入

### Phase 3: 接知识库 (Knowledge) — 半天
1. 上传文档 → 选 **High-Quality** (embed + vector) 或 **Economical** (BM25, 省钱)
2. 调 chunk size / overlap (默认 500/50 起手，长文档调到 1000+)
3. 跑 **Retrieval Testing**——用真实问题模拟，看召回的 chunks
4. 调 retrieval mode: Semantic / Full-text / **Hybrid (推荐)**
5. 接 Rerank 模型（jina-rerank, cohere-rerank, BGE-rerank）
6. 文档量大 / 多类型时 → 用 **Knowledge Pipeline** 自定义 ingest

> "Dify provides a comprehensive RAG pipeline handling the full lifecycle from raw file upload through extraction, cleaning, segmentation, embedding, indexing, retrieval, and reranking."  [pyshine.com/2026/04/20/Dify-Open-Source-LLM-App-Development-Platform]

### Phase 4: 接工具 (Tools) — 半天
- 内置 50+ 工具: Google Search, DALL·E, WolframAlpha, Stable Diffusion…  [github.com/langgenius/dify]
- 自家 API → 优先用 **HTTP Request 节点** (零代码)
- 复用 / 团队共享 → 写成 **Tool plugin**
- 复杂业务逻辑 → **Code 节点** (Python/Node.js, sandboxed)

### Phase 5: 编 workflow (Build) — 1-3 天
**构建顺序** (反直觉但重要):
1. **先线性跑通**——LLM → Knowledge → LLM → End
2. **加 IF/ELSE 分支**——只在真正需要分流时
3. **加 Iteration**——批量处理列表
4. **加 Agent Node** (1.9+)——当确实需要 LLM 自主选工具时
5. **再加 Code 节点**——填补无法表达的逻辑

**反模式**: 一上来就画 30+ 节点的复杂图。先线性跑通，再分支。

### Phase 6: 测试 + 发布 (Test & Publish) — 1 天
1. **Step debugging**——每个节点单步执行
2. **Test run**——从任意节点开始跑 (1.9+ 支持)
3. **Annotation Reply** (chat apps)——把好回答标注下来，下次直接返回 (省 token + 提质)  [dify.ai/blog/boosting-chatbot-quality-cutting-costs-with-dify-annotation-replies]
4. **Version control**——发布版本带 release notes，可回滚  [legacy-docs.dify.ai/guides/management/version-control]
5. **导出 DSL (YAML)**——纳入 git 版本管理  [github.com/langgenius/dify-docs/blob/main/en/guides/workflow/export_import.md]
6. **发布**为 Web App / API endpoint / MCP Server

### Phase 7: 接观测 (Monitor) — 半天
1. 内建 logs：每次调用的 input/output/token/latency
2. 外接 LLMOps:
   - **LangSmith** — LangChain 全家桶用户  [docs.dify.ai/guides/monitoring/integrate-external-ops-tools]
   - **Langfuse** — 开源自托管首选  [langfuse.com/integrations/no-code/dify]
   - **Arize Phoenix** — 评测优先  [dify.ai/blog/dify-arize-how-to-evaluate-monitor-and-improve-agents]
   - **Opik** — 性能最快  [comet.com Opik]
3. 跟踪 7 类 trace: Workflows / Messages / Moderation / Suggested Questions / Dataset Retrieval / Tools / Generated Names

### Phase 8: 迭代 (Iterate) — 持续
1. 看监控里的 **bad cases** → 标注 → annotation reply 或返工 prompt
2. 收集 traces → 在 Phoenix/Langfuse 建 eval dataset → 对比 prompt 变体
3. 复杂 workflow 出现性能问题 → 拆 sub-workflow / 改 queue model / 接外部服务

---

## 4. 操作模型 (Operation Model)

### 4.1 工作流构件清单
```yaml
# 一个典型 Dify workflow 的 building blocks
inputs:           # Start 节点变量 (text / number / file / select)
nodes:
  - llm:                    # 调模型
      model: gpt-4-turbo
      prompt: "..."
      memory: false         # workflow 永远是 false
  - knowledge_retrieval:    # 查知识库
      datasets: [kb_id_1, kb_id_2]
      mode: hybrid
      rerank: bge-rerank
  - if_else:                # 分支
      conditions: [...]
  - iteration:              # 批处理列表
      iterator: {{node.output}}
      sub_workflow: [...]
  - code:                   # Python/Node
      code: "def main(x): return ..."
  - http_request:           # 调外部
      method: POST
      url: "..."
  - agent:                  # 自主决策子节点 (1.9+)
      strategy: react / function_calling / custom
      tools: [...]
      max_iterations: 5
outputs:          # End / Answer 节点
```

### 4.2 变量系统
- **User Input** — Start 节点定义
- **Node Output** — `{{node_id.var}}` 跨节点引用
- **Environment Variables** — secrets, API keys
- **Conversation Variables** (Chatflow only) — 跨轮持久化  [docs.dify.ai/en/use-dify/getting-started/key-concepts]
- **System Variables** — `sys.user_id`, `sys.conversation_id` 等

### 4.3 发布形态
1. **Web App** — 一键得 hosted chat UI
2. **API** — REST endpoint + API key
3. **Embed** — iframe / web SDK
4. **MCP Server** (新) — 暴露给外部 agent 调用
5. **Tool** — 作为另一个 Dify app 的工具

### 4.4 多租户 / Workspace
- 同一 Dify 实例支持多 workspace
- 每 workspace 独立的 models / API keys / members / apps
- RBAC: Owner / Admin / Editor / Normal  [blog.elest.io/dify-vs-langflow-vs-flowise]
- ⚠️ **已知限制**: model provider key 是 workspace 级，无法 per-app 区分  [github.com/langgenius/dify/issues/32167]

### 4.5 DSL (YAML) 工作流
- **导出**: Studio → 应用菜单 → Export DSL
- **导入**: 跨实例迁移、git 版本管理、CI/CD
- **限制**: Knowledge base 数据本身不打包到 DSL (v1.8.1 时仍未支持)  [github.com/langgenius/dify/issues/25999]

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1: "Workflow 变得不可维护——拆子工作流还是改写代码？"

**症状**:
- Workflow 画到 30+ 节点，canvas 拖动卡顿 (issue #28245)  [github.com/langgenius/dify/issues/28245]
- 分支嵌套深，看不清数据流
- 改一处怕碰别处

**决策树**:
```
节点数 < 20 且分支扁平
   → 留在 Dify, 优化命名 + 加 Note
节点数 20-40, 有可复用子流程
   → 拆 sub-workflow (打包成 Tool 给主流程调用)
节点数 > 40 或 大量 Code 节点
   → 信号: 业务逻辑已超出可视化优势
   → 把核心逻辑改写为 Python 服务, Dify 只做编排前端 + RAG
```

**实操**:
- Workflow app 可以被打包为另一个 workflow/chatflow 的 **Tool** — 这是 Dify 提供的模块化路径  [hellodify.com/en/docs/workflow/workflow-chatflow-difference]
- 复杂业务逻辑 → 用 HTTP Request 节点调外部微服务，Dify 退化为 orchestrator

**反模式**: 在 Code 节点里写 200 行 Python——这是 "Dify 已不合适" 的信号。

### Case 2: "可视化已到天花板——继续 Dify 还是切 LangGraph / 直接代码？"

**症状**:
- 需要 **pause-and-wait-for-user**（审批、用户多步选择）— Dify 不支持，issue #21455 closed "not planned"
- 需要复杂状态机 / 循环 / 中断恢复 / time-travel
- 需要 sub-second 延迟
- 节点级 DB 查询拖累吞吐  [memo.d.foundation/breakdown/dify]

**判断公式**:
| 信号 | 留 Dify | 切代码 |
|---|---|---|
| 团队非 100% 工程师 | ✅ | ❌ |
| 需要快速 UI / API / 认证 | ✅ | ❌ (得自己搭) |
| pause-and-wait | ❌ | ✅ (LangGraph 原生) |
| QPS > 10 / pod | ❌ | ✅ |
| 复杂状态 + 回滚 | ❌ | ✅ |
| RAG + 简单编排 | ✅ | — |

**混合方案 (推荐)**: Dify 做前端 / RAG / 用户管理 / 监控；核心 agent 逻辑跑在 LangGraph 服务后端，Dify HTTP Request 节点调用。

> "Dify wins when you're building an LLM-powered SaaS, an internal product with multiple teams… Langflow is for teams that need power now and will need more later."  [blog.elest.io/dify-vs-langflow-vs-flowise]

### Case 3: "Self-host 还是 Cloud——什么时候值得自己运维？"

**症状**:
- 团队在评估 Dify Cloud Pro ($59) vs 自部署 Docker

**决策矩阵**  [architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host]:

| 条件 | 选 Cloud | 选 Self-host |
|---|---|---|
| 团队 ≤ 3 人, 用量小 | ✅ ($59-159/mo 比养 DevOps 便宜) | ❌ |
| 合规 / 数据驻留 (金融、医疗) | ❌ | ✅ |
| 用量大 (millions of API calls) | ❌ (订阅成本超过 infra) | ✅ |
| Air-gapped / 内网部署 | ❌ | ✅ |
| 自定义 vector store / 模型 | 部分支持 | ✅ 完全控制 |
| 不想管 backup / scaling | ✅ | ❌ |

**实操要点**:
- 自部署不是"docker compose up"完事——需要反向代理 + HTTPS + 备份 + 监控 + 升级策略
- 生产 self-host 用 Kubernetes + Helm + 外部 PostgreSQL/Redis/Vector DB（不要用容器内置的）
- ⚠️ Community / Premium / Enterprise 用同一 Docker image，差异在环境变量  [github.com/langgenius/dify/discussions/32254]

### Case 4: "Dify 知识库 vs 独立向量库 (Pinecone / Weaviate 自管)——边界在哪？"

**症状**:
- 团队有现存 Pinecone 索引 / 多个产品共享 RAG / 想精细控制 chunking 和 embedding pipeline

**决策**:
| 场景 | 用 Dify 内建 Knowledge | 用 External Knowledge |
|---|---|---|
| 单个 app 单个数据集 | ✅ 一键搞定 | ❌ over-kill |
| 多 app 共享同一份 KB | ✅ Dify KB 可被多 app 引用 | — |
| 极致 chunking / 实验性 retrieval | ❌ Dify 抽象有限 | ✅ |
| 已有自建 RAG 服务 | ❌ | ✅ Dify HTTP/External KB 接入 |
| 数据量 > 100M chunks | ❌ Dify 有 memory leak 风险  [memo.d.foundation/breakdown/dify] | ✅ |
| 需要 KG-RAG / hybrid + late interaction | ❌ | ✅ 或换 RAGFlow |

**混合**: Dify Knowledge 管常规文档；External Knowledge API 接你的自有 RAG 服务做长尾。

### Case 5: "用 Agent app vs Workflow + Agent Node vs 显式 Workflow——分歧何在？"

**症状**: 同一个需求，三种实现方式纠结。

**决策原则**  [zediot.com/blog/dify-difference-between-agent-and-workflow], [dify.ai/blog/dify-agent-node-introduction-when-workflows-learn-autonomous-reasoning]:

```
任务路径可预测、调试性优先
  → 显式 Workflow (写死分支)

任务路径不可预测、需 LLM 选工具
  → Workflow + Agent Node (1.9+)
     [推荐!! 比纯 Agent app 更可控, 既享受自主性又有 workflow 外壳]

纯对话 + 工具调用、不需要复杂编排
  → Agent app (legacy)

混合: 主流程显式, 局部不确定路径
  → Workflow 主图 + 不确定段塞 Agent Node
```

> "The best systems combine both — workflows as orchestrators that delegate reasoning tasks to agents. This hybrid model provides both predictability and intelligence."  [zediot.com/blog/dify-difference-between-agent-and-workflow]

**反模式**:
- Agent app 包打天下——失去 workflow 的可观察性
- 用 Workflow 强行表达完全不可预测的任务——逻辑膨胀

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### 6.1 常见反模式

| 反模式 | 症状 | 修法 |
|---|---|---|
| **30+ 节点单图** | 卡顿 + 难调  [issue #28245] | 拆 sub-workflow / Tool |
| **Code 节点写业务核心** | Code 节点 200+ 行 Python | 抽到外部微服务, Dify 用 HTTP 调用 |
| **不上 Knowledge Pipeline** | 文档质量飘忽 | 用 1.9+ 的 pipeline 自定义 ingest |
| **没接 LLMOps** | 上线后看不见 bad case | 接 Langfuse / Phoenix |
| **DSL 不入 git** | 改飞了无法回滚 | 导出 DSL → git, 用 dify-dsl-exporter 批量化  [github.com/linhai0872/dify-dsl-exporter] |
| **legacy Chatbot/Agent app 长期演进** | 无法表达分支 / 后期被迫迁移 | 直接上 Chatflow / Workflow |
| **workspace 共用 API key** | 不同 app 计费混乱 | 已知限制, 暂用多 workspace 规避 |
| **不做 retrieval testing** | RAG 召回质量差还不自知 | 上传后**立刻**用真实 query 在 Retrieval Testing 里跑 |
| **stream 长任务 > 120s 不调超时** | Agent node 突然断开  [issue #27053] | 调 `WORKFLOW_MAX_EXECUTION_TIME` + 反代超时 |

### 6.2 性能边界 (硬约束)
- **~10 QPS / pod** (1 CPU 2GB)——超过需水平扩 worker + queue depth 调优  [memo.d.foundation/breakdown/dify]
- **每节点单独 DB query**——长 workflow 累积延迟
- **120s streaming**——agent node 默认 timeout (可调但反代也要调)  [github.com/langgenius/dify/discussions/27053]
- **plugin daemon 300s**——`PLUGIN_DAEMON_TIMEOUT`
- **Cloud 配额硬上限**——超额无法 reindex, 只能删数据  [discussions/32013]

### 6.3 不要用 Dify 做的事
- 模型训练 / 微调编排（用 Axolotl / LLaMA-Factory）
- 通用工作流自动化（n8n / Zapier 更全, 400+ 集成）
- 极致 RAG（RAGFlow / 自建栈）
- pause-and-wait-for-user 审批流（LangGraph / Temporal）
- 高频实时推理路由（vLLM + 自己的网关层）
- 拿 Code 节点当微服务（迟早爆）

### 6.4 治理与升级
- 升级前**必读 release notes**——1.9 升级会摧毁 beta knowledge pipelines  [discussions/26138]
- API 兼容性：DSL 跨大版本可能需 migration
- 插件签名: 1.0+ 引入加密签名, marketplace 上传需通过审核
- Apache 2.0-like license（"not really"）——商业重度依赖前确认条款  [memo.d.foundation/breakdown/dify]

---

## 7. 生态对照 (Ecosystem Comparison)

### 7.1 对位表 — 何时选谁
| 框架 | 抽象层 | 上手 | 天花板 | 选它的硬触发 |
|---|---|---|---|---|
| **Dify** | 平台 (UI+API+RAG+Auth) | 几小时 | 中等 (DB-bound, 单图复杂度) | 全栈 + 多角色协作 + 快速上线 |
| **Flowise** | 节点编辑器 (薄层) | 几小时 | 低 (chatbot+RAG 为主) | 1GB RAM 最小部署、纯 chatbot |
| **LangFlow** | LangChain 可视化包 | 半天 | 高 (可导出代码) | 已用 LangChain，想加 UI |
| **Coze (扣子)** | 字节托管平台 | 小时 | 中等 (国内生态) | 国内市场 / 飞书集成 / 不要 self-host |
| **RAGFlow** | 专精 RAG 引擎 | 半天 | RAG 维度极高 | 文档解析 + KG-RAG 是核心 |
| **n8n** | 通用 workflow | 半天 | LLM 是 plugin | 400+ 非 AI 集成 + AI 是辅助 |
| **LangGraph** | 代码框架 | 几天 | 极高 | 需要状态机 / 中断 / 时间旅行 |
| **LlamaIndex** | RAG 框架 | 几天 | 极高 (数据侧) | RAG 是 P0 + 工程团队 |
| **CrewAI** | 多 agent 代码 | 半天 | 中 (角色编排) | 2-5 个角色协作 pipeline |

参考: [blog.elest.io/dify-vs-langflow-vs-flowise], [jimmysong.io/blog/open-source-ai-agent-workflow-comparison], [toolhalla.ai/blog/dify-vs-flowise-vs-langflow-2026]

### 7.2 关键对比 (一行话)

- **Dify vs Flowise**: Dify 是 "production SaaS 全家桶"; Flowise 是 "最小可用 chatbot 编辑器"。生产用 Dify, demo 用 Flowise。  [blog.elest.io/...]
- **Dify vs LangFlow**: Dify 不绑定 LangChain, 更平台化; LangFlow 是 LangChain 可视化壳, 工程团队友好。
- **Dify vs Coze**: Coze 是托管 only + 字节生态; Dify 开源 + 自部署。海外 / 自主可控选 Dify。
- **Dify vs RAGFlow**: Dify 是 "平台 with RAG"; RAGFlow 是 "极致 RAG with thin UI"。文档解析需求重选 RAGFlow，应用层选 Dify。  [sider.ai/blog/ai-tools/dify-vs-ragflow]
- **Dify vs n8n**: n8n 集成多 (400+) 但 AI 是补丁; Dify AI 原生但非 AI 集成弱。AI 为主选 Dify, 自动化为主选 n8n。  [zhuanlan.zhihu.com/p/1898775808660710158]
- **Dify vs LangGraph**: Dify 是 visual platform; LangGraph 是 code framework。可视化协作选 Dify, 复杂状态机选 LangGraph。混合用最常见。
- **Dify vs LlamaIndex**: 不同层。LlamaIndex 做数据/RAG 底层, Dify 可以**接 LlamaIndex 的 retrieval 输出**。

### 7.3 "为什么 50k+ stars"
1. **打平了脚手架**——auth、UI、API、向量库、模型 provider、日志、版本，开箱
2. **多角色友好**——PM/运营可以画 chatflow，工程师下钻 Code 节点
3. **国际化**——中文社区强 (江西 LangGenius 团队) + 英文文档完整 + 海外用户多
4. **真在打磨"production"**——1.0 引入插件，1.9 重写 graph engine, 持续高频迭代

### 7.4 "什么时候 Dify 已经不够"
- 单图节点数 > 50 (canvas 卡 + 难维护)
- 需要 pause-wait-resume 或复杂时间旅行
- QPS > 10/pod 持续负载
- 极致 RAG 实验
- 业务核心是 agent 自主性（Agent 比 workflow 更核心）

此时: Dify 退到 "前端 + 监控 + RAG 仓库"，核心逻辑切到 LangGraph / 自研代码服务。

---

## 附录 A: 关键链接

- 主页 / Repo: https://github.com/langgenius/dify
- 文档: https://docs.dify.ai/
- Marketplace: https://marketplace.dify.ai/
- 官方插件: https://github.com/langgenius/dify-official-plugins
- Cloud: https://cloud.dify.ai/
- 中文文档镜像: https://hellodify.com/

## 附录 B: 最小可运行示例（Workflow YAML 心智）
```yaml
# 一个 "知识库问答 + 工具调用" 的最小 chatflow 骨架
app:
  name: support-copilot
  mode: advanced-chat   # = chatflow
graph:
  nodes:
    - start: { variables: [{name: query, type: text}] }
    - knowledge_retrieval:
        dataset_ids: [kb_docs]
        retrieval_mode: hybrid
        top_k: 5
        rerank_model: bge-reranker-v2
    - llm:
        model: gpt-4-turbo
        prompt:
          - role: system
            content: "You are a support agent. Use the context to answer."
          - role: user
            content: "Context: {{knowledge_retrieval.result}}\n\nQ: {{start.query}}"
        memory: { enabled: true, window: 10 }  # chatflow 才有
    - answer: { stream: true, content: "{{llm.text}}" }
features:
  - annotation_reply: true
  - moderation: openai-moderation
  - conversation_variables: [user_tier]
```
