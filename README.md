<div align="center">

# SkillAlchemy

Turn people, methods, and experience into installable, reusable agent skills.

[English](README.md) · [中文](README_CN.md)

</div>

<p align="center">
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/github/license/agentsope/SkillAlchemy?color=blue" alt="License">
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

SkillAlchemy is an open-world agent skill creation system. It discovers omitted requirements, extracts executable procedures from public sources, and produces skills that agents can install and use directly.

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## Features

- **Distill people** — Build Persona Skills from public evidence about decisions, failures, values, and communication patterns.
- **Distill methods** — Turn books, methodologies, repositories, or interviews into executable Skills with conditions, steps, branches, and failure handling.
- **Fuse Skills** — Combine existing workflows, domain knowledge, or working styles into a new capability.
- **Stay evidence-grounded** — Separate reusable procedures, scoped cases, and unsupported content to reduce unjustified generalization.

## Quick Start

The easiest way to install SkillAlchemy is to ask Claude Code or Codex:

```text
Install SkillAlchemy from https://github.com/agentsope/SkillAlchemy and show me how to use it.
```

Or use the command line:

```bash
npx skills add agentsope/SkillAlchemy
```

Then describe the Skill you want to create:

```text
Use SkillAlchemy to create a Skill for reviewing RAG systems. Use public documentation and research papers as sources.
```

Generated packages are written to `output/` in the active project.

### Install Individual Skills

```bash
# Core components
npx skills add agentsope/SkillAlchemy/skills/Lens
npx skills add agentsope/SkillAlchemy/skills/LEAP

# Another bundled Skill
npx skills add agentsope/SkillAlchemy/skills/<skill-name>
```

[Browse all installable Skills](skills/)

## Results

We evaluate SkillAlchemy on 87 tasks from SkillsBench v1.1 across four agent–model configurations. It improves average task pass rate by **19.9 percentage points** over no-skill execution and by **8.6 points** over the strongest automated skill-creation baseline, with aggregate performance comparable to human-curated skills.

<div align="center">
  <img src="assets/main-results.png" alt="SkillAlchemy task-level evaluation results" width="75%">
</div>

---

<p align="center">
  <a href="TECHNICAL.md"><strong>Documentation</strong></a> ·
  <a href="LICENSE"><strong>MIT License</strong></a>
</p>
