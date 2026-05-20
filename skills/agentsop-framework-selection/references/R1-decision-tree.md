# R1 · Decision Tree & Source Evidence

Resolves every inline `<sop> · <id>` source tag used in `SKILL.md` to the 7
landmark-project SOPs' R5 ecosystem sections plus the Phase B inventory. This
skill is a *synthesis*; the authority for any single claim lives in the cited SOP.

## Source map

| Tag prefix | Resolves to |
|---|---|
| `langgraph-sop · R5` | `output/langgraph-sop-skill/references/R5-ecosystem-context.md` |
| `llamaindex-sop · R5` | `output/llamaindex-sop-skill/references/R5-ecosystem-context.md` |
| `dspy-sop · R5` | `output/dspy-sop-skill/references/R5-ecosystem-context.md` |
| `crewai-sop · R5`, `crewai-sop · OP-1`, `crewai-sop · DC-1` | `output/crewai-sop-skill/` (R5 + operation_candidates.json) |
| `vllm-sop · R5`, `vllm-sop · OP-7` | `output/vllm-sop-skill/references/R5-ecosystem-context.md` |
| `aider-sop · R5` | `output/aider-sop-skill/references/R5-ecosystem-context.md` |
| `dify-sop · R5` | `output/dify-sop-skill/references/R5-ecosystem-context.md` |
| `phase-b · open-questions` | `output/phase-b-coder-agent-skill-inventory.md` (capability A7 + "where the 7 SOPs disagree") |

---

## The master decision tree (Pass A → B → C)

```
PROJECT KICKOFF
   │
   ▼
PASS A · Which layers do I need? (walk the stack)
   ├─ L1 Modeling      — non-trivial LM call iterated/swapped/parsed?      → almost always YES
   ├─ L2 Retrieval     — answer over private/large/changing data?         → YES → need retrieval
   ├─ L3 Orchestration — cycle/branch/memory/HITL/>1 agent?               → YES → need orchestration
   ├─ L6 Serving       — self-hosting open-weights (vs hosted API)?       → YES → [[agentsop-llm-engine-selection]]
   ├─ L7 App platform  — non-engineers operate it? need UI+API+auth?      → YES → consider platform
   └─ Coding surface   — deliverable is code edits in a repo?             → YES → [[agentsop-repo-state-gating]]
   │
   ▼
PASS B · Per-layer pick (apply §4 rubric to each needed layer)
   │
   ▼
PASS C · G0 gate (framework vs raw, per layer) + interop check (§7 map)
   │
   ▼
OUTPUT: one decision line per layer
```

## Per-layer sub-trees

### L1 — Modeling / prompt-compile (`dspy-sop · R5`)

```
1 LM call, no metric, verbatim-prompt audit, rapid iteration → RAW prompts
≥2 calls AND ≥30 examples AND a metric AND model-swaps      → DSPy (compile to artifact)
need valid JSON/regex/BNF on a single call                  → Outlines / Guidance / LMQL
                                                              (orthogonal: combine with DSPy)
AVOID: DSPy + LangChain prompt-templates (same-layer collision, "a smell")
```

DSPy line-count evidence (same agent task): DSPy 30 · OpenAI Agents SDK 46 ·
LangChain 71 — but fewer lines is *not* a reason to compile a task that doesn't
need it (DC-2). DSPy "sits underneath LangChain/LlamaIndex/LangGraph as a compiler
for individual LM calls." Production users: JetBlue+Databricks, Haize Labs,
Shopify, Dropbox, Moody's, AWS, Sephora, VMware.

### L2 — Retrieval / context (`llamaindex-sop · R5`, `dify-sop · R5`, `aider-sop · R5`)

```
corpus <100k tokens AND static                  → NO framework (stuff context + prompt cache)
private/large/changing prose data               → LlamaIndex (index = first-class noun)
"classical IR + LLM bolted on", YAML ops         → Haystack
hard-document RAG quality is THE bottleneck      → RAGFlow
will reimplement ≤2 RAG primitives               → raw vector store SDK (else rebuild LlamaIndex badly)
the "corpus" is a code repo                       → Aider tree-sitter repo-map (NOT embeddings)
```

LlamaIndex 2025 self-positioning: "the leading document agent and OCR platform"
(deliberately *document* agent, not general agent). Hybrid norm: "LlamaIndex as
the retrieval layer, LangGraph as the orchestration layer." Aider repo-map:
70.3% correct-file on SWE-Bench Lite without embeddings/index. **Disagreement:**
LlamaIndex assumes embeddings work for code; Aider's evidence contradicts. No SOP
reconciles — likely "repo-map for code, embeddings for prose" (`phase-b ·
open-questions`).

### L3 — Orchestration / control (`langgraph-sop · R5`, `crewai-sop · R5`, `llamaindex-sop · R5`)

```
control flow fits in if/else, no state, no HITL  → single agent + tools / raw SDK
roles on a whiteboard, no branching, demo-fast    → CrewAI Sequential
need cycles/durable-state/HITL/time-travel/parallel topology → LangGraph
retrieval-heavy + SOME agency, stay in-ecosystem  → LlamaIndex Workflows
debate/negotiation IS the product                 → AutoGen (⚠ maintenance mode)
study/reference only                              → OpenAI Swarm (⚠ experimental)
```

Comparison matrix (`langgraph-sop · R5`):

| Dim | LangGraph | CrewAI | AutoGen | Swarm |
|---|---|---|---|---|
| Paradigm | state graph | role crew | conversation | handoff |
| Production 2026 | first-class | "limited; lacks persistence" | maintenance mode | not production |
| Persistence | Sqlite/Postgres/Redis | none built-in | bolt-on | none |
| HITL | first-class `interrupt()` | limited | limited | none |
| Learning curve | steep | excellent docs | moderate | gentle |

CrewAI three philosophies: Agent(role) / Node+State(LangGraph) / Conversation
(AutoGen). Honest 2026 consensus: production reliability → LangGraph; team
velocity / "ship by Friday" → CrewAI. Standard arc: prototype CrewAI → port
LangGraph. **Disagreement:** no clean crossover-point rubric; CrewAI itself
recommends the port, conceding it (`phase-b · open-questions`).

### L6 — Serving (`vllm-sop · R5`, `vllm-sop · OP-7`) — defer to [[agentsop-llm-engine-selection]]

```
hosted API (OpenAI/Anthropic)                     → skip L6 entirely
production + GPU + concurrent users                → vLLM (2026 default)
prefix-heavy agent/RAG (shared context)            → A/B SGLang (RadixAttention, ~29% higher when shared)
NVIDIA-only + 1–2wk tuning budget + accept lock-in → TensorRT-LLM (+30–50% high-concurrency)
no GPU OR ≤1 user OR edge/Apple-Silicon            → llama.cpp / GGUF
local dev / prototyping / model switching          → Ollama
existing TGI not broken                            → keep, but new projects default vLLM/SGLang
```

vLLM throughput: 14–24× HF Transformers; 2.2–3.5× early TGI. Vendor-neutral
(NVIDIA/AMD/Intel/TPU/Ascend/CPU), 200+ architectures, OpenAI-compatible API.
HF itself now recommends vLLM/SGLang over its own maintenance-mode TGI.

### L7 — App platform (`dify-sop · R5`)

```
scaffolding is the bottleneck + mixed-role team    → Dify (visual DAG + Code-node escape)
single "chatbot + doc retrieval" demo, fastest      → Flowise (thin beyond that)
visual builder you can EXPORT to Python & evolve    → LangFlow (LangChain-bound)
automation-first (400+ non-AI integrations), AI sprinkled → n8n
managed bots in Feishu/Lark, zero ops               → Coze (ByteDance, hosted only)
```

Dify ceilings (Dify-engine-specific, uncorroborated → directional only):
graph >40–50 nodes (canvas/comprehension collapse); needs HITL (issue #21455
"not planned" — explicitly unsupported); >10 QPS/pod sustained; extreme RAG;
sub-second latency. Past ceiling → retreat to "frontend + monitoring + simple RAG"
and move core logic to LangGraph/Temporal/custom. Adopters: Maersk, ETS, Samsung
(vLLM+Dify air-gapped), banks.

### Coding surface (`aider-sop · R5`) — gate via [[agentsop-repo-state-gating]]

```
greenfield, nothing exists yet                      → plain LLM chat (not a coding agent)
existing repo + terminal + git-clean + scriptable   → Aider
existing repo + per-tool-call approval in VS Code    → Cline
existing repo + visual/autocomplete + closed product → Cursor
existing repo + cross-IDE (VS Code + JetBrains)      → Continue
autonomous ticket → PR in a sandbox                  → OpenHands
```

Aider's transferable research (reference text even if you pick another surface):
edit-format selection (udiff 20%→61% on GPT-4 Turbo refactor); repo-map > RAG for
code; architect+editor split (79.7%→85% Polyglot); JSON-vs-text (every tested
model worse with JSON-wrapped code — but **code-specific**, do not over-generalize
to extraction tasks, `phase-b · open-questions`).

---

## The canonical additive stack (2026 consensus)

```
DSPy (compile LM calls)
   │ additive — compiled module loaded inside a node
   ▼
LlamaIndex (retrieve)
   │ additive — retriever exposed as a tool
   ▼
LangGraph (orchestrate: durable state + HITL + time-travel)
   │ calls model via OpenAI-compatible API
   ▼
vLLM (serve open-weights)
   │ optionally fronted by
   ▼
Dify (UI / auth / API; calls the above behind HTTP)
```

Cited as the praised production pattern across `dspy-sop · R5`,
`llamaindex-sop · R5`, `dify-sop · R5`.

## Open disagreements (NOT resolved — `phase-b · open-questions`)

1. **Graph vs role crossover** — LangGraph (durability) vs CrewAI (prototype
   speed); no clean rubric; "prototype → port" concedes it.
2. **HITL first-class vs unsupported** — LangGraph definitional; Dify "not
   planned." Must be known *before* platform pick.
3. **Visual ceiling thresholds** — Dify's 20/40-node numbers are engine-specific,
   uncorroborated by other SOPs.
4. **Embeddings vs symbol-map for code** — LlamaIndex assumes embeddings; Aider
   beats them with tree-sitter repo-map. Likely "repo-map for code, embeddings for
   prose" but unstated.
5. **JSON-tool-calls for non-code outputs** — Aider's degradation finding is
   code-specific; extraction tasks untested. Do not over-generalize.
6. **Multi-agent benefit at all** — even multi-agent SOPs concede single-agent is
   right for ~80% of cases (`crewai-sop · DC-1`).
