---
name: agentsop-framework-selection
version: 0.1.0
description: |
  Neutral, framework-agnostic decision tree for project kickoff: "which agent /
  RAG / LLM framework should I reach for?" Synthesizes the ecosystem sections of
  7 landmark-project SOPs (LangGraph, LlamaIndex, DSPy, CrewAI, vLLM, Aider, Dify)
  into one layered rubric. Core stance: frameworks are LAYERS, not competitors —
  a real project usually combines DSPy (compile) + LlamaIndex (retrieve) +
  LangGraph (orchestrate) + vLLM (serve), and you choose ONE per layer, not one
  to rule all. Use when starting any LLM/agent/RAG project, or whenever
  the "which framework?" question is asked. Deliberately neutral — unlike vendor
  docs and the LangChain-biased `framework-selection` on skill.sh, this skill has
  no horse in the race.
overlay: true
cross_links: [llm-engine-selection, agent-topology-selection, repo-state-gating]
---

# Framework-Fit Decision Tree at Project Kickoff · SOP (ENHANCE overlay)

> Overlay posture: this is the **capstone** Phase-D skill — the most-cited entry
> at any project kickoff. It decides *which layer(s) you need* and *which
> framework owns each layer*. It does **not** teach any framework's API; for that,
> descend to the per-framework SOPs (`langgraph-sop`, `llamaindex-sop`,
> `dspy-sop`, `crewai-sop`, `vllm-sop`, `aider-sop`, `dify-sop`). Every
> load-bearing claim carries an inline source tag resolving in
> `references/R1-decision-tree.md`.
>
> Neutrality note: vendor pages each claim the center of the universe
> (LangChain: "use LangGraph for production"; LlamaIndex: "the document agent
> platform"; Dify: "scaffolding is the bottleneck"). This skill quotes those
> claims but does not adopt any of them. The 7 SOPs *disagree* on the crossover
> points; we surface the disagreements rather than papering over them.

---

## 1. 何时激活 (When to Activate)

Activate when **any** of the following fire:

- A new LLM / agent / RAG project is starting and no framework has been chosen yet.
- Someone asks "which framework should I use?" / "LangChain or LlamaIndex?" /
  "LangGraph vs CrewAI?" / "do we need a framework at all?"
- A coder is about to `pip install` an orchestration / RAG / agent framework
  before having articulated *what layers the project needs*.
- A project already picked one framework "for everything" and is now fighting it
  in a layer it was never good at (e.g., doing deep RAG inside CrewAI, or
  hand-rolling retrieval inside LangGraph).
- A no-code / visual builder (Dify, Flowise, LangFlow) has hit a complexity
  ceiling and the team is asking "do we rewrite in code?"

Do **not** re-run this skill mid-implementation for a layer already chosen — that
is churn. Run it once at kickoff, and again only when a *new layer* appears
(e.g., "we now need to self-host the model" → triggers `[[agentsop-llm-engine-selection]]`).

> Mental check: *the wrong framework is the single highest-cost decision in the
> project — it is a one-week-to-reverse mistake, sometimes a one-month one.*
> `crewai-sop · OP-1`, `vllm-sop · OP-7`. Spend 20 minutes on this tree before
> opening any tutorial.

---

## 2. 核心心智模型 (Core Mental Model)

**Frameworks are layers, not competitors.** The single most common kickoff error
is treating "LangChain vs LlamaIndex vs DSPy vs CrewAI vs vLLM" as a horse race
with one winner. They are not on the same axis. A mature LLM system is a *stack*:

```
┌─────────────────────────────────────────────────────────────┐
│  L7 App platform / UI / Auth   │ Dify, Flowise, LangFlow      │  ship-fast scaffolding
├─────────────────────────────────────────────────────────────┤
│  L6 Serving / inference        │ vLLM, SGLang, llama.cpp …    │ → see [[agentsop-llm-engine-selection]]
├─────────────────────────────────────────────────────────────┤
│  L3 Orchestration / control    │ LangGraph, CrewAI, Workflows │ → see [[agentsop-agent-topology-selection]]
├─────────────────────────────────────────────────────────────┤
│  L2 Retrieval / context        │ LlamaIndex, Haystack         │  ingestion, index, query
├─────────────────────────────────────────────────────────────┤
│  L1 Modeling / prompt-compile  │ DSPy, Outlines, Guidance     │  the LM call itself
├─────────────────────────────────────────────────────────────┤
│  Coding-agent surface (cross)  │ Aider, Cline, Cursor …       │  end-user product, not a layer
└─────────────────────────────────────────────────────────────┘
```

DSPy's own ecosystem doc draws this layering explicitly — DSPy "sits *underneath*
LangChain, LlamaIndex, LangGraph as a compiler for individual LM calls"
`dspy-sop · R5`. LlamaIndex's doc says "many production systems use both:
LlamaIndex as the retrieval layer, LangGraph as the orchestration layer"
`llamaindex-sop · R5`. Dify's doc describes the hybrid "Dify for frontend/RAG/auth
+ LangGraph for core agent logic behind HTTP" `dify-sop · R5`. The convergence is
unanimous: **choose per layer, then check interop.**

Three corollaries:

1. **You may not need every layer.** A static-corpus Q&A bot needs L1 only
   (stuff the context window). A RAG chatbot needs L1+L2. A durable multi-step
   agent needs L1+L2+L3. Only self-hosting adds L6. Only mixed-role teams add L7.
2. **The cleanest combinations are additive; the awkward ones are same-layer.**
   DSPy+LangGraph (compile-inside-node) and LlamaIndex+LangGraph (retrieve-then-
   orchestrate) are textbook `dspy-sop · R5`. DSPy+LangChain or DSPy+CrewAI are a
   "smell" — both are L1-ish prompt strategies fighting for the same slot
   `dspy-sop · R5`.
3. **"No framework" is a legitimate answer for ≥1 layer.** Frameworks earn their
   dependency surface only past a complexity threshold (§4 gate G0).

---

## 3. SOP (The Procedure)

The kickoff procedure runs as numbered steps (Pass A = Steps 1–6, Pass B = Step 7, Pass C = Step 8):

**Pass A — Identify the layers you actually need.** Walk the stack top to bottom
and mark each layer needed / not-needed for *this* project:

1. L1 Modeling — Is there ≥1 non-trivial LM call whose prompt will be iterated,
   swapped across models, or whose output is parsed by code? (Almost always yes.)
2. L2 Retrieval — Does the system answer over private / large / changing data it
   cannot fit in context? (Yes → need retrieval. No → skip.)
3. L3 Orchestration — Is there cycle / branch / memory-across-turns / human
   approval / >1 coordinating agent? (Yes → need orchestration. A single straight-
   line call → skip; raw SDK suffices.)
4. L6 Serving — Are you hosting open-weights models yourself (vs calling a hosted
   API)? (Yes → `[[agentsop-llm-engine-selection]]`. No → skip.)
5. L7 App platform — Do non-engineers (PM/ops) need to co-author or operate the
   app, or do you need UI+API+auth+logging out of the box? (Yes → consider a
   platform. No → code framework.)
6. Coding-agent surface — Is the deliverable *code edits in a repo*? (Yes →
   `[[agentsop-repo-state-gating]]` then Aider/Cline/Cursor. This is orthogonal to L1–L7.)

7. **Pass B — For each needed layer, apply the per-layer fit rubric** (§4). Each
   layer has its own short decision tree; do not let one framework's gravity pull
   you into using it for a layer it is weak at.

8. **Pass C — Check interop and the "do you even need a framework?" gate.** Confirm
   the chosen pieces compose (additive, not same-layer collisions — §7 interop map),
   and run gate G0 on each layer to confirm a framework beats raw SDK there.

Output of the procedure: a one-line-per-layer decision, e.g.
`L1: raw prompts (will revisit DSPy at 30 labeled examples) · L2: LlamaIndex ·
L3: LangGraph · L6: hosted API (no self-host yet) · L7: none (code-first)`.

## 4. 操作模型 (Operations)

### G0 — The "do you even need a framework?" gate (run per layer)

Before adopting *any* framework on a layer, confirm raw SDK is insufficient.
Frameworks trade dependency-surface and a learning curve for batteries. Raw wins
when the layer is trivial:

| Layer | Raw SDK wins when… | Framework wins when… |
|---|---|---|
| L1 | 1 LM call, no metric, verbatim-prompt audit need, rapid iteration | ≥2 calls, ≥30 labeled examples, a metric, model swaps `dspy-sop · R5` |
| L2 | corpus <100k tokens & static → stuff context + prompt cache | reimplementing >2 of {splitter, ingestion, reranker, synthesizer, evaluator} `llamaindex-sop · R5` |
| L3 | control flow expressible in plain `if/else`, no state-between-turns, no HITL | cycles, durable state, HITL, parallel topology `langgraph-sop · R5` |

> "If the corpus is small (<100k tokens) and static → no framework needed. Stuff
> the context window with prompt caching." `llamaindex-sop · R5`. "Plain LangChain
> [or raw SDK]: no cycles, no state-between-turns, no HITL — a single LLM call."
> `langgraph-sop · R5`.

### OP-1 — Layer identification (Pass A)

Mark each of L1/L2/L3/L6/L7 + coding-surface as needed or not, per §3 Pass A.
This is the highest-leverage step: most "wrong framework" pain is actually
"picked an L3 tool when the project was L2," or vice versa.

### OP-2 — L1 Modeling pick rubric

- **Raw prompts** — default for a single, rapidly-iterating call (G0).
- **DSPy** — when you have ≥2 LM calls, ≥30 labeled examples, and a measurable
  metric, and prompts are brittle on model swap. DSPy *compiles* prompts into a
  versioned artifact `dspy-sop · R5`. Combines additively into L3 (compile inside
  a LangGraph node) and L2 (compile the synthesizer downstream of a retriever).
- **Outlines / Guidance / LMQL** — when you need *grammar-level* guarantees
  (valid JSON / regex / BNF) on a single call. Orthogonal to DSPy: Outlines forces
  the shape, DSPy makes the prompt good `dspy-sop · R5`.
- Do **not** pick two L1 strategies that fight for the slot (DSPy + LangChain-
  prompt-templates is a "smell" `dspy-sop · R5`).

### OP-3 — L2 Retrieval pick rubric

- **LlamaIndex** — the default retrieval layer; index is a first-class noun,
  ~5-line baseline RAG, built-in evaluators, LlamaParse for messy documents
  `llamaindex-sop · R5`. Reach for it whenever private/large/changing data must
  be retrieved.
- **Haystack** — when the system is "classical IR with an LLM bolted on" and
  YAML-configurable pipelines are valued by ops `llamaindex-sop · R5`.
- **RAGFlow** — when *retrieval quality on hard documents* (tables, layout,
  KG-RAG) is the literal bottleneck, not app assembly `dify-sop · R5`.
- **Raw vector store (Pinecone/Qdrant/…)** — only if you will reimplement ≤2 RAG
  primitives (G0); otherwise you rebuild LlamaIndex badly `llamaindex-sop · R5`.
- **Repo-map (Aider tree-sitter), NOT embeddings** — when the "corpus" is a code
  repo. Aider's symbol-map hits 70.3% file-selection on SWE-Bench Lite without an
  index `aider-sop · R5`. The SOPs *disagree* here (LlamaIndex assumes embeddings
  work for code; Aider's evidence says repo-map beats them) — for code, prefer the
  repo-map; for prose, prefer embeddings (§6).

### OP-4 — L3 Orchestration pick rubric

First gate through `[[agentsop-agent-topology-selection]]` (single-agent + tools handles
~80% of "multi-agent" asks `crewai-sop · DC-1`). Then, if orchestration is needed:

- **Single agent + tools** — the baseline. `create_react_agent` (LangGraph),
  `dspy.ReAct`, a CrewAI single Agent, or a plain SDK tool loop. Start here.
- **LangGraph** — when the workflow needs cycles, durable state across crashes,
  human-in-the-loop (`interrupt()`), time-travel debugging, or
  supervisor/swarm/hierarchical parallelism `langgraph-sop · R5`. The 2026
  production-reliability leader.
- **CrewAI** — when the domain maps cleanly to *roles on a whiteboard*
  (researcher → writer → reviewer), non-engineers must read/edit agent definitions
  (YAML), and you want idea→demo fastest `crewai-sop · R5`. Trade-off: shallow
  state, thin eval, no built-in persistence.
- **LlamaIndex Workflows** — when the project is *retrieval-heavy* and needs only
  *some* agency; staying in-ecosystem keeps retrieval primitives as first-class
  neighbors `llamaindex-sop · R5`.
- The graph-vs-role crossover is the central disagreement (§5, DC-1). Common
  pattern: prototype on CrewAI, port to LangGraph for production `crewai-sop · R5`.
- **AutoGen** — only if conversation/debate is the literal product; note it is in
  **maintenance mode** as of 2026 — adopt with eyes open `crewai-sop · R5`,
  `langgraph-sop · R5`. **OpenAI Swarm** — study/reference only, not production.

### OP-5 — L6 Serving pick → delegate

If self-hosting open-weights models: hand off entirely to `[[agentsop-llm-engine-selection]]`.
One-line summary of that skill's rubric: production+GPU+concurrent → vLLM (the
2026 default); prefix-heavy agent/RAG → A/B SGLang; NVIDIA-locked + 1–2wk budget →
TensorRT-LLM; CPU/edge/≤1 user → llama.cpp; local dev → Ollama `vllm-sop · R5`,
`vllm-sop · OP-7`. If calling a hosted API (OpenAI/Anthropic/…), skip L6 entirely.

### OP-6 — L7 App-platform pick rubric

- **Dify** — when the bottleneck is *scaffolding* (UI+API+auth+vector store+logs
  +versioning in one box) and mixed-role teams (PM+ops+eng) co-author
  `dify-sop · R5`. Visual DAG with Code-node escape hatch.
- **Flowise** — fastest path for a single "chatbot + doc retrieval" demo; thin
  beyond that `dify-sop · R5`.
- **LangFlow** — when you want a visual builder you can later *export to Python*
  and evolve (LangChain-bound) `dify-sop · R5`.
- **n8n + AI nodes** — when the project is *automation-first* (400+ non-AI
  integrations) with AI sprinkled in, not AI-first `dify-sop · R5`.
- Mind the ceiling (§5 DC-3, §6): visual builders break down past ~40 nodes /
  HITL needs / >10 QPS/pod / extreme RAG / sub-second latency `dify-sop · R5`.

### OP-7 — Coding-agent surface pick → gate first

If the deliverable is code edits in a repo, gate through `[[agentsop-repo-state-gating]]`
(Aider et al. are for *existing* repos; greenfield → plain LLM chat
`aider-sop · R5`). Then: terminal + git-clean history + scriptable → Aider;
per-tool-call approval in VS Code → Cline; visual/autocomplete + closed product →
Cursor; cross-IDE → Continue; autonomous ticket→PR → OpenHands `aider-sop · R5`.
This surface is orthogonal to L1–L7 — a coding agent *uses* L1–L6 internally.

### OP-8 — Interop check (Pass C)

Confirm chosen pieces compose. Additive (good): DSPy-in-node, LlamaIndex-retriever-
as-tool, Dify-frontend + LangGraph-behind-HTTP, vLLM serving any of the above via
its OpenAI-compatible API `dspy-sop · R5`, `dify-sop · R5`. Collisions (re-pick):
two L1 prompt strategies; two L3 orchestrators owning the same control flow; a
visual platform asked to do what its code-escape-hatch should.

---

## 5. 困境决策案例 (Dilemma Cases)

### DC-1 — LangGraph vs CrewAI (graph vs role)

**Tension.** Both are L3 orchestrators; they pick different first abstractions.
LangGraph: "everything is a node in a state graph." CrewAI: "everything is a role
on a team" `crewai-sop · R5`. The SOPs openly concede there is **no clean rubric
for the crossover** — CrewAI itself recommends "prototype on Crew, port to
LangGraph for production," which *concedes* the disagreement
`phase-b · open-questions`.

**Resolution.** Decide on two axes:
- *Whiteboard test* — if you can draw the workflow as named teammates with
  handoffs and **no branching/cycles**, CrewAI Sequential is the faster path to a
  demo `crewai-sop · R5`.
- *Durability test* — if any of {cycles, crash-survival, multi-tenant shared
  threads, human-approval gate, time-travel debugging} is a hard requirement, go
  LangGraph — these are definitional there and absent/shallow in CrewAI
  `langgraph-sop · R5`.
- Honest 2026 consensus: production reliability → LangGraph; team velocity / "ship
  a demo by Friday" → CrewAI `crewai-sop · R5`. The standard arc is *prototype on
  CrewAI → port critical paths to LangGraph.*

### DC-2 — Framework vs raw SDK (when raw wins)

**Tension.** Framework gravity says "always use the framework." But every
framework is a dependency surface and a learning curve, and on a trivial layer it
is pure overhead `dify-sop · R5` (Dify's own doc: "for teams whose bottleneck is
expressive depth, Dify is overhead").

**Resolution.** Run G0 per layer. Raw SDK wins when: a single LM call with no
cross-turn state and no metric (L1); a corpus under 100k tokens that fits in
context with prompt caching (L2 `llamaindex-sop · R5`); control flow that fits in
plain `if/else` with no HITL (L3 `langgraph-sop · R5`). The DSPy line-count table
is instructive but *not* a reason to pick a framework — fewer lines on a task that
doesn't need compilation is a false economy `dspy-sop · R5`. Pick the framework
the moment you cross the threshold, not before.

### DC-3 — Dify (visual) vs a code framework (the ceiling)

**Tension.** Visual builders let PM/ops co-author and ship in days; code
frameworks give expressive depth. Picking visual *too early* wastes the
scaffolding savings; picking code *too early* excludes non-engineers
`dify-sop · R5`.

**Resolution.** Start visual (Dify) when the bottleneck is scaffolding and a
mixed-role team must operate the app; plan the **code-escape hatch up front**
(Code nodes, or externalize logic behind HTTP). Migrate to a code framework when
you hit Dify's stated ceilings: single graph >~40–50 nodes (canvas/comprehension
collapse), need for pause-wait-resume / time-travel (Dify explicitly **does not**
support HITL — issue #21455 "not planned"), sustained >10 QPS/pod, or extreme RAG
experimentation `dify-sop · R5`, `phase-b · open-questions`. Note the threshold
numbers are *Dify-engine-specific* and uncorroborated by other SOPs — treat as
directional, not gospel (§6).

### DC-4 — LlamaIndex vs LangGraph for agentic RAG (which layer leads?)

**Tension.** A "RAG agent" needs both L2 and L3; which framework do you build
*around*? LlamaIndex frames itself as "the document agent platform"
`llamaindex-sop · R5`; LangChain frames LangGraph as the production orchestrator
`langgraph-sop · R5`. Both want to be the spine.

**Resolution.** Let the *dominant difficulty* lead. If the hard part is messy
documents / retrieval quality, build around LlamaIndex (with LlamaParse) and add
LangGraph only when agentic logic emerges. If the hard part is multi-step
reasoning / many tools / durable state, build around LangGraph and embed
LlamaIndex retrievers as one tool among many `llamaindex-sop · R5`. They are not
competitors at the same layer — the error is forcing one to do the other's job.

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

- **AP-1 — Framework-driven development.** Picking the framework *before*
  articulating the problem ("let's build it in LangChain/CrewAI/Dify") and then
  bending the problem to fit. The fix is Pass A first: identify layers, *then*
  pick. The framework choice is downstream of the layer map, never upstream.
- **AP-2 — One framework for all layers.** Using CrewAI to do deep RAG, or
  LangGraph to hand-roll retrieval, or DSPy to orchestrate, because it was the
  first tool installed. Each framework is strong on ~1 layer and mediocre off it
  `dspy-sop · R5`. Choose per layer; compose.
- **AP-3 — Same-layer framework collision.** Combining two tools that fight for
  the same slot: DSPy + LangChain prompt-templates, two L3 orchestrators, or DSPy
  inside CrewAI agents (cultural mismatch — "prompt as config" vs "prompt as
  compiled artifact") `dspy-sop · R5`. Mixed same-layer adoption is "usually a
  smell."
- **AP-4 — Visual-builder past its ceiling.** Pushing a Dify/Flowise canvas past
  ~40 nodes, or demanding HITL / sub-second latency / extreme RAG from a visual
  platform that was never built for it `dify-sop · R5`. The fix is the planned
  code-escape hatch (DC-3), not more nodes.
- **AP-5 — Treating serving as an orchestration choice.** vLLM/SGLang/TGI are a
  *different layer* (L6); your LangGraph graph *calls* them through a model
  provider `langgraph-sop · R5`. Don't compare "LangGraph vs vLLM" — defer to
  `[[agentsop-llm-engine-selection]]`.
- **AP-6 — Adopting maintenance-mode tools blind.** AutoGen is in maintenance mode
  (Microsoft pivoted to its Agent Framework); OpenAI Swarm and TGI are
  experimental / maintenance `crewai-sop · R5`, `vllm-sop · R5`. Adoption-risk is
  a first-class selection criterion, not a footnote.

**Boundary — disagreements this skill does NOT resolve** (surfaced honestly per
`phase-b · open-questions`): the graph-vs-role crossover point (DC-1); Dify's
specific node-count thresholds (DC-3, Dify-specific, uncorroborated);
embeddings-vs-repo-map for code (OP-3 — likely "repo-map for code, embeddings for
prose," but no single SOP states it); and whether JSON-tool-calls degrade
*non-code* structured outputs (Aider's finding is code-specific — do not
over-generalize).

---

## 7. 跨框架对照 (Cross-Framework Layered Map)

The full layered map — which framework owns which layer, with interop notes:

| Layer | Primary owner(s) | Reach-past when… | Interop |
|---|---|---|---|
| **L1 Modeling / compile** | DSPy `dspy-sop · R5` | grammar guarantees → Outlines/Guidance; single rapid call → raw | Additive into L2 (synthesizer) & L3 (in-node). Awkward with LangChain/CrewAI prompts (same-layer). |
| **L2 Retrieval** | LlamaIndex `llamaindex-sop · R5` | classical IR → Haystack; hard-doc RAG → RAGFlow; **code → Aider repo-map** | Retriever exposed as a *tool* to any L3 (LangGraph/CrewAI/AutoGen). |
| **L3 Orchestration** | LangGraph (durable) / CrewAI (role) / Workflows (retrieval-native) `langgraph-sop · R5`, `crewai-sop · R5`, `llamaindex-sop · R5` | single-agent suffices → drop to baseline; debate → AutoGen (maint-mode) | Calls L2 retrievers as tools; runs L1 (DSPy) inside nodes; served by L6. Gate via `[[agentsop-agent-topology-selection]]`. |
| **L6 Serving** | vLLM (default) `vllm-sop · R5` | prefix-heavy → SGLang; NVIDIA-locked → TensorRT-LLM; CPU/edge → llama.cpp; dev → Ollama | OpenAI-compatible API; any L1/L2/L3 above calls it transparently. Defer to `[[agentsop-llm-engine-selection]]`. |
| **L7 App platform** | Dify `dify-sop · R5` | single chatbot → Flowise; export-to-Python → LangFlow; automation-first → n8n | Hosts UI/API/auth; calls a code framework (LangGraph/CrewAI) or LlamaIndex behind HTTP for depth. |
| **Coding surface** (cross) | Aider `aider-sop · R5` | VS Code approval → Cline; visual → Cursor; cross-IDE → Continue; autonomous → OpenHands | Orthogonal product; *uses* L1–L6 internally. Gate via `[[agentsop-repo-state-gating]]`. |

**Canonical additive stack (2026 consensus):** DSPy compiles the LM calls →
LlamaIndex retrieves → LangGraph orchestrates (with HITL + durable state) → vLLM
serves the open-weights model → (optionally) Dify wraps the frontend/auth. Each
piece is best-in-class on its layer and composes cleanly with the next
`dspy-sop · R5`, `llamaindex-sop · R5`, `dify-sop · R5`.

**The one-paragraph kickoff answer.** Don't ask "which framework?" — ask "which
layers does this project need, and what's the dominant difficulty on each?"
Identify layers (Pass A), pick the best tool per layer with the §4 rubrics (Pass
B), confirm they compose and that each layer actually clears the no-framework gate
(Pass C). Defer serving to `[[agentsop-llm-engine-selection]]`, multi-agent shape to
`[[agentsop-agent-topology-selection]]`, and coding-agent applicability to
`[[agentsop-repo-state-gating]]`. The frameworks are layers; you are assembling a stack,
not crowning a winner.
