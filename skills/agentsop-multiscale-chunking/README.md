# multiscale-chunking (C5 enhancement overlay)

Enhancement overlay on top of [[llamaindex]] that resolves the **chunk
paradox** in RAG over long documents: small chunks win retrieval precision but
lose context, large chunks win context but dilute embedding relevance into
"topic averages". The base LlamaIndex skill lists `DecoupleChunkScope` as one
optimization knob among many; this overlay turns that single knob into a full
recipe.

**Core flip**: decouple the embed-unit from the return-unit — *embed small for
retrieval precision, return large for generation context*.

**What it adds**
- A three-gate SOP: prove a single chunk size is insufficient (sweep) → choose a
  horizontal (sentence-window) vs vertical (auto-merging / parent-child)
  expansion strategy → measure the lift or revert.
- 7 operation models (MSC-01…07) refining LlamaIndex OP-02 / OP-05 into
  executable sub-steps.
- 2 dilemma cases: sentence-window vs auto-merging, and the chunk-size sweep
  (Uber 10-K → 1024 prose optimum; when it does *not* converge, decouple).
- Anti-patterns (the `chunk_size=4096` reflex, sentence-window without
  metadata replacement, indexing parent nodes) and boundaries (short corpora,
  hard real-time).
- Cross-framework map: LlamaIndex `AutoMergingRetriever` / `HierarchicalNodeParser`
  / `SentenceWindowNodeParser` ≈ LangChain `ParentDocumentRetriever`.

**Activate when** a chunk-size sweep has stalled (no single size wins both
faithfulness and recall) over long prose / filings / manuals / code. **Do not**
activate for short static corpora or when the sweep already converged.

**Files**
- `SKILL.md` — the overlay (7 sections).
- `references/R1-source-evidence.md` — provenance for every claim.
- `intermediate/operation_candidates.json` — machine-readable MSC ops.

This overlay does not replace [[llamaindex]]; defer to the base skill for
baseline, eval loop, hybrid search, reranking, routing, and production hardening.
