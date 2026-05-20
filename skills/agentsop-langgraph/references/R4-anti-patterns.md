# R4 · Anti-patterns & Boundaries

The set of things you should not do, and the set of situations where
LangGraph is the wrong tool entirely. Each item has source + reasoning.

## Don'ts inside a LangGraph project

### AP-1 · Don't graph a stateless pipeline
A 3-step `prompt → tool → prompt` with no cycles, no HITL, no durability
requirement does not need LangGraph. The abstraction layer "could be a
disadvantage in more straightforward scenarios"
([duplocloud.com/blog/langchain-vs-langgraph](https://duplocloud.com/blog/langchain-vs-langgraph/)).
The complaint is recurrent:
> "The framework's complexity creates a steep learning curve, which is not
> merely a usability concern but a technical limitation that impacts
> development efficiency and maintenance."
> — same source.

### AP-2 · Don't use `recursion_limit` as control flow
> "It is not intended to be a primary control flow mechanism or a substitute
> for well-designed graph logic."
> — [sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)

Hitting it almost always means the conditional edge logic is wrong (see
Dilemma Case 1).

### AP-3 · Don't put side effects before `interrupt()`
On resume, the entire node body re-runs from the top. Charges/emails/DB
writes that ran the first time will run again
([cheatsheet/gotchas](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)).
Move the side effect to a downstream node + use idempotency keys.

### AP-4 · Don't mutate state inputs
> "Treat each node like a pure function: return a partial state update
> rather than mutating inputs."
> — [www.swarnendu.de/blog/langgraph-best-practices/](https://www.swarnendu.de/blog/langgraph-best-practices/)

Mutation breaks checkpoint replayability — the checkpointer captures the
return value, not the in-place edits.

### AP-5 · Don't share state between parallel branches without a reducer
Triggers `InvalidUpdateError`:
> "Missing reducer functions when multiple concurrent nodes update the same
> State key triggers `InvalidUpdateError`. Reducers are mandatory, not
> optional, for parallel execution."
> — [cheatsheet/gotchas](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)

### AP-6 · Don't run `checkpointer.setup()` at app boot
> "Handle this as part of a CI/CD migration script or a separate management
> command, not inside the primary application runtime."
> — [docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/](https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/)

### AP-7 · Don't leave interrupted threads to rot
> "A thread that is interrupted and nobody resumes it will have its state
> held in the checkpointer indefinitely; in production, implement a
> TTL-based expiry job."
> — same source. Recommended threshold: 24 h or domain-appropriate.

### AP-8 · Don't use `MessageGraph` for new code
> "Use StateGraph for complex workflows; MessageGraph only for basic
> chatbots."
> — [cheatsheet/gotchas](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)

Every production reference architecture in this skill uses `StateGraph`.

### AP-9 · Don't parallelize blindly
> "If one parallel node fails, the entire superstep fails atomically."
> — [aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)

Successful sibling work gets discarded; rate limits get hit faster. Use
parallelism when work is truly independent and you control rate budgets.

### AP-10 · Don't fan out with `Send` for fixed-cardinality work
Static parallel edges are simpler; `Send` is for **runtime-variable**
cardinality (the number of branches is decided per invocation).
"Reserve map-reduce for genuinely variable workloads. The cost of premature
complexity with map-reduce outweighs the flexibility it provides for fixed
workflows." — same source.

### AP-11 · Don't trust an LLM-only loop to terminate
Direct evidence: [github.com/langchain-ai/langgraph/issues/6731](https://github.com/langchain-ai/langgraph/issues/6731).
Always bound retries explicitly in state.

### AP-12 · Don't bloat state
State is pickled on every superstep into the checkpointer. Keep it
"lightweight and serializable" — large blobs go to object storage with a
URL in state, not the blob itself
([medium.com/@bharatraj1918](https://medium.com/@bharatraj1918/langgraph-state-management-part-1-how-langgraph-manages-state-for-multi-agent-workflows-da64d352c43b)).

### AP-13 · Don't rely on shared-state subgraphs for isolation
> "Subgraph state is only accessible when the subgraph is interrupted."
> — [aipractitioner.substack.com](https://aipractitioner.substack.com/p/scaling-langgraph-agents-parallelization)

If you need to inspect subgraph state during execution, design the parent
graph to surface key fields.

### AP-14 · Don't conflate `create_react_agent` with full LangGraph
The prebuilt is "syntactic sugar over the same graph mechanics"
([agentsindex.ai/blog/langgraph-tutorial](https://agentsindex.ai/blog/langgraph-tutorial)).
Teams that only ever use the prebuilt should ask whether they actually
needed LangGraph in the first place vs. a thinner agent loop.

### AP-15 · Don't skip LangSmith in production
Replaying a checkpoint locally only goes so far; production needs the
trace UI ([swarnendu.de/blog/langgraph-best-practices](https://www.swarnendu.de/blog/langgraph-best-practices/)).
The same team builds both — integration is first-class.

## Hard boundaries: when LangGraph is the wrong tool

| Situation | Reach for | Why not LangGraph |
|---|---|---|
| Latency-critical inference (< 200ms total) | Direct API call / vLLM | Checkpoint serialisation adds overhead per superstep |
| Visual drag-and-drop builder needed | Dify, n8n, LangFlow | LangGraph is code-first |
| Zero-config role-based crew | CrewAI | LangGraph is verbose for the role-playing mental model |
| Self-debugging code-generation agent | AutoGen | AutoGen's strength is the iterative refinement pattern (though it's in maintenance mode in 2026 — [bswen/compare](https://docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/)) |
| 24-hour proof of concept | CrewAI or Swarm | LangGraph onboarding is days, not hours |
| Stateless RAG over a single index | Plain LangChain / LlamaIndex | No cycles, no state-between-turns |
| Embedded in a non-Python / non-JS stack | Native HTTP to LangGraph Platform, or a different framework | LangGraph SDKs are Python + JS/TS |

## Documentation hazards (as of mid-2026)

- v1 Python docs were marked "Alpha – content incomplete and subject to
  change" — early adopters complain that the API moves faster than the
  guide ([duplocloud/compare](https://duplocloud.com/blog/langchain-vs-langgraph/)).
- TypeScript guide gap noted in the same source.
- Security: SQL injection CVE reported March 2026 in the SQLite
  checkpointer ([thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html](https://thehackernews.com/2026/03/langchain-langgraph-flaws-expose-files.html)).
  Use Postgres in production; keep deps current.

## Cultural anti-pattern

Building "agentic" because it's fashionable.

> "LangGraph is potentially overcomplicated for single-agent tasks."
> — [docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/](https://docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/)

If you'd ship the same value with a single LLM call + a tool, do that. The
question to ask before adding a graph is: *what would resume look like if
this thread crashed at step N?* If you don't care, you don't need LangGraph.
