# R5 — Ecosystem Context

## Layer map

DSPy is **not** in the same layer as LangChain, LlamaIndex, or LangGraph. It sits *underneath* them as a compiler for individual LM calls [langwatch.ai/blog/best-ai-agent-frameworks-in-2025].

```
┌──────────────────────────────────────────────┐
│  Orchestration:  LangGraph, CrewAI, Dify     │  graphs, agents, state, HITL
├──────────────────────────────────────────────┤
│  Retrieval:      LlamaIndex                  │  ingestion, indexing, query engines
├──────────────────────────────────────────────┤
│  Compiler:       DSPy                        │  signatures + modules + compile
├──────────────────────────────────────────────┤
│  Generation:     Guidance, LMQL, Outlines    │  single-call grammar / structured output
├──────────────────────────────────────────────┤
│  Inference:      vLLM, llama.cpp, Anthropic  │  serving
└──────────────────────────────────────────────┘
```

This layering is the central frame for understanding when DSPy combines with what.

---

## DSPy vs LangChain

**LangChain**: orchestration framework. Composes LLM calls, memory, tools, agents. Prompts are hand-authored templates.

**DSPy**: compiler for LM calls. Prompts are *generated* artifacts.

**Code comparison** (same agent task) [eito.substack.com/p/dspy-the-most-misunderstood-agent]:
- DSPy: 30 lines.
- OpenAI Agents SDK: 46 lines.
- LangChain: 71 lines.

**Together**: friction. LangChain's prompt-template assumption collides with DSPy's compile-the-prompt model. If you must combine, isolate DSPy modules behind clean Python interfaces and treat them as opaque LLM calls from LangChain's perspective. Per the FAQ: "DSPy doesn't internally contain hand-crafted prompts" — that's the deliberate split [dspy.ai/faqs/].

**Decision**: pick one per pipeline. Mixed adoption is usually a smell.

---

## DSPy vs LangGraph

**LangGraph**: stateful graph orchestration — nodes, edges, conditional routing, checkpointing, human-in-the-loop. Reasoning lives *in* a node body.

**DSPy**: the LM call *inside* a node — optimized for prompt quality.

**Together**: highly complementary. The community-validated pattern [rajapatnaik.com/blog/2025/10/23/langgraph-dspy-gepa-researcher, medium.com/@akankshasinha247]:

```
LangGraph node:
  ┌──────────────────────────────────────┐
  │ def my_node(state):                  │
  │     compiled_dspy = load_compiled()  │
  │     pred = compiled_dspy(            │
  │         question=state.question)     │
  │     return {"answer": pred.answer}   │
  └──────────────────────────────────────┘
```

LangGraph handles state, routing, retries. DSPy handles prompt quality inside each node. Quote from acldigital.com:

> "DSPy fits into the Prompt Management & Optimization layer—bringing software engineering discipline to prompting. LangGraph fits into the Orchestration & Agent Framework layer."

**Decision**: combine. This is one of the few cross-skill combinations that's clearly additive.

---

## DSPy vs LlamaIndex

**LlamaIndex**: data ingestion, indexing, retrieval, query engines. ~300 data connectors.

**DSPy**: optimizes the generator / reranker / synthesizer downstream of retrieval.

**Together**: textbook pattern [databricks.com/blog/optimizing-databricks-llm-pipelines-dspy]. JetBlue's RAG chatbot uses this split:
- Retrieval quality = one metric.
- Answer quality = another metric.
- DSPy optimizes both via two compiled modules.

```
LlamaIndex retriever → DSPy-compiled Predict(context, question -> answer)
```

**Decision**: combine. LlamaIndex's batteries-included query engines also work without DSPy; switch to DSPy-in-the-loop when you have evaluation metrics and want to drive them.

---

## DSPy vs Guidance / LMQL / Outlines

**Those tools**: per-call structured output. Force valid JSON, regex match, BNF grammar.

**DSPy**: multi-call program optimization. Doesn't guarantee grammar conformance (only nudges via typed `OutputField`).

**Together**: orthogonal, additive. Use Outlines to force valid JSON shape; use DSPy to make the JSON-emitting *prompt* good. Per FAQ: "Those libraries handle low-level, structured control of a single LM call but don't ensure the JSON is going to be correct or useful for your task" — DSPy provides the latter [dspy.ai/faqs/].

**Decision**: combine when both are needed.

---

## DSPy vs raw prompt engineering

| | Raw prompts win | DSPy wins |
|---|---|---|
| Pipeline depth | 1 LM call | ≥ 2 calls |
| Data | None | ≥ 30 examples |
| Metric | None / informal | Exists, even noisy |
| Iteration | One-off | Multiple cycles, model swaps |
| Audit constraint | Verbatim required | Generated artifacts OK |
| Team familiarity | Low | Comfortable with PyTorch-style abstractions |

---

## Production case studies

| Org | Use case | Reference |
|---|---|---|
| **JetBlue + Databricks** | RAG chatbot, customer feedback classification, predictive maintenance | [databricks.com/blog/optimizing-databricks-llm-pipelines-dspy] |
| **Haize Labs** | Automated red-teaming for LLMs | [dspy.ai/community/use-cases/] |
| **Databricks** | LM Judges, RAG, classification products | [databricks.com/blog/dspy-databricks] |
| **Shopify, Dropbox, Moody's, AWS, Sephora, VMware** | "In production" per official site | [dspy.ai] |

Endorsement: Tobi Lütke (Shopify CEO): "Both DSPy and (especially) GEPA are currently severely under hyped in the AI context engineering world" [eito.substack.com].

---

## When the 7-project landscape combines

For the synthesis pipeline this skill feeds into:

- **DSPy + LangGraph** — additive (DSPy inside nodes).
- **DSPy + LlamaIndex** — additive (LlamaIndex retrieves, DSPy synthesizes).
- **DSPy + vLLM** — additive (vLLM serves the LM that DSPy optimizes against). vLLM is a serving layer; DSPy is the compile layer; they don't interact except via the OpenAI-compatible API surface.
- **DSPy + Aider** — orthogonal. Aider is an interactive coding agent; DSPy is library-level. No native integration.
- **DSPy + CrewAI** — overlap. CrewAI is multi-agent orchestration with hand-authored agent prompts. Combining is possible (DSPy-compile the LLM calls inside crew agents) but the cultural fit is awkward — CrewAI users typically want the "prompt as configuration" model, which is the opposite of DSPy's "prompt as compiled artifact."
- **DSPy + Dify** — Dify is a no-code/low-code app builder; combining with DSPy is unusual (Dify's audience generally doesn't want compile-time optimization in the loop).

The cleanest combinations are with **LangGraph (orchestration)** and **LlamaIndex (retrieval)**. The cleanest *contrast* is with **LangChain / CrewAI** (hand-prompt orchestrators).
