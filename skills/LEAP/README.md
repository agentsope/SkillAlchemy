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

LEAP 内含两条管线——A 分支从 raw data 蒸馏 Skill，B 分支把多个 Skill 编织为一个。不自己做路由，不跟用户交互，只做执行。可以直接用，也可以被编排器调用。

但它真正强的地方不是管线多，是它手里有三张牌——这三张牌，目前没有第二个 Skill 生产系统拿得出来。

---

## 三张底牌

### 1. skill-grammar — 从数据里反向工程出来的写作铁律

我们从 skills.sh 解析了大量公开 Skill，建了一套评分系统，逐项打分、统计、找规律。

**数据教会我们的事：**

- **精英 Skill 100% 用 chain-of-steps。** 没有一个例外。
- **纯参考文档型 Skill 在质量过滤后几乎消失。** 没有可执行步骤 = 判死刑。
- **太薄的 Skill 被大量排除。** 行数不够是硬伤。
- **混合触发（关键词 + 上下文）是好 Skill 的信号。**

编译阶段，LEAP 必须先读 skill-grammar。不读 → 禁止编译。

**我们不是在猜什么是好 Skill。我们量过。**

### 2. find-skills + score_skill — 面向全 skills.sh 的实时检索 + 运行时机械评分

不维护本地索引。skills.sh 上 Skill 天天在涨，静态快照就是限制上限。

**检索层 find-skills：** 语义搜索引擎，面向全部公开 Skill。**评分层 score_skill：** 搜出候选 → 并发下载 → 毫秒级评分 → 精英优先，draft 丢弃 → 自动注入编译。

### 3. 三级质量金字塔 — 好、中、差量化到数字

| 层级 | 分数 | 特征 |
|------|------|------|
| 精英 | ≥11 | 100% chain-of-steps，94% 有边界声明，89% 诊断+验证兼备 |
| 中间 | ≥9 | chain-of-steps 为主，hybrid trigger 占比更高 |
| 底层 | <9 | 纯参考型全集中在此，平均行数仅为精英的 1/5 |

---

## 两条分支

| 分支 | 做什么 | 管线 |
|------|------|------|
| **A：蒸馏** | 从 raw data 提取 OS → Persona / Tool Skill | 7 Stage + 2 Gate |
| **B：融合** | method.skill × subject.skill → 新 Skill | 4 Step + 3 Gate |

---

<div align="center">
  <br>
  <em style="font-size: 20px;">三条底牌，两条管线，一套规则。</em>
  <br>
</div>
