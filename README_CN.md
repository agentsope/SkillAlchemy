<div align="center">

# SkillAlchemy

**把人物、方法和经验转化为可安装、可复用的 Agent Skill。**

[English](README.md) · [中文](README_CN.md) · [日本語](README_JA.md)

</div>

<p align="center">
  <a href="https://arxiv.org/abs/2608.23417"><img src="https://img.shields.io/badge/arXiv-2608.23417-b31b1b.svg" alt="arXiv"></a>
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

SkillAlchemy 是一个**开放世界 Agent Skill 创建系统**。它从简短、欠完整的 Skill 需求和开放世界公开资料中发现遗漏条件，提取有证据支持的可执行步骤，并将其编译为 Agent 可以直接安装和使用的 Skill。

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## 🔥 最新动态

* **2026-08-24** — 我们的论文 **[SkillAlchemy: Open-World Agent Skill Creation](https://arxiv.org/abs/2608.23417)** 已上线 arXiv。

## 概览

当目标能力并不熟悉时，创建可靠的 Agent Skill 并不容易：简短需求往往遗漏关键条件，现成的专家流程可能并不存在，完整的执行轨迹也未必能够获得。

SkillAlchemy 将 Skill 创建建模为一个**基于来源证据的流程准入问题（source-grounded procedure-admission problem）**。

给定一个信息不完整的 Skill 需求以及开放世界资料，SkillAlchemy 会：

1. **发现隐含需求** — 补全原始需求中遗漏、但会影响实际执行的条件、约束和能力维度。
2. **提取有依据的可执行流程** — 从文档、代码仓库、论文、Issue、访谈等公开资料中提炼可执行方法。
3. **判断流程的适用范围** — 区分哪些内容可以写成通用指令，哪些只能作为限定场景下的示例，以及哪些内容证据不足、不应纳入。
4. **生成可安装的 Skill 包** — 将最终确认的流程、示例、参考资料和辅助资源编译成 Agent 可直接加载和使用的 Skill。

## 核心能力

* **发现隐含需求** — 从简短、欠完整的需求中恢复实际执行所需的约束、条件和行为维度。
* **蒸馏人物** — 从公开资料中提取决策方式、失败处理、价值取舍和表达特点，生成 Persona Skill。
* **蒸馏方法** — 将书籍、方法论、开源仓库、技术文档、论文或访谈整理为包含条件、步骤、分支和失败处理的可执行 Skill。
* **基于证据准入流程** — 区分可复用指令、限定场景示例和证据不足的内容，避免把所有检索结果都无条件泛化为通用规则。
* **融合 Skill** — 组合已有工作流程、领域知识或工作风格，形成新的复合能力。
* **生成可安装 Skill** — 将确认后的流程、示例、引用和相关资源打包为 Agent 可以直接加载和复用的 Skill。

## 快速开始

最简单的方式是直接告诉 Claude Code 或 Codex：

```text
请从 https://github.com/agentsope/SkillAlchemy 安装 SkillAlchemy，并告诉我如何使用。
```

也可以使用命令行：

```bash
npx skills add agentsope/SkillAlchemy
```

安装后，直接描述你想创建的 Skill：

```text
使用 SkillAlchemy，从公开文档和论文中创建一个用于审查 RAG 系统的 Skill。
```

生成结果默认写入当前项目的 `output/`。

### 单独安装 Skill

```bash
# 核心组件
npx skills add agentsope/SkillAlchemy/skills/Lens
npx skills add agentsope/SkillAlchemy/skills/LEAP

# 仓库中的其他 Skill
npx skills add agentsope/SkillAlchemy/skills/<skill-name>
```

[浏览全部可安装 Skills](skills/)

## 实验结果

我们在 **SkillsBench v1.1 的 87 个任务**和四种 Agent–Model 配置上评估了 SkillAlchemy。

SkillAlchemy 在 **4 种配置中的 3 种取得了最高任务通过率**。

在四种配置上取平均后，SkillAlchemy 的任务通过率达到 **55.8%**：

* 相比不使用 Skill，提升 **19.9 个百分点**；
* 相比最强的自动 Skill 创建基线，提升 **8.6 个百分点**；
* 整体表现与**人工编写的 Skill 相当**，并在平均结果上略高于人工 Skill。

<table>
  <thead>
    <tr>
      <th align="left">Skill Setting</th>
      <th align="center">Claude Code<br>DeepSeek-V4-Pro</th>
      <th align="center">Claude Code<br>Opus 4.8</th>
      <th align="center">Codex<br>DeepSeek-V4-Pro</th>
      <th align="center">Codex<br>GPT-5.5</th>
      <th align="center">Avg.</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>No Skill</td>
      <td align="right">23.4</td>
      <td align="right">45.3</td>
      <td align="right">29.7</td>
      <td align="right">45.1</td>
      <td align="right">35.9</td>
    </tr>
    <tr>
      <td>Anthropic Skill-Creator</td>
      <td align="right">31.7</td>
      <td align="right">49.2</td>
      <td align="right">32.9</td>
      <td align="right">48.5</td>
      <td align="right">40.6</td>
    </tr>
    <tr>
      <td>OpenAI Skill-Creator</td>
      <td align="right">33.3</td>
      <td align="right">49.9</td>
      <td align="right">37.0</td>
      <td align="right">48.5</td>
      <td align="right">42.2</td>
    </tr>
    <tr>
      <td>OpenSkill</td>
      <td align="right">42.3</td>
      <td align="right">51.5</td>
      <td align="right">40.7</td>
      <td align="right">49.4</td>
      <td align="right">46.0</td>
    </tr>
    <tr>
      <td>MUSE-Autoskill</td>
      <td align="right">43.2</td>
      <td align="right">53.3</td>
      <td align="right">40.2</td>
      <td align="right">52.0</td>
      <td align="right">47.2</td>
    </tr>
    <tr>
      <td>Human-Curated Skill</td>
      <td align="right">51.3</td>
      <td align="right">59.5</td>
      <td align="right"><strong>45.7</strong></td>
      <td align="right">60.9</td>
      <td align="right">54.4</td>
    </tr>
    <tr>
      <td><strong>SkillAlchemy</strong></td>
      <td align="right"><strong>54.7</strong></td>
      <td align="right"><strong>60.9</strong></td>
      <td align="right">43.9</td>
      <td align="right"><strong>63.7</strong></td>
      <td align="right"><strong>55.8</strong></td>
    </tr>
  </tbody>
</table>

## 论文与引用

完整的问题定义、系统设计和实验结果请参见：

> **SkillAlchemy: Open-World Agent Skill Creation**
> Hengjun Wang, Shuyue Wei, Boyi Liu, Jun Yang, Yongxin Tong
> arXiv:2608.23417, 2026
> **[arXiv](https://arxiv.org/abs/2608.23417)** · **[PDF](https://arxiv.org/pdf/2608.23417)**

如果 SkillAlchemy 对你的研究或工作有帮助，欢迎引用我们的论文：

```bibtex
@article{wang2026skillalchemy,
  title   = {SkillAlchemy: Open-World Agent Skill Creation},
  author  = {Wang, Hengjun and Wei, Shuyue and Liu, Boyi and Yang, Jun and Tong, Yongxin},
  journal = {arXiv preprint arXiv:2608.23417},
  year    = {2026}
}
```

## License

SkillAlchemy 基于 [MIT License](LICENSE) 开源。

---

<p align="center">
  <a href="TECHNICAL.md"><strong>技术文档</strong></a>
</p>
