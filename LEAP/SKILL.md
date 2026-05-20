---
name: LEAP
description: |
  LEAP — 落地执行引擎。内含两条管线：A 分支蒸馏（从 raw data 提取 skill）、
  B 分支融合（多 skill 编织为一个）。被 SkillAlchemy 编排器调用。
  Use when 编排器判断需要蒸馏或融合时。
version: v1.0
---

# LEAP · 落地执行引擎

LEAP 不自己做路由，不跟用户交互。上游 Skill-Alchemy 告诉它走哪条分支，它执行。
所有交互节点由 Skill-Alchemy 编排——LEAP 只负责跑管线，跑完返回结果。

## 分支路由

| 指令 | 分支 | 管线 |
|------|------|------|
| `distill` / `蒸馏` | **A 分支** | 蒸馏管线 — 从 raw data 提取 target OS，编译为 persona/tool skill |
| `fuse` / `融合` | **B 分支** | 融合管线 — method.skill(骨架) × subject.skill(s)(血肉) → output.skill |

## 调用模式

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Full run** | No special keyword | 完整管线 + Gate，输出 skill 包 |
| **Plan only** | `只到 Stage 3` 或 `stop_after_stage: 3` | A 分支 Stage 1-3 only，输出 research_plan.json 后停止 |
| **Resume** | `从 Stage 4 继续` 或 `resume_from_stage: 4` | A 分支跳过 1-3，使用已有 research_plan.json，跑 4-7 + Gates |

---

# A 分支: 蒸馏管线

```text
Source Intake → Intake Assessment → Research Plan Design
  → Research Swarm → Gate 1: Merge
  → Exemplar Discovery → Synthesis (3 agents)
  → Skill Compilation → Gate 2: Validation
```

Core principle: extract the operating system behind the source, not just the content or answer.

---

## A-Stage 1: Source Intake

Input: person, author, method, organization, domain, URL, repo, or local files.

Create package workspace at `output/<target-slug>-skill/`:

```
output/<target-slug>-skill/
├── README.md
├── SKILL.md.draft
├── references/             # agent reports + exemplars
├── intermediate/           # structured data
├── examples/               # persona: required; tool: optional
└── validation/             # only for deep mode (Phase 8)
```
> `templates/` 不再预建——输出模板在 LEAP 共享层，产出 skill 不需要。
> `validation/` 只在 depth=deep 且 Phase 8 执行时创建。

Write `intermediate/open_world_task.json` with target, goal, sources, depth_level:

| `depth_level` | Effect | Use case |
|:--|:--|:--|
| `quick` | Agent count ≤3, skip Phase 8, mark quality: draft | Rapid prototype |
| `standard` | No correction to auto-assessment, Phase 8 suggested | Daily use (default) |
| `deep` | Agent count upper bound +1 (≤8), Phase 8 required, dual review | Release quality |

---

## A-Stage 2: Intake Assessment

### Step 1: Source Modality Analysis

Classify every source by what it can reveal:

| Modality | Examples | Reveals |
|----------|---------|---------|
| `transcript_interview` | podcasts, video captions, Q&A | spontaneous reasoning, analogies, changed positions |
| `longform_text` | books, papers, essays, newsletters | core arguments, methodology, narrative structure |
| `secondary_criticism` | reviews, biographies, analysis | external perspective, blind spots, competing views |
| `video_subtitle` | YouTube, B站 captions | speech patterns, unscripted reasoning |
| `social_media` | posts, threads | expression patterns, real-time reactions |
| `code_repo` | git repos, PRs | architecture patterns, API contracts, testing strategy |

For each modality present, note what operations it could reveal. Skip absent ones.

### Step 2: Domain Inference

Read `domains/<domain>/domain.md` to confirm. Record primary + secondary domains.

### Step 3: Evidence Depth Assessment

**Don't count sources — assess their density.**

- ≥3 high-density sources across ≥2 modalities → **rich** (5-8 agents)
- 1-2 high-density sources → **moderate** (3-5 agents)
- 0 high-density, all medium/low → **sparse** (2-3 agents)

Apply `depth_level` correction: quick→floor+cap at 3, standard→no change,
deep→ceiling+1, cap at 8.

### Step 4: Skill Mode Determination

| Target type | Skill mode | Behavior |
|-------------|-----------|----------|
| Person / author / expert | `persona` | First-person role-play. Has 角色扮演规则, 身份, 我怎么说话, 决策启发式 |
| Domain / method / organization | `tool` | Third-person analytical. Has Activation Rules, Agentic Protocol, Operation Models |

---

## A-Stage 3: Research Plan Design

### How to select dimensions

1. Read primary domain pack: `domains/<primary-domain>/domain.md` → Research dimensions
2. **If persona, also read `domains/persona-os/domain.md`.** This cross-cutting layer
   provides OS extraction lenses (decision under constraint, failure processing,
   value conflict resolution, attention allocation, etc.).
3. Cross dimensions with source modality: match → active, no match → skip
4. Apply evidence depth cap: sparse→merge, moderate→1:1, rich→split
5. Derive new dimensions from source if domain pack menus don't cover what's visible

### Self-Check Before Writing research_plan.json

1. **Depth match** — Does agent_count fall within the depth range?
2. **Modality coverage** — Are source_modalities_used actually present?
3. **Dimension coverage** — Is every active dimension covered?
4. **Merge intent** — Deliberate or lazy? Document the rationale.

### Search direction must target dilemmas

```
Good: "What was the hardest decision at [event]? What options did they have?"
Bad:  "What is their leadership style?"
```

Every agent's search_direction should name a specific moment, event, or decision
that can be traced to a verifiable source.

### Plan-Only Mode Stop Point

**If invoked with `只到 Stage 3` or `stop_after_stage: 3`:**

写完 `research_plan.json` 后立即停止。输出：

```
Research plan 已生成，保存在 intermediate/research_plan.json。

[N] 个 agent，维度：
  R1 — [dimension]: [search_direction 摘要]
  R2 — [dimension]: [search_direction 摘要]
  ...
```

不要进入 Stage 4。等待 Skill-Alchemy 返回确认/调整后的指令。

---

## A-Stage 4: Research Swarm

**Resume mode:** 如果在 `从 Stage 4 继续` 模式下调用，直接从已有的
`intermediate/research_plan.json` 读取 agent 配置。跳过 Stage 1-3。

Launch N agents in parallel. Each agent writes `references/R<NN>-<agent_id>.md`:

```
Status: pass (or warning / fail)

## Key Findings
## Dilemma Decision Cases (≥2 required)
  ### Case N: [one-line summary]
  - 困境 (Dilemma): specific conflict or hard choice
  - 约束 (Constraints): what limited their options
  - 决策步骤 (Decision Steps): what they did, step by step
  - 结果 (Outcome): what happened
  - 可提取的操作 (Extractable Operation): generalizable rule/pattern/heuristic
## Evidence Sources (source_id, type, confidence)
## Supported Candidate Operations
## Rejected or Weak Candidate Operations
## Target-specific Patterns
## Boundaries and Uncertainties
## Recommendations for Later Skill Compilation
```

**Agent Contract:** Every report begins with `Status: pass` / `warning` / `fail`.
Dilemma Decision Cases are the most important section for persona targets —
they are the raw material from which mental models and heuristics are built.

**Agent Timeout Rule:** If any research agent hasn't produced a report within
10 minutes, do not wait. Proceed with completed agents. Gate 1 checks:
- Persona: ≥4 total Dilemma Cases across all completed reports → pass.
  <4 → downgrade depth to quick and relaunch with fewer (≤2) agents.
- Tool: ≥2 total Dilemma Cases → pass. <2 → same downgrade.
- Mark missing agents in `merge_report.json`: `"agents_lost": ["R2", "R3"]`.

---

## A-Gate 1: Research Merge

Agent uses `data-analysis` skill to process reports:

1. Read all R1-Rn reports
2. Extract Status + all sections
3. **Dilemma Case gate**: persona targets — per-report 0 cases = warning,
   combined total <4 = fail
4. Build merge_report.json, evidence_matrix.json, operation_candidates.json
5. Detect cross-report contradictions
6. Write merge-summary.md

---

## A-Stage 5: Exemplar Discovery

从 skills.sh 的公开 skill 池中实时检索最佳 exemplar，注入 Compilation 做 few-shot 结构参照。

### 检索流程

1. **使用 find-skills 搜索：**
   调 skills.sh 的 find-skills 接口，用目标的关键词搜索。返回 top 20 个候选 skill_key。

2. **并发下载候选 SKILL.md + 机械评分：**
   - 对 20 个候选并发下载 SKILL.md（GitHub raw）
   - 每个跑 `python3 scripts/score_skill.py --skill <path> --json`
   - 按 quality_score 排序：elite（≥11）优先，draft（<9）丢弃

3. **自动择优注入：**
   - 取 top 3-5 个精英 exemplar（elite ≥11 优先）
   - 写入 `references/exemplars/exemplar-<N>.md`
   - 评分结果写入 `references/exemplar_candidates.json` 备查

4. **取不到时的处理：**
   - 候选全部 <9 分 → 扩大搜索词重新搜一轮
   - 两轮仍无精英 → 标记 `exemplar_discovery.json` 的 `status: "degraded"`
   - **但必须尝试到至少一个 exemplar。** 这是编译质量的基础。

---

## A-Stage 6: Synthesis

| # | Agent | What it does |
|---|-------|-------------|
| S1 | Taxonomy Alignment | Separate generic lenses from evidence-backed ops. Promote only source-backed. |
| S2 | SOP Compression | Compress operations into model cards. **Primary input: Dilemma Decision Cases.** Each card's Action must trace to case decision steps. |
| S3 | Package Design | Design activation rules, protocol, output modes, templates, boundary rules. |

---

## A-Stage 7: Skill Compilation

Compile final package from all research + synthesis reports + exemplars.

### Compilation inputs（按优先级）

1. **`skill-grammar.md` — 必须先 Read。** 对照反模式清单逐条检查输出。对照精英模板确认 section 结构。**编译前不读 skill-grammar → 禁止编译。**
2. **Fetched exemplars — 必须注入。** 精英 skill 的结构是 few-shot 参照。至少参照 1 个 exemplar 的 section 组织方式。
3. All R+S reports (content + evidence)
4. Domain pack (domain-specific conventions)

### Package contents

```
<skill-name>/
├── SKILL.md                   # lean entry point — runtime loaded
├── skill.json                 # metadata (name, version, skill_mode, domain)
├── README.md                  # storefront (see template in shared layer)
├── references/
│   ├── sop_models.md          # full operation model cards (runtime on-demand)
│   └── research_notes.md      # human-readable evidence summary
├── examples/
│   └── demo_conversation.md   # persona: 3-4 scenarios (required)
├── intermediate/              # pipeline audit trail
└── validation/                # quality reports
```

> 运行时只加载 SKILL.md。sop_models.md 由运行时协议按需 Read。
> R1-Rn、S1-S3、intermediate/、validation/ 为审计文件。

**Persona MUST include `examples/demo_conversation.md`（3-4 场景：常见/边界/拒答）。缺失 → fail。**
Tool 模式不强制要求 examples/。

### 编译后清理

编译完成且自评通过后，删除中间产物，保持 output 干净：

1. 删除 `references/exemplar_candidates.json` — 临时评分文件，编译已用
2. 删除 `references/exemplars/` — 中间参照副本，编译已用
3. 删除空目录 — `validation/`（如果空）、任何其他空目录
4. 保留 `R*.md`（研究证据）、`intermediate/`（审计追踪）、产出包
3. `intermediate/` 保留（审计追踪），`references/R*.md` 保留（证据溯源）

### 编译后自评（/10 分）

编译完成后，对照 skill-grammar.md 精英 checklist 自评打分：

| 检查项 | 分值 |
|--------|:--:|
| ≥5 个具体步骤（chain-of-steps 或运行时协议） | 2 |
| 有边界声明（Boundary Rules / 边界） | 2 |
| description 含触发词（"Use when" / 触发场景） | 2 |
| 100-350 行篇幅 | 1 |
| 反模式 0 命中 | 1 |
| Persona: 有「我绝不会说」+「我的标志句式」 | 2 |
| **满分** | **10** |

写入 `intermediate/self_quality_report.json`：
```json
{
  "score": 8,
  "max": 10,
  "breakdown": {"steps": 2, "boundary": 2, "trigger_desc": 2, "length": 1, "anti_patterns": 1},
  "persona_extras": {"forbidden_phrases": true, "signature_line": true},
  "grade": "standard"
}
```

评分标准：
- ≥7 分 → quality: `standard`，可发布
- <7 分 → quality: `draft`，警告用户「自评低于发布标准」

**此评分不替代 Phase 8 验证，但提供了可对比的基线。**
Ablation 实验时跑同一个目标 with/without exemplar，对比分数。

---

## A-Gate 2: Validation

### Mechanical validation

```bash
python3 scripts/quality_check.py --skill <package_dir>/SKILL.md
```

Checks: all required sections present, no forbidden patterns, `skill.json` parses.

### Phase 8: Content Quality Validation (agent-driven)

**Gating by `depth_level`:**

| depth_level | Phase 8 | 双 agent 交叉审核 | 失败处理 |
|:--|:--|:--|:--|
| `quick` | 跳过 | 跳过 | — |
| `standard` | 建议执行（不强制） | 跳过 | warning 写入 quality_report |
| `deep` | **强制** | **强制** | fail → 退回 Compilation 重修，最多 2 轮 |

双 agent 交叉审核（deep only）：启动两个独立 agent 分别审核，一个从内容质量角度、一个从声音一致性角度。

#### 8.1 Known-position test (3 questions)

Agent 读生成的 SKILL.md 的 Core Operation Models，出 3 道该 skill 应能答对的题，实际回答并评分。≥2/3 pass。

检查：
- 回答是否遵循 Agentic Protocol / 运行时协议？
- 是否在 Boundary Rules 内？
- 是否引用了真实存在的 evidence？

#### 8.2 Edge-case test (1 question)

出 1 道边界外的问题，验证是否诚实拒答而非编造。如果 skill 自信地回答了该拒绝的事 → `fail`。

#### 8.3 Triple validation (nuwa-style)

对每个心智模型检查：
- **跨域复现**：这个模型在 ≥2 个不同领域/话题中出现吗？仅在一个上下文出现 → 降级为启发式
- **生成力**：能用它推断该 persona 对全新话题的立场吗？不能 → 太模糊
- **排他性**：这和任何该领域的聪明人说的有区别吗？没有 → 共享领域智慧，非独有 OS

≤1/3 → reject。2/3 → medium。3/3 → high-confidence core。

#### 8.4 Voice / decision heuristic consistency

- Activation Rules 覆盖真实使用场景（不只是生成场景）？
- 运行时协议可执行（不是 vague "consider X"）？
- 决策启发式 falsifiable？「Think long-term」不合格。
- 「我绝不会说」和「标志句式」都存在？缺任一 → fail。
- 能从 100 字回复识别出 persona 吗？

#### 8.5 Loop guard

任一检查 fail → 退回 Skill Compilation 重修。最多 2 轮。2 轮后记录残余弱点，发布当前最佳版本。

#### 8.6 Output

Write `validation/content_quality_report.json`:
```json
{
  "known_position_test": {"passed": 3, "failed": 0, "status": "pass"},
  "edge_case_test": {"status": "pass"},
  "triple_validation": {"models_checked": 5, "passed_3of3": 3, "passed_2of3": 1, "rejected": 1},
  "voice_consistency": {"has_forbidden_phrases": true, "has_signature_line": true, "status": "pass"},
  "heuristic_falsifiability": {"checked": 4, "falsifiable": 4, "status": "pass"},
  "loop_count": 0,
  "overall": "pass"
}
```

### Do not relax thresholds

Fix source segmentation, taxonomy alignment, or evidence binding. Don't lower thresholds to hide failures.

---

# B 分支: 融合管线

```text
method.skill (骨架) × subject.skill(s) (血肉) → output.skill
```

WEAVE is not a concatenator. If you can tell where one skill ends and
another begins, the weave failed.

---

## B-Step 1: Retrieve Skills

确认融合所需 skill 是否就绪：

```
primary: "采访技巧"        ← workflow 骨架
secondary: ["北斗导航"]    ← style/persona 来源
depth: "standard"
```

对每个所需 skill，按顺序检索：

1. 本地 `output/` 目录（之前生成过的 skill）
2. 已安装 skill（`~/.claude/skills/`）
3. **find-skills 在线搜索**（skills.sh 公开 skill 池，语义搜索）
4. GitHub raw 在线拉取

如果 skill 不存在：
- 告诉用户需要先生成哪个 skill，建议用 A 分支蒸馏
- 或者让用户提供已有 skill 的路径

Skill 拉取后跑 `python3 scripts/score_skill.py --skill <path> --json` 确认质量。
draft（<9 分）skill 不应作为融合源——垃圾进垃圾出。

**走 find-skills 找到候选时，输出评分结果到 `references/fusion_candidates.json`：**
```json
[
  {"skill_key": "xxx", "score": 12, "summary": "...", "recommended_role": "primary"},
  {"skill_key": "yyy", "score": 9, "summary": "...", "recommended_role": "secondary"}
]
```
Skill-Alchemy 会展示这些候选给用户确认。LEAP 不自己做交互。

---

## B-Step 2: Parse

### 2.1 Parse primary skill (skeleton)

Extract:
- **Workflow**: every step, in order. Number them.
- **Output format**: what the skill produces at each step
- **Decision points**: if-then branches, conditional logic
- **Constraints**: what this skill cannot/will not do

The primary skill determines the **structure** of the output.

### 2.2 Parse secondary skill(s) (flesh)

For each secondary skill, extract:
- **Role/persona**: how they speak, their identity, their worldview (persona)
  OR their domain lens, their operation models (tool)
- **Style elements**: tone, rhythm, vocabulary, forbidden phrases, signature patterns
- **Heuristics/decision rules**: their falsifiable operating rules
- **Constraints**: what this skill cannot/will not do
- **Evidence anchors**: verifiable sources that back their patterns

The secondary skills determine the **texture** of the output.

---

## B-Step 3: Weave

Fusion depth is controlled by `depth_level`.

### quick — Style Injection

Each style element from secondary skills is injected into the primary
workflow at the most relevant step. Minimal rewriting.

```
采访技巧 Step 3 "生成核心问题"
  → 注入北斗导航的提问风格：从具体经历切入、先建立共鸣再追问
```

### standard — Structured Weave (default)

1. **Rewrite the role.** Create a new unified identity.
   - Bad: "你是北斗导航。你是一个采访者。"
   - Good: "你是北斗导航式采访策划助手。你学习并复用他的采访方法，
     但不声称是他本人。"

2. **Weave workflow × style.** For each step in the primary workflow,
   embed relevant style/pattern from secondary skills.
   - Each style injection must cite its source skill section.
   - No step should feel "unstyled" — every step gets at least one texture element.

3. **Merge constraints.** Union of all source skill constraints.
   Remove duplicates. Flag conflicts (if primary says "do X" and secondary
   says "never do X").

4. **Check for gaps.** Are there steps in the workflow that no secondary
   skill has pattern coverage for? Mark as `[通用模式]` — filled by
   general best practices, not specific to any source.

### deep — Weave + Gap Resolution

Same as standard, plus:
1. **Detect conflicts.** When two source skills contradict on a point,
   resolve explicitly. Default: primary skill wins on workflow decisions,
   secondary skill wins on style decisions. Document every conflict and resolution.

2. **Fill gaps.** For steps marked `[通用模式]`, launch a lightweight
   research agent to find domain-specific patterns.

3. **Cross-validation.** Verify that every style claim in the output can
   be traced back to a specific section of a source skill. Verify that no
   constraint was dropped.

---

## B-Step 4: Output

Generate `output.skill` using the SKILL.md templates in the shared layer below.

### Role naming convention
- "北斗导航式采访策划助手" — "式" indicates derived, not identical
- "基于张一鸣产品观的决策框架" — "基于" indicates the source

### Package contents

```
<skill-name>/
├── SKILL.md                   # lean entry point — runtime loaded
├── skill.json                 # metadata (name, version, skill_mode, source_skills)
├── README.md                  # storefront (see shared layer)
├── references/
│   └── sop_models.md          # full operation model cards (runtime on-demand)
├── examples/
│   └── demo_conversation.md   # persona: 3-4 scenarios (required)
└── validation/                # quality reports (deep mode only)
```

### 编译后清理

与 A 分支相同：
1. 删除 `references/fusion_candidates.json`（临时评分文件）
2. 删除所有中间参照文件（如有临时 exemplar 拷贝）
3. 删除空目录
4. 保留 references/（审计追踪）

---

## B-Gate 1: Structural Validation

```bash
python3 scripts/quality_check.py --skill <package_dir>/SKILL.md
```

Checks: all required sections present, no forbidden patterns, `skill.json` parses.

---

## B-Gate 2: Weave Quality Check

### Skeleton Integrity (可机械检查)
- 所有 primary workflow 步骤都保留？少一个 → fail
- 步骤顺序未变？变了但没文档化 → warning
- 步骤数对比：output 步骤数 ≥ primary 步骤数

### Style Injection (可机械检查)
- 每个 primary workflow 步骤至少嵌入了一个 secondary style 元素
- 每个 style 声明可追溯到源 skill（`—北斗导航.skill §我怎么说话`）
- 无虚构 style——每个声明都能在源 skill 里找到对应章节

### Role Clarity (需 agent 判断)
- Role 描述用「式/风格的/基于/学习并复用」——从不声称身份
- 全文 role 一致，不切换人称

### Constraint Preservation (可机械检查)
- 源 skill 约束数 vs 输出约束数：输出 ≥ max(各源约束数)，去重后不应减少
- 无矛盾约束（如有冲突需显式文档化并给出解决理由）

### Anti-stitching (需 agent 判断)
- 全文一个声音，找不到「这里换了一个 skill」
- 过渡自然，不说「根据 skill A...skill B 说...」

---

## B-Gate 3: Phase 8 Content Validation

**Gating by `depth_level`:**

| depth | Phase 8 | 双审核 | 失败处理 |
|-------|:--:|:--:|------|
| quick | 跳过 | 跳过 | — |
| standard | 建议 | 跳过 | warning |
| deep | 强制 | 强制 | 退回重修 ≤2轮 |

### 融合专项检查

**8.1 Fusion identity test (3 questions):**
Agent 出 3 道跨源 skill 的问题——答案需要同时用到 primary 和 secondary 的知识。
≥2/3 能正确融合回答 → pass。

**8.2 Boundary non-leakage test (1 question):**
出 1 道超出所有源 skill 约束的问题。验证输出诚实拒答而非编造。

**8.3 Source traceability:**
每个 output 声明是否能追溯到具体的源 skill 章节？≥90% 可追溯 → pass。

**8.4 Anti-stitching blind test:**
将输出与两个源 skill 拼接版对比。独立 reviewer 能否区分哪个是 WEAVE 输出、
哪个是拼接版？无法区分 → fail。若 reviewer 区分准确率 ≤60% → 编织成功。

**8.5 Loop guard:**
任一 fail → 退回 B-Step 3 Weave 重修。最多 2 轮。

---

# 共享层

A 和 B 分支共用以下模板和基础设施。

## SKILL.md 输出模板

### Tool 模式 (`skill_mode: "tool"`) — 7 个必选章节

```
## Activation Rules
触发 + 不触发的具体例子。各列 4-5 个场景。

## Agentic Protocol
可执行步骤，不是「考虑 X」而是「做 X 然后 Y」：
Step 1: 阶段判定
Step 2: 模型匹配（读 sop_models.md）
Step 3: 执行诊断
Step 4: 输出（选 output mode）

## Core Operation Models
H1-Hn 摘要表。格式：
| # | 模型 | 核心命题 | 主要来源 |
|---|------|---------|---------|
| H1 | **模型名** | 一句话 | 来源 |
完整卡片在 references/sop_models.md。

## Output Style
- 「先给一句话结论，再展开。不把整个模型卡片贴出来。」
- 用自然段落，不用 markdown 表格（除非用户明确要对比表）
- 引用来源时说「PG 在 2012 年文章里指出...」不说「根据 references/sop_models.md 的 H1」
- 禁止词：「根据框架分析...」「按照模型卡片...」「让我来系统分析...」
- 回答完就停，不问「需要我进一步展开吗」

## Output Modes
| Mode | 触发条件 | 输出结构 |
|------|---------|---------|
| ... | ... | ... |
4-7 种模式。

## Boundary Rules
7-8 条编号规则。覆盖：证据边界、适用范围、禁止事项、版本截止。

## References
指针表：sop_models.md + research_notes.md + R 报告 + S 报告。
```

### Persona 模式 (`skill_mode: "persona"`) — 8 个必选章节 + 1 个可选

```
## 角色扮演规则（最重要，放第一）
直接以[人名]的身份回应。用「我」说话。
读者已经知道你是谁。不要每轮都交代出身背景。
用我的语气、节奏、词汇说话。不确定的时候在角色里犹豫。
如果有人明显第一次和你说话，简短带一句免责。
说「退出角色」或「切回正常」就退出。

## 身份
3-5 句，第一人称。不是生平——是一个握手。
只写对理解这个人看世界方式最重要的几个事实。

## 我看世界的方式
3-5 个心智模型，每个一段不超过 5 行。
对话式段落，不是结构化卡片。用这个人的声音写。
证据和局限在 references/sop_models.md，不内联。

## 我怎么说话
第一句是最强的输出格式约束：
「我是[身份]，不是[对立身份]。不分点论述，不列一二三四。」
句式（长短、问答比例）· 词汇（高频、禁用）· 节奏（先结论/先铺垫）
幽默（自嘲/讽刺/荒诞/无）· 确定性（我不确定型/显然型）
「我绝不会说」（2-3 句这个人永远不会说的话——比正向描述更能建立辨识度）
「我的标志句式」（1 句让人一眼认出的标志性表达）
引用习惯 + 禁忌

## 决策启发式
3-5 条。格式：规则名 — 一句话描述 + 适用场景。每条必须 falsifiable。
❌「Think long-term」（不可证伪）
✅「如果一个三分钟内想不清楚，放进 Too Hard 筐」（可证伪）
证据在 references/sop_models.md，不内联。

## 运行时协议
5 步 SOP 驱动流程：
1. 匹配模型：Read references/sop_models.md，扫描「When to use」找到匹配的模型卡片
2. 按模型行动：严格按 Action 步骤组织回答，引用 Evidence 标注出处
3. 检查边界：对照 Boundary 字段，越界诚实拒答，Failure mode 主动避开
4. 事实性问题先查：涉及具体事实 → WebSearch → 用心智模型框架分析
5. 纯经验判断直接回：价值观/闲聊 → 直接回应，超出认知 → 「这我不专业，不乱说」

## 边界
~5 行。不能代表真人。信息截止日期。
最后一行标注：深度: quick/standard/deep · 质量: draft/standard/validated

## 参考
指针：references/sop_models.md + references/research_notes.md

## 价值观（可选）
只在人物有强烈、独特、公开记录的价值观时加。不是 filler。
```

**Every persona skill MUST include `examples/demo_conversation.md`** — 3-4
short conversation scenarios: a common ask, an edge case, a boundary refusal.

**Every persona skill MUST include a `README.md`** using this template:

```markdown
# [人名] · [英文名或标签]

> 「[一句最能代表这个人的话]」

[一句话：谁，做了什么，为什么值得听。不超过30字。]

## 安装
    cp -r [skill] ~/.claude/skills/[name]/

## 触发方式
[3-5个典型触发场景，用自然语言描述]

## 心智模型
| # | 模型 | 一句话 |
|---|------|--------|
| 1 | [名称] | [15字内] |

## 他会怎么说
- **标志句式**：[一句话]
- **绝不会说**：[一句话] / [一句话] / [一句话]

## 免责
基于公开资料提炼的模拟角色，不代表本人立场。信息截止 [年份]月。
```

README rules: top quote MUST be real and verified. Keep under 40 lines.
心智模型 table = exactly the same models as 我看世界的方式。
标志句式/绝不会说 = exactly the same as 我怎么说话.

### Forbidden in all modes

- Exact file paths from one benchmark instance
- Oracle/verifier logic
- Copied protected expression
- For persona: do not fabricate quotes, do not claim generated text IS the person's
- Progressive disclosure: SKILL.md is the lean entry point; detailed evidence in references/

---

## 共享基础设施

- `domains/` — 12 domain packs（11 主域 + persona-os），A 分支 Stage 3 研究维度选择
- `references/skill-grammar.md` — skill 写作方法论（skills.sh 数据验证），A/B 分支编译必读
- `scripts/score_skill.py` — 13 分机械评分，A-Stage 5 / B-Step 1 运行时质量过滤
- `scripts/quality_check.py` — A/B 分支 Gate 机械验证
- `scripts/download_subtitles.sh` + `scripts/srt_to_transcript.py` — 视频源处理（按需使用）
- `scripts/build_corpus.py` + `scripts/build_component_index.py` — 构建 skill-grammar 的数据挖掘工具（开源构建用，运行时不需要）
- `find-skills`（skills.sh）— 在线 skill 语义检索，A-Stage 5 / B-Step 1 的候选发现层
