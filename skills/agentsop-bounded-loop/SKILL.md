---
name: agentsop-bounded-loop
version: 0.1.0
description: >-
  Universal discipline for any LM-driven loop — agent retries, plan-act-observe, multi-agent
  handoffs, optimiser passes, test-fix cycles. Encodes the one rule every framework
  documents quietly and every team relearns expensively: the LM in the loop is NEVER a
  reliable terminator. Termination must be provided by an explicit counter + exit predicate
  + stagnation signal + escalation path that live OUTSIDE the LM's control. This is a tool-
  level, framework-agnostic skill. It maps onto LangGraph (recursion_limit + state counter +
  interrupt), CrewAI (max_iter + max_rpm + human_input), Claude / OpenAI SDKs
  (max_iterations + tool_use_budget), DSPy (declared evaluation budget), Aider (REPL +
  explicit retry cap), and AutoGen (max_consecutive_auto_reply). Search keywords: infinite
  loop, recursion limit, recursion_limit, GraphRecursionError, max iterations, max_iter,
  agent stuck, agent won't stop, runaway agent, ReAct loop not terminating, agent repeating
  itself.
---

# bounded-loop · O7

> Source posture: every load-bearing claim is cited inline with a short tag
> resolved against `references/R1-source-evidence.md` and
> `references/R2-cross-framework.md`. Examples cite the real GitHub issues
> they're distilled from.

---

## 1. 何时激活 (Activation Rules)

Activate this skill when **any** of the following is true:

- The task involves a workflow that contains a **cycle** — tool-call → reflect
  → retry, plan → act → observe → re-plan, draft → critique → revise,
  test → fix → re-test.
- The user is hitting a framework's "loop too deep" error:
  `GRAPH_RECURSION_LIMIT` (LangGraph), `MaxIterationsExceeded` (LangChain
  `AgentExecutor`), "agent exceeded max_iter" (CrewAI), `max_turns reached`
  (OpenAI Agents SDK), `stop_reason="max_tokens"` mid-tool-use (Anthropic).
- The user proposes "let's just raise the limit" / "set max_iter to 100" /
  `recursion_limit=200` — this is the canonical anti-pattern this skill
  exists to prevent.
- The user is building a **multi-agent** system with delegation, handoff,
  or supervisor patterns — these are exposure-multipliers for unbounded
  loops (see `[gh/crewai-330]`).
- The user is building an **optimiser / evaluator loop** (DSPy, AutoEval,
  RLHF, self-refining agent) where "stop when good enough" is the
  termination criterion — this is *never* sufficient on its own.
- The user wants a **test-fix loop**, **self-healing code agent**, or
  **iterative refinement** workflow — every code-agent in production
  (Cursor, Aider, Devin, Claude Code) ships with an explicit step budget.

Do **not** activate for: single LLM calls, one-shot RAG queries, stateless
tool pipelines, or flows where the cycle is provably bounded by data (e.g.,
"iterate once per row in this fixed list").

---

## 2. 核心心智模型 (Core Mental Model)

**Every loop body must produce a state change that proves progress — and
the proof must be checkable without calling another LM.**

Read that twice. It contains four claims:

1. **The body must change state.** A no-op iteration (same input → same
   output) is the definition of a stuck loop. If your body might return
   the same value twice, the loop is already broken; the safety net just
   hasn't fired yet.

2. **The change must be progress, not just diff.** A retry that says "I
   tried again, same error" is a change but not progress. The witness has
   to be monotone: counter strictly increasing, error list strictly
   shrinking, confidence strictly rising, or a new fact added to the plan.

3. **The proof must be checkable.** Pure Python. A `dict.get("retries") < N`,
   not `await llm.ainvoke("are we done?")`. If you ask the LM to evaluate
   termination, you've recreated the problem one level up — now *that* loop
   needs bounding.

4. **The LM is not allowed to vote.** It can *suggest* finality
   (`stop_reason="end_turn"`, `final_answer` tool, etc.) but the framework
   must verify against the predicate before terminating. Otherwise an LM
   that always says "let me try once more" runs forever.

### Why the framework's default safety net is not enough

Every framework ships a default cap:

- LangGraph: `recursion_limit=25` `[lc-docs/errors]`
- CrewAI: `Agent.max_iter=20`, `Crew.max_rpm` `[crewai-docs/agents]`
- LangChain `AgentExecutor`: `max_iterations=15` (deprecated default)
- OpenAI Agents: `Run.max_turns`
- Anthropic Messages: `max_tokens` per call (per-call, not per-loop)

These are **billing safety nets**, not control flow. The LangGraph docs
say so explicitly:

> "If you are not expecting your graph to go through many iterations, you
> likely have a cycle. Check your logic for infinite loops."
> — `[lc-docs/errors]` `https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT`

And the cheatsheet adds:

> "Hitting the limit typically indicates an underlying design flaw. The
> recursion limit is a safety net for runaway code, not a primary control
> flow mechanism."
> — `[cheatsheet/gotchas]`

When you raise the limit to "fix" the error, you've **moved the bug
further away**, not removed it. The text-to-SQL agent in `[gh/6731]`
would have hit `recursion_limit=100` after burning 5× the Databricks
quota.

### The three-axis termination model

A bounded loop has three independent termination axes; you need at least
two firing in series:

```
                ┌─── (a) success predicate met → exit success
                │
[loop body] ────┼─── (b) counter / budget exhausted → exit escalation
                │
                └─── (c) stagnation detected → exit escalation
```

If you only have (a), the LM controls termination — it doesn't.
If you only have (b), you'll burn the budget on N identical iterations.
If you only have (c), one-shot flake will look like success.

Compose all three.

---

## 3. SOP 工作流 (Standard Operating Procedure)

A coder agent walks this top-down. Each step has a decision gate — answer
"no" and you go back, not forward.

### Step 1 · Identify the loop body and the cycle invariant

Before adding *any* bound, write down on paper:

- What is the loop body? (one function / one node / one task)
- What input does it read? What output does it write?
- What state field MUST be different on iteration N+1 vs iteration N for
  this to be progress? That field is your **progress witness**.

Gate: if you can't name the witness, you don't yet understand the loop
well enough to bound it. Don't add a counter — go think.

Common witnesses by workflow shape:

| Workflow | Witness |
|---|---|
| Tool-call → error → retry | `last_error` text must change (or counter increments) |
| Plan → act → observe | `plan_revision: int` strictly increases |
| Draft → critique → revise | `critique` length shrinks OR `revision_count` increments with non-empty diff |
| Test → fix → re-test | `failing_tests` set strictly shrinks |
| Optimiser sweep | `best_metric` strictly improves (with patience) |
| Multi-agent handoff | `task_status` transitions through a state machine, not "in_progress → in_progress → ..." |

### Step 2 · Add the iteration counter

Counter discipline:

- **One counter per loop**, not per agent. In multi-agent systems where
  agents can call each other (CrewAI delegation, LangGraph subgraphs),
  the counter must live in the **shared** state, not per-agent
  `max_iter` — that is the CrewAI ping-pong bug `[gh/crewai-330]`.
- **Counter is monotonic** — `Annotated[int, operator.add]` in LangGraph,
  not a state replace.
- **Counter is visible** — log it; surface it in traces. A counter you
  can't see in LangSmith / Maxim / Datadog is a counter you'll forget
  is there.

Pseudocode (framework-agnostic):

```python
def loop_body(state):
    new_state = do_one_iteration(state)
    new_state["retries"] = state.get("retries", 0) + 1
    return new_state

def should_continue(state) -> Literal["continue", "give_up"]:
    if state["retries"] >= MAX_RETRIES:
        return "give_up"
    if success_predicate(state):
        return "end"
    return "continue"
```

### Step 3 · Add the stagnation detector

The counter alone wastes (N-1) iterations on identical work. Add a
progress witness comparison:

```python
def should_continue(state):
    if state.get("last_witness") == state.get("witness"):
        return "give_up_stagnant"
    if state["retries"] >= MAX_RETRIES:
        return "give_up_budget"
    if success_predicate(state):
        return "end"
    return "continue"
```

Stagnation signals worth detecting:

- Same `last_error` two iterations running.
- Same `tool_calls` hash (same tool, same args) two iterations.
- `plan_revision` did not increment.
- `failing_tests` did not shrink (test-fix loop).

When stagnation fires, **always escalate** — don't retry.

### Step 4 · Pick the LM's view of the loop state

The LM must see the loop counter and the last error / last witness. If
it doesn't, it will happily repeat. Concretely:

- **LangGraph**: include `retries` and `last_error` in the messages
  passed to the LLM node — or render them into the system prompt at
  each iteration.
- **CrewAI**: surface the previous task's failure in the next task's
  `context=[...]`, not in `Crew.memory` (which is muddier).
- **Claude / OpenAI SDKs**: in the next user/tool-result message,
  include `"Attempt {n} of {N}. Previous error: {err}. If you cannot
  fix it on this attempt, return final_answer with status=failed."`

Without this, the LM thinks it's on iteration 1 forever. The framework's
counter is in your code; the *behavioural* counter must be in the prompt.

### Step 5 · Build the escalation branch *before* you remove the safety net

The framework's safety net exists for a reason — runaway billing. Don't
disable it. Instead, build the **graceful give-up** that catches the
counter/stagnation exit:

- LangGraph: a `give_up` node that calls `interrupt({"reason": ...})`,
  preserving the full state for a human or outer agent to inspect.
- CrewAI: a fallback `Task` with `human_input=True` that fires when the
  main task fails the validation in `expected_output`.
- Claude SDK: a `human_escalation` tool that the model is *forced* to
  call when `attempt == N`.
- OpenAI Agents: handle `Run.status == "incomplete"` /
  `incomplete_reason == "max_turns"` in the caller and surface to user.

Rule of thumb: **a loop without a give-up branch is a loop that fails to
a stack trace**. That's not graceful.

### Step 6 · Layer the outer safety bound

Even with counter + witness + escalation, each individual iteration can
be expensive (one tool call doing a 200k-token web search). Add:

- **Token budget**: sum input + output tokens across iterations; cap.
- **Wall-clock timeout**: `asyncio.wait_for(loop, timeout=T)` at the
  outermost caller.
- **Rate limit**: CrewAI `max_rpm`, OpenAI tier limits, Anthropic
  `requests_per_minute`. Hit these *before* you hit the model's
  rate-limit error which adds backoff + more retries.

These are not redundant with the counter — they're orthogonal axes. A
3-iteration loop where one iteration runs for 4 hours still wedges your
system.

### Step 7 · Test the bound

Write a regression test that *injects a permanent failure* and asserts:

- The loop exits within N iterations (counter works).
- The loop exits *before* N if the same error recurs (stagnation works).
- The final state is captured in the escalation branch (escalation works).
- The trace shows the counter visible (observability works).

This is the same shape as `[gh/6731]`'s recommended fix: "Add a
regression test that injects a permanent SQL error and asserts the graph
terminates within 3 iterations." Steal that pattern.

---

## 4. 操作模型 (Operation Models)

Each operation is a primitive a coder agent can invoke. Format:
**Trigger → Action → Output → Evidence**.

### OP-1 · Retry counter in state (the foundational operation)

- **Trigger**: Any cyclic LM workflow exists — even one cycle.
- **Action**: Add a typed integer field to the workflow's persistent state
  with a monotonic semantics (LangGraph: `Annotated[int, operator.add]`;
  CrewAI: shared dict in `Crew` context or `Flow` state; Claude SDK: app
  variable). Increment inside the loop body; check in the exit predicate.
- **Output**: A deterministic upper bound on iterations regardless of LM
  behaviour.
- **Evidence**: `[gh/6731]` (text-to-SQL fix), `[lc-docs/errors]`
  ("explicit termination conditions are the right answer").

### OP-2 · Stagnation detection via progress witness

- **Trigger**: The counter alone keeps firing — you're wasting N
  iterations on identical retries.
- **Action**: Store the previous iteration's distinguishing artifact
  (`last_error`, `last_tool_call_hash`, `last_witness`) in state. In the
  exit predicate, compare current vs previous *before* checking the
  counter. Same → exit `stagnant`, don't increment.
- **Output**: Fast-fail on truly stuck loops; reserves the counter for
  cases where iterations *are* progressing slowly.
- **Evidence**: `[gh/6731]` (LLM was retrying identical query 20 times —
  stagnation would have fired after 1).

### OP-3 · Human / outer-loop escalation

- **Trigger**: Counter exhausted OR stagnation detected.
- **Action**: Route to a designated escalation node that *does not crash*.
  LangGraph: `give_up` node → `interrupt({"reason", "state"})`. CrewAI:
  fallback `Task(human_input=True)` or Flow `@listen("failed")` branch.
  Claude SDK: `human_escalation` tool injection. OpenAI Agents: catch
  `incomplete_reason == "max_turns"` in caller.
- **Output**: A clean give-up branch carrying enough state for a human
  or outer agent to diagnose.
- **Evidence**: `[lc-blog/interrupt]` four-pattern table; Aider's REPL
  return-to-human on failed test.

### OP-4 · Token & wall-clock budget (orthogonal safety net)

- **Trigger**: Iterations are themselves expensive (long context, web
  search, code execution).
- **Action**: Track cumulative tokens in state; enforce wall-clock
  `asyncio.wait_for` at outer caller; enforce per-model
  `requests_per_minute`. Any one tripping → escalation (OP-3).
- **Output**: Defense-in-depth — neither "3 cheap iterations" nor "1
  expensive iteration" can run away.
- **Evidence**: Anthropic Computer Use "step budget"; CrewAI `max_rpm`;
  OpenAI `max_completion_tokens` / `max_prompt_tokens` on `Run`.

### OP-5 · Progress witness declared up front

- **Trigger**: Designing a new cyclic flow.
- **Action**: Identify the state field that MUST change between
  iterations to prove progress. Declare it as a typed field. The exit
  predicate verifies it changed; the LM's prompt is told to set it.
- **Output**: A loop body that is structurally incapable of being a
  no-op.
- **Evidence**: `[cheatsheet/gotchas]` "Treat each node like a pure
  function — return a partial state update"; LangChain best practices.

### OP-6 · Refuse-to-raise-the-net (diagnostic)

- **Trigger**: User asks "just raise `recursion_limit` / `max_iter`."
- **Action**: Refuse and diagnose. Walk: (a) is there a state counter?
  (b) is there a witness? (c) does the LM see the previous error? Add
  what's missing. Leave the framework default in place — it's a circuit
  breaker, not a control knob.
- **Output**: A diagnostic conversation that ends with OP-1+OP-2 instead
  of papering over the failure.
- **Evidence**: `[gh/6731]` maintainer marked "not planned" — i.e., this
  is *by design*. `[cheatsheet/gotchas]` "indicates an underlying design
  flaw."

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 · "Text-to-SQL agent loops 20× to GRAPH_RECURSION_LIMIT"

- **Source**: `[gh/6731]`
  (https://github.com/langchain-ai/langgraph/issues/6731), maintainer
  labelled "not planned."

- **困境**: A team built a text-to-SQL agent on LangGraph 1.0.6. When
  the Databricks query returned an error, the agent retried the same
  broken SQL 20 times until the default `recursion_limit=25` fired. It
  had worked on 0.6.x; the upgrade exposed the missing exit condition.

- **约束**:
  - Can't pin to 0.6.x — security fixes only in 1.x.
  - Maintainer won't ship a fix — explicitly "not planned."
  - Databricks quota is bleeding; business needs the agent live.

- **决策步骤**:
  1. **Reject** "just raise `recursion_limit` to 100." That makes the
     bleeding worse and confirms the cheatsheet's diagnosis
     `[cheatsheet/gotchas]`.
  2. Add state counter (OP-1):
     ```python
     class S(TypedDict):
         messages: Annotated[list[AnyMessage], add_messages]
         retries: Annotated[int, operator.add]
         last_error: str | None
     ```
  3. Add stagnation detector (OP-2): if `state["last_error"]` is the same
     as the new error, route to give-up — don't burn 2 more attempts on
     the identical broken query.
  4. Surface `last_error` into the next LLM prompt — the *content* of
     the SQL error usually tells the LLM whether to retry or abandon.
  5. Add give-up node (OP-3) that uses `interrupt()` to ask the user:
     "Tried 3 times, got: {last_error}. Should I rewrite the query
     differently or stop?"
  6. Add regression test (Step 7) injecting a permanent SQL error and
     asserting termination within 3 iterations.

- **结果**: Loop bounded at 3 iterations. Stagnation typically fires on
  iteration 2 (same query, same error). Quota cost capped. Failure mode
  observable in LangSmith. Maintainer-labelled-"not-planned" issue
  becomes a non-issue without an upstream patch.

- **可提取的操作**: OP-1 + OP-2 + OP-3 are mandatory for any cyclic
  graph. **The LM is never the terminator.**

---

### Case 2 · "CrewAI delegation ping-pong burns 10× the token budget"

- **Source**:
  [github.com/crewAIInc/crewAI/issues/330](https://github.com/crewAIInc/crewAI/issues/330)
  + related issues #4783, #2606 + azguards.com writeup on
  ["the delegation ping-pong"](https://azguards.com/technical/the-delegation-ping-pong-breaking-infinite-handoff-loops-in-crewai-hierarchical-topologies/).

- **困境**: A team running CrewAI in hierarchical mode set
  `allow_delegation=True` on all 3 worker agents. Agent A delegated to
  B; B delegated back to A; A delegated to C; C delegated back to A. The
  per-agent `max_iter=20` did NOT propagate across the handoffs — every
  delegation reset the count. Token bill 10× expected; the loop only
  ended when OpenAI rate-limited them.

- **约束**:
  - Can't trivially flatten to sequential — the workflow really does
    need different specialists.
  - The CrewAI maintainer documentation acknowledges this as a known
    limitation but recommends "design your agents not to delegate
    circularly" — i.e., the framework's safety net is genuinely
    bypassed.
  - Compliance needs an audit trail of which agent ran when.

- **决策步骤**:
  1. **Reject** "raise `max_iter` per agent to 100." The bug is that
     `max_iter` doesn't cross handoffs — raising it does nothing
     `[gh/crewai-330]`.
  2. **Set `allow_delegation=False` on all worker agents.** Only the
     manager agent gets delegation. This kills the cycle structurally
     — the CrewAI canonical advice from `[azguards.com]`.
  3. **Add a Crew-level handoff counter** in `Crew` context (Flow state
     if using Flows). Each delegation increments; manager checks before
     dispatching.
  4. **Stagnation detector**: hash `(from_agent, to_agent, task_id)` —
     if the same triple recurs, route to the manager's
     "I-can't-resolve-this" fallback Task with `human_input=True`.
  5. **Outer timeout**: `asyncio.wait_for(crew.kickoff_async(...),
     timeout=600)` — wall-clock cap regardless of token budget.
  6. **Switch to CrewAI Flow + small Crews** if delegation logic really
     needs to be conditional — `@listen` gives explicit routing
     `[crewai-docs/flows]`, eliminating the LM-driven handoff.

- **结果**: Cycle eliminated structurally (no worker delegates back).
  Token bill returns to expected level. Audit trail preserved (the
  manager owns dispatch; the handoff counter logs each).

- **可提取的操作**:
  - In multi-agent systems, **counter and witness must live in shared
    state**, not per-agent config. Per-agent `max_iter` is a useful
    inner net but not a sufficient outer net.
  - When the framework's primitive is structurally insufficient (CrewAI
    `max_iter` not crossing handoffs), the right move is to *remove the
    primitive's source of failure* (`allow_delegation=False`), not
    raise its limit.

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

Concrete don'ts. Each has a real-world example.

- **❌ Raise `recursion_limit` / `max_iter` / `max_turns` to "fix" a
  loop.** This is *the* anti-pattern this skill exists to name. The
  framework defaults are circuit breakers; raising them moves the
  failure further away while doubling the cost. Source: `[gh/6731]`
  maintainer "not planned"; `[cheatsheet/gotchas]` "indicates an
  underlying design flaw."

- **❌ Let the LM vote on termination via reflection.** Calling
  `llm.invoke("are we done?")` to decide whether to exit recreates the
  problem one level up — and the answer is biased ("let me just check
  one more thing"). The LM may *suggest* finality (a `final_answer`
  tool, `stop_reason="end_turn"`); the framework code must verify.

- **❌ Bound only by tokens.** A slow loop with cheap iterations never
  hits the token cap and runs for hours. Token budget is one of three
  axes (OP-4), not the whole bound.

- **❌ Per-agent `max_iter` in multi-agent systems with delegation.**
  CrewAI's `Agent.max_iter` does not propagate across delegation
  handoffs `[gh/crewai-330]`. The counter must be shared.

- **❌ Bound without an escalation path.** A loop that hits
  `recursion_limit` and raises is not "bounded" in any useful sense —
  it's "crashed with stacktrace." A bounded loop has a clean give-up
  branch (OP-3).

- **❌ Counter that the LM cannot see.** If you increment a counter in
  Python state but never surface "attempt N of M, previous error: X" in
  the LM's prompt, the LM thinks it's on attempt 1 forever and emits
  the same plan. Counter must be in the *behaviour*, not just the
  *control plane*.

- **❌ "Stop when the metric stops improving" with no patience or cap.**
  Classic optimiser footgun. The metric can plateau and resume; the
  loop should be bounded by *both* a max-step count *and* a patience
  counter — DSPy and W&B sweeps document this. Source: optimiser docs
  across DSPy / Optuna / W&B.

- **❌ Bound the framework's max_iter but not the outer caller.** If
  the LM raises an exception inside the loop body and your retry
  decorator wraps the whole call, the bounded loop becomes an unbounded
  retry. Bound at every layer the framework gives you.

- **❌ Use `interrupt()` / `human_input=True` only on success.** The
  give-up branch is the *most important* place for human-in-the-loop —
  that's where the agent is admitting it's stuck. Routing the failure
  to a stack trace instead of a human wastes the diagnostic moment.

### Hard boundaries (when this skill does NOT apply)

- One-shot LLM calls (no loop to bound).
- Data-bounded loops where the cardinality is fixed at design time
  ("iterate once per row in this 500-row CSV"). The bound is the data
  size; counters/witnesses are over-engineering.
- Pure-deterministic loops that don't involve LM calls.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

The same termination contract expressed in each framework's vocabulary.
Use this table when porting a bounded loop between frameworks — the
*shape* is identical, only the names change.

| Concept | LangGraph | CrewAI | Claude SDK | OpenAI Agents | DSPy |
|---|---|---|---|---|---|
| **Iteration counter** | `state["retries"]: Annotated[int, operator.add]` | shared dict in `Crew` context or `Flow` state | app-side `for i in range(max_iter):` | `Run(max_turns=N)` config | optimiser `max_bootstrapped_demos` |
| **Exit predicate** | conditional edge function returning `"END"` | manager Task validating `expected_output` | `if stop_reason == "end_turn": break` | `Run.status == "completed"` | metric early-stopping (with explicit patience) |
| **Safety-net default** | `recursion_limit=25` | `Agent.max_iter=20` + `Crew.max_rpm` | `max_tokens` per call | `max_turns` (no default) | none (dataset size) |
| **Progress witness** | typed state field updated by node | Task `expected_output` mandates delta | validator on tool output | function schema enforces non-empty delta | metric must strictly improve |
| **Stagnation signal** | compare `state["last_X"] == state["X"]` in conditional edge | task callback hashes output → stored in context | compare `tool_use` blocks across iterations | compare `tool_calls` in Run steps | patience counter (steps since best) |
| **Escalation** | `interrupt({"reason": ...})` node | fallback Task with `human_input=True` | tool call to human channel | `incomplete_reason == "max_turns"` handler | terminate optimiser + log |
| **Resume after escalation** | `Command(resume=...)` | re-`kickoff()` with appended human input | re-invoke with new user message | `submit_tool_outputs(...)` | re-run with adjusted config |
| **Outer safety bounds** | wrap `graph.ainvoke` in `asyncio.wait_for` | `Crew.max_rpm` + outer `wait_for` | sum `usage.input_tokens` + `usage.output_tokens` across calls; wall-clock | `Run(max_completion_tokens, max_prompt_tokens)` | `num_threads` budget + wall-clock |

**Translation example.** "Text-to-SQL agent retries the broken query 20
times" expressed in three frameworks:

| | LangGraph | CrewAI | Claude SDK |
|---|---|---|---|
| Counter | `retries: Annotated[int, operator.add]` in TypedDict | `Crew(memory=False, context={"retries": 0})` updated in callback | `attempt = 0` in caller |
| Increment | LLM node returns `{"retries": 1}` | Task `on_complete` callback updates dict | `attempt += 1` after each Messages call |
| Exit | conditional edge → `END` when `retries >= 3` | manager Task aborts when context counter ≥ 3 | `if attempt >= 3: break` |
| Witness | `last_error: str` field updated by tool node | `last_error` key in Crew context | track in caller variable |
| Stagnation | edge function compares `last_error` | callback compares stored vs new | caller compares strings |
| Escalation | `interrupt({"err": state["last_error"]})` node | fallback `Task(human_input=True)` | tool call `human_escalate(err)` |
| Outer net | `recursion_limit=10` (leave default low) | `Crew(max_rpm=30)` + `wait_for(60s)` | `max_tokens=2048` + `wait_for(60s)` |

The translation is mechanical because the contract is universal. **That
is the entire point of this skill.**

---

## 8. 附录 · 引用速查 (Citation Index)

Short tags resolved against `references/R1-source-evidence.md` and
`references/R2-cross-framework.md`:

- `[gh/6731]` = github.com/langchain-ai/langgraph/issues/6731 — text-to-SQL
  recursion_limit, maintainer "not planned"
- `[gh/crewai-330]` = github.com/crewAIInc/crewAI/issues/330 — delegation
  ping-pong; related #4783, #2606
- `[lc-docs/errors]` = docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT
- `[lc-blog/interrupt]` = www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt
- `[cheatsheet/gotchas]` = sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/
- `[crewai-docs/agents]` = docs.crewai.com/en/concepts/agents
- `[crewai-docs/flows]` = docs.crewai.com/en/concepts/flows
- `[azguards.com]` = azguards.com/technical/the-delegation-ping-pong-breaking-infinite-handoff-loops-in-crewai-hierarchical-topologies/
- `[anthropic-docs]` = docs.anthropic.com/en/api/messages — Messages API +
  Agent SDK "step budget" pattern
- `[dspy-docs]` = dspy.ai/docs/building-blocks/optimizers — declared
  evaluation budget
- `[openai-agents-docs]` = platform.openai.com/docs/assistants — Run
  config `max_turns`, `max_completion_tokens`, `max_prompt_tokens`

---

## TL;DR (one-paragraph version for the impatient)

Every LM loop must carry an **explicit counter in state**, a **progress
witness** the loop body must update, a **stagnation detector** that
compares the witness across iterations, and a **graceful escalation
branch** when either fires. Never raise the framework's
`recursion_limit` / `max_iter` / `max_turns` to "fix" a loop —
that limit is a billing safety net, not control flow, and raising it
moves the failure further away while burning more tokens. The LM in
the loop is **never** a reliable terminator. Source-of-truth case:
LangGraph issue [#6731](https://github.com/langchain-ai/langgraph/issues/6731)
marked "not planned" — the framework will not save you; the discipline
must.
