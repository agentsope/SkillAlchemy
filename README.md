<div align="center">

# SkillAlchemy

### 一念落地，万象成形

把人物、方法和经验转化为可安装、可复用的 Agent Skill。

[English](README_EN.md) · [中文](README.md)

</div>

<p align="center">
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/github/license/agentsope/SkillAlchemy?color=blue" alt="License">
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

## 项目简介

创建可靠的 Skill 不只是总结资料。系统需要发现任务描述中遗漏的条件，
从公开来源中提取可执行步骤，并判断每条经验可以复用到多大的范围。

SkillAlchemy 支持三类任务：

1. **蒸馏人物**：从公开资料中提取决策方式、失败处理、价值取舍和表达特点，生成 Persona Skill。
2. **蒸馏方法**：将书籍、方法论、开源仓库或访谈整理为包含条件、步骤、分支和失败处理的可执行 Skill。
3. **融合 Skill**：组合已有 Skill 的工作流程与领域视角，形成新的复合能力。

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## 安装

安装完整的 SkillAlchemy 工作流：

```bash
npx skills add agentsope/SkillAlchemy
```

也可以直接告诉 Claude Code 或 Codex：

```text
请从 https://github.com/agentsope/SkillAlchemy 安装 SkillAlchemy，并告诉我如何使用。
```

也可以单独安装核心组件：

```bash
npx skills add agentsope/SkillAlchemy/skills/Lens
npx skills add agentsope/SkillAlchemy/skills/LEAP
```

安装仓库中其他 Skill：

```bash
npx skills add agentsope/SkillAlchemy/skills/<skill-name>
```

[浏览仓库中的全部 Skills](skills/)

## 快速开始

安装后，直接告诉 Claude Code 或 Codex 你想蒸馏或融合什么。例如：

```text
使用 SkillAlchemy，从公开文档和论文中创建一个用于审查 RAG 系统的 Skill。
```

SkillAlchemy 先用 **Lens** 补全任务中的隐含需求，再由 **LEAP** 收集证据、
整理可复用步骤并生成 Skill 包。生成结果默认写入当前项目的 `output/`。

## 仓库结构

```text
.
├── SKILL.md                 # SkillAlchemy 主入口
├── skills/
│   ├── Lens/                # 发现隐含需求
│   ├── LEAP/                # 蒸馏、融合并生成 Skill
│   └── agentsop-*/          # 可直接安装的 Agent 工程 Skill
├── assets/                  # README 图片
├── package.json
├── skill.json
└── LICENSE
```

更详细的内部流程见[技术文档](技术文档.md)。参与贡献前请阅读
[CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目采用 [MIT License](LICENSE)。
