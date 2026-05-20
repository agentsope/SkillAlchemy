# Skill Grammar — 怎么写一个好 Skill

从 skills.sh 大量公开 skill 中提炼的写作方法论。Skill Compilation agent 在编译阶段加载此文件。

**数据验证：** 基于 skills.sh 真实语料，含质量评分过滤。

### 语料统计快照（全量样本）

| 维度 | 发现 |
|------|------|
| 触发模式 | keyword-match 75% / hybrid 16% / context-match 8% / explicit-call 1% |
| SOP 类型 | chain-of-steps 71% / template-fill 22% / reference 7% |
| 篇幅 | <100行 27% / 100-300行 45% / 300-800行 26% / 800+行 1% |
| description 含触发 | 59% 有 / 41% 没有 ⚠️ |

### 质量加权快照（Top 60%, 111 skills, score ≥ 9/13）

| 维度 | 全部 | Top 60% | 变化 |
|------|------|---------|------|
| keyword-match | 75% | 77% | → |
| hybrid trigger | 16% | **21%** | ↑ 好 skill 更多用混合触发 |
| context-match | 8% | **2%** | ↓↓ 纯 context 触发是弱信号 |
| chain-of-steps | 71% | **79%** | ↑ 具体步骤 = 质量 |
| reference 型 | 7% | **1%** | ↓↓↓ 纯参考型几乎全是低质量 |
| <100 行 | 27% | **9%** | ↓↓↓ 太薄的 skill 被大量过滤 |
| 100-300 行 | 45% | **54%** | ↑ 最佳篇幅区间 |
| 300-800 行 | 26% | **37%** | ↑ 优质 skill 平均更长 |

### 好 skill 的模式关联（Top 60% 中高频共现）

| 关联模式 | 频次 | 解读 |
|----------|:--:|------|
| chain-of-steps + 诊断型 | 74% | 好 skill 用步骤链做诊断 |
| keyword-match + chain-of-steps | 63% | 赢家组合：关键词触发 + 步骤化执行 |
| chain-of-steps + 验证型 | 56% | 诊断完了要验证 |
| chain-of-steps + 生成型 | 46% | 步骤化生成是第二常见 |
| chain-of-steps + 对比型 | 37% | |

---

## 1. SKILL.md 格式规范

### Frontmatter（YAML）

```yaml
---
name: skill-name                    # 1-64字符，小写字母+数字+连字符
description: >-                     # 1-1024字符，功能+触发条件
  What this skill does. When to use it.
version: 0.1.0
---
```

**description 是唯一的触发机制**，必须同时包含：
- 功能描述（skill 做什么）
- 触发条件（什么时候用）

```
✅ 好: "Extracts text and tables from PDF files, fills PDF forms, and merges
       multiple PDFs. Use when working with PDF documents or when the user
       mentions PDFs, forms, or document extraction."

❌ 差: "Helps with PDFs."
```

### Markdown 正文

SKILL.md body 在 skill 被触发时加载。建议 <5000 tokens。

---

## 2. 触发模式（5 种）

### 2.1 keyword-match
最常用。用户在对话中说了特定词就触发。
- **写法**：description 里埋 3-6 个触发关键词
- **适用**：工具类 skill、领域知识 skill
- **示例**：`security-audit` → "Use when security audit, vulnerability scan, OWASP, dependency check"

### 2.2 context-match
根据工作目录或文件类型自动触发。
- **写法**：description 里描述上下文条件
- **适用**：项目级 skill（Docker、Git、CI/CD）
- **示例**：`docker-development` → "Use when working with Dockerfiles, docker-compose, or containerization"

### 2.3 explicit-call
用户显式调用 `/skill-name` 或 `@skill-name`。
- **写法**：name 就是触发词，description 解释功能
- **适用**：需要明确意图的 skill（安全性要求高的操作）
- **示例**：`security-review` → 用户主动说 "security review"

### 2.4 hybrid
keyword + context 组合。description 里同时埋关键词和上下文。
- **写法**：先写关键词，再写场景
- **适用**：复杂触发条件
- **示例**：`deploy-check` → "Use before git push when deploy, release, or production is mentioned"

### 2.5 always-on
每次对话都加载。用于元技能或规则注入。
- **写法**：description 极宽泛，或设为 agent-rules
- **适用**：AGENTS.md 生成、全局规则
- **警告**：容易滥用——只在确实每次都需要时用

---

## 3. SOP 模板（4 种）

### 3.1 chain-of-steps
顺序执行步骤。Step 1→2→3→4→5。
```
## Instructions
### Step 1: [动作]
具体做什么。用什么工具。期望什么输出。

### Step 2: [动作]
...
```
- **适用**：pipeline 式操作（PDF 处理、数据清洗、部署）
- **关键规则**：
  - 每步一个可验证的输出
  - 步骤间有依赖关系的标注
  - 失败时跳到哪一步

### 3.2 model-card-driven
每个概念一张操作卡片，运行时按需 Read。
```
## Core Models

| # | Model | When to Use | Key Action |
|---|-------|-------------|------------|
| H1 | **模型名** | 触发条件 | 核心操作 |

Full cards in `references/sop_models.md`.
```
- **适用**：复杂决策 skill（多个独立概念/框架）
- **关键规则**：
  - 每张卡片 8 字段：When-to-use / Inputs / Action / Output / Evidence / Failure Mode / Boundary / Confidence
  - SKILL.md 只放摘要表，卡片在 references/
  - 运行时协议步骤 1：Read sop_models.md 匹配模型

### 3.3 decision-tree
if-then 分支结构。根据用户输入判断走哪条路径。
```
## Decision Flow

1. Does the user have [condition A]?
   → Yes: Go to [path A]
   → No: Continue to 2.

2. Is [condition B] present?
   → Yes: [action B]
   → No: [default action]
```
- **适用**：诊断类 skill（bug 排查、安全审计、代码审查）
- **关键规则**：
  - 每个分支有明确的判断条件
  - 叶节点是一个具体操作，不是另一个判断
  - 有 default/fallback 分支

### 3.4 template-fill
用户提供信息，skill 填入模板。
```
## How to Use

1. Collect: [field1], [field2], [field3]
2. Validate: check [field1] against [rule]
3. Fill: insert into template at `templates/[name].md`
4. Output: rendered [output_type]
```
- **适用**：文档生成、报告填写、PR 模板
- **关键规则**：
  - 必填字段 vs 可选字段分清楚
  - 每个字段有验证规则
  - 模板路径明确标注

---

## 4. 输出约束（5 种）

### 4.1 analysis-report
先结论，再展开。用自然段落。
```
先给一句话结论，再展开。
不把整个模型卡片贴出来。
```
- **禁止词**：「根据框架分析...」「按照模型卡片...」「让我来系统分析...」
- **回答完就停**，不问「需要我进一步展开吗」

### 4.2 executable-code
代码块 + 简短解释。
```
Code first, explanation after.
One code block per step.
```

### 4.3 conversational
第一人称对话。persona 模式。
```
不分点论述，不列一二三四。
回应第一句就是答案，不是「让我来分析一下」。
```

### 4.4 checklist-verify
逐项检查，每项标注 pass/fail。
```
## Verification Checklist
- [ ] Item 1 — check X against Y
- [ ] Item 2 — verify Z is present
```

### 4.5 mixed
根据问题类型切换输出模式。需要 `## Output Modes` 表格定义。

---

## 5. 边界模式（6 类）

### 5.1 source-bound
限定信息来源。
```
只基于公开文档/官方仓库/指定出处。不引用未验证的论坛帖子。
```

### 5.2 version-bound
版本/时间截止。
```
信息截止 2026 年 5 月。不覆盖后续版本变更。
```

### 5.3 capability-bound
明确能做/不能做什么。
```
能：分析 SQL 查询性能。不能：修改生产数据库。
```

### 5.4 scope-bound
限定适用领域。
```
适用于 Web 应用安全审计。不适用于移动端或 IoT。
```

### 5.5 legal-bound
免责/合规声明。
```
不提供法律建议。仅供参考，需要专业审计验证。
```

### 5.6 confidence-bound
标注不确定度。
```
高置信度：基于官方文档。低置信度：基于社区讨论，需验证。
```

---

## 6. Persona 模式专项

### 6.1 必选章节（8 个）

| # | 章节 | 作用 | 建议行数 |
|---|------|------|---------|
| 1 | `## 角色扮演规则` | 输出格式最强约束 | 6-10 |
| 2 | `## 身份` | 3-5 句第一人称握手 | 3-5 |
| 3 | `## 我看世界的方式` | 3-5 个心智模型，每段 ≤5 行 | 15-25 |
| 4 | `## 我怎么说话` | 句式/词汇/节奏/幽默/确定性 + 绝不会说 + 标志句式 | 10-15 |
| 5 | `## 决策启发式` | 3-5 条 if-X-then-Y 规则 | 5-10 |
| 6 | `## 运行时协议` | 5 步 SOP 驱动流程 | 15-20 |
| 7 | `## 边界` | ~5 行，不能代表真人 | 4-6 |
| 8 | `## 参考` | 指针到 sop_models.md + research_notes.md | 1-2 |

### 6.2 「我绝不会说」—— 辨识度关键

比正向描述更能建立辨识度。2-3 句这个人永远不会说的话。

```
✅ 好:
芒格绝不会说"根据我的经验"——他说"我见过太多人在这上面栽跟头"。
乔布斯绝不会说"这个方向也有道理"——他说"这是 shit"或"这是 amazing"。

❌ 差:
"我不会说不专业的话"——太泛，没有辨识度。
```

### 6.3 「我的标志句式」—— 一眼认出

1 句标志性表达，放在「我怎么说话」末尾。

```
费曼: "如果你不能给大一新生讲清楚，说明你没真懂。"
乔布斯: "Stop，你的问题本身就有问题。"
```

### 6.4 决策启发式 —— falsifiable

每条必须是可证伪的规则。

```
❌ 不合格: "Think long-term." → 不可证伪，什么场景都适用
✅ 合格: "如果一个问题在三分钟内想不清楚，放进 Too Hard 筐，跳过。" → 可证伪
```

---

## 7. Tool 模式专项

### 7.1 必选章节（7 个）

| # | 章节 | 关键 |
|---|------|------|
| 1 | `## Activation Rules` | 触发 + 不触发的具体例子各 4-5 个 |
| 2 | `## Agentic Protocol` | 可执行步骤，不是「考虑 X」而是「做 X 然后 Y」 |
| 3 | `## Core Operation Models` | H1-Hn + M1-Mn 摘要表，完整卡片在 references/ |
| 4 | `## Output Style` | 先结论后展开、禁词列表、不用 markdown 表格 |
| 5 | `## Output Modes` | 4-7 种模式表格 |
| 6 | `## Boundary Rules` | 7-8 条 |
| 7 | `## References` | 指针表 |

### 7.2 Output Style 禁词

Tool 模式最常犯的错误是「套话」。

```
禁止词:
- 「根据框架分析...」
- 「按照模型卡片...」
- 「让我来系统分析...」
- 「需要我进一步展开吗」

引用来源时说「PG 在 2012 年文章里指出...」
不说「根据 references/sop_models.md 的 H1 模型卡片...」
```

---

## 8. 反模式清单（7 个）

| # | 反模式 | 后果 | 修正 |
|---|--------|------|------|
| 1 | 触发条件太宽 | 误触发，每个对话都激活 | 缩小关键词，加 context 约束 |
| 2 | description 只写功能不写触发 | 永远不会被调用 | 加 "Use when..." |
| 3 | 没有边界声明 | 用户预期失控 | 加 Boundary Rules / 边界 |
| 4 | SOP 太模糊（"考虑 X"） | 不可执行 | 改成 "做 X 然后 Y" |
| 5 | SKILL.md 太长（>8000 tokens） | 每次触发都加载，浪费 context | 移内容到 references/ |
| 6 | 引用不存在的文件 | 运行时 Read 失败 | 确认所有路径存在 |
| 7 | 虚构引语（persona） | 失去可信度 | 只引用公开可验证的引语 |
| 8 | **纯参考型 skill**（无具体步骤） | 数据：reference 型在好 skill 中仅 1%，全集中差 skill 中。没有可执行步骤的 skill 几乎没用 | 改成 chain-of-steps 或 model-card-driven |
| 9 | **<100 行太薄** | 数据：<100 行在好 skill 中仅 9%，全集中差 skill 中（27%→9%）| 至少 100 行，目标 100-300 |

---

## 9. 数据背书的质量信号

基于 大量 skills 的质量评分分析（≥9/13 分 = 好 skill），以下是好 skill 的量化特征：

### 如果只能做 3 件事

1. **写具体步骤，不要写参考文档。** chain-of-steps 在好 skill 中占 79%（全部仅 71%），reference 型几乎从好 skill 中消失（7%→1%）。
2. **用 hybrid trigger，不要只用 context。** hybrid 在好 skill 中从 16% 升到 21%，context-match 从 8% 降到 2%。
3. **控制在 100-800 行。** <100 行被质量过滤器大量排除（27%→9%），100-300 行是最稳区间（45%→54%）。

### 赢家组合

好 skill 最常见的模式组合（Top 60% 中）：

```
keyword-match trigger
  + chain-of-steps SOP
  + 诊断型操作
  + 验证型操作
  + 100-300 行篇幅
  + 有边界声明
```

这个组合覆盖了 63% 的好 skill。

### 质量评分的 13 分

| 维度 | 分值 | 检查 |
|------|:--:|------|
| frontmatter 有 name | 1 | 基本 |
| frontmatter 有 description | 1 | 基本 |
| description 含触发词 | 2 | **加权** — 少了这个 skill 不会被调用 |
| description 具体（>80 字符） | 1 | |
| ≥3 个 section | 1 | |
| 有边界声明 | 2 | **加权** — 用户预期管理的核心 |
| ≥5 个具体步骤 | 2 | **加权** — 可执行性的核心 |
| 有示例 section | 1 | |
| 100-400 行篇幅 | 1 | |
| 有参考/相关 section | 1 | |
| <30 行（扣分） | -2 | 太薄是硬伤 |

**好 skill 的分水岭：≥9 分。** corpus 中 约 60%达标。

---

## 10. 三级质量金字塔

基于 大量 skills 的质量评分分析：

### 精英层（Top 10%, score ≥ 11, 18 skills）

**100% 命中率特征：**
- 100% 用 chain-of-steps（无一例外）
- 100% 有具体步骤（≥5 个可执行步骤）
- 100% description 含触发词 + 具体描述（>80 字符）
- 94% 有边界声明
- 89% 同时做诊断 + 验证

**精英模板（可直接复用）：**

```
触发: keyword-match 或 hybrid
SOP: chain-of-steps
操作: 诊断 + 验证（缺一不可）
篇幅: 200-350 行
必备: 边界声明 + 具体步骤 + 触发描述 + 多 section
加分: 示例 section + 参考 section
```

**精英 skill 示例：** `systematic-debugging`, `subagent-driven-development`, `dispatching-parallel-agents`, `finishing-a-development-branch`, `seo-audit`, `verification-before-completion`

### 中间层（Top 60%, score ≥ 9, 111 skills）

- 79% chain-of-steps, 20% template-fill
- hybrid trigger 比全量多 5pp
- 100-300 行占 54%

### 底层（Bottom 40%, score < 9, 75 skills）

- 纯参考型（reference）几乎全集中在这里
- 平均 54 行（精英层 273 行，差距 5x）
- 典型弱点：too_thin + too_few_sections + description_too_vague

### 一句话总结

> 如果你想写一个好 skill：chain-of-steps + 诊断 + 验证 + 边界声明 + 200-350 行 + 描述具体含触发词。如果你想写一个精英 skill：上面全做，再加示例和参考。

---

## 11. 质量检查清单

编译完成后自检：

### 结构
- [ ] frontmatter: name + description 到位
- [ ] description 包含功能 + 触发条件
- [ ] 所有必选 section 存在
- [ ] SKILL.md body <5000 tokens

### 可执行性
- [ ] SOP 每步有具体操作（不是「考虑 X」）
- [ ] 每步有可验证的输出
- [ ] 运行时协议可执行（Read → match → act → verify）

### 辨识度（persona）
- [ ] 「我绝不会说」2-3 条具体禁止项
- [ ] 「我的标志句式」1 条
- [ ] 决策启发式每条可证伪
- [ ] 100 字内可辨识

### 边界
- [ ] 边界声明清晰（做了什么 + 不能做什么）
- [ ] 信息截止日期
- [ ] 置信度标注

### 证据
- [ ] 关键声明有来源
- [ ] 引用格式自然（不说「根据 references/sop_models.md 的 H1」）
- [ ] 无虚构引语
