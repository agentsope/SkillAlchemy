# R1 — Source Evidence for `metric-design`

Each load-bearing claim in `SKILL.md` traced to its source, with a verbatim
quote where one exists. Three source families:

1. **DSPy SOP** — `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/`
   (`SKILL.md` Case C + metric table; `intermediate/operation_candidates.json`
   ops `op-004`, `op-024`, `op-030`).
2. **LlamaIndex SOP evaluator stack** —
   `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`
   (OP-10 EvalLoop; Faithfulness / Relevancy / Retriever triad).
3. **Judge-bias research** — [arxiv.org/pdf/2506.02592],
   [arxiv.org/pdf/2509.26072]; GEPA paper [arxiv.org/abs/2507.19457].

> **Naming note (inconsistency, see §6):** SKILL.md references DSPy ops in
> upper case (`OP-030`, `OP-024`, `OP-004`). In the dspy-sop source the IDs are
> lower case (`op-030`, `op-024`, `op-004`). Same operations; case differs.

---

## 1. DSPy SOP — metric mode switch, decomposition, calibration, GEPA

Source: `output/dspy-sop-skill/SKILL.md` and `.../intermediate/operation_candidates.json`

### Claim: "The metric IS the model. Change the metric, change the behavior." / "A bad metric beats a good optimizer."
- SKILL.md §2 core mental model + opening quote.
- **Source:** DSPy Case C 约束.
  > "DSPy will optimize *toward whatever the metric rewards*. A bad metric becomes a bad program at scale."
  — DSPy SOP Case C [dspy.ai/learn/optimization/overview/]
- Opening epigraph "It's unproductive to launch optimization runs using a poorly designed program or a bad metric." paraphrases the same DSPy optimization-overview guidance.

### Claim: Decompose a holistic judge into orthogonal yes/no sub-judges (OP-M01).
- SKILL.md §2 corollary 1, Stage 1, Stage 3, OP-M01.
- **Source:** DSPy Case C step 2.
  > "**Decompose the judge** into orthogonal sub-judges, each a `dspy.Predict(Assess)` call with a single yes/no question (factual? on-topic? concise? non-hedging?). Documented pattern [dspy.ai/learn/evaluation/metrics/]."
  — DSPy SOP Case C
- Also DSPy metric table:
  > "Multi-criteria (factuality + tone + length) | Sub-judge each dim, return **`bool` during optimization (`trace is not None`) and `float` during evaluation**"

### Claim: Bool during compile, float during eval — same function, `trace is not None` (OP-M02).
- SKILL.md §2 corollary 2, Stage 2 universal rule, OP-M02.
- **Source:** dspy-sop `op-030` ("metric_mode_switch").
  > "Inside the metric: return strict bool when trace is not None (compile mode); return float otherwise (eval mode)" — output: "One metric function, two semantics"
  — dspy-sop `operation_candidates.json` op-030 [dspy.ai/learn/evaluation/metrics/, dspy.ai/cheatsheet/]
- And DSPy Case C step 3:
  > "**Use `trace is not None` to return bool during compile, float during eval** — same metric function, two modes. Avoids the optimizer overfitting to score noise."

### Claim: Human-calibrate on ≥20 spot-checks; fix metric if >20% disagreement (OP-M05).
- SKILL.md §2 corollary 3, Stage 5, OP-M05, AP-4, Dilemma 1.
- **Source:** DSPy Case C step 4 + 可提取的操作.
  > "**Spot-check the metric on 20 examples with a human judge first.** If sub-judges disagree with human on >20% of cases, fix the metric before compiling. Garbage metric → garbage compiled program."
  > "**Never compile against a metric you haven't human-validated on ≥ 20 spot-checks.**"
  — DSPy SOP Case C
- Note: SKILL.md raises the bar to "30 if open-ended" and frames it as ≥80% agreement; the DSPy source states "20 examples" and ">20% disagreement". The 30/open-ended figure is a SKILL.md tightening, not in the DSPy source.

### Claim: Add a length penalty as a separate scalar; do not let the judge penalize verbosity (OP-M03).
- SKILL.md Stage 2/3, OP-M03, AP-2, AP-7.
- **Source:** DSPy Case C step 6.
  > "Add a **length penalty** as a separate scalar in the metric — don't rely on the judge to penalize verbosity (judges over-prefer length)."
  — DSPy SOP Case C

### Claim: Rich textual feedback → `dspy.Prediction(score, feedback)` → GEPA, not MIPROv2 (OP-M08).
- SKILL.md OP-M08, Stage 6, §7 textual-feedback row.
- **Source:** DSPy Case C step 5 and dspy-sop `op-004`.
  > "**If sub-judge feedback is rich (e.g. "answer was verbose"), pipe textual feedback into `dspy.GEPA`** instead of MIPROv2 — GEPA leverages text feedback for faster, more sample-efficient convergence."
  — DSPy SOP Case C [dspy.ai/api/optimizers/GEPA/overview/, arxiv.org/abs/2507.19457]
  > "Apply dspy.GEPA with a metric that returns dspy.Prediction(score=..., feedback=...)"
  — dspy-sop `op-004`
- Quantified lift: DSPy Case C 结果 — "typically beats single-judge + MIPROv2 by 10–13% on AIME-style benchmarks [arxiv.org/abs/2507.19457]".

### Claim: Refuse to compile without a metric (AP-10).
- SKILL.md AP-10 "Compiling without a metric → Refuse the compile (DSPy OP-024)".
- **Source:** dspy-sop `op-024` ("anti_pattern_guard").
  > "Refuse to compile. Help them write a metric first (exact match, sub-judge decomposition, or text feedback)"
  — dspy-sop `op-024` [dspy.ai/learn/optimization/overview/]

### Claim: Single LLM-judge as the only metric is an anti-pattern.
- SKILL.md AP-1.
- **Source:** DSPy anti-patterns:
  > "Using LLM-as-judge as the *only* metric for any open-ended task. See Case C. Biases are documented and reproducible [arxiv.org/pdf/2506.02592]."
  — DSPy SOP anti-pattern list

---

## 2. LlamaIndex SOP — RAG evaluator triad (Faithfulness / Relevancy / Retriever)

Source: `output/llamaindex-sop-skill/SKILL.md` (OP-10 EvalLoop)

### Claim: For RAG, use the Faithfulness + Relevancy + Retriever triad; gate every change (OP-M06, Dilemma 2).
- SKILL.md Stage 1, OP-M06, AP-6, §7 RAG rows.
- **Source:** LlamaIndex OP-10 EvalLoop.
  > "`DatasetGenerator` → labeled QA pairs; run `FaithfulnessEvaluator` + `RelevancyEvaluator` + `RetrieverEvaluator(["mrr","hit_rate"])`. Gate every change."
  — LlamaIndex SOP OP-10 [developers.llamaindex.ai/python/framework-api-reference/evaluation/]
- And the baseline/gating discipline:
  > "Track {MRR, hit-rate, faithfulness, relevancy, p95 latency}. **Every** subsequent change must be gated on these numbers."
  — LlamaIndex SOP Stage 2

### Claim: No eval loop / debug-by-anecdote is wrong; stand up the evaluators first.
- SKILL.md §1 production-regression trigger, Dilemma 2.
- **Source:** LlamaIndex anti-pattern A3.
  > "A3 | No eval loop; debug by anecdote | Stand up `RetrieverEvaluator` + `FaithfulnessEvaluator` + `RelevancyEvaluator` first"
  — LlamaIndex SOP anti-patterns table

### Claim: Faithfulness-only is structurally incomplete (a faithful answer can still miss the question) — Dilemma 2.
- SKILL.md Dilemma 2 lesson.
- **Support:** definitional. `FaithfulnessEvaluator` measures entailment of the answer by the retrieved context; `RelevancyEvaluator` measures whether the answer addresses the query — distinct axes per the LlamaIndex evaluation API. The "faithful but off-topic" failure is a direct consequence of the two axes being orthogonal. (Illustrative numbers in Dilemma 2 are scenario figures, not measured.)

---

## 3. Judge-bias research

### Claim: LLM judges over-prefer length / verbosity (length bias) — OP-M03, AP-2, AP-7, Dilemma 1.
- **Source:** [arxiv.org/pdf/2506.02592]. SKILL.md attributes length/self-preference/provenance bias to this paper. DSPy Case C step 6 independently states "judges over-prefer length".

### Claim: Self-preference (judge prefers its own family) — OP-M04, AP-3.
- **Source:** [arxiv.org/pdf/2506.02592]; DSPy Case C step 1.
  > "LLM judges exhibit self-preference, recency, rubric-order, and provenance biases [arxiv.org/pdf/2506.02592, arxiv.org/pdf/2509.26072]."
  — DSPy SOP Case C step 1

### Claim: Recency / position, rubric-order, score-ID biases — §2 catalog, OP-M07, OP-M09, Stage 4.
- **Source:** [arxiv.org/pdf/2509.26072]; cross-confirmed by DSPy metric table:
  > "LLM-as-judge … Watch for self-preference bias, recency bias, score-ID bias [arxiv.org/pdf/2509.26072]"
  — DSPy SOP §metric table

### Claim: GEPA beats MIPROv2 by ~10–13% with textual feedback — OP-M08, Stage 6.
- **Source:** [arxiv.org/abs/2507.19457] (GEPA, ICLR 2026 oral per dspy-sop). DSPy Case C 结果 cites the same paper for the 10–13% figure on AIME-style benchmarks.

---

## 4. Claims that are SKILL.md opinion / synthesis (no single external source)

Flagged honestly so an auditor knows what is sourced vs. authored:

- **≥80% agreement threshold** and **"30 if open-ended"** spot-check count — a tightening of DSPy's "20 examples / >20% disagreement"; author's bar.
- **The bias-probe suite** (length probe, self-preference probe, position probe, rubric-order probe with the specific +5pp / >10% thresholds) — operationalization of the biases above; thresholds are author-chosen, not from the cited papers.
- **Calibration receipt schema** (OP-M10) — author-defined audit artifact; SKILL.md itself labels it "General audit best-practice; DSPy `save(save_program=True)` analog".
- **Dilemma 3 (`cekura-metric-design`, "11 installs")** — illustrative competitor framing; the install count and vendor behavior are scenario detail, not a cited fact.
- **Numeric outcomes inside all three Dilemmas** (e.g. 0.84→0.79, Relevancy 0.41→0.79, MRR figures, +12% thumbs-up) — illustrative scenario numbers, not measured results.

---

## 5. Cross-links

- `[[agentsop-dspy]]` — the optimizer side; consumes the metric this skill produces.
  Case C and ops op-004 / op-024 / op-030 are the primary source.
- `[[agentsop-llamaindex]]` — RAG evaluator triad (OP-10) reused as sub-judges (OP-M06).
- `[[agentsop-domain-eval-set]]` — defines *what* examples are scored; this skill defines
  *how* (the scoring function). Complementary.
- `[[agentsop-regression-gate]]` — consumes the calibrated metric as the per-PR gate.

## 6. Known inconsistency in SKILL.md

DSPy operation IDs are cited upper-case in SKILL.md (`OP-030`, `OP-024`,
`OP-004`) but are lower-case in the dspy-sop source
(`op-030`, `op-024`, `op-004`). The operations referenced are correct and map
1:1; only the casing differs. Recorded here rather than edited, since the task
forbids modifying SKILL.md.
