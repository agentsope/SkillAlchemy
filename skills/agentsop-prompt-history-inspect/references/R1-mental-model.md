# R1 — The Three-Layer Mental Model

The core insight behind this skill: **between the prompt you wrote and the prompt the model received, there are *at least* two transformation layers**, each of which can silently mutate, inject, drop, or reformat content.

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ LAYER 1          │ →  │ LAYER 2          │ →  │ LAYER 3          │
│ Your source code │    │ Framework render │    │ Provider transport│
│ (template,       │    │ (templating,     │    │ (HTTP body,      │
│  signature,      │    │  few-shot inject,│    │  role coercion,  │
│  chain config)   │    │  tool defs,      │    │  token cap,      │
│                  │    │  history mgmt,   │    │  finish reason)  │
│                  │    │  context cap)    │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
```

## Layer 1 — Your source code

What you typed. Variables, templates, signatures, chain configurations.

**Bugs at this layer**:
- Variable not interpolated (`{var}` shows up literally).
- Wrong key passed to the chain (`{"qery": ...}` instead of `{"query": ...}`).
- Signature field misnamed (DSPy `query -> response` when downstream expects `question -> answer`).
- Template f-string interpolated at definition time, not call time.

**How to inspect**: read the source. Conventional debugging.

**How to fix**: change the source.

## Layer 2 — Framework render

What the framework does to your code before it goes to the SDK. This is where most surprises live.

**Bugs at this layer**:
- **Few-shot injection** — DSPy compiled programs, LangChain `FewShotPromptTemplate`, CrewAI internal demos all inject few-shot exemplars at runtime. They can be wrong-for-task, take up too much budget, or leak training data.
- **System message auto-inject** — most agent frameworks prepend an "agentic" system message (instructions about tool use, reasoning, etc.) that you didn't write.
- **Tool definitions appended** — every tool's JSON-schema is serialised into the prompt. 10 tools = 2k+ tokens silently consumed (see Case B in SKILL.md).
- **History summarisation / truncation** — LangChain `ConversationSummaryMemory`, LangGraph state reducers, CrewAI memory all compress history. The compressed version may lose key facts.
- **Map-reduce / refine chains** — split-and-aggregate patterns can drop content the user assumed would be in the final prompt (see Case A).
- **Context truncation** — when total tokens exceed the model's window, frameworks silently drop the oldest / least-relevant content.
- **Demo selection** — compiled DSPy programs choose demos based on the optimizer's training distribution. Mismatch with test-time distribution = wrong demos.

**How to inspect**: framework-specific dump command (§7 of SKILL.md). The dump must show *what the framework produced*, not what you wrote.

**How to fix**: change framework config — different template, fewer demos, smaller tool set, different memory class, different chain type. Sometimes: change the module choice in DSPy (`ChainOfThought` vs `Predict`).

## Layer 3 — Provider transport

What the provider's SDK and API do to the rendered prompt before the model actually receives it.

**Bugs at this layer**:
- **Message role coercion** — providers normalise (`system` / `user` / `assistant`); multiple system messages may be concatenated or dropped depending on provider.
- **Token cap (`max_tokens`)** — output truncated mid-sentence. `finish_reason: "length"` is the signal.
- **Context window cap** — if your prompt + reserved completion budget exceeds the window, the provider may error or silently truncate (provider-dependent).
- **Streaming reassembly bugs** — partial tool calls, fragmented JSON.
- **Prompt caching boundaries** — some providers (Anthropic) cache prefixes; cache misses change latency and behaviour.
- **Model rerouting** — provider may route an "openai/gpt-4o" call to a specific snapshot or a quantised endpoint.

**How to inspect**: raw SDK debug logging (`OPENAI_LOG=debug` / `ANTHROPIC_LOG=debug`) or HTTPX event-hook (OP-7 in SKILL.md). This is the *only* way to see what actually hit the wire.

**How to fix**: change provider call config — different model, raise `max_tokens`, restructure messages to avoid role coercion, force-disable streaming, manage cache control points explicitly.

## Why "inspect at Layer 3" is the gold standard

For production debugging, only Layer-3 inspection (the raw HTTP body) is fully trustworthy. Layer-2 dumps (`set_debug`, `inspect_history`) show what the framework *thinks* it sent, but:

- They format the dump for human reading — newlines, role labels, indentation that don't match the wire.
- They may dump the *pre-serialisation* object, not the post-serialisation JSON.
- They may miss provider-specific transformations (cache control headers, tool-use format conversion).

In contrast, Layer-3 dumps (`OPENAI_LOG=debug` or HTTPX hook) show the literal bytes that went to the API. The trade-off: more noise, less readable.

**Rule of thumb**: start with Layer-2 (faster, cleaner). Escalate to Layer-3 when Layer-2 doesn't reveal the bug.

## The "30-second test"

You should be able, *right now*, to print the exact final prompt for whatever framework you're using, in under 30 seconds. If you can't:

- You don't have the framework's inspect command memorised → study §7 of SKILL.md.
- You don't have logging configured → set `OPENAI_LOG=debug` once and confirm it works.
- You don't have a debug toggle in your code → add `set_debug(True)` behind an env flag.

This is **infrastructure for debugging**. Set it up *before* the bug arrives, not during.

## Citations

- DSPy mental model on prompts-as-weights: arxiv.org/abs/2310.03714 (DSPy paper).
- LangChain debugging guide: python.langchain.com/v0.1/docs/guides/development/debugging/
- LangGraph time-travel concept (the only Layer-2 inspect that's free of LM cost when read-only): langchain-ai.github.io/langgraph/concepts/time-travel/
- OpenAI logging README: github.com/openai/openai-python (§Logging)
- Simon Willison's HTTPX hook pattern: til.simonwillison.net/httpx/openai-log-requests-responses
