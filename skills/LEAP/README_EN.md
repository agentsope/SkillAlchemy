<div align="center">

# LEAP (Launch Every Ambitious Plan) · Execution Engine

<br>
<em style="font-size: 16px;">Three aces, two pipelines, one rule — this is not prompt engineering. This is Skill engineering.</em>
<br>
</div>

<div align="center">

**Other Languages:** [中文](README.md)

<br>
</div>

LEAP houses two pipelines — A-branch distills Skills from raw data, B-branch weaves multiple Skills into one. It never routes, never interacts with users, just executes. Use it standalone or let an orchestrator call it.

But its real strength isn't the pipelines. It's the three aces. No other Skill production system has them.

---

## The Three Aces

### 1. skill-grammar — Writing rules reverse-engineered from real data

We parsed a massive number of public Skills from skills.sh, built a scoring system, and ran statistical comparisons.

**The data taught us:**

- **Elite Skills (Top 10%) use chain-of-steps 100% of the time.** No exceptions.
- **Reference-type Skills almost disappear after quality filtering.** No executable steps = dead on arrival.
- **Skills that are too thin get massively filtered out.** Line count matters.
- **Hybrid triggers are a signal of good Skills.**

LEAP must read skill-grammar before compilation. No read → no compile.

**We're not guessing what makes a good Skill. We measured.**

### 2. find-skills + score_skill — Real-time retrieval + mechanical scoring for the entire skills.sh pool

No local index. Skills on skills.sh grow daily — a static snapshot limits your ceiling.

**Retrieval layer: find-skills.** Semantic search across all public Skills. **Scoring layer: score_skill.** 13-point mechanical scoring, runtime filtering.

A-Stage 5 auto-picks elite exemplars. B-Step 1 filters out garbage sources. Garbage in, garbage out.

### 3. Quality pyramid — Good, average, bad, quantified to numbers

| Tier | Score | Feature |
|------|-------|---------|
| **Elite** | ≥11 | 100% chain-of-steps, 94% boundary declarations, 89% diagnosis + validation |
| **Standard** | ≥9 | chain-of-steps dominant, hybrid trigger ratio higher |
| **Bottom** | <9 | Reference types concentrated here, average line count 1/5 of elite |

---

## Two Pipelines

| Branch | What it does | Pipeline |
|--------|-------------|----------|
| **A: Distill** | Raw data → Persona / Tool Skill | 7 Stage + 2 Gate |
| **B: Fuse** | method × subject → New Skill | 4 Step + 3 Gate |

---

<div align="center">
  <br>
  <em style="font-size: 20px;">Three aces, two pipelines, one rule.</em>
  <br>
</div>
