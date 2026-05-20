# hybrid-retrieval — Enhancement Overlay (C3)

Standalone "when corpus has identifiers, add BM25" recipe, extracted from the
`llamaindex` SOP skill where hybrid search lives buried inside the optimization ladder
(Stage 3, step 4) and Dilemma 2.

## What this skill answers

> My retriever uses embeddings. Users paste an exact code / SKU / function name and get
> the wrong document — or nothing. Should I add BM25? How do I fuse it, and what `alpha`?

## One-sentence model

Dense captures meaning, sparse captures exact tokens; **hybrid wins when both matter** —
but only fuse when traffic actually carries exact-match queries, and **tune the blend
per query type or hybrid loses to dense**.

## When it fires

- Corpus has exact-match tokens: identifiers, error codes, SKUs, API/function names,
  proper nouns, citations, rare jargon.
- "I searched the exact string and got nothing" bug reports on a dense-only retriever.
- Tuning recall where both meaning and exact strings matter.

## When it does NOT fire

- Purely semantic traffic (<5% lexical-identity queries) — dense-only.
- No dense baseline + eval loop yet — baseline first (see `[[llamaindex]]`).
- The problem is chunking / embedding-model / reranking, not recall of exact tokens.

## The decision ladder (traffic-driven)

| Lexical share of traffic | Move |
|---|---|
| `< 5%` | Dense-only. Skip hybrid. |
| `5–50%` | Add hybrid (BM25 + dense), fuse, tune alpha **per query type**. |
| `> 50%` (code, logs, legal) | Invert: BM25-first, dense as rerank signal. |

## Files

- `SKILL.md` — 7-section operating model (activation / mental model / SOP / 8 ops /
  2 dilemmas / anti-patterns / cross-framework table).
- `references/R1-source-evidence.md` — extraction provenance from `[[llamaindex]]`.
- `intermediate/operation_candidates.json` — machine-readable operations + dilemmas.

## Cross-links

- `[[llamaindex]]` — parent RAG SOP (baseline, eval loop, optimization ladder, Dilemma 2).
- `[[langchain]]` — `EnsembleRetriever` equivalent.
- `[[agentsop-query-routing]]` — applies per-type alpha when no single global alpha works.

Overlay · v0.1.0 · Phase D enhance.
