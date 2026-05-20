---
name: agentsop-multiscale-chunking
version: 0.1.0
description: >-
  Enhancement-overlay (C5) for RAG over long documents — the chunk-paradox resolution.
  Activate when a single fixed chunk size cannot satisfy both retrieval precision (small
  chunks) and generation context (large chunks): small chunks lose surrounding context,
  large chunks dilute embedding relevance into "topic averages". Encodes the core flip —
  decouple the embed-unit from the return-unit: embed small for retrieval precision, return
  large for synthesis context — and the SOP to pick a base chunk size, choose a horizontal
  (sentence-window) vs vertical (auto-merging / parent-child) expansion strategy, and
  measure the lift. Cross-links [[llamaindex]] for the full RAG SOP; this overlay supplies
  the missing "chunk-paradox-resolution" recipe that the framework docs
  (HierarchicalNodeParser, SentenceWindow) only describe in fragments. Medium-frequency for
  any RAG over long prose, manuals, filings, or codebases. Search keywords: chunk size,
  chunking strategy, parent document retriever, sentence window, small-to-big retrieval,
  hierarchical chunking, optimal chunk size.
---

# Multi-scale Chunking · C5 Enhancement Overlay

> Overlay on top of [[llamaindex]]. The base skill teaches the 5-layer RAG
> pipeline and lists `DecoupleChunkScope` as one optimization knob among many.
> This overlay zooms in on that single knob and turns it into a standalone
> recipe: **how to resolve the chunk paradox when one chunk size is provably
> not enough.** Third-person analytical view for an agent writing / reviewing
> RAG ingestion code — not an end-user tutorial.

---

## 1. 何时激活 (Activation Rules)

Activate this overlay when **all three** RAG preconditions hold and the chunk
paradox has actually surfaced:

1. The corpus is **long documents** — prose manuals, financial filings, legal
   contracts, research papers, codebases — where a single answer-bearing fact
   sits inside a larger context that the LLM needs to interpret it.
2. A **chunk-size sweep has stalled**: small chunks (128–256) win retrieval
   precision but the LLM answers from fragments; large chunks (1024–2048) give
   rich context but recall on specific queries drops because the embedding
   becomes a "topic average". The official failure-mode checklist documents
   both poles as *separate* failures — #2 (wrong chunk from too-small) and #6
   (context overflow / dilution from too-large) (cited in [[llamaindex]] R3).
3. Faithfulness or relevancy is **plateauing below target** and bumping
   `chunk_size` only moves the failure from one pole to the other.

Concrete triggers:
- "Answers are technically retrieved but the model lacks context to explain them."
- "I keep retuning chunk_size and it never wins on both faithfulness and recall."
- A reviewer sees `SentenceSplitter(chunk_size=4096)` shipped as the fix for
  "incomplete answers" (this is anti-pattern A1 in [[llamaindex]]).

Do **not** activate when:
- The corpus is short/static (<100k tokens) — prompt-stuff with caching; multi-scale chunking is over-engineering (§6).
- The chunk-size sweep *did* converge on a single winner (e.g. 1024 for prose) — pin it and stop.
- Retrieval quality is fine and the bottleneck is orchestration or synthesis.

---

## 2. 核心心智模型 (Core Mental Model)

> **Decouple the embed-unit from the return-unit. Embed small for retrieval
> precision; return large for generation context.**

The naive assumption is that the unit you index *is* the unit you feed the LLM.
That single identity is the source of the paradox: it forces one chunk size to
serve two opposing jobs.

```
NAIVE (one unit, two jobs)          MULTI-SCALE (two units, one job each)
─────────────────────────          ─────────────────────────────────────
       [ chunk ]                    embed unit  →  small  (precision job)
      /         \                          │
 embed it     feed it                   match
 (wants       (wants                       │
  small)       large)                 return unit →  large  (context job)
   ↓             ↓                          ▲
  CONFLICT — pick one,                   expand from
  lose the other                        match → parent / window
```

Three load-bearing sub-principles:

1. **A Node is a graph node, not a chunk.** In LlamaIndex a `Node` carries
   `relationships` (PREV/NEXT/PARENT/CHILD). Those links are exactly what let
   you store a small node for matching and *resolve* it to a larger node for
   return ([[llamaindex]] Principle 2). Multi-scale chunking is "build a
   chunk-graph", not "split into chunks".

2. **Two geometries of expansion.** Once embed ≠ return, you must choose *how*
   the small match expands into the large return:
   - **Horizontal** — return N adjacent sentences around the matched sentence
     (sentence-window). The expansion is *positional*.
   - **Vertical** — return the parent chunk when enough sibling children match
     (auto-merging / parent-child). The expansion is *hierarchical*.

3. **Match the geometry to the document, not to taste.** Flat narrative prose →
   horizontal. Documents with real structure (headings, sections, tables of
   contents) → vertical. This is the central dilemma case (§5.1).

The overlay's promise: this *strictly dominates* a compromise chunk size when
the sweep frontier is non-flat — you no longer average two bad sizes.

---

## 3. SOP 工作流 (Decision Protocol)

A three-gate protocol. Do **not** skip Gate 0 — multi-scale chunking is only
justified once a single chunk size has been proven insufficient.

### Gate 0 — Pick the base chunk size first (and try to stop here)

Run the canonical sweep from [[llamaindex]] OP-02 *before* reaching for any
multi-scale machinery:

```python
from llama_index.core.evaluation import (
    FaithfulnessEvaluator, RelevancyEvaluator,
)
# 1. ~20 eval QA pairs via DatasetGenerator.from_documents(docs)
# 2. sweep:
for cs in (128, 256, 512, 1024, 2048):           # overlap = 0.1–0.2 × cs
    idx = build_index(docs, chunk_size=cs, overlap=int(0.15 * cs))
    record(cs, faithfulness=eval_f(idx), relevancy=eval_r(idx), p95=latency(idx))
```

- If a **single chunk size dominates** both faithfulness and relevancy → pin it
  and **stop**. LlamaIndex's own Uber 10-K study peaked at **1024** for prose;
  code lands at **80–160** tokens (§5.2).
- If the **frontier is non-flat** (small wins precision, large wins context,
  no single winner) → proceed to Gate 1. *Do not compromise on a middle size.*

### Gate 1 — Choose the expansion strategy by document structure

| Document shape | Strategy | Geometry |
|---|---|---|
| Flat prose, no clear sectioning | **Sentence-Window** | horizontal |
| Clear hierarchy (headings, sections, ToC) | **Auto-Merging** (Hierarchical / parent-child) | vertical |
| Bursty multi-chunk relevance ("this whole section matters") | **Auto-Merging** | vertical |
| Point-fact needing surrounding paragraph | **Sentence-Window** | horizontal |
| Unknown structure / lowest setup cost | **Start Sentence-Window** | horizontal |

Set the embed-unit small (single sentence, or 128–256-token leaf) and the
return-unit large (the window, or the parent/root chunk).

### Gate 2 — Wire it and measure the lift

- **Sentence-Window**: `SentenceWindowNodeParser` **must** be paired with
  `MetadataReplacementPostProcessor` — otherwise the metadata-stuffed matched
  sentence (not the window) reaches the LLM, defeating the entire point (§6 A2).
- **Auto-Merging**: `HierarchicalNodeParser` builds leaf+parent nodes; store all
  leaves in the docstore and `AutoMergingRetriever` merges children → parent
  when ≥ threshold siblings match.
- Re-run the **same eval set** from Gate 0. Both patterns should beat naive
  top-k on faithfulness; if neither does, the bottleneck is elsewhere (revert).
- Pin the chosen parser + retriever config and the embedding-model version into
  index metadata, exactly as Gate 0's chunk size would have been pinned.

---

## 4. 操作模型 (Operation Models)

Each operation: **Trigger / Action / Output / Evidence**. These refine
[[llamaindex]] OP-02 and OP-05 into executable sub-steps.

### MSC-01 — ChunkSizeSweep
- **Trigger**: New long-doc corpus; chunk size unknown; before any multi-scale work.
- **Action**: Generate ~20 QA pairs; sweep `chunk_size ∈ {128,256,512,1024,2048}`,
  overlap = 10–20%; build one `VectorStoreIndex` per config; record
  faithfulness + relevancy + p95 latency.
- **Output**: Either a pinned single winner, OR a documented non-flat frontier
  that *authorizes* multi-scale chunking.
- **Evidence**: `llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`; [[llamaindex]] OP-02.

### MSC-02 — SentenceWindowSetup (horizontal expansion)
- **Trigger**: Flat prose; point-facts that need a surrounding paragraph; lowest setup cost wanted.
- **Action**: `SentenceWindowNodeParser(window_size=3)` to embed single
  sentences with N-neighbor windows in metadata; at query time apply
  `MetadataReplacementPostProcessor(target_metadata_key="window")` so the LLM
  receives the window, not the lone sentence.
- **Output**: Precise sentence-level matching + paragraph-level synthesis context.
- **Evidence**: `developers.llamaindex.ai` SentenceWindow / MetadataReplacement docs; [[llamaindex]] R3 Dilemma 5.

### MSC-03 — AutoMergingHierarchy (vertical expansion)
- **Trigger**: Documents with clear hierarchy; bursty multi-chunk relevance.
- **Action**: `HierarchicalNodeParser.from_defaults(chunk_sizes=[2048,512,128])`
  to build a leaf→parent→root tree; index **leaf** nodes in a
  `VectorStoreIndex`, keep all nodes in a `docstore`; retrieve with
  `AutoMergingRetriever`, which returns the parent once a configured fraction of
  its children are in the hit set.
- **Output**: Leaf-level precision that escalates to section-level context when warranted.
- **Evidence**: `developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/`; [[llamaindex]] OP-05.

### MSC-04 — WindowVsMergeChoice
- **Trigger**: Multi-scale authorized (MSC-01 non-flat) but strategy undecided.
- **Action**: Inspect document structure (Gate 1 table). Flat → MSC-02;
  structured/bursty → MSC-03; unknown → start MSC-02 (cheaper), escalate to MSC-03 if it underperforms on multi-chunk queries.
- **Output**: A strategy chosen by document shape, not by elegance.
- **Evidence**: [[llamaindex]] R3 Dilemma 5; `medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-...`.

### MSC-05 — EmbedReturnDecouple (the core flip)
- **Trigger**: Any time chunk-size tuning oscillates between precision and context.
- **Action**: Set embed-unit small, return-unit large; never let them be the
  same object once the sweep is non-flat. Verify by inspecting *what text the
  retriever actually sends to the synthesizer* (must be the large unit).
- **Output**: Pareto improvement on precision×context that no single size achieves.
- **Evidence**: [[llamaindex]] Principle 2 (Node relationships); R3 Dilemma 1 resolution.

### MSC-06 — MetadataBudgetGuard
- **Trigger**: Small embed-units (≤256 tokens) with rich metadata propagated into payload.
- **Action**: Ensure metadata never occupies >50% of the embed-unit token budget;
  strip/shorten metadata before shrinking chunks (GitHub `#12200`, `#13792`).
- **Output**: Embed-units carry signal, not mostly boilerplate metadata.
- **Evidence**: `github.com/run-llama/llama_index/issues/12200`, `#13792`; [[llamaindex]] A7.

### MSC-07 — MeasureOrRevert
- **Trigger**: Multi-scale config wired but lift unverified.
- **Action**: Re-run the Gate-0 eval set; require a measurable faithfulness lift
  over the best single chunk size; if none, **revert** to the pinned single size.
- **Output**: Evidence that the added complexity earns its keep — or its removal.
- **Evidence**: [[llamaindex]] Stage 2 (eval loop gates every change).

---

## 5. 困境决策案例 (Dilemma Cases)

### 5.1 — Sentence-Window vs Auto-Merging (which "embed-small-return-large"?)

**困境**: Both patterns implement the same core flip. They are *not*
interchangeable — choosing wrong wastes setup cost and underperforms.

**约束**:
- Sentence-Window expands **horizontally** — N adjacent sentences around the matched one.
- Auto-Merging expands **vertically** — returns the parent when ≥ threshold child chunks match.
- Sentence-Window has lower setup cost (one parser + one postprocessor).
- Auto-Merging needs a docstore holding the full node hierarchy.

**决策步骤**:
1. Documents have clear hierarchical structure (sections, headings, ToC) → **Auto-Merging**.
2. Documents are flat narrative prose → **Sentence-Window**.
3. Queries are bursty multi-chunk ("this entire section is relevant") → **Auto-Merging** escalates correctly.
4. Queries are point-fact with surrounding context needed → **Sentence-Window**.
5. Structure unknown → **start Sentence-Window** (lower setup cost), escalate if multi-chunk queries underperform.

**结果**: Both consistently beat naive top-k on faithfulness in published
comparisons. Auto-Merging is more *principled* for structured docs;
Sentence-Window is more *robust* for unstructured prose. The decision is driven
by document structure, not theoretical elegance.
(Source: [[llamaindex]] R3 Dilemma 5;
`developers.llamaindex.ai/.../auto_merging_retriever/`;
`medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-...`)

**可提取的操作**: MSC-02, MSC-03, MSC-04.

### 5.2 — Chunk-size sweep: the 1024 optimum, and when it does not converge

**困境**: At `chunk_size=256` embeddings are precise but the LLM gets fragments;
at `chunk_size=2048` context is rich but the embedding becomes a "topic
average" and recall on specific queries drops. Where to set chunk_size — and
what to do when no single value wins?

**约束**:
- Cannot test in production; need a deterministic offline answer.
- Embedding model has a fixed input window (e.g. 512 tokens for many BGE variants — over-chunking is a hard error).
- Synthesis-side token budget caps how many chunks fit downstream.
- Metadata propagated into payload makes very small chunks "all metadata" (issues `#12200`, `#13792`).

**决策步骤**:
1. Generate ~20 eval QA pairs.
2. Sweep `chunk_size ∈ {128,256,512,1024,2048}`, overlap 10–20%.
3. Build a `VectorStoreIndex` per config; record faithfulness + relevancy + latency.
4. Single winner → pin it.
5. **Non-flat frontier → do not compromise**; switch to embed-small/return-large via Sentence-Window or Auto-Merging.

**结果**: LlamaIndex's own published evaluation on **Uber's 10-K** found
faithfulness peaked at chunk_size **1024** and relevancy maxed at **1024**,
with only mild latency growth — so **1024 became the framework default for
prose** (code lands at 80–160 tokens). But on corpora where the curve does not
converge, the multi-scale decoupling pattern wins; never average two bad chunk
sizes into one mediocre one.
(Source: [[llamaindex]] R3 Dilemma 1;
`llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`;
`statsig.com/perspectives/llamaindex-rag-retrieval`)

**可提取的操作**: MSC-01, MSC-05, MSC-06.

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Anti-patterns

| # | Anti-pattern | Correct move |
|---|---|---|
| A1 | Bump `chunk_size` (e.g. → 4096) when answers feel incomplete | Decouple embed-scope from return-scope (MSC-02/03); do not enlarge the embed-unit |
| A2 | Use `SentenceWindowNodeParser` without `MetadataReplacementPostProcessor` | Always pair them — else the lone sentence, not the window, reaches the LLM |
| A3 | Index *parent* nodes in the vector store for auto-merging | Index **leaf** nodes; keep parents in the docstore for merge-on-retrieval |
| A4 | Pick a single compromise chunk size on a non-flat frontier | Refuse the compromise; switch to multi-scale (MSC-05) |
| A5 | Reach for multi-scale chunking on a short/static corpus | Prompt-stuff with caching; multi-scale is over-engineering (B1) |
| A6 | Ship multi-scale config without re-running the eval set | MSC-07: measure the lift or revert |
| A7 | Shrink the embed-unit while metadata still dominates the payload | MSC-06: budget metadata <50% before shrinking |

### Boundaries — when **not** to use multi-scale chunking

- **B1 — Short / static corpus (<100k tokens)**: prompt-stuff with caching; the
  chunk paradox does not arise. (Mirrors [[llamaindex]] B1.)
- **B2 — Sweep already converged**: a single chunk size won both metrics → pin
  it and stop; multi-scale adds complexity with no payoff.
- **B3 — Bottleneck is elsewhere**: if faithfulness is limited by the embedding
  model, the reranker, or the synthesizer (lost-in-the-middle), fix that first —
  multi-scale chunking only resolves the *precision-vs-context* axis.
- **B4 — Hard real-time (<100ms) retrieval**: auto-merging's docstore lookups
  and window expansion add latency; a raw vector store may be the right tool.

### PR-review smells (instant red flags)

- `SentenceSplitter(chunk_size=4096)` introduced as a fix for "incomplete answers" → A1.
- `SentenceWindowNodeParser` present but no `MetadataReplacementPostProcessor` in the query engine → A2.
- `AutoMergingRetriever` over an index built from parent nodes (no leaf docstore) → A3.
- Multi-scale parser added with no eval-set delta in the PR description → A6.

---

## 7. 跨框架对照 (Cross-framework Mapping)

The "embed small, return large" pattern is framework-agnostic; the primitives differ.

| Concept | LlamaIndex | LangChain | Notes |
|---|---|---|---|
| Horizontal (sentence-window) | `SentenceWindowNodeParser` + `MetadataReplacementPostProcessor` | (no direct equivalent; emulate with custom retriever returning neighbor windows) | LlamaIndex's is the cleanest first-class implementation |
| Vertical (parent-child / auto-merging) | `HierarchicalNodeParser` + `AutoMergingRetriever` | `ParentDocumentRetriever` (child splitter + parent splitter + docstore) | Same idea: embed children, return parents |
| Small-embed unit store | `VectorStoreIndex` over leaf nodes | child vectorstore | both index the small unit |
| Large-return unit store | `docstore` (nodes with PARENT/CHILD relationships) | `InMemoryStore` / byte-store for parent docs | the return-unit lives outside the vector index |

**Mapping rule**: LlamaIndex `AutoMergingRetriever`/`HierarchicalNodeParser` ≈
LangChain `ParentDocumentRetriever`. LlamaIndex additionally offers the
horizontal `SentenceWindowNodeParser`, which LangChain has no first-class
analogue for. For a coder agent already inside the LlamaIndex stack, prefer the
native parsers; the [[llamaindex]] base skill governs the surrounding pipeline
(ingestion, eval loop, reranking, routing).

> This overlay does not replace [[llamaindex]] — it deepens the single
> `DecoupleChunkScope` knob into a full recipe. For everything around it
> (baseline, eval, hybrid, rerank, routing, production hardening), defer to the
> base skill.

---

## References

- `references/R1-source-evidence.md` — citations and provenance for every claim above.
- `intermediate/operation_candidates.json` — machine-readable MSC operation list.
- Base skill: [[llamaindex]] (`SKILL.md` + `references/R3-dilemma-cases.md` Dilemmas 1 & 5).

### Primary sources (cited inline)

- `llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5` (Uber 10-K, 1024 optimum)
- `developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/`
- `developers.llamaindex.ai` SentenceWindowNodeParser / MetadataReplacementPostProcessor / HierarchicalNodeParser docs
- `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/` (failures #2, #6)
- `medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-with-llamaindex-f778173bed98`
- `statsig.com/perspectives/llamaindex-rag-retrieval` (code chunk size 80–160)
- `github.com/run-llama/llama_index/issues/12200`, `#13792` (metadata-dominates-chunk)
- LangChain `ParentDocumentRetriever` docs (`python.langchain.com/docs/how_to/parent_document_retriever/`)
