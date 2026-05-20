---
name: agentsop-aider
version: 1.0.0
description: >-
  SOP for terminal-based, git-native AI pair programming with Aider (git work-tree + tree-sitter repo-map + edit-format + human-in-loop REPL). Use when editing code in an existing git repo via an LLM, when you need to converge a change to 2-5 files, pick an edit format that fits the model, run architect+editor mode, or wire an auto-test loop.
domain: terminal-based AI pair programming, git-native code editing
source: aider.chat docs + Paul Gauthier's blog + leaderboards
audience: coder-agents and human engineers who edit code via LLMs
---

# Aider SOP — 终端结对编程的操作系统

> 一句话：Aider 是“**git 工作树 + tree-sitter 仓库地图 + 编辑格式 + 人类在环 REPL**”的四元组。理解这四个原语，剩下的都是配置。

## 1. 何时激活本技能

下列任一情形成立时，按本 SOP 进入 Aider 工作模式：

- 任务是**编辑已有 git 仓库**里的代码（不是从零起项目）。
- 你能把改动范围**收敛到 2–5 个文件**，或愿意先用 `/ask` 让模型借助 repo-map 把范围找出来。
- 你需要**逐步可回滚**的修改历史（每次编辑一个 commit，`/undo` 一步回退）。
- 你在**终端**里工作（tmux / 远程 ssh / CI）；或者你在写一个把 Aider 当子进程驱动的 agent。
- 你关心**编辑格式对模型质量的影响**（diff / udiff / whole / patch 的选择问题）。
- 你需要 BYOM（自带模型），跑本地 LLM 或非主流厂商。

**不应激活的反面信号**：见 §6 反模式与边界。

## 2. 核心心智模型

### 2.1 四个原语

```
+------------------+   +------------------+   +------------------+   +------------------+
| 1. Git working   |   | 2. Tree-sitter   |   | 3. Edit format   |   | 4. REPL loop     |
|    tree          |   |    repo-map      |   |    (wire proto)  |   |    (你在环里)    |
|                  |   |                  |   |                  |   |                  |
| - per-edit       |   | - symbol-level   |   | - diff / udiff   |   | - /ask /code     |
|   commit         |   |   summary        |   |   / whole /      |   |   /architect     |
| - /undo          |   | - PageRank over  |   |   patch          |   | - 每轮人手确认   |
| - dirty 文件     |   |   import graph   |   | - 模型适配选择   |   | - 不自主         |
|   先 commit 再编 |   | - 动态预算       |   | - JSON 是反模式  |   |                  |
+------------------+   +------------------+   +------------------+   +------------------+
```

四者缺一不可：
- 去掉 git → 失去回滚与审计；
- 去掉 repo-map → 大仓库里 LLM 找不到正确文件（SWE-Bench Lite 上 repo-map 让 Aider 70.3% 命中正确文件 [aider.chat/2024/05/22/swe-bench-lite.html]）；
- 用错 edit format → 出现“lazy coding”、SEARCH 块找不到、JSON 句法破坏（udiff 在 GPT-4 Turbo 上把 refactor 基准从 20% 拉到 61% [aider.chat/2023/12/21/unified-diffs.html]）；
- 放弃 REPL → 退化为自主 agent，但 Aider 在 SWE-Bench 上恰好证明“人在环 + 多次尝试”比纯自主链路更稳。

### 2.2 LLM 看到的上下文分三层（优先级递减）

| 层 | 内容 | 谁能改 |
|---|---|---|
| 系统提示 + 编辑格式说明 | Aider 固化 | Aider |
| 只读上下文 | repo-map + `/read` 文件 + CONVENTIONS.md | 你（通过 `--read`） |
| 读写上下文 | `/add` 的文件 | LLM **只能编辑**这里的文件 |

> **铁律**：LLM 只允许编辑 `/add`-ed 的文件。这是 Aider 的安全边界。模型“改错了文件”几乎总是因为该文件没 `/add` 或你 `/add` 了太多无关文件。

### 2.3 上下文预算（25k 信号阈）

> "Above about 25k tokens of context, most models start to become distracted." [aider.chat/docs/troubleshooting/edit-errors.html]

把这条当硬约束：超过 25k tokens，编辑准确率断崖式下降。`/tokens` 持续监控。

### 2.4 Repo-map 不是 RAG

repo-map 是 **tree-sitter 提取的符号清单**（类、函数、签名），用 PageRank 在源文件依赖图上排序，**塞给 LLM 当地图**。这不是 embedding 检索。

为什么不用 embeddings：
- LLM 能读签名，但读不懂向量。
- 不需要维护索引/重建/失效；代码改了下次自动重生成。
- `/map` 可以打印出来人工审计，向量做不到。

预算是**动态**的：你不 `/add` 任何文件时，map 占用大；`/add` 了正确文件后，map 自动缩小，省下的 token 给真正的代码。

### 2.5 编辑格式是“模型适配问题”，不是“用户偏好”

| 格式 | 谁用 | 强项 | 弱项 |
|---|---|---|---|
| `whole` | 弱模型 / GPT-3.5 / 应急回退 | 解析最稳，无 merge 错误 | 贵；4k 输出上限会截断 |
| `diff` (SEARCH/REPLACE) | GPT-4o, Sonnet, 多数强模型 | token 高效 | SEARCH 块必须字节匹配 |
| `diff-fenced` | Gemini 系列 | 路径放在 fence 内 | 非主流 |
| `udiff` | GPT-4 Turbo (1106) | 模仿 patch 程序的严格性，降低 laziness | 提示更重 |
| `patch` | GPT-4.1 (OpenAI patch 协议) | 多动作鲁棒 | 模型特定 |
| `editor-diff` / `editor-whole` | architect 模式的 editor 子模型 | 提示更瘦，专注编辑 | 仅在 architect 下有意义 |

Aider 已经对常见模型选好默认值；**只有出现编辑错误时才覆盖**。

> ⇒ **不要**把代码编辑包进 JSON tool-call。所有模型在 Aider 的实测里都因此变差，包括 Sonnet（详见 §5 案例 6 与引文）。

## 3. SOP 工作流

### Phase 1 — Bootstrap（每次会话开始）

```bash
# 0. 在 git 仓库根目录。stash 或 commit 在途修改。
git status

# 1. 选模型（榜单当前前列：gpt-5, claude-3.7-sonnet, o3-pro, gemini-2.5-pro）
#    [aider.chat/docs/leaderboards/]

# 2. 最小启动 — 让 repo-map 帮 LLM 自己找路
aider

# 3. 范围已知 — 直接预加 + 风格文件
aider src/auth.py tests/test_auth.py --read CONVENTIONS.md

# 4. 强思考 + 廉价编辑（architect 模式）
aider --architect --model o1-preview --editor-model gpt-4o

# 5. 自动测试回路
aider --test-cmd "pytest -x" --auto-test

# 6. 巨型 monorepo
cd packages/feature-foo && aider --subtree-only
# 并维护 .aiderignore
```

### Phase 2 — 收敛范围（`/add` 纪律）

```
不知道改哪个文件？
  → /ask which files implement <feature>?     (LLM 用 repo-map 回答)
  → /add 它命名的文件（只加这些）

知道改哪个文件？
  → 启动时 CLI 直接传，或 /add path/to/file.py

需要参考但不允许改的文件（schema, config, conventions）？
  → /read path/to/ref.md
```

铁律重申：**少 `/add`，敢 `/drop`**。`/tokens` 看现状。

### Phase 3 — 讨论再动手（`/ask` → `/code`）

```
> /ask 当前的 auth 怎么实现？如果改成 JWT 会有什么破坏？
< [模型基于 repo-map + 已 /add 的文件作答]

> /ask 那我们用 PyJWT 还是 authlib？给出权衡。
< [...]

> /code 按刚才讨论的方案，把 sessions 改成 JWT。
< [模型给出 diff]
[Aider 自动应用 → 自动 git commit]

> /test pytest
< [失败时模型看到输出并尝试修复]
```

> "Break your goal down into bite sized steps. Do them one at a time." [aider.chat/docs/usage/tips.html]

### Phase 4 — Architect 模式（reasoning ≠ editing）

何时开启：**你最好的 reasoner 编辑能力差**（典型：o1-preview 单独跑 79.7%，搭配 Sonnet 当 editor 拉到 82.7% [aider.chat/2024/09/26/architect.html]）。

| 组合 | Polyglot Pass@2 | 备注 |
|---|---|---|
| o1-preview (architect) + o1-mini (editor, whole) | 85% | SOTA 当时；慢，不适合交互 |
| o1-preview + Sonnet | 82.7% | "entirely practical" |
| Sonnet + Sonnet | 80.5% | 比单跑 77.4% 高 |
| GPT-4o + GPT-4o | 75.2% | 比单跑 71.4% 高 |

启用：`--architect` 或 `/architect`。Aider 自动把 editor 切到 `editor-diff` / `editor-whole`。

### Phase 5 — 验证（lint / test / run）

```
/lint                  # 默认 --auto-lint 已开
/test pytest -x        # 失败时输出回填到 chat
/run npm run typecheck # 输出可选择性回填
/diff                  # 看上一轮的 diff
```

> "Aider will try and fix any errors if the command returns a non-zero exit code." [aider.chat/docs/usage/lint-test.html]

formatter 注意：把会重写文件并返回非零的 formatter 包装在双跑脚本里（第一遍 format，第二遍验证）。

### Phase 6 — 上下文卫生

| 症状 | 操作 |
|---|---|
| `/tokens` > 25k | `/drop` 不再需要的文件 |
| 话题切换 | `/clear`（保留文件，清历史） |
| 想全新开始 | `/reset`（丢文件 + 清历史） |
| 模型反复改错文件 | `/ls` 检查；`/drop` 多余的；`/add` 缺的 |
| 反复 edit format 错误 | `/clear`；换模型；`--edit-format whole` 兜底 |

### Phase 7 — 收尾

- `git log --oneline` 看一次会话的提交链。
- 想压成一个 feature commit：`git rebase -i HEAD~N`（**先保留中间 commit 当 undo 栈，最后压**）。
- 提 PR — 提交信息已经是 Conventional Commits 风格。

## 4. 操作模型（命令速查）

源：[aider.chat/docs/usage/commands.html]

```
/add <files>      把文件加入 chat（LLM 可编辑）
/read <file>      加为只读（LLM 不能编辑）
/drop <files>     从 chat 移除
/ls               列出已知文件 + 标注哪些在 chat 里
/ask <q>          只讨论，不动文件
/code <req>       明确要求改代码（不加前缀也行）
/architect <req>  双模型 architect+editor
/model <name>     切换主模型
/clear            清 chat 历史（保留文件）
/reset            丢文件 + 清历史
/tokens           当前 token 占用
/map              打印当前 repo-map
/diff             上一轮的 diff
/undo             回退最近一次 Aider commit
/commit           为 chat 外的改动生成 commit
/run <cmd>        跑命令，可选回填输出（别名 !）
/test <cmd>       跑测试，失败时回填
/web <url>        抓网页转 markdown 进 chat
/copy             复制最后一条回复
/help <q>         关于 Aider 本身的问题
```

CLI 关键标志：

```
--model X                 主模型
--editor-model Y          editor 子模型（architect 用）
--edit-format whole|diff|udiff|patch
--editor-edit-format ...  editor 子模型的格式
--architect               进入 architect 模式
--read FILE               只读上下文（可多次）
--map-tokens N            repo-map 预算；N=0 关闭
--subtree-only            仅本子目录 + 子树
--auto-lint / --no-auto-lint
--test-cmd CMD --auto-test
--no-auto-commits         关掉自动提交（不建议）
--no-git                  完全脱 git（失去安全保障）
--message "..."           一次性非交互模式（脚本/agent 用）
--yes                     全部确认（脚本/agent 用）
```

配置文件：`.aider.conf.yml`（持久 CLI 默认）、`.aiderignore`（排除 repo-map 路径）、`CONVENTIONS.md`（用 `--read` 加载）。

## 5. 困境决策案例 (Examples / Scenarios)

### 案例 1 — “模型一直改错文件”

**触发**：LLM 改的不是你想改的文件，或编造路径。

**诊断**：LLM 只能安全编辑 `/add` 的文件。要么目标没 `/add`，要么 `/add` 太多导致干扰。

**决策规则**：
1. `/ls` 看现状。
2. 缺目标 → `/add path/to/target.py`。
3. 太多文件（>4–5 或 tokens > 25k）→ `/drop` 无关的。
4. 不知道哪个文件 → `/ask which file implements X?`，让 repo-map 替你答。

**为什么有效**：`/add`-ed 文件就是写集合（write-set）。repo-map 只是可读地图，不是写集合。

### 案例 2 — “大仓库里上下文炸了”

**触发**：tokens 涨到 25–50k+，响应被截断，模型在 monorepo 上明显变笨。

**决策规则**（从最便宜的做起）：

| 步 | 动作 |
|---|---|
| 1 | `/tokens` 看占用分布 |
| 2 | `/drop` 不再需要的文件 |
| 3 | `/clear` 清聊天历史（保留文件） |
| 4 | `--map-tokens 1024`（或弱模型 `0`） |
| 5 | monorepo：进子目录 + `--subtree-only`；加 `.aiderignore` |
| 6 | 拆任务：每个子任务一个会话 |

**关键认知**：不要“为了保险全 `/add`”。SWE-Bench 数据，**只靠 repo-map** Aider 仍然 70.3% 选对文件 [aider.chat/2024/05/22/swe-bench-lite.html]。

### 案例 3 — “diff 格式不停 hallucinate / SEARCH 块找不到”

**触发**：Aider 报 “SEARCH block not found in file”。

**诊断**：模型给的 SEARCH 文本和文件字节不匹配（空白、前次失败后状态漂移、纯臆造）。

**决策规则**：
1. `/tokens` — 接近 25k 时合规率下降。
2. `/drop` + `/clear` 减负。
3. 升级模型；弱模型“更容易违背系统提示” [aider.chat/docs/troubleshooting/edit-errors.html]。
4. 兜底格式：`--edit-format whole`。贵但稳。
5. 试 `--architect` —— 双步流程对“执行编辑指令”的依从性更高。

**历史教训**：GPT-4 Turbo 上 unified-diff 把 refactor 基准从 **20% 拉到 61%**，并把 “lazy comment” 砍到 1/3 [aider.chat/2023/12/21/unified-diffs.html]。说明 **格式工程的边际收益经常高于换模型**。

### 案例 4 — “architect 模式值得花这个钱吗？”

**触发**：硬推理任务；你有 o1/o3（强 reasoner，但编辑差）。

**决策规则**：

| 情况 | 建议 |
|---|---|
| reasoner 编辑也干净（GPT-4o, Sonnet） | 不开 architect。单跑就行 |
| reasoner 编辑差（o1-preview 单跑 79.7%） | 开 architect：o1-preview + Sonnet → 82.7% |
| 追 SOTA、能等 | o1-preview + DeepSeek/o1-mini whole → 85%（慢，"probably not practical for interactive use"） |
| 例行编辑 | 单跑更快更省 |

**反直觉点**：连 Sonnet 自配 editor 也涨（77.4 → 80.5%）。但 +3pp 是否值翻倍的 token 成本，取决于场景。

### 案例 5 — “Sonnet 写超长被 4k 截断”

**触发**：Claude 3.5 Sonnet 回复在编辑中段截断。

**诊断**：Sonnet 倾向**写太多**——整文件 SEARCH/REPLACE 而不是最小 diff [aider.chat/2024/07/01/sonnet-not-lazy.html]。

**决策规则**：
- 升级 Aider；它已经支持 “multiple 4k token responses... seamlessly combines them” 并加了精简提示。修复后 Sonnet 的 refactor 基准 55.1 → 64.0%。
- 还截断时，手动追加：“Make minimal SEARCH/REPLACE blocks. Do not quote unchanged sections.”

### 案例 6 — “该用 JSON tool-call 包代码吗？”

**触发**：自建 agent 包 Aider 时考虑结构化 tool-call。

**决策规则**：**不要**把代码包进 JSON tool-call。

> "All of the models did worse on the benchmark when asked to return code in a structured JSON response." [aider.chat/2024/08/14/code-in-json.html]

即便用 OpenAI strict mode 强制 JSON 合法，**JSON 里的代码本身**也劣化（更多 SyntaxError / IndentationError）。若 harness 必须 tool-call，把代码塞**单一字符串字段**，并预期质量损失。

## 6. 反模式与边界

### 不要用 Aider 的场景

| 场景 | 替代 |
|---|---|
| **从零起项目**（无 git history、无现有代码） | Cursor 一类，或纯 LLM 对话 |
| **跨千个文件的机械重构** | 先用 sed / AST 工具 / IDE 重构；Aider 收尾语义部分 |
| **不能用 git 的工作流**（Perforce-only、二进制资产） | 别用 Aider；它的安全保障建立在 git 之上 |
| **需要 IDE/浏览器感知**（实时 diagnostics、devtools） | Cline / Continue / Cursor — Aider 看不到 IDE |
| **完全自主的 ticket→PR** | OpenHands / Devin — Aider 是人在环设计 |

### 常见错误

1. **多 `/add` 求保险**——反而干扰模型。`/drop` 才是常态操作。
2. **忽略 repo-map**——以为“模型不知道”就乱加文件。`/map` 看一下它已经知道什么。
3. **architect 模式用弱 editor**——再好的 reasoner，editor 不会写格式也白搭。Sonnet / DeepSeek / GPT-4o 才是合格 editor。
4. **不 `/clear`**——长会话历史漂移会让模型“记住错的东西”。话题切换就清。
5. **关 auto-commit “保历史干净”**——失去 `/undo` 栈。正确做法是事后 `git rebase -i` 压。
6. **CONVENTIONS.md 不写**——风格（用 httpx 不用 requests、加 type hints）反复纠正不如一次写进 `--read CONVENTIONS.md`；formatter 返回非零会搞砸 auto-lint，用双跑脚本包一下。

### Aider 有意不做的事（硬边界）

- 不渲染 IDE（保持终端纯净）。
- 不维护 embedding 索引（repo-map 按需重生成）。
- 默认不自主（人在环是设计哲学，Paul 论证过这是生产力优势）。
- 一会话一仓库（跨仓库需要更高层编排）。
- 无跨会话长期记忆（持久化靠 CONVENTIONS.md、`.aider.conf.yml`、git history 本身）。

## 7. 生态对照

| | Aider | Cline | Cursor | Continue | OpenHands |
|---|---|---|---|---|---|
| 表面 | 终端 REPL | VS Code 扩展 | 闭源 IDE（VS Code fork） | VS Code + JetBrains 扩展 | Web UI + Docker 沙箱 |
| 开源 | Apache 2.0 | 是 | 否 | 是 | MIT |
| 编辑原语 | diff/udiff/whole 文本 + git commit | tool-call + 每步人审 | 内嵌 Composer 多文件 | Edit/Chat/Agent/Autocomplete | 自主 plan→edit→test→PR |
| 上下文 | tree-sitter repo-map + 选择性 /add | 按需 tool-call 读 | 全仓库索引 | RAG | agentic 读 |
| 人审 | 每轮（`/undo` 兜底） | 每个 tool-call | 每次 Composer apply | 每次 edit | 无 |
| Git 集成 | 原生（每编辑一 commit） | 通过终端工具 | 手动 | 手动 | 沙箱里 PR |
| BYOM | 是（100+，经 LiteLLM） | 是 | 受限 | 是 | 是 |

来源：[frontman.sh/blog/best-open-source-ai-coding-tools-2026]、[cline.bot/blog/top-9-cursor-alternatives-in-2025]、[opensourcealternatives.to]、[shakudo.io/blog/best-ai-coding-assistants]。
### 何时选 Aider 而非其他

1. **你住在终端**：tmux + vim/emacs + Aider 是经典栈，零 IDE 切换。
2. **你要 git-clean 历史**：per-edit commit 自动产出可审计提交链。
3. **你在写 agent**：`--message`、`--yes`、配置文件 → 子进程驱动友好。
4. **你关心编辑格式工程**：Aider 在 udiff、architect、JSON-vs-text 上有最多公开实验数据。
5. **你要确定性上下文**：tree-sitter 地图可 `/map` 检查、可复现、无向量库依赖。
6. **任务已收敛**：你知道 2–5 个目标文件。

### 反过来选别的

- **Cline**：要 VS Code 内每个编辑 / shell 命令的逐步确认。Aider 是事后 `/undo`；Cline 是事前 approve。
- **Cursor**：要内嵌 diff 浮层、ghost-text 自动补全、视觉化文件上下文指示。
- **Continue**：要跨 IDE（VS Code + JetBrains）一致体验，要 autocomplete + chat + agent 一体。
- **OpenHands**：要**自主**ticket→PR；issue 进、PR 出。Aider 没瞄准这场景。

### Aider 留给 agent-coder 的研究遗产

即便你选别的前端，Aider 的公开实验是这些决定的参考：编辑格式选择（GPT-4 Turbo refactor 20%→61%）、repo-map 战胜 RAG（SWE-Bench Lite 70.3%）、architect+editor 拆分（79.7%→85%）、JSON-vs-text 劣化、lazy-coding 缓解——具体数据见前文各节。

## 引用源

- [aider.chat/docs/usage.html] [aider.chat/docs/usage/tips.html] [aider.chat/docs/usage/modes.html] [aider.chat/docs/usage/commands.html] [aider.chat/docs/usage/conventions.html] [aider.chat/docs/usage/lint-test.html]
- [aider.chat/docs/repomap.html] [aider.chat/docs/more/edit-formats.html] [aider.chat/docs/git.html] [aider.chat/docs/faq.html]
- [aider.chat/docs/troubleshooting/edit-errors.html] [aider.chat/docs/troubleshooting/token-limits.html]
- [aider.chat/docs/leaderboards/]
- [aider.chat/2023/12/21/unified-diffs.html] [aider.chat/2024/04/09/gpt-4-turbo.html] [aider.chat/2024/05/22/swe-bench-lite.html] [aider.chat/2024/07/01/sonnet-not-lazy.html] [aider.chat/2024/08/14/code-in-json.html] [aider.chat/2024/09/26/architect.html]
- [aider.chat/HISTORY.html]
- [github.com/Aider-AI/aider]（生态对照来源见 §7）
