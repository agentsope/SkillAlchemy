<div align="center">

# Skill-Alchemy

<br>
<em style="font-size: 20px;">一念落地，万象成形</em>
<br>
<br>
<em style="font-size: 16px;">把任何人、任何方法、任何经验，变成一个可安装的 Skill。</em>
<br>
</div>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#它能做什么">它能做什么</a> ·
  <a href="#效果">效果</a> ·
  <a href="#参数">参数</a> ·
  <a href="#边界">边界</a> ·
  <a href="#我们的野心">野心</a>
</p>

<div align="center">

[English](README_EN.md) | [中文](README.md)

<br>
</div>

## 快速开始

把下面这句话发给 Claude Code（或者 Codex）：

```
请你帮我从 https://github.com/Whj9283/SkillAlchemy 拉取这个 skill 到本地，安装到 Claude Code 的 skills 里，然后告诉我怎么用。
```

Agent 会自动完成安装。装好之后，你就可以这样用：

```
蒸馏张雪峰，depth=standard
融合第一性原理思考和费曼学习法
帮我分析一下「做一个 AI 客服产品」需要考虑什么
```

也可以走命令行：

```bash
npx skills add Whj9283/Skill-Alchemy
```

---

## 它能做什么

**蒸馏一个人。** 告诉它一个名字，系统派出 4-5 个研究 Agent 并行深挖——从他的决策时刻、失败处理、价值观冲突、表达风格中提取 OS——编译成一个可以随时对话的 Persona Skill。

**蒸馏方法论。** 一本书、一套方法论、一个开源仓库、一段专家访谈——蒸馏成可执行的 SOP：前置条件 → 执行步骤 → 分支判断 → 失败处理，每一步都有可验证的证据。

**融合已有 Skill。** 把两个 skill 组合成一个新能力——「第一性原理 × 费曼学习法」→ 一个拆到底、讲到懂的深度理解引擎。

---

## 效果

```
◆ 任务简报

▸ 需求    蒸馏「张雪峰」→ persona skill
▸ 流程    Lens → A 分支（7 Stage + 2 Gate）
          ├─ Research Swarm  5 agent 并行研究
          ├─ Exemplar        find-skills 在线检索 + 自动评分
          └─ Compile         编译 + 自评 + 验证
▸ 深度    standard · ~15-20 min
▸ 交互    步步确认（2 次暂停）

> 确认，按 standard 跑

[5 个 Agent 并行研究完成，Gate 1 通过，Dilemma Cases 11+]
[编译 SKILL.md，quality_check pass，自评 10/10 · elite]

◆ 蒸馏完成

  skill     张雪峰 · zhang-xuefeng
  类型      persona · 102 行
  质量      ✓ pass · 自评 10/10 · elite
  产出      output/zhang-xuefeng-skill/

  试试      /张雪峰 我孩子理科590分河南想学计算机
```

---

## 参数

只有一个参数：`depth`。默认 `standard`。

| 维度 | quick | standard | deep |
|---|---|---|---|
| Agent 数 | ≤3 | 4-5 | 6-8 |
| 预计耗时 | ~5-8 min | ~15-20 min | ~25-35 min |
| 内容验证 | 跳过 | 建议 | 强制 + 双审核 |
| 标注 | `draft` | `standard` | `validated` |

蒸馏路线上有 2 个确认点：任务简报、research plan（Agent 维度可调）。支持「一路默认」跳过全部交互。

有任何问题直接问就好，不用客气。

---

## 边界

不适合资料稀缺的人物复刻——别指望三条新闻就召唤出一个完整的人格。不适合私密人格杜撰——公开资料里没有的内心戏，系统不替人加戏。不适合高风险专业决策——真要签字背锅时，你比所有「乔布斯们」更有用。不适合版权内容改写复用——换个发型不等于换了个人，洗稿也不等于原创。

---

## 我们的野心

未来 Agent 的差距，不会只看谁接入了更强的模型。模型会越来越强，也会越来越接近。真正拉开差距的，是 Agent 接入的 Skill。

同一个模型，什么 Skill 都不加载，只是一个会说话的通用大脑。加载了第一性原理 Skill，它就能拆复杂问题。加载了张雪峰 Skill，它就能帮普通家庭算教育账。

Skill 不是 prompt。它是一个人、一套方法、一个领域、一段经验背后的工作方式。

Skill-Alchemy 要做的，就是把 source 背后的判断规则、执行步骤、边界条件和验证标准蒸馏出来，变成 Agent 可以直接加载的 Skill。从此 Skill 不是玄学，不是 prompt 拼凑，而是一条可复现、可验证、可规模化的生产线。

---

<div align="center">
  <br>
  <em style="font-size: 20px;">一念落地，万象成形</em>
  <br>
  <br>
  MIT License © <a href="https://github.com/Whj9283">Whj9283</a>
</div>
