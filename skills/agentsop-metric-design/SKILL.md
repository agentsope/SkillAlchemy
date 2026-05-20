---
name: agentsop-metric-design
version: 0.1.0
phase: D
tier: core
frequency: high
status: opinionated
description: >-
  Decomposed, multi-criteria metric design for LLM pipelines. The metric IS the model —
  change the metric and the optimizer changes behavior. Decompose by default; bool during
  compile, float during eval; calibrate against human; mitigate judge bias. Search keywords:
  LLM-as-judge, llm as judge, eval metric, evaluation score, scoring function, rubric,
  RAGAS, G-Eval, judge bias, verbosity bias, how to evaluate LLM output.
---

# metric-design — Decomposed, Multi-Criteria Metrics for LLM Pipelines

> "It's unproductive to launch optimization runs using a poorly designed program or a bad metric."
> — DSPy core team [dspy.ai/learn/optimization/overview/]

> "LLM judges exhibit self-preference, recency, rubric-order, score-ID, and length biases."
> — Synthesized from [arxiv.org/pdf/2506.02592, arxiv.org/pdf/2509.26072]

This is a **tool skill**. It produces a metric function (and a calibration receipt) that other skills consume — DSPy compilers (MIPROv2 / GEPA / BootstrapFewShot), LlamaIndex `FaithfulnessEvaluator`/`RelevancyEvaluator`/`RetrieverEvaluator`, LangGraph eval judges, RAGAS, TruLens. The metric is the optimization target. Get it wrong and every downstream optimizer is theatre.

---

## 1. 何时激活 (When to Activate)

Activate when **any** of these is true:

- **Optimization runs**: a DSPy / OpenAI-Evals / RAGAS / TruLens job is about to consume a `metric(example, pred) -> bool|float`. The metric drives gradient-free search; bias propagates into the artifact.
- **RAG evaluation**: deciding chunk size, reranker, hybrid alpha, retriever-k. A bad metric here picks the wrong chunking strategy and you ship it.
- **Agent benchmarks**: tool-use, multi-step, planning. A single holistic LLM judge cannot distinguish "wrong tool" from "right tool, wrong args".
- **Prompt tuning that has gone past 2 manual iterations**: if you're tuning a prompt and have no quantitative metric, you are guessing. Stop the prompt edits, write the metric.
- **Production regression test**: every chunking / embedding / retriever / prompt PR change needs a metric gate (LlamaIndex `OP-10 EvalLoop`).

**Do NOT activate for:**

- One-off exploratory prompt tests where no decision rides on the output.
- Tasks where exact-match / unit-test / schema-validity already gives ≥95% of signal — don't over-engineer.
- Where the user explicitly refuses to commit to any evaluation criteria (then `dspy-sop` will refuse to compile anyway; this skill cannot help).

---

## 2. 核心心智模型 (Core Mental Model)

### **"The metric IS the model. Change the metric, change the behavior."**

A DSPy/GEPA/MIPRO optimizer is a black-box search that maximizes `metric(pred, example)`. Whatever the metric rewards, the compiled prompt will produce. If the metric prefers verbose, hedged answers (which an LLM judge will, by default — judges over-prefer length [arxiv.org/pdf/2506.02592]), the optimizer will produce verbose, hedged answers. **A bad metric beats a good optimizer every time.**

Three corollaries:

1. **Decompose by default.** A single holistic LLM-as-judge call ("is this answer good? rate 1-5") collapses orthogonal axes (factuality, tone, length, relevance) into one noisy scalar. Decompose into N orthogonal yes/no sub-judges, then aggregate. Same number of LM calls in the limit, vastly less noise.
2. **Bool during compile, float during eval.** Same metric function, two return types based on the `trace` argument. Compile-time `bool` prevents the optimizer from chasing noise in the middle of the distribution; eval-time `float` gives gradient for reporting and debugging. [dspy.ai/learn/evaluation/metrics/]
3. **The metric must be calibrated against humans.** ≥20 spot-checks where you (the human) rate the same examples the metric does. If metric disagrees with human on >20% of cases, **fix the metric before any compile**. Otherwise the optimizer just learns the metric's bias.

### Why holistic judges fail (the catalog)

| Bias | What it does | Source |
|---|---|---|
| Length bias | Judges prefer longer answers regardless of quality | [arxiv.org/pdf/2506.02592] |
| Self-preference | A judge from family X prefers outputs from family X | [arxiv.org/pdf/2506.02592] |
| Recency / position | Last option in a pairwise rated higher | [arxiv.org/pdf/2509.26072] |
| Rubric-order | Criteria listed first weighted more | [arxiv.org/pdf/2509.26072] |
| Score-ID | "5" and "10" anchor differently across rubrics | [arxiv.org/pdf/2509.26072] |
| Provenance | Knowing the source model biases the rating | [arxiv.org/pdf/2506.02592] |

Full catalog in `references/R2-judge-bias-catalog.md`.

---

## 3. SOP (Standard Operating Procedure)

```
0. Confirm activation criteria (§1)
1. DECOMPOSE: list orthogonal criteria
2. CHOICE: bool vs float per criterion
3. WRITE: implement sub-judges + aggregator
4. BIAS-TEST: probe for length, position, self-preference
5. CALIBRATE: ≥20 human spot-checks; agreement ≥80%
6. SHIP: hand metric to optimizer / eval loop
```

### Stage 1 — Decompose

Write down the criteria the user *actually* cares about. For an open-ended Q&A:
- **Factual?** (yes/no) — answer makes no unsupported claims
- **On-topic?** (yes/no) — addresses the question
- **Concise?** (length penalty, scalar) — token count vs budget
- **Non-hedging?** (yes/no) — no "as an AI language model..." or "it depends" cop-outs
- **Cites source?** (yes/no) — if grounded retrieval is required

For RAG specifically, copy LlamaIndex's triad: **Faithfulness** (answer entailed by context), **Relevancy** (answer addresses query), **Retriever quality** (MRR / hit-rate on labeled QA pairs). See `references/R1-source-evidence.md`.

**Output of this stage**: a checklist of 3–6 sub-criteria, each with type (`bool` / scalar) and aggregation rule (AND for hard gates, weighted sum for soft).

### Stage 2 — Bool vs Float Choice (per criterion)

Per [dspy.ai/learn/evaluation/metrics/]:

| Criterion shape | Return | Why |
|---|---|---|
| Hard requirement (factual, schema-valid, no PII) | `bool` | Optimizer should reject anything that fails, not partially credit |
| Soft preference (concise, fluent, on-tone) | `float ∈ [0,1]` | Optimizer benefits from gradient |
| Length | **explicit scalar penalty**, not LLM-rated | LLM judges over-prefer length; bake the penalty in deterministically |

**Universal rule** (DSPy OP-030): wrap the whole metric so it returns `bool` when `trace is not None` (compile mode) and `float` otherwise (eval mode). Same function, two semantics.

### Stage 3 — Write the Judge

```python
import dspy

class Assess(dspy.Signature):
    """Assess a single binary criterion. Reply yes/no."""
    text_to_assess = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer: bool = dspy.OutputField()

def metric(example, pred, trace=None):
    # Hard gates (bool sub-judges)
    factual = dspy.Predict(Assess)(text_to_assess=pred.answer,
        assessment_question="Is every factual claim supported by the context?").assessment_answer
    on_topic = dspy.Predict(Assess)(text_to_assess=pred.answer,
        assessment_question=f"Does this address the question: '{example.question}'?").assessment_answer
    non_hedging = dspy.Predict(Assess)(text_to_assess=pred.answer,
        assessment_question="Does this answer commit to a position (no 'it depends' / 'as an AI' hedging)?").assessment_answer

    # Length penalty (deterministic — DO NOT delegate to judge)
    over_budget = len(pred.answer.split()) > 150
    length_score = 1.0 if not over_budget else max(0.0, 1.0 - (len(pred.answer.split()) - 150) / 150)

    if trace is not None:  # compile mode → strict bool
        return factual and on_topic and non_hedging and not over_budget

    # eval mode → float for reporting
    return (factual + on_topic + non_hedging) / 3.0 * length_score
```

**Rules:**
- One yes/no question per sub-judge. Combining ("is it factual AND concise?") re-introduces holistic confusion.
- Length is a deterministic scalar, never an LLM call. Judges have systematic length bias [arxiv.org/pdf/2506.02592].
- Use a **cheaper / different model family** for the judge than the task model (mitigates self-preference). E.g. task = GPT-4o, judge = Claude-Haiku.

### Stage 4 — Bias Test

Before calibration, run these probes on a 20-example dev set:

1. **Length probe**: take 10 good answers, append a redundant paragraph. Does the metric score them *higher*? If yes, your length penalty is too weak.
2. **Self-preference probe**: generate the same answer from 2 model families. Does the judge prefer its own family by >10pp? If yes, swap judge family.
3. **Position probe** (pairwise only): swap A/B order. Does winner flip >10% of the time? If yes, randomize order or average both orderings.
4. **Rubric-order probe**: list sub-judges in 2 different orders. Does aggregated score shift >5pp? If yes, randomize sub-judge order per call.

Document failures in `references/R2-judge-bias-catalog.md` for this project.

### Stage 5 — Human Calibration

- Sample 20 (or 30 if open-ended) examples spanning the task distribution.
- A human rates each on the same sub-criteria.
- Compute per-sub-judge agreement (Cohen's κ or simple accuracy).
- **Threshold**: ≥80% agreement on each sub-judge, ≥80% on aggregate.
- If below: **fix the metric, do not compile**. Common fixes: rephrase the assessment question, switch judge model, narrow the question scope.

This is non-negotiable. Per DSPy Case C: "Never compile against a metric you haven't human-validated on ≥ 20 spot-checks." Garbage metric → garbage compiled program.

### Stage 6 — Ship

Hand off:
- The metric function (callable).
- A **calibration receipt**: `{n_spot_checks, per_judge_agreement, bias_probe_results, judge_model_id, task_model_id, date}`. Stored next to the compiled artifact. Required for any later audit.
- Recommended optimizer pairing: if sub-judges produce *textual* feedback (not just bool), pipe into `dspy.GEPA` for sample efficiency; otherwise `MIPROv2`.

---

## 4. 操作模型 (Operations)

### OP-M01 — DecomposeMultiCriteria
- **Trigger**: Open-ended generation; multiple correctness axes (factuality + tone + length + relevance).
- **Action**: List 3–6 orthogonal yes/no sub-criteria. One `dspy.Predict(Assess)` call per criterion. Aggregate with AND (hard) + weighted sum (soft).
- **Output**: Multi-judge metric callable; one criterion per call.
- **Evidence**: [dspy.ai/learn/evaluation/metrics/]; DSPy Case C; LlamaIndex Faithfulness+Relevancy+Retriever triad.

### OP-M02 — BoolDuringCompileFloatDuringEval
- **Trigger**: Writing any metric used for both compile (`teleprompt.compile`) and `dspy.Evaluate`.
- **Action**: Inside the metric, `if trace is not None: return bool_aggregate; else: return float_aggregate`.
- **Output**: One metric function, two modes; optimizer avoids chasing float noise.
- **Evidence**: [dspy.ai/learn/evaluation/metrics/]; [dspy.ai/cheatsheet/]; DSPy OP-030.

### OP-M03 — ExplicitLengthPenalty
- **Trigger**: Any LLM-as-judge metric (always).
- **Action**: Add a deterministic scalar `length_score = clip(1 - max(0, len - budget) / budget, 0, 1)` multiplied into the final float. Do NOT delegate length judgment to the LLM.
- **Output**: Length-controlled metric immune to the judge's length bias.
- **Evidence**: [arxiv.org/pdf/2506.02592]; DSPy SOP step "Add length penalty as separate scalar".

### OP-M04 — CrossFamilyJudge
- **Trigger**: Judge model is in same family as task model (e.g., both GPT-4).
- **Action**: Swap judge to a different family (Claude, Llama, Gemini, Mistral). Document choice.
- **Output**: Self-preference mitigated.
- **Evidence**: [arxiv.org/pdf/2506.02592].

### OP-M05 — HumanSpotCheck20
- **Trigger**: Before *any* compile / production rollout of a new or modified metric.
- **Action**: 20 (open-ended: 30) human ratings on the same sub-criteria. Compute agreement. Reject if <80% per-sub or aggregate.
- **Output**: Calibration receipt; metric is human-validated.
- **Evidence**: DSPy Case C step 4; [dspy.ai/learn/evaluation/metrics/].

### OP-M06 — RAGFaithfulnessRelevancyContext
- **Trigger**: RAG pipeline; tuning chunk size / reranker / retriever-k / hybrid alpha.
- **Action**: Instantiate three evaluators: `FaithfulnessEvaluator` (answer entailed by retrieved context), `RelevancyEvaluator` (answer addresses query), `RetrieverEvaluator(["mrr","hit_rate"])` (does retrieval pull the gold passage). Gate every PR.
- **Output**: 3-axis RAG quality vector; never a single number.
- **Evidence**: LlamaIndex OP-10 EvalLoop; [developers.llamaindex.ai/python/framework-api-reference/evaluation/].

### OP-M07 — BiasProbeSuite
- **Trigger**: Before calibration.
- **Action**: Run length-probe, self-preference probe, position probe, rubric-order probe (§3 Stage 4) on 20 examples. Log deltas.
- **Output**: Bias-probe report; rejected if length probe ≥+5pp on padded answers or position flips >10%.
- **Evidence**: [arxiv.org/pdf/2509.26072]; [arxiv.org/pdf/2506.02592].

### OP-M08 — TextualFeedbackForGEPA
- **Trigger**: Sub-judge can articulate *why* it failed (e.g., "answer was verbose", "missed cited source").
- **Action**: Return `dspy.Prediction(score=float, feedback=str)` from the metric. Pair with `dspy.GEPA` optimizer (not MIPROv2).
- **Output**: Sample-efficient, reflection-evolved prompts.
- **Evidence**: [dspy.ai/api/optimizers/GEPA/overview/]; [arxiv.org/abs/2507.19457]; DSPy OP-004.

### OP-M09 — RandomizeJudgeOrder
- **Trigger**: Pairwise judge or rubric with N>3 criteria.
- **Action**: Per-call: randomize A/B order in pairwise; randomize sub-judge ordering. Or run both and average.
- **Output**: Position and rubric-order bias mitigated.
- **Evidence**: [arxiv.org/pdf/2509.26072].

### OP-M10 — CalibrationReceipt
- **Trigger**: Ship a compiled artifact.
- **Action**: Save JSON next to artifact: `{metric_version, n_spot_checks, per_judge_agreement, bias_probe_results, judge_model_id, task_model_id, date, criteria_list}`.
- **Output**: Audit-ready provenance for the metric used to compile.
- **Evidence**: General audit best-practice; DSPy `save(save_program=True)` analog.

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — MIPRO inherited the judge's verbosity bias

**困境**: Team compiled an open-ended customer-support response program with `MIPROv2(metric=llm_judge, auto="medium")`. Auto-eval score climbed from 0.62 to 0.84. Production rolled out. Users complained answers were too long. Auditor traced it: the LLM judge gave +0.18 to answers >120 words across the eval set, including some objectively wrong ones. The optimizer faithfully chased that signal.

**约束**: Re-compile costs ~$30. Cannot re-label dataset. Cannot change judge model (vendor approval cycle).

**决策步骤**:
1. **Diagnose**: Confirm length bias on a held-out set: bin answers by length, plot judge-score vs length. Look for monotonic positive slope. (It was there: +0.21 per 50 words.)
2. **Patch the metric, not the artifact**: Add explicit length penalty (`OP-M03`) and decompose the holistic judge into factual / on-topic / non-hedging sub-judges (`OP-M01`). Length is now deterministic, not judge-rated.
3. **Re-calibrate** on 30 human spot-checks (`OP-M05`). Agreement: was 64%, now 87%.
4. **Re-compile**: Same MIPROv2, new metric. Score on new metric: starts at 0.55 (because old prompts over-verbose under new metric), recovers to 0.79 after compile.
5. **Production A/B**: New artifact has 38% shorter answers, equal factuality, +12% user thumbs-up.

**结果**: The "score regression" (0.84 → 0.79) was misleading — the old metric was the bug. Real quality improved because the metric finally matched the user.

**可提取的操作**: `OP-M01 DecomposeMultiCriteria`, `OP-M03 ExplicitLengthPenalty`, `OP-M05 HumanSpotCheck20`. **Lesson: when a compiled program is "good on metric, bad in production", the metric is wrong. Don't tune harder — fix the metric.**

### Dilemma 2 — RAG faithfulness = 100% but answers are wrong

**困境**: RAG pipeline reports `Faithfulness = 1.0` across 200 eval QA pairs. Users complain answers don't address their questions. Team is confused: "but we're 100% faithful…"

**约束**: Cannot change evaluator vendor. Existing eval suite has only `FaithfulnessEvaluator`.

**决策步骤**:
1. **Realize the missing axis**: `FaithfulnessEvaluator` only asks "is the answer entailed by retrieved context?" An answer of "The context discusses Q3 financials" is *faithful* to the context but does not *answer* "What was Q3 revenue?".
2. **Add `RelevancyEvaluator`** (does the answer address the question?) and `RetrieverEvaluator(["mrr", "hit_rate"])` (is the gold passage even retrieved?). [LlamaIndex OP-10]. This is `OP-M06`.
3. **Re-evaluate**: Faithfulness still 1.00. Relevancy: 0.41. MRR: 0.62. Now the picture is clear — retrieval pulls *some* relevant passages, but the synthesizer hedges with topic-level statements rather than answering the question.
4. **Fix the synthesizer prompt**, gated on the 3-axis metric. Add a sub-judge: "Does the answer give a direct response to the question (not just describe the context)?" — bool, AND-gated.
5. **Result**: Faithfulness 0.97, Relevancy 0.79, MRR 0.74. Users stop complaining.

**结果**: A single metric (faithfulness) created a blind spot. Decomposition exposed the actual failure (synthesizer hedging) which no single number could surface.

**可提取的操作**: `OP-M01`, `OP-M06 RAGFaithfulnessRelevancyContext`. **Lesson: a single RAG metric, however precise, is structurally incomplete. Triad is the minimum.**

### Dilemma 3 — Vendor metric ships in 11 installs but covers one axis

**困境**: A vendor-tied `cekura-metric-design` skill (11 installs) wraps a single proprietary judge. Convenient, but: (a) cannot inspect the rubric, (b) cannot swap judge family, (c) cannot add length penalty, (d) calibration receipt does not include bias probes. Optimizer is chasing the vendor judge's blind spots.

**决策步骤**:
1. **Diagnose dependency**: Identify which axes the vendor judge covers (often: a holistic "quality" score). Identify what is missing (length, hedging, position bias mitigation).
2. **Wrap, don't replace**: Use the vendor score as one sub-judge in a composed metric (`OP-M01`). Add length penalty (`OP-M03`), non-hedging sub-judge, cross-family fact-check (`OP-M04`).
3. **Calibrate the composed metric** (`OP-M05`), not the vendor's alone.
4. If vendor score correlates <0.7 with human aggregate after composition: drop the vendor; you are paying for noise.

**结果**: Vendor metrics buy convenience but lose audit and bias control. Open, decomposed metrics dominate for any pipeline that will be optimized against.

**可提取的操作**: `OP-M01`, `OP-M03`, `OP-M04`, `OP-M10`. **Lesson: a vendor-tied holistic metric is a managed optimizer target you cannot inspect. Decompose around it.**

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

### Anti-patterns

| # | Anti-pattern | Why it's wrong | Fix |
|---|---|---|---|
| AP-1 | **Single holistic LLM-as-judge** ("rate 1-5") as optimizer metric | Conflates orthogonal axes; inherits all judge biases; optimizer chases noise | Decompose into yes/no sub-judges (`OP-M01`) |
| AP-2 | **No length penalty** in a generation metric | Judges over-prefer length; optimizer learns to be verbose | Deterministic length term (`OP-M03`) |
| AP-3 | **Same family for judge and task model** | Self-preference bias inflates score 5–15pp | Cross-family judge (`OP-M04`) |
| AP-4 | **Skipping human calibration** | Optimizer learns the metric's bias, not the task | ≥20 spot-checks (`OP-M05`) |
| AP-5 | **Throwing optimizers at a stalled compile** | If metric is bad, no optimizer can save it | Return to metric design |
| AP-6 | **Single-axis RAG metric** (faithfulness only) | Misses query-relevance and retrieval-quality | Triad (`OP-M06`) |
| AP-7 | **LLM-rated length** ("is this concise?" as a judge call) | Inherits length bias; deterministic is free | Length is `len(tokens)`, not a judge call |
| AP-8 | **Hand-edited metric mid-experiment** without re-calibration | Past compile artifacts now have invalid calibration receipts | Bump metric version; re-calibrate |
| AP-9 | **Float metric in compile mode** | Optimizer chases sub-percent noise; overfit | bool in compile, float in eval (`OP-M02`) |
| AP-10 | **Compiling without a metric** at all | Without a metric DSPy degenerates to verbose prompting | Refuse the compile (DSPy OP-024) |

### Boundaries (when this skill cannot help)

- **No willingness to define success criteria**: if the user cannot articulate any criterion for "good", no metric exists. Route to `scientific-critical-thinking` for problem definition first.
- **Tasks where exact-match dominates** (classification, structured extraction, code-passes-tests): use the obvious metric; this skill's decomposition machinery is overkill. Don't gold-plate.
- **Pure preference-pair tasks** (RLHF data): preference judges have their own bias profile (Bradley-Terry-style); see `simpo` / `trl-fine-tuning` skills, not this one.
- **Aesthetic / subjective tasks with no human ground truth** (poetry, art): metric design here is essentially arbitrary. Be explicit that you are encoding *one* aesthetic, not measuring quality.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

| Concept | DSPy | LlamaIndex | RAGAS | TruLens | This skill |
|---|---|---|---|---|---|
| Metric type | `def metric(ex, pred, trace=None) -> float\|bool` | `EvaluationResult` from `BaseEvaluator` | `Metric` class (`Faithfulness`, `AnswerRelevancy`, etc.) | `Feedback` function | metric function + calibration receipt |
| Multi-criteria | sub-judges via `dspy.Predict(Assess)` | stack of `FaithfulnessEvaluator` + `RelevancyEvaluator` + `RetrieverEvaluator` | metric ensemble | `Feedback` per criterion | `OP-M01 DecomposeMultiCriteria` |
| Mode switch (compile vs eval) | `trace is not None` returns bool | N/A (eval only) | N/A | N/A | `OP-M02` |
| Faithfulness | sub-judge "every claim supported?" | `FaithfulnessEvaluator` (entailment-based) | `Faithfulness` metric (claim-by-claim NLI) | groundedness feedback | sub-judge or pre-built |
| Relevancy | sub-judge "addresses question?" | `RelevancyEvaluator` | `AnswerRelevancy` (embedding-based) | answer-relevance feedback | sub-judge |
| Retrieval quality | LlamaIndex `RetrieverEvaluator` MRR/hit-rate | `RetrieverEvaluator(["mrr","hit_rate"])` | `ContextPrecision`, `ContextRecall` | context-relevance feedback | pre-built (use LlamaIndex / RAGAS) |
| Length penalty | manual scalar in metric | manual | manual | manual | `OP-M03` (deterministic) |
| Textual feedback | `dspy.Prediction(score, feedback)` → GEPA | N/A | rationale strings | feedback rationale | `OP-M08` |
| Cross-family judge | swap `judge_lm` in metric | swap `service_context.llm` of evaluator | swap evaluator LLM | swap feedback LLM | `OP-M04` (always) |

**Combination patterns:**

- **DSPy + LlamaIndex**: use LlamaIndex `FaithfulnessEvaluator` + `RelevancyEvaluator` *as* the sub-judges inside a DSPy metric; aggregate to bool/float per `OP-M02`. (JetBlue/Databricks pattern.)
- **DSPy + RAGAS**: use `Faithfulness` / `AnswerRelevancy` / `ContextPrecision` as sub-scalars; pass into a DSPy metric for compile.
- **TruLens for production monitoring**: same sub-judges, different runtime (live, sampled). Calibration receipts should match.

**Opinionated default**: build the metric in pure Python with `dspy.Predict(Assess)` calls (transparent, version-controllable) and import LlamaIndex evaluators only for the RAG triad where the LlamaIndex evaluators are battle-tested. Avoid vendor SDKs whose rubrics you cannot inspect.

---

## Appendix — Quickstart Skeleton

```python
import dspy

class Assess(dspy.Signature):
    """One yes/no assessment."""
    text = dspy.InputField()
    question = dspy.InputField()
    answer: bool = dspy.OutputField()

# Use a DIFFERENT family from the task model
judge_lm = dspy.LM("anthropic/claude-haiku-4")  # task model is openai/gpt-4o

def make_metric(budget_words=150):
    def metric(example, pred, trace=None):
        with dspy.context(lm=judge_lm):
            factual = dspy.Predict(Assess)(text=pred.answer,
                question="Is every claim supported by the provided context?").answer
            on_topic = dspy.Predict(Assess)(text=pred.answer,
                question=f"Does this directly address: {example.question}?").answer
            non_hedging = dspy.Predict(Assess)(text=pred.answer,
                question="Does this commit to a position (no 'as an AI', no 'it depends')?").answer
        n_words = len(pred.answer.split())
        length_score = 1.0 if n_words <= budget_words else max(0.0, 1 - (n_words - budget_words)/budget_words)
        if trace is not None:
            return bool(factual and on_topic and non_hedging and n_words <= budget_words)
        return (int(factual) + int(on_topic) + int(non_hedging)) / 3.0 * length_score
    return metric
```

Then: bias-probe → human-calibrate → save receipt → ship.

---

## References

- `references/R1-source-evidence.md` — DSPy / LlamaIndex / LangGraph source quotes
- `references/R2-judge-bias-catalog.md` — Judge bias taxonomy + mitigations
- `intermediate/operation_candidates.json` — Operation registry

**Citations**: [dspy.ai/learn/evaluation/metrics/], [dspy.ai/learn/optimization/overview/], [dspy.ai/cheatsheet/], [dspy.ai/api/optimizers/GEPA/overview/], [arxiv.org/abs/2507.19457], [arxiv.org/pdf/2506.02592], [arxiv.org/pdf/2509.26072], [developers.llamaindex.ai/python/framework-api-reference/evaluation/], [cookbook.openai.com/examples/evaluation/evaluate_rag_with_llamaindex].
