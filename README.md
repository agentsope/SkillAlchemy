<div align="center">

# SkillAlchemy

把人物、方法和经验转化为可安装、可复用的 Agent Skill。

[English](README_EN.md) · [中文](README.md)

</div>

<p align="center">
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/github/license/agentsope/SkillAlchemy?color=blue" alt="License">
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

SkillAlchemy 是一个开放世界 Agent Skill 创建系统。它从简短需求和公开资料中发现遗漏条件、提取可执行步骤，并生成可直接安装的 Skill。

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## 核心能力

- **蒸馏人物** — 从公开资料中提取决策方式、失败处理、价值取舍和表达特点，生成 Persona Skill。
- **蒸馏方法** — 将书籍、方法论、开源仓库或访谈整理为包含条件、步骤、分支和失败处理的可执行 Skill。
- **融合 Skill** — 组合已有 Skill 的工作流程、领域知识或工作风格，形成新的复合能力。
- **证据驱动** — 区分可复用步骤、限定场景和证据不足的内容，减少无依据的泛化。

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

我们在 SkillsBench v1.1 的 87 个任务和四种 Agent–Model 配置上评估了 SkillAlchemy。与不使用 Skill 相比，平均任务通过率提高 **19.9 个百分点**；与最强的自动 Skill 创建基线相比，提高 **8.6 个百分点**，整体表现与人工编写的 Skill 相当。

<div align="center">
  <img src="assets/main-results.png" alt="SkillAlchemy task-level evaluation results" width="75%">
</div>

---

<p align="center">
  <a href="TECHNICAL.md"><strong>技术文档</strong></a> ·
  <a href="LICENSE"><strong>MIT License</strong></a>
</p>
