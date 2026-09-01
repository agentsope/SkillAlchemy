<div align="center">

# SkillAlchemy

**Turn people, methods, and experience into installable, reusable agent skills.**

[English](README.md) · [中文](README_CN.md) · [日本語](README_JA.md)

</div>

<p align="center">
  <a href="https://arxiv.org/abs/2608.23417"><img src="https://img.shields.io/badge/arXiv-2608.23417-b31b1b.svg" alt="arXiv"></a>
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

SkillAlchemy is an **open-world agent skill creation system** that turns underspecified skill briefs and open-world sources into installable, reusable agent skills.

It discovers omitted requirements, identifies executable procedures from heterogeneous public sources, determines how broadly each procedure is justified by evidence, and compiles the admitted knowledge into agent skill packages.

<div align="center">
  <img src="assets/framework.png" alt="SkillAlchemy framework" width="100%">
</div>

## 🔥 News

* **2026-08-24** — Our paper, **[SkillAlchemy: Open-World Agent Skill Creation](https://arxiv.org/abs/2608.23417)**, is now available on arXiv.

## Overview

Creating reliable agent skills is difficult when the target capability is unfamiliar: task descriptions omit important requirements, expert-written procedures may not exist, and execution traces may be unavailable.

SkillAlchemy approaches skill creation as a **source-grounded procedure-admission problem**.

Given an underspecified skill brief and access to open-world sources, it:

1. **Discovers implicit requirements** that are missing from the original brief.
2. **Acquires grounded procedures** from documentation, repositories, papers, issue reports, and other public sources.
3. **Determines procedure scope** — deciding whether evidence supports a reusable instruction, a scoped example, or exclusion.
4. **Compiles an installable Skill package** that agents can load and use directly.

## Results

We evaluate SkillAlchemy on **87 tasks from SkillsBench v1.1** across four agent–model configurations.

SkillAlchemy achieves the highest overall task pass rate in **3 of 4 configurations**.

Averaged across all configurations, SkillAlchemy reaches a **55.8%** task pass rate:

* **+19.9 percentage points** over no-skill execution.
* **+8.6 percentage points** over the strongest automated skill-creation baseline.
* Performance **comparable to human-curated skills**, slightly exceeding them on average in our evaluation.

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

## Features

* **Discover implicit requirements** — Recover behavior-relevant requirements, constraints, and operational dimensions omitted by an underspecified Skill brief.
* **Distill people** — Build Persona Skills from public evidence about decisions, failures, values, and communication patterns.
* **Distill methods** — Turn books, methodologies, repositories, documentation, papers, or interviews into executable Skills with conditions, steps, branches, and failure handling.
* **Admit evidence-supported procedures** — Separate reusable instructions from context-specific examples and unsupported content instead of treating every retrieved finding as universally valid.
* **Fuse Skills** — Combine existing workflows, domain knowledge, or working styles into a new capability.
* **Compile installable Skills** — Package admitted procedures, examples, references, and supporting resources into Skills that agents can load and use directly.

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
Use SkillAlchemy to create a Skill for reviewing RAG systems.
Use public documentation and research papers as sources.
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

## Paper & Citation

For the full formulation, framework design, and experimental evaluation, see:

> **SkillAlchemy: Open-World Agent Skill Creation**
> Hengjun Wang, Shuyue Wei, Boyi Liu, Jun Yang, Yongxin Tong. 
> arXiv:2608.23417, 2026
> **[arXiv](https://arxiv.org/abs/2608.23417)** · **[PDF](https://arxiv.org/pdf/2608.23417)**

If you find SkillAlchemy useful in your research or work, please cite our paper:

```bibtex
@article{wang2026skillalchemy,
  title   = {SkillAlchemy: Open-World Agent Skill Creation},
  author  = {Wang, Hengjun and Wei, Shuyue and Liu, Boyi and Yang, Jun and Tong, Yongxin},
  journal = {arXiv preprint arXiv:2608.23417},
  year    = {2026}
}
```

## License

SkillAlchemy is released under the [MIT License](LICENSE).

---

<p align="center">
  <a href="TECHNICAL.md"><strong>Technical Documentation</strong></a>
</p>
