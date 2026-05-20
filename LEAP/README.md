<div align="center">

# LEAP (Launch Every Ambitious Plan) · 落地执行引擎

<br>
<em style="font-size: 16px;">三张底牌，两条管线，一套规则——这不是 prompt engineering，这是 Skill engineering。</em>
<br>
</div>

<div align="center">

[English](README_EN.md) | [中文](README.md)

<br>
</div>

LEAP 内含两条管线——A 分支从 raw data 蒸馏 Skill，B 分支把多个 Skill 编织为一个。不自己做路由，不跟用户交互，只做执行。

但它真正强的地方不是管线多，是它手里有三张牌——这三张牌，目前没有第二个 Skill 生产系统拿得出来。

---

## 三张底牌

### 1. skill-grammar.md — 从数据里反向工程出来的 Skill 写作铁律

网上所有人都在教怎么写 prompt，没有人在教怎么写 Skill。为什么？因为没有数据。

我们从 skills.sh 解析了大量公开 Skill，建了一套评分系统，逐项打分、统计、找规律。

**数据告诉我们什么？**

- **精英 skill（Top 10%，≥11 分）100% 用 chain-of-steps。** 没有一个例外。
- **reference 型 skill 在质量过滤后几乎消失（8%→1%）。** reference 型 = 判死刑。
- **<100 行的 skill 被大量排除（27%→9%）。** 太薄 = 硬伤。
- **hybrid trigger 在好 skill 中反而占比更高（16%→21%）。** 混合触发是好 skill 的信号。

这些不是意见，是统计事实。skill-grammar.md 把结论编译成强制规则——每一条反模式都有数据背书。

编译阶段，LEAP **必须**先读 skill-grammar.md。不读 → 禁止编译。读完 → 对照精英模板 + 反模式清单逐条检查，编译后自评 /10 分，机械验证跑 quality_check.py。

**我们不是在猜什么是好 Skill。我们量过。**

### 2. find-skills + score_skill.py — 面向全 skills.sh 的实时检索 + 运行时机械评分

我们不维护本地索引。本地索引是小圈子自嗨——skills.sh 上 skill 天天在涨，存个静态快照就是在限定自己的上限。

取而代之的是两级实时架构：

**检索层：find-skills。** skills.sh 的语义搜索引擎，面对全部公开 skill。搜「创业决策」「debugging methodology」——返回的是当下最匹配的候选，不是几个月前的快照。

**评分层：score_skill.py。** 同一个 13 分评分标准，搬到了运行时。find-skills 搜出 20 个候选 → 并发下载 SKILL.md → 每个毫秒级机械评分 → elite（≥11）优先，draft（<9）丢弃。评分逻辑不依赖 LLM——全是规则匹配：section 数量、trigger 关键词、boundary 声明、步骤密度、行数区间。确定性的，可复现的，不开玩笑的。

A-Stage 5 拿 top 3-5 精英做 exemplar。B-Step 1 拿评分过滤掉垃圾源。垃圾进垃圾出——这条铁律在入口就守住。

**别人靠 prompt engineering 猜什么是好 Skill。我们靠 find-skills 搜全量，再用 score_skill 机械判定好坏。离线索引时代结束了。**

### 3. 三级质量金字塔 — 好、中、差各长什么样，量化到数字

从全量数据统计出的量化结论：

| 层级 | 分数 | 占比 | 特征 |
|------|------|------|------|
| 精英 | ≥11 | 10% | 100% chain-of-steps，94% 有边界声明，89% 诊断+验证 |
| 中间 | ≥9 | 60% | 79% chain-of-steps，hybrid trigger 比底层多 5pp |
| 底层 | <9 | 40% | reference 型全集中在此，平均 54 行（精英 273 行，5x 差距） |

这意味着：**你拿到任何一个 SKILL.md，跑一下 score_skill.py，立刻知道它属于哪一层。** 编译自评不是感觉——是同一个评分体系下的量化结果。

---

## 两条分支

| 分支 | 做什么 | 管线 |
|------|------|------|
| **A：蒸馏** | 从 raw data 提取 OS → Persona / Tool Skill | 7 Stage + 2 Gate |
| **B：融合** | method.skill × subject.skill → 新 Skill | 4 Step + 3 Gate |

**A 分支**：Source Intake → Assessment → Research Plan Design → Research Swarm（N agents 并行，每个 ≥2 Dilemma Decision Cases）→ Gate 1: Merge → Exemplar Discovery（find-skills 搜索 → score_skill 评分 → 取 top 3-5 精英）→ Synthesis（3 agents）→ Skill Compilation → Gate 2: Validation。

**B 分支**：Retrieve（四级检索：output/ → ~/.claude/skills/ → find-skills → GitHub raw）→ Parse（骨架 + 血肉）→ Weave（standard: 重写身份 → 编织 workflow×style → 合并约束 → 检查缺口）→ Output → Gate 1/2/3。

**两条分支共用三张底牌。** 蒸馏靠 skill-grammar 约束编译质量，靠 find-skills + score_skill 找到精英 exemplar。融合靠 find-skills 发现新 skill，靠 score_skill 过滤垃圾源。

---

## Skill-Alchemy 生态

LEAP 不直接面向用户。它是 Skill-Alchemy 编排器调用的执行引擎：

| 项目 | 做什么 |
|---|---|
| [Skill-Alchemy](..) | 编排器，Phase 0（depth）→ Phase 1（Lens）→ Phase 2（路由）→ Phase 3（LEAP）→ Phase 4（报告） |
| [Lens](../Lens) | 认知镜片，四步认知展开，先于 LEAP 发现隐性维度 |

**Lens 看清，Skill-Alchemy 编排，LEAP 落地。**

---

<div align="center">
  <br>
  <em style="font-size: 20px;">三张底牌，两条管线，一套规则——这不是 prompt engineering，这是 Skill engineering。</em>
  <br>
</div>
