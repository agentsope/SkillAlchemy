---
name: agentsop-repo-map
version: 0.1.0
description: >-
  Symbol-level code context for LLM coder-agents: tree-sitter extracts symbols, PageRank ranks them over the cross-file reference graph, and the top class/function signatures are fed to the LLM as a token-budgeted read-only map (not RAG, no vector index, human-auditable). Use when an agent must locate the right files in a large/multi-file repo, when builds/refreshes/scopes a repo-map, or when "model edits the wrong file" needs fixing.
domain: symbol-level code context for LLM coder-agents
source: aider.chat repo-map docs + Paul Gauthier blog + SWE-Bench Lite evidence + cross-tool comparison
audience: coder-agents (Aider/Cline/Cursor/Continue/OpenHands/custom) editing multi-file repositories via LLMs
status: specialized but high-leverage; hits on every multi-file edit
---

# Repo-Map — 让 LLM 在大仓库里找到正确文件

> 一句话：**`tree-sitter` 抽取符号 → 在跨文件引用图上跑 PageRank → 按 token 预算把最重要的 class/function 签名作为只读地图塞进上下文**。它不是 RAG、不维护向量索引、可被人审。Aider 用同样的机制在 SWE-Bench Lite 上把"正确文件命中率"打到 **70.3%** [aider.chat/2024/05/22/swe-bench-lite.html]。

这是一个**工具技能**（tool skill），不绑定 Aider；任何 coder-agent harness 只要能给 LLM 喂上下文，都可以接入或自建 repo-map。
## 1. 何时激活本技能

下列任一条件成立时，将"构建/刷新/使用 repo-map"作为该会话的标准动作：

- 任务涉及 **多文件编辑** 或 **跨文件影响分析**（rename、抽函数、改 API 签名、加 hook 点）。
- 仓库 ≥ ~20 个源文件，或 LLM 无法靠记忆/猜测找到正确目标。
- 你不想（或不能）维护 embedding 索引：环境无 GPU、不允许出仓数据、PR 评审需可追溯证据。
- 你想给 LLM **可审计的导航地图**（vs. 黑盒向量检索）。`/map` 一样的 dump 必须能给人看。
- 多文件编辑后 LLM 反复改错文件、编造路径、SEARCH/REPLACE 找不到目标——典型的"没地图就乱走"信号。
- 你在写**自定义 coder agent**，需要一个"廉价、确定性、即时刷新"的代码 context 原语。

**不应激活的反面信号**：单文件改动且文件已知；任务是从零起项目；二进制资产仓库；非源代码（CSV/data lake）—— 详见 §6。
## 2. 核心心智模型

### 2.1 三个原语 + 两个不变量

```
+----------------------+   +-----------------------+   +-----------------------+
| 1. tree-sitter       |   | 2. cross-file graph   |   | 3. token budget       |
|    symbol extraction |-->|    + PageRank-style   |-->|    (dynamic, shrink   |
|                      |   |    importance rank    |   |    when files added)  |
| - parse, no execute  |   | - nodes = files       |   | - default ~1k tokens  |
| - class / fn / sig   |   | - edges = symbol refs |   | - cap configurable    |
| - works offline,     |   | - PageRank picks      |   | - 0 = disabled        |
|   no LLM call        |   |   "most referenced"   |   |                       |
+----------------------+   +-----------------------+   +-----------------------+
                                       |
                                       v
                       +-----------------------------------+
                       | Output: skeleton text in prompt   |
                       | (NOT a tool-call, NOT a vector)   |
                       |                                   |
                       |   path/to/file.py:                |
                       |     class Auth:                   |
                       |       def login(user, pwd) -> T   |
                       |       def logout() -> None        |
                       |     def hash_password(pwd) -> str |
                       +-----------------------------------+
```

**不变量 A — Skeleton over snippets**：地图只放 **签名/类名/函数名**，不放函数体。LLM 真要看实现，就**让它点名要文件**——这是 read-only navigation aid，不是 retriever。

> "If it needs to see more code, the LLM can use the map to figure out which files it needs to look at." [aider.chat/docs/repomap.html]

**不变量 B — Dynamic budget**：当对话还没加载任何文件时，地图**展开**到上限（给 LLM 最多导航信息）；一旦真的把文件加进可读写上下文，地图**自动收缩**（省下的 token 让给真代码）。

> "Aider adjusts the size of the repo map dynamically based on the state of the chat." [aider.chat/docs/repomap.html]

### 2.2 为什么不用 embeddings/RAG（设计决策）

| 维度 | Repo-map (tree-sitter + PageRank) | Embedding RAG |
|---|---|---|
| LLM 可读性 | 真签名，LLM 能直接推理 | 向量，LLM 看不懂；只能信检索器选出的片段 |
| 索引维护 | 无；每次会话按需重建 | 需要 chunker + embedder + 向量库 + 失效策略 |
| 确定性 | 同代码同输入 → 同地图 | embedding 模型/参数变化 → 检索结果漂移 |
| 可审计 | 一段纯文本，能 `cat`、能 diff、能给 reviewer 看 | 黑盒：哪些 chunk 被选不直观 |
| 出仓风险 | 全本地静态分析 | 通常调用外部 embedding API |
| 失败模式 | tree-sitter 不支持该语言 → 优雅降级 | 语义距离 ≠ 调用关系，错召回 |

**核心判据**：编辑代码的瓶颈是"**找到要改的文件**"，不是"找到语义相近的段落"。LLM 在签名级别上做"我该改哪里"的推理远比让向量替它推理强。

> Aider's repo-map "successfully identified the correct file to edit in **70.3%** of the benchmark tasks." 这一数字**不依赖 embeddings、不依赖代码执行、不依赖网络** [aider.chat/2024/05/22/swe-bench-lite.html]。

### 2.3 LLM 看到的上下文分三层（优先级递减）

| 层 | 内容 | 写权限 |
|---|---|---|
| 系统/编辑格式 | harness 固化 | harness |
| **Repo-map**（本技能） + read-only files + CONVENTIONS | **只读上下文** | 人/agent 配置 |
| Read-write files | LLM 唯一允许编辑的 | 人/agent 显式加入 |

**铁律**：repo-map 是**地图**，不是**写集合**。LLM 看见某个文件在地图里 ≠ 它能编辑它。**写集合永远只由人/agent 显式声明**（在 Aider 里是 `/add`；在自建 harness 里是"可编辑文件白名单"）。这条边界是 repo-map 安全使用的前提。

### 2.4 25k token 的稀释阈

> "Above about 25k tokens of context, most models start to become distracted." [aider.chat/docs/troubleshooting/edit-errors.html]

repo-map **本身就在 token 预算里**。如果地图占太大，反而稀释了真正的源码上下文。所以预算需要"够找路 + 不挤压代码"。经验起点：1k–4k tokens；monorepo 上限 8k；超过就要靠**子目录/ignore 文件**先缩小搜索范围（§3 Phase 4）。

### 2.5 Skeleton-over-snippets 的工程含义

| 选 skeleton | 选 snippets |
|---|---|
| 全仓导航、定位修改点 | 已锁定 ≤5 个文件、想看实现细节 |
| Token 预算紧 | 真的需要函数体语义 |
| 多语言混合 | 单语言、深度分析 |

skeleton 给"哪儿"，snippets 给"怎么"。**永远先 skeleton，再 snippets**——倒过来会把预算烧光、还没找到对的文件。
## 3. SOP 工作流

### Phase 1 — Bootstrap：建图（每会话一次）

```
1. 确认仓库类型：源码 + git 历史。否则不要用 repo-map（见 §6）。
2. 应用 ignore 列表：
     - .gitignore（必）
     - 自定义 ignore（如 Aider 的 .aiderignore；自建 agent 可直接复用）
     - 默认排除：vendor/, node_modules/, dist/, build/, *.min.js, generated/
3. 选定 tree-sitter 语言集：
     - 主流（Python/JS/TS/Go/Rust/Java/C/C++/Ruby/PHP/...) 默认开
     - 小众语言：要么接 grammars，要么留作 fallback（只列文件路径）
4. 设定 token 预算：
     - 小仓库（<200 文件）: 1k–2k
     - 中等（200–2000 文件）: 2k–4k
     - Monorepo（>2000 文件）: 4k–8k + 限定子目录
5. 首次运行：构建符号表 + 引用图 + PageRank。后续增量更新。
```

输出物：一段纯文本骨架（path + 类/函数签名），符合 token 预算。

### Phase 2 — Use：让 LLM 用地图回答"改哪里"

**反模式**：人类拍脑袋决定加哪些文件 → 漏文件、加多文件。

**正确模式**：把"定位"问题外包给 LLM + repo-map。

```
[harness 提供给 LLM 的上下文]
- system prompt
- repo-map skeleton (read-only)
- task: "Add JWT-based auth replacing session cookies"

[LLM 输出]
- 候选目标文件: src/auth.py, src/middleware.py, tests/test_auth.py
- 候选只读引用: src/config.py, docs/auth.md
```

然后 harness 才把 LLM 命名的文件**真正加入写集合**。这一步是 repo-map 的**唯一**调用价值：把"navigation"从人脑卸载给 LLM。

### Phase 3 — Refresh：何时重建地图

| 触发 | 动作 |
|---|---|
| 会话开始 | 全量构建 |
| 文件被编辑（包括 LLM 自己改的）| 增量更新该文件的符号表 |
| 用户切到不同子目录 | 局部重建（限定 root） |
| LLM 报告"找不到 X 函数"但 X 应该存在 | 强制刷新（如 Aider 的 `--map-refresh always`）|
| 大规模重构（rename across files）| 重构完成后全量重建一次，避免地图与现实漂移 |

**关键认知**：地图过期的代价不是错，是**幻觉**——LLM 会以为某符号还存在/还在某处。每次 LLM 报告"找不到 X"时，第一反应是"地图过期了吗？"，第二反应才是"真的不存在吗？"

### Phase 4 — Scope：地图也撑不住时

地图 > 8k token 仍然稀释信号？这是仓库太大、问题太宽的信号，不是地图的问题。逐步收缩：

```
1. Subtree-only: 把工作目录定到 packages/feature-foo/，只对这棵子树建图。
2. Ignore 扩展: 把 generated/、proto/、vendored/、test fixtures 全 ignore。
3. Domain split: 一次会话只覆盖一个领域（auth / payment / search 三选一）。
4. Map-tokens 0: 已经知道改哪些文件 → 直接关闭地图，节省所有 token 给代码。
5. 拆任务: 大需求拆成多会话，每会话一个收敛子目标。
```

**判断阈**：如果你不能在一句话内描述"这次任务影响哪一类模块"，那 repo-map 帮不了你——先用 `/ask` 类讨论 narrow 任务范围，再激活地图。

### Phase 5 — Audit：把地图当可审计文物

repo-map 的最大优势是**可以打印给人看**：

- `/map` (Aider) 或等价的 `dump_map()` 钩子：用于 reviewer 复现"LLM 看到了什么"。
- 把当次 repo-map 存到 `intermediate/repo-map-<sha>.txt`，作为 PR 附件——比 "trust the agent" 强。
- 当 LLM 决策可疑时，diff 两次地图：是地图变了，还是 LLM 推理变了？
## 4. 操作模型（通用操作，去 Aider 化）

每条操作给 **Trigger / Action / Output / Evidence**。命令名是参考，实际接口取决于你的 harness。

### Op 1 — `map.build(root, budget, ignore)` 构建/重建

- **Trigger**：会话开始；或大规模重构后；或切换工作根。
- **Action**：遍历 `root` 下所有匹配 tree-sitter 的源文件 → 抽符号 → 建跨文件引用图 → 跑 PageRank → 按 `budget` 截取顶部 → 渲染 skeleton。
- **Output**：纯文本，形如 `path:\n  class X:\n    def foo(a: T) -> U`。
- **Evidence**：[aider.chat/docs/repomap.html] "concise map … includes the most important classes and functions along with their types and call signatures"。

### Op 2 — `map.refresh(files)` 增量刷新

- **Trigger**：某文件被 LLM 或人编辑；或 LLM 提示"找不到符号"但应存在。
- **Action**：只对 `files` 重抽符号，更新引用图边集，重跑 PageRank（局部）。
- **Output**：新的 skeleton。
- **Evidence**：Aider `--map-refresh` 文档；动态预算"adjusts ... based on the state of the chat" [aider.chat/docs/repomap.html]。

### Op 3 — `map.scope(subtree | glob)` 缩范围

- **Trigger**：monorepo；或仓库 > 2000 文件；或地图 > 8k token。
- **Action**：把 PageRank 跑在 `subtree` 内或 glob 命中的文件上，根之外的文件最多保留路径不渲染签名。
- **Output**：更瘦的 skeleton。
- **Evidence**：Aider `--subtree-only`；`.aiderignore`。

### Op 4 — `map.print()` / dump 可审计

- **Trigger**：reviewer 要求；或决策不解；或写 PR description。
- **Action**：直接打印当前 skeleton。
- **Output**：plain text，存 `intermediate/repo-map-<sha>.txt`。
- **Evidence**：Aider `/map`。"deterministic & inspectable"（地图是确定性产物，不是模型采样）。

### Op 5 — `map.locate(task_description)` 让 LLM 找文件

- **Trigger**：任务进来但写集合未定。
- **Action**：把 `task_description` + repo-map 喂给 LLM，要求输出"目标文件 + 引用文件"两组路径。**不让 LLM 直接编辑**，只让它命名。
- **Output**：候选文件列表（建议 ≤5 个写集合 + ≤3 个只读）。
- **Evidence**：SWE-Bench Lite 上 repo-map 让 Aider **70.3%** 命中正确文件 [aider.chat/2024/05/22/swe-bench-lite.html]。

### Op 6 — `map.budget_set(N)` / `map.disable()` 调预算

- **Trigger**：上下文超 25k；或目标文件已锁定（地图无用）。
- **Action**：缩小或归零 `--map-tokens` 等价物。`N=0` 等于完全关闭。
- **Output**：更瘦上下文。
- **Evidence**：Aider `--map-tokens`；25k 阈值 [aider.chat/docs/troubleshooting/edit-errors.html]。

### Op 7 — `map.ignore_add(patterns)` 加排除

- **Trigger**：地图被 `node_modules` / `generated/*.pb.go` 类垃圾撑大。
- **Action**：写入 ignore 文件（`.aiderignore` / 等价物）；下次构建生效。
- **Output**：更聚焦的地图。
- **Evidence**：Aider 文档；通用做法。

### Op 8 — `map.diff(prev, curr)` 地图差分

- **Trigger**：怀疑地图过期；或大规模 rename 后审计；或调试 LLM 反复改错文件。
- **Action**：对比两次 skeleton 文本 diff。
- **Output**：新增/消失/重命名的符号列表。
- **Evidence**：repo-map 是文本 → 任何 diff 工具都能跑。这是 embedding 系统**做不到**的可观测性。
## 5. 困境决策案例 (Examples / Scenarios)

### 案例 1 — Repo too big：地图撑大了反而稀释信号

**触发**：monorepo 10k+ 文件；首次 `map.build` 出来的 skeleton 接近 8k token，主对话快要破 25k。LLM 开始忽视细节、编辑跑偏。

**症状**：
- `/tokens`（或等价物）显示 map 占比 > 40%。
- LLM 答非所问，给出的修改散在十几个文件里。
- 25k 阈值越线，模型注意力分散 [aider.chat/docs/troubleshooting/edit-errors.html]。

**决策树**（按代价递增）：

| 步 | 动作 | 何时停止 |
|---|---|---|
| 1 | `map.ignore_add(generated/, vendor/, *.pb.*)` | 大宗噪声砍掉后预算降到 4k 以下 |
| 2 | `map.scope(packages/foo)` 限子树 | 你确知改动只在该子树 |
| 3 | `map.budget_set(2k)` 直接砍预算 | 你愿意接受"少看签名换出空间" |
| 4 | `map.locate(task)` 让 LLM 先用大图找一次目标文件，**然后 `map.disable()`** + 只保留这些文件 | 一旦锁定写集合 |
| 5 | 拆任务、新开会话 | 单会话扛不动 |

**反模式**：把地图开到 16k 期望"看全"——LLM 会被噪声呛死。**地图不是越大越好**；它的价值是"navigation precision per token"。

**为什么这有效**：repo-map 的 PageRank 已经在按重要性排序，预算砍掉的是**长尾低相关符号**，不是核心 API。再加 ignore 排除生成代码，信噪比改善是非线性的。

### 案例 2 — Wrong file edited：LLM 改了不该改的文件

**触发**：LLM 给出 diff，但目标文件根本不是用户想改的；或更糟，编造了不存在的路径。

**症状**：
- 提交回滚 → 反复发生。
- 文件路径在地图里压根没出现 → 模型在幻觉。
- 文件路径在地图里出现 → 但语义其实不对应该改的位置。

**根因诊断**：

| 现象 | 根因 | 修复 |
|---|---|---|
| 路径不在地图 | 地图覆盖不够 / 该路径被 ignore / 文件刚加未刷新 | `map.refresh` / 缩窄 ignore / 检查 tree-sitter 是否支持该语言 |
| 路径在地图但 LLM 选错 | 地图够，**写集合策略错**：让 LLM 自己挑写哪个 | 改流程：让 LLM **命名候选**，人/agent **决定写集合**（Op 5） |
| 地图过期（昨天那次会话留下） | 上次大重构后未刷新 | `map.build` 全量重建 |
| 多个同名 class/function | PageRank 无法区分谁更"正确" | 增加 read-only context（CONVENTIONS / 模块 README）澄清；或 `map.scope` 限定 |

**决策规则**：
1. **永远把"找文件"和"改文件"分两步**。LLM 找，harness 决定是否把找到的文件加进写集合。Aider 的设计哲学：写集合只由人/agent 显式声明，地图只是参考。
2. 如果你在自建 harness 跳过了第 1 步（直接让 LLM 在地图基础上 edit anywhere）——**这是 Aider 实测最常翻车的姿势**。

**评估指标**（值得加进 harness）：
- 命中率：`(LLM 命名的目标文件 ∩ 实际应改文件) / 实际应改文件`。Aider 在 SWE-Bench Lite 上是 70.3%——你的 harness 应该作为下限基准。
- 编造率：`LLM 命名但仓库不存在的路径 / LLM 命名总数`。> 5% 说明地图过小或过期。

### 案例 3 — 多语言混合仓库：tree-sitter 部分语言不支持

**触发**：repo 是 Python + Rust + 一份 Terraform + 一份 Bash。tree-sitter 主流语言抽得出符号，HCL 和 Bash 抽不出。

**决策**：
- 对支持的语言走完整 symbol skeleton。
- 对不支持的语言**保留文件路径**，可选地用启发式正则抽顶级标识符（function/class/resource 关键字）。
- 在 SKILL 提示里告诉 LLM："以下语言的文件只列了路径，需要看实现请明确点名"。
- 不要为了"完整"硬上一个粗糙的 fallback——粗糙 fallback 比没 fallback 更容易误导。

### 案例 4 — 频繁变动的代码库：地图刷新成瓶颈

**触发**：LLM 每分钟编辑一次，每次全量重建 PageRank 太慢。

**决策**：
- 增量刷新策略：只更新被编辑文件的符号，PageRank **只在跨文件引用边变化时**重跑。函数体改但签名没变 → 不重跑 PageRank。
- 文件级缓存：(file path, mtime) → parsed symbols。
- 后台异步刷新：编辑后立即返回旧地图给 LLM，刷新在下一回合到来前完成。
- 接受小段窗口的"地图微滞后"——一两秒的滞后不会让 LLM 找错文件；分钟级滞后才会。
## 6. 反模式与边界

### 不应使用 repo-map 的场景

| 场景 | 替代 |
|---|---|
| 单文件已知任务 | 直接 `/add` 该文件，`map.disable()` |
| 从零起项目 | 没有现有符号可建图 |
| 二进制 / 数据仓库 | tree-sitter 不解析；用 schema/metadata 替代 |
| 不允许静态分析的合规环境 | 罕见但存在（敏感代码）；退回手动文件清单 |
| 任务跨多仓库 | repo-map 是单仓原语；多仓需要更高层"项目地图"编排 |
| 自然语言/文档仓库（pure markdown） | tree-sitter 没有意义；用文件树 + headings 索引 |

### 常见错误

1. **把地图当写集合**——LLM 看见某文件 ≠ 该文件可编辑。永远显式声明写集合。
2. **首次失败 → 加大预算**——预算 8k → 16k 通常恶化结果（稀释）。先 ignore + scope，再考虑加预算。
3. **不刷新地图**——大重构后地图过期 → LLM 全程在用旧符号推理。每次大改后强制全量重建。
4. **混淆 repo-map 与 RAG**——别用向量库替换它，也别在它之上叠一层 embedding 重排（除非你测出收益）。它们解决不同问题：repo-map 给签名，RAG 给实现片段。
5. **把不支持的语言硬塞进 skeleton**——粗糙正则提取出来的"符号"经常误导 LLM。**留路径不留假符号**。
6. **地图开了就不审计**——`map.print()` 是工程师工具，不是装饰。每次决策可疑都该 dump 一次。
7. **对 monorepo 用全局 PageRank**——跨 package 边过多，重要性会被无关 package 稀释。用 `map.scope` 限定到当前工作 package。

### 硬边界

- repo-map **不替代 IDE 的 go-to-definition**：它只给 LLM 看的近似，不给你点击。
- repo-map **不做语义理解**：它只看"这个符号被多少地方引用"。一个被滥用的 helper 也会排名靠前。
- repo-map **不是 100% 命中**：70.3% 是 SWE-Bench Lite 的 Aider 数字。剩下 30% 仍需人/agent 兜底（提供 `--read` 额外提示，或人工指定文件）。
- repo-map **只在 git-tracked 文件上工作**（多数实现）：未跟踪的草稿不会出现。
## 7. 跨框架对照

### 7.1 同问题，四种工程解

| 维度 | repo-map (Aider) | Embedding RAG (LlamaIndex/Chroma + 代码 chunker) | Cursor codebase index | Cline file tree + 按需读 |
|---|---|---|---|---|
| 抽取方式 | tree-sitter 符号 | 文本 chunk + embedding | 闭源（多数推测含 embedding + AST） | 不抽取；只列文件树 |
| 选择算法 | PageRank on import graph | cosine similarity / hybrid BM25 | 闭源 | LLM tool-call 现场读 |
| LLM 看到的 | 真签名 skeleton | 文本片段 | UI 内部使用 | 文件树 + LLM 主动 `read_file` |
| 索引存储 | 无（内存重建） | 向量库（持久） | 云端 | 无 |
| 索引更新 | 文件 mtime 增量 | 需 re-embed | 后台同步 | 不需要 |
| 出仓数据 | 否（全本地） | 通常调外部 embedding API | 是（代码上云） | 否 |
| 可审计 | 文本 dump | 难（chunk 排序不直观） | 黑盒 | tool-call 历史可读 |
| 失败模式 | 长尾符号被砍 | 语义近 ≠ 调用关系，错召回 | 不可知 | 多轮 tool-call 拖慢 + 上下文膨胀 |
| 多文件命中率（公开数据） | 70.3% (SWE-Bench Lite) | 无对应公开基准 | 无公开 | 无公开 |

### 7.2 选择决策

| 你的约束 | 选 |
|---|---|
| 不能出仓、需要可审计、tree-sitter 覆盖你的语言 | **repo-map** |
| 文档/规格/non-code 大量参与 | **Embedding RAG**（或 repo-map + RAG 并存） |
| 你住在 VS Code、要 UI 体验、能接受闭源/上云 | **Cursor codebase index** |
| 你要 step-by-step tool-call 审批 | **Cline 文件树 + read_file**（牺牲 token 换可控） |
| 你在写完全自主 agent | repo-map 作为 base + agent 的 plan 阶段查它（OpenHands 类思路） |

### 7.3 组合使用

repo-map 和 RAG **不互斥**：
- repo-map：定位"改哪里"（基于结构）。
- RAG：找"语义相关的文档/历史 commit message/ADR"（基于自然语言）。

合理组合：repo-map 决定 write-set，RAG 提供 read-only references。**不要倒过来**——让 embedding 决定写集合是已知的失败模式（Aider 实验得到的负面证据）。

### 7.4 给 agent 框架作者的研究遗产

1. **签名 > 片段**：在编辑任务上，符号级 skeleton 是更高 ROI 的上下文形态。
2. **可解释 > 黑盒**：可 dump 的地图让 reviewer 信你的 agent。
3. **找文件 ≠ 改文件**：把 navigation 和 write authorization 拆成两个原语。
4. **70.3% 是基线**：你新设计的 retrieval 机制如果在 SWE-Bench Lite 上打不过它，不要发明轮子。
5. **token 预算是 first-class**：repo-map 内嵌的动态预算是少有的"上下文工程"实例，值得借鉴到非代码场景。
## 引用源

主要：
- [aider.chat/docs/repomap.html] — repo-map 设计与使用
- [aider.chat/2023/10/22/repomap.html] — 初始设计博文：tree-sitter + graph ranking
- [aider.chat/2024/05/22/swe-bench-lite.html] — 70.3% 文件命中率数据
- [aider.chat/docs/troubleshooting/edit-errors.html] — 25k token 注意力衰减阈
- [aider.chat/docs/more/edit-formats.html] — 上下文层级与编辑边界

派生：
- 同目录 `references/R1-source-evidence.md` — 来源逐条 quote
- 同目录 `references/R2-cross-tool-comparison.md` — 跨工具实现对比详表
- `intermediate/operation_candidates.json` — 操作模型抽取过程

跨工具：
- [github.com/Aider-AI/aider] — 参考实现（Apache 2.0）
- [github.com/grantjenks/py-tree-sitter-languages] — 多语言 tree-sitter 绑定
- 一般认知（不引证）：Cline / Cursor / Continue / OpenHands 公开博客与文档
