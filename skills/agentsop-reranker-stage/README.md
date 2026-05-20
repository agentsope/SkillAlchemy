# reranker-stage skill

Cross-framework **enhancement overlay** for the **reranker stage** of a RAG
pipeline — the "**retrieve wide, rerank narrow**" discipline. A cheap bi-encoder
retrieves a wide candidate pool (top-50) for recall; an expensive cross-encoder
that reads query + document *together* reranks it down to a narrow, high-precision
tail (top-5) for the LLM.

This is the **C4 gap skill** in the Phase-D enhance pass. The reranker SOP
existed only buried inside the `[[llamaindex]]` skill (`OP-03 AddReranker`,
Stage 3 step 7, anti-pattern A6). Because it is the **highest-ROI single
addition** to a naive RAG pipeline, it earns a standalone overlay.

## Scope

- **Activation**: a RAG pipeline whose quality has plateaued, the relevant doc
  is in top-k but buried (high hit-rate, low MRR), or the context window is
  pressured by too many marginal chunks.
- **Core insight**: *retrieve wide for recall (bi-encoder), rerank narrow for
  precision (cross-encoder that sees query + doc together).*
- **Date stamp**: May 2026. Re-verify rerank model names / API versions each
  quarter (Cohere rerank-v3.5, Voyage rerank-2, bge-reranker-v2-m3).

## Layout

```
d-reranker-stage-skill/
├── SKILL.md                          # 7-section SOP (activation → cross-framework table)
├── README.md                         # this file
├── references/
│   └── R1-source-evidence.md         # every cited claim resolved to a source line
└── intermediate/
    └── operation_candidates.json     # raw trigger/action/output/evidence operations
```

## Key claim

> A bi-encoder embeds query and document *separately and offline* — fast but
> lossy. A cross-encoder scores `[query, document]` as a *joint input* with full
> attention — sharp but expensive, so it only runs on a small candidate set.
> Retrieve top-20-50 (recall), rerank to top-3-5 (precision). A reranker only
> reorders what retrieval already found, so it never fixes a recall problem.

The skill encodes: the two-stage recall→precision model, the order law
("prompts first, reranking last"), 7 operations, 2 dilemma cases (rerank latency
vs quality; API reranker cost vs local model), 8 anti-patterns + 4 boundaries,
and the cross-framework mapping (LlamaIndex node postprocessors, LangChain
`ContextualCompressionRetriever`, Cohere/Voyage rerank APIs, bge / cross-encoder
/ ColBERT local models, Haystack rankers).

## ENHANCE overlay

This skill is an **overlay**, not a replacement. For the per-framework API it
cross-links the base skills inline as `[[name]]`:

- `[[llamaindex]]` — node postprocessors (`CohereRerank`,
  `SentenceTransformerRerank`, `ColbertRerank`, `LLMRerank`), `similarity_top_k`
  + `top_n` wiring, the canonical reranker SOP.
- `[[agentsop-hybrid-retrieval]]` — the wide/recall stage (BM25 + dense) that feeds the
  reranker its candidate pool; lexical-identity recall.

Activate this skill for the *reranking decision* (whether / where / how wide /
which model / what it costs); descend to the base skill for the API surface.

## Method

Mined primarily from the `[[llamaindex]]` source SKILL under
`/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/`, plus the
`llamaindex` frontmatter at `~/.claude/skills/llamaindex/`, with external grounding
on "cohere rerank", "bge-reranker", and "cross-encoder rerank RAG". Every
load-bearing claim carries an inline `[[source]]` tag and resolves in
`references/R1-source-evidence.md`. No fabricated APIs.

## Position in the Phase-D inventory

- **Sibling overlays**: `d-query-routing-skill` (route by query *kind* before
  retrieval), `d-multi-tenant-rag-skill` (filter by *who*), and a forthcoming
  `hybrid-retrieval` overlay (the recall stage).
- **Boundary vs `hybrid-retrieval`**: hybrid maximizes *recall into* the
  candidate pool (right doc is present); reranking maximizes *precision out of*
  it (right doc ranked first). They **compose** — hybrid then rerank
  (SKILL `OP-06 RerankAfterHybrid`).
- **Boundary vs query-routing**: routing picks *which retriever* runs; reranking
  reorders *what one retriever returned*. Orthogonal stages.
