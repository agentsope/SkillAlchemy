<div align="center">

# SkillAlchemy

<br>
<em style="font-size: 20px;">One thought conceived, one goal achieved</em>
<br>
<br>
<em style="font-size: 16px;">Turn any person, any method, any experience into an installable Skill.</em>
<br>
</div>

<p align="center">
  <a href="https://github.com/agentsope/SkillAlchemy/stargazers"><img src="https://img.shields.io/github/stars/agentsope/SkillAlchemy?logo=github&color=ffca28" alt="Stars"></a>
  <img src="https://img.shields.io/github/license/agentsope/SkillAlchemy?color=blue" alt="License">
  <img src="https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-6E56CF" alt="Supported agents">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#what-it-does">What It Does</a> ·
  <a href="#example">Example</a> ·
  <a href="#parameters">Parameters</a> ·
  <a href="#distilled-skills">Distilled Skills</a> ·
  <a href="#boundaries">Boundaries</a> ·
  <a href="#our-ambition">Ambition</a>
</p>

<div align="center">

**Other Languages:** [中文](README.md)

<br>
</div>

## Quick Start

Send this to Claude Code (or Codex):

```
Please pull the skill from https://github.com/agentsope/SkillAlchemy and install it into my Claude Code skills, then tell me how to use it.
```

Or via command line:

```bash
npx skills add agentsope/SkillAlchemy
```

---

## What It Does

**Distill a person.** Give it a name. 4-5 research Agents dig into their decision moments, failure handling, value conflicts, and expression patterns — extracting their OS into a conversational Persona Skill.

**Distill a methodology.** A book, a framework, an open-source repo, an expert interview — distilled into executable SOPs: prerequisites → steps → branch logic → failure handling, with verifiable evidence at every step.

**Fuse existing skills.** Combine two skills into one — "First-Principles × Feynman Technique" → a deep-understanding engine that decomposes to fundamentals, then teaches to a 12-year-old.

---

## Example

<div align="center">
  <img src="SkillAlchemy.gif" alt="SkillAlchemy Demo" width="700">
  <br>
  <em>Distilling "Stephen Chow" → persona skill, full pipeline</em>
</div>

<br>

```
◆ Task Briefing

▸ Target   Distill "Stephen Chow" → persona skill
▸ Pipeline Lens → A-branch (7 Stage + 2 Gate)
           ├─ Research Swarm  5 agents parallel
           ├─ Exemplar        find-skills online search + auto-score
           └─ Compile         compile + self-score + validate
▸ Depth    standard · ~15-20 min
▸ Mode     step-by-step (2 checkpoints)

> Confirm, run with standard

[5 Agents completed in parallel, Gate 1 passed, 11+ Dilemma Cases]
[Compiled SKILL.md, quality_check pass, self-score 10/10 · elite]

◆ Distillation Complete

  skill     Stephen Chow · stephen-chow
  type      persona · 102 lines
  quality   ✓ pass · self-score 10/10 · elite
  output    output/stephen-chow-skill/

  try       /stephen-chow What do you think makes comedy funny?
```

---

## Parameters

One parameter: `depth`. Default `standard`.

| Dimension | quick | standard | deep |
|---|---|---|---|
| Agents | ≤3 | 4-5 | 6-8 |
| Est. time | ~5-8 min | ~15-20 min | ~25-35 min |
| Quality review | Skip | Recommended | Required + dual review |
| Label | `draft` | `standard` | `validated` |

2 confirmation checkpoints on the distill route: task briefing, research plan. "All default" mode skips all interactions.

Feel free to ask any question.

---

## Distilled Skills

The `skills/` directory contains a rich collection of pre-distilled Skills covering major AI Agent frameworks, tools, and workflows. No need to distill from scratch — install and use immediately.

**Method 1: Command line**

```bash
npx skills add agentsope/SkillAlchemy/skills/<skill-name>
```

**Method 2: Natural language**

Send this to Claude Code (or Codex):

```
Please install <skill-name> from https://github.com/agentsope/SkillAlchemy for me
```

For example, to install Lens:

```
Please install Lens from https://github.com/agentsope/SkillAlchemy for me
```

See [`skills/`](skills/) for all available Skills.

---

## Boundaries

Not suitable for recreating people with scarce source material. Don't expect three news articles to summon a full persona. Not suitable for inventing private personalities — if public material doesn't contain the inner drama, we don't add it. Not suitable for high-risk professional decisions — when someone needs to sign and bear responsibility, you're more useful than all the "Steve Jobses." Not suitable for rewriting copyrighted content — changing the hairstyle doesn't make it a different person.

---

## Our Ambition

The gap between future Agents won't come from who has the stronger model. Models will converge. The real difference will come from the Skills loaded into those Agents.

The same model with no Skills is just a general brain that can talk. Load a First-Principles Thinking Skill, and it breaks down complex problems. Load a Zhang Xuefeng Skill, and it helps ordinary families calculate the ROI of education.

Skill is not a prompt. It is the working method behind a person, a methodology, a domain, a body of experience.

Skill-Alchemy distills the judgment rules, execution steps, boundary conditions, and validation standards behind a source into a Skill that an Agent can load directly. Skill stops being mysticism or stitched-together prompting. It becomes a reproducible, verifiable, scalable production line.

---

<div align="center">
  <br>
  <em style="font-size: 20px;">One thought conceived, one goal achieved</em>
  <br>
  <br>
  MIT License © <a href="https://github.com/agentsope">agentsope</a>
</div>
