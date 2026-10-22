# agentsop-claude-code — Claude Code 提效 SOP

一条面向 Claude Code（CLI / IDE / 桌面端）的提效 SOP 技能：把 agentic 会话当稀缺资源管理，用「喂对上下文 → 拆到可验证 → 每次验证 → 控制上下文膨胀」四步提升编码会话的效率与可靠性。

## 这个 skill 教什么

- Claude Code 的 agentic 循环心智模型，以及上下文的三层结构。
- 专用工具（Glob / Grep / Read / Edit）与 Bash 的选择边界。
- 7 步 SOP：建立上下文 → 定位 → 拆任务 → 修改 → 验证 → 上下文卫生 → 收尾。
- 5 个常见决策案例（改动验证、上下文膨胀、子代理取舍、大文件读取、工具选错）。
- 反模式与硬边界（哪些不可逆/对外操作必须授权后才做）。

## 文件结构

```
agentsop-claude-code/
├── SKILL.md                       # 主技能（frontmatter + 6 节，中文 SOP）
├── README.md                      # 本文件
├── references/
│   ├── R1-architecture.md         # agentic 循环 + 三层上下文 + 工具面
│   ├── R2-sop-workflow.md         # 7 步 SOP + 命令速查
│   ├── R3-dilemma-cases.md        # 6 个决策案例
│   ├── R4-anti-patterns.md        # 反模式 + 硬边界
│   └── R5-ecosystem-context.md    # vs Cursor / Aider / Cline / Codex
└── intermediate/
    └── operation_candidates.json  # 提炼出的操作/决策原子，供横向合成
```

## 用法

- **Agent 运行时**：读 `SKILL.md`。frontmatter 的 `description` 是唯一触发机制，包含功能说明与触发关键词（Claude Code、subagent、context、task 等）。
- **横向合成（跨技能）**：读 `intermediate/operation_candidates.json`——每个条目含 `operation` / `trigger` / `decision_rule` / `evidence_cite`。
- **单维度深挖**：打开 `references/R{1-5}-*.md`。
- 安装后可被 Claude Code 按需加载：`npx skills add agentsope/SkillAlchemy/skills/agentsop-claude-code`（合并入仓库后）。

## 依据

- Anthropic Claude Code 官方文档（CLI 命令、CLAUDE.md、权限、子代理、Skills、Memory）。
- 通用 agentic 工作流最佳实践（可验证分解、上下文卫生、验证先行）。

## 边界

- 不修改生产环境/数据库，除非明确授权。
- 不对外发布内容，除非明确要求。
- 提交/推送只按用户要求做。
- 版本更新后，命令/工具以本机 `claude --help` 与官方文档为最终依据。
