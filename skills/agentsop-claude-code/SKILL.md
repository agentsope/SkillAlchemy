---
name: agentsop-claude-code
version: 1.0.0
description: >-
  SOP for efficient Claude Code sessions: manage context deliberately, decompose
  tasks into verifiable steps, locate code with Glob/Grep before reading, edit with
  minimal diffs, and verify every change. Use when working in Claude Code (CLI, IDE,
  or desktop), when a task is large or the context is getting long, when choosing
  between doing work inline versus a subagent, or when the user asks to improve,
  speed up, or debug a Claude Code workflow.
domain: Claude Code agentic coding workflow
source: Anthropic Claude Code documentation + agentic-workflow best practices
audience: coder-agents and human engineers who use Claude Code
---

# Claude Code 提效 SOP — 把 agentic 会话当稀缺资源管理

> 一句话：Claude Code 是「读取 → 工具 → 观察 → 迭代」的 agentic 循环。
> 提效的关键不是更快地写，而是四件事：**喂对上下文、拆到可验证、每次改动都验证、别让上下文膨胀。**

## 1. 何时激活本技能

下列任一情形成立时，按本 SOP 进入工作模式：

- 在 Claude Code（CLI / IDE 扩展 / 桌面端）里做真实编码任务。
- 任务偏大，或你不确定该从哪一步下手。
- 上下文变长、响应变慢、模型开始「忘掉」前面的约定。
- 需要在「自己直接做」和「派子代理（Agent）」之间做选择。
- 用户要求提速、改进、或排查一个 Claude Code 会话。

**不应激活的反面信号**：见 §5 反模式与边界。

## 2. 核心心智模型

### 2.1 会话是稀缺资源

每次会话的上下文窗口有限且有成本，三样东西在消耗它：

1. 读进来的文件（Read 的内容）。
2. 跑出来的命令输出（Bash 的 stdout/stderr）。
3. 累积的历史对话与工具结果。

**效率第一原则：让读进来的每一样东西都值得被读。**
宁可多花一次 Grep 定位到 `file:line`，也不要一次 Read 整个大文件。

### 2.2 Agentic 循环，不是一问一答

Claude Code 是循环：读上下文 → 选工具 → 观察结果 → 决定下一步。
所以给它的指令要让它能「看到结果再判断」，而不是要求一次就输出完美结果；
验证是循环本身的一部分，不是事后附加的动作。

### 2.3 三层上下文

| 层 | 内容 | 谁控制 |
|---|---|---|
| 系统 + CLAUDE.md | 项目记忆、规范、约定 | 你（写进 CLAUDE.md） |
| 会话历史 | 累积的对话与工具结果 | 你（`/clear` / `/compact`） |
| 临时读入 | 本次 Read / Grep 的内容 | 模型按需读 |

**关键：把要反复交代的东西写进 CLAUDE.md，而不是每次在对话里重复。**

### 2.4 工具选择——有专用工具就别用 Bash

| 目的 | 首选 | 别用 |
|---|---|---|
| 按文件名找文件 | Glob | `find` |
| 按内容搜代码 | Grep（ripgrep） | `grep -r` |
| 读文件 | Read（带 offset/limit 定位） | `cat` 整个文件 |
| 精确修改 | Edit（old/new 精确替换） | 整文件重写 |
| 新建文件 | Write | — |

原因：专用工具的结果能进权限系统、能被精确引用为 `file:line`，也更省 token。

### 2.5 权限与安全边界

Claude Code 有权限模式；不可逆的、对外的操作（删文件、覆盖、`push`、发到外部服务）
要先确认。没有明确授权的生产环境改动、对外发布一律不做。

## 3. SOP 工作流（chain-of-steps）

### Step 1 — 建立上下文

- 启动后先看项目有没有 CLAUDE.md；没有且任务复杂，先让模型 `/init` 生成，或用几句话描述项目结构。
- 用 Glob 摸清目录结构，而不是让模型「猜」文件在哪。
- **输出可验证**：你能一句话说清项目布局和本次任务的目标。

### Step 2 — 定位（先搜再读）

- 改代码前：Grep 关键词 / Glob 文件名，定位到具体 `file:line`。
- 读文件用 offset/limit 读相关区间，别整读大文件。
- **输出可验证**：你知道要改哪些文件、哪几行。

### Step 3 — 拆任务（每步可验证）

- 大任务拆成 2–5 个能独立验证的小步。
- 每步结束有个「怎么算做完」的标准：测试过、命令跑通、报错消失。

### Step 4 — 修改（精确、贴合上下文）

- 用 Edit 做最小 diff；匹配周围代码的命名、注释密度、风格。
- 不确定就先 Read 一下再改，不要整文件重写。

### Step 5 — 验证

- 每改一处，跑对应测试/命令确认；失败就把真实输出如实反馈，不装成功。
- 用 `git diff` 自查改动范围，确认没动到无关文件。

### Step 6 — 上下文卫生

- 话题切换或历史太长 → `/clear`；想保留主线但压缩体积 → `/compact`。
- 发现反复读同一大文件 → 让模型改用 Grep / offset 读区间。

### Step 7 — 收尾

- `git status` / `git diff` 确认改动都在预期内。
- 只在用户要求时提交/推送；不擅自 push。

## 4. 决策案例（Examples / Scenarios）

### 案例 1 — 「模型改了半天，怎么确认没改坏？」

**触发**：改动完成，但不确定正确性。

**决策规则**：

1. `git diff` 看实际改动范围。
2. 跑针对性测试/命令验证行为。
3. 失败 → 把真实报错贴给模型修，别让它凭空猜。

### 案例 2 — 「上下文越来越长，模型开始变笨」

**触发**：响应变慢、被截断、模型忘记前面的约定。

**决策规则**（从便宜到贵）：

1. `/clear` 清历史——结论已落到代码里就不怕丢。
2. 把还需要反复用的约定写进 CLAUDE.md。
3. `/compact` 压缩、保留主线。
4. 拆成新会话，每个会话只做一个子任务。

### 案例 3 — 「该自己做，还是派子代理？」

**触发**：任务可拆成多个独立子任务。

**决策规则**：

- 有明确、可独立并行的子任务 → 派 Agent 并行。
- 只是几步查找/读文件 → 自己做，别为了「并行」派一堆代理烧 token。
- 一旦派出去，别自己又做一遍；等结果，再据此推进。

### 案例 4 — 「大文件读不读？」

**触发**：面对一个几千行的文件。

**决策规则**：

- 先 Grep 定位关键词/函数 → Read 带 offset/limit 读区间。
- 只有确定要通读理解时才整读（谨慎使用 allow_large）。

### 案例 5 — 「工具选错了」

**触发**：模型在 Bash 里跑 `find` / `cat` / `grep`。

**决策规则**：引导改用 Glob / Grep / Read——这些能进权限系统、可引用行号、更省上下文。

## 5. 反模式与边界（Boundaries & Limitations）

### 不要做的事

| 场景 | 替代 |
|---|---|
| 盲目 `cat` 整个大文件 | Grep 定位 + Read 区间 |
| 用 Bash 跑 `find`/`grep`/`cat` 找东西 | Glob / Grep / Read 专用工具 |
| 一次塞十几个不相关改动 | 拆成 2–5 个可验证小步 |
| 改完不验证就宣称完成 | 跑测试/命令，报真实结果 |
| 重复交代同样的规范 | 写进 CLAUDE.md |
| 擅自 push / 删文件 / 发到外部 | 明确授权前不做不可逆/对外操作 |

### 硬边界

- 不修改生产环境/数据库，除非用户明确授权。
- 不对外发布内容（会进缓存/索引），除非用户明确要求。
- 提交/推送只按用户要求做，不在默认分支上自作主张。
- 凡声称「完成」必须给出验证证据（测试结果、命令输出），不得凭感觉宣称成功。

## 6. 引用源（References）

- Anthropic Claude Code 官方文档：docs.claude.com / code.claude.com（CLI 命令、CLAUDE.md、权限、子代理、Skills、Memory）。
- 本技能列出的命令/工具以你本机 `claude --help` 与 `/help` 输出为准；版本更新后以官方文档为最终依据。
