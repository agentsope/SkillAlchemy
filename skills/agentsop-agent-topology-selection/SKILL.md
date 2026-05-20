---
name: agentsop-agent-topology-selection
version: 0.1.0
description: >-
  Cross-framework enhancement overlay for choosing a multi-agent topology BEFORE writing any
  agent. A binary-question rubric — is single-agent + tools enough? do agents need to know
  about each other? does the output need one voice? — maps the answer to single-agent /
  supervisor / swarm / sequential / hierarchical. Activates when a coder agent is tempted to
  "split the work into roles" or reaches for a multi-agent framework. Encodes the *selection
  rubric* that the per-framework skills assume but never surface. Search keywords: when to
  use multi-agent, single vs multi agent, do I need multiple agents, supervisor vs swarm,
  multi-agent vs single agent, agent team design.
overlay: true
cross_links: [crewai, langgraph, bounded-loop]
---

# Multi-Agent Topology Selection · SOP (ENHANCE overlay)

> Overlay posture: this skill decides *whether and which* topology. It does not
> teach the API — descend to `[[crewai]]` or `[[agentsop-langgraph]]` for that. Every
> load-bearing claim carries an inline source tag resolving in
> `references/R1-source-evidence.md`.

---

## 1. 何时激活 (When to Activate)

Activate when **any** of the following fire:

- The task description contains "team of agents", "researcher + writer + reviewer",
  "manager agent", "agents that hand off", "split this into roles", or "multi-agent".
- A coder agent is about to instantiate ≥2 agents (CrewAI `Agent(...)` × N,
  LangGraph supervisor/swarm, OpenAI Swarm handoffs) and has **not yet** justified
  why a single agent with tools is insufficient.
- Someone is choosing between CrewAI `Process.sequential` vs `Process.hierarchical`,
  or LangGraph supervisor vs swarm vs hierarchical-teams, and wants the *rubric*,
  not the syntax.
- A multi-agent system is over budget on tokens/latency and the question is "can we
  collapse agents back into one?".

Do **not** activate for: a single LLM call, a one-shot RAG query, or a fixed
tool-call pipeline with no role separation. Those are the single-agent baseline
this skill defends.

> Mental check: *"An agent needs agency, otherwise it's just another script."*
> — João Moura, CrewAI founder `[[crewai · §1.3]]`. If you can write the control
> flow in `if/else`, you do not need multiple agents — you need one agent (or a
> graph) with explicit edges.

---

## 2. 核心心智模型 (Core Mental Model)

**Most "multi-agent" problems are single-agent + tools.** Add agents only when
*context isolation* or *parallel expertise* genuinely demands it.

> "Single-agent is right for approximately 80% of cases; the trap is reaching for
> multi-agent because it sounds more capable." `[[crewai · DC-1]]`

Two — and only two — forces justify a second agent:

1. **Context isolation.** One agent's working context would pollute another's
   (a critic that must not see its own draft's rationalisations; a tool-heavy
   sub-task whose 40 intermediate tool calls should not bloat the main thread).
   Splitting gives each agent a clean, bounded prompt.
2. **Parallel expertise.** Two *genuinely different* skills run concurrently or in
   strict sequence (research → write → review), where a single prompt provably
   cannot hold both jobs without quality collapse `[[crewai · DC-1]]`.

If neither force is present, **a single agent with the union of tools wins** —
fewer hops, fewer tokens, no handoff failures. This is the baseline the rubric
must beat, not the default to escape.

### The selection rubric (three binary questions)

```
Q0  Is single-agent + tools enough?
      (no context-isolation need, no parallel-expertise need)
        YES → single-agent + tools. STOP. Do not add agents.
        NO  → ↓

Q1  Do the agents need to KNOW ABOUT EACH OTHER (peer handoff)?
        NO  → one funnels through a coordinator → SUPERVISOR
              (or static order → SEQUENTIAL, if order is fixed)
        YES → ↓

Q2  Must the OUTPUT speak with ONE VOICE / single audit funnel?
        YES → SUPERVISOR (single user-facing persona, one funnel)
        NO  → SWARM (dynamic peer handoff, last-active agent remembered)

Scaling override: ≥6 specialists that group into teams → HIERARCHICAL
(supervisor-of-supervisors). Use only for grouping, not for routing.
```

The two questions that actually separate the patterns: **(a) can sub-agents know
each other, (b) is one user-facing voice mandated.** Everything else is tuning
`[[langgraph · Case 2]]`.

---

## 3. SOP 工作流 (Selection Protocol)

Walk top-down. Each gate can send you *back down* the ladder — collapsing agents
is as valid an answer as adding them.

### Step 1 · Defend the single-agent baseline first
Ask Q0. Enumerate the would-be roles. For each, ask: *would merging it into one
agent's prompt + toolset actually degrade output?* If you cannot point to a
concrete failure mode (style drift, missed checklist, context bloat, parallel
latency), the honest answer is single-agent + tools. Exit here ~80% of the time
`[[crewai · DC-1]]`.

### Step 2 · If splitting, decide static vs dynamic routing
- **Order is fixed and known at design time** (research always precedes write
  precedes review) → **SEQUENTIAL**. Cheapest, most debuggable, 1× token baseline
  `[[crewai · §2.3]]`. In CrewAI this is `Process.sequential`; in LangGraph it is
  static edges A→B→C.
- **Routing must be decided at runtime** (which specialist handles *this* query) →
  you need a coordinator or peer handoff → continue to Step 3.

### Step 3 · Coordinator (supervisor) vs peers (swarm)
Ask Q1 then Q2.
- Agents that do **not** know each other and funnel through one router →
  **SUPERVISOR**. Sub-agents are effectively tools the supervisor calls; the
  supervisor "translates" their output back to the user — which is *exactly* why
  it costs the most tokens `[[langgraph · Step 4]]`.
- Agents that **do** know each other and **no** single voice is mandated →
  **SWARM**. Dynamic handoff, last-active agent stays active across turns, no
  translation step → fewer tokens, slightly higher accuracy on the τ-bench retest
  `[[langgraph · §SOP Step 4]]`.

### Step 4 · Apply the supervisor-default caveat (read this twice)
LangChain's *own* benchmark found swarm "slightly outperformed supervisor across
all scenarios" and supervisor "consistently uses more tokens than swarm" — yet
they **still ship supervisor as the recommended default** `[[langgraph · Step 4]]`.
Why the nuance matters:
- Supervisor is the **safest with third-party / untrusted agents** (single funnel,
  single audit log, single place to enforce policy) `[[langgraph · Step 4]]`.
- Swarm is a **bad fit for third-party agents** — peers handing off to peers means
  no central control point `[[langgraph · Step 4]]`.
- So: **do not copy "default = supervisor" blindly.** If your agents are internal
  and trusted, swarm is often the better pick the default hides. Pick on the two
  questions, not on the framework's default.

### Step 5 · Verify the chosen topology can terminate
Any topology with runtime handoff (swarm, hierarchical, CrewAI delegation) can
loop. Bound it before shipping — cross-link `[[agentsop-bounded-loop]]`. Concretely:
default `allow_delegation=False` on workers, set per-agent `max_iter`, wrap an
outer timeout, and bake an explicit exit counter into state rather than trusting
the LLM to stop `[[crewai · DC-5]]` `[[agentsop-bounded-loop]]`.

### Step 6 · Reconsider before scaling agents up
≥6 specialists → group into **HIERARCHICAL teams** purely for *navigability*, not
to get free routing (see Anti-patterns). At >5 agents CrewAI starts hitting
coordination failure `[[crewai · §6.1]]`; that is a signal to group or collapse,
not to add more.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**.

### OP-1 · Defend the single-agent baseline
- **Trigger**: a task is being described as "a team of agents".
- **Action**: list the proposed roles; for each, name the concrete failure that
  merging into one agent would cause (style drift / missed checklist / context
  bloat / required parallelism). No nameable failure ⇒ single agent.
- **Output**: single-agent + tools, OR a justified list of must-split roles.
- **Evidence**: `[[crewai · DC-1]]` "single-agent right for ~80% of cases".

### OP-2 · Single-vs-multi gate
- **Trigger**: baseline defended and at least one role has a real split-justifying
  failure mode.
- **Action**: confirm the force is *context isolation* or *parallel expertise* —
  not "it sounds more capable". If only the latter, stay single.
- **Output**: a yes/no on multi-agent with the force named in one sentence.
- **Evidence**: `[[crewai · §2.2]]`, `[[crewai · DC-1]]`.

### OP-3 · Static-order gate (→ sequential)
- **Trigger**: multi-agent confirmed; the order of work is fixed at design time.
- **Action**: choose SEQUENTIAL — list agents in execution order; pass dependencies
  explicitly (CrewAI `context=[...]`), do not rely on implicit transfer.
- **Output**: an ordered task list; CrewAI `Process.sequential` or LangGraph static
  edges.
- **Evidence**: `[[crewai · §2.3]]` (sequential = 1× tokens, low debug cost).

### OP-4 · Peer-awareness gate (Q1 → supervisor vs swarm branch)
- **Trigger**: routing must be decided at runtime.
- **Action**: ask "do sub-agents know about each other?" — NO ⇒ supervisor branch;
  YES ⇒ continue to OP-5.
- **Output**: chosen branch.
- **Evidence**: `[[langgraph · Step 4]]` decision tree.

### OP-5 · Single-voice gate (Q2 → supervisor vs swarm)
- **Trigger**: peers know each other (Q1=YES).
- **Action**: ask "must output be one voice / single audit funnel?" — YES ⇒
  SUPERVISOR; NO ⇒ SWARM.
- **Output**: SUPERVISOR or SWARM.
- **Evidence**: `[[langgraph · Case 2]]` (compliance ⇒ supervisor; UX continuity ⇒ swarm).

### OP-6 · Apply the supervisor-default caveat
- **Trigger**: supervisor was selected, OR you are about to accept a framework
  default.
- **Action**: check trust. Third-party/untrusted agents ⇒ supervisor is correct.
  Internal/trusted ⇒ re-test whether swarm's lower token cost wins; if so, switch.
- **Output**: a topology chosen on trust + the two questions, not on the default.
- **Evidence**: `[[langgraph · Step 4]]` — swarm beats supervisor on bench, yet
  supervisor remains the shipped default *for third-party safety*.

### OP-7 · Tune-before-switch
- **Trigger**: chosen topology is over token/latency budget.
- **Action**: before changing paradigm, apply the published fixes to the *current*
  one. For supervisor: remove handoff messages, add a forwarding-messages tool,
  optimise tool naming — LangChain measured "nearly 50% increase in performance"
  `[[langgraph · Step 4]]`. Switch paradigm only if still over budget.
- **Output**: a tuned topology or a justified migration.
- **Evidence**: `[[langgraph · Case 2]]`.

### OP-8 · Bound the topology
- **Trigger**: any runtime-handoff topology before ship.
- **Action**: `allow_delegation=False` on workers, per-agent `max_iter`, outer
  timeout, explicit state-based exit counter.
- **Output**: a topology that provably terminates.
- **Evidence**: `[[crewai · DC-5]]` (delegation ping-pong), `[[agentsop-bounded-loop]]`.

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 · "Swarm beats supervisor on the benchmark — why ship supervisor?"
- **困境**: LangChain's own multi-agent benchmark shows swarm "slightly
  outperformed supervisor across all scenarios" and supervisor "consistently uses
  more tokens" (the telephone-game translation overhead). Yet LangChain's
  *recommended default* is still supervisor `[[langgraph · Step 4]]`. A coder
  agent copying the default would leave accuracy and tokens on the table.
- **约束**:
  - Want the benchmark's efficiency (swarm).
  - But may integrate third-party / untrusted agents later.
  - Need a single auditable funnel for tool calls (compliance).
- **决策步骤**:
  1. Read the default's *reason*, not the default. Supervisor wins on **safety with
     third-party agents** and **single audit funnel** — not on accuracy `[[langgraph · Step 4]]`.
  2. If all agents are internal and trusted **and** no single-voice mandate →
     pick **swarm**; the default does not apply to you.
  3. If a single auditable funnel is mandated → keep supervisor, then apply the
     three fixes (remove handoff messages, forwarding-messages tool, tool-name
     tuning) for the measured ~50% bump *before* concluding it is too slow
     `[[langgraph · Case 2]]`.
  4. Re-measure tokens; migrate to swarm only if still over budget and audit is
     tolerant.
- **结果**: Topology chosen on trust + the two questions. The benchmark's "swarm >
  supervisor" is true *and* the supervisor default is rational — for a *different*
  constraint (third-party safety) than the one the benchmark measured (accuracy/cost).
- **可提取的操作**: OP-6. **A framework default encodes the framework author's
  worst-case constraint, not yours. Decode the reason; re-derive for your case.**

### Case 2 · "CrewAI hierarchical for simple routing is structurally broken"
- **困境**: 5 agents, order roughly fixed, but the system should *route* — skip
  irrelevant specialists based on the query. `Process.hierarchical` looks like it
  "should auto-route". In practice the manager **executes all tasks** and the last
  task's output overwrites the rest — it does not skip on triage `[[crewai · DC-2]]`.
  ```
  Query: "Why is my laptop overheating?" (pure technical)
  Expected:  triage → technical_agent → done
  Hierarchical reality: triage → technical → billing → … → last output wins
  ```
- **约束**: routing is required; default `manager_llm` is unreliable; latency/cost
  matter.
- **决策步骤**:
  1. Recognise hierarchical-for-routing is the wrong tool: CrewAI hierarchical is a
     *coordination* topology, not a *router* `[[crewai · DC-2]]`.
  2. If routing logic fits in ~5 lines of Python → use a **CrewAI Flow** (`@router`
     / `@listen`) or a **LangGraph conditional edge** — explicit branch, then call
     one small crew / single agent per branch `[[crewai · DC-2]]`.
  3. If routing genuinely needs LLM semantic judgement → hierarchical **with a
     custom `manager_agent`** carrying an explicit branching backstory — *never*
     the bare default `manager_llm` `[[crewai · OP-4]]`.
  4. Bound it: workers `allow_delegation=False`, outer timeout `[[agentsop-bounded-loop]]`.
- **结果**: Routing handled by explicit control flow; hierarchical reserved for
  true coordination of trusted teams, never for if/else routing.
- **可提取的操作**: **Hierarchical ≠ router. Routing is control flow — make it
  explicit (Flow / conditional edge), don't delegate it to a manager LLM that will
  run everything.** Compare with `d-query-routing-skill` for the routing-specific rubric.

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

- **Multi-agent theater.** Splitting into roles because it "sounds more capable"
  with no context-isolation or parallel-expertise force. Symptom: agents that just
  pass a string along, each adding a paragraph. Fix: collapse to one agent + tools
  `[[crewai · DC-1]]`.
- **Hierarchical for simple routing.** Using `Process.hierarchical` (or a
  supervisor) to get free if/else routing. It runs everything; routing must be
  explicit control flow (Flow / conditional edge) `[[crewai · DC-2]]`.
- **Copying the supervisor default blindly.** The benchmark says swarm is better on
  accuracy *and* tokens; supervisor is the default for *third-party safety*. Internal
  trusted agents should reconsider swarm `[[langgraph · Step 4]]`.
- **Agent-count explosion (>5).** Coordination failure, token blow-up, debug pain.
  ≥6 ⇒ group into hierarchical teams *for navigability*, or merge near-duplicate
  roles `[[crewai · §6.1]]`.
- **Unbounded delegation.** `allow_delegation=True` on every agent ⇒ ping-pong
  loops. Default off on workers; bound with `max_iter` + timeout `[[crewai · DC-5]]`,
  `[[agentsop-bounded-loop]]`.
- **Picking on aesthetics.** Choosing supervisor/swarm/sequential by which "feels
  cleaner" instead of the two binary questions (peer-awareness, single-voice)
  `[[langgraph · Case 2]]`.

**Hard boundaries (this rubric does NOT decide):**
- *Which framework* — see `[[crewai]]` vs `[[agentsop-langgraph]]` ecosystem sections.
- *Routing by query kind* — that is `d-query-routing-skill`.
- *Bounding the loop* — that is `[[agentsop-bounded-loop]]`.
- *Latency < 200ms / single LLM call* — no multi-agent framework at all
  `[[langgraph · 反模式]]`.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

| Topology | CrewAI | LangGraph | OpenAI Swarm | Choose when |
|---|---|---|---|---|
| **Single-agent + tools** | one `Agent` + tools (skip Crew) | `create_react_agent` | one routine | Q0=YES — ~80% of cases `[[crewai · DC-1]]` |
| **Sequential** | `Process.sequential` + `context=[...]` | static edges A→B→C | linear handoffs | order fixed at design time `[[crewai · §2.3]]` |
| **Supervisor** | `Process.hierarchical` + custom `manager_agent` | supervisor pattern (sub-agents as tools) | central routine dispatching | peers don't know each other; one voice / third-party safety `[[langgraph · Step 4]]` |
| **Swarm** | (no native; Flow + handoff funcs) | swarm pattern (dynamic handoff) | `handoff` between agents | peers know each other; no single-voice mandate; internal/trusted `[[langgraph · Step 4]]` |
| **Hierarchical teams** | nested crews via Flow | supervisor-of-supervisors / subgraphs | n/a | ≥6 specialists needing grouping `[[crewai · §6.1]]` |

Notes:
- **CrewAI** frames agents as role-playing teammates; `hierarchical` is coordination,
  *not* routing — the default `manager_llm` runs all tasks `[[crewai · DC-2]]`.
- **LangGraph** frames topology as routing logic over typed state; supervisor is the
  shipped default for third-party safety despite swarm winning the bench
  `[[langgraph · Step 4, Case 2]]`.
- **OpenAI Swarm** is the minimal handoff baseline — OpenAI labels it experimental;
  use as reference, not production `[[langgraph · 生态对照]]`.
- **Single-agent + tools** is the baseline every topology above must beat. Defend it
  first (OP-1).

> Pick the smallest topology that fits the two questions; promote upward only when a
> named force demands it, and collapse back down when the force disappears.

---

## 附录: 引用 (Citations)

Inline tags resolve to source-skill sections in `references/R1-source-evidence.md`:
- `[[crewai]]` = `/Users/5imp1ex/Desktop/Skill-Workplace/output/crewai-sop-skill/SKILL.md`
- `[[agentsop-langgraph]]` = `/Users/5imp1ex/Desktop/Skill-Workplace/output/langgraph-sop-skill/SKILL.md`
- The benchmark: LangChain, *Benchmarking Multi-Agent Architectures*
  (`www.langchain.com/blog/benchmarking-multi-agent-architectures`), surfaced via
  `[[langgraph · Step 4 / Case 2]]`.
