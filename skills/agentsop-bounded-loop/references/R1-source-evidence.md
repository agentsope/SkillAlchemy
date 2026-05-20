# R1 · Source Evidence — bounded-loop

This skill is distilled from four "real production scar" sources where an LM
loop ran longer than intended and a framework's *generic safety net* (recursion
limit, max-iter, retry cap) was insufficient. Each piece of evidence below ties
a specific claim in `SKILL.md` to a primary URL.

---

## S1 · LangGraph `GRAPH_RECURSION_LIMIT` — text-to-SQL retry storm

- **Primary**: [github.com/langchain-ai/langgraph/issues/6731](https://github.com/langchain-ai/langgraph/issues/6731)
  — a team upgraded LangGraph 0.6.x → 1.0.6 and their text-to-SQL agent began
  retrying the same broken Databricks query 20 times until `recursion_limit`
  fired. Maintainer labelled the issue **"not planned"** — no upstream fix
  coming.
- **Doctrine** (the docs say this *is* a design flaw, not a framework bug):
  > "If you are not expecting your graph to go through many iterations, you
  > likely have a cycle. Check your logic for infinite loops."
  > — [docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT)
- **Cheatsheet reinforcement**:
  > "Hitting the limit typically indicates an underlying design flaw. The
  > recursion limit is a safety net for runaway code, not a primary control
  > flow mechanism."
  > — [sumanmichael.github.io/langgraph-cheatsheet — FAQs & Gotchas](https://sumanmichael.github.io/langgraph-cheatsheet/cheatsheet/faqs-gotchas/)
- **Implication used in SKILL.md**:
  - OP-1 (retry counter in state)
  - Anti-pattern AP-1 ("raise recursion_limit")
  - Dilemma DC-1

---

## S2 · CrewAI delegation ping-pong & `max_iter`

- **Primary issue**: [github.com/crewAIInc/crewAI/issues/330](https://github.com/crewAIInc/crewAI/issues/330)
  — `allow_delegation=True` on multiple agents → infinite delegation loop
  ("A delegates to B, B delegates back to A, …"). Token cost blew past budget
  before any timeout fired.
- **Related issues**: [#4783](https://github.com/crewAIInc/crewAI/issues/4783),
  [#2606](https://github.com/crewAIInc/crewAI/issues/2606).
- **Root-cause writeup**:
  [azguards.com — "The delegation ping-pong: breaking infinite handoff loops
  in CrewAI hierarchical topologies"](https://azguards.com/technical/the-delegation-ping-pong-breaking-infinite-handoff-loops-in-crewai-hierarchical-topologies/)
  documents three failure modes: (1) circular delegation, (2) `DelegateWorkTool`
  silent schema-validation failure (`dict` where `str` expected → infinite
  retries), (3) **`max_iter` does not propagate across handoffs** — so the
  per-agent cap is bypassed once the agent delegates.
- **Doctrine quote**:
  > "max_iter in hierarchical mode does not carry across delegation boundaries
  > — the protection you set on the worker agent is bypassed the moment another
  > agent invokes it."
  > — azguards.com (paraphrased from the article)
- **Implication used in SKILL.md**:
  - OP-2 (counter must be in *shared* state, not per-call)
  - DC-2 (the ping-pong case)
  - AP-2 ("raise max_iter to fix the loop")

---

## S3 · Aider — test-fix loop bounded by explicit retry budget

- **Primary**: [aider.chat/docs/usage/lint-test.html](https://aider.chat/docs/usage/lint-test.html)
  > "Aider will try and fix any errors if the command returns a non-zero exit
  > code."
- **The crucial detail** Aider gets right: the auto-fix loop is **bounded by a
  configurable retry count** (`--auto-test`, `--auto-lint` each have an
  implicit single-pass retry, and the `/test` REPL command is one-shot). The
  human stays in the REPL — the loop is structurally bounded by *human input*
  as the outermost termination signal.
- **Compare with**: Cursor / Devin / Codex CLI implementations that re-run
  tests until pass or N attempts — every well-engineered code agent ships with
  an explicit fix-retry budget (`max_test_retries`, `max_attempts`, etc).
- **Implication used in SKILL.md**:
  - OP-3 (stagnation detection: same error → don't retry blindly)
  - OP-4 (human / outer-loop as the ultimate termination guarantee)

---

## S4 · Anthropic Claude SDKs — `tool_use_budget` / step limits

- **Anthropic docs** (Messages API + Agent SDK):
  - `max_tokens` is a per-call cap; for a multi-step agent loop, Anthropic
    recommends an explicit `max_iterations` / `tool_use_budget` controlled by
    the caller. See
    [docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)
    and the Claude Agent SDK pattern docs.
  - The Computer Use blog post and the Claude Code internals describe an
    explicit "step budget" pattern: each tool call consumes one step from a
    bounded pool; when the pool is exhausted the agent must summarise and ask
    the user.
- **OpenAI Assistants API parallel**: the Runs API has `max_completion_tokens`
  and `max_prompt_tokens`; the Agents SDK exposes `max_turns` per run.
- **Implication used in SKILL.md**:
  - OP-5 (token-budget termination)
  - Cross-framework table — every modern LM SDK has *some* form of bounded
    loop primitive. The skill makes that universal.

---

## S5 · DSPy evaluation budget

- **Primary**: DSPy's `Evaluate` and `BootstrapFewShot` optimisers all accept
  an explicit `max_bootstrapped_demos`, `max_labeled_demos`, and `num_threads`
  — the budget is *declared* up front. No notion of "let the optimiser
  decide when to stop."
- **Source**: [dspy.ai/docs/building-blocks/optimizers](https://dspy.ai/docs/building-blocks/optimizers)
  and [github.com/stanfordnlp/dspy](https://github.com/stanfordnlp/dspy).
- **Implication used in SKILL.md**:
  - Eval / optimisation loops are no different — the budget must be a
    declared parameter, not "until the metric stops improving."

---

## S6 · Generic "infinite agent loop" reports

- Reddit + HN threads cataloguing AutoGPT / BabyAGI infinite loops
  (2023-2024). The common pattern: the agent's *self-evaluation* says "task
  not complete" forever, because the success criterion was open-ended.
- LangChain `AgentExecutor` originally had `max_iterations=15` as a hardcoded
  default — explicit acknowledgement from the framework that the LM cannot
  be trusted to terminate.
- **Implication used in SKILL.md**: Mental model section — "every loop body
  must produce a state change proving progress, and the success criterion
  must be checkable without another LM call."

---

## Cross-source synthesis

Every source above tells the same story:

1. The LM in the loop is **not a reliable terminator**. It will happily retry,
   re-delegate, re-plan, re-evaluate — forever.
2. The framework's generic safety net (recursion_limit, max_iter, token cap)
   exists *only* to prevent runaway billing — it is NOT control flow.
3. The fix is always the same shape: **explicit counter + explicit exit edge
   + stored progress signal** in whatever the framework calls "state".

The skill `bounded-loop` codifies this universal pattern so a coder agent can
apply it without re-reading four framework docs.
