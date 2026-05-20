# R2 — Framework Cheat Sheet (Extended)

Per-framework first-move command, with code, output shape, and gotchas. This is the long-form version of §7 of SKILL.md.

---

## DSPy

```python
import dspy

# Last 1 call (default n=1):
dspy.inspect_history()
# Last N calls:
dspy.inspect_history(n=5)

# Per-LM (if you've configured multiple LMs):
my_lm = dspy.LM("openai/gpt-4o")
dspy.configure(lm=my_lm)
# ... run program ...
my_lm.inspect_history(n=3)
```

**Output shape**: prints `[YYYY-MM-DD HH:MM:SS]` timestamp + system message + user message + assistant message + raw response for each call, ordered oldest-to-newest.

**Gotchas**:
- Shows **LM calls only** — not retrievers, not tool calls, not subgraphs.
- Issue [#784](https://github.com/stanfordnlp/dspy/issues/784) reported `n` parameter inconsistency historically; verify behaviour on your version.
- Issue [#1120](https://github.com/stanfordnlp/dspy/issues/1120) reported a `print` statement causing empty lines on console — minor, doesn't affect correctness.
- For multi-component pipelines, layer with `mlflow.dspy.autolog()` per [dspy.ai/tutorials/observability/](https://dspy.ai/tutorials/observability/).

**Source**: [dspy.ai/api/utils/inspect_history/](https://dspy.ai/api/utils/inspect_history/)

---

## LangChain

```python
from langchain.globals import set_debug, set_verbose

# Most verbose — prompt + response + chain internals:
set_debug(True)

# Lighter — prompt + response only:
set_verbose(True)

# Toggle off:
set_debug(False)
set_verbose(False)
```

**Output shape**: console-printed JSON-like blocks per call, showing the chain entry, the prompts passed to each LLM, the LLM output, the chain exit.

**Gotchas**:
- Process-global. Affects every LangChain call in the process.
- `set_debug(True)` produces a lot of noise — start with `set_verbose(True)` and escalate.
- Per-call alternative: pass `callbacks=[StdOutCallbackHandler()]` to a specific chain instead of toggling globally.
- For Layer-3 ground truth, combine with `OPENAI_LOG=debug` since LangChain's `set_debug` shows Layer 2.

**Source**:
- [python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html](https://python.langchain.com/api_reference/core/globals/langchain_core.globals.set_debug.html)
- [python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html](https://python.langchain.com/api_reference/langchain/globals/langchain.globals.set_verbose.html)
- Debugging guide: [python.langchain.com/v0.1/docs/guides/development/debugging/](https://python.langchain.com/v0.1/docs/guides/development/debugging/)

---

## LangGraph

```python
# Inspect history (read-only, free):
config = {"configurable": {"thread_id": "user-123"}}
history = list(graph.get_state_history(config))
for snap in history:
    print("Checkpoint:", snap.config["configurable"]["checkpoint_id"])
    print("State:", snap.values)             # includes messages array (LM input)
    print("Next nodes:", snap.next)

# Replay from a checkpoint (RE-PAYS LM cost):
graph.invoke(
    None,
    config={"configurable": {"thread_id": "user-123",
                              "checkpoint_id": "<chosen id>"}},
)

# Fork by modifying state (also re-pays LM cost):
graph.update_state(config, {"messages": [...new message...]})
graph.invoke(None, config)
```

**Output shape**: `StateSnapshot` objects with `values` (dict of state fields), `config`, `next` (tuple of node names to execute next), `metadata`.

**Gotchas**:
- Requires a checkpointer configured on the graph (`MemorySaver`, `PostgresSaver`, `SqliteSaver`).
- **`invoke(None, config=...)` re-executes nodes** — LLM calls and tool calls fire again. Read state for free; replay only when needed [[time-travel docs](https://langchain-ai.github.io/langgraph/concepts/time-travel/)].
- `get_state_history` returns newest first by default — reverse if you want chronological order.

**Source**:
- [langchain-ai.github.io/langgraph/concepts/time-travel/](https://langchain-ai.github.io/langgraph/concepts/time-travel/)
- [docs.langchain.com/oss/python/langgraph/use-time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)

---

## CrewAI

```python
from crewai import Agent, Crew

# Per-step structured callback:
def my_step_callback(step_output):
    # step_output is AgentAction (tool call) or AgentFinish (final)
    print(f"STEP: {step_output}")

agent = Agent(
    role="...", goal="...", backstory="...",
    verbose=True,                  # prints thoughts + tool I/O
    step_callback=my_step_callback,  # structured per-step capture
)

crew = Crew(
    agents=[agent], tasks=[...],
    verbose=True,                  # prints crew-level events
)
```

**Output shape**:
- `verbose=True` prints a mix of agent thoughts, action JSON, tool input, tool observation, and "Final Answer".
- `step_callback` receives `AgentAction(tool, tool_input, log)` or `AgentFinish(return_values, log)` per step.

**Gotchas**:
- CrewAI's internal log is intentionally narrative-style — for structured production data, use `step_callback` *and* a real observability backend (Langtrace, OpenLIT, AgentOps, MLflow).
- `task_callback` also exists — fires after each task completes, not each step.
- `step_callback` set on `Agent` fires per agent step; on `Crew` fires per crew-level step.

**Source**:
- [docs.crewai.com/en/concepts/agents](https://docs.crewai.com/en/concepts/agents) (`step_callback`, `verbose` parameters)
- [docs.crewai.com/en/observability/overview](https://docs.crewai.com/en/observability/overview)

---

## LlamaIndex

```python
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

handler = LlamaDebugHandler(print_trace_on_end=True)
Settings.callback_manager = CallbackManager([handler])

# ... run query ...

# Get LLM inputs/outputs:
llm_events = handler.get_llm_inputs_outputs()
for event_pair in llm_events:
    print("Input:", event_pair[0].payload)
    print("Output:", event_pair[1].payload)
```

**Output shape**: list of `(start_event, end_event)` tuples per LLM call. Payload contains messages and response.

**Gotchas**:
- Global via `Settings.callback_manager` — same scope caveats as LangChain.
- `print_trace_on_end=True` is a quick toggle; the `get_llm_inputs_outputs()` API is for programmatic access.
- Event types: `LLM`, `EMBEDDING`, `RETRIEVE`, `SYNTHESIZE`, etc. — filter by type if you only want LM calls.

**Source**: docs.llamaindex.ai (debugging / observability section)

---

## Aider

```bash
# CLI flags:
aider --verbose             # prints every full prompt sent
aider --verbose --message "..."  # one-shot with verbose

# In-session slash commands:
/diff        # last turn's diff (what aider actually changed)
/tokens      # current token budget breakdown
/ls          # files in chat (editable) vs read-only
/map         # repo-map sent to the LLM
```

**Output shape**: `/diff` shows a git-style diff. `--verbose` prints the full rendered prompt to stderr each turn.

**Gotchas**:
- Aider auto-commits successful edits — `git log -p HEAD~1` is a sister tool to `/diff`.
- `/clear` and `/reset` change the rendered prompt by wiping history — re-test after.
- Verbose output is voluminous; pipe to a file (`aider --verbose 2> aider.log`).

**Source**: [aider.chat/docs/usage/commands.html](https://aider.chat/docs/usage/commands.html)

---

## Raw OpenAI SDK

```bash
# Enable debug logging via env var (stdlib logging under the hood):
export OPENAI_LOG=debug    # or =info for less noise
python my_script.py
```

```python
# Programmatic alternative:
import logging
logging.basicConfig(level=logging.DEBUG)  # affects all loggers including openai
```

**Output shape**: stderr lines including HTTP method, URL, headers, body, response status, response body.

**Gotchas — CRITICAL**:
- **`OPENAI_LOG=debug` logs the `Authorization` header in plaintext** — your API key ends up in logs [[issue #1196](https://github.com/openai/openai-python/issues/1196), [issue #1082](https://github.com/openai/openai-python/issues/1082)]. Never commit a debug log, never paste it raw, scrub the `Authorization:` line before sharing.
- Disable for production deployments.

**Source**: [github.com/openai/openai-python](https://github.com/openai/openai-python) README §Logging

---

## Raw Anthropic SDK

```bash
export ANTHROPIC_LOG=debug    # or =info
```

Same model as OpenAI — env var sets stdlib logging level. Same API-key-leak warning applies.

**Source**: [github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) README §Logging

---

## Clean dump via HTTPX event hook (works for both)

```python
import httpx, json
from openai import OpenAI

def log_request(req: httpx.Request):
    print(f"==> {req.method} {req.url}")
    if req.content:
        try:
            print(json.dumps(json.loads(req.content), indent=2))
        except Exception:
            print(req.content.decode("utf-8", errors="replace"))

def log_response(resp: httpx.Response):
    print(f"<== {resp.status_code}")
    # Note: response body in event hook requires read() first

http_client = httpx.Client(
    event_hooks={"request": [log_request], "response": [log_response]},
)
client = OpenAI(http_client=http_client)
# ... use `client` as normal ...
```

**Output shape**: clean JSON dump of every request body. No API key leaked (unless you log headers).

**Gotchas**:
- Both OpenAI and Anthropic SDKs accept `http_client=` — same pattern works for both.
- Async variant: `httpx.AsyncClient` + `AsyncOpenAI`.
- Reading response body in the hook requires `resp.read()` first — see [httpx discussion #3073](https://github.com/encode/httpx/discussions/3073).

**Source**: [til.simonwillison.net/httpx/openai-log-requests-responses](https://til.simonwillison.net/httpx/openai-log-requests-responses)

---

## When NONE of these are quite right: dump from a known good observability platform

If you've already wired LangSmith / LangFuse / Phoenix / MLflow, open the trace UI and inspect the rendered prompt there. The first-move SOP still applies — only the *mechanism* of the dump changes. See OP-9 in SKILL.md.
