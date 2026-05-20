---
name: agentsop-context-scope-discipline
version: 0.1.0
description: >-
  Coder-agent working-file budget discipline: keep the editable working set (files you /add
  into writable context) under ~25k tokens, separate "read" from "edit", delegate breadth to
  a read-only repo-map, and drop files once edited. Use when an LLM coder-agent edits
  multiple files, when the working set must stay focused, or when the model starts editing
  the wrong file / missing targets because too much context dilutes attention. Search
  keywords: context window full, agent edits wrong file, too much context, /add /drop files,
  working file budget, context dilution, lost in the middle.
domain: working-file budget management for LLM coder-agents (multi-file editing)
source: aider.chat troubleshooting/edit-errors (25k distraction threshold) + /add /drop discipline; generalized across coder harnesses
audience: coder-agents (Aider/Claude Code/Cursor/Cline/custom) editing multiple files where the working set must stay focused
status: enhancement overlay — sharpens the generic token-budget rule into a coding-agent-specific working-file discipline
type: enhance
overlays: token-budget skills (this adds the coder-agent "only load what you'll edit" rule)
crosslinks: "[[agentsop-repo-map]], [[agentsop-session-state-hygiene]]"
---

# Context Scope Discipline — 只把你要改的文件放进工作集

> 一句话：**编辑代码时，工作文件预算（你 `/add`-ed 进可写上下文的文件）要压在 ~25k tokens 以内**。超过这个量，"more context ≠ better edits"——模型注意力被稀释，开始改错文件、漏看你刚加进去的目标。广度交给 [[agentsop-repo-map]]（只读签名地图），深度只留给"这次真要编辑"的那几个文件。

这是一个**增强叠加技能（enhance overlay）**。它不替代任何"通用 token 预算"建议，而是把那条泛泛的"少塞上下文"打磨成一条 coder-agent 专属的硬规则：**区分"读"与"改"，只把"改"的文件加进工作集**。借用 Aider 的实测阈值——

> "Above about 25k tokens of context, most models start to become distracted." [aider.chat/docs/troubleshooting/edit-errors.html]

---

## 1. 何时激活本技能

下列任一情形成立时，把"工作文件预算纪律"作为该编辑会话的标准约束：

- 任务是**多文件编辑**：rename、抽函数、改 API 签名、加 hook 点——你需要理解 N 个文件，但只会真正修改其中一小部分。
- **agent 正在改错文件**：给出的 diff 落在你没想改的文件上，或编造了不存在的路径。这几乎总是"工作集不对"——目标没加进去，或加了太多无关文件把模型呛晕。
- **上下文窗口在涨**：`/tokens`（或等价物）逼近 25k；响应被截断；长会话里模型"记住了错的东西"。
- 你在大仓库里工作，凭"为了保险全加进去"的本能正在把整个目录、整个 repo 灌进可写上下文。
- 你在写**自建 coder harness**，需要一条明确的"可编辑文件白名单何时收/何时放"的规则。

**不应激活的反面信号**：单文件已知的小改动（工作集天然就是 1）；纯讨论/架构问答（用只读上下文 + [[agentsop-repo-map]] 即可，不进工作集）；非编辑任务。

---

## 2. 核心心智模型

### 2.1 一句话铁律

> **more context ≠ better edits.** 过了约 ~25k tokens 的文件量，模型就开始失焦——**只把你这一轮真要编辑的文件加进工作集，其余的靠 [[agentsop-repo-map]] 顶上。**

### 2.2 "读" vs "改"是两种不同的上下文，需要两种不同的预算

LLM 看到的编辑上下文分三层，**优先级与写权限递减**：

| 层 | 内容 | 写权限 | 预算策略 |
|---|---|---|---|
| 系统提示 + 编辑格式 | harness 固化 | harness | 不可控 |
| **只读上下文** | [[agentsop-repo-map]] 签名地图 + `/read` 的参考文件 + CONVENTIONS.md | 人/agent 配置 | 给"广度"——用地图覆盖全仓，但只放签名不放函数体 |
| **工作集（写集合）** | `/add`-ed 的文件 | LLM **唯一**能编辑的 | 给"深度"——只放这次真要改的，压在 ~25k 以内 |

> **核心区分**：repo-map 给"哪儿"（breadth，签名级，便宜），工作集给"怎么改"（depth，全文级，贵）。把这两种需求混进同一个篮子（"全 `/add` 进来再说"）是本技能要根除的反模式。

### 2.3 25k 是稀释阈，不是上限

25k 不是"塞到 25k 就崩"，而是"过了 25k 编辑准确率开始断崖式下降"。它是个**信号阈**：

- 工作集本身 + 对话历史 + repo-map 都算进这一份预算。
- 文件越多、越大，留给"模型对当前编辑点的注意力"越少。
- 模型越弱，对 25k 越敏感（弱模型"更容易违背系统提示" [aider.chat/docs/troubleshooting/edit-errors.html]）。

### 2.4 "全加进去保险"是错觉——repo-map 已经替你覆盖了广度

凭直觉，"我要理解这 10 个文件才能改对，那就全 `/add`"。实测相反：

> Aider **只靠 repo-map**（不把文件加进工作集）在 SWE-Bench Lite 上仍 **70.3%** 命中正确文件 [aider.chat/2024/05/22/swe-bench-lite.html]。

即"找文件"这件事不需要把文件灌进工作集——只读地图就够了。工作集只为"编辑"存在。把这两件事拆开，是省预算的关键。详见 [[agentsop-repo-map]]。

### 2.5 动态预算：工作集涨，地图就该缩

预算是一份蛋糕，不是各自独立的盘子。`/add` 了正确文件后，[[agentsop-repo-map]] 应自动缩小（"adjusts ... based on the state of the chat" [aider.chat/docs/repomap.html]），把 token 让给真代码。如果你的 harness 不会自动缩地图，编辑期就手动 `--map-tokens` 调小或归零。

### 2.6 与 [[agentsop-session-state-hygiene]] 的分工

本技能管**文件维度**（工作集里有哪些文件）；[[agentsop-session-state-hygiene]] 管**历史维度**（对话历史是否污染当前任务）。二者共用同一份 25k 预算：

- 预算超了，先 `/drop` 不再需要的文件（本技能）；
- 仍然超 / 话题已切换，再 `/clear` 清历史（[[agentsop-session-state-hygiene]]）。
- `/drop` 保历史去文件；`/clear` 保文件去历史；`/reset` 两者都丢。

---

## 3. SOP 工作流

### Phase 1 — 区分"要编辑"和"只要读懂"

任务进来，第一步不是 `/add`，而是分类。对每个相关文件问一句：**"这一轮我会修改它的字节吗？"**

```
会改它的字节        → 候选写集合（稍后 /add）
只需理解它的契约     → 只读：/read，或干脆只靠 repo-map 的签名
不确定改哪些        → 先不加任何文件，进 Phase 2 让 repo-map 帮你定位
```

> 经验法则：写集合目标 **≤ 5 个文件**。超过，多半是任务没拆够。

### Phase 2 — 不知道改哪个？让 repo-map 定位，而不是全加进来

```
> /ask which files implement <feature>?
< [模型基于只读 repo-map 回答候选文件]
```

模型命名出目标后，**你**再决定把哪些加进工作集（Op `locate-then-add`）。"找文件"和"改文件"永远两步走——这是 [[agentsop-repo-map]] 与本技能共享的设计哲学。

### Phase 3 — 只 `/add` 你会编辑的，参考文件用 `/read`

```
/add  src/auth.py tests/test_auth.py     # 这两个会改 → 进写集合
/read src/config.py docs/auth.md         # 只参考，不改 → 只读
```

铁律重申：**少 `/add`，敢 `/drop`**。"为了保险全加"恰恰是让模型改错文件的主因。

### Phase 4 — 编辑过程中持续盯预算

```
/tokens                  # 看当前占用；接近 25k 是黄灯
```

| 信号 | 动作 |
|---|---|
| `/tokens` 逼近 25k | `/drop` 已经改完、不再相关的文件 |
| repo-map 占比偏大 | 调小 `--map-tokens`（目标文件已定，地图可缩） |
| 模型反复改错文件 | `/ls` 检查工作集；`/drop` 多余的，`/add` 缺的 |
| 历史漂移（不是文件问题） | 转交 [[agentsop-session-state-hygiene]]：`/clear` |

### Phase 5 — 一个文件改完就 `/drop` 它

工作集不是"会话期一直累积"的。某文件这一轮的修改告一段落、后续子任务不再碰它——立即 `/drop`。把腾出的预算还给下一批要改的文件。这是把工作集**当滑动窗口**用，而不是当垃圾堆。

### Phase 6 — 任务太大撑不住时，拆，而不是塞

地图也缩了、能 `/drop` 的都 `/drop` 了，预算还是破 25k？这是**任务太宽**的信号，不是预算的问题：

```
1. 进子目录 + --subtree-only（缩小 repo-map 范围，见 [[agentsop-repo-map]] §3）
2. 拆任务：大需求拆成多个收敛子目标，每个子目标一个会话
3. 每个新会话只带它真正要改的那 ≤5 个文件
```

---

## 4. 操作模型

每条给 **Trigger / Action / Output / Evidence**。命令名以 Aider 为参考，行为框架无关。

### Op 1 — `classify(file)` 区分"读"与"改"

- **Trigger**：任何相关文件进入视野。
- **Action**：问"这一轮会修改它的字节吗？"。会改 → 写集合候选；只读懂 → 只读层（`/read` 或仅 repo-map 签名）。
- **Output**：每个文件被标记为 EDIT / READ-ONLY / NAVIGATE-ONLY 三类之一。
- **Evidence**：LLM 只能编辑工作集里的文件 [aider.chat/docs/more/edit-formats.html]；只读 vs 读写是 Aider 的安全边界。

### Op 2 — `locate-then-add(task)` 先定位再加

- **Trigger**：写集合未定，不知道改哪个文件。
- **Action**：把 task + repo-map 喂给 LLM，让它**只命名**候选文件（不直接编辑）；人/agent 再 `/add` 命名出的目标。
- **Output**：≤5 个写集合文件 + ≤3 个只读参考。
- **Evidence**：repo-map 只读即可达 **70.3%** 文件命中 [aider.chat/2024/05/22/swe-bench-lite.html]——定位不需要进工作集。

### Op 3 — `add(files)` 加入工作集（克制）

- **Trigger**：某文件确定这一轮会被编辑。
- **Action**：`/add` 只加该文件。不加"可能会用到"的、不加整目录。
- **Output**：工作集 +1。
- **Evidence**：模型改错文件"几乎总是因为该文件没 `/add` 或你 `/add` 了太多无关文件" [aider.chat/docs/usage].

### Op 4 — `read(files)` 加为只读参考

- **Trigger**：文件需要被理解但不会被改（schema、config、CONVENTIONS）。
- **Action**：`/read`，进只读层，LLM 不能编辑。
- **Output**：只读上下文 +1，写集合不变。
- **Evidence**：Aider `--read` / `/read`；只读层与读写层分离 [aider.chat/docs/usage/conventions.html]。

### Op 5 — `budget_watch()` 监控预算

- **Trigger**：每次编辑回合开始，或感觉模型变笨时。
- **Action**：`/tokens` 看占用分布（工作集 / 历史 / 地图各占多少）。
- **Output**：是否越过 25k 黄灯的判断。
- **Evidence**：25k 稀释阈 [aider.chat/docs/troubleshooting/edit-errors.html]。

### Op 6 — `drop(files)` 改完即释放

- **Trigger**：某文件这一轮修改完成、后续不再碰；或预算逼近 25k。
- **Action**：`/drop` 该文件，腾出预算。
- **Output**：工作集 -1，地图自动回涨补位。
- **Evidence**：`/drop` 是常态操作而非应急；动态预算 [aider.chat/docs/repomap.html]。

### Op 7 — `lean-on-map()` 把广度还给地图

- **Trigger**：你想"全加进来才安心"的冲动；或工作集 >5。
- **Action**：把"只为理解、不为编辑"的文件从写集合移到只读地图（`/drop` + 信任 repo-map）。必要时 `/map` 审计地图已覆盖什么。
- **Output**：更瘦的工作集，广度由签名地图承担。
- **Evidence**：见 [[agentsop-repo-map]]；breadth 用签名、depth 用全文是两种预算。

### Op 8 — `split-task()` 拆任务而非塞预算

- **Trigger**：地图缩了、能 drop 的都 drop 了，预算仍破 25k。
- **Action**：把需求拆成多个收敛子目标，每个新会话只带它要改的 ≤5 个文件。
- **Output**：每会话工作集都在预算内。
- **Evidence**：monorepo 上下文溢出的标准缓解 [aider.chat/docs/troubleshooting/token-limits.html]。

---

## 5. 困境决策案例 (Examples / Scenarios)

### 案例 1 — "我要理解 10 个文件才能改对那 2 个：全加，还是用地图？"

**触发**：一个改动横跨 10 个文件的调用链，但你实际只会修改 2 个（比如改一个 API 签名 + 它的一处实现）。本能是把 10 个全 `/add` 进来"看全"。

**诊断**：你把"理解广度"误当成"编辑深度"。10 个里有 8 个你只需要看签名/契约，不会动它们的字节。

**决策规则**：

| 文件角色 | 数量 | 放哪 |
|---|---|---|
| 真要改字节 | 2 | `/add`（写集合） |
| 需看完整契约/会被这次改动影响、要核对 | 1–2 | `/read`（只读全文） |
| 只需知道"它在哪、签名是什么" | 6–7 | 不加，靠 [[agentsop-repo-map]] 签名 |

**为什么有效**：repo-map 只读即 70.3% 命中正确文件 [aider.chat/2024/05/22/swe-bench-lite.html]——广度不需要进工作集。把 2 个进写集合、地图覆盖其余 8 个，预算从"10 个全文"降到"2 全文 + 8 签名"，编辑注意力集中在真正要改的两处。

**反模式**：10 个全 `/add` → 破 25k → 模型在 8 个无关文件里挑了错的位置改 → 回滚 → 重来。

### 案例 2 — "任务做到一半预算满了，怎么办？"

**触发**：多文件重构进行中，`/tokens` 显示已过 25k，模型开始截断响应、漏看你刚加的文件。

**决策树**（按代价递增，能停就停）：

| 步 | 动作 | 何时停 |
|---|---|---|
| 1 | `/tokens` 看占用分布：工作集 / 历史 / 地图谁是大头 | 找到主要占用者 |
| 2 | 已改完的文件 `/drop`（Op 6） | 工作集回到 ≤5、预算降到 25k 下 |
| 3 | 地图占比大 → `--map-tokens` 调小或归零（目标已定，地图可让位） | 预算回落 |
| 4 | 历史是大头、且话题已切 → 转 [[agentsop-session-state-hygiene]]：`/clear`（保文件去历史） | 历史清掉 |
| 5 | 仍破 25k → 任务太宽：`split-task()`，余下子任务新开会话 | 单会话扛得住 |

**关键认知**：先动**文件维度**（drop / 缩地图），再动**历史维度**（clear），最后才**拆任务**。`/drop` 与 `/clear` 是互补而非二选一——前者是本技能，后者是 [[agentsop-session-state-hygiene]]。

**反模式**：预算满了第一反应是"换更大上下文窗口的模型"。窗口更大不改变 25k 稀释阈——大窗口模型塞到 25k+ 一样失焦。先收工作集，别先换模型。

### 案例 3 — "模型一直改错文件，我该再多加几个文件让它看清吗？"

**触发**：连续几轮，模型的 diff 落在错误文件上。直觉是"它没看够，再 `/add` 几个"。

**诊断**：方向反了。改错文件的两种根因都不靠"加更多文件"解决：

| 现象 | 根因 | 修复 |
|---|---|---|
| 改的文件根本没在工作集里 | 目标没 `/add` | `/add` 目标文件（Op 3） |
| 工作集里文件太多、它挑错了 | `/add` 过量稀释 | `/drop` 无关的，收到 ≤5（Op 6） |

**决策规则**：`/ls` 看现状 → 缺目标就加目标、多余就 drop → 不知道哪个是目标就 `locate-then-add`（Op 2）让地图替你找。**几乎不会**是"加更多文件"能解的。

---

## 6. 反模式与边界

### 常见反模式

1. **`/add` 整个目录**——"这个 feature 在 `src/payments/`，全加"。目录里 90% 的文件你不会改，纯稀释。只 `/add` 那 2–3 个目标文件。
2. **从不 `/drop`**——把工作集当只进不出的垃圾堆。改完的文件不释放，预算单调上涨直到破 25k。`/drop` 是常态操作。
3. **dump entire repo**——"上下文越多越好"，把整仓灌进去。这是 25k 阈值的反面教材；repo-map 的全部意义就是让你**不必**这么做。
4. **用工作集做广度**——把"只为读懂"的文件 `/add` 进可写上下文。读懂用 `/read` 或 repo-map 签名，编辑才用 `/add`。
5. **预算满了先换模型不先收工作集**——更大窗口不改变稀释阈。
6. **混淆 `/drop` 与 `/clear`**——文件多就 `/drop`（本技能）；历史脏就 `/clear`（[[agentsop-session-state-hygiene]]）。用错维度解决不了问题。

### 硬边界

- 本技能**不替代** [[agentsop-repo-map]]：广度（找文件）是 repo-map 的活，本技能管深度（哪些进工作集）。两者配套使用。
- 25k **是经验阈不是物理上限**：具体数字随模型变；强模型耐受更高，弱模型更低。把它当"该警觉"的信号，不是"卡死"的红线。
- 本技能**只管文件维度**：对话历史污染交给 [[agentsop-session-state-hygiene]]；二者共享同一份 25k 预算。
- **单文件已知任务无需本技能**：工作集天然是 1，地图可关。
- 本技能**不保证 100% 不改错**：收紧工作集大幅降低改错率，但定位本身仍有 ~30% 残余误差（repo-map 70.3% 命中的另一面），需人工兜底。

---

## 7. 跨框架对照

同一条"只把要改的文件放进工作集"纪律，四个 harness 各自的接口与默认行为：

| | Aider | Claude Code | Cursor | Cline |
|---|---|---|---|---|
| 加入工作集 | `/add <files>`（显式，仅这些可编辑） | `Read` 工具按需读文件入上下文 | `@file` / `@folder` mention | 按需 `read_file` tool-call |
| 移出/释放 | `/drop <files>` | 上下文压缩 / `/clear` | 移除 mention | tool-call 历史自然滚出 |
| 只读参考 | `/read <file>`（不可编辑） | 读了即在上下文（无读/写区分） | `@file` 同样方式 | 同上，无显式只读层 |
| 广度来源 | tree-sitter repo-map（签名） | Grep/Glob/Read 按需探索 | 全仓 codebase index | 文件树 + 主动读 |
| 预算监控 | `/tokens`（25k 显式建议） | 上下文窗口指示 + 自动压缩 | 闭源 | 上下文长度可见 |
| 写权限边界 | **硬**：仅 `/add` 的可编辑 | 软：能读即能改（用工具白名单约束） | 软：可改任意打开文件 | 软：可改任意读过的文件 |

**关键差异**：

- **Aider** 把"读/写"做成**硬边界**（`/read` vs `/add`），最贴合本技能——工作集就是写白名单。其 25k 阈值是这条纪律的实测来源。
- **Claude Code** 没有显式"工作集"概念：`Read` 进来的文件既可读也可被 `Edit`。本技能在这里表现为**自律**——不要为了"看全"而 `Read` 整个目录；用 `Grep`/`Glob` 定位（相当于 repo-map 的广度），只 `Read` 你要 `Edit` 的文件。`/clear` 与自动压缩对应 `/drop` 的预算回收。
- **Cursor** 用 `@`-mention 选上下文；mention 越多预算越紧。纪律是"@ 你要改的，别 @ 整个 folder 求保险"。
- **Cline** 靠 tool-call 现场读文件，工作集隐式等于"读过的文件集"。纪律是不要在 plan 阶段把一堆文件读进来当背景——读过即占预算。

**统一心智**：无论接口是 `/add`、`@file`、`Read` 还是 `read_file`，规则不变——**进工作集的应当是"这一轮会编辑的文件"，广度交给地图/搜索，预算盯住 ~25k**。

---

## 引用源

主要：
- [aider.chat/docs/troubleshooting/edit-errors.html] — "Above about 25k tokens of context, most models start to become distracted." 本技能的核心阈值。
- [aider.chat/docs/troubleshooting/token-limits.html] — 上下文溢出缓解。
- [aider.chat/docs/repomap.html] — 动态预算："adjusts the size of the repo map dynamically based on the state of the chat."
- [aider.chat/2024/05/22/swe-bench-lite.html] — repo-map 只读即 70.3% 文件命中（广度无需进工作集）。
- [aider.chat/docs/more/edit-formats.html] — 只读 vs 读写上下文边界。
- [aider.chat/docs/usage/commands.html] [aider.chat/docs/usage/conventions.html] — `/add` `/read` `/drop` `/tokens` 命令面。

派生：
- `references/R1-source-evidence.md` — 来源逐条 quote。
- `intermediate/operation_candidates.json` — 操作抽取过程。

关联技能：
- [[agentsop-repo-map]] — 广度伙伴：签名地图给"哪儿"，本技能给"哪些进工作集"。
- [[agentsop-session-state-hygiene]] — 历史维度伙伴：`/drop`（文件）与 `/clear`（历史）共享同一份 25k 预算。
- 上游：本技能是"通用 token 预算"建议的 coder-agent 专属增强叠加。

跨工具（一般认知）：Aider / Claude Code / Cursor / Cline 公开文档与博客。
