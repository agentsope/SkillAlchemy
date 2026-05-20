# R2 · SOP Workflow

The end-to-end protocol for bringing a LangGraph agent from idea to production.

## Phase 0 · Decide if you need a graph at all

Cheap-test before building:
- Has the workflow ≥1 cycle (retry / reflect / re-tool)?
- Must it survive a process crash?
- Will humans inspect or override mid-run?
- Are there ≥2 specialists that hand off?

If **all four are no** — use plain LangChain or raw API calls. Verbose-by-default
is LangGraph's tax; pay it only when justified
([duplocloud.com/blog/langchain-vs-langgraph](https://duplocloud.com/blog/langchain-vs-langgraph/)).

## Phase 1 · Bootstrap (10 min target)

1. `pip install langgraph` (current stable: 1.2.0, May 2026 —
   [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)).
2. For a **standard tool-calling agent**: `create_react_agent(model, tools)`.
3. Test with `agent.invoke({"messages": [HumanMessage(...)]})`.
4. Add `MemorySaver()` as checkpointer + a `thread_id` config to start
   experiencing the stateful loop.

Source: [agentsindex.ai/blog/langgraph-tutorial](https://agentsindex.ai/blog/langgraph-tutorial)
"Start with `create_react_agent` for any standard tool-calling agent."

## Phase 2 · Promote to StateGraph when the prebuilt cracks

Triggers to leave the prebuilt:
- Need a state field that isn't `messages`.
- Need a supervisor or specialist handoff.
- Need parallel work via `Send`.
- Need custom retry / backoff that the LLM can't be trusted to do itself
  (see Dilemma Case 1 + [github.com/langchain-ai/langgraph/issues/6731](https://github.com/langchain-ai/langgraph/issues/6731)).

Refactor pattern:
```python
class S(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    retries: Annotated[int, operator.add]
    # …other typed fields
g = StateGraph(S)
g.add_node("llm", call_llm); g.add_node("tools", ToolNode(tools))
g.add_conditional_edges("llm", route)        # END or "tools"
g.add_edge("tools", "llm")
g.set_entry_point("llm")
graph = g.compile(checkpointer=postgres_saver)
```

## Phase 3 · Pick the multi-agent topology

Decision logic from LangChain's own benchmark
([www.langchain.com/blog/benchmarking-multi-agent-architectures](https://www.langchain.com/blog/benchmarking-multi-agent-architectures)):

- **Supervisor** — one router agent delegates to specialists. Highest token
  cost (the "translation" / "game of telephone" overhead). Best when
  sub-agents are third-party or you need one auditable funnel.
- **Swarm** — agents hand off control dynamically; the system remembers the
  last active agent. Lower tokens, slightly higher accuracy in the τ-bench
  retest. Requires each sub-agent to know the others. Bad for third-party
  agents.
- **Hierarchical Teams** — supervisor-of-supervisors. Reach for it only when
  6+ specialists need grouping (see
  [langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/)).
- **Tool-calling supervisor (current default recommendation)** — implement
  the supervisor via tool-calling rather than the `langgraph-supervisor`
  library; gives more control over context engineering
  ([reference.langchain.com/python/langgraph-supervisor](https://reference.langchain.com/python/langgraph-supervisor)).

Apply LangChain's three documented supervisor fixes for ~50% perf gain:
removing handoff messages, using a forwarding-messages tool, tool-name
optimization
([www.langchain.com/blog/benchmarking-multi-agent-architectures](https://www.langchain.com/blog/benchmarking-multi-agent-architectures)).

## Phase 4 · Add human-in-the-loop

The `interrupt()` API was introduced specifically because older
`NodeInterrupt` / breakpoint primitives were too limiting. Official rationale:

> "Over the past few months, we've seen developers want to do more and more
> complicated things, and so we've added a new tool to help with this. […]
> `interrupt` will pause execution of the graph, mark the thread you are
> running as `interrupted`, and put whatever you passed as an input to
> `interrupt` into the persistence layer."
> — [www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt)

Four canonical patterns, picked per node:

1. Approve / Reject — review a critical step before it runs.
2. Review & Edit State — human corrects mid-run.
3. Review Tool Calls — oversee LLM-requested actions.
4. Multi-turn Conversation — back-and-forth in multi-agent setups.

Resume: `graph.invoke(Command(resume=value), config)`.

**Operational rules** (sourced from [docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/](https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/)):

- Interrupt only on "irreversible, high-blast-radius actions" — not every step.
- Side effects must go **after** the interrupt, not before, because resume
  re-runs the entire node body.
- Use a persistent checkpointer (Postgres recommended). Run `setup()` as
  a CI/CD migration, not at app boot.
- Implement a TTL sweep for orphaned threads — otherwise state accumulates
  in the checkpointer indefinitely.

## Phase 5 · Choose the durability backend

| Backend | When | Cite |
|---|---|---|
| `InMemorySaver` | Notebooks, tests | [docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence) |
| `SqliteSaver` | Single-machine local dev | same |
| `PostgresSaver` | Production multi-user default; ACID; same backend LangSmith uses | same |
| `RedisSaver` | High-throughput swarms, sub-ms reads, TTL'd sessions | [redis.io/blog/langgraph-redis-checkpoint-010](https://redis.io/blog/langgraph-redis-checkpoint-010/) |

## Phase 6 · Bound the loop

Default `recursion_limit` is 25. Raise via
`graph.invoke({...}, {"recursion_limit": 100})`.

**Do not** use `recursion_limit` as your termination strategy. From the
official error doc ([docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT)):

> "If you are not expecting your graph to go through many iterations, you
> likely have a cycle. Check your logic for infinite loops."

Real bug in the wild: [github.com/langchain-ai/langgraph/issues/6731](https://github.com/langchain-ai/langgraph/issues/6731)
— text-to-SQL agent retried a broken query 20 times. Maintainer marked it
"not planned." Fix is downstream: counter in state + exit edge.

## Phase 7 · Wire observability

- **LangSmith** is the default trace + replay UI. Same team builds both;
  the integration is first-class.
- Streaming modes for UX vs. ops
  ([docs.langchain.com/oss/python/langgraph/streaming](https://docs.langchain.com/oss/python/langgraph/streaming)):
  - `values` — full state snapshot each step
  - `updates` — state diffs (default)
  - `messages` — token-level LLM stream (use for UI)
  - `custom` — your own progress events
  - `debug` — every node entry/exit, tool I/O, errors
- **Time-travel** for debugging:
  > "When replaying from a checkpoint, the agent knows that this checkpoint
  > has already been executed and will just display the historical output
  > instead of making new LLM calls."
  > — [dragonforest.in/time-travel-in-langgraph/](https://dragonforest.in/time-travel-in-langgraph/)

## Phase 8 · Ship and iterate

- Deploy via LangGraph Platform or self-host. Platform is the team's
  "purpose-built deployment platform for agents"
  ([github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)).
- Test at graph-level: "construct a tiny state, invoke/ainvoke, and assert
  on the resulting state and chosen edge" — mock external tools deterministically
  ([www.swarnendu.de/blog/langgraph-best-practices](https://www.swarnendu.de/blog/langgraph-best-practices/)).
- Production case studies for what "shipped" looks like:
  - **Klarna**: 85M users, 80% reduction in resolution time
    ([www.langchain.com/blog/is-langgraph-used-in-production](https://www.langchain.com/blog/is-langgraph-used-in-production)).
  - **Uber**: "thousands of daily code fixes, 10% improvement in developer
    platform coverage, ~21,000 developer hours saved"
    ([zenml.io/llmops-database/building-ai-developer-tools-using-langgraph-for-large-scale-software-development](https://www.zenml.io/llmops-database/building-ai-developer-tools-using-langgraph-for-large-scale-software-development)).
  - **AppFolio**: copilot Realm-X saves "over 10 hours per week" with
    "2x accuracy improvement"
    ([www.langchain.com/blog/is-langgraph-used-in-production](https://www.langchain.com/blog/is-langgraph-used-in-production)).
  - **Replit**: AI agent with "hundreds of steps" per run forced
    LangSmith ingestion improvements
    ([alphabold.com/langgraph-agents-in-production](https://www.alphabold.com/langgraph-agents-in-production/)).
