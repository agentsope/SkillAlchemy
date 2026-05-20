# R2 — LLM-as-Judge Bias Catalog + Mitigations

Companion to `SKILL.md` §2 ("Why holistic judges fail") and Stage 4 (Bias Test).
Each bias: what it does → why it corrupts an optimizer target → how to detect it
→ how to mitigate it (mapped to a SKILL.md operation).

Sources: [arxiv.org/pdf/2506.02592], [arxiv.org/pdf/2509.26072]; cross-confirmed
by the dspy-sop Case C and metric table
(`/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`):

> "Refuse to ship a single-LLM-judge as the optimization metric. Document
> evidence: LLM judges exhibit self-preference, recency, rubric-order, and
> provenance biases [arxiv.org/pdf/2506.02592, arxiv.org/pdf/2509.26072]."
> — dspy-sop Case C step 1

> "LLM-as-judge … Watch for self-preference bias, recency bias, score-ID bias
> [arxiv.org/pdf/2509.26072]" — dspy-sop metric table

**Why this matters for metric design:** a DSPy/GEPA/MIPRO optimizer maximizes
`metric(pred, example)`. Any bias in the judge becomes a reward signal the
optimizer faithfully chases. The biases below are systematic and reproducible,
so they do not "average out" across a dataset — they shift the compiled program.

---

## 1. Length / Verbosity bias

- **What it does:** the judge assigns higher scores to longer answers regardless
  of substantive quality. dspy-sop Case C: "judges over-prefer length".
- **Optimizer harm:** the compiled prompt learns to pad. See SKILL.md Dilemma 1
  (MIPRO score climbed 0.62→0.84 while producing over-long, sometimes wrong
  answers; judge gave +0.18 to answers >120 words).
- **Detect (Stage 4 length probe):** take 10 good answers, append a redundant
  paragraph; if the metric scores them *higher* the penalty is too weak. Reject
  if padded answers gain ≥+5pp. Also: bin answers by length, plot judge-score vs
  length, look for a monotonic positive slope.
- **Mitigate:** never delegate length to the judge. Use a **deterministic scalar
  penalty** `length_score = clip(1 - max(0, len - budget)/budget, 0, 1)`
  multiplied into the float. → **OP-M03 ExplicitLengthPenalty**; anti-patterns
  AP-2, AP-7.
- **Source:** [arxiv.org/pdf/2506.02592]; dspy-sop Case C step 6.

## 2. Self-preference (family / provenance) bias

- **What it does:** a judge from model family X scores outputs from family X
  higher; more broadly, knowing the *source* of an answer biases the rating
  ("provenance bias").
- **Optimizer harm:** if judge and task model share a family, the score is
  inflated 5–15pp (SKILL.md AP-3) and the optimizer is rewarded for matching the
  judge's house style rather than the task.
- **Detect (Stage 4 self-preference probe):** generate the same answer from two
  model families; if the judge prefers its own family by >10pp, swap the judge.
- **Mitigate:** use a **different / cheaper family** for the judge than the task
  model (e.g. task = GPT-4o, judge = Claude-Haiku). Strip provenance from the
  text shown to the judge. → **OP-M04 CrossFamilyJudge**; AP-3.
- **Source:** [arxiv.org/pdf/2506.02592].

## 3. Positional / Recency bias (pairwise)

- **What it does:** in a pairwise comparison the option presented last (or in a
  fixed slot) is rated higher independent of content. dspy-sop calls this
  "recency bias".
- **Optimizer harm:** any pairwise reward channel becomes order-dependent noise;
  the optimizer can win by exploiting position rather than quality.
- **Detect (Stage 4 position probe):** swap A/B order; if the winner flips >10%
  of the time, position bias is material.
- **Mitigate:** randomize A/B order per call, or **run both orderings and
  average** the result. → **OP-M09 RandomizeJudgeOrder**.
- **Source:** [arxiv.org/pdf/2509.26072]; dspy-sop metric table.

## 4. Rubric-order bias

- **What it does:** criteria listed first in a multi-criterion rubric are
  weighted more heavily by the judge than criteria listed later.
- **Optimizer harm:** aggregate score depends on the incidental ordering of
  sub-judges, not just their values — a hidden, unintended weighting.
- **Detect (Stage 4 rubric-order probe):** list the sub-judges in two different
  orders; if the aggregated score shifts >5pp, the order is leaking into the
  score.
- **Mitigate:** **decompose** so each sub-judge is a separate single-question
  call (removes within-prompt ordering effects), and randomize sub-judge order
  per call. → **OP-M01 DecomposeMultiCriteria** + **OP-M09 RandomizeJudgeOrder**.
- **Source:** [arxiv.org/pdf/2509.26072]; dspy-sop Case C step 1.

## 5. Score-ID / anchoring bias

- **What it does:** the numeric scale anchors the rating — "5" on a 1–5 scale and
  "10" on a 1–10 scale do not map to the same quality, and the chosen IDs shift
  the distribution across rubrics.
- **Optimizer harm:** scalar scores are not comparable across rubric versions;
  thresholds drift silently when the scale changes.
- **Detect:** re-rate the same items on two scales (e.g. 1–5 vs 1–10 normalized);
  large divergence indicates anchoring.
- **Mitigate:** prefer **binary yes/no sub-judges** (no numeric scale to anchor)
  and aggregate deterministically; if a scale is unavoidable, fix one scale and
  version it in the calibration receipt. → **OP-M01 DecomposeMultiCriteria**;
  **OP-M10 CalibrationReceipt** (pins the rubric/scale).
- **Source:** [arxiv.org/pdf/2509.26072]; dspy-sop metric table ("score-ID bias").

## 6. Hedging / non-commitment bias

- **What it does:** judges tolerate (and holistic judges sometimes reward)
  hedged, non-committal answers ("it depends", "as an AI language model…") that
  read as cautious/safe but do not answer the question. Surfaced in SKILL.md
  Dilemma 2: a synthesizer that "hedges with topic-level statements rather than
  answering the question" stayed faithful (1.0) while relevancy was 0.41.
- **Optimizer harm:** the program learns to dodge rather than commit; high
  faithfulness/safety scores mask uselessness.
- **Detect:** add an explicit "does this commit to a position?" sub-judge and
  inspect its rate on the dev set; a faithful-but-irrelevant gap (high
  faithfulness, low relevancy) is the tell.
- **Mitigate:** add a **non-hedging bool sub-judge** ("commits to a position, no
  'it depends' / 'as an AI'"), AND-gated. → **OP-M01 DecomposeMultiCriteria** +
  **OP-M06 RAGFaithfulnessRelevancyContext** (relevancy axis catches it).
- **Source:** SKILL.md §3 Stage 3 non-hedging sub-judge + Dilemma 2;
  bias framing per [arxiv.org/pdf/2506.02592].

---

## 7. Single-axis blindness (RAG-specific, not a judge bias but a metric defect)

- **What it does:** one precise metric (e.g. Faithfulness only) can read 1.0
  while the system is unusable, because it does not measure the missing axis
  (query-relevance, retrieval quality). SKILL.md Dilemma 2.
- **Mitigate:** the **triad** — `FaithfulnessEvaluator` + `RelevancyEvaluator` +
  `RetrieverEvaluator(["mrr","hit_rate"])`, gating every change.
  → **OP-M06**; AP-6.
- **Source:** LlamaIndex OP-10 EvalLoop
  [developers.llamaindex.ai/python/framework-api-reference/evaluation/].

---

## 8. Mitigation summary

| Bias | Probe (Stage 4) | Reject threshold | Mitigation op |
|---|---|---|---|
| Length / verbosity | Pad good answers | ≥+5pp on padded | OP-M03 (deterministic penalty) |
| Self-preference / provenance | Same answer, 2 families | >10pp own-family | OP-M04 (cross-family judge) |
| Positional / recency | Swap A/B order | flip >10% | OP-M09 (randomize / average orders) |
| Rubric-order | Reorder sub-judges | shift >5pp | OP-M01 + OP-M09 |
| Score-ID / anchoring | Re-rate on 2 scales | large divergence | OP-M01 (binary) + OP-M10 (pin scale) |
| Hedging / non-commitment | Non-hedging sub-judge rate | faithful≫relevant gap | OP-M01 + OP-M06 |
| Single-axis blindness (RAG) | — (structural) | any single-number RAG metric | OP-M06 (triad) |

**Document every probe result in the project's calibration receipt (OP-M10).**
Per dspy-sop Case C: never compile against a metric you have not
human-validated on ≥20 spot-checks — the bias probes run *before* that
calibration step (SKILL.md Stage 4 → Stage 5).
