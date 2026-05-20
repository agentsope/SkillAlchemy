---
name: agentsop-langgraph
description: |
  Decision protocol for building, debugging, and operating LangGraph-based agent
  systems. Activates when a coder agent is asked to design a stateful LLM workflow,
  add human-in-the-loop, choose a multi-agent pattern (supervisor / swarm /
  hierarchical), pick a checkpoint backend, or migrate a fragile chain into a
  durable graph. LangGraph is positioned by its maintainers as a "low-level
  orchestration framework for building, managing, and deploying long-running,
  stateful agents" — this skill encodes the *when* and *why*, not the API.
version: 0.1.0
---

# LangGraph · SOP

> Source posture: every non-trivial claim is cited inline. Citations use short
> tags like `[lc-docs]`, `[lc-blog/interrupt]`, `[gh/6731]`, `[zenml/uber]` —
> resolve them against `references/*.md` for the full URL.

---

## 何时激活 (Activation Rules)

Activate this skill when **any** of the following triggers fire:

- The task mentions LangGraph, `StateGraph`, `MessageGraph`, `create_react_agent`,
  `interrupt(`, `Command(resume=`, `add_messages`, `checkpointer`, `PostgresSaver`,
  `Send(`, or `entrypoint` / `task` decorators.
- The user wants to build a **stateful** agent (memory across turns, long-running,
  must survive a process crash) — LangGraph's stated sweet spot
  `[lc-docs/why-langgraph]`.
- The user wants **human-in-the-loop** (approve a tool call, edit state, multi-turn
  validation) — LangGraph offers a first-class `interrupt()` primitive that
  competitors require "duct-taping" to achieve `[bswen/hitl]`.
- The user is hitting **`GRAPH_RECURSION_LIMIT`** errors, infinite loops, or
  `InvalidUpdateError` on parallel branches — these are LangGraph-specific failure
  modes with known fixes `[lc-docs/errors]` `[cheatsheet/gotchas]`.
- The user is choosing between LangGraph and CrewAI / AutoGen / OpenAI Swarm /
  raw LangChain — section *生态对照* gives the decision matrix.
- The user is migrating an existing LangChain chain or a hand-rolled while-loop
  agent to something durable and observable.

Do **not** activate if the task is a single LLM call, a one-shot RAG query, or
a stateless tool pipeline — `Sec. 反模式` explains why graphs are overkill there.

---

## 核心心智模型 (Core Mental Model)

**LangGraph is a state machine, not a chain.** The cleanest one-liner from the
2026 docs: "If chains were about passing outputs between steps, graphs are about
maintaining and evolving a shared state over time" `[eastondev/2026]`. Pre-LLM
analog: think BPMN / finite state machine / Pregel-style "supersteps", not a
Unix pipe. The official position is even more reductive: LangGraph is "a
deterministic execution engine for AI reasoning workflows" `[eastondev/2026]`.

Three load-bearing concepts ride this model:

1. **State is the single source of truth.** All nodes read from and write to one
   shared, typed object (`TypedDict` / Pydantic / dataclass). A node returns a
   *partial update*, never a mutation. How updates merge into state is governed
   by **reducers**, declared via `Annotated[list[Msg], add_messages]` etc.
   Missing a reducer on a key that two parallel nodes both write to triggers
   `InvalidUpdateError` — reducers are mandatory for parallel writes
   `[cheatsheet/gotchas]`. The reducer system is what lets the graph be
   composable, replayable, and crash-safe.

2. **Checkpoints make state durable.** After every superstep, the full state is
   snapshotted into a checkpointer (SQLite for local, Postgres for production,
   Redis for fast TTL'd swarms) `[lc-docs/persistence]` `[redis/checkpoint]`.
   This single property is what unlocks the headline features: durable execution
   that "persists through failures and resumes from their exact stopping point",
   time-travel debugging (replay or fork from any checkpoint), and
   human-in-the-loop (a thread can sit interrupted for hours and resume cleanly)
   `[gh/langgraph-readme]` `[dragonforest/timetravel]`.

3. **Graph topology is just routing logic over state.** Edges are static
   (always go to N), conditional (a function reads state and picks a next node),
   or dynamic via the `Send` API (a routing function returns a list of `Send`
   objects to spawn variable-count parallel workers) `[deepwiki/mapreduce]`.
   This is where LangGraph diverges from CrewAI's role-based crew and AutoGen's
   conversational pattern — control flow is **explicit**, not emergent from
   chat history.

The OS-level claim: **"2026 is the year of Stateful Orchestration"**
`[eastondev/2026]`. LangGraph bet that production agents need persistence,
explicit control flow, and observability more than they need elegance. That bet
is paying off (Klarna serves 85M users on it, Replit pushed it so hard
LangSmith had to be rewritten to ingest the traces) — but the cost is verbosity
that frustrates anyone trying it on a toy problem `[lc-blog/production]`
`[duplocloud/compare]`.

---

## SOP 工作流 (Agentic Protocol)

A coder agent should walk this protocol top-down. Each step has a **decision
gate** — if the answer is "no" or "not yet", stop and reconsider before adding
graph complexity.

### Step 1 · Decide whether a graph is actually warranted

Gate questions:
- Does the workflow have ≥1 cycle (tool-call → reflect → retry)?
- Does it need to **survive a crash** mid-execution?
- Will a human need to inspect or override state mid-run?
- Are there ≥2 specialized agents that hand off?

If **all four are no**, use a plain `RunnableSequence` or raw API calls and
exit. Over-graphing simple flows is the #1 anti-pattern `[swarnendu/best]`.

### Step 2 · Pick the API surface

| Need | Choice | Why |
|---|---|---|
| Standard tool-calling ReAct loop | `create_react_agent` (prebuilt) | Syntactic sugar over StateGraph; ~3 lines of code `[agentsindex/v1]` |
| Imperative Python style, async tasks, no explicit graph | Functional API (`@entrypoint`, `@task`) | Shares the runtime with StateGraph; trades time-travel granularity for code brevity `[lc-blog/functional]` |
| Multi-agent, parallel, custom routing, supervisor | `StateGraph` (manual) | Required for non-trivial topology `[agentsindex/v1]` |
| Chat-only message history | `MessageGraph` *(legacy)* | Only for very basic chatbots; prefer StateGraph `[cheatsheet/gotchas]` |

Default to `create_react_agent` and **graduate** to `StateGraph` only when you
need parallel nodes, supervisor-worker patterns, custom retry logic, or
complex branching `[agentsindex/v1]`.

### Step 3 · Design the state schema *before* writing nodes

The state schema is "the most critical design component" `[bharatraj/state]`.
Discipline:

- Use `TypedDict` for ergonomics, Pydantic only when validation matters.
- Every key that may be **written in parallel** gets an explicit reducer
  (`add_messages`, `operator.add`, or custom) — otherwise plan for it to be
  overwritten last-write-wins.
- Keep state **lightweight and serializable** — it gets pickled to the
  checkpointer on every superstep `[bharatraj/state]`.
- Treat each node like a **pure function**: return a partial state update,
  do not mutate inputs `[swarnendu/best]`.

### Step 4 · Choose the multi-agent topology

Decision tree, sourced from LangChain's own benchmark `[lc-blog/benchmark]`:

```
Is there exactly one "user-facing" persona?
├─ YES  → Supervisor pattern (single supervisor, sub-agents are tools)
│        - Highest token cost (supervisor "translates" sub-agent output)
│        - Safest with third-party agents
│        - LangChain's *current recommended default*
└─ NO   → Do sub-agents know about each other?
         ├─ YES → Swarm pattern (dynamic handoff, last-active agent remembered)
         │       - Lower tokens than supervisor (no translation step)
         │       - Slightly higher accuracy in the τ-bench retest
         │       - Bad fit for third-party agents
         └─ NO  → Hierarchical Teams (supervisor-of-supervisors)
                 - Use only when ≥6 specialists need grouping
```

Concrete bench finding: swarm "slightly outperformed supervisor across all
scenarios"; supervisor "consistently uses more tokens than swarm" because of
the telephone-game translation overhead `[lc-blog/benchmark]`. LangChain's
own response was to fix the supervisor (remove handoff messages, add a
forwarding-messages tool, tune tool names) for "a nearly 50% increase in
performance" `[lc-blog/benchmark]`.

### Step 5 · Add human-in-the-loop *only* on irreversible actions

Use `interrupt(value)` at the node that would perform the high-blast-radius
operation; resume with `Command(resume=...)` `[lc-blog/interrupt]`. Four
canonical patterns `[lc-blog/interrupt]`:

1. **Approve / Reject** — review a critical step before it runs.
2. **Review & Edit State** — human corrects or augments mid-run.
3. **Review Tool Calls** — oversee LLM-requested actions.
4. **Multi-turn Conversation** — back-and-forth in a multi-agent setup.

Rule of thumb: "interrupt on irreversible, high-blast-radius actions only —
not on every step" `[bswen/hitl]`. Side effects (DB writes, API calls) must
go **after** the interrupt or in a downstream node — placing them before
causes unwanted re-execution on resume `[cheatsheet/gotchas]`.

### Step 6 · Pick the checkpointer to match the durability requirement

| Backend | Use when | Source |
|---|---|---|
| `InMemorySaver` | Tests / notebooks only | `[lc-docs/persistence]` |
| `SqliteSaver` / `AsyncSqliteSaver` | Single-machine local dev, low concurrency | `[lc-docs/persistence]` |
| `PostgresSaver` / `AsyncPostgresSaver` | Production default, multi-user, ACID needed | `[lc-docs/persistence]` |
| `RedisSaver` | High-throughput swarms, TTL-expiring sessions, sub-ms reads | `[redis/checkpoint]` |

Run `checkpointer.setup()` **as a CI/CD migration**, never inside app runtime
`[bswen/hitl]`. Implement a **TTL sweep** for interrupted-but-never-resumed
threads (e.g., abandon after 24 h) — otherwise state accumulates indefinitely
`[bswen/hitl]`.

### Step 7 · Add observability + bounded loops before shipping

- Wire LangSmith from day one — replaying a checkpoint locally only goes so
  far; production needs the trace UI `[swarnendu/best]`.
- Set a deliberate `recursion_limit` (default 25); raise it via
  `graph.invoke({...}, {"recursion_limit": 100})` only after confirming
  the loop *can* terminate `[lc-docs/errors]`.
- Treat `recursion_limit` as a **safety net, not control flow**. Hitting it
  means the conditional edge logic is wrong, not that the limit is too low
  `[cheatsheet/gotchas]`.

---

## 操作模型 (Operation Models)

Each operation is a primitive a coder agent can invoke. Format:
**Trigger → Action → Output → Evidence**.

### OP-1 · Bootstrap a ReAct agent in <10 lines
- **Trigger**: User says "make me an agent that uses tool X" with no other
  requirements.
- **Action**: Call `from langgraph.prebuilt import create_react_agent`; pass
  model + tools list. Skip StateGraph entirely.
- **Output**: A compiled graph supporting `.invoke()` / `.stream()` with
  built-in message history.
- **Evidence**: `[agentsindex/v1]` "Start with create_react_agent for any
  standard tool-calling agent."

### OP-2 · Promote a prebuilt agent to a custom StateGraph
- **Trigger**: The prebuilt agent needs parallel branches, a supervisor,
  custom retry, or a non-message state field.
- **Action**: Re-implement with `StateGraph(MyTypedDict)`, manually add the
  LLM node, tool node, and conditional edge that routes on `tool_calls`.
- **Output**: A graph with explicit topology and full control.
- **Evidence**: `[agentsindex/v1]` "If you find yourself needing parallel node
  execution, a supervisor-worker pattern, custom retry logic, or complex
  branching, migrate to a manual StateGraph."

### OP-3 · Add a reducer to fix `InvalidUpdateError`
- **Trigger**: Two nodes write the same state key in parallel and the graph
  raises `InvalidUpdateError`.
- **Action**: Replace `key: list[X]` with
  `key: Annotated[list[X], operator.add]` (or `add_messages` for chat).
- **Output**: Parallel writes merge instead of conflicting.
- **Evidence**: `[cheatsheet/gotchas]` "Reducers are mandatory, not optional,
  for parallel execution."

### OP-4 · Spawn dynamic parallel workers with `Send`
- **Trigger**: At runtime, the agent needs to fan out a variable number of
  parallel tasks (e.g., one summarizer per retrieved doc).
- **Action**: From a conditional edge, return
  `[Send("worker", {"chunk": c}) for c in state["chunks"]]`. The worker uses
  its own state schema, and results are reduced back via `operator.add`.
- **Output**: True dynamic map-reduce, decided per-invocation.
- **Evidence**: `[deepwiki/mapreduce]` "Send allows a conditional edge
  function to schedule a node with a custom state…the primary mechanism for
  dynamic fan-out."

### OP-5 · Insert a human approval gate
- **Trigger**: A node would perform an irreversible action (charge a card,
  send email, run SQL `DELETE`).
- **Action**: Inside the node, call
  `decision = interrupt({"proposed": payload})` *before* the side effect.
  Compile the graph with a checkpointer. The caller resumes with
  `graph.invoke(Command(resume="approve"), config)`.
- **Output**: Thread pauses, state persists, resumes with the human's
  decision threaded back into the node.
- **Evidence**: `[lc-blog/interrupt]` four-pattern table + `[bswen/hitl]` side-
  effect ordering.

### OP-6 · Encapsulate a multi-step subflow as a subgraph
- **Trigger**: A logical chunk (a research agent inside a larger workflow,
  a reusable validation pipeline) deserves its own state and lifecycle.
- **Action**: Compile the child graph, add it as a node:
  `parent.add_node("research", research_subgraph)`. If schemas differ, wrap
  the call in a node function that translates between schemas.
- **Output**: Reusable, independently testable module; child state isolated
  unless keys overlap.
- **Evidence**: `[lc-docs/subgraphs]` `[deepwiki/subgraphs]` "subgraph state
  is only accessible when the subgraph is interrupted" — accept the debug
  cost.

### OP-7 · Switch to durable Postgres checkpointing
- **Trigger**: Moving from notebook to production OR multi-user OR thread
  state must survive deploys.
- **Action**: `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver`,
  pass to `.compile(checkpointer=...)`. Run `await saver.setup()` in a
  migration job, not at app boot.
- **Output**: Threads survive crashes, multi-replica reads work, ACID
  guarantees for state transitions.
- **Evidence**: `[lc-docs/persistence]` PostgresSaver "ideal for using in
  production"; `[bswen/hitl]` "handle this as part of a CI/CD migration
  script…not inside the primary application runtime."

### OP-8 · Stream tokens to the UI without sacrificing graph observability
- **Trigger**: Need character-by-character UX *and* server-side debugging.
- **Action**: Use `graph.stream(input, stream_mode=["messages", "updates"])`
  — `messages` yields LLM tokens, `updates` yields state diffs. For
  intra-tool progress, emit via `stream_mode="custom"`.
- **Output**: User sees streaming tokens; server logs structured state diffs.
- **Evidence**: `[lc-docs/streaming]` five modes — values, updates, messages,
  custom, debug.

### OP-9 · Bound an agent loop without papering over with `recursion_limit`
- **Trigger**: Agent hits `GRAPH_RECURSION_LIMIT` (e.g., text-to-SQL retrying
  the same broken query).
- **Action**: Read the conditional-edge logic — the *real* fix is an exit
  condition counting retries in state and routing to `END` after N attempts.
  Bump `recursion_limit` only as a temporary diagnostic.
- **Output**: Graceful termination on persistent failure.
- **Evidence**: `[lc-docs/errors]` "Check your logic for infinite loops";
  `[cheatsheet/gotchas]` "Hitting the limit indicates an underlying design
  flaw"; concrete bug case `[gh/6731]`.

### OP-10 · Time-travel debug a failed production run
- **Trigger**: A production thread produced a wrong answer; need to see what
  state the LLM saw at step 7 and try a different prompt.
- **Action**: Fetch the thread's checkpoint history via
  `graph.get_state_history(config)`, pick the checkpoint, invoke with
  `config={"configurable": {"thread_id": ..., "checkpoint_id": ...}}`.
  Modify state with `graph.update_state(...)` to fork.
- **Output**: Reproduce + fork a past run without re-paying for LLM calls
  on replayed nodes.
- **Evidence**: `[dragonforest/timetravel]` "replay…the agent knows that this
  checkpoint has already been executed and will just display the historical
  output instead of making new LLM calls."

---

## 困境决策案例 (Dilemma Cases)

### Case 1 · "Text-to-SQL agent loops forever until recursion limit"
- **困境**: A team built a text-to-SQL agent on LangGraph 1.0.6. When the
  Databricks query returned an error, the agent retried the same broken query
  20 times until `GRAPH_RECURSION_LIMIT` fired. It had worked on 0.6.x
  `[gh/6731]`.
- **约束**:
  - Cannot pin to old version (security fixes in 1.x).
  - Maintainer marked the issue "not planned" — no official patch coming
    `[gh/6731]`.
  - Business needs the agent live.
- **决策步骤**:
  1. **Reject** the temptation to just raise `recursion_limit` — that masks
     the bug and burns Databricks quota `[cheatsheet/gotchas]`.
  2. Add an explicit retry counter to state:
     `retries: Annotated[int, operator.add]`.
  3. After the tool node, increment counter on SQL error; in the conditional
     edge, route to `END` (or a "give up and ask user" node) once
     `retries >= 3`.
  4. Surface the failure mode by storing the last error message in state and
     letting the LLM see it on the next loop — the *content* of the error
     usually informs whether to retry or abandon.
  5. Add a regression test that injects a permanent SQL error and asserts the
     graph terminates within 3 iterations.
- **结果**: Bounded retries, observable failure, no quota blow-out. The
  community-acknowledged fact is that LangGraph's recursion limit is a safety
  net, not control flow — exit conditions are the real fix `[lc-docs/errors]`.
- **可提取的操作**: OP-9. **Always bake a retry/exit counter into state for any
  cyclic graph.** Trust nothing the LLM does to terminate itself.

### Case 2 · "Supervisor vs. swarm in a multi-domain customer support agent"
- **困境**: A team needed a customer-service agent covering retail, billing,
  and shipping. They started with the supervisor pattern (one router agent
  → three specialists). User-perceived latency was high and token cost was
  double what they budgeted. They wondered if swarm would be better.
- **约束**:
  - The three specialists are internal — they *can* be aware of each other.
  - User expects continuous conversation in one domain (no constant
    "transferring you to...").
  - Compliance requires a single auditable agent for tool calls.
- **决策步骤**:
  1. Consult LangChain's own benchmark: swarm "slightly outperformed
     supervisor"; supervisor uses more tokens because of the translation
     step `[lc-blog/benchmark]`.
  2. Map constraints to patterns: compliance favours supervisor (single
     funnel); UX favours swarm (last-active agent stays active across turns).
  3. Compromise: keep supervisor topology *but* apply LangChain's three
     supervisor fixes — "removing handoff messages, forwarding messages tool,
     tool naming optimization" — which yielded a "nearly 50% increase in
     performance" in the bench `[lc-blog/benchmark]`.
  4. Re-evaluate token cost after the fixes; if still too high and audit
     trail is tolerant, migrate to swarm.
- **结果**: Hybrid — supervisor topology with tuned tools captures most of
  swarm's efficiency while preserving the single-funnel audit log.
- **可提取的操作**: **Don't pick supervisor vs. swarm on aesthetics — anchor
  on (a) whether sub-agents can know each other, (b) whether one user-facing
  voice is mandated. Then optimise the chosen pattern with LangChain's own
  published fixes before switching paradigms.**

### Case 3 · "Replit-scale traces overwhelmed the observability stack"
- **困境**: Replit built a code-generation agent on LangGraph that "involved
  hundreds of steps" per run. Traces were so large that LangSmith — built by
  the same team — couldn't ingest or render them initially
  `[alphabold/case]`.
- **约束**:
  - The depth of the graph is intrinsic to the product (planning → code →
    tests → deploy → debug → fix).
  - Cannot trim steps without harming product quality.
  - Need debugability for a multi-agent system with HITL.
- **决策步骤** (reconstructed from the case study):
  1. Accept that pushing LangGraph to its limit means **co-evolving the
     observability layer** — Replit and LangChain iterated on LangSmith's
     ingestion and rendering specifically for this trace shape
     `[alphabold/case]`.
  2. Use **subgraphs** to break "hundreds of steps" into named, navigable
     teams (planner-team, codegen-team, test-team) — flat graphs of that
     size are unreadable `[deepwiki/subgraphs]`.
  3. Use **`Send` API** for fan-out at known parallel points (e.g.,
     generate-then-test in parallel) so each branch is a distinct trace
     segment.
  4. Use **HITL `interrupt`** at the deploy boundary — humans approve a
     deploy plan rather than letting the agent push autonomously.
  5. Use **time-travel** on failed runs — fork from the last good checkpoint
     to test prompt variants without re-paying for upstream LLM calls
     `[dragonforest/timetravel]`.
- **结果**: Replit Agent ships; the friction it surfaced fed back into
  LangSmith improvements. The lesson: at scale, the observability tool is
  part of the system design, not external to it.
- **可提取的操作**: **For agents with > ~50 steps per run, plan the
  observability story alongside the graph topology. Subgraphs + `Send` are
  not optional optimisations — they are how you make the graph debuggable
  at production scale.**

### Case 4 · "Side effects before `interrupt()` re-executed on resume"
- **困境**: A team built a payment workflow: node A charges the card, then
  calls `interrupt()` for a human to confirm the receipt. On resume, the
  card was charged *twice* because resuming a thread "re-runs the entire
  node function" `[cheatsheet/gotchas]`.
- **约束**: Can't disable HITL (compliance requirement); can't undo charges
  silently; cannot rewrite payment SDK.
- **决策步骤**:
  1. **Recognize the framework semantics**: resume re-enters the node from
     the top, not from the line of the `interrupt()`. Treat every node body
     as potentially re-runnable.
  2. **Restructure**: Move the charge into a downstream node that runs
     *after* the interrupt-bearing node returns approval into state. Now the
     interrupt-node only proposes; the next node executes.
  3. **Idempotency belt-and-braces**: Generate a charge_id in state before
     `interrupt`, pass it to the payment SDK as idempotency key — re-run
     becomes a no-op even if topology changes.
- **结果**: One charge per approval; safe-by-construction.
- **可提取的操作**: **Two-line rule**: (a) nothing irreversible *before* an
  `interrupt()` in the same node; (b) every external side-effect uses an
  idempotency key drawn from state. Sourced directly from the cheatsheet
  pitfall list `[cheatsheet/gotchas]`.

---

## 反模式与边界 (Anti-patterns & Boundaries)

Concrete don'ts, each with the underlying reasoning.

- **Don't graph a stateless pipeline.** A 3-step prompt-tool-prompt chain
  with no cycles, no HITL, and no need to survive a crash does not need
  LangGraph. The abstraction overhead "could be a disadvantage in more
  straightforward scenarios" `[duplocloud/compare]`. Use a `RunnableSequence`.
- **Don't use `recursion_limit` as a termination strategy.** It "is not
  intended to be a primary control flow mechanism"; hitting it "indicates an
  underlying design flaw" `[cheatsheet/gotchas]`. Bake exit conditions into
  state.
- **Don't put side effects before `interrupt()`.** On resume, the node body
  re-runs from the top `[cheatsheet/gotchas]`.
- **Don't mutate state inputs.** "Treat each node like a pure function:
  return a partial state update rather than mutating inputs" `[swarnendu/best]`.
  Mutation breaks checkpoint replayability.
- **Don't share state between parallel branches without a reducer.** Missing
  reducers on a key two nodes both write to triggers `InvalidUpdateError`
  `[cheatsheet/gotchas]`.
- **Don't run `checkpointer.setup()` at app boot.** Treat it as a DB
  migration; run via CI/CD `[bswen/hitl]`.
- **Don't leave interrupted threads to rot.** Implement a TTL sweep — without
  one, "state is held in the checkpointer indefinitely" `[bswen/hitl]`.
- **Don't use `MessageGraph` for new code.** It's only "for basic chatbots";
  every production case in this skill uses `StateGraph` `[cheatsheet/gotchas]`.
- **Don't parallelize blindly.** "If one parallel node fails, the entire
  superstep fails atomically" — successful branches are discarded. Rate
  limits also hit faster `[aipractitioner/scaling]`.
- **Don't fan out with `Send` for fixed-cardinality work.** Static parallel
  edges are simpler. Reserve `Send` for genuinely runtime-variable workloads
  `[aipractitioner/scaling]`.
- **Don't trust that an LLM-only loop will terminate.** The text-to-SQL
  bug `[gh/6731]` is the canonical proof — always bound retries explicitly.

**Hard boundaries (LangGraph is the wrong tool when):**
- Latency budget < 200ms per call: checkpoint serialisation adds overhead.
- You need a *visual* drag-and-drop builder: that's Dify / n8n / LangFlow.
- You want zero-config role-based agents: that's CrewAI.
- You want a self-debugging code agent paradigm: AutoGen's strength
  `[bswen/compare]`.

---

## 生态对照 (Ecosystem Context)

Source: LangChain's own production page `[lc-built-with]`, the Bswen
side-by-side comparison `[bswen/compare]`, the OpenAgents comparison
`[openagents/2026]`, and the v1.0 vs functional-API blog `[lc-blog/functional]`.

| Dimension | LangGraph | CrewAI | AutoGen | OpenAI Swarm |
|---|---|---|---|---|
| **Mental model** | State machine / graph | Role-playing crew | Conversation between agents | Minimal handoff routine |
| **Time-to-prototype** | Hours-to-days | <1 hour | Moderate | <30 min |
| **Production-ready** | **Yes** (Klarna, Replit, Uber, LinkedIn, AppFolio, Elastic) | Limited (no built-in persistence) | Yes (maintenance mode 2026) | **No** (explicitly experimental) |
| **State management** | First-class, typed, reducer-merged | Implicit in task chain | In conversation history | Minimal |
| **Persistence / durability** | First-class (Sqlite/Postgres/Redis) | Bolt-on | Bolt-on | None |
| **Human-in-the-loop** | First-class (`interrupt()`) | Limited | Limited | None |
| **Observability** | LangSmith integration | Basic | Basic | Minimal |
| **Steepness** | Steep | Gentle | Moderate | Gentle |

Decision heuristics:

- **Reach for LangGraph when**: durability matters, the workflow has cycles or
  long-running threads, multiple users share threads, you already use the
  LangChain ecosystem, or you need to insert humans into the loop without
  duct-tape `[bswen/compare]`.
- **Reach for CrewAI when**: 24-hour proof-of-concept, role-based mental model
  fits the domain, no persistence needed. Many teams "use CrewAI for rapid
  prototyping to validate workflow logic, then port critical pipelines to
  LangGraph for production" `[bswen/compare]`.
- **Reach for AutoGen when**: code-generation tasks where self-healing /
  iterative refinement is the point — but note Microsoft has shifted focus
  to the broader Agent Framework, so AutoGen is effectively in maintenance
  mode `[bswen/compare]`.
- **Reach for Swarm only when**: studying multi-agent concepts as reference
  code. OpenAI itself labels it experimental `[bswen/compare]`.
- **Stay on plain LangChain when**: no cycles, no state across turns, single
  LLM call or simple RAG. LangGraph is overkill `[duplocloud/compare]`.

**Internal LangGraph subdivision** — also a choice point:

- `create_react_agent` (prebuilt): default for one tool-calling agent.
- Functional API (`@entrypoint`, `@task`): imperative Python style, shares
  the runtime, trades fine-grained time-travel for code brevity
  `[lc-blog/functional]`.
- `StateGraph`: full control, required for multi-agent / parallel / custom
  routing.

Pick the smallest one that fits the requirements; promote upward as needed.

---

## 附录: 引用速查 (Citation Index)

Short tags used inline → full sources in `references/`:

- `[lc-docs]` = https://docs.langchain.com/oss/python/langgraph/*
- `[lc-docs/why-langgraph]` / `[lc-docs/persistence]` /
  `[lc-docs/errors]` / `[lc-docs/streaming]` / `[lc-docs/subgraphs]`
- `[lc-blog/interrupt]` = www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt
- `[lc-blog/benchmark]` = www.langchain.com/blog/benchmarking-multi-agent-architectures
- `[lc-blog/production]` = www.langchain.com/blog/is-langgraph-used-in-production
- `[lc-blog/functional]` = www.langchain.com/blog/introducing-the-langgraph-functional-api
- `[lc-built-with]` = www.langchain.com/built-with-langgraph
- `[gh/langgraph-readme]` = github.com/langchain-ai/langgraph
- `[gh/6731]` = github.com/langchain-ai/langgraph/issues/6731
- `[zenml/uber]` = www.zenml.io/llmops-database/building-ai-developer-tools-using-langgraph-for-large-scale-software-development
- `[alphabold/case]` = www.alphabold.com/langgraph-agents-in-production/
- `[bswen/hitl]` = docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/
- `[bswen/compare]` = docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/
- `[openagents/2026]` = openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared
- `[eastondev/2026]` = eastondev.com/blog/en/posts/ai/20260424-langgraph-agent-architecture
- `[deepwiki/mapreduce]` = deepwiki.com/langchain-ai/langchain-academy/7.1-map-reduce-pattern
- `[deepwiki/subgraphs]` = deepwiki.com/langchain-ai/langgraph/3.5-control-flow-primitives
- `[swarnendu/best]` = www.swarnendu.de/blog/langgraph-best-practices/
- `[cheatsheet/gotchas]` = sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/
- `[bharatraj/state]` = medium.com/@bharatraj1918/langgraph-state-management-part-1
- `[duplocloud/compare]` = duplocloud.com/blog/langchain-vs-langgraph/
- `[dragonforest/timetravel]` = dragonforest.in/time-travel-in-langgraph/
- `[redis/checkpoint]` = redis.io/blog/langgraph-redis-checkpoint-010/
- `[aipractitioner/scaling]` = aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization
- `[agentsindex/v1]` = agentsindex.ai/blog/langgraph-tutorial
