---
name: agentsop-crewai
version: 1.0.0
description: SOP for building multi-agent systems with CrewAI — role-based collaboration, sequential/hierarchical processes, Flows, memory, delegation. Use when modeling agent teams with clear roles and task pipelines.
domain: multi-agent-orchestration
framework: crewAI
framework_version: ">=0.80, current 1.14.x (May 2026)"
trigger_keywords:
  - "multi-agent crew"
  - "role-based agents"
  - "agent collaboration"
  - "sequential process"
  - "hierarchical agents"
  - "manager agent"
  - "CrewAI Flow"
  - "agent delegation"
when_to_use:
  - "modeling 2-5 specialized agents with clear roles (researcher + writer + reviewer)"
  - "linear or hierarchical content pipelines where role separation is intuitive"
  - "rapid prototyping of agent teams without graph-state engineering"
  - "business workflows where ops/PM can reason about agents as 'team members'"
when_not_to_use:
  - "single-agent tasks (~80% of use cases per production guides — use plain LLM call)"
  - "cyclic / state-rich workflows with branching logic (use LangGraph)"
  - "real-time / sub-second latency (multi-agent handshakes add 30–50% tokens)"
  - "conversational debate / negotiation patterns (use AutoGen)"
  - "deterministic routing with strict SLA (CrewAI hierarchical executes tasks sequentially regardless of triage)"
---

# CrewAI SOP — Role-Based Multi-Agent Orchestration

> 框架口号: "Framework for orchestrating role-playing, autonomous AI agents. By fostering collaborative intelligence, CrewAI empowers agents to work together seamlessly."  [github.com/crewAIInc/crewAI]

---

## 1. 何时激活 (When to Activate)

### 1.1 直接信号 (Direct triggers)
- 用户说 "我需要 researcher + writer + reviewer 这种团队配合"
- 用户说 "用 CrewAI 实现 / 我已经在用 crew.kickoff()"
- 任务可以拆为 2–5 个**专业角色**，且每个角色有明确职责边界
- 流程是**线性 pipeline**（数据→分析→报告）或**轻度分支**

### 1.2 反向信号 (Skip CrewAI when)
- 单 agent + tool-use 就够 → 直接用 SDK / Instructor（CrewAI 是 over-engineering）
- 需要状态图 + 循环 + 中断恢复 → **LangGraph** 更合适
- 需要 agents 之间自由对话辩论 → **AutoGen** 更合适
- 需要严格条件路由（"if X then only A else B"）→ 用 **CrewAI Flows** 而非 hierarchical Crew，或直接 LangGraph
- 延迟敏感（<500ms） → 多 agent 编排不适合

### 1.3 心智门槛 (Mental check)
> "An agent needs agency, otherwise it's just another script." — João Moura, CrewAI 创始人  [softwareengineeringdaily.com/2025/06/03/crew-ai-with-joao-moura/]

如果你能用 `if/else` 提前写死流程，**不要用 Crew**。Crew 的本质是把"决策权"让渡给 LLM 角色。

---

## 2. 核心心智模型 (Mental Model)

### 2.1 四元抽象 (The 4 primitives)
```
Agent (role + goal + backstory)  ← 谁
   ↓ 持有
Task (description + expected_output + agent + context)  ← 做什么
   ↓ 组装
Crew (agents + tasks + process)  ← 怎么协作
   ↓ 选择
Process (sequential | hierarchical) + Flow (event-driven 编排)  ← 控制流
```

### 2.2 为什么 "role + goal + backstory" 三件套？
CrewAI 的核心假设：**LLM 在 role-playing 状态下表现更好**。
- **role**: 函数性身份 ("Senior Data Researcher") — 决定 prompt 主语
- **goal**: 个体目标 ("Uncover cutting-edge developments in {topic}") — 决定决策方向
- **backstory**: 经验/性格 ("You're a seasoned researcher with a knack for…") — 校准语气与判断风格

> "Backstory provides depth to the agent's persona, enriching its motivations and engagements within the crew."  [docs.crewai.com/en/concepts/agents]

**关键洞察**: backstory 不是装饰。它是 system prompt 的最大杠杆——同一个 role+goal，换 backstory 会显著改变产出质量与风格。

### 2.3 Sequential vs Hierarchical vs Flow

| 维度 | Sequential | Hierarchical | Flow |
|---|---|---|---|
| 任务路由 | 静态列表顺序 | manager LLM 动态分派 | `@listen` 事件驱动 |
| 控制力 | 高 (写死顺序) | 低 (manager 自由发挥) | 最高 (代码 + 状态) |
| Token 开销 | 1× 基线 | 1.3–1.5× (manager overhead) | 接近 1× |
| 调试难度 | 低 | 高 (manager 黑盒) | 中 |
| 何时用 | 80% 场景默认 | 真正需要动态分派 | 复杂分支 + 多 Crew 编排 |
| 已知坑 | task context 自动透传可能膨胀 | manager 会"执行所有 task"而非"按需调用" | 学习曲线 + 状态设计 |

参考: [docs.crewai.com/en/learn/hierarchical-process], [docs.crewai.com/en/concepts/flows], [towardsdatascience.com/why-crewais-manager-worker-architecture-fails-and-how-to-fix-it/]

### 2.4 Crew 不是 LangChain
CrewAI **从零写成、零 LangChain 依赖**，是 João Moura 刻意决定。这带来：
- 更快 import / 更小 footprint
- 但**生态工具少**（observability、eval 需要外接 Maxim/MLflow/Datadog）
- 错误日志在 Task 内部不易捕获，`print` 不易冒出来  [aaronyuqi.medium.com/first-hand-comparison-of-langgraph-crewai-and-autogen]

---

## 3. SOP 工作流 (Standard Operating Procedure)

### Phase 0: 决策 — 真的需要 Crew 吗？
```
[问] 这个任务是否需要 ≥2 个截然不同的"专业视角"协作？
  ├─ 否 → 用单 agent + tools，停止使用 CrewAI
  └─ 是 → 继续

[问] 流程是否有循环 / 状态依赖 / 人工中断点？
  ├─ 是 → 转 LangGraph (或 CrewAI Flow + 简化的 Crew)
  └─ 否 → 进入 Phase 1
```

### Phase 1: 角色设计 (Agent Design)

#### 1.1 拆分原则
- **每个 agent 一个职能动词**: research / write / review / extract / decide
- 避免 "万能 agent"。一个 agent 同时 research + write，质量必劣于两个专家
- **2–5 个 agent 是甜区**。≥7 个开始出现协调失败  [medium.com/@armankamran/anti-patterns-in-multi-agent-gen-ai-solutions]

#### 1.2 三件套写法 (role/goal/backstory)
```python
researcher = Agent(
    role="Senior AI Research Analyst",   # ← 名词性头衔，含"高级/资深"提升先验
    goal="Uncover cutting-edge developments in {topic} with citations",  # ← 含 {var} 模板 + 验收标准
    backstory=(
        "You're a methodical researcher with 10 years at top AI labs. "
        "You distrust hype and always cross-check with primary sources."  # ← 注入判断偏好
    ),
    allow_delegation=False,   # ← 默认 False，避免 ping-pong
    max_iter=10,              # ← 显式收敛上限（默认 20–25）
    verbose=True,             # ← 开发期必开
    tools=[search_tool],
)
```

#### 1.3 YAML 化（生产推荐）
配置与代码分离，使用 `@CrewBase` 装饰器 + `config/agents.yaml` + `config/tasks.yaml`，便于非工程人员迭代提示词  [docs.crewai.com YAML Configuration]。

### Phase 2: 任务设计 (Task Design)

#### 2.1 描述写法 (description)
- **动词开头** + 具体输入：`"Analyze the search results for {topic} and identify 3 emerging trends"`
- **不要写 how**，写 what。HOW 是 agent 的自由度
- 长度建议: 1–4 句。过长 = 把 agent 当工程模板用，违背 agency 哲学

#### 2.2 expected_output（验收契约）
- **必填**。这是 CrewAI 的"测试断言"
- 写成可机器校验的结构化描述：`"A markdown report with H2 headers per trend, each containing: trend name, 3 supporting citations, risk assessment"`
- 配合 `output_pydantic=MyModel` 强制结构化  [docs.crewai.com/en/concepts/tasks]

#### 2.3 context 显式声明依赖
```python
analysis_task = Task(
    description="...",
    expected_output="...",
    agent=analyst,
    context=[research_task],   # ← 不依赖隐式自动透传，显式声明
)
```
> "In crewAI, the output of one task is automatically relayed into the next one, but you can specifically define what tasks' output … should be used as context."

**默认隐式透传是坑**——pipeline 长了之后 prompt 爆炸。建议从一开始就显式 `context=[...]`。

### Phase 3: 装配 Crew

```python
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analysis_task, write_task],
    process=Process.sequential,   # ← 默认；改 hierarchical 前请读 §5.2
    memory=False,                 # ← 默认关，除非真的跨 kickoff 需要持久化
    verbose=True,
    max_rpm=30,                   # ← 防止 API 限流爆炸
    planning=False,               # ← v0.80+ 的实验功能，生产前先测
)
result = crew.kickoff(inputs={"topic": "agentic RAG"})
```

### Phase 4: 观测与收敛

#### 4.1 必装观测
CrewAI 内部日志薄。**生产前必须**：
- 接 `mlflow.crewai.autolog()` 或 Maxim / Langfuse / Datadog
- 包一层 `step_callback=` 捕获每步 agent action  [docs.crewai.com/en/observability/overview]

#### 4.2 token / 成本上限
- 单次 `kickoff` 设硬上限（外层 timeout + max_rpm）
- Hierarchical 模式追加 30–50% token 预算  [callsphere.ai/blog/crewai-process-types]

#### 4.3 eval 化
- 把每次失败的 kickoff trace 转成 eval case
- 用 LLM-as-judge 检查 `expected_output` 契约是否兑现

---

## 4. 操作模型 (Operational Model — Trigger / Action / Output / Evidence)

### OP-1: 决定是否使用 CrewAI
- **Trigger**: 用户描述任务时出现"团队/协作/不同角色"语义
- **Action**: 检查 §1.1/§1.2 清单 + Phase 0 决策树
- **Output**: 三选一 — (a) 用 CrewAI Sequential, (b) 用 CrewAI Flow+Crew, (c) 换框架
- **Evidence**: [§1, github.com/crewAIInc/crewAI README]

### OP-2: 设计 agent role/goal/backstory
- **Trigger**: 已决定用 Crew，开始建模角色
- **Action**: 每个 agent 填 role (头衔)、goal (含 {var} 与验收)、backstory (经验+判断偏好)；默认 `allow_delegation=False`、`max_iter=10`
- **Output**: agents.yaml 或 Python Agent() 调用
- **Evidence**: [docs.crewai.com/en/concepts/agents, §2.2]

### OP-3: 写 Task
- **Trigger**: agent 设计完毕，开始拆任务
- **Action**: description 写 what 不写 how；expected_output 写可校验契约；显式 `context=[...]`；可选 `output_pydantic`
- **Output**: tasks.yaml 或 Task() 调用列表
- **Evidence**: [docs.crewai.com/en/concepts/tasks, §3.2]

### OP-4: 选 Process
- **Trigger**: 装配 Crew 前
- **Action**: 默认 `Process.sequential`；只有当任务路由真的需要 LLM 动态判断时才用 `Process.hierarchical` + **自定义 manager_agent**（不要用裸 `manager_llm`）
- **Output**: `process=` 与（若 hierarchical）一个带详细 backstory 的 manager_agent
- **Evidence**: [§5.2, towardsdatascience.com 'Manager-Worker fails']

### OP-5: 启用 Memory
- **Trigger**: 跨 kickoff 需要"记住"或同一 kickoff 内复杂上下文聚合
- **Action**: 优先用 task `context=[...]` 显式传递；只有当真的需要"跨 session 持久"才 `memory=True`；高级场景考虑 Mem0 后端
- **Output**: `memory=False` 或 `memory=Memory(scope=...)`
- **Evidence**: [docs.crewai.com/en/concepts/memory, mem0.ai/blog/crewai-memory-production-setup-with-mem0]

### OP-6: 加观测与上限
- **Trigger**: 上生产前
- **Action**: `mlflow.crewai.autolog()` + `max_rpm` + `max_iter` 每 agent + 外层 timeout + step_callback
- **Output**: 可观测、可中止的 Crew
- **Evidence**: [docs.crewai.com/en/observability/overview, §4]

### OP-7: 从 Crew 升级到 Flow
- **Trigger**: Crew 出现 — (1) 需要条件分支 (2) 需要多个 Crew 串联 (3) hierarchical 不可控
- **Action**: 用 `@start`/`@listen` 写 Flow，每个 step 内部可 `crew.kickoff()`
- **Output**: 一个 Flow 类，state 用 Pydantic BaseModel
- **Evidence**: [docs.crewai.com/en/concepts/flows, community.crewai.com/t/5710]

---

## 5. 困境决策案例 (Dilemma Cases)

### DC-1: Agent 卡住反复重试 — 改 prompt 还是拆 agent？
**场景**: writer agent 输出质量差，反复 self-critique，5 次迭代后还在改文章结构。

**两条路**:
- **A. 改 prompt** — 把 backstory 写得更具体，goal 加更严的验收。优点：零改动 crew 结构。缺点：当 agent 在做"两件不同的事"（写 + 审），单 prompt 永远抓不住。
- **B. 拆 agent** — writer + reviewer 双 agent，sequential pass。优点：每个 agent 职责单一，更稳定。缺点：多一次 LLM 调用，token+50%。

**判断规则**:
1. 看失败案例：失败模式是否**风格不一致**？ → 改 backstory
2. 失败模式是否**遗漏检查项**（事实错误、格式错误）？ → **拆 agent**，让 reviewer 用结构化 checklist
3. 如果 5 次迭代后仍未稳定 → **强信号要拆**

**推荐**: 默认拆。CrewAI 的核心红利就在"单一职责角色"。当你纠结要不要拆，答案 80% 是拆。
> "Single-agent is right for approximately 80% of cases; the trap is reaching for multi-agent because it sounds more capable. But once you've committed to multi-agent, the next trap is putting too much in one agent."  [daily.dev AI agents guide]

**Evidence**: [§2.2, anti-patterns]

---

### DC-2: Sequential vs Hierarchical — 何时 manager 开销值得？
**场景**: 5 个 agent，task 顺序大致固定但偶尔需要根据上游结果跳过某些 task。

**陷阱**: 看起来"hierarchical 应该能自动路由"，**但实测 hierarchical 会执行所有 task，不会真的按 triage 结果跳过**  [towardsdatascience.com Manager-Worker fails]。论文式案例：

```
Query: "Why is my laptop overheating?" (纯技术问题)
期望: triage → technical_agent → done
实际 hierarchical: triage → technical → billing → ... → 最后一个 task 的输出覆盖前面
```

**三条路**:
- **A. Sequential** — 写死顺序，所有 task 都跑。简单稳定但浪费 token。
- **B. Hierarchical + 默认 manager_llm** — **不推荐**。manager 会失控执行所有 task。
- **C. Hierarchical + 自定义 manager_agent (带显式分支 backstory)** — 可工作但需要细致 prompt 工程。
- **D. CrewAI Flow** — 用 `@listen` + 条件函数显式路由，每分支调用一个小 Crew 或单 agent。

**判断规则**:
1. 路由逻辑可以**用 5 行 Python 表达**？ → 用 **Flow** (D)
2. 路由真的需要 LLM 语义理解（不能写规则）→ Hierarchical + **自定义 manager**（C），**永远不要**靠默认 manager_llm
3. 不确定 → 先 Sequential (A)，性能可接受就停

**红线**: 永远不要把生产路由依赖**默认 `manager_llm`**——João Moura 团队也承认这是当前最大坑之一  [github.com/crewAIInc/crewAI/discussions/1220]。

**Evidence**: [§2.3, community.crewai.com/t/5710, towardsdatascience.com]

---

### DC-3: 工具共享 vs 每个 agent 独立工具集？
**场景**: 你有 web_search、code_executor、db_query 三个工具，3 个 agent (researcher / analyst / reporter)。

**两条路**:
- **A. 全部共享** — 每个 agent `tools=[search, exec, db]`。简单但 agent 容易"逛工具" — researcher 也调 code_executor 写代码，违背角色分工。
- **B. 按角色配** — researcher=[search]，analyst=[exec, db]，reporter=[]（纯综合）。**职责更清晰，错误更可定位**。

**判断规则**:
- CrewAI 官方推荐 **B**（write once, use everywhere — tool 定义可复用；但每个 agent 只绑定其角色匹配的工具）  [docs.crewai.com/en/concepts/tools]
- 如果发现 agent 跨工具滥用 → 收紧工具白名单是最快的 fix
- 工具定义层面共享（同一个 BaseTool 类），但**绑定层面按需**

**Evidence**: [docs.crewai.com/en/concepts/tools, community.crewai.com/t/tool-best-practice-assign-to-agent-or-task/5919]

---

### DC-4: Memory 默认关 vs 全开？
**场景**: 一个客服 crew，多个会话之间是否需要记住用户？

**陷阱**:
- `memory=True` 默认开 short_term + entity，会**自动跑额外 LLM 调用做"记忆 LLM 分析"**，token 翻倍
- 当 memory 不对（错召回、过期信息）→ 调试地狱

**判断规则**:
1. **单 kickoff 内**的上下文 → 用 task `context=[...]` 显式传，**不用 memory**
2. **跨 kickoff** 才考虑 `memory=True`；首选 long_term（SQLite，便宜）
3. 真正生产级 + 高频 → 接 Mem0 后端，**不要用默认 LanceDB**  [mem0.ai/blog/crewai-memory-production-setup-with-mem0]
4. 调试期一律 `memory=False`，不然 trace 难读

**红线**: 不要把"agent 没记住 X"当成必须开 memory 的信号。99% 的情况是 task description 没把 X 写清楚。

**Evidence**: [docs.crewai.com/en/concepts/memory, §4]

---

### DC-5: allow_delegation 开还是关？
**场景**: hierarchical 模式下，是否给 worker agent 也开 `allow_delegation=True`？

**陷阱**: 多个 agent 都能 delegate → **delegation ping-pong**，agents 互相传球，token 爆炸 + 超时。已知 GitHub issue [#330 #4783 #2606]。

**根因**:
1. 循环 delegation（A → B → A → B…）
2. `DelegateWorkTool` schema 期望 string，新 LLM 传 dict，silent validation 失败 → 重试  [azguards.com delegation ping-pong]
3. `max_iter` 在 hierarchical 跨 handoff 时不生效，protection 形同虚设

**判断规则**:
1. **默认 `allow_delegation=False`** 在所有 worker agent 上
2. 仅 manager_agent 开 delegation
3. 即使在 hierarchical，链中至少有一个 agent `allow_delegation=False`
4. 加全局 token / 时间上限（外层包 timeout）
5. 如果一定要复杂 delegation → 用 Flow 显式编排，**别让 LLM 决定 delegate 给谁**

**Evidence**: [github.com/crewAIInc/crewAI/issues/330, azguards.com, inkog.io/glossary/crewai-infinite-loop]

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

### 6.1 五大反模式

| # | 反模式 | 症状 | 修复 |
|---|---|---|---|
| AP-1 | **Agent 数量爆炸** (>5 个 agent) | 协调失败、token 飞涨、debug 困难 | 合并职能近似的 agent；7+ 几乎必拆 Flow |
| AP-2 | **Backstory 不写或写"你是助手"** | 输出风格平庸、判断偏好混乱 | 注入经验、判断偏好、禁忌 |
| AP-3 | **依赖默认 hierarchical manager_llm** | manager 执行所有 task / 路由错乱 | 永远自定义 manager_agent，或换 Flow |
| AP-4 | **`allow_delegation=True` 全开** | 无限 delegation ping-pong | 默认关，仅 manager 开 |
| AP-5 | **没 observability 就上生产** | trace 黑盒，故障无法复现 | 上线前必接 MLflow/Maxim/Datadog |

### 6.2 何时**不要**用 CrewAI（重要）

| 场景 | 替代方案 |
|---|---|
| 单 agent 就够（80% 任务） | OpenAI/Anthropic SDK + Instructor/Outlines |
| 状态机 / 循环 / human-in-the-loop / 中断恢复 | **LangGraph** |
| 长对话 / 辩论 / 群体决策 | **AutoGen** |
| 简单工具调用 + handoff | **OpenAI Swarm / Anthropic Computer Use** |
| 数据为中心的 RAG (300+ connectors) | **LlamaIndex** |
| 严格的低延迟 SLA | 不用 multi-agent 框架，直接编排 |
| 需要 production-grade durability + 精细 state | **LangGraph** (已成 production-deployment 事实标准) |

### 6.3 已知工程坑速查表

- **日志**: Task 内 `print()` 经常不冒头。用 `step_callback` 或 verbose=True
- **token 预算**: hierarchical +30~50%；memory=True 再 +1×（记忆 LLM 分析）
- **Pydantic 版本**: CrewAI 与某些 langchain-tools 的 pydantic v1/v2 不兼容时常爆错
- **manager 模型选择**: gpt-4o-mini 不够强，hierarchical 推荐 gpt-4o / Claude Sonnet
- **YAML 模板变量**: `{topic}` 在 kickoff(inputs={"topic": ...}) 时替换，**不写在 inputs 里就是字面 "{topic}"**

---

## 7. 生态对照 (Ecosystem Comparison)

### 7.1 三大框架定位
| 框架 | 一句话定位 | 第一抽象 | 哲学 |
|---|---|---|---|
| **CrewAI** | "Agents are role-playing teammates" | Agent (role) | 把 LLM 当人格化协作者 |
| **LangGraph** | "Agents are nodes in a state graph" | Node + State | 把 agent 当可编译的图 |
| **AutoGen** | "Agents are chat participants" | Conversation | 把 agent 当群聊成员 |

### 7.2 选择决策树
```
你的核心需求是什么？
├─ 多角色明确 + 任务可线性串 → CrewAI Sequential
├─ 多角色 + 需要事件驱动分支 → CrewAI Flow（内嵌 Crew）
├─ 状态/循环/中断/恢复/precise control → LangGraph
├─ 多 agent 辩论/谈判/群体决策 → AutoGen
├─ 单 agent + handoff (不需要协作) → OpenAI Swarm / Anthropic
└─ 数据为中心 RAG → LlamaIndex
```

### 7.3 CrewAI 独特价值（什么时候首选）
1. **学习曲线最低** — PM/ops 能读懂 role/goal/backstory
2. **YAML 优先** — 提示词与代码分离，非工程人员可改
3. **Flow + Crew 混搭** — 既要 LLM agency 又要工程控制时的平衡点
4. **生态轻量** — 无 LangChain 依赖，启动快
5. **角色叙事 = 团队建模工具** — 在跨职能讨论中比 "node graph" 更易达成共识

### 7.4 CrewAI 已知短板（要承认的）
1. **生产可靠性** — hierarchical 模式有结构性 bug（OP-4, DC-2, DC-5），LangGraph 在生产部署占优
2. **observability** — 内置日志薄，必须外接
3. **状态管理** — 比 LangGraph 浅；复杂状态用 Flow 也吃力
4. **测试范式** — eval 工具链不如 LangSmith 成熟
5. **AutoGen 近况** — AutoGen 已进入 maintenance，长期看 LangGraph + CrewAI 是双雄

---

## Appendix A: 最小可工作示例 (Reference snippet)

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Senior AI Research Analyst",
    goal="Surface 3 emerging trends in {topic} with verifiable citations",
    backstory=(
        "You're a meticulous researcher who distrusts hype and demands "
        "primary sources. You've spent a decade at frontier AI labs."
    ),
    allow_delegation=False,
    max_iter=8,
    verbose=True,
)

writer = Agent(
    role="Technical Writer",
    goal="Turn research findings into a crisp executive brief",
    backstory=(
        "You write for time-poor execs. Bullet points over paragraphs. "
        "You refuse to ship without inline citations."
    ),
    allow_delegation=False,
    max_iter=5,
    verbose=True,
)

research_task = Task(
    description="Research {topic}. Find 3 emerging trends from 2025–2026.",
    expected_output=(
        "Markdown with 3 H2 sections, each: trend name, 2-sentence summary, "
        "≥2 citations (URL + title)."
    ),
    agent=researcher,
)

write_task = Task(
    description="Write an executive brief from the research output.",
    expected_output="≤400 word brief, bullet structure, inline citations preserved.",
    agent=writer,
    context=[research_task],   # 显式
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
    memory=False,
    verbose=True,
    max_rpm=30,
)

result = crew.kickoff(inputs={"topic": "agentic RAG"})
print(result.raw)
```

---

## Sources (核心引用)
- [docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents)
- [docs.crewai.com/en/concepts/tasks](https://docs.crewai.com/en/concepts/tasks)
- [docs.crewai.com/en/concepts/flows](https://docs.crewai.com/en/concepts/flows)
- [docs.crewai.com/en/concepts/memory](https://docs.crewai.com/en/concepts/memory)
- [docs.crewai.com/en/learn/hierarchical-process](https://docs.crewai.com/en/learn/hierarchical-process)
- [github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)
- [github.com/crewAIInc/crewAI/discussions/1220](https://github.com/crewAIInc/crewAI/discussions/1220) — manager_agent 正确用法讨论
- [github.com/crewAIInc/crewAI/issues/330](https://github.com/crewAIInc/crewAI/issues/330) — allow_delegation 无限循环
- [towardsdatascience.com Manager-Worker fails](https://towardsdatascience.com/why-crewais-manager-worker-architecture-fails-and-how-to-fix-it/)
- [azguards.com/the-delegation-ping-pong](https://azguards.com/technical/the-delegation-ping-pong-breaking-infinite-handoff-loops-in-crewai-hierarchical-topologies/)
- [softwareengineeringdaily.com/2025/06/03/crew-ai-with-joao-moura](https://softwareengineeringdaily.com/2025/06/03/crew-ai-with-joao-moura/) — João Moura "agency" 哲学
- [callsphere.ai/blog/crewai-process-types](https://callsphere.ai/blog/crewai-process-types-sequential-hierarchical-consensual-workflows)
- [community.crewai.com/t/5710](https://community.crewai.com/t/choosing-between-sequential-and-hierarchical-processes-in-crewai-for-a-shopping-chatbot/5710)
- [mem0.ai/blog/crewai-memory-production-setup-with-mem0](https://mem0.ai/blog/crewai-memory-production-setup-with-mem0)
- [datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
