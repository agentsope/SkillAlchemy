# R3 · Dilemma Cases

Hard decisions taken from real production reports, GitHub issues, and the
LangChain team's own published bench. Each case follows
**困境 / 约束 / 决策步骤 / 结果 / 可提取的操作**.

---

## Case 1 · Text-to-SQL agent loops 20× to `GRAPH_RECURSION_LIMIT`

**Source**: [github.com/langchain-ai/langgraph/issues/6731](https://github.com/langchain-ai/langgraph/issues/6731)
(filed late 2025/early 2026, LangGraph 1.0.6).

### 困境
A team built a text-to-SQL agent on LangGraph that worked on 0.6.x but broke
on 1.0.6. When the Databricks query returned an error, the agent retried the
same broken SQL 20 times until the default `recursion_limit` fired. Stack
trace showed the same query string being cached and reissued.

### 约束
- Cannot pin to 0.6.x — security fixes only in 1.x.
- Maintainer marked the issue **"not planned"** — no upstream patch coming.
- Business needs the agent live; quota cost rising on Databricks side.

### 决策步骤
1. **Reject** raising `recursion_limit`. The cheatsheet is explicit:
   > "Hitting the limit typically indicates an underlying design flaw."
   > — [sumanmichael.github.io/langgraph-cheatsheet](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)
2. Add explicit retry tracking to state:
   ```python
   class S(TypedDict):
       messages: Annotated[list[AnyMessage], add_messages]
       retries: Annotated[int, operator.add]
       last_error: str | None
   ```
3. After the tool node, increment `retries` on SQL error; in the conditional
   edge, route to `END` (or a "give up, ask the user" node) once
   `retries >= 3`.
4. Surface the error content back into the LLM prompt — the *text* of the
   SQL error usually tells the LLM whether to retry or abandon.
5. Add a regression test that injects a permanent SQL error and asserts the
   graph terminates within 3 iterations.

### 结果
Bounded retries. Quota cost capped. Observable failure mode (`last_error`
visible in checkpoint history). LangSmith trace shows the exit edge firing.

### 可提取的操作
**OP-9 (Bound an agent loop)**. **Always** bake an explicit retry counter
into state for any cyclic graph. Trust nothing the LLM does to terminate
itself. The recursion limit is a safety net for runaway code, not a primary
control flow mechanism — direct quote from
[docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT):

> "If you are not expecting your graph to go through many iterations, you
> likely have a cycle. Check your logic for infinite loops."

---

## Case 2 · Supervisor vs. swarm in a multi-domain customer support agent

**Source**: synthesised from LangChain's own benchmark
([www.langchain.com/blog/benchmarking-multi-agent-architectures](https://www.langchain.com/blog/benchmarking-multi-agent-architectures))
and the framework comparison
([docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/](https://docs.bswen.com/blog/2026-04-29-agent-framework-production-comparison/)).

### 困境
A team needed a customer-service agent covering retail, billing, and
shipping. Their initial supervisor implementation had:
- Double the token budget they expected
- Noticeable latency from the "translation" step
- Users complaining about being "transferred" between specialists

They considered tearing it down and rebuilding as a swarm.

### 约束
- Specialists are internal — they *can* know about each other (a precondition
  for swarm).
- Users expect continuous conversation in one domain — they don't want to
  feel they are being passed between agents.
- Compliance requires a single, auditable funnel for tool invocation.

### 决策步骤
1. **Consult LangChain's own bench**: swarm "slightly outperformed
   supervisor across all scenarios"; supervisor uses more tokens because of
   the "translation" the supervisor is doing — they explicitly compare it to
   "a game of telephone"
   ([www.langchain.com/blog/benchmarking-multi-agent-architectures](https://www.langchain.com/blog/benchmarking-multi-agent-architectures)).
2. **Map constraints to patterns**: compliance favours supervisor (single
   funnel for audit); UX favours swarm (last-active agent stays active).
3. **Try supervisor's documented fixes first** — LangChain published three
   improvements that yielded "a nearly 50% increase in performance":
   - Remove handoff messages (declutter context).
   - Add a forwarding-messages tool (prevent paraphrasing errors).
   - Optimise tool names (improve routing).
4. Re-bench in-domain. If gains close the gap to swarm, keep supervisor.
   Otherwise, migrate to swarm and replace the audit log with checkpoint
   history + LangSmith traces.

### 结果
Hybrid: supervisor topology with tuned tools captures most of swarm's
efficiency while preserving the single-funnel audit log. Compliance happy,
costs in budget.

### 可提取的操作
**Anchor pattern choice on constraints, not aesthetics.** The two binary
questions:
- Do sub-agents know about each other? (No → supervisor or hierarchical.)
- Is one user-facing voice mandatory? (Yes → supervisor.)

Apply LangChain's three documented supervisor fixes before considering
paradigm migration.

---

## Case 3 · Replit-scale traces overwhelmed LangSmith

**Source**: [www.alphabold.com/langgraph-agents-in-production/](https://www.alphabold.com/langgraph-agents-in-production/)
and [www.langchain.com/blog/is-langgraph-used-in-production](https://www.langchain.com/blog/is-langgraph-used-in-production).

### 困境
Replit Agent generates entire applications "from planning to deployment."
Trace depth was "hundreds of steps" per run. The same team's own
observability tool (LangSmith) initially couldn't ingest or render the
traces.

### 约束
- Graph depth is intrinsic to the product — can't trim.
- Need debuggability for a multi-agent system with HITL approval steps.
- Cost of replaying expensive LLM nodes must be bounded.

### 决策步骤 (reconstructed)
1. **Treat observability as part of the system design.** Replit and
   LangChain co-evolved LangSmith ingestion + rendering for this trace
   shape. The implication for any agent designer pushing graph depth:
   plan the trace consumer alongside the graph.
2. **Use subgraphs to chunk the topology** into named teams (planner,
   codegen, test, deploy). Flat graphs with hundreds of nodes are
   unreadable; subgraphs give you a navigable hierarchy
   ([deepwiki.com/langchain-ai/langgraph/3.5-control-flow-primitives](https://deepwiki.com/langchain-ai/langgraph/3.5-control-flow-primitives)).
3. **Use the `Send` API for runtime fan-out** (e.g., generate-then-test in
   parallel per file). Static parallel edges aren't expressive enough when
   the cardinality is data-dependent.
4. **Use `interrupt()` at deploy boundary.** Humans approve a deploy plan
   instead of letting the agent push autonomously — bounds blast radius.
5. **Use time-travel for failed runs.** Fork from the last good checkpoint
   to test prompt variants without re-paying upstream LLM cost
   ([dragonforest.in/time-travel-in-langgraph/](https://dragonforest.in/time-travel-in-langgraph/)).

### 结果
Replit Agent ships. The friction surfaced fed back into LangSmith
improvements. Reported scale: agent supports building full applications
from scratch, multi-agent architecture with HITL.

### 可提取的操作
**For agents with > ~50 steps per run:**
- Subgraphs are not a stylistic choice — they are the only way the trace
  remains navigable.
- `Send` for runtime parallelism, not for known cardinality (static parallel
  edges are simpler).
- HITL at the deploy / write-to-prod boundary, not at every step.
- Treat checkpoints as the unit of reproducibility, not the prompt.

---

## Case 4 · Side effects before `interrupt()` re-execute on resume

**Source**: [sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)
listed as a "common pitfall for beginners." Synthesised real-world
manifestation: payment flow.

### 困境
A team built a payment workflow:
```python
def charge_node(state):
    payment.charge(state["amount"])          # side effect
    confirmation = interrupt({"amount": state["amount"]})  # HITL
    return {"confirmation": confirmation}
```
On resume, the customer was charged **twice** because LangGraph
"re-runs the entire node function" on resume.

### 约束
- HITL cannot be removed (compliance).
- Cannot silently undo charges.
- Payment SDK can't be rewritten.

### 决策步骤
1. **Recognise the runtime semantic**: resume re-enters the node from the
   top, not from the line after `interrupt()`. Treat every node body as
   potentially re-runnable. (Cheatsheet quote: "resuming from an `interrupt`
   *re-runs the entire node function*".)
2. **Restructure topology**: move the charge into a downstream node that
   runs *after* the interrupt-bearing node returns. The interrupt node
   only proposes; the next node executes.
   ```python
   propose_node  --interrupt--> approve_decision --> charge_node
   ```
3. **Belt-and-braces idempotency**: generate a `charge_id` in state before
   `interrupt`; pass it to the payment SDK as an idempotency key. Re-run
   becomes a no-op even if topology drifts.

### 结果
One charge per approval. Resume-safe by construction.

### 可提取的操作
- **Two-line rule**:
  1. Nothing irreversible before `interrupt()` in the same node.
  2. Every external side-effect uses an idempotency key drawn from state.
- Source: [docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/](https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/)
  ("position side effects *after* interrupt or in separate downstream
  nodes") + [cheatsheet/gotchas](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/).

---

## Cross-case takeaways

1. **Termination, idempotency, and side-effect ordering are the three
   operating concerns the framework does NOT solve for you.** It gives you
   the primitives (state, reducers, checkpoints, interrupt) but you must
   design the discipline.
2. **LangChain's own published benchmarks and bug fixes are first-class
   sources** — read the post before reinventing.
3. **At scale, observability shapes architecture.** Subgraphs + `Send` +
   time-travel are not optimisations; they are the only sustainable way to
   debug deep graphs.
