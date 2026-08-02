<div align="center">

# SkillAlchemy

### Open-World Agent Skill Creation

Turn people, methods, and experience into installable, reusable agent skills.

[English](README_EN.md) · [中文](README.md)

</div>

<p align="center">
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/github/license/agentsope/SkillAlchemy?color=blue" alt="License">
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

## Overview

Creating a reliable skill requires more than summarizing source material. The
creator must recover conditions omitted by the task brief, extract executable
procedures from open-world sources, and decide how broadly each procedure applies.

SkillAlchemy supports three workflows:

1. **Distill a person** into a Persona Skill grounded in public evidence about decisions, failures, values, and communication patterns.
2. **Distill a method** from a book, methodology, repository, or interview into an executable Skill with conditions, steps, branches, and failure handling.
3. **Fuse existing Skills** by combining a workflow with complementary domain knowledge or working styles.

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## Installation

Install the complete SkillAlchemy workflow:

```bash
npx skills add agentsope/SkillAlchemy
```

Or ask Claude Code or Codex directly:

```text
Install SkillAlchemy from https://github.com/agentsope/SkillAlchemy and show me how to use it.
```

Install the core components separately:

```bash
npx skills add agentsope/SkillAlchemy/skills/Lens
npx skills add agentsope/SkillAlchemy/skills/LEAP
```

Install another bundled Skill:

```bash
npx skills add agentsope/SkillAlchemy/skills/<skill-name>
```

[Browse all bundled Skills](skills/)

## Quick Start

After installation, tell Claude Code or Codex what you want to distill or fuse.
For example:

```text
Use SkillAlchemy to create a Skill for reviewing RAG systems. Use public
documentation and research papers as sources.
```

SkillAlchemy first uses **Lens** to discover implicit requirements. **LEAP** then
collects evidence, organizes reusable procedures, and builds the Skill package.
Generated packages are written to `output/` in the active project.

## Repository Structure

```text
.
├── SKILL.md                 # Main SkillAlchemy entry point
├── skills/
│   ├── Lens/                # Discovers implicit requirements
│   ├── LEAP/                # Distills, fuses, and builds Skills
│   └── agentsop-*/          # Ready-to-install agent engineering Skills
├── assets/                  # README figures
├── package.json
├── skill.json
└── LICENSE
```

See the [technical documentation](技术文档.md) for the internal workflow and
[CONTRIBUTING.md](CONTRIBUTING.md) before contributing.

## License

This project is released under the [MIT License](LICENSE).
