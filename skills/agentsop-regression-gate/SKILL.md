---
name: agentsop-regression-gate
version: 0.1.0
phase: D
tier: core
frequency: high
status: opinionated
description: Build a held-out eval set, run it on every prompt/model change, and block regressions in CI. An LM change is a code change — gate it with a test suite (eval set + metric + threshold). Cross-framework SOP not surfaced by any single base skill.
---

# regression-gate — Eval Set + Metric + Threshold, Wired Into CI

> "Every subsequent change must be gated on these numbers."
> — Synthesized from [[llamaindex]] Stage 2 (eval loop *before* optimizing) [llamaindex-sop-skill/SKILL.md:114-126]

> "Compiled program beats baseline on a *held-out* test set (not the val set used in optimization)."
> — [[dspy]] Stage 3 exit criterion [dspy-sop-skill/SKILL.md:101]

This is an **enhancement overlay**. The regression-gate SOP exists only as fragments scattered across base skills — [[llamaindex]] `OP-10 EvalLoop` ("gate every change"), [[dspy]] train/dev/test split + metric — and is never assembled as a standalone cross-framework discipline. It is the discipline that turns a one-off eval into a *gate*: a test suite that runs in CI on every prompt/model/retriever change and fails the build on regression. It consumes a metric from `[[agentsop-metric-design]]` and, for domain-specific held-out sets, hands off to `[[agentsop-domain-eval-set]]`.

---

## 1. 何时激活 (When to Activate)

Activate when **any** of these is true:

- **Any prompt change you want to ship safely**: a prompt edit, a system-message tweak, a few-shot-demo swap is about to merge and you have no automated way to know if it made things worse.
- **Any model change**: swapping GPT-4o → a cheaper/newer model, a temperature change, a provider migration. An LM change silently shifts the whole output distribution. [[dspy]] Case B: "If you optimize a complex pipeline for GPT-4, it usually breaks on a smaller model" [dspy-sop-skill/SKILL.md:184].
- **Any retriever/chunking/reranker change in a RAG pipeline**: every such change needs a quantitative gate. [[llamaindex]] `OP-10`: "Quantitative regression test for every chunking / embedding / retriever / prompt change" [llamaindex-sop-skill/SKILL.md:235].
- **Recurring "it got worse" surprises**: the team keeps shipping changes that users report as regressions after the fact. The fix is a gate, not more careful review.
- **Setting up CI for an LLM app** and there is no eval job in the pipeline.

**Do NOT activate for:**

- **One-shot tasks** with no production surface — there is nothing to regress. ([[dspy]] boundary: "Summarize this email once → raw API call" [dspy-sop-skill/SKILL.md:259].)
- **The signature/task is still changing daily** — gate only after the I/O contract stabilizes, else you re-baseline every commit. ([[dspy]] boundary [dspy-sop-skill/SKILL.md:260].)
- **No willingness to define any success criterion** — without a metric there is nothing to gate. Route to `[[agentsop-metric-design]]` first; if the user refuses, this skill cannot help.

---

## 2. 核心心智模型 (Core Mental Model)

### **"An LM change is a code change. Gate it with a test suite: eval set + metric + threshold."**

You already gate code with unit tests in CI: a change that breaks a test fails the build. A prompt edit, a model swap, a chunk-size tweak are *also* changes to the system's behavior — but they slip through review because their effect is statistical, not a stack trace. The regression gate is the missing unit test for LM behavior.

The gate is exactly three artifacts plus a wiring step:

```
   eval set        metric           threshold          CI wiring
  (held-out QA)  (ex,pred)->score   (fail if <X / drop>Y)  (block merge)
        │              │                  │                    │
        └──────────────┴──────────────────┴────────────────────┘
                          REGRESSION GATE
```

Three load-bearing principles:

1. **The eval set is held out and frozen.** It is a labelled, version-controlled fixture that the prompt/model under test has *never seen*. [[dspy]] is explicit: the compiled program must beat baseline on a held-out test set "not the val set used in optimization" [dspy-sop-skill/SKILL.md:101]. The split is `train / dev / test`; the **gate runs on test only**. If the eval set leaks into the prompt (few-shot demos, instructions), the gate measures memorization, not quality.

2. **The metric comes from `[[agentsop-metric-design]]`, not invented here.** This skill does not design metrics — it consumes one. A bad metric makes the gate theatre: it will pass changes that hurt users and block changes that help them. The metric must be human-calibrated *before* it gates anything ([[agentsop-metric-design]] `OP-M05`).

3. **The threshold is a policy, not a number you guess.** Two common shapes: an **absolute floor** (fail if score < X) and a **relative no-regression** (fail if score drops > Y from the committed baseline). Relative is the regression gate proper; absolute is a quality bar. Most teams use both: a floor for "never ship below this," plus a no-regression delta for "this PR must not make it worse."

### Build the eval loop *before* you optimize anything

[[llamaindex]] Stage 2 is named "Build the eval loop **before** optimizing anything" [llamaindex-sop-skill/SKILL.md:114]. The anti-pattern it names is A3: "No eval loop; debug by anecdote" [llamaindex-sop-skill/SKILL.md:348]. The gate is the institutional form of that loop — once it exists, every change is debugged by number, not by vibe.

---

## 3. SOP (Standard Operating Procedure)

```
0. Confirm activation (§1); confirm a metric exists or invoke [[agentsop-metric-design]]
1. BUILD eval set:  generate candidates -> curate to a golden set -> freeze + version
2. SPLIT:           train / dev / test; the GATE runs on TEST only
3. PICK metric:     consume from [[agentsop-metric-design]] (do not invent here)
4. SET threshold:   absolute floor AND/OR relative no-regression delta
5. WIRE into CI:    run eval on every prompt/model/retriever PR; fail on regression
6. HANDLE flakiness: pin seeds/temp, average N runs, separate flaky from real drops
```

### Stage 1 — Build the eval set (generate + curate)

Two stages, never one. **Generation** gives coverage cheaply; **curation** gives trust.

- **Generate** candidates from your corpus. [[llamaindex]] `DatasetGenerator.from_documents(docs).generate_dataset_from_nodes(num=50)` produces labelled QA pairs from the documents themselves [llamaindex-sop-skill/SKILL.md:121]. promptfoo and synthetic-data generators do the same for non-RAG tasks.
- **Curate** the generated set into a *golden set*: a human reviews, fixes wrong labels, drops ambiguous items, and adds known hard/edge cases the generator missed. A purely generated set inherits the generator model's blind spots and tends to be too easy (Dilemma 1).
- **Freeze and version**. The golden set is a committed fixture (`eval/golden_v1.jsonl`), tagged with the date and the generator model. Changing it is a versioned event, not an edit.

Size: [[dspy]] documents the sweet spot — "30 examples = minimum useful, 300 = recommended" [dspy-sop-skill/SKILL.md:87]. For a held-out *gate*, 50–200 curated domain examples is the working range; descend to `[[agentsop-domain-eval-set]]` for domain-specific construction.

### Stage 2 — Split: train / dev / test

The gate runs on **test only**. Keep test sealed from anything that touches the prompt:
- `train` — feeds optimizers / few-shot demo selection.
- `dev` — tuning and threshold-setting.
- `test` — the gate. Never used to author prompts, pick demos, or tune. ([[dspy]] held-out exit criterion [dspy-sop-skill/SKILL.md:101].)

### Stage 3 — Pick the metric (cross-link `[[agentsop-metric-design]]`)

Do not invent a metric here. Consume one from `[[agentsop-metric-design]]`:
- RAG → the Faithfulness + Relevancy + Retriever(MRR/hit-rate) triad ([[llamaindex]] `OP-10` [llamaindex-sop-skill/SKILL.md:234]).
- Exact-answer → exact-match ([[dspy]] §4.3 [dspy-sop-skill/SKILL.md:137]).
- Open-ended → decomposed sub-judges, bool-in-compile/float-in-eval, length penalty ([[agentsop-metric-design]] `OP-M01`/`OP-M02`/`OP-M03`).

A metric that has not been human-calibrated must not gate ([[agentsop-metric-design]] `OP-M05`). An uncalibrated gate is worse than no gate — it gives false confidence.

### Stage 4 — Set the threshold

| Threshold shape | Rule | Use when |
|---|---|---|
| Absolute floor | fail if `score(test) < X` | "never ship below this quality bar" |
| Relative no-regression | fail if `baseline − score > Δ` | "this PR must not make it worse" (the gate proper) |
| Per-slice floor | fail if any slice (e.g. lexical-query subset) drops > Δ | aggregate hides a regressed minority |

Set Δ above measured run-to-run noise (Stage 6), else the gate flaps. Commit the current `test` score as `baseline.json` next to the eval set; the gate compares against it.

### Stage 5 — Wire into CI

- Add an `eval` CI job that runs on every PR touching prompts, model config, retriever/chunking config, or the program graph.
- Job: load frozen eval set → run pipeline at PR's config → compute metric → compare to `baseline.json` → exit non-zero on threshold breach → post the before/after table as a PR comment.
- On merge to main with an *intended* improvement, bump `baseline.json` in the same PR (reviewed, not silent).

### Stage 6 — Handle flaky evals

LLM outputs are nondeterministic; a naive gate flaps and gets disabled. Mitigations:
- **Pin** `temperature=0` and seeds where the provider supports them; disable response caching in CI ([[dspy]] AP-10: "Forgetting `cache=False` in stateless deploys" [dspy-sop-skill/SKILL.md:255]).
- **Average N runs** (e.g. 3) and gate on the mean; report variance.
- **Separate flaky from real**: if the same config scores differently across reruns by more than Δ, the *gate* (Δ too tight) or the *metric* (noisy judge) is the problem — fix those before trusting a single red build. A judge-based metric with high variance should be hardened in `[[agentsop-metric-design]]`, not papered over by widening Δ.

---

## 4. 操作模型 (Operations)

### OP-01 — GenerateEvalCandidates
- **Trigger**: Need a held-out eval set; no labelled fixture exists yet.
- **Action**: Generate QA candidates from the corpus — [[llamaindex]] `DatasetGenerator.generate_dataset_from_nodes(num=50)`, promptfoo synthetic generation, or task-specific synthesis. Tag with generator model + date.
- **Output**: A raw candidate set (unvalidated), ready for curation.
- **Evidence**: [[llamaindex]] Stage 2 [llamaindex-sop-skill/SKILL.md:121]; `OP-10` [llamaindex-sop-skill/SKILL.md:234]; external "eval set generation".

### OP-02 — CurateGoldenSet
- **Trigger**: A generated candidate set exists; it has not been human-reviewed.
- **Action**: Human reviews every item: fix wrong labels, drop ambiguous/duplicate items, inject known hard cases and past production failures. Freeze as a versioned fixture (`golden_vN.jsonl`).
- **Output**: A trusted, frozen golden eval set that the gate runs against.
- **Evidence**: [[dspy]] metric human-validation discipline [dspy-sop-skill/SKILL.md:212]; [[agentsop-metric-design]] `OP-M05`; Dilemma 1.

### OP-03 — SplitTrainDevTest
- **Trigger**: Eval set built; about to use it for both tuning and gating.
- **Action**: Partition into train/dev/test. Seal `test` from all prompt-authoring. The gate reads only `test`. (Note [[dspy]]'s reversed 20/80 train/val split for *prompt optimizers* [dspy-sop-skill/SKILL.md:96] — that is an optimizer concern; the gate still needs an untouched test slice.)
- **Output**: Three disjoint splits; a sealed test set for the gate.
- **Evidence**: [[dspy]] Stage 3 held-out exit criterion [dspy-sop-skill/SKILL.md:101]; AP-9 [dspy-sop-skill/SKILL.md:254].

### OP-04 — SetRegressionThreshold
- **Trigger**: Have a `test` score; need a pass/fail policy.
- **Action**: Commit current `test` score as `baseline.json`. Define absolute floor X and/or relative no-regression Δ (Δ > measured noise). Optionally per-slice floors.
- **Output**: A versioned threshold policy the CI job enforces.
- **Evidence**: [[dspy]] Stage 3 exit "by ≥ task-relevant delta" [dspy-sop-skill/SKILL.md:101]; [[llamaindex]] gate-every-change [llamaindex-sop-skill/SKILL.md:124].

### OP-05 — WireCIGate
- **Trigger**: Eval set + metric + threshold exist; not yet enforced automatically.
- **Action**: Add a CI job triggered by prompt/model/retriever/graph changes: run eval at PR config → compute metric → compare to baseline → fail on breach → comment the before/after table.
- **Output**: Merges that regress quality are blocked; every change carries a number.
- **Evidence**: [[llamaindex]] `OP-10` regression-test framing [llamaindex-sop-skill/SKILL.md:233-235]; external "llm regression testing CI", "promptfoo".

### OP-06 — BumpBaselineOnIntendedWin
- **Trigger**: A PR *intentionally* raises quality; the gate would otherwise pin the old baseline forever.
- **Action**: In the same reviewed PR, update `baseline.json` to the new `test` score. Never let CI auto-bump silently.
- **Output**: Baseline ratchets upward deliberately; future regressions are caught against the new bar.
- **Evidence**: [[dspy]] "keep both `program.gpt4o.json` and `program.llama8b.json`; A/B" [dspy-sop-skill/SKILL.md:191] (versioned-artifact discipline).

### OP-07 — StabilizeFlakyEval
- **Trigger**: The gate flaps — same config, different verdicts across reruns.
- **Action**: Pin temperature/seed, disable CI caching, average N runs and gate on the mean, report variance. If variance > Δ, fix the metric (harden judge via `[[agentsop-metric-design]]`) or widen Δ — never disable the gate.
- **Output**: A stable gate whose red builds are trustworthy.
- **Evidence**: [[dspy]] `cache=False` AP-10 [dspy-sop-skill/SKILL.md:255]; [[agentsop-metric-design]] judge-bias hardening; [[dspy]] Stage 2 exit "stable across two runs" [dspy-sop-skill/SKILL.md:91].

### OP-08 — SliceTheEvalSet
- **Trigger**: Aggregate score is flat but a subpopulation (lexical queries, a tenant, a topic) silently regressed.
- **Action**: Tag eval items by slice; compute and gate per-slice. A win on the majority must not mask a regression on a minority slice.
- **Output**: Slice-level regression detection; aggregate no longer hides harm.
- **Evidence**: [[llamaindex]] per-query-type taxonomy [llamaindex-sop-skill/SKILL.md:280]; [[agentsop-metric-design]] triad (no single number).

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — Generated eval set vs hand-curated golden set

**困境**: Team needs an eval set fast. `DatasetGenerator` produces 200 QA pairs in minutes ([[llamaindex]] Stage 2 [llamaindex-sop-skill/SKILL.md:121]). Hand-curating 200 examples costs days of human time. Ship the generated set as the gate, or pay for curation?

**约束**: The generator is the same model family that powers the pipeline → its questions are answerable by exactly the kind of reasoning the pipeline already does (self-preference leakage). Generated sets skew easy and miss the long-tail failures users actually hit. But zero eval set means shipping blind (anti-pattern).

**决策步骤**:
1. **Generate for coverage, never gate on raw generation.** Use the generated set as a *candidate pool*, not the gate.
2. **Curate a golden subset** (`OP-02`): a human keeps the good items, fixes labels, drops the trivially-easy and the ambiguous, and *injects* known production failures and adversarial/edge cases the generator never proposes.
3. **Cross-family generation** where possible: generate with a *different* model family than the task model to reduce self-preference leakage (mirrors [[agentsop-metric-design]] `OP-M04`).
4. **Size to budget**: 50 curated > 200 raw. [[dspy]] floor is 30 useful examples [dspy-sop-skill/SKILL.md:87]; a tight, curated, edge-case-loaded 50 gates better than a bloated easy 200.
5. **Version both**: keep the raw generated pool (regeneratable) and the frozen golden set (the gate fixture).

**结果**: The golden set is the gate; the generated pool is scaffolding. Teams that gate on raw generated sets ship regressions that the easy set never exercised — the gate was green while users churned.

**可提取的操作**: `OP-01 GenerateEvalCandidates`, `OP-02 CurateGoldenSet`. **Lesson: generation buys coverage, curation buys trust. A gate needs trust — never gate on an uncurated generated set.**

### Dilemma 2 — Threshold too strict blocks good changes

**困境**: A no-regression gate is set at Δ = 0 (any drop fails). A genuinely *good* refactor — simpler prompt, 40% cheaper model — scores 0.81 vs the 0.83 baseline: a 2-point drop within run-to-run noise. The gate blocks a change that is net-positive (equal quality, far cheaper). The team starts overriding the gate, and soon ignores it entirely.

**约束**: Run-to-run noise on this judge-based metric is ±1.5 points (measured across 3 reruns). The 2-point "drop" is statistically indistinguishable from noise. A gate that flags noise as regression trains the team to bypass it — a bypassed gate is worse than none.

**决策步骤**:
1. **Measure noise first** (`OP-07`): rerun the *baseline* config N times; compute the standard deviation. Here σ ≈ 1.5pp.
2. **Set Δ above noise**: Δ = 2σ ≈ 3pp, not 0. A drop must clear the noise band to count as a regression.
3. **Average N runs** and gate on the mean to shrink the noise band, rather than just widening Δ.
4. **Separate cost from quality**: this PR is a *cost* win at *equal* quality. The quality gate should pass (drop within Δ); cost is tracked on its own axis (cross-link `[[agentsop-cost-tiered-models]]`). Don't let a quality gate block a cost win that doesn't hurt quality.
5. **If the metric is too noisy to set a sane Δ**, the metric is the bug — harden it in `[[agentsop-metric-design]]` (decompose, length penalty, cross-family judge), don't widen Δ to infinity.

**结果**: Δ tuned to ~2σ passes the cheaper-equal-quality change, still catches real regressions (a 6pp drop), and the team keeps trusting the gate. A gate calibrated to noise survives; a Δ=0 gate gets disabled.

**可提取的操作**: `OP-04 SetRegressionThreshold`, `OP-07 StabilizeFlakyEval`. **Lesson: the threshold must clear measured noise. A gate that flags noise as failure gets bypassed, and a bypassed gate protects nothing.**

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

### Anti-patterns

| # | Anti-pattern | Why it's wrong | Fix |
|---|---|---|---|
| AP-1 | **No eval set; ship blind** | Every prompt/model change is an uncontrolled experiment on users; "it got worse" is discovered in production | Build a held-out gate ([[llamaindex]] A3 [llamaindex-sop-skill/SKILL.md:348]) |
| AP-2 | **Eval set leaks into the prompt** (few-shot demos / instructions drawn from test) | The gate measures memorization, not generalization; green build, real regression | Seal `test`; demos come from `train` only (`OP-03`; [[dspy]] AP-9 [dspy-sop-skill/SKILL.md:254]) |
| AP-3 | **Gate on a raw generated set** | Inherits generator blind spots; too easy; misses real failures | Curate a golden set (`OP-02`; Dilemma 1) |
| AP-4 | **Gate on an uncalibrated metric** | A wrong metric passes harmful changes and blocks good ones — gate is theatre | Calibrate via `[[agentsop-metric-design]]` `OP-M05` before gating |
| AP-5 | **Δ = 0 / threshold below noise** | Gate flaps on noise, team bypasses it | Set Δ > 2σ measured noise (`OP-04`, `OP-07`; Dilemma 2) |
| AP-6 | **Run the gate on the val/dev set used for tuning** | Optimistic, leaks tuning into evaluation | Gate on held-out `test` only ([[dspy]] [dspy-sop-skill/SKILL.md:101]) |
| AP-7 | **Caching on in CI** | Stale cached outputs mask the change under test | `cache=False` ([[dspy]] AP-10 [dspy-sop-skill/SKILL.md:255]) |
| AP-8 | **Aggregate-only gate** | A win on the majority hides a regressed minority slice | Per-slice gating (`OP-08`) |
| AP-9 | **Silent baseline auto-bump** | Quality can ratchet *down* unnoticed if CI rewrites baseline | Bump baseline only in a reviewed PR (`OP-06`) |
| AP-10 | **Disabling the gate when it flakes** | Removes the only protection; flakiness is a metric/Δ bug, not a gate bug | Stabilize (`OP-07`), never disable |

### Boundaries (when this skill does not apply)

- **One-shot / throwaway tasks** — no production surface to regress ([[dspy]] [dspy-sop-skill/SKILL.md:259]).
- **Unstable signature** — gate only after the I/O contract stabilizes ([[dspy]] [dspy-sop-skill/SKILL.md:260]); otherwise you re-baseline every commit.
- **No metric possible and none willing to be built** — without a metric there is nothing to gate; route to `[[agentsop-metric-design]]` first.
- **Public-benchmark evaluation** (MMLU, HumanEval) — that is a *capability* benchmark, not a *domain regression* gate; use `lm-evaluation-harness`. For a domain-specific held-out set, descend to `[[agentsop-domain-eval-set]]`.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

| Concept | LlamaIndex | DSPy | promptfoo | LangSmith | This skill |
|---|---|---|---|---|---|
| Eval set generation | `DatasetGenerator.generate_dataset_from_nodes(num=N)` [llamaindex-sop-skill/SKILL.md:121] | bring labelled examples; `BootstrapFewShot` self-generates demos (not the test set) | `tests:` synthesis / `generate` from prompts | Datasets created from traces / uploads | `OP-01 GenerateEvalCandidates` |
| Golden / curated set | manual review of generated QA | hand-labelled trainset/devset | curated `tests` YAML with `assert` | curated Dataset + reference outputs | `OP-02 CurateGoldenSet` |
| Train/dev/test split | manual | explicit; **reversed 20/80** for prompt optimizers, held-out test for gate [dspy-sop-skill/SKILL.md:96,101] | n/a (test set is the suite) | dataset splits | `OP-03 SplitTrainDevTest` |
| Metric | `Faithfulness`/`Relevancy`/`RetrieverEvaluator(mrr,hit_rate)` [llamaindex-sop-skill/SKILL.md:234] | `def metric(ex,pred,trace=None)->bool\|float` [dspy-sop-skill/SKILL.md:88] | `assert` (equals/contains/llm-rubric/javascript) | evaluator fns / LLM-as-judge | consumed from `[[agentsop-metric-design]]` |
| Threshold / gate | manual (gate every change [llamaindex-sop-skill/SKILL.md:124]) | held-out beats baseline "by ≥ delta" [dspy-sop-skill/SKILL.md:101] | `assert` pass + `--fail-on` thresholds | rules + alerts on eval scores | `OP-04 SetRegressionThreshold` |
| CI wiring | not built-in (DIY job around `Evaluate`) | not built-in (DIY around `dspy.Evaluate`) | **first-class**: `promptfoo eval` in CI, non-zero exit | CI integration + regression alerts | `OP-05 WireCIGate` |
| Flaky handling | run multiple times | `cache=False`; "stable across two runs" [dspy-sop-skill/SKILL.md:91,255] | repeat + threshold | run aggregation | `OP-07 StabilizeFlakyEval` |

**Combination patterns:**

- **LlamaIndex + this skill**: `DatasetGenerator` for `OP-01`, the Faithfulness/Relevancy/Retriever triad as the metric, wired into a DIY CI job. The base skill names the loop ("gate every change"); this skill makes it a CI gate.
- **DSPy + this skill**: DSPy's split + metric is the eval-loop substrate; this skill adds the *CI enforcement* DSPy leaves to you. Gate the compiled artifact on the held-out test set; bump baseline when recompiling for a new model (Case B).
- **promptfoo as the engine**: promptfoo is the most CI-native option — `promptfoo eval` exits non-zero on failed asserts; it is the closest off-the-shelf realization of `OP-05`. Use it as the runner; still bring a curated set (`OP-02`) and a calibrated metric.
- **LangSmith for managed datasets + monitoring**: managed datasets and regression alerts; pairs with this skill's curation/threshold discipline.

**Opinionated default**: build the eval set with the base framework's generator (`OP-01`), **curate by hand** (`OP-02`), keep the metric in `[[agentsop-metric-design]]`, and run the gate with promptfoo (CI-native) or a thin script around `dspy.Evaluate` / LlamaIndex evaluators. The gate, the metric, and the eval set are three separable, version-controlled artifacts — never one tangled blob.

---

## References

- `references/R1-source-evidence.md` — every cited claim resolved to a source line
- `intermediate/operation_candidates.json` — machine-readable operation registry

**Citations**: [[llamaindex]] `OP-10 EvalLoop` / Stage 2 [llamaindex-sop-skill/SKILL.md:114-126,232-236,348]; [[dspy]] Stage 2-3 split+metric+held-out [dspy-sop-skill/SKILL.md:85-105,137,191,254-255]; [[agentsop-metric-design]]; [[agentsop-domain-eval-set]]; external "llm regression testing CI", "promptfoo", "eval set generation".
