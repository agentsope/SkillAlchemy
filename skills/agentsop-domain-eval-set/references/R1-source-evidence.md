# R1 — Source Evidence for `domain-eval-set`

Verbatim claims and their sources. This overlay distills the **held-out domain
benchmark** idea from two source skills and positions it explicitly against the
**public-benchmark** skill (`lm-evaluation-harness`).

---

## 1. DSPy — train/dev/test discipline, held-out distinct from val

Source: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`

- **Held-out test set is the exit gate, not the val set:**
  > "compiled program beats baseline on a *held-out* test set (not the val set used in optimization) by ≥ task-relevant delta."
  — DSPy SOP Stage 3 exit criterion [dspy.ai/learn/optimization/overview/]

- **Dev-set sizing sweet spot:**
  > "Documented sweet spot: 30 examples = minimum useful, 300 = recommended, 200+ required for MIPROv2 to avoid overfitting."
  — DSPy SOP Stage 2 step 5 [dspy.ai/learn/optimization/overview/]

- **Held-out must be distinct from val when escalating compute:**
  > "Only escalate to `heavy` if data ≥ 300 *and* you have a held-out test set distinct from val."
  — DSPy Case A step 4 [dspy.ai/learn/optimization/optimizers/]

- **Metric must be human-validated before trust (the labeling/curation analogue):**
  > "Never compile against a metric you haven't human-validated on ≥ 20 spot-checks."
  — DSPy Case C [dspy.ai/learn/evaluation/metrics/]

- **Below ~30 you memorize, not measure:**
  > "Below ~30 examples, you're not training — you're memorizing."
  — DSPy anti-pattern 2 [dspy.ai/learn/optimization/overview/]

- **Artifacts are versioned and shipped, not free-floating:**
  > "You ship `program.json`, not a `.txt` prompt."
  — DSPy core mental model [dspy.ai/tutorials/saving/]

---

## 2. LlamaIndex — eval set built from the corpus, gated on every change

Source: `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`

- **Build the eval loop BEFORE optimizing — from the real corpus:**
  > "Build the eval loop **before** optimizing anything … `DatasetGenerator.from_documents(docs).generate_dataset_from_nodes(num=50)`."
  — LlamaIndex SOP Stage 2. Note `num=50` default — the low end of the 50–200 band.

- **Every change gates on the eval numbers:**
  > "Every subsequent change must be gated on these numbers."
  — LlamaIndex SOP Stage 2

- **Labeled gold passages are required for retrieval metrics:**
  > "`RetrieverEvaluator(["mrr","hit_rate"])` … does retrieval pull the gold passage."
  — LlamaIndex OP-10 EvalLoop [developers.llamaindex.ai/python/framework-api-reference/evaluation/]

- **Eval surfaces failures anecdote cannot:**
  > "No eval loop; debug by anecdote" is anti-pattern A3; correct move is to stand up the evaluators first.
  — LlamaIndex anti-patterns table

- **Versioned artifacts + reconcile on drift:**
  > "Indices versioned as deployment artifacts" (Stage 5); live corpus must be reconciled via `IngestionPipeline … UPSERTS_AND_DELETE` (A10).
  — LlamaIndex SOP Stage 5 / anti-pattern A10. This is the data-drift analogue for an eval set going stale.

### Caveat — generated sets are a starting point, not a held-out

LlamaIndex `DatasetGenerator` produces *synthetic* QA pairs from the corpus.
These are excellent for bootstrapping a dev set, but a model can look good on
auto-generated questions while failing real user phrasing. A held-out **domain**
set is sampled from *real traffic* and labeled by humans — generated sets do not
replace it. (See §7 cross-framework mapping in SKILL.md.)

---

## 3. lm-evaluation-harness — the PUBLIC-bench skill to distinguish from

Source: `~/.claude/skills/lm-evaluation-harness/SKILL.md` (frontmatter)

- **Scope is public academic benchmarks:**
  > "Evaluates LLMs across 60+ academic benchmarks (MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag). Use when benchmarking model quality, comparing models, reporting academic results, or tracking training progress."
  — `evaluating-llms-harness` description, v1.0.0

- **Invocation is over public task names, not your data:**
  > `lm_eval --model hf --model_args pretrained=... --tasks mmlu,gsm8k,hellaswag`
  — Quick start

**Distinction (the core of this overlay):** lm-evaluation-harness measures
*general capability* on shared, public, often-contaminated benchmarks. It says
nothing about whether the system answers *your* customers' questions on *your*
data. The two are complementary axes, not substitutes — see anti-pattern AP-1
and OP-DE08 in SKILL.md.

---

## 4. Cross-links

- `[[lm-evaluation-harness]]` — public benchmark runner; the capability-floor axis.
- `[[agentsop-regression-gate]]` — consumes this set as the per-PR gate; this skill produces the artifact, regression-gate enforces it on every change.
- `[[agentsop-metric-design]]` — defines *how* each held-out example is scored (decomposed sub-judges, bool/float, calibration). This skill defines *what* is in the set; metric-design defines the scoring function applied to it.
