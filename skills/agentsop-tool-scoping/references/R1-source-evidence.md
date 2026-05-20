# R1 — Source Evidence

Direct evidence extracted from the source skills, supporting every non-trivial
claim in `SKILL.md`. Inline tags in the skill resolve here.

---

## `[crewai-sop]` — `crewai-sop-skill/SKILL.md`

### §DC-3 — the tool-scoping dilemma (the load-bearing source)
> **DC-3: 工具共享 vs 每个 agent 独立工具集？**
> 场景: 你有 web_search、code_executor、db_query 三个工具，3 个 agent
> (researcher / analyst / reporter)。
>
> 两条路:
> - A. 全部共享 — 每个 agent `tools=[search, exec, db]`。简单但 agent 容易
>   "逛工具" — researcher 也调 code_executor 写代码，违背角色分工。
> - B. 按角色配 — researcher=[search]，analyst=[exec, db]，reporter=[]（纯综合）。
>   职责更清晰，错误更可定位。
>
> 判断规则:
> - CrewAI 官方推荐 B（write once, use everywhere — tool 定义可复用；但每个 agent
>   只绑定其角色匹配的工具）
> - 如果发现 agent 跨工具滥用 → 收紧工具白名单是最快的 fix
> - 工具定义层面共享（同一个 BaseTool 类），但绑定层面按需

**What it grounds**: the entire definition-vs-binding split (§2, OP-1, OP-3,
DC-1); the zero-tool reporter (OP-5); tighten-whitelist-as-fastest-fix (OP-7);
blanket-share anti-pattern (AP-1).
Source cited in skill: `docs.crewai.com/en/concepts/tools`,
`community.crewai.com/t/tool-best-practice-assign-to-agent-or-task/5919`.

### §DC-1 — split-vs-merge an agent
> 当你纠结要不要拆，答案 80% 是拆。CrewAI 的核心红利就在"单一职责角色"。
> "the next trap is putting too much in one agent." [daily.dev]

**What it grounds**: Phase 1 gate, DC-2 option B (split the mega-agent), DC-3
step 3 (under-specified roles).

### §DC-5 — allow_delegation widens effective capability
> 默认 `allow_delegation=False` 在所有 worker agent 上；仅 manager_agent 开
> delegation。

**What it grounds**: cross-framework table note that delegation widens an
agent's effective capability surface beyond its bound tools.

### §6.1 AP-1 — scaling wall as analogy for tool-count
> | AP-1 | Agent 数量爆炸 (>5 个 agent) | 协调失败、token 飞涨、debug 困难 |
> 合并职能近似的 agent；7+ 几乎必拆 Flow |

**What it grounds**: OP-4 and DC-2 — too-many-tools degrades selection by the
same mechanism (overloaded selection space, token inflation) that too-many-agents
degrades coordination.

---

## `[langgraph-sop]` — `langgraph-sop-skill/SKILL.md`

### §Step2 / §Step4 — tools bound to nodes, not globally
> | Standard tool-calling ReAct loop | `create_react_agent` (prebuilt) | ... |
> Step 4 · Choose the multi-agent topology ... control flow is explicit ...
> sub-agents are tools / supervisor routes to specialists.

**What it grounds**: cross-framework mapping (per-node `bind_tools`); OP-1
"binds tools to nodes, not globally"; DC-2 option C (router + scoped sub-agents).

### §Step5 — HITL only on irreversible, high-blast-radius actions
> Use `interrupt(value)` at the node that would perform the high-blast-radius
> operation ... "interrupt on irreversible, high-blast-radius actions only —
> not on every step" `[bswen/hitl]`. Side effects (DB writes, API calls) must
> go after the interrupt.

**What it grounds**: the runtime half of side-effect guarding (OP-2, DC-3,
AP-2); the "tool scoping is the design-time half of the same risk control"
framing in §2.

### §Case4 — side effects before interrupt re-execute (double charge)
> A team built a payment workflow: node A charges the card, then calls
> `interrupt()` ... On resume, the card was charged twice because resuming a
> thread re-runs the entire node function ... every external side-effect uses an
> idempotency key drawn from state.

**What it grounds**: OP-2 idempotency requirement; AP-2 symptom (double-charge on
retry); DC-2/DC-3 destructive-tool blast radius; the cross-links to
`[[agentsop-llm-tool-idempotency]]` and `[[agentsop-http-tool-wrapping]]`.

---

## Cross-link rationale

- `[[crewai]]` — the base framework whose §DC-3 footnote this overlay expands.
- `[[agentsop-http-tool-wrapping]]` — owns *how* a tool's I/O is implemented (out of scope
  here; scoping decides *who holds* the tool, not how it's built).
- `[[agentsop-llm-tool-idempotency]]` — owns *making a side-effectful tool safe to retry*,
  the partner discipline to scoping a destructive tool to a single guarded owner.

## Gap confirmation

Base `crewai` skill frontmatter (`~/.claude/skills/crewai/SKILL.md`) describes
"role-based agent collaboration with memory" and "sequential/hierarchical
execution" — it does **not** name a tool-scoping rubric. The SOP skill mentions it
only in DC-3. No base skill provides a per-agent binding matrix, a tool-count
ceiling, or a single-owner rule for destructive tools. This overlay supplies all
three.
