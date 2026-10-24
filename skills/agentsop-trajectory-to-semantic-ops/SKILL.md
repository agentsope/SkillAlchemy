---
name: agentsop-trajectory-to-semantic-ops
version: 1.0.0
description: >-
  SOP for distilling reusable semantic operators (data-science operation skills) from agent execution trajectories: read action/observation traces, classify per-task failures, bind data-semantic constraints (input semantics / operation decision / output constraints / validation), and feed bounded edits back through an optimizer such as SkillOpt. Use when mining agent runs for cross-task operation knowledge, when a data-science skill keeps failing on the same operation family (join cardinality, group granularity, unit, time alignment), or when wiring trajectory history into a skill optimizer without polluting the skill body.
domain: agent execution-trajectory mining, data-science semantic operators, skill optimization
source: AgenticDataBench local repo (generator/ + testbed/) + SkillOpt + related-work survey
audience: coder-agents and researchers who extract or optimize operation skills from agent traces
---

# 执行轨迹 → 语义算子 提炼 SOP

> 一句话：把 agent 的一次运行轨迹（动作 + 观察 + 退出码 + 分数）压成「失败证据」，再把它翻译成**带数据语义约束的可复用算子**——不是把轨迹原样塞回提示词，而是提炼出「为什么这一步会错」的跨任务决策规则。

## 1. 何时激活本技能

下列任一情形成立时，按本 SOP 进入「轨迹提炼」工作模式：

- 你手里有一批 agent 运行产物：`trajectory.json`（结构化动作流）、`agent_trace.txt`（可读的「动作 → 观察」）、`results.jsonl`（逐题分数/失败原因）。
- 你要**从失败里长出新技能**，或让一个现有数据科学技能在某类操作上不再重复犯错。
- 你在跑 SkillOpt（或类似轨迹优化器），需要把历史轨迹喂进去，但**不希望污染技能正文**。
- 你关心的是**跨任务可复用**的操作知识，而不是某一题的具体答案。

**不应激活的反面信号**：见 §6 反模式与边界。

## 2. 核心心智模型

### 2.1 先分清三个「技能／算子」概念

| 概念 | 作用 | 你该提取的是哪一层 |
|---|---|---|
| LOTUS 式语义算子 | 用自然语言描述数据变换，交由执行计划实现 | 不能因名字叫 sem_join 就继承其语义模型 |
| 任务能力分类（AgenticDataBench skills） | 用操作模式标注/组织任务 | 是能力标签，不等于可直接加载的运行时技能 |
| SKILL.md 运行时技能 | 执行时提供流程、知识、代码与资源 | **这是承载形式**；贡献来自其中的机制 |

一句话：语义算子的价值，是保存「跨任务可复用的**决策约束**」，并让相邻操作能检查它们——不是把某条管线的实现代码当知识。

### 2.2 执行轨迹的真实结构

一条轨迹是 agent 动作的时间序列表（AgenticDataBench 实测格式）：

```json
{"kind":"message","content":"..."}
{"kind":"command","command":"bash -lc 'python3 - ...'","exit_code":0,"output":"..."}
{"kind":"command","command":"bash -lc '...'","exit_code":1,"output":"SyntaxError: ..."}
```

三个铁律：

- **`exit_code` 是失败信号，不是全部**。`exit≠0` 的步是「哪里断了」；但 `exit=0` 的步也可能错在语义（算对但口径错）。
- **`message` 是 agent 的自我叙述，不是事实**。它说「已完成」不等于产物正确；要拿命令/观察/分数交叉核对。
- **`output` 是观察**：`WROTE output.csv ROWS 10` 这种回读自检，比一句「完成」可信得多。

### 2.3 语义算子的五字段模板

每个算子至少记录这五样（缺一不可）：

| 组成 | 具体内容 |
|---|---|
| 适用条件 | 什么输入/状态下该用这个算子 |
| 输入语义 | 每行代表什么、连接键、键是否唯一、时间粒度、缺失键策略 |
| 操作决策 | 是否确需模糊匹配、阈值从哪来、一对多是否允许、未匹配如何处理 |
| 输出约束 | 输出粒度、键关系、连接覆盖率、行数变化、新增缺失值 |
| 验证与修复 | 键碰撞、多对多扩增、错误匹配；按失败类别读取对应修复说明 |

### 2.4 八类「容易出错」的操作族

先只挑 6–10 个高频且确实易错的操作族做原型：entity alignment（实体对齐）、join cardinality（连接基数）、grouped/window statistics（分组/窗口统计）、time alignment（时间对齐）、missingness（缺失）、unit handling（量纲）、train/test transformation（训练/测试转换）、artifact validation（产物校验）。

> 反例：join 后行数变化本身**不能判错**——一对多可能正是任务要求。检查器必须对照事先绑定的期望关系；没证据时给出「未验证」，不套统一规则。

## 3. SOP 工作流（轨迹 → 算子）

### Phase 1 — 收料（collect）

收集最近 N 轮的 `results.jsonl`（分数/失败原因）+ 每条轨迹。**只收，不改**。缺了分数只剩轨迹，等于只有症状没有诊断。

### Phase 2 — 压迹（trajectory → text）

把 actions 压成「动作 → 观察」文本。**优先失败步（`exit≠0`）**，再取尾部若干步。超预算就截断（默认 6000 字符，`OPT_HISTORY_CHARS` 可调）。

### Phase 3 — 归类（classify）

逐题趋势分五类：

```
persistent_fail    持续失败（跨轮都是 0）
regressed          之前能过，本轮退化
flat_partial       长期卡在部分分
improved           本轮有进步
stable_success     稳定满分（可跳过，不占预算）
```

排序占位按失败严重度：`persistent_fail → regressed → flat_partial`。

### Phase 4 — 合成材料（build material）

把分数、逐题趋势、失败轨迹拼成 markdown，用显式标记包裹：

```
<!-- SKILLOPT_HISTORY_START -->  …材料…  <!-- SKILLOPT_HISTORY_END -->
```

### Phase 5 — 注入并优化（inject → optimize）

材料挂到技能**尾部**（或放 `references/history_material.md` 走 bundle），交给优化器做**有界文本编辑** + 门控验证 + 拒绝坏编辑。

### Phase 6 — 剥离（strip）

优化产物里把材料**整段剥除**，产出一个干净的 `SKILL.md`。注入→剥离必须字节级一致（`filecmp` 通过）。

### Phase 7 — 验收

四个验收问题：
1. 同分布未见任务是否提升？
2. 未见数据集/领域是否提升？
3. 已见操作的新组合是否提升？
4. 换模型/harness 后收益是否保留？

## 4. 操作模型（命令/函数速查）

```
collect_history(窗口 N)     收集最近 N 轮分数+轨迹
_trajectory_text(actions)   动作压成「动作→观察」，优先 exit≠0 步
classify(逐题分)            五类趋势分类
build_history_material()    合成 markdown 材料
make_history_skill_init()   材料挂技能尾部
strip_history_text()        从产物剥除材料
```

关键约束：

- **bundle 优于扁平注入**：材料放 `references/history_material.md`，主文件从 9873 字符降到 3877 字符，主文件不被污染、执行器按需加载。
- **别把路径写成宿主机路径**：轨迹里的 `D:\...` 进 Linux 容器会找不到文件——送进去前把 workspace 映射成 `/workspace`。
- **token 口径要分清**：容器内网关可能不上报 usage（回退 tiktoken 估算），宿主机才给真实值。

## 5. 困境决策案例 (Examples / Scenarios)

### 案例 1 — 「调用次数涨了，但不知道是不是机制」

**触发**：技能调用次数与分数一起涨，想据此宣称「技能有用」。

**决策规则**：调用次数 ≠ 正确采用。分开记录：发现 → 激活 → 正文/资源加载 → 实际采用 → 结果收益。调用成功也不等于采用；零显式调用也不等于零效应（技能描述本身可能已进上下文）。

### 案例 2 — 「门控 4 题，噪声同量级」

**触发**：4 道门控题 × 每题 1 轮，用「技能变好/变坏」做判决。

**决策规则**：4 题门控的 95% 区间约 ±0.22，同技能两次评估可差 0.50，判决≈抛硬币。扩容到至少 8 题 × 2 轮，或 4 题 × 3 轮；换掉恒满分/恒零分的题。

### 案例 3 — 「技能越优化越膨胀，效果反而不单调」

**触发**：9 代净增 92 行（128→218），6 代零删除，规则互相反转（先立后反）。

**决策规则**：限制单代 diff（如 ≤8 行）、禁止反转上代规则；长度与效果不单调（163 行反而稳定）。最小改动 + 拒绝反转，比「每代大改」更稳。

### 案例 4 — 「训练集看不到提升，测试集却提升」

**触发**：训练集高基线低分辨率（单轮噪声 ±0.125），测试集低基线高分辨率（3 轮平均）。

**决策规则**：统一 repeat ≥ 3；训练/门控/测试三集零重叠，训练分本质是「另一组题的抽样」。按数据来源/任务家族分组，别随机按任务切。

### 案例 5 — 「语义约束写进 skill，但没人真的读 references」

**触发**：正文出现 references 链接，但顶层轨迹里没有读取 references/ 的记录。

**决策规则**：正文链接只证明「提供了入口」，不等于「资源被读取」。把「资源是否被读」单独当指标测，别把入口当采用。

## 6. 反模式与边界

### 不要这样做

| 反模式 | 后果 |
|---|---|
| 把实例答案 / 任务 ID / 测试集列名特例写进技能 | 过拟合，污染技能，泄漏评测 |
| 注入历史材料但不剥除 | 主文件膨胀，执行超时 |
| 用「未验证」当「已验证」 | 模糊匹配的语义正确性，类型/行数检查只能发现部分错误 |
| 把「连接后行数变化」一律判错 | 一对多可能正是任务要求 |
| 用单轮分数指导优化 | 噪声（±0.125）淹没信号 |

### 硬边界

- **不生产答案，生产约束**：算子保存的是可复用决策约束，不是某题的代码。
- **不把 oracle 当正式成绩**：用 gold skills/gold 代码做路由只能标作 oracle 诊断，不能混入主结果。
- **不预设「层级越深越好」**：渐进披露收益取决于规模和 harness，需实验支撑。
- **不把相关性当因果**：评分与调用次数一起变，不足以证明机制。

## 7. 生态对照

| 工作 | 与本 SOP 的关系 |
|---|---|
| SkillOpt | 直接复用的有界文本编辑 + 门控 + 慢更新优化器；本 SOP 是它的「喂料」前置 |
| SemPipes / EvoDS / EvoSkill | 均已覆盖「给数据科学设计可优化算子」；差异点应在数据语义状态、组合约束、局部反馈 |
| Skill Blocks / SkillJuror | 已做「渐进披露 vs 全量加载」的对照；本 SOP 不预设层级，只要求控制知识量 |
| LOTUS / DocETL / Abacus | 语义算子/管线优化；本 SOP 关心「操作之间的数据语义可检查」，不是管线重写 |
| COBRA-Skills | 有限预算下分配技能评估的更新基线，比较成本时不能只对无技能 |

关键差异主张：让操作之间的**数据语义可检查**——执行前绑定任务参数、执行后输出可检查状态摘要、失败后判定是参数/数据语义/执行代码/技能知识哪一层的问题。

## 引用源

- AgenticDataBench 本地仓库：`docs/research/IDEA_ASSESSMENT_2026-09-19.md`、`generator/README.md`、`generator/data_classes.py`、`testbed/SKILLOPT_HISTORY_PATCH.md`、`testbed/SkillOpt_两种优化方式分析.md`、`testbed/opt_common.py`
- 轨迹 schema 与样例：`testbed/traindata/_skillopt_*/rollout*/predictions/*/trajectory.json`、`agent_trace.txt`、`results.jsonl`
- 相关论文：LOTUS (arXiv:2407.11418)、AgenticDataBench (arXiv:2607.01647)、SkillOpt (arXiv:2605.23904)、SemPipes (arXiv:2602.05134)、EvoDS (arXiv:2606.03841)、Skill Blocks (arXiv:2608.14943)、SkillJuror (arXiv:2606.11543)、COBRA-Skills (arXiv:2609.11682)
