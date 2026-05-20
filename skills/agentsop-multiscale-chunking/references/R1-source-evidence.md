# R1 · Source Evidence — multiscale-chunking (C5)

Provenance for every load-bearing claim in `SKILL.md`. This overlay distills the
chunk-paradox resolution from the [[llamaindex]] base skill (its R3 Dilemmas 1
and 5) plus the framework's own docs and published evaluations. No hypothetical
claims; every assertion traces to a cited source.

---

## Core flip — embed small, return large

> "When no single chunk_size dominates, do not pick a compromise — instead
> decouple embed-scope from synthesis-scope by switching to
> `HierarchicalNodeParser + AutoMergingRetriever` or `SentenceWindowNodeParser`.
> Embed small (e.g. 128-256), return large (e.g. 1024-2048)."
> — [[llamaindex]] `references/R3-dilemma-cases.md`, Dilemma 1, 决策步骤 step 5.

This is the same primitive LlamaIndex calls **"Small-to-Big"** in its
long-context RAG patterns ([[llamaindex]] R3 Dilemma 4: "Small-to-Big: embed
small, send large — exactly the same primitive as Dilemma 1's resolution").

The "Node is a graph node, not a chunk" foundation (PREV/NEXT/PARENT/CHILD
relationships enabling small-match → large-return) is [[llamaindex]] Core
Mental Model Principle 2.

---

## Chunk-size sweep & the 1024 optimum (Dilemma 5.2)

- Tradeoff statement: "smaller chunks match queries more precisely but lose
  surrounding context, while larger chunks preserve relationships between ideas
  but dilute relevance in embeddings."
  — quoted in [[llamaindex]] R3 Dilemma 1, attributed to
  `medium.com/@sayantanmanna840/rag-chunking-strategies-...`.

- **Uber 10-K, 1024 optimum**: "LlamaIndex's own published evaluation on Uber's
  10-K: faithfulness peaked at chunk_size 1024, relevancy maxed at 1024,
  response time grew only mildly. 1024 became the framework default for prose."
  — [[llamaindex]] R3 Dilemma 1, 结果; primary source
  `llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`.

- **Code chunk size 80–160 tokens**: `statsig.com/perspectives/llamaindex-rag-retrieval`
  (cited [[llamaindex]] R3 Dilemma 1 and OP-02).

- **Two failure poles**: "The official failure-mode checklist documents both
  poles as separate failures (#2: wrong chunk selection from too-small; #6:
  context-window overflow from too-large)."
  — [[llamaindex]] R3 Dilemma 1; `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/`.

- **Embedding input window constraint** (512 tokens for many BGE variants —
  over-chunking is a hard error): [[llamaindex]] R3 Dilemma 1, 约束.

- **Metadata-dominates-chunk constraint**: "Metadata is propagated into each
  chunk's payload, so very small chunks become 'all metadata'" —
  GitHub `run-llama/llama_index#12200`, `#13792` (cited [[llamaindex]] R3
  Dilemma 1 and A7). Drives MSC-06 (metadata budget <50%).

- **Sweep method** (~20 QA pairs, `{128,256,512,1024,2048}`, overlap 10–20%,
  `FaithfulnessEvaluator` + `RelevancyEvaluator` + latency): [[llamaindex]]
  R3 Dilemma 1, 决策步骤; [[llamaindex]] OP-02 / Stage 3.

---

## Sentence-Window vs Auto-Merging (Dilemma 5.1)

Directly distilled from [[llamaindex]] `references/R3-dilemma-cases.md`,
Dilemma 5 ("Sentence-window vs auto-merging — which 'small-embed-large-return'
pattern?"):

- Both implement "embed small, return large" and are *not* interchangeable.
- **Horizontal vs vertical expansion**: "Sentence-Window expands horizontally
  (returns N adjacent sentences around the matched sentence). Auto-Merging
  expands vertically (returns the parent chunk when ≥ threshold child chunks
  match)." — [[llamaindex]] R3 Dilemma 5, 约束.
- **Decision by document structure**: clear hierarchy → Auto-Merging; flat prose
  → Sentence-Window; bursty multi-chunk → Auto-Merging; point-fact + surrounding
  context → Sentence-Window. — [[llamaindex]] R3 Dilemma 5, 决策步骤.
- **Result**: "Both consistently beat naive top-k chunk retrieval on
  faithfulness in published comparisons. Auto-Merging is more 'principled' for
  structured docs, Sentence-Window is more 'robust' for unstructured prose. A
  team that doesn't know their doc structure should start with Sentence-Window
  (lower setup cost)." — [[llamaindex]] R3 Dilemma 5, 结果.
- **Mandatory pairing**: "Always pair `SentenceWindowNodeParser` with
  `MetadataReplacementPostProcessor` — otherwise the metadata-stuffed sentence
  is what reaches the LLM, defeating the point." — [[llamaindex]] R3 Dilemma 5,
  可提取的操作 (drives A2 and MSC-02).

Primary sources (from [[llamaindex]] R3 Sources):
- `developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/`
- `medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-with-llamaindex-f778173bed98`

---

## Auto-merging mechanics (index leaves, store parents)

`HierarchicalNodeParser` builds leaf+parent+root nodes; the leaf nodes are
embedded in a `VectorStoreIndex` while the full hierarchy lives in a `docstore`;
`AutoMergingRetriever` returns the parent when a configured fraction of its
children appear in the hit set.
— `developers.llamaindex.ai/.../auto_merging_retriever/`; [[llamaindex]]
OP-05 ("`HierarchicalNodeParser` + `AutoMergingRetriever` ... Embed small,
return large"). Drives MSC-03 and anti-pattern A3 (do not index parent nodes).

---

## Anti-pattern A1 (the chunk_size=4096 reflex)

[[llamaindex]] A1: "Bump chunk_size when answers feel incomplete → Decouple
embed-scope from synthesis-scope (Hierarchical / SentenceWindow)." Also a PR
smell in [[llamaindex]]: "`SentenceSplitter(chunk_size=4096)` → likely A1."

---

## Boundaries

- **B1 short/static corpus**: [[llamaindex]] B1 ("Tiny static corpus (<100k
  tokens) → prompt-stuff with caching"). Multi-scale chunking presupposes long
  documents; on short corpora the paradox does not arise.
- **B4 hard real-time**: [[llamaindex]] B3 (hard real-time / sub-100ms →
  raw vector store). Auto-merging's docstore lookups add latency.
- Over-engineering boundary (don't multi-scale when the sweep converged): direct
  corollary of [[llamaindex]] OP-02 ("If a single winner emerges → pin it").

---

## Cross-framework mapping

- LlamaIndex `SentenceWindowNodeParser` + `MetadataReplacementPostProcessor`
  (horizontal); `HierarchicalNodeParser` + `AutoMergingRetriever` (vertical) —
  `developers.llamaindex.ai`.
- LangChain `ParentDocumentRetriever` (child splitter + parent splitter +
  docstore) is the vertical / parent-child analogue —
  `python.langchain.com/docs/how_to/parent_document_retriever/`. LangChain has
  no first-class horizontal sentence-window primitive.

---

## Source list

1. `llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5`
2. `developers.llamaindex.ai/python/framework/integrations/retrievers/auto_merging_retriever/`
3. `developers.llamaindex.ai` — SentenceWindowNodeParser / MetadataReplacementPostProcessor / HierarchicalNodeParser
4. `developers.llamaindex.ai/python/framework/optimizing/rag_failure_mode_checklist/` (#2, #6)
5. `medium.com/@harsh_77214/beyond-naive-rag-comparing-basic-sentence-window-and-auto-merging-retrieval-with-llamaindex-f778173bed98`
6. `statsig.com/perspectives/llamaindex-rag-retrieval`
7. `github.com/run-llama/llama_index/issues/12200`, `#13792`
8. `python.langchain.com/docs/how_to/parent_document_retriever/`
9. Base skill [[llamaindex]] — `SKILL.md`, `references/R3-dilemma-cases.md` (Dilemmas 1 & 5)
