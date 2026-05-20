# R1 · Architecture & Mental Model

## TL;DR

LangGraph is best understood as a **state machine for LLMs** — explicitly an
inheritor of finite-state-machine / BPMN / Pregel-style thinking, not of Unix
pipes or LangChain Runnables. Its maintainers call it
> "a low-level orchestration framework for building, managing, and deploying
> long-running, stateful agents"
> — [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) (README, v1.2.0, May 2026)

The single sentence that captures the OS-level shift:
> "If chains were about passing outputs between steps, graphs are about
> maintaining and evolving a shared state over time."
> — [eastondev.com/blog/en/posts/ai/20260424-langgraph-agent-architecture/](https://eastondev.com/blog/en/posts/ai/20260424-langgraph-agent-architecture/)

## The four primitives the framework exposes

| Primitive | Role | Notes |
|---|---|---|
| **State** | The system's working memory, schema-typed (TypedDict / Pydantic). Every node reads + writes it. | "State is the single source of truth for your LangGraph workflow design" — [medium.com/@bharatraj1918](https://medium.com/@bharatraj1918/langgraph-state-management-part-1-how-langgraph-manages-state-for-multi-agent-workflows-da64d352c43b) |
| **Node** | A function (sync/async) `(state) -> partial_state_update`. | Recommended to be pure — see best-practices [swarnendu.de/blog/langgraph-best-practices](https://www.swarnendu.de/blog/langgraph-best-practices/). |
| **Edge** | Static, conditional (`add_conditional_edges`), or dynamic (`Send`). | Edges encode *control flow over state*, not data flow. |
| **Checkpointer** | Persists full state after every superstep (InMemory / Sqlite / Postgres / Redis). | Unlocks durable execution, HITL, time-travel. |

## Why "graph" not "chain"

The official answer:
> "2026 is the year of Stateful Orchestration—we are no longer just passing
> text between steps, but building structured, stateful systems that can
> reason across multiple stages, recover from failure, and adapt over time."
> — [eastondev.com](https://eastondev.com/blog/en/posts/ai/20260424-langgraph-agent-architecture/)

Three concrete forcing functions push you off chains:

1. **Cycles are first-class.** A ReAct agent is fundamentally
   `LLM → Tool → LLM → Tool → … → LLM (final answer)`. Chains can express
   this only by hiding the loop in an "agent executor" black box.
2. **State must survive failures.** Chains have no opinion on persistence;
   LangGraph snapshots state after every node so the same `thread_id`
   resumes exactly where it crashed.
3. **State must be inspectable / editable.** HITL requires pausing,
   inspecting, possibly mutating state, then resuming — chains have no
   stable "state" to pause on.

## Reducers: the algebra that makes parallelism safe

State updates merge via **reducers**. The default is "last write wins"; for
chat history you use `Annotated[list[Msg], add_messages]`; for accumulating
lists `Annotated[list, operator.add]`.

> "Reducers are mandatory, not optional, for parallel execution."
> — [sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)

The `add_messages` reducer has one extra trick:
> "If a message with the same ID already exists, it updates that message in
> place rather than duplicating it." — secondary source on state design

This is what enables `interrupt()` + edit-state HITL: a human can edit the
last AI message in-place, resume, and the agent sees the edited version.

## Checkpointing: the OS-level innovation

> "Durable execution — Agents persist through failures and resume from their
> exact stopping point."
> — [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) README

Backends available:

- `InMemorySaver` — tests
- `SqliteSaver` / `AsyncSqliteSaver` — local dev (security: SQL injection
  CVE was reported in March 2026 in this implementation —
  [thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html](https://thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html))
- `PostgresSaver` / `AsyncPostgresSaver` — production default; the same
  backend LangSmith uses ([docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence))
- `RedisSaver` — sub-ms latency, TTL'd sessions, "particularly well-suited
  for short-lived conversational agents"
  ([redis.io/blog/langgraph-redis-checkpoint-010/](https://redis.io/blog/langgraph-redis-checkpoint-010/))

## Three execution APIs over the same runtime

| API | Best for | Trade-off |
|---|---|---|
| `create_react_agent` | One agent + tools, no special routing | Hides graph; easy to outgrow |
| Functional API (`@entrypoint`/`@task`) | Imperative Python style | "inability to time travel in the functional API is one of [its] critical differences" — [docs.langchain.com/oss/python/langgraph/functional-api](https://docs.langchain.com/oss/python/langgraph/functional-api) |
| `StateGraph` | Full control: parallel, supervisor, custom routing | Most verbose, steepest curve |

The team's explicit positioning:
> "Both APIs use the same underlying runtime, allowing you to mix and match
> the two paradigms."
> — [www.langchain.com/blog/introducing-the-langgraph-functional-api](https://www.langchain.com/blog/introducing-the-langgraph-functional-api)

## Pre-LLM lineage

- **Pregel** (Google's graph compute model) → supersteps, where each step
  executes all eligible nodes in parallel, then merges.
- **BPMN / state machines** → explicit nodes, edges, decision gates,
  start/end events.
- **Workflow engines (Airflow, Temporal)** → durable execution via
  checkpoints; resumability after crash. Temporal in particular is the
  closest cousin philosophically.

This lineage is what gives LangGraph its "boring infrastructure" feel
compared to CrewAI's role-playing or AutoGen's chat-driven emergence.

## Where the mental model leaks

- **Subgraph state is invisible during execution** — "subgraph state is only
  accessible when the subgraph is interrupted"
  ([aipractitioner.substack.com](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)).
- **Resuming an `interrupt()` re-runs the whole node body**, not just the
  line after `interrupt()` — [cheatsheet/gotchas](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/).
- **Parallel super-steps are atomic on failure** — one failed branch
  discards successful siblings ([aipractitioner](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)).

The mental model is *state + reducers + supersteps + checkpoints*. Holding
all four in mind is the cost of admission.
