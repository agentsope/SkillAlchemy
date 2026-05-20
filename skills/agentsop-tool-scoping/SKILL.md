---
name: agentsop-tool-scoping
version: 0.1.0
description: >-
  Enhancement overlay for multi-agent / tool-using coder agents. Encodes the per-agent tool-
  scoping discipline that role-based frameworks (CrewAI, LangChain) document only as a
  passing best-practice: which agent gets which tool, and why blanket-sharing every tool to
  every agent is a correctness and blast-radius risk. Activates when an agent system has
  tools AND there is more than one agent (or one agent holding many tools). Treat a tool as
  a capability grant; scope by least-privilege. ENHANCE overlay — read alongside [[crewai]],
  [[agentsop-http-tool-wrapping]], [[agentsop-llm-tool-idempotency]]. Search keywords: which
  tools per agent, least-privilege agent, agent tool access, tool permissions, limit agent
  tools, scope tools to roles.overlay_type: enhancement
enhances: [crewai, langchain, langgraph]
---

# Tool Scoping · Per-Agent Tool Binding (Least-Privilege Discipline)

> Overlay posture: the base frameworks ([[crewai]], LangChain, LangGraph) all
> *define* tools and *bind* them, but treat scoping as a one-line "assign tools
> to the agent that needs them" footnote. This overlay makes the rubric
> first-class. Non-trivial claims cite inline against
> `references/R1-source-evidence.md`.

The lever the base skills under-surface: **tool definition and tool binding are
two separate decisions.** You define a tool *once* (reusable class/function), but
you *bind* it per-agent deliberately. The [[crewai]] SKILL states this in one
clause — "tool 定义可复用；但每个 agent 只绑定其角色匹配的工具"
`[crewai-sop §DC-3]` — and then moves on. Production failures (wrong-tool
selection, an agent running a destructive op outside its role) come from skipping
the binding decision and defaulting to "give everyone everything."

---

## 1. 何时激活 (When to Activate)

Activate when **any** of these hold:

- The system is **multi-agent** (CrewAI crew, LangGraph supervisor/swarm,
  AutoGen group) AND at least one agent holds ≥1 tool.
- A **single agent holds many tools** (rule of thumb: ≥8 — see OP-4) and tool
  selection has started degrading (picks the wrong tool, or "tool-hops").
- You are **tempted to give all agents all tools** — `tools=[search, exec, db]`
  copy-pasted onto every `Agent(...)`, or one `bind_tools([...everything])` call
  reused for every node. This is the canonical trigger.
- A tool has **side effects** (DB write, payment, email, `DELETE`, shell exec,
  outbound HTTP POST) and you are deciding who may hold it.
- You are doing a **security / blast-radius review** of an agent system and need
  to answer "which agent can do what, and why."

Do **not** activate for: a single agent with 1–3 read-only tools (scoping is
trivial), or a stateless single LLM call with no tools.

---

## 2. 核心心智模型 (Core Mental Model)

**A tool is a capability grant, not a convenience.** Binding a tool to an agent
is the same act as granting a Unix process a syscall, a service an IAM role, or a
container a Linux capability. The discipline is identical and ancient:
**least-privilege — an agent should hold only the tools its role actually
needs.**

Three load-bearing consequences:

1. **Definition ≠ binding.** Define the tool once (a reusable `BaseTool` /
   function); decide the *binding* (which agents see it) separately and
   minimally. [[crewai]] says "write once, use everywhere" applies to the
   *definition* layer only; the *binding* layer is per-role `[crewai-sop §DC-3]`.

2. **Every bound tool is in the agent's selection space, and the model pays for
   it.** The LLM must reason over the full tool list on every turn. More tools =
   bigger schema in context = higher token cost AND lower selection accuracy.
   This is why a 20-tool agent picks wrong (OP-4, DC-2).

3. **Side-effectful tools change the blast radius of a misfire.** A read-only
   `search` tool on the wrong agent wastes tokens. A `run_sql` or `send_payment`
   tool on the wrong agent (or one with no guard) is a production incident. The
   LangGraph HITL discipline — "interrupt on irreversible, high-blast-radius
   actions only" — is the *runtime* half; tool scoping is the *design-time* half
   of the same risk-control `[langgraph-sop §Step5]`.

The mental test before binding any tool to any agent:

> "Does THIS role's goal require THIS capability to be exercised by THIS agent
> autonomously? If a different agent could/should do it, don't bind it here."

---

## 3. SOP 工作流 (Standard Operating Procedure)

A coder agent walks this top-down. Each phase has a gate.

### Phase 0 · Inventory the surface
List every tool (name, side-effect class: `read` | `compute` | `write` |
`destructive`) and every agent (name, one-verb role). If there is exactly one
agent and ≤3 read tools — **stop, scoping is trivial.**

### Phase 1 · Map roles → minimal tool set
For each agent, write its role as a single verb (research / analyze / write /
review). Then, for each tool, ask the §2 test. Bind only on a "yes."
- Default to the **empty set** and add tools, not the full set and remove them.
- A "synthesis-only" agent (writer, reporter) often needs **zero** tools — it
  consumes upstream output `[crewai-sop §DC-3]`.

Gate: if two agents end up with identical tool sets, ask whether they are really
two roles or one (the [[crewai]] "split-vs-merge" question `[crewai-sop §DC-1]`).

### Phase 2 · Guard side-effectful tools
Any tool classed `write` or `destructive`:
- Bind it to **exactly one** agent (single funnel, auditable).
- Pair it with a runtime guard: HITL `interrupt()` before the side effect in
  LangGraph `[langgraph-sop §Step5]`, or an approval/confirm step in CrewAI.
- Make the underlying operation **idempotent** so a retry/re-run is a no-op —
  see [[agentsop-llm-tool-idempotency]] and [[agentsop-http-tool-wrapping]]. LangGraph's payment
  case (charged twice on resume) is exactly this failure `[langgraph-sop §Case4]`.

### Phase 3 · Enforce per-agent tool-count limit
If any agent now holds **>8 tools**, selection accuracy degrades (OP-4). Options:
split the role, group tools behind a router/sub-agent, or move read-only helpers
into the prompt as context instead of tools.

### Phase 4 · Audit
Produce a binding matrix (agents × tools). For each `write`/`destructive` cell,
confirm there is exactly one owner and a guard. For each agent, confirm tool
count ≤ limit. This matrix is the security artifact a reviewer reads.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**.

### OP-1 · Least-privilege role→tool mapping
- **Trigger**: Assembling a multi-agent crew/graph with a shared tool pool.
- **Action**: For each agent, start from `tools=[]`. Add a tool only when the
  role's goal *requires that agent* to exercise it. Reuse the tool *definition*
  across agents, but bind per-role.
- **Output**: Each `Agent(tools=[...])` / per-node `bind_tools([...])` holds the
  minimal set; a binding matrix.
- **Evidence**: `[crewai-sop §DC-3]` "每个 agent 只绑定其角色匹配的工具";
  `[langgraph-sop §Step4]` topology binds tools to nodes, not globally.

### OP-2 · Side-effect tool guarding
- **Trigger**: A tool performs a `write` or `destructive` operation.
- **Action**: Bind it to one agent only. Add a runtime guard (HITL interrupt /
  human approval) before the effect, and make the op idempotent.
- **Output**: A single-owner, guarded, idempotent side-effectful tool.
- **Evidence**: `[langgraph-sop §Step5]` interrupt on irreversible only;
  `[langgraph-sop §Case4]` double-charge from unguarded side effect; cross-link
  [[agentsop-llm-tool-idempotency]], [[agentsop-http-tool-wrapping]].

### OP-3 · Shared-registry vs per-agent binding decision
- **Trigger**: You have a tool registry and N agents and must decide how to wire.
- **Action**: Share at the **definition** layer (one registry of tool classes).
  Decide **binding** per-agent via OP-1. Never `tools=registry.all()` on every
  agent.
- **Output**: One definition source, N minimal per-agent bindings.
- **Evidence**: `[crewai-sop §DC-3]` definition-reuse vs binding-scope split.

### OP-4 · Per-agent tool-count limit
- **Trigger**: An agent's tool list grows (≥8) or it starts mis-selecting tools.
- **Action**: Cap tools per agent (~8 as a working ceiling). If over, split the
  role, introduce a routing sub-agent, or demote read-only tools to context.
- **Output**: Every agent ≤ the ceiling; improved selection accuracy.
- **Evidence**: too-many-tools degrades selection — same root cause as
  CrewAI's ">5 agents = coordination failure" scaling wall `[crewai-sop §6.1 AP-1]`;
  see DC-2.

### OP-5 · Zero-tool synthesis agents
- **Trigger**: An agent only consumes upstream output (writer, reporter, judge).
- **Action**: Bind **no tools**. Feed it context via task `context=[...]`
  (CrewAI) or state (LangGraph).
- **Output**: A tool-free agent that cannot "wander" into capabilities.
- **Evidence**: `[crewai-sop §DC-3]` "reporter=[] (纯综合)".

### OP-6 · Binding-matrix audit
- **Trigger**: Pre-ship review, or security review of an agent system.
- **Action**: Build an agents × tools matrix. Flag any `write`/`destructive`
  tool bound to >1 agent or lacking a guard; flag any agent over the count limit.
- **Output**: A reviewable capability matrix + remediation list.
- **Evidence**: Phase 4; mirrors least-privilege IAM review practice.

### OP-7 · Tighten scope as the fastest misuse fix
- **Trigger**: An agent is observed using a tool outside its role (e.g. a
  researcher invoking a code executor).
- **Action**: Remove the tool from that agent's binding (the whitelist tighten),
  rather than prompt-engineering "please don't use X."
- **Output**: A structurally-prevented misuse instead of a hoped-for one.
- **Evidence**: `[crewai-sop §DC-3]` "agent 跨工具滥用 → 收紧工具白名单是最快的 fix".

---

## 5. 困境决策案例 (Dilemma Cases)

### DC-1 · Shared tool registry vs per-agent tool sets
**场景**: You have `web_search`, `code_executor`, `db_query` and three agents
(researcher / analyst / reporter). The convenient move is
`tools=[search, exec, db]` on all three.

**两条路**:
- **A. Blanket share** — every agent gets all three. Zero wiring thought.
  Problem: the researcher also calls `code_executor` to "just quickly compute,"
  violating role separation; failures become un-localizable (who ran the bad
  query?); every agent pays the full 3-tool schema cost every turn.
- **B. Per-role binding** — `researcher=[search]`, `analyst=[exec, db]`,
  `reporter=[]`. Clearer responsibilities, localizable errors, smaller per-turn
  schema `[crewai-sop §DC-3]`.

**判断规则**:
1. Share at the **definition** layer (one `BaseTool` per tool — reuse is good).
2. Decide **binding** by OP-1: a tool is bound only if the role needs that agent
   to exercise it.
3. If you genuinely cannot say which single agent owns a `write` tool, your roles
   are under-specified — go back to role design `[crewai-sop §DC-1]`.

**红线**: Never let "it's easier to share" be the binding rationale. Ease of
wiring is not a capability requirement.

**Evidence**: `[crewai-sop §DC-3]`, `[langgraph-sop §Step4]`.

---

### DC-2 · The 20-tool agent that picks the wrong tool
**场景**: A single "do-everything" agent accumulates 20 tools over time. It now
calls `delete_record` when the user asked to *read* a record, or burns turns
hopping between near-duplicate tools (`search_v1`, `search_v2`, `lookup`).

**陷阱**: The instinct is to "improve the prompt" so the model picks better. But
the root cause is the **selection space is too large** — 20 tool schemas in
context dilute attention and inflate token cost, exactly as ">5 agents" causes
coordination collapse in CrewAI `[crewai-sop §6.1 AP-1]`. Prompt tweaks paper
over a structural problem.

**三条路**:
- **A. Prompt-engineer the selection** — describe each tool more carefully.
  Helps marginally; does not fix the count.
- **B. Split the agent by capability cluster** — research-agent (search tools),
  data-agent (db/exec tools), each ≤8 tools. Mirrors the CrewAI "split when one
  agent does two jobs" rule `[crewai-sop §DC-1]`.
- **C. Router + scoped sub-agents** — a thin supervisor routes to a sub-agent
  whose small tool set matches the sub-task `[langgraph-sop §Step4]`.

**判断规则**:
1. Tool count > ~8 → suspect the count, not the prompt (OP-4).
2. Duplicate/overlapping tools → consolidate definitions first.
3. Mixed read + destructive tools on one agent → split so destructive tools live
   on a single guarded owner (OP-2), shrinking the dangerous agent's surface.

**红线**: A destructive tool on a 20-tool agent is the worst case — high
mis-selection probability × high blast radius. Scope it out *first*.

**Evidence**: `[crewai-sop §6.1 AP-1]`, `[langgraph-sop §Step4/§Case4]`.

---

### DC-3 · Should a destructive tool ever be shared across agents?
**场景**: Two agents both "occasionally need" to write to the database.

**判断规则**:
1. Default **no** — a `write`/`destructive` tool gets exactly one owning agent
   (single auditable funnel), per OP-2.
2. If two agents truly both need it, the write should usually be **extracted into
   a dedicated single-owner "writer" agent/node** that the others call — not
   duplicated. This is the supervisor-funnel argument applied to capabilities
   `[langgraph-sop §Step4]`.
3. Whichever agent owns it: guard with HITL/approval and idempotency
   ([[agentsop-llm-tool-idempotency]], [[agentsop-http-tool-wrapping]]).

**红线**: Two agents holding the same unguarded destructive tool = two
independent ways to cause the same irreversible incident, and an ambiguous audit
trail.

**Evidence**: `[langgraph-sop §Step5/§Case4]`, `[crewai-sop §DC-3]`.

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

| # | Anti-pattern | Symptom | Fix |
|---|---|---|---|
| AP-1 | **Blanket tool sharing** (`tools=[all]` on every agent) | role bleed, un-localizable failures, inflated token cost | per-role binding (OP-1, DC-1) |
| AP-2 | **No guard on destructive tools** | double-charge / accidental delete on retry or mis-selection | single owner + HITL + idempotency (OP-2, [[agentsop-llm-tool-idempotency]]) |
| AP-3 | **One mega-agent with 20 tools** | wrong-tool selection, tool-hopping, cost | cap ≤8, split or route (OP-4, DC-2) |
| AP-4 | **Prompt-patching tool misuse** | "please don't use X" in backstory | remove the tool from the binding (OP-7) |
| AP-5 | **Sharing the destructive tool itself** instead of the definition | two paths to the same incident | extract single-owner writer (DC-3) |
| AP-6 | **Binding tools to synthesis agents** | writer/reporter "wanders" into search/exec | bind zero tools (OP-5) |

**Boundaries — this overlay does NOT cover:**
- *How* to implement a tool (ret, errors, HTTP wrapping) → [[agentsop-http-tool-wrapping]].
- *How* to make a tool safe to retry → [[agentsop-llm-tool-idempotency]].
- *Runtime* HITL gating mechanics → base LangGraph skill `[langgraph-sop §Step5]`.
- Whether to use multi-agent at all → [[crewai]] / agent-topology selection.
- This is a **design-time scoping rubric**, not a sandbox/permission *runtime*.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

The scoping decision is universal; only the binding syntax differs.

| Framework | Define a tool | Bind per-agent (the scoping point) | Scoping notes |
|---|---|---|---|
| **CrewAI** | `BaseTool` subclass / `@tool` | `Agent(role=..., tools=[search])` — per agent | Definition reusable, binding per-role `[crewai-sop §DC-3]`. `allow_delegation` further widens effective capability — keep it `False` on workers `[crewai-sop §DC-5]`. |
| **LangGraph** | a callable / `@tool` | `model.bind_tools([...])` **per node**, or per `create_react_agent` | Tools bound to the node that needs them, not globally; topology decides who routes to the tool-bearing node `[langgraph-sop §Step2/§Step4]`. Guard destructive tools with `interrupt()` `[langgraph-sop §Step5]`. |
| **LangChain (agents)** | `@tool` / `Tool` | tools list passed to each `AgentExecutor` | Same definition-vs-binding split; the base LangChain docs note "give the agent the tools it needs" but leave the per-agent rubric implicit — this overlay fills that gap. |
| **OpenAI Assistants** | `tools=[{type/function...}]` | per-Assistant `tools` array | Each Assistant is a scoping boundary; create role-specific Assistants rather than one with every function. |
| **Claude tool_use** | `tools=[{name, input_schema}]` in the API call | the `tools` list of a given request/agent | Scope by sending only the tools relevant to that agent's turn; large tool lists raise mis-selection and token cost identically. |

**One-line cross-walk**: CrewAI `agent.tools` ≈ LangGraph per-node
`bind_tools` ≈ Assistant `tools` array ≈ Claude request `tools` — in every case,
**the right-hand list is the capability grant, and least-privilege says keep it
minimal.**

---

## Appendix · Binding matrix template

```
              | web_search | run_sql (write) | send_email (write) | code_exec |
--------------+------------+-----------------+--------------------+-----------+
researcher    |     ✓      |        ·        |         ·          |     ·     |
analyst       |     ·      |        ·        |         ·          |     ✓     |
db_writer*    |     ·      |        ✓ (HITL)  |         ·          |     ·     |
notifier*     |     ·      |        ·        |       ✓ (HITL)      |     ·     |
reporter      |     ·      |        ·        |         ·          |     ·     |   ← zero-tool synthesis
--------------+------------+-----------------+--------------------+-----------+
* single owner of a destructive tool; guarded + idempotent
```
Audit rule: every `(write)` column has exactly one `✓`, and it is `(HITL)`.

---

## Sources
- `[crewai-sop]` = `crewai-sop-skill/SKILL.md` (per-agent tools §DC-3; split §DC-1; delegation §DC-5; scaling AP-1)
- `[langgraph-sop]` = `langgraph-sop-skill/SKILL.md` (bind_tools to nodes §Step2/4; HITL §Step5; double-charge §Case4)
- `[[crewai]]`, `[[agentsop-http-tool-wrapping]]`, `[[agentsop-llm-tool-idempotency]]` — sibling overlays
- Full evidence with quotes: `references/R1-source-evidence.md`
