# R1 — Source Evidence

Every load-bearing claim in `SKILL.md` resolved to its source. Primary source is
the `[[llamaindex]]` SKILL at
`/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`
(line numbers below), plus its frontmatter at `~/.claude/skills/llamaindex/SKILL.md`.
External claims are grounded on the named search topics; verify model names /
API versions quarterly.

## A — Claims sourced from the llamaindex SKILL

| SKILL claim | Source (llamaindex-sop-skill/SKILL.md) |
|---|---|
| Reranker triggers on "top-1 wrong but relevant docs appear in top-k (failure #1/#10)" | `OP-03 AddReranker`, Trigger — line 191 |
| "widen retrieval top_k to 20-50, narrow to top_n=3-5 after rerank" | `OP-03`, Action — line 192; Stage 3 step 7 — line 138 |
| "Faithfulness lift typically 5-15pp on noisy corpora; lower context-window pressure" | `OP-03`, Output — line 193 |
| CohereRerank / SentenceTransformerRerank / ColBERT named as reranker models | Stage 3 step 7 — line 138; `OP-03` — line 192 |
| "prompts first, reranking last … high-impact but expensive — exhaust cheap knobs first" (order law) | Stage 3 note — line 140 |
| Optimization order: prompt → embed → chunk → hybrid → metadata → decouple → rerank | Stage 3 list — lines 132-138 |
| Reranking is the LAST step in the recommended optimization order | Stage 3 step 7 (#7 of 7) — line 138 |
| A6 anti-pattern: "Naive top_k=N, no reranker" → widen + add reranker | Anti-pattern table A6 — line 351 |
| PR smell: `as_query_engine(similarity_top_k=20)` without a rerank postprocessor | PR-review smells — line 368 |
| Eval loop must precede optimization; gate every change on {MRR, faithfulness, relevancy, p95} | Stage 2 — lines 114-124; `OP-10 EvalLoop` — lines 232-236 |
| hit-rate / MRR as the retrieval-quality metrics | Stage 2 — line 124; `OP-10` — line 234 |
| "Most RAG failures trace to weak retrieval or sloppy ingestion — not the LLM" | Stage 2 note — line 126 |
| Hybrid (BM25 + dense) as the recall stage; lexical-identity queries | `OP-04 AddHybridBM25` — lines 196-200; Dilemma 2 — lines 273-288 |
| Dense embeddings "destroy lexical identity by pooling token representations" (bi-encoder lossiness) | Dilemma 2 约束 — lines 277-278 |
| "lost in the middle" degrades quality — motivates fewer, better chunks | Dilemma 4 约束 — line 314; Stage 5 (`tree_summarize`) — line 158 |
| Long context does not replace RAG; rerank + position-aware synthesis matter MORE | Dilemma 4 结果 — lines 322-324 |
| Sweep-and-pin discipline (applied here to N/k) | `OP-02 TuneChunkSize` — lines 184-188; Dilemma 1 — lines 256-271 |
| B1 boundary: tiny static corpus → prompt-stuff, no retrieval to rerank | Boundaries B1 — line 359 |
| Pin tuned constants once; forbid inline drift | `OP-11 LockGlobalSettings` — lines 238-242 (discipline analogue) |

## B — Claims sourced from llamaindex frontmatter

`~/.claude/skills/llamaindex/SKILL.md`

| SKILL claim | Source |
|---|---|
| LlamaIndex is the data framework for RAG / document Q&A / knowledge retrieval | description — "Data framework for building LLM applications with RAG" |
| Vector indices + query engines are the retrieval substrate the reranker sits on | description — "Features vector indices, query engines, agents" |

## C — External claims (grounding topics; verify quarterly)

These are general, well-established facts about rerankers, grounded on the search
topics named in the task brief. They do not depend on any single fabricated API.

| SKILL claim | Grounding topic | Note |
|---|---|---|
| A bi-encoder embeds query and document separately/offline; similarity is a dot product of vectors that never met (fast, lossy) | "cross-encoder rerank RAG" | Standard IR two-tower vs cross-encoder distinction |
| A cross-encoder scores `[query, document]` as a joint input with full attention; accurate but cannot be precomputed → runs per (query, candidate) at query time | "cross-encoder rerank RAG" | Why rerank only a small N is feasible |
| Cohere Rerank: hosted cross-encoder API, multilingual, per-search billing; `rerank-v3.5` | "cohere rerank" | Verify current model id |
| Voyage rerank: hosted API (`rerank-2`), pairs with Voyage embeddings | "cohere rerank" / vendor docs | Verify current model id |
| bge-reranker: BAAI open-weights local cross-encoder (`bge-reranker-v2-m3`, `-large`), strong multilingual, GPU-recommended, no per-call fee | "bge-reranker" | Verify current checkpoint |
| SentenceTransformers cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) — light, CPU-viable for small N | "cross-encoder rerank RAG" | Lowest-dependency local option |
| ColBERT / late-interaction: token-level scoring, precomputable, scales to larger N than a full cross-encoder | "cross-encoder rerank RAG" | Middle ground vs full cross-encoder |
| Latency scales with N (number of candidates reranked), not k | "cross-encoder rerank RAG" | Cross-encoder cost is per-pair |

## D — Cross-framework mapping evidence

| Mapping row | Source / grounding |
|---|---|
| LlamaIndex node postprocessors (`CohereRerank`, `SentenceTransformerRerank`, `ColbertRerank`, `LLMRerank`) | [[llamaindex]] `OP-03`, Stage 3 step 7 |
| LangChain `ContextualCompressionRetriever` + `CohereRerank` / `CrossEncoderReranker` | "cross-encoder rerank RAG" (LangChain docs pattern) |
| Cohere / Voyage rerank API signatures | "cohere rerank" |
| bge-reranker via `FlagReranker` / `sentence-transformers` `CrossEncoder` | "bge-reranker" |
| Haystack `TransformersSimilarityRanker` / `CohereRanker` | "cross-encoder rerank RAG" (Haystack ranker components) |

## Verification status

- **A / B** — fully traceable to source SKILL line numbers above. No fabrication.
- **C / D** — established reranker facts grounded on the named search topics.
  Model identifiers and API versions are time-sensitive (May 2026); re-verify
  `rerank-v3.5`, `rerank-2`, `bge-reranker-v2-m3` against current vendor docs
  before relying on exact names.
