# R5 · Ecosystem Context

How LangGraph sits relative to its closest neighbours, and how to choose
between them.

## Position statement

LangChain's own framing (2026):

> "LangGraph proved itself for production with real users depending on the
> system. LangGraph is recommended if you need production-grade durability,
> precise state management, and are already using LangChain."
> — [www.langchain.com/built-with-langgraph](https://www.langchain.com/built-with-langgraph)

Independent assessment from the framework comparison:

> "LangGraph is best for production workflows where reliability matters,
> AutoGen is for code tasks where self-healing is valuable, and CrewAI is
> for rapid prototyping when you need to prove a concept fast."
> — [docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/](https://docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/)

## Comparison matrix

| Dimension | LangGraph | CrewAI | AutoGen | OpenAI Swarm |
|---|---|---|---|---|
| **Paradigm** | State machine / graph | Role-based crew | Conversation between agents | Minimal handoff routine |
| **Origin** | LangChain team (2024+) | crewAIInc | Microsoft Research | OpenAI |
| **Production status (2026)** | First-class | "Limited; lacks persistence" | "Maintenance mode" | "Not production-ready" |
| **Setup time** | Hours-to-days | "Within an hour" | Moderate | <30 min |
| **State management** | First-class typed state, reducers | Implicit in task chain | In conversation history | Minimal |
| **Persistence** | First-class (Sqlite/Postgres/Redis) | None built-in | Bolt-on | None |
| **Human-in-the-loop** | First-class `interrupt()` | Limited | Limited | None |
| **Streaming** | 5 stream modes, token-level | Limited | Limited | Limited |
| **Observability** | LangSmith, time-travel debugging | Basic logs | Basic | Minimal |
| **Multi-agent patterns** | Supervisor / Swarm / Hierarchical | Role-based crew | Conversational | Handoff |
| **Steepness** | "Steep learning curve" | "Excellent documentation" | Moderate | Gentle |

Sources for the table:
- [docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/](https://docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/)
- [openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared](https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared)
- [aaronyuqi.medium.com/first-hand-comparison-of-langgraph-crewai-and-autogen-30026e60b563](https://aaronyuqi.medium.com/first-hand-comparison-of-langgraph-crewai-and-autogen-30026e60b563)

## When to reach for LangGraph specifically

- **Workflow has cycles** — reflection, retry, multi-step planning.
- **Threads must outlive processes** — crashes, restarts, deploys must not
  reset agent state.
- **Multiple users share threads** — multi-tenant production, requires
  durable per-thread state.
- **HITL is a requirement, not a nice-to-have** — payments, approvals,
  edits, compliance gates.
- **Multi-agent topology with parallelism** — supervisor/swarm/hierarchical
  patterns over LangGraph primitives.
- **Already in LangChain ecosystem** — LangSmith, LangChain Runnables,
  LangChain Hub all interop natively.

## When to reach for an alternative

### CrewAI
- 24-hour PoC where the role-playing metaphor matches the domain.
- Demos / prototypes where persistence isn't a requirement.
- "Some teams use CrewAI for rapid prototyping to validate workflow logic,
  then port critical pipelines to LangGraph for production"
  ([bswen/compare](https://docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/)).

### AutoGen
- Code-generation tasks where self-healing / iterative refinement is the
  product (the agent debugs its own code).
- **Caveat (2026):** "AutoGen is effectively in maintenance mode as
  Microsoft shifted focus to its broader Agent Framework, and major feature
  development has stopped" — same source. Adopt with eyes open.

### OpenAI Swarm
- Studying multi-agent concepts; reference-code reading.
- Not production: OpenAI explicitly labels it experimental.

### Plain LangChain
- No cycles, no state-between-turns, no HITL — a single LLM call wrapped
  in a Runnable.

### vLLM / SGLang / TensorRT-LLM
- Different layer entirely — these are inference engines. Your LangGraph
  graph *calls* them through model providers.

### Dify / LangFlow / n8n
- Visual builder is required by the team (no-code/low-code stakeholders).
- LangGraph is code-first.

### Aider / Cursor / Cline
- Pair-programming UX is the deliverable, not an agent service. These have
  LangGraph-like internals but are end-user products.

## Internal LangGraph subdivision

Even within LangGraph there is a three-way choice:

| API | Best for | Trade-off |
|---|---|---|
| `create_react_agent` | Single agent, tool calling | Hides graph; outgrown when topology gets complex |
| Functional API (`@entrypoint`, `@task`) | Imperative Python style | "The inability to time travel in the functional API is one of [its] critical differences" — [docs.langchain.com/oss/python/langgraph/functional-api](https://docs.langchain.com/oss/python/langgraph/functional-api) |
| `StateGraph` | Full control | Most verbose; required for parallel / supervisor / custom routing |

Recommendation from the v1 tutorials:
> "Start with `create_react_agent` for any standard tool-calling agent.
> […] If you find yourself needing parallel node execution, a
> supervisor-worker pattern, custom retry logic, or complex branching,
> migrate to a manual `StateGraph`."
> — [agentsindex.ai/blog/langgraph-tutorial](https://agentsindex.ai/blog/langgraph-tutorial)

## Why companies pick LangGraph in 2026

Production page roll-call ([www.langchain.com/built-with-langgraph](https://www.langchain.com/built-with-langgraph) + [/is-langgraph-used-in-production](https://www.langchain.com/blog/is-langgraph-used-in-production)):

- **Klarna** — AI Assistant for 85M users, 80% reduction in resolution time.
- **Replit** — Multi-agent code-generation agent, drove LangSmith
  ingestion improvements.
- **Uber** — "Lang Effect" framework wrapping LangGraph; thousands of daily
  code fixes; ~21,000 developer hours saved
  ([zenml.io/llmops-database/.../building-ai-developer-tools-using-langgraph](https://www.zenml.io/llmops-database/building-ai-developer-tools-using-langgraph-for-large-scale-software-development)).
- **LinkedIn** — AI recruiter on hierarchical agent system.
- **AppFolio** — Realm-X copilot, saves >10 hours/week per property
  manager, 2x accuracy improvement.
- **Elastic** — Real-time threat detection orchestration.

Common thread in every case:
> "All companies selected LangGraph specifically for reliability,
> observability, and control capabilities needed for production deployment."
> — [www.langchain.com/blog/is-langgraph-used-in-production](https://www.langchain.com/blog/is-langgraph-used-in-production)

## Trend hypothesis (2026)

The "Year of Stateful Orchestration" framing
([eastondev.com](https://eastondev.com/blog/en/posts/ai/20260424-langgraph-agent-architecture/))
implies the agent space is bifurcating:

- **Top layer**: declarative, role-based, fast prototyping (CrewAI, Swarm,
  ChatGPT GPTs).
- **Bottom layer**: explicit, stateful, durable, observable orchestration
  (LangGraph, Temporal-style engines, Dapr Agents).

The pattern "prototype on top, ship on bottom" is becoming standard:
PoC in CrewAI → port to LangGraph for production. This is the ecosystem
position LangGraph is consolidating in 2026.

## One paragraph for the impatient reader

If you have an agent that must survive crashes, host conversations across
sessions, accept human approvals, and be debugged in production — start
with LangGraph + `create_react_agent`, graduate to a hand-built
`StateGraph` when topology demands it, anchor on Postgres checkpointers,
and pay the LangSmith bill. If you are building a 24-hour demo or a
stateless RAG pipeline, do not use LangGraph; use CrewAI or plain
LangChain. If you are doing code-gen self-debugging, AutoGen is the better
metaphor but it's in maintenance mode — factor that into adoption risk.
