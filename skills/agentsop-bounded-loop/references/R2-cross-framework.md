# R2 · Cross-framework comparison — bounded-loop primitives

How each major LM-loop framework exposes (and how it *fails to expose*) a
proper termination primitive. Read this table when you're moving the same
agent logic between frameworks — the shape stays the same, the names change.

---

## Comparison table

| Framework | Generic safety net | Recommended explicit bound | Where the counter lives | Known footgun |
|---|---|---|---|---|
| **LangGraph** | `recursion_limit=25` (`GRAPH_RECURSION_LIMIT`) | retry counter in `TypedDict` state + conditional edge to `END` | `state["retries"]: Annotated[int, operator.add]` | Raising `recursion_limit` to 100 to "fix" a loop — issue [#6731](https://github.com/langchain-ai/langgraph/issues/6731), marked **"not planned"** |
| **CrewAI** | `max_iter=20` per Agent, `max_rpm` per Crew | `max_iter` per agent **plus** `allow_delegation=False` on workers + outer timeout | Per-Agent (does NOT cross delegation handoffs — issue [#330](https://github.com/crewAIInc/crewAI/issues/330)) | Setting `allow_delegation=True` on every agent → delegation ping-pong. `max_iter` is bypassed across handoffs |
| **Claude Agent SDK / Messages API** | `max_tokens` per call | Caller-controlled `max_iterations` / `tool_use_budget`; explicit "step budget" pattern in Computer Use | App code (the SDK does not own the loop) | Letting the model decide via "should I stop?" reflection — same content can be re-emitted forever |
| **OpenAI Agents SDK / Assistants** | `max_completion_tokens`, `max_prompt_tokens` | `max_turns` per Run | Run config | Same reflection footgun; also `tool_choice="auto"` can re-call the same tool |
| **DSPy** | None for inference; `Evaluate` is bounded by dataset size | `max_bootstrapped_demos`, `max_labeled_demos` on optimisers | Optimiser config | "Train until metric stops improving" — no early-stopping primitive ⇒ caller must set explicit budget |
| **AutoGen** | `max_consecutive_auto_reply` per agent | Same | Per-Agent | Group chat can loop forever if every agent's auto-reply triggers another |
| **AutoGPT / BabyAGI** *(historical)* | None initially; later `--continuous-limit` | Explicit step budget required | App code | Self-evaluation "task not complete" → infinite. Why these systems acquired the reputation they did |
| **Aider** | Human REPL as outermost bound | `--auto-test` retries are single-pass; `/test` is one-shot | Aider process state | Auto-fix loop without an explicit retry cap → silent token burn |
| **LangChain `AgentExecutor`** *(legacy)* | `max_iterations=15` hardcoded default | Same + `max_execution_time` | AgentExecutor config | The default was acknowledgement that LMs don't self-terminate |

---

## What "right" looks like across all of them

The minimum termination contract a bounded loop must satisfy, regardless of
framework:

1. **A counter that increments per iteration**, persisted in whatever the
   framework calls state (graph state, agent memory, run context).
2. **An exit predicate** evaluated *outside the LM's control* — usually a
   pure Python function. The LM can suggest "I'm done"; only the predicate
   can say so.
3. **A stagnation signal** — same error / same tool call / same output two
   iterations in a row → exit with `failed` rather than retry.
4. **A token / wall-clock budget** as the second safety net (the first is
   the counter; this is for the case where each iteration is unbounded
   itself).
5. **An escalation path** — when the counter or budget expires, the agent
   must hand off to a human or a fallback flow, not just crash.

If any of (1)-(5) is missing, you have a *partial* bound. The skill calls
that an anti-pattern.

---

## Naming dictionary (translate when porting agents)

| Concept | LangGraph | CrewAI | Claude SDK | OpenAI | DSPy |
|---|---|---|---|---|---|
| Iteration counter | state field + reducer | `Agent.max_iter` | caller-defined | `Run.max_turns` | optimiser config |
| Exit edge | conditional edge → `END` | task `expected_output` + manager logic | tool-loop break | `stop_reason="end_turn"` | metric early-stop |
| Outer safety net | `recursion_limit` | `max_rpm` + outer timeout | `max_tokens` | `max_completion_tokens` | `num_threads` budget |
| Human escalation | `interrupt()` | `human_input=True` in Task | tool call to human | function-call to human | n/a |
| Resume after pause | `Command(resume=...)` | re-`kickoff` | re-invoke | `submit_tool_outputs` | re-run |

When mapping the *same* termination logic between two frameworks, find the
row for the concept and replace names — the bound itself is unchanged.

---

## Why frameworks ship "wrong" defaults

The recursion limit / max_iter defaults are universally too high to be a
useful primary control (LangGraph 25; CrewAI 20; LangChain 15). They are
sized to prevent *billing accidents*, not to prevent the loop from being
wrong. Reading the docs carefully shows every framework saying the same
thing in different words:

- LangGraph docs: "safety net, not a primary control flow mechanism"
- CrewAI docs: "max_iter prevents runaway, design your tasks to converge"
- LangChain `AgentExecutor`: deprecated `max_iterations=15` default

The lesson for a coder agent: never set a "high enough" recursion limit;
always set a "low enough one and add your own counter."
