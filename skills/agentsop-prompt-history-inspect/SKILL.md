---
name: agentsop-prompt-history-inspect
version: 0.1.0
description: |
  Tool skill — the *first move* in any LM-debugging session: dump the actual rendered prompt
  the framework sent to the model, before changing anything else. Activate when an LM call
  produced an unexpected output (wrong answer, schema violation, refusal, truncation,
  cost spike, latency spike, infinite loop, "model got dumber after upgrade"). The skill
  enforces a 30-second inspect step BEFORE any prompt edit, model swap, retry, or temperature
  tweak. Cross-framework cheat sheet: DSPy `inspect_history`, LangGraph `get_state_history`,
  CrewAI `step_callback`, LangChain `set_debug`/`set_verbose`, Aider `/diff`+`--verbose`,
  raw OpenAI/Anthropic via `OPENAI_LOG=debug`/`ANTHROPIC_LOG=debug` or HTTPX event hooks.
  Do NOT activate for first-time prompt authoring, exploratory prompt design, or non-LM bugs.
---

# Prompt-History Inspect — First Move Before Anything Else

> *"The prompt you wrote is not the prompt the model received."*
> — Operating axiom for every framework that templates, injects few-shots, appends tool definitions, or wraps system messages.

---

## 1. 何时激活 (When to activate)

Activate this skill the **moment** an LM call surprises you, BEFORE any other debug move.

| Trigger | Signal |
|---|---|
| Output wrong | "Why did it answer X?" / hallucinated fact / wrong format / refusal |
| Output truncated | mid-sentence cut, partial JSON, missing fields |
| Output empty / repeats | model returns `""`, repeats the same token, loops |
| Behaviour changed | "It worked yesterday" / "It worked on GPT-4o but not on Llama-3" |
| Cost / latency spike | tokens jumped 3× without code change → something got injected |
| Tool call wrong | wrong tool picked, args malformed, tool call missing |
| Schema validation failed | Pydantic / Outlines / guidance grammar refused output |
| Eval regression | metric dropped after upgrading framework version |
| Production bug | a user-facing thread produced a wrong answer — need to see what the LM saw |

**Do NOT activate** when:
- You are *authoring* a new prompt for the first time (no rendered prompt exists yet).
- The bug is clearly outside the LM call (retriever returned empty, API key invalid, network down).
- The framework hasn't even been called yet (e.g., import error, schema validation pre-call).

**The trigger is universal across the stack.** Any framework that *templates* a prompt — DSPy, LangChain, LangGraph, CrewAI, LlamaIndex, Aider, Guidance, Outlines — has a layer between "what you wrote" and "what the model received." This skill is the first-line probe into that gap.

---

## 2. 核心心智模型 (Core mental model)

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ What you wrote   │ ≠  │ What was rendered│ ≠  │ What the LM saw  │
│ (template,       │    │ (after few-shot  │    │ (after provider  │
│  signature, etc) │    │  injection, tool │    │  reformatting,   │
│                  │    │  defs appended,  │    │  message squash, │
│                  │    │  system msg,     │    │  token truncation)
│                  │    │  history, etc)   │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
       layer 1                layer 2                  layer 3
       (your code)         (framework render)      (provider transport)
```

**Three mental shifts** the agent must internalize:

1. **The rendered prompt is the ground truth, not your source code.** Frameworks silently inject system messages, append tool JSON-schemas, deduplicate messages, summarise history, truncate context, reorder fields. The *only* trustworthy artefact is what was sent on the wire.

2. **Inspect first, change nothing.** Premature prompt edits hide the bug. If you "fix" the prompt before seeing the rendered output, you're optimising against a hallucination of the problem. The discipline is: **dump → diff against expectation → identify which layer diverged → fix at that layer.**

3. **The inspect command is framework-specific but the SOP is universal.** DSPy gives you `inspect_history(n=1)`. LangChain gives you `set_debug(True)`. Raw SDKs give you `OPENAI_LOG=debug` or HTTPX event hooks. You learn one cheat sheet (§7) once and the SOP applies everywhere.

**The 30-second test.** Before you do *anything* else, you should be able to print the exact final prompt text in <30 seconds. If you can't — you're not set up to debug LMs. Fix that first.

---

## 3. SOP 工作流 (SOP workflow)

A four-step ritual. Do them in order. Do not skip ahead.

### Step 1 — Dump the rendered prompt (≤30 sec)

Look up the framework on the §7 cheat sheet. Run the inspect command. Get the actual text of:
- The system message (if any)
- The user message
- Any few-shot demos that were injected
- Tool / function definitions (if any)
- Assistant prefill (if any)
- The model's raw response

For DSPy: `dspy.inspect_history(n=1)` [[dspy.ai/api/utils/inspect_history/](https://dspy.ai/api/utils/inspect_history/)].
For LangChain: `from langchain.globals import set_debug; set_debug(True)` [[python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html)].
For raw SDKs: `export OPENAI_LOG=debug` or `ANTHROPIC_LOG=debug` [[github.com/openai/openai-python](https://github.com/openai/openai-python), [github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)].

### Step 2 — Diff against expectation

Write down (mentally or in a scratch file): *what did I expect the prompt to contain?* Then compare to the dump. Look for:
- **Extra content** you didn't intend (auto-injected system message, hidden few-shot, tool JSON-schema bloat).
- **Missing content** you did intend (your variable interpolation rendered as `None` / empty / `{var}` literal).
- **Wrong order** (assistant message before system, tool call before tool result).
- **Truncation** (your 10k-token context was clipped to 4k; few-shot ate your real input).
- **Encoding** (raw HTML/JSON characters un-escaped, leaking template markers like `{% if %}`).

### Step 3 — Identify the divergence layer

Now classify the bug into one of three layers (mental model §2):

- **Layer 1 (your code)**: variable not interpolated, wrong key passed to chain, signature field misnamed → fix in your code.
- **Layer 2 (framework render)**: framework's template logic injected something unwanted, demos chosen by optimizer don't match task, tool definitions inflated past budget → fix at the framework config (different prompt template, fewer demos, smaller tool set, different module).
- **Layer 3 (provider transport)**: provider's message squashing, role coercion, token cap, finish_reason="length" → fix at provider config (different model, raise `max_tokens`, restructure to avoid role coercion).

### Step 4 — Fix at the correct layer, then re-dump

Apply the minimum change at the identified layer. Re-run. Re-dump. Confirm the prompt now matches expectation. *Then* check whether the bug is fixed.

**Critical anti-pattern**: do not skip step 4's re-dump. Many "fixes" change Layer 1 when the real bug is Layer 2 — the prompt still looks broken on re-dump, even if the visible symptom changed.

---

## 4. 操作模型 (Operational model — Trigger / Action / Output / Evidence)

### OP-1 · Inspect last N DSPy LM calls
- **Trigger**: A DSPy `Predict` / `ChainOfThought` / `ReAct` returned wrong output, OR a compile run hung mid-trial.
- **Action**: `import dspy; dspy.inspect_history(n=1)` — increase `n` to see the last few calls. For per-LM history: `lm.inspect_history(n=3)`.
- **Output**: Prints system / user / assistant blocks plus the raw response for the last N LM invocations.
- **Evidence**: [dspy.ai/api/utils/inspect_history/](https://dspy.ai/api/utils/inspect_history/), DSPy docs "Debugging & Observability" [[dspy.ai/tutorials/observability/](https://dspy.ai/tutorials/observability/)]. Note: `inspect_history` shows *only LM calls*, not retriever/tool calls — for those, wire `mlflow.dspy.autolog()` [[github.com/stanfordnlp/dspy issue #784](https://github.com/stanfordnlp/dspy/issues/784) for `n`-parameter quirks].

### OP-2 · LangChain global debug / verbose
- **Trigger**: A LangChain chain or agent produced unexpected output; you want to see every LM call's prompt and response.
- **Action**:
  ```python
  from langchain.globals import set_debug, set_verbose
  set_debug(True)     # most verbose — full prompt + response + chain internals
  # OR for less noise:
  set_verbose(True)   # prompt + response only, no chain internals
  ```
  Scope: process-global. Toggle off when done.
- **Output**: Console-printed prompt/response for every LM call in the process.
- **Evidence**: [python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html), [python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html](https://python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html), debugging guide [[python.langchain.com/v0.1/docs/guides/development/debugging/](https://python.langchain.com/v0.1/docs/guides/development/debugging/)].

### OP-3 · LangGraph time-travel state inspection
- **Trigger**: A LangGraph thread produced a wrong final answer; you need to see the state (and the LM input) at step k, possibly fork from there.
- **Action**:
  ```python
  history = list(graph.get_state_history(config))   # newest → oldest
  for snap in history:
      print(snap.config["configurable"]["checkpoint_id"], snap.values)
  # Replay from a checkpoint:
  graph.invoke(None, config={"configurable": {
      "thread_id": "...", "checkpoint_id": "<chosen id>"}})
  # Fork by modifying state:
  graph.update_state(config, {"some_field": "new value"})
  ```
- **Output**: Full per-step state list (including messages, the inputs the LM saw); ability to replay or fork.
- **Evidence**: [langchain-ai.github.io/langgraph/concepts/time-travel/](https://langchain-ai.github.io/langgraph/concepts/time-travel/), [docs.langchain.com/oss/python/langgraph/use-time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel). **Caveat**: replay *re-executes* nodes — LLM calls and API requests fire again and may produce different results [time-travel docs]. To inspect without re-cost, read state from history only; do not invoke.

### OP-4 · CrewAI step-by-step inspection
- **Trigger**: A CrewAI agent picked the wrong tool, looped, or delivered the wrong output; you need per-step visibility.
- **Action**: Two layers:
  ```python
  Agent(..., verbose=True)             # prints agent thoughts + tool I/O
  Crew(..., verbose=True)
  # Per-step structured capture:
  def my_step(step_output):
      print("STEP:", step_output)      # AgentAction / AgentFinish / observation
  Agent(..., step_callback=my_step)
  ```
- **Output**: Every agent action, tool input, tool observation, and final answer printed or captured to your callback.
- **Evidence**: [docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents) (`step_callback` parameter), [docs.crewai.com/en/observability/overview](https://docs.crewai.com/en/observability/overview). CrewAI's internal log is thin — for production observability also wire `mlflow.crewai.autolog()` or Langtrace [[docs.crewai.com/how-to/langtrace-observability](https://docs.crewai.com/how-to/langtrace-observability)].

### OP-5 · Aider show last diff and full prompts
- **Trigger**: Aider applied a wrong edit, mis-identified files, or behaved differently than expected.
- **Action**:
  ```
  /diff           # see exactly what Aider just changed
  /tokens         # see how big the context actually got
  /ls             # see which files are in chat vs read-only
  ```
  Plus CLI: `aider --verbose` prints the full prompt sent to the model on each turn.
- **Output**: Last-turn diff, current token budget, file set, and (with `--verbose`) the rendered prompt.
- **Evidence**: [aider.chat/docs/usage/commands.html](https://aider.chat/docs/usage/commands.html), [aider.chat/docs/usage/tutorials.html](https://aider.chat/docs/usage/tutorials.html). Combine with `git diff HEAD~1` for verification — Aider auto-commits, so the diff is also in git history.

### OP-6 · Raw OpenAI / Anthropic SDK debug logging
- **Trigger**: You're calling `client.chat.completions.create(...)` (OpenAI) or `client.messages.create(...)` (Anthropic) directly, and the response is wrong. No framework templating layer to blame.
- **Action**:
  ```bash
  # OpenAI:
  export OPENAI_LOG=debug   # also: OPENAI_LOG=info for less verbose
  # Anthropic:
  export ANTHROPIC_LOG=debug
  ```
  Both SDKs use the stdlib `logging` module — the env var sets the logger level.
- **Output**: Full request/response bodies (and headers) printed to stderr.
- **Evidence**: [github.com/openai/openai-python](https://github.com/openai/openai-python) README §Logging, [github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) README §Logging.
- **CRITICAL security caveat**: at `debug` level, **the Authorization header (including the API key) is printed in plaintext** [[github.com/openai/openai-python issue #1196](https://github.com/openai/openai-python/issues/1196), [issue #1082](https://github.com/openai/openai-python/issues/1082)]. Never commit a `debug`-level log file. Strip keys before sharing.

### OP-7 · HTTPX event-hook logger (full control)
- **Trigger**: You need the *full raw* HTTP request body (e.g., to verify what `additional_drop_params` or `extra_body` did), and `OPENAI_LOG=debug` is too noisy or formats badly.
- **Action**: Pass a custom `httpx.Client` with event hooks to the SDK:
  ```python
  import httpx, json
  from openai import OpenAI
  def log_request(req):
      print("REQUEST:", req.method, req.url)
      print(json.dumps(json.loads(req.content), indent=2))
  client = OpenAI(http_client=httpx.Client(event_hooks={"request": [log_request]}))
  ```
- **Output**: Clean, structured dump of the exact JSON body sent over the wire.
- **Evidence**: Simon Willison's TIL [[til.simonwillison.net/httpx/openai-log-requests-responses](https://til.simonwillison.net/httpx/openai-log-requests-responses)], httpx event-hooks docs [[encode/httpx discussion #3073](https://github.com/encode/httpx/discussions/3073)]. Works for both OpenAI and Anthropic SDKs (both accept `http_client=`).

### OP-8 · Tool-definition bloat probe
- **Trigger**: Tokens / latency spiked, model "got dumber" after adding tools, or context-window error fires before your real input.
- **Action**: Dump the prompt (any of OP-1–7), then **count tokens in the tool-definitions block alone**. Most frameworks serialise each tool's JSON-schema (description, parameters, types, enums) into the prompt — 10 tools easily costs 2k+ tokens before any user input.
- **Output**: Concrete token cost per tool; identification of which tools to drop or compress.
- **Evidence**: Reproducible by inspect-dump; community pattern documented in agent-framework debugging threads (e.g., [github.com/microsoft/semantic-kernel discussion #1239](https://github.com/microsoft/semantic-kernel/discussions/1239) on getting the raw prompt).

### OP-9 · Production trace inspection (LangSmith / LangFuse / MLflow / Phoenix)
- **Trigger**: Bug surfaced in production; you don't have a repro locally; you need to inspect a real user's thread.
- **Action**: Open the trace in the configured platform (LangSmith / LangFuse / Phoenix / MLflow), navigate to the failing run, click into the LM call, view the rendered prompt and response. This is the production-equivalent of OP-1–7.
- **Output**: Reviewed prompt for the failing run, ready for diff against expectation (Step 2 of SOP).
- **Evidence**: Use the corresponding skill (`langsmith`, `phoenix`, `langfuse`) for the platform-specific UI. *This skill enforces the first-move SOP; those skills provide the UI.*

### OP-10 · Save the rendered prompt as a fixture
- **Trigger**: You've found the bad rendered prompt and now need to reproduce / regression-test.
- **Action**: Save the dumped prompt text to `tests/fixtures/prompt-bug-<id>.txt`. Add a test that asserts the *next* render does not contain the bad pattern. (For LangChain, snapshot the `prompt.format(**inputs)` output; for DSPy, snapshot what `inspect_history` printed.)
- **Output**: A regression test that pins the prompt rendering, not just the model output.
- **Evidence**: Same principle as snapshot testing in UI — the rendered prompt is the artefact to pin.

---

## 5. 困境决策案例 (Dilemma cases)

### Case A — "Framework template silently truncated my context"

**困境 (Dilemma)**: A RAG pipeline retrieves 10 passages and asks the LM to synthesize. Outputs miss obvious facts that are in the retrieved passages. User's first instinct: "the model is bad / the retriever is bad / let me re-rank."

**约束 (Constraints)**:
- 10 passages, ~600 tokens each = ~6k tokens of context.
- Framework: a custom LangChain `MapReduceDocumentsChain` wrapper.
- Model: GPT-4o, 128k context — no obvious context-budget issue.

**决策步骤 (Decision steps)**:
1. **Refuse to re-rank, refuse to swap the model, refuse to "fix" the prompt.** First move is inspect (§3 Step 1).
2. Enable `set_debug(True)` from `langchain.globals` [[python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html)]. Re-run.
3. In the dumped prompt: notice the prompt only contains **3 passages**, not 10. The framework's map-reduce splits and the *reduce* prompt got only the per-chunk summaries — and the chunk-summarizer dropped facts.
4. Layer classification (§3 Step 3): **Layer 2** — framework render. The bug is the map-reduce decomposition, not the model or the retriever.
5. Fix: switch to a `stuff` chain (all 10 passages in one prompt — fits in 128k) or write better chunk-summary prompts. Re-dump to confirm all 10 passages now appear.

**结果 (Outcome)**: Wrong layer would have been: a week of re-ranker tuning. Right layer: 10 minutes of template fix. Visible *only* via rendered-prompt dump.

**可提取的操作 (Extractable operation)**: **When a RAG pipeline misses obvious retrieved facts, dump the prompt and count how many retrieved chunks actually appear. The framework probably dropped some.**

---

### Case B — "Tool definitions inflated my prompt past budget"

**困境**: A LangChain or CrewAI agent worked fine with 3 tools. After adding 4 more tools, accuracy dropped and latency tripled. User suspects the model "gets confused by more tools."

**约束**:
- 7 tools, each with rich JSON-schema (descriptions, enum params, nested objects).
- Model: claude-3.5-sonnet, 200k context.
- The new tools are individually correct (unit tests pass).

**决策步骤**:
1. **First move: dump the prompt.** OP-7 (HTTPX hook) gives the cleanest view of the raw JSON body. Count tokens in the `tools=[...]` array alone (OP-8).
2. Finding: tool definitions now consume **3.4k tokens** — they replaced ~3k of the available reasoning budget. The system message + few-shots + tools eats the head of the context, pushing user input + history toward the tail where attention is weaker.
3. Layer classification: **Layer 2** (framework render) AND **Layer 3** (provider transport — attention degrades in long-context tails for many models).
4. Fix options:
   - **Compress descriptions** (the cheapest tool description halved tokens with no quality loss).
   - **Lazy-load tools** (route first, expose only relevant tools per query).
   - **Drop verbose `enum` lists** in params — describe them in natural language.
5. Re-dump to confirm token count dropped. Re-test.

**结果**: Without inspect, the user would "fix" by removing tools (losing capability) or switching models (expensive). Inspect reveals the tool-schema is the cost driver.

**可提取的操作**: **More tools = silent prompt inflation. Always inspect tool-block token count before blaming the model.**

---

### Case C — "Optimized DSPy program degraded after model swap — why?"

**困境**: A `MIPROv2`-compiled program for GPT-4o hits 85% on dev. Re-pointed at Llama-3-8B, drops to 41%. User assumes Llama is just weaker.

**约束**:
- `compiled.json` saved with demos + instructions tuned to GPT-4o.
- Same program code, only `dspy.configure(lm=...)` changed.
- Cost: re-compile is $2–5 vs. accepting the 41% loss.

**决策步骤**:
1. **First move (per this skill, not DSPy doctrine yet): dump.** `dspy.inspect_history(n=3)` on Llama-3-8B [[dspy.ai/api/utils/inspect_history/](https://dspy.ai/api/utils/inspect_history/)].
2. Finding: the bootstrapped demos in `compiled.json` contain verbose, GPT-4o-style chains-of-thought (5–8 sentences per demo). Llama-3-8B copies the *length* but skips the *reasoning structure* — producing plausible-shaped but wrong outputs.
3. Layer classification: **Layer 2** — the rendered prompt looks fine *for GPT-4o*, wrong *for Llama-8B*. The artefact is model-coupled.
4. Fix per DSPy doctrine [Case B of `dspy-sop`]: recompile against Llama-3-8B. *But* without the inspect step, the user would not have known the demos were the bottleneck (vs. the instructions, or the signature).
5. Optional: after re-compile, re-dump to confirm the new demos are shorter / more explicit.

**结果**: Inspect reveals *what changed* in the rendered prompt; doctrine says *what to do* about it. Skipping inspect leads to "Llama is bad" — wrong root cause.

**可提取的操作**: **Compiled-prompt artefacts are model-coupled. Inspect-dump on the new model is mandatory before declaring the model "weaker."**

---

### Case D — "Production thread gave wrong answer — can't reproduce locally"

**困境**: A LangGraph customer-support agent gave a confidently wrong answer in production. User logs show only the final output, not intermediate state. No local repro.

**约束**:
- Production has a checkpointer configured (Postgres-backed).
- The thread ID is known.
- Can't replay full LLM calls (production cost / rate-limit risk).

**决策步骤**:
1. **First move: inspect the production trace.** Use OP-3 with the production checkpointer:
   ```python
   history = list(graph.get_state_history({"configurable": {"thread_id": "<prod-id>"}}))
   ```
2. Walk back from the final state to find the LM call that introduced the error. View the `messages` field in each `StateSnapshot.values` — that's the rendered prompt as seen by the LM [[langchain-ai.github.io/langgraph/concepts/time-travel/](https://langchain-ai.github.io/langgraph/concepts/time-travel/)].
3. Finding: at step 4, a tool returned an error string that the next node concatenated into the system message — confusing the LM into a confabulated answer.
4. Layer: **Layer 1** (your code) — node didn't error-handle the tool result.
5. **Do not** call `graph.invoke(None, config=...)` to "replay" — that re-executes LM calls and incurs cost [[time-travel docs caveat](https://langchain-ai.github.io/langgraph/concepts/time-travel/)]. Reading state history is read-only and free.
6. Fix the node's error-handling, push, write a regression test using the captured state as fixture (OP-10).

**结果**: Time-travel reads state without re-paying for LLM calls. The bug is visible in the inspected state, not in the final output alone.

**可提取的操作**: **For production bugs, `get_state_history` is read-only and free; `invoke(None, config=...)` is replay and costs LM calls. Inspect first, replay only if necessary.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns (in rough order of how often they cost engineer-hours)

1. **Changing the prompt before inspecting it.** This is the #1 mistake. If you don't know what was sent, you don't know what to change. Inspect costs 30 seconds; "fix the prompt and see" costs an afternoon.
2. **Trusting the source code matches what was sent.** False *every time* there's a templating, few-shot, signature, or tool-injection layer between your code and the provider. Treat source as a hypothesis; the dump is evidence.
3. **Inspecting at the wrong layer.** Dumping a `PromptTemplate.format(...)` output is *not* the same as dumping what hit the wire — the framework adds messages, system instructions, tool schemas after that point. Prefer SDK-level (`OPENAI_LOG=debug`) or HTTPX-hook (OP-7) over template-render for production debugging.
4. **Leaving `set_debug(True)` / `OPENAI_LOG=debug` on in production.** Both leak request bodies, and `OPENAI_LOG=debug` / `ANTHROPIC_LOG=debug` print the **API key** in plaintext [[openai-python issue #1196](https://github.com/openai/openai-python/issues/1196)]. Always scope to debug sessions; toggle off when done.
5. **Replaying production threads via `graph.invoke(None, config=...)` to debug.** Re-executes LM calls and tools, paying real cost, possibly mutating real systems. Read state history; replay only when needed [[time-travel docs](https://langchain-ai.github.io/langgraph/concepts/time-travel/)].
6. **Inspecting only the *prompt*, ignoring the *response*.** Many bugs (model truncation, refusal, schema validation) are visible only in the raw response including finish_reason. Always dump both.
7. **Using `inspect_history` as the *only* observability.** DSPy's `inspect_history` shows LM calls only — not retrievers, not tools, not subgraphs. For multi-component pipelines, layer it with MLflow / LangSmith tracing [[dspy.ai/tutorials/observability/](https://dspy.ai/tutorials/observability/)].
8. **Eyeballing the dump.** For long prompts, diff against a known-good rendering rather than reading top-to-bottom. Token-count the segments.
9. **Reasoning about why the prompt is "fine" without re-rendering after each change.** Frameworks change prompts at runtime based on history, retries, tool state. Each invocation can produce a different rendered prompt. Re-dump.
10. **Sharing a debug log without scrubbing keys.** Strip `Authorization:` headers before pasting into chat / issues / Slack.

### Boundaries (when this skill is NOT the right move)

- **Pre-call errors** (import error, auth failure, network down) — no LM call happened; there's nothing to inspect. Fix infra first.
- **Prompt authoring from scratch** — no rendered prompt exists yet. Use prompt-engineering / DSPy-Signature / template-design skills instead.
- **Eval-time aggregate metrics** — single prompt dump is the wrong granularity. Use eval / langsmith / phoenix.
- **Streaming-only debugging** — if you only care about token-by-token streaming behaviour, framework streaming hooks are better than post-hoc inspect.
- **You already have a deep trace UI configured (LangSmith, LangFuse, Phoenix, MLflow)** — the *first move* SOP still applies (OP-9), but the implementation is "open the trace" not "run inspect_history". Same skill, different action.

---

## 7. 跨框架对照 (Cross-framework cheat sheet)

| Framework | First-move command | What it shows | Source |
|---|---|---|---|
| **DSPy** | `dspy.inspect_history(n=1)` | Last LM call: system / user / assistant / response | [dspy.ai/api/utils/inspect_history/](https://dspy.ai/api/utils/inspect_history/) |
| **DSPy (per-LM)** | `lm.inspect_history(n=3)` | Last N calls for a specific LM instance | [dspy.ai/tutorials/observability/](https://dspy.ai/tutorials/observability/) |
| **LangChain (max)** | `from langchain.globals import set_debug; set_debug(True)` | Prompt + response + chain internals for every call | [python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html) |
| **LangChain (lighter)** | `set_verbose(True)` | Prompt + response only | [python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html](https://python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html) |
| **LangGraph** | `graph.get_state_history(config)` | Per-step state including messages (rendered LM input) | [langchain-ai.github.io/langgraph/concepts/time-travel/](https://langchain-ai.github.io/langgraph/concepts/time-travel/) |
| **LangGraph (fork)** | `graph.update_state(config, {...})` then `graph.invoke(None, config={"checkpoint_id": ...})` | Replay/fork from any past checkpoint (re-pays LM cost) | [docs.langchain.com/oss/python/langgraph/use-time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel) |
| **CrewAI** | `Agent(..., verbose=True)` + `Crew(..., verbose=True)` | Agent thoughts, tool I/O, final answer | [docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents) |
| **CrewAI (structured)** | `Agent(..., step_callback=fn)` | Per-step AgentAction / observation captured in your callback | [docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents), [docs.crewai.com/en/observability/overview](https://docs.crewai.com/en/observability/overview) |
| **LlamaIndex** | `Settings.callback_manager = CallbackManager([LlamaDebugHandler(...)])` then `handler.get_llm_inputs_outputs()` | All LLM inputs/outputs during a query | [docs.llamaindex.ai](https://docs.llamaindex.ai/) (debugging guide) |
| **Aider** | `/diff` (last turn) + `aider --verbose` (full rendered prompt) | Per-turn diff and full prompt sent | [aider.chat/docs/usage/commands.html](https://aider.chat/docs/usage/commands.html) |
| **OpenAI SDK** | `export OPENAI_LOG=debug` | Full HTTP request + response (incl. API key — strip!) | [github.com/openai/openai-python](https://github.com/openai/openai-python) README §Logging |
| **Anthropic SDK** | `export ANTHROPIC_LOG=debug` | Full HTTP request + response (incl. API key — strip!) | [github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) README §Logging |
| **Any SDK (clean)** | Custom `httpx.Client(event_hooks={"request": [log_fn]})` passed via `http_client=` | Structured JSON body of every request | [til.simonwillison.net/httpx/openai-log-requests-responses](https://til.simonwillison.net/httpx/openai-log-requests-responses) |
| **Production traces** | Open the run in LangSmith / LangFuse / Phoenix / MLflow | Rendered prompt + response for a specific production thread | Per-platform skill |

### Decision tree (one screen)

```
LM call surprised you?
   │
   Yes ──► STOP. Do not edit the prompt. Do not retry. Do not swap models.
            │
            ▼
   What framework?
      DSPy            → dspy.inspect_history(n=1)
      LangChain       → set_debug(True)
      LangGraph       → graph.get_state_history(config)
      CrewAI          → step_callback + verbose=True
      Aider           → /diff  AND  aider --verbose
      Raw OpenAI/Anth → OPENAI_LOG=debug  /  ANTHROPIC_LOG=debug
      Clean dump      → httpx event hook (OP-7)
      Production bug  → LangSmith / LangFuse / Phoenix trace
            │
            ▼
   Diff dump against expectation. Identify layer (1/2/3 — §3 Step 3).
            │
            ▼
   Fix at correct layer. Re-dump. Confirm prompt now matches.
            │
            ▼
   NOW check if the bug is fixed. If not, repeat from inspect.
```

### Ecosystem note

This skill is **adjacent** to but **distinct from** trace-UI skills:

- `langsmith`, `phoenix`, `langfuse`, `mlflow` provide the **UI** for inspecting traces.
- `prompt-history-inspect` provides the **SOP** (inspect-first discipline) and the **cross-framework command lookup**.

Use them together: this skill says *when* and *why* to inspect; the platform skills say *where* the UI lives. For local dev, the framework-native commands in §7 are usually enough.

### Key citations (all official)

- DSPy `inspect_history` API: [dspy.ai/api/utils/inspect_history/](https://dspy.ai/api/utils/inspect_history/)
- DSPy observability: [dspy.ai/tutorials/observability/](https://dspy.ai/tutorials/observability/)
- LangChain `set_debug`: [python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html)
- LangChain `set_verbose`: [python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html](https://python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html)
- LangChain debugging guide: [python.langchain.com/v0.1/docs/guides/development/debugging/](https://python.langchain.com/v0.1/docs/guides/development/debugging/)
- LangGraph time-travel: [langchain-ai.github.io/langgraph/concepts/time-travel/](https://langchain-ai.github.io/langgraph/concepts/time-travel/), [docs.langchain.com/oss/python/langgraph/use-time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
- CrewAI Agents (incl. `step_callback`, `verbose`): [docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents)
- CrewAI observability: [docs.crewai.com/en/observability/overview](https://docs.crewai.com/en/observability/overview)
- Aider commands: [aider.chat/docs/usage/commands.html](https://aider.chat/docs/usage/commands.html)
- OpenAI SDK logging: [github.com/openai/openai-python](https://github.com/openai/openai-python) README §Logging
- Anthropic SDK logging: [github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) README §Logging
- OpenAI debug-log API-key-leak warning: [github.com/openai/openai-python issue #1196](https://github.com/openai/openai-python/issues/1196), [issue #1082](https://github.com/openai/openai-python/issues/1082)
- HTTPX event-hook logger: [til.simonwillison.net/httpx/openai-log-requests-responses](https://til.simonwillison.net/httpx/openai-log-requests-responses)
