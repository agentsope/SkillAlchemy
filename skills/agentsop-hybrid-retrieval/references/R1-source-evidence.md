# R1 · Source Evidence & Extraction Provenance

This overlay (`hybrid-retrieval`, v0.1.0) is extracted from the `llamaindex` SOP skill.
It standalone-izes the "when corpus has identifiers, add BM25" recipe that is otherwise
buried inside the parent skill's optimization ladder. Every claim below traces to a
cited source line in the parent material.

## Primary extraction targets

| Parent location | What was extracted |
|---|---|
| `llamaindex-sop-skill/SKILL.md` Stage 3, step 4 ("Hybrid search (BM25 + dense) — *only if traffic contains lexical-identity queries*") | The Stage-0 "decide if corpus needs sparse" gate and the traffic-driven framing. |
| `llamaindex-sop-skill/SKILL.md` OP-04 AddHybridBM25 | OP-01/OP-03/OP-04/OP-05/OP-07: trigger (exact identifiers, error codes, SKUs, code symbols, rare jargon), `QueryFusionRetriever([vector, BM25])` or vendor hybrid, "tune alpha per query type, not globally". |
| `llamaindex-sop-skill/references/R3-dilemma-cases.md` Dilemma 2 ("Hybrid BM25+dense vs pure dense — is the complexity worth it?") | This overlay's Dilemma 1 (verbatim decision steps + result) and Dilemma 2 (alpha per query type). The lexical-share thresholds (<5% / 5-50% / >50%) come straight from R3 决策步骤 lines 56-59. |
| `~/.claude/skills/llamaindex/SKILL.md` frontmatter | Frontmatter style/voice; `description` block format. |

## Verbatim source quotes (load-bearing)

1. **Dense destroys lexical identity** (R3 Dilemma 2 约束, line 49; SKILL line 436 source):
   > "Dense embedding models destroy lexical identity by pooling token representations,
   > so when querying specific error strings, the resulting vector captures something
   > like 'document about SSL errors' rather than 'document containing this specific
   > error string'. BM25 scores against an inverted index of exact tokens."
   > — `tianpan.co/blog/2026-04-12-hybrid-search-production-bm25-dense-embeddings`

   → Mental Model Principle 1.

2. **Traffic-driven, not theoretical** (R3 Dilemma 2 可提取的操作, lines 65-67):
   > "`OP-04 AddHybridBM25`: trigger is **traffic-driven** (presence of lexical-identity
   > queries), not theoretical. Tune alpha per query type, not globally — otherwise
   > hybrid can underperform dense. For very lexical corpora (code, logs), invert the
   > default: BM25 first, dense as reranker signal."

   → Mental Model Principle 2 + 3; OP-01, OP-05, OP-07.

3. **Per-type alpha or hybrid loses to dense** (R3 Dilemma 2 结果, line 62):
   > "A flat global alpha often loses to pure dense on semantic queries, which is why
   > teams sometimes wrongly conclude 'hybrid didn't help'."

   → Principle 3; Dilemma 2; anti-pattern A2/A5; the Stage-3 gate.

4. **Lexical-share decision ladder** (R3 Dilemma 2 决策步骤, lines 56-59):
   > "If lexical share is <5% → dense-only is fine; skip hybrid. If 5-50% → add hybrid
   > via `QueryFusionRetriever([vector_retriever, BM25Retriever])` or vendor hybrid
   > (Qdrant, Milvus, Weaviate) with alpha tuning. If >50% (legal citations, code
   > search, log search) → consider BM25-first with dense as a fallback rerank signal."

   → Stage 0; OP-01; OP-07; both Dilemmas.

5. **Alpha semantics + sweep grid** (R3 Dilemma 2 约束 line 52; 决策步骤 line 59):
   > "Alpha tuning (`alpha=0` → pure BM25, `alpha=1` → pure dense) is a per-query-type
   > hyperparameter; one alpha rarely fits all… Evaluate alpha at `{0.0, 0.25, 0.5,
   > 0.75, 1.0}` on a labeled subset of each query type; tune per type, not globally."

   → Stage 3; OP-05; Dilemma 2.

6. **Hybrid is a Stage-3 optimization, not a starting point** (SKILL Stage 3, line 136):
   > "4. **Hybrid search** (BM25 + dense) — *only if traffic contains lexical-identity
   > queries*… Note the order: prompts first, reranking last."

   → when_not_to_use; boundary B2; Stage 0 preamble.

## Net-new material (not in parent, added for standalone completeness)

The parent skill names `QueryFusionRetriever` and "vendor hybrid" but does not detail
the fusion mechanics. This overlay adds, with independent citation:

- **RRF vs weighted fusion** (OP-02; §7.3): RRF is rank-based and score-scale-robust;
  weighted fusion needs normalization. Citation: Cormack, Clarke, Büttcher (2009),
  *Reciprocal Rank Fusion outperforms Condorcet and individual rank learning methods*.
- **Native-hybrid preference** (OP-04; §7.4): Qdrant `FusionQuery`/`Prefetch`, Weaviate
  `hybrid(alpha=)`, Pinecone sparse-dense, pgvector full-text, Milvus rankers. These
  generalize the parent's "vendor (Qdrant/Milvus alpha)" mention. Weaviate's literal
  `alpha` parameter is the concrete instance the LlamaIndex alpha-tuning blog abstracts.
- **LangChain `EnsembleRetriever`** (§7.2): the cross-framework analogue requested by
  the task; uses RRF with per-retriever `weights` as the alpha analogue.
- **Per-leg candidate headroom** (OP-03; A6): retrieve wide per leg, narrow after
  fusion — standard hybrid practice, made explicit because the parent skill does not.

## Cross-link rationale

- `[[llamaindex]]` — parent SOP; canonical home of the eval loop, optimization ladder,
  and Dilemma 2. This overlay defers all baseline/eval/chunking concerns to it.
- `[[langchain]]` — `EnsembleRetriever` cross-framework equivalent.
- `[[agentsop-query-routing]]` — the mechanism that applies per-type alpha (OP-06) when no single
  global alpha works; the two skills compose.

## Source files (paths)

- `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`
- `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/references/R3-dilemma-cases.md`
- `~/.claude/skills/llamaindex/SKILL.md`
