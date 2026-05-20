---
name: agentsop-cost-tiered-models
version: 0.1.0
description: >-
  Split a multi-call LM workflow by cognitive load, not by accuracy: let one strong model
  make the few reasoning decisions and a cheap model do the many mechanical executions
  (Aider architect+editor, DSPy optimizer-LM vs task-LM, vLLM speculative draft+target,
  LangGraph supervisor+worker are the same shape). Use when designing or cost-optimizing a
  pipeline that calls an LM many times, when deciding which steps need a strong reasoner vs
  a cheap executor, or when adding an escalation valve for when the cheap tier degrades.
  Search keywords: reduce LLM cost, cheaper model, lower token cost, model cascade, route to
  cheap model, strong model plus cheap model, LLM cost optimization.
domain: cost-aware model/role splitting in multi-call LM workflows
dated: 2026-05
audience: coder-agents and engineers designing multi-call LM pipelines
sources:
  - https://aider.chat/2024/09/26/architect.html
  - https://github.com/stanfordnlp/dspy/issues/1596
  - https://docs.vllm.ai/en/latest/features/speculative_decoding/
  - https://langchain-ai.github.io/langgraph/concepts/multi_agent/
---

# Cost-aware Model/Role Split — "强推理者 + 廉价执行者"

> 一句话：一条多次调用 LM 的工作流里，**少数调用需要推理，多数调用是机械执行**。让一个强模型做决策，让一个便宜模型干活——按认知负荷拆分，不是按"哪个更准"拆分。

> **统一声明**：Phase B 发现这个模式在 4 个 SOP 里以 4 个名字反复出现——DSPy 的 optimizer-LM vs task-LM、Aider 的 architect+editor、vLLM 的 speculative draft+target、LangGraph 的 supervisor+worker。它们是**同一个形状**。本技能把这个形状抽出来，命名为 cost-tiered models。详见 §7 跨框架对照。

---

## 1. 何时激活 (When to activate)

任一情形成立时激活本技能：

- 工作流会**对 LM 发起多次调用**，且这些调用**认知负荷不均**——有的需要规划/推理/判断，有的只是改写、抽取、格式化、应用一个已定好的决定。
- 你正在为一条 LM 流水线**选模型**，并且默认想"全程用同一个最强模型"——这是本技能要挑战的反射。
- 你有一个**强 reasoner 但执行差**的模型（典型：o1/o3 推理强但编辑代码格式脏），需要给它配一个干净的执行者。
- 你在**成本/延迟压力**下，想知道哪些调用可以降级到便宜模型而不掉质量。
- 你在设计 **agent 编排**（supervisor 路由 + worker 执行），或 **推理加速**（speculative draft + target verify），意识到这和上面是同一个决策。

**不应激活**（见 §6）：

- 单次调用、无内部步骤的工作流——没有可拆分的角色。
- 微型工作流（2–3 次调用、总成本可忽略）——拆分的协调开销 > 节省。
- 质量是唯一目标、成本无关紧要的场景——直接全程用最强模型。

---

## 2. 核心心智模型 (Core Mental Model)

**按认知负荷拆分：一个强模型做决策，一个便宜模型执行——而且绝大多数调用是执行。**

### 2.1 两层，不是一层

绝大多数团队的默认是"全程一个模型"。这把两种本质不同的工作混在了一个价位上：

| 层 | 工作性质 | 调用频率 | 模型要求 | 选谁 |
|---|---|---|---|---|
| **Tier-S（决策层）** | 规划、推理、路由、判断、提案 | **少**（每任务 1–N 次） | 推理强；执行干不干净不重要 | 最强 reasoner |
| **Tier-E（执行层）** | 改写、抽取、格式化、应用决定、生成草稿 | **多**（占总调用 80%+） | 听话、格式干净、便宜、快 | 便宜/快模型 |

关键洞察：**成本由调用次数主导，调用次数由执行层主导**。所以把执行层降级到便宜模型，省下大部分成本，却几乎不碰决策质量——因为决策层调用次数少，仍然用最强模型。

### 2.2 为什么"强 reasoner 执行差"是常态而非例外

推理能力和指令依从（产出干净的 diff/JSON/格式）是两种不同的能力，不总同向。Aider 的 Polyglot 数据是最干净的证据：o1-preview **单独**跑 79.7%，但它当 architect 配一个便宜 editor 后，整体到 82.7%–85%——**两次便宜的专门调用胜过一次又贵又全能的调用** [aider.chat/2024/09/26/architect.html]。强模型负责"想"，便宜模型负责"把想法落成格式正确的编辑"。

### 2.3 三种省钱方向，同一个形状

- **省钱**：执行层从 GPT-4o 降到 mini/Llama，决策层不动。
- **提质**：把"想"和"做"解耦，强模型不再被格式约束分心（JSON-wrapping 实测会降低模型推理能力 [aider.chat/2024/08/14]）。
- **提速**：便宜模型先草拟（draft），强模型只做验证（vLLM speculative decoding 的本质就是这个 [docs.vllm.ai speculative_decoding]）。

三者都是"强决策 + 廉价执行"的拆分，只是优化目标不同。

### 2.4 升级阀门（escalation valve）

拆分不是单向的。便宜执行者会在某些输入上**失败或退化**（格式错、跑题、质量塌）。正确的设计带一个**回退-升级阀门**：检测到执行层失败 → 把这一步升级到强模型重试。便宜执行者覆盖 80–95% 的常规输入，强模型兜底长尾。这把"省钱"和"不掉质量"同时拿到。

---

## 3. SOP 工作流 (SOP Workflow)

```
[Step 0] 列出工作流里所有 LM 调用
   └─ 对每次调用记：它在"想"还是在"做"？预期调用频率？

[Step 1] 给每次调用打认知负荷标签
   ├─ 高推理（规划/路由/判断/提案/纠错）        → 候选 Tier-S
   └─ 机械执行（改写/抽取/格式化/应用决定/草稿）  → 候选 Tier-E
   规则：把"需要全局判断 / 一旦错代价高 / 频率低"的归 Tier-S，
        其余尽量下沉到 Tier-E。

[Step 2] 分配模型层
   ├─ Tier-S → 你能负担的最强 reasoner（少量调用，单价高无所谓）
   ├─ Tier-E → 便宜/快模型（大量调用，单价主导总成本）
   └─ 给 Tier-E 选最适配它的输出格式（弱模型用 whole/简单 schema，
      不要逼它产 token 高效但易错的 diff）。

[Step 3] 度量质量 delta（必须做，否则是赌博）
   ├─ baseline：全程强模型的质量分 + 成本
   ├─ split：S+E 拆分后的质量分 + 成本
   ├─ 看 (质量 delta, 成本 delta) 这一对，不要只看其一
   └─ 在你自己的真实任务上量，不要信别人 benchmark 的绝对数

[Step 4] 装升级阀门
   ├─ 定义"执行层失败"的可检测信号（格式不合法 / 测试不过 /
   │   schema 校验失败 / 自评分低）
   ├─ 失败 → 升级到 Tier-S 重试这一步（或换执行格式重试）
   └─ 记录升级率：若 >30%，说明这步本就属于 Tier-S，重新归类

[Step 5] 调拆分点（tune the split）
   ├─ 升级率高 / 质量掉太多 → 把更多步上移到 Tier-S
   ├─ 升级率近 0 / 质量持平 → 把更多步下沉到 Tier-E，再省一截
   └─ 拆分点是个滑块，不是开关；按 Step 3 的数往返调
```

---

## 4. 操作模型 (Operation Model)

### OP-1: Role-tier mapping（角色→层映射）

- **Trigger**: 一条多次调用 LM 的工作流，想知道哪些调用降级安全。
- **Action**: 对每次调用问"它在想还是在做"。想（规划/路由/判断/提案）→ Tier-S；做（改写/抽取/格式化/应用）→ Tier-E。Tier-S 配最强 reasoner，Tier-E 配便宜模型。
- **Output**: 一张 (调用 → 层 → 模型) 映射表 + 预期成本结构（哪层主导成本）。
- **Evidence**: 四框架共有形状 §7；DSPy 文档明确"决定哪个模型优化 vs 哪个是 task model——它们可以不同" [dspy SKILL §3 Stage]。

### OP-2: The architect+editor recipe（架构师+编辑者配方）

- **Trigger**: 你有强 reasoner 但它执行（产出干净 diff/格式）差，或想给任何"推理后要落地"的步骤解耦。
- **Action**: 强模型当 architect 只输出**自然语言方案**（不写最终格式）；便宜模型当 editor 把方案落成格式正确的产物。给 editor 用瘦提示 + 它擅长的格式（Aider 自动切 `editor-diff`/`editor-whole`）。
- **Output**: 两步管线：propose（强、自由文本）→ apply（廉价、严格格式）。
- **Evidence**: Aider Polyglot Pass@2——o1-preview 单跑 **79.7%**，o1-preview+Sonnet **82.7%**，o1-preview+o1-mini(whole) **85%**；连 Sonnet 自配 editor 也从 77.4%→**80.5%** [aider.chat/2024/09/26/architect.html]。

### OP-3: Fallback-escalation（回退-升级阀门）

- **Trigger**: 便宜执行者在部分输入上失败/退化。
- **Action**: 定义可检测的失败信号（格式非法、测试失败、schema 不过、自评低）→ 命中则把该步升级到 Tier-S 重试。记录升级率。
- **Output**: 带升级阀门的执行层；升级率指标。
- **Evidence**: vLLM speculative decoding 是硬件层同构——draft 提议、target 验证，验证失败就用 target 的真分布纠正 [docs.vllm.ai speculative_decoding]；Aider 编辑错误时升级模型/换格式重试 [aider.chat/troubleshooting/edit-errors]。

### OP-4: Format-by-tier（按层选输出格式）

- **Trigger**: 给 Tier-E 选输出格式。
- **Action**: 别让便宜模型背强模型的负担。弱执行者用解析最稳的格式（whole 文件 / 简单 schema），不要逼它产 token 高效但字节敏感的 diff。**绝不**把代码/复杂产物包进 JSON tool-call。
- **Output**: 每个 Tier-E 调用的格式选择。
- **Evidence**: "所有模型在 JSON 包裹下基准都变差，包括 Sonnet" [aider.chat/2024/08/14/code-in-json.html]；Aider 已为各模型选好默认编辑格式。

### OP-5: Cheap-optimizer / expensive-task（廉价优化器 + 昂贵任务模型）

- **Trigger**: 你在自动调提示/搜索/编排（meta 层），而被服务的 task 调用很贵。
- **Action**: meta 层（优化、提案、搜索）用便宜模型；被优化的 task 调用才用贵模型。注意这是 §2 的**镜像**——这里"决策/搜索"反而可以便宜，"执行任务"才贵。判据始终是：**哪类调用的质量直接进最终产物，哪类只是脚手架**。脚手架降级。
- **Output**: optimizer-LM（便宜）vs task-LM（贵）的分配。
- **Evidence**: DSPy 社区实测 gpt-4o-mini 当 optimizer-LM 优化 gpt-4o 的 task-LM，质量持平、成本大降 [github.com/stanfordnlp/dspy issue #1596]。

### OP-6: Distill-after-split（拆分后蒸馏）

- **Trigger**: 拆分稳定后，想把执行层进一步压成更便宜的本地小模型。
- **Action**: 用强模型/已优化管线当 teacher，蒸馏出 student 小模型接管 Tier-E。
- **Output**: 微调后的小执行模型 + 强决策模型的组合。
- **Evidence**: DSPy `BootstrapFinetune(student=Llama-3.2-1B, teacher=gpt-4o-mini)`，先在大模型优化再蒸馏 [dspy SKILL §4.1]。**警告**：换 task-LM 家族必须重编译/重测，大模型的 verbose CoT demo 会让小模型"鹦鹉学舌长度而无推理" [dspy SKILL Case B]。

### OP-7: Supervisor/worker tiering（编排层分层）

- **Trigger**: 多 agent 编排，一个路由/协调 agent + 多个执行 sub-agent。
- **Action**: supervisor（决策：路由、综合、决定下一步）用强模型；worker（执行某个具体子任务）用便宜模型。注意 supervisor 因为要"翻译" worker 输出会**多花 token**，把这笔翻译成本算进总账。
- **Output**: supervisor=Tier-S，workers=Tier-E 的编排。
- **Evidence**: LangGraph supervisor 模式"始终比 swarm 多用 token，因为要翻译 sub-agent 输出" [langgraph SKILL Case 2]。

---

## 5. 困境决策案例 (Dilemma Cases)

### 案例 1 — "Aider architect 模式值得花这个钱吗？"

**触发**：硬推理编码任务；你有 o1/o3（强 reasoner，但单独跑编辑脏）。开 architect 等于把每个任务从 1 次调用变 2 次，token 成本接近翻倍。

**张力**：
- 拆分**确实提质**：o1-preview 79.7% → o1-preview+Sonnet 82.7% → o1-preview+o1-mini 85% [aider.chat/2024/09/26/architect.html]。
- 但 +3pp 到 +5pp 是否值翻倍 token，取决于任务价值。例行编辑里这点提升不值；难题/高价值改动里很值。
- 而且 reasoner 本来执行就干净的模型（GPT-4o、Sonnet），开 architect 收益小、纯亏钱。

**决策规则**：

| 情况 | 建议 |
|---|---|
| reasoner 执行也干净（GPT-4o / Sonnet 单跑） | **不开** architect，单跑省钱省时 |
| reasoner 执行差（o1/o3 单跑格式脏） | **开** architect：强 reasoner + 便宜干净 editor → +3pp~+5pp |
| 追 SOTA、能等慢 | o1-preview + o1-mini(whole) → 85%（"probably not practical for interactive use"） |
| 例行/低价值编辑 | 单跑，别拆 |

**可提取操作**：拆分的收益 = (质量 delta) × (任务价值) − (额外调用成本)。reasoner 执行已干净时 delta≈0，不拆；reasoner 执行差时 delta 大，拆。

**Evidence**: [aider.chat/2024/09/26/architect.html]。

### 案例 2 — "便宜执行者什么时候退化到该升级？"

**触发**：Tier-E 用便宜模型干活，部分输入上质量明显塌（代码改错、抽取漏字段、格式反复非法），但多数输入仍正常。是把整层换回强模型，还是只升级失败的那部分？

**张力**：
- 整层升级回强模型 → 质量稳但成本回到原点，拆分白做。
- 死守便宜模型 → 长尾输入持续产坏结果。
- 真正的答案几乎总是中间：**便宜模型覆盖常规，强模型兜底长尾**。

**决策规则**：
1. 给 Tier-E 装可检测失败信号：格式校验、测试退出码、schema 校验、自评分阈值。
2. 失败命中 → 升级该步到 Tier-S 重试（或先换更稳的执行格式重试一次，再升级）。
3. 持续记**升级率**：
   - 升级率 < 10% → 拆分健康，保持。
   - 升级率 10–30% → 可接受，但盯着；考虑给 Tier-E 换更强一点的便宜模型。
   - 升级率 > 30% → 这步**本就属于 Tier-S**，重新归类，别在执行层硬扛。
4. 别用"概率全升级"求保险——那等于退回单层。

**可提取操作**：升级率是拆分点是否放对的体温计。它不是要清零，而是要稳定在低位；持续高升级率 = 拆分点划错了。

**Evidence**: vLLM speculative——高 QPS 下 draft 被频繁拒、speculation 反而偷算力，此时该关 [docs.vllm.ai speculative_decoding]，同构于"升级率太高就别拆"；Aider 编辑错误升级模型/换格式 [aider.chat/troubleshooting/edit-errors]。

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### 反模式 1：One-model-for-everything（全程一个模型）

最常见的默认值，也是本技能要挑战的反射。它把少量高价值决策调用和大量机械执行调用按同一个价位收费——要么为执行层overpay（全用最强），要么为决策层欠配（全用便宜，难题翻车）。先按 §2.1 分层，再选模型。

### 反模式 2：Over-splitting tiny workflows（微型工作流过度拆分）

2–3 次调用、总成本可忽略的工作流，拆成 S+E 两层引入的协调/翻译开销（supervisor 翻译 worker 输出要多花 token [langgraph Case 2]；architect 多一次往返）经常**超过**节省。拆分有固定成本，只在调用次数多、执行层占大头时才回本。

### 反模式 3：不量 delta 就拆（赌博式拆分）

凭"便宜模型应该够用"的直觉降级，不在自己任务上量 (质量 delta, 成本 delta)。别人 benchmark 的绝对数不可移植——Aider 的 85% 是 Polyglot 上特定模型对的结果，不是你的任务的保证。必须按 §3 Step 3 自测。

### 反模式 4：给便宜执行者背强模型的格式负担

逼弱 editor 产 token 高效但字节敏感的 diff，或把代码包进 JSON tool-call。弱模型在这些格式上合规率塌。便宜执行者要配**它擅长**的格式（whole / 简单 schema），见 OP-4。

### 反模式 5：拆了但没有升级阀门

便宜执行者必然有长尾失败。没有失败检测 + 升级回退，坏输出直接进产物。拆分必须连阀门一起设计（OP-3），否则省的钱用 debug 坏结果赔回去。

### 反模式 6：拆分点当开关而非滑块

"要么全强要么全便宜"是把连续的拆分点退化成二元开关。正确做法是按升级率/质量 delta 往返微调哪些步在哪层（§3 Step 5）。

### 反模式 7：换了 task 模型不重新校准

把为大模型调好的拆分/提示原样套到小模型上。DSPy 明示"为 GPT-4 优化的复杂管线在 Llama-3-8B 上通常崩" [dspy Case B]。换执行层模型家族 = 重测拆分，不是免费迁移。

### 边界

本技能**适用**当：工作流多次调用 LM；调用间认知负荷不均；成本/延迟有约束；你能在自己任务上量质量 delta。

本技能**不适用**当：单次调用、无内部步骤（无角色可拆）；微型工作流（拆分开销 > 节省，见反模式 2）；质量是唯一目标且预算无限（直接全程最强模型）；本质是"选哪个推理引擎"而非"如何分层用模型"（那是 `llm-engine-selection` 技能）。

---

## 7. 跨框架对照 (Cross-framework Comparison)

**同一个形状，四个名字。** 每一行都是"强模型决策 + 廉价模型执行 + 失败时回退/纠正"。

| 框架 | 这个模式叫什么 | Tier-S（强/决策） | Tier-E（廉价/执行） | 升级/纠正阀门 | 公开证据 |
|---|---|---|---|---|---|
| **Aider** | architect + editor | architect 模型（o1-preview）出自然语言方案 | editor 模型（Sonnet/o1-mini）落成 diff | 编辑错误→升级模型/换格式重试 | Polyglot 79.7%→82.7%→**85%** [aider.chat/2024/09/26] |
| **DSPy** | optimizer-LM vs task-LM | 这里是**镜像**：被服务的 task-LM（gpt-4o）才贵；脚手架可降级 | optimizer-LM（gpt-4o-mini）跑提示搜索/提案 | 优化平台→重编译/换 LM 家族 | mini 优化器 + 4o 任务，质量持平成本大降 [dspy #1596] |
| **LangGraph** | supervisor + worker | supervisor 路由/综合/决定下一步 | worker sub-agent 执行具体子任务 | supervisor 重新路由；swarm 互相 handoff | supervisor 比 swarm 多花 token（翻译开销）[langgraph Case 2] |
| **vLLM** | speculative draft + target | target 模型验证、给真分布 | draft 模型（小/EAGLE/n-gram）先草拟 token | 验证拒绝→用 target 分布纠正；高 QPS 关闭 | 最高 ~2.5× 解码加速 [developers.redhat.com 2025 eagle3] |

### 7.1 三个共同结构

1. **频率不对称**：执行层调用远多于决策层；成本由执行层主导，所以降级执行层最划算。
2. **能力解耦**：推理强 ≠ 执行/产出干净。把两者分开，各用最适配的模型（Aider 的 79.7%→85% 是直接证据）。
3. **带阀门**：四个框架都有失败回退——Aider 升级模型、DSPy 重编译、LangGraph 重路由、vLLM 验证拒绝。拆分不是单向降级，是"廉价覆盖常规 + 强模型兜底长尾"。

### 7.2 注意 DSPy 是镜像

DSPy 行里便宜的是 optimizer（脚手架/meta 层），贵的是 task（最终产物）。这不矛盾——判据始终是 **§2 那一条**：质量直接进最终产物的调用用强模型，只是脚手架的调用降级。在 Aider/LangGraph/vLLM 里执行层是产物的一部分但机械，所以降级；在 DSPy 里 optimizer 不进产物，所以降级。同一个原则，不同的"哪类是脚手架"。

### 7.3 选型口诀

> 先问每次 LM 调用：**它的输出是最终产物，还是脚手架/草稿/可被验证的提议？** 是产物且需判断 → Tier-S。是草稿/脚手架/可验证提议 → Tier-E + 升级阀门。

---

## 引用源 / References (参考)

- aider.chat/2024/09/26/architect.html （architect+editor，Polyglot 79.7%→82.7%→85%）
- aider.chat/2024/08/14/code-in-json.html （JSON 包裹劣化所有模型）
- aider.chat/docs/troubleshooting/edit-errors.html （编辑错误升级/换格式）
- github.com/stanfordnlp/dspy/issues/1596 （cheap optimizer-LM + expensive task-LM 质量持平）
- dspy.ai/api/optimizers/BootstrapFinetune/ （拆分后蒸馏 student/teacher）
- docs.vllm.ai/en/latest/features/speculative_decoding/ （draft+target，高 QPS 关闭）
- developers.redhat.com/articles/2025/07/01/fly-eagle3-fly （EAGLE-3 最高 ~2.5× 加速）
- langchain-ai.github.io/langgraph/concepts/multi_agent/ （supervisor/worker；翻译 token 开销）
- 来源 SOP：dspy-sop-skill / aider-sop-skill / langgraph-sop-skill / vllm-sop-skill（本仓 output/）
