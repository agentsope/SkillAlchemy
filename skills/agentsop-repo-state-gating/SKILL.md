---
name: agentsop-repo-state-gating
version: 0.1.0
description: >-
  A 5-minute gate the coder runs at project kickoff (and again whenever the repo shape
  changes). Classifies the workspace into Greenfield / Brownfield-large / Mid-size-familiar
  / Library-SDK, then maps the state to an agent strategy (autonomy, context primitive, tool
  choice). Use BEFORE picking Cursor vs Claude Code vs Aider, BEFORE turning on repo-map,
  BEFORE writing the first prompt. Skip only if the same repo was gated within the last day
  and nothing changed. Search keywords: greenfield vs brownfield, new project vs existing
  codebase, project setup strategy, legacy codebase agent, where to start a coding agent.
domain: coder-agent meta-strategy
audience: coder-agents (Claude Code / Cline / Cursor / Aider) and the humans driving them
source: aider-sop R4, dify-sop A6 escape-hatch, dspy-sop M3 compile-gate, BMAD greenfield/brownfield, GSD codebase-map, The Brownfield Problem (jjmasse 2026)
---

# Repo-State Gating — 5-Line Decision at Project Kickoff

> 一句话：**agent strategy = f(repo-state)**。先判定 repo 状态，再选工具/上下文原语/自治程度。
> 跳过这一步 = 用错工具，浪费一个小时的上下文。

---

## 1. 何时激活

只在以下时刻跑一次（≤5 分钟）：

- **新会话第一次进入某仓库**（含 `cd` 切到新目录、`git clone` 后第一次启动 agent）
- **仓库形态显著变化**：从空目录跑到 100+ 文件、引入新子系统、merge 一个大 PR
- **agent 选错过工具**之后的复盘（"我为什么开了 Cursor 写 SDK / 用 Aider 起新项目"）
- **被项目经理/同事问到** "你应该用 X 还是 Y" — 给一个 5 行的答复

**不要激活**：

- 同一 repo 当天已经 gate 过 → 复用上一次结论
- 单次脚本性任务（"帮我跑个一次性的数据迁移"） → 跳过，直接干
- 你已经知道答案且仓库状态明显（"这是个三天前刚 `npx create-next-app` 的仓库"） → 仍写下结论，但 30 秒搞定

---

## 2. 核心心智模型

### 2.1 一句话

> **不同 repo 状态，agent 的最佳武器不同**。同一个 prompt 在 greenfield 里能跑通，在 brownfield 里会胡编路径；同一个 Aider 在 brownfield 里发光，在 greenfield 里失去 70% 价值。

### 2.2 四个状态 × 四个杠杆

```
状态                  | 关键约束          | 最大杠杆            | 风险
----------------------+-------------------+---------------------+-------------------
Greenfield            | 没有现成符号      | LM 自治 + scaffolder| 过度设计、目录漂移
Brownfield-large      | 上下文炸 + 风格僵 | repo-map + 严格 /add| 修错文件、违反约定
Mid-size-familiar     | 你脑里有图        | 最小上下文 + /ask   | 多加文件稀释信号
Library / SDK         | 你的代码即 API    | 约定 + test-fix 环  | 破坏向后兼容
```

四个杠杆（按优先级递减）：

1. **上下文原语**：repo-map / scaffolder / docstrings / test runner
2. **自治程度**：full-auto / approve-each-tool / ask-then-code / pair
3. **工具选择**：Claude Code / Cursor / Aider / Cline
4. **范围纪律**：/add 数量、token 预算上限、是否允许 free-roam

### 2.3 错误状态假设的代价

| 假设错 | 症状 | 损失 |
|---|---|---|
| 把 brownfield 当 greenfield | LM 编造路径、违反隐含约定、改错文件 | 1–3 小时回滚 + 信任度 |
| 把 greenfield 当 brownfield | 等不到 repo-map 帮忙（图是空的）、纠结要不要 /add | 启动成本 + 错失 scaffolder |
| 把 library 当一般 brownfield | 改了公共 API 没改 changelog、破坏外部用户 | 隐性 bug，回归测试才能发现 |
| 把 mid-size-familiar 当 brownfield-large | 过度加载文件 / 反复扫 repo-map / token 爆 | 浪费的不是错误，而是 *慢* |

> 引用：Aider 自己声明，"For 'build me a new project from scratch' the repo-map is empty and the safety guarantees provide no marginal value."  [aider-sop-skill/references/R4-anti-patterns.md §1]
> 引用：The General Partnership (2026)："legacy code doesn't come in neat, modular pieces… AI agent must learn the project's established patterns and not break things." [thegeneralpartnership.substack.com/p/a-practical-guide-to-brownfield-ai]

---

## 3. SOP 工作流（5 步，每步 ≤30 秒）

### Step 1 — 三个一次性命令

```bash
git log --oneline | wc -l          # 提交数
git ls-files | wc -l               # 跟踪文件数
ls -la                              # 顶层结构（package.json? pyproject? README? src/?）
```

可选第四个：`git log --since='90 days ago' --oneline | wc -l`（活跃度）

### Step 2 — 五题门禁（每题二选一）

| Q | 选 A | 选 B |
|---|---|---|
| 1. `git ls-files \| wc -l` | < 20 → A | ≥ 20 → B |
| 2. 仓库里有公开/发布 API（PyPI、npm、SDK）？ | 否 → A | 是 → B |
| 3. 你能不打开文件就说出主要模块名？ | 否 → A | 是 → B |
| 4. 一次完整改动通常跨几个文件？ | 1–3 → A | 4+ → B |
| 5. 风格约定写在哪？（CONVENTIONS.md / lint / package.json） | 没写过 → A | 有 → B |

### Step 3 — 状态分类（看 A/B 计数 + 关键信号）

```
Q1=A 且 Q5=A                              → Greenfield
Q2=B（公共 API 存在）                       → Library / SDK
Q1=B 且 Q3=A（不熟）                       → Brownfield-large
Q1=B 且 Q3=B（熟）且 Q4=A                  → Mid-size-familiar
其他                                       → Brownfield-large 兜底（最保守）
```

### Step 4 — 查状态卡片（§4 操作模型），挑工具 + 原语 + 自治度

### Step 5 — 把结论写一行进 chat 或 README

```
[repo-state: brownfield-large] tool=Aider, primitive=repo-map, autonomy=approve-each,
add-budget=2-5 files (<25k tok), convention=CONVENTIONS.md required.
```

> 这一行让 *下一次会话* 也能秒接，省去重新 gate。

---

## 4. 操作模型（8 个 ops）

```
op-1  gate-classify
  trigger: 新会话进入仓库
  rule: 跑 §3 Step 1 三命令 + §3 Step 2 五题 → 输出四态之一

op-2  greenfield-strategy
  trigger: state=greenfield
  rule:
    - 工具: Claude Code / Cursor / 纯 LLM 对话；不要 Aider（repo-map 空）
    - 原语: scaffolder 优先（create-next-app, cargo new, uv init, cookiecutter）
    - 自治: 中-高；让 LM 一次产出多文件骨架
    - 范围: 不限；但每生成 ~10 文件就 commit 一次

op-3  brownfield-large-strategy
  trigger: state=brownfield-large
  rule:
    - 工具: Aider（repo-map 是核心杠杆） / Claude Code（长上下文兜底）
    - 原语: 符号索引 / repo-map / ctags / tree-sitter；先 /ask 再 /code
    - 自治: 低；每个 tool-call / 编辑都 approve
    - 范围: /add 严格控制在 2–5 文件 + <25k tokens [aider edit-errors troubleshooting]
    - 必读: CONVENTIONS.md（不存在就先建）

op-4  mid-size-familiar-strategy
  trigger: state=mid-size-familiar
  rule:
    - 工具: Aider --architect 或 Claude Code（你脑里有图，工具只是杠杆）
    - 原语: 你给定文件 + /read 约定文件；不浪费 repo-map 预算
    - 自治: 中；/ask 先讨论方案，/code 再动手
    - 范围: 1–3 文件，单次 commit

op-5  library-sdk-strategy
  trigger: state=library-sdk
  rule:
    - 工具: Aider --auto-test 或 Claude Code with test runner
    - 原语: test-fix 闭环最高价值；docstring 自动生成；semver 检查
    - 自治: 低；改公共 API 必须人工确认
    - 范围: 不只看本仓 — 同时看 CHANGELOG / migration guide
    - 必备: 写 CONVENTIONS.md（API 命名风格、错误模式、deprecation 节奏）

op-6  state-reclassify
  trigger: 跑了一周后仓库形态明显变了；或工具一直选错
  rule: 重跑 op-1；如状态升级（greenfield→brownfield）则把第一行结论改写

op-7  cross-repo-multi-state
  trigger: monorepo / 多包仓库
  rule:
    - 不跑整仓 gate，跑子目录 gate（cd packages/foo && 跑 op-1）
    - 不同子目录可以有不同状态；agent 进入子目录时切策略
    - Aider 用 --subtree-only；Claude Code 用 cwd 限定

op-8  state-mismatch-rescue
  trigger: 已经开干，发现状态判错
  rule:
    - 立刻 /clear 或新会话，按对的状态重启
    - 不要"将就着用"——错状态下省的 5 分钟 < 错工具浪费的 1 小时
```

完整操作目录见 `intermediate/operation_candidates.json`。

---

## 5. 困境决策案例

### 案例 1 — "boss 让我用 Aider 起个新微服务"

**触发**：项目从零，没 git history，团队主推 Aider。

**5 题门禁**：Q1=A（0 文件）、Q5=A（没写过）、Q3=A（无可言说）→ **Greenfield**。

**结论**：先用 `npx create-next-app` / `cargo new` / `uv init` 把骨架打出来，commit 一次。
**然后**才进 Aider，此时已经有了基础符号 + 约定 + tests，repo-map 才有内容可摸。

**反模式**：直接 `aider --message "建个 Next.js + Postgres + Auth 项目"` —— Aider 的 repo-map 是空的，git 安全保障建立在 *增量编辑* 上，对 *无中生有* 没价值。Paul Gauthier 自己也这么说。[aider-sop-skill/R4 §1]

**教训**：工具偏好 < 状态匹配。Aider 是好工具，但不是 *起步* 工具。

---

### 案例 2 — "继承了一个十年老 Django 仓，要加 OAuth"

**5 题门禁**：Q1=B（800 文件）、Q3=A（不熟）、Q5=B（有 pylintrc + 历史约定）→ **Brownfield-large**。

**结论**：

1. 启动 Aider，**不 /add 任何文件**，直接 `/ask which files implement current auth?`
2. 让 repo-map 告诉你（Aider 在 SWE-Bench Lite 上 70.3% 命中正确文件 [aider 2024-05-22 swe-bench-lite]）
3. 只 /add 它列出的 3 个文件，加 /read CONVENTIONS.md
4. /ask 设计方案 → /code 实施 → /test pytest

**反模式 A**：用 Cursor "全仓索引" 一把梭 —— 索引会过期，向量检索精度不如符号图，且无法 *选择性* 编辑写集合。

**反模式 B**：把 50 个相关文件都 /add 进来 —— token 直接破 25k，模型蒸馏度断崖。

---

### 案例 3 — "维护一个公司内部 Python SDK，加个新方法"

**5 题门禁**：Q2=B（已 pip install 过）→ **Library / SDK**。

**结论**：

1. 主要不是 *写代码*，而是 *守 API*。先看 CHANGELOG、看 deprecation 政策、看 type stubs。
2. Aider `--auto-test`：每次编辑后自动跑 pytest，新方法没测试会立刻暴露。
3. 改公共签名 → 必须人工 review，且更新 CHANGELOG.md 和 docs/。
4. 不动 minor 版本号下的破坏性改动；如必要，加 `DeprecationWarning` + 双路径。

**反模式**：当成普通 brownfield 处理，跳过 semver 检查 / 不更新 docs → 下次用户升级炸了，且 bug 不显式（只是 import 路径变了）。

---

### 案例 4 — "Dify 工作流写到一半，想加自定义 Python 节点"

**5 题门禁**：复杂——Dify 本体是 brownfield-large，但你的 *自定义节点* 是 greenfield。

**结论**：**多状态共存**，跑 op-7。

- 在 Dify 项目里：brownfield-large，按 op-3 走。
- 在你新建的 `dify-plugins/my-plugin/` 子目录里：greenfield，按 op-2 走。

**底线**：Dify 提供 code escape hatch 正是给这种场景 —— 但 escape 出去后那段代码是新写的、独立的，不要把 Dify 编排习惯（visual canvas）带进来。 [dify-sop-skill §A6 escape-hatch]

---

## 6. 反模式与边界

### 反模式

1. **"我总用 X" 偏好驱动**：忽略状态、直接套你最熟的工具。Aider-only 党 / Cursor-only 党都犯这个。
2. **不做 gate，凭感觉**：5 分钟省了，1 小时回滚。
3. **gate 一次定终身**：仓库长大了不重 gate（op-6 就是为这个）。
4. **多状态当单状态**：monorepo 里整仓一把抓，不分子目录（op-7）。
5. **用 "lines of code" 当唯一指标**：1k 行的小 lib 和 1k 行的早期 prototype 完全不同策略。
6. **greenfield 上重武器**：刚 `git init` 就配 Aider + repo-map + CONVENTIONS.md —— scaffolder 一行命令的事，何必？
7. **brownfield 不写约定**：让 LM 反复"猜"项目风格；写一次 CONVENTIONS.md 受益所有未来会话 [aider conventions doc]。
8. **库/SDK 当应用处理**：忽视向后兼容，让 LM "随便重构内部" —— 内部不存在，所有内部都是某用户的实现细节。

### 硬边界

- 本 skill **只决定策略**，不替你写代码。下游：`d-repo-map-skill`（brownfield 大杀器）、`aider-sop-skill`（具体命令）、`scaffolder` 工具集（greenfield）。
- 本 skill **不替代 framework 选型**（A7 框架决策树是另一个 skill）；那是 *写什么*，这是 *怎么进入*。
- 本 skill 假设 *有 git*。Perforce-only / 大量二进制资产场景，repo-map 价值锐减，部分状态判定失效。

---

## 7. 跨框架对照（同一状态 × 不同工具的最佳实践）

| 状态 | Claude Code | Cline | Cursor | Aider |
|---|---|---|---|---|
| **Greenfield** | 强；1M 上下文承载多文件骨架生成 | 中；每个 file-write 要 approve，慢 | 强（officially 推荐 greenfield）[scrimba 2026] | **弱**；repo-map 空，价值缺失 [aider R4 §1] |
| **Brownfield-large** | 强；long-context 兜底 + agent loop | 强；逐步 approve 适合不熟仓 | 中；index 易过期，符号精度 < tree-sitter | **最强**；repo-map + /add 写集合是为此而生 |
| **Mid-size-familiar** | 强；你脑里有图，可以放手让它跑 | 中；approve 摩擦在熟仓里反而是噪声 | 强；ghost-text + composer 顺手 | 强；--architect 模式 + /ask /code 极简 |
| **Library / SDK** | 强；写 docstring + test 的 loop 很顺 | 中；适合人工把关 API 变更 | 中；缺 test-fix 内建闭环 | **强**；--auto-test + per-edit commit 是 SDK 维护的甜区 |

> 决策行：选工具不要看 "哪个最强"，要看 **你的状态下哪个强**。Aider 在 brownfield 是首选，在 greenfield 是反模式 —— 同一个工具。

### 跨 SOP 互引

- 进 brownfield-large → 立刻调 **d-repo-map-skill**（符号索引 SOP）
- 任何状态确定后 → 写 **CONVENTIONS.md**（A2 conventions skill，待蒸馏）
- 多状态 monorepo → 配合 **A3 session-state hygiene**（/clear between subdirs）
- Library 状态 → 配合 **T5 test-fix loop**（待蒸馏）

---

## 引用源

- aider-sop-skill/SKILL.md §1 §6；references/R4-anti-patterns.md §1（greenfield 反模式）
- aider.chat/2024/05/22/swe-bench-lite.html（70.3% 命中数据）
- aider.chat/docs/troubleshooting/edit-errors.html（25k token 阈值）
- aider.chat/docs/usage/conventions.html（CONVENTIONS.md 效果对比）
- dify-sop-skill/SKILL.md（visual-builder + code escape hatch 模式）
- dspy-sop-skill/SKILL.md §1（"task signature 还在每天变就不要 compile" → 状态稳态先于优化）
- thegeneralpartnership.substack.com/p/a-practical-guide-to-brownfield-ai（2026 brownfield 实战）
- jjmasse.com/2026/03/06/the-brownfield-problem（"AI advice ignores your actual codebase"）
- medium.com/@visrow/greenfield-vs-brownfield-in-bmad-method-step-by-step-guide-89521351d81b（BMAD 方法二分）
- docs.bswen.com/blog/2026-04-21-gsd-brownfield-codebase（GSD /gsd-map-codebase 实践）
- github.com/ralfstrobel/agentic-brownfield-coding（Claude Code brownfield scaffolding）
- scrimba.com/articles/best-ai-coding-assistants-2026（Cursor/Claude Code/Aider 2026 对照）
