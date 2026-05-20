---
name: agentsop-prompt-compilation
version: 0.1.0
phase: D
tier: core
frequency: medium
status: opinionated
layer: enhance-overlay
decision_layer_only: true
defers_implementation_to: ["dspy", "dspy-sop", "metric-design"]
description: The compile-readiness gate for prompt auto-optimization. Decide whether you have earned the right to run an optimizer (DSPy MIPROv2 / GEPA / BootstrapFewShot) before spending compute. Two preconditions only — a real metric, and enough examples for the optimizer you picked. Garbage metric in, garbage prompt out. Pick the optimizer by data scale; GEPA inverts the scale assumption (~10 examples + textual feedback).
---

# prompt-compilation — The Compile-Readiness Gate

> "It's unproductive to launch optimization runs using a poorly designed program or a bad metric."
> — DSPy core team [dspy.ai/learn/optimization/overview/]

> "Compile when you can measure. The optimizer maximizes your metric — garbage metric in, garbage prompt out."
> — this skill's operating principle (synthesized from the line above + DSPy Case C)

This is an **enhancement-overlay decision skill**. It answers exactly one question the broad `[[dspy]]` library
skill buries under API surface: **have you earned the right to run an optimizer yet, and which one?** It produces a
go / no-go gate plus an optimizer pick. It defers *every* implementation detail — Signature syntax, module choice,
`compile()` calls, save/deploy — to `[[dspy]]` and the full workflow in `[[agentsop-dspy]]`. It defers metric *construction*
to `[[agentsop-metric-design]]`; this skill only checks the metric *exists and is validated*, then uses it as the gate.

The trap it removes: people reach for `MIPROv2(auto="heavy")` because the API is right there, before they have a
metric worth maximizing or enough data to avoid memorization. Compilation is a hyperparameter search costing
hundreds-to-thousands of LM calls ($2–$40+, minutes-to-hours) [dspy.ai/faqs/]. Spending that on an un-validated
metric or 8 examples is pure waste.

---

## 1. 何时激活 (When to Activate)

Activate when **all three** of these are plausibly true (the gate then *confirms* them):

- **A hand-tuned prompt has plateaued.** The team has manually iterated few-shot examples / wording past the point
  of obvious returns. Symptom from `[[agentsop-dspy]]` §1: "the team manually tunes few-shot examples; a metric exists
  but isn't being used to drive prompt design."
- **A metric exists (or can be built).** There is a `metric(example, pred) -> bool|float` — or one can be written
  and human-validated. Without this, do not activate; the optimizer has nothing to maximize.
- **Labeled examples exist.** There is a dev set. The *count* determines which optimizer is even legal (§3, §4.2).

Concrete triggers in intent or codebase:

| Trigger | Signal |
|---|---|
| Spend intent | "auto-tune this prompt", "should I run MIPRO?", "is it worth compiling?", "GEPA vs MIPROv2", "optimize prompts for our metric" |
| API reach | `MIPROv2(`, `BootstrapFewShot(`, `dspy.GEPA(`, `teleprompter`, `optimizer.compile(` about to be called |
| Symptom | hand-tuned prompt stuck; few-shot examples curated by hand; metric written but only used for reporting, not optimization |

**Do NOT activate when:**

- The task is one-shot or the Signature/I-O contract is still churning daily — compile only after it stabilizes
  [dspy.ai/learn/optimization/overview/]; otherwise you pay compile cost for prompts you'll throw away.
- No metric is possible and none will be built — then this is verbose prompting, not compilation. Route to
  `[[agentsop-metric-design]]` first; if the user refuses any success criterion, the gate stays closed.
- Compliance requires verbatim human-authored prompts — optimized prompts are machine-generated artifacts.
- You only need *parse safety* (a typed Signature), not *quality optimization* — that is `[[agentsop-dspy]]` Stage 1 and
  the `signature-design` overlay. Promoting prose to a typed Signature and *compiling* it are two different gates.

---

## 2. 核心心智模型 (Core Mental Model)

### **"Compile when you can measure. The optimizer maximizes your metric — garbage metric in, garbage prompt out."**

An optimizer (MIPROv2, GEPA, BootstrapFewShot) is a black-box search over prompt instructions + few-shot demos that
maximizes `metric(pred, example)`. It has no taste. It will faithfully chase *whatever the metric rewards*, biases
and all. From `[[agentsop-dspy]]` Case C: "DSPy will optimize toward whatever the metric rewards. A bad metric becomes a
bad program at scale." Two corollaries make this a *gate*, not a step:

1. **The metric is the precondition, not a tunable.** Before any compute is spent, the metric must (a) exist and
   (b) agree with human judgment on ≥20 spot-checks. An un-validated metric means the expensive search optimizes
   the metric's blind spot. This is non-negotiable [dspy.ai/learn/evaluation/metrics/; Case C]. Construction is
   `[[agentsop-metric-design]]`'s job; this skill only *checks the receipt*.

2. **Data scale is a hard floor, not a preference.** Below the optimizer's example floor you are not training, you
   are memorizing. The DSPy 20/80 train/val split exists *because* "prompt-based optimizers often overfit to small
   training sets" [dspy.ai/learn/optimization/overview/]. The floor differs per optimizer (§4.2).

### The two-gate picture

```
            ┌──────────────────────────────────────────────┐
 Gate 1     │  METRIC: exists?  AND  human-validated ≥20?   │  ── No ─► STOP. Build/validate metric ([[agentsop-metric-design]]).
 (measure)  └──────────────────────────────────────────────┘
                              │ Yes
                              ▼
            ┌──────────────────────────────────────────────┐
 Gate 2     │  EXAMPLES: ≥ floor for the optimizer I want?  │  ── No ─► Pick a lower-floor optimizer, collect data,
 (data)     └──────────────────────────────────────────────┘           or STOP (use LabeledFewShot as a floor).
                              │ Yes
                              ▼
                   COMPILE (cheap probe first: auto="light")
```

### The cost reality (why the gate is worth having)

Compilation runs hundreds-to-thousands of LM calls. Reference run: ~3.2k API calls, $2–$3, 6–20 min for
`auto="light"`; `auto="heavy"` on 1000+ examples can hit tens of dollars and hours [dspy.ai/faqs/]. Cost scales with
`num_trials × |trainset| × |program LM calls|`. The gate's entire job is to stop you spending that on a metric or
dataset that cannot pay it back.

---

## 3. SOP (Standard Operating Procedure)

```
0. Confirm activation (§1): plateaued hand-tuning + metric + examples.
1. GATE 1 — metric exists AND validated ≥20 human spot-checks?   [hard]
2. GATE 2 — example count ≥ floor for the chosen optimizer?      [hard]
3. PICK    — choose optimizer by data scale + feedback signal.   (§4.2)
4. BUDGET  — estimate cost; cap it; choose a cheap optimizer LM.
5. PROBE   — run auto="light" (or smallest config) as a signal.
6. DECIDE  — gain ≥ threshold → escalate; else go back, don't escalate.
```

### Gate 1 — Metric (the "can you measure" gate)

- Is there a `metric(example, pred, trace=None) -> bool|float`? If not → **STOP**, route to `[[agentsop-metric-design]]`.
- Has it been validated against a human on ≥20 spot-checks (≥30 if open-ended), with ≥80% agreement? If not →
  **STOP and validate first.** "Never compile against a metric you haven't human-validated on ≥20 spot-checks"
  [`[[agentsop-dspy]]` Case C; dspy.ai/learn/evaluation/metrics/].
- Is the metric a *single* holistic LLM-judge? Then it inherits length / self-preference / position bias and the
  optimizer will chase those biases — decompose it (`[[agentsop-metric-design]]`) before compiling [arxiv.org/pdf/2506.02592].

**Exit:** a validated metric callable + a calibration receipt. Otherwise the gate is closed; do not proceed.

### Gate 2 — Examples (the "enough data" gate)

Count labeled examples. The DSPy-documented thresholds: **≥30 = minimum useful, ~300 = recommended, 200+ required
for MIPROv2** to avoid overfitting [dspy.ai/learn/optimization/overview/]. The floor is *per optimizer*:

- `< 10` → only `LabeledFewShot(k=8)` (no search, weakest) — usually means **STOP, collect data**.
- `~10+` **with textual feedback** → `GEPA` is legal and sample-efficient (this inverts the usual "more data" rule).
- `~30–50` → `BootstrapFewShot` / `BootstrapFewShotWithRandomSearch`.
- `200+` → `MIPROv2`.

**Exit:** the example count clears the floor of the optimizer you intend to run. If not, either drop to a
lower-floor optimizer or stop.

### Step 3 — Pick optimizer by data scale + signal

Use the table in §4.2. The single most important branch: **do you have textual error feedback** (test diffs, schema
violations, judge rationales like "answer was verbose")? If yes, `GEPA` needs only ~10 examples and converges faster
because it reflects on the *text* of the feedback, not just a scalar [dspy.ai/tutorials/gepa_ai_program/;
arxiv.org/abs/2507.19457]. If no, fall back to the data-scale ladder.

### Step 4 — Budget

Estimate before launching (§4.4). Cap spend. Use a **cheap optimizer LM** (e.g. gpt-4o-mini) even when the *task* LM
is expensive — community-reported parity at a fraction of cost [github.com/stanfordnlp/dspy/issues/1596]. Set
`dspy.configure(track_usage=True)` to log actual spend.

### Step 5 — Probe cheap first

Run `auto="light"` (MIPROv2) or the smallest config first. Docs: "start with moderate values, observe behavior, and
scale up only if you see clear gains" [github.com/stanfordnlp/dspy/issues/1596]. **Never start at `auto="heavy"`.**

### Step 6 — Decide on the probe result

- `light` gives **<2% lift** → do **not** escalate. The bottleneck is the program/metric, not the optimizer. Loop
  back to `[[agentsop-dspy]]` Stage 1 (signature ambiguous? wrong decomposition?) [dspy.ai/learn/optimization/overview/].
- `light` gives **2–10% lift** → escalate to `medium`; go to `heavy` only if data ≥300 *and* you have a held-out
  test set distinct from val.
- Always confirm the final gain on a **held-out test set**, not the val set used during optimization.

---

## 4. 操作模型 (Operations)

### 4.1 — Operation registry (Trigger / Action / Output / Evidence)

#### OP-1 — ReadinessGate (entry, hard gate)
- **Trigger**: Anyone about to call an optimizer's `compile()`.
- **Action**: Run Gate 1 (metric exists + validated ≥20) then Gate 2 (examples ≥ optimizer floor). Any failure → STOP.
- **Output**: Decision token `compile-ready` | `not-ready` + the failing gate.
- **Evidence**: [dspy.ai/learn/optimization/overview/]; `[[agentsop-dspy]]` Case C, §3 three-stage gate.

#### OP-2 — MetricExistsCheck
- **Trigger**: Gate 1.
- **Action**: Confirm a `metric(example, pred, trace=None) -> bool|float` exists. If absent → route to `[[agentsop-metric-design]]`, gate stays closed.
- **Output**: Metric callable or a STOP.
- **Evidence**: Anti-pattern "compiling without a metric" [dspy.ai/learn/optimization/overview/].

#### OP-3 — MetricValidatedCheck
- **Trigger**: Metric exists (OP-2).
- **Action**: Require ≥20 (open-ended ≥30) human spot-checks at ≥80% agreement, plus a calibration receipt. If a single holistic LLM-judge, require decomposition first.
- **Output**: `validated` flag + receipt reference.
- **Evidence**: `[[agentsop-dspy]]` Case C step 4; [dspy.ai/learn/evaluation/metrics/]; [arxiv.org/pdf/2506.02592].

#### OP-4 — ExampleFloorCheck
- **Trigger**: Gate 2.
- **Action**: Count labeled examples; compare to the floor of the intended optimizer (LabeledFewShot any; GEPA ~10+feedback; Bootstrap ~30–50; MIPROv2 200+).
- **Output**: `cleared` | `below-floor` + the legal optimizer set.
- **Evidence**: [dspy.ai/learn/optimization/overview/] (30 min / 300 rec / 200+ MIPROv2).

#### OP-5 — OptimizerByDataScale
- **Trigger**: Both gates passed.
- **Action**: Pick from the §4.2 table by example count and feedback signal. Prefer GEPA when textual feedback exists.
- **Output**: Optimizer choice + config.
- **Evidence**: [dspy.ai/learn/optimization/optimizers/]; [dspy.ai/api/optimizers/GEPA/overview/].

#### OP-6 — CostBudgetGuard
- **Trigger**: Before launching compile.
- **Action**: Estimate `num_trials × |trainset| × calls`; cap spend; set a cheap optimizer LM; enable `track_usage=True`.
- **Output**: A budget ceiling + chosen optimizer LM.
- **Evidence**: [dspy.ai/faqs/]; [github.com/stanfordnlp/dspy/issues/1596].

#### OP-7 — CheapProbeFirst
- **Trigger**: Compile-ready, budget set.
- **Action**: Run `auto="light"` (or smallest config) first. Never start at `heavy`.
- **Output**: A cheap lift signal.
- **Evidence**: [github.com/stanfordnlp/dspy/issues/1596]; `[[agentsop-dspy]]` Case A.

#### OP-8 — EscalateOrReturn
- **Trigger**: Probe finished.
- **Action**: <2% lift → return to program/metric design (do NOT escalate). 2–10% → `medium`. `heavy` only if data ≥300 + held-out test set. Confirm gain on held-out test.
- **Output**: Escalate / iterate-back decision.
- **Evidence**: `[[agentsop-dspy]]` Case A; [dspy.ai/learn/optimization/overview/].

### 4.2 — Optimizer-by-data-scale table

| Examples | Feedback signal | Optimizer | Why / floor |
|---|---|---|---|
| `<10` | any | `LabeledFewShot(k=8)` | No search; weakest. Usually means STOP and collect data. [dspy.ai/cheatsheet/] |
| `~10+` | **textual** (diffs, schema violations, judge rationales) | `dspy.GEPA(metric=m_with_feedback)` | Inverts the data-scale rule — reflection on text feedback is sample-efficient. [arxiv.org/abs/2507.19457] |
| `~30–50` | scalar | `BootstrapFewShot` / `…WithRandomSearch` | Self-bootstrapped demos; minimum useful regime. [dspy.ai/learn/optimization/optimizers/] |
| `200+` | scalar | `MIPROv2(metric=m, auto="light")` then escalate | Joint instruction + demo Bayesian search; 200 is the documented floor. [dspy.ai/api/optimizers/MIPROv2/] |
| any (post-MIPRO, ship smaller model) | — | chain `BootstrapFinetune(student=small, teacher=optimized)` | Distills prompts into weights. [dspy.ai/api/optimizers/BootstrapFinetune/] |

### 4.3 — Readiness checklist (copy/paste)

```
GATE 1 — MEASURE
[ ] metric(example, pred, trace=None) -> bool|float exists
[ ] validated vs human: >=20 spot-checks (>=30 open-ended), >=80% agreement
[ ] receipt saved {n_spot_checks, agreement, judge_model, task_model, date}
[ ] NOT a lone holistic LLM-judge (else decompose via [[agentsop-metric-design]] first)

GATE 2 — DATA
[ ] labeled examples counted: N = ____
[ ] N clears the floor of the optimizer chosen below
[ ] (prompt-based optimizers) 20/80 train/val split planned; GEPA uses standard split

PICK + BUDGET
[ ] optimizer chosen by §4.2 (GEPA if textual feedback)
[ ] cost ceiling set; cheap optimizer LM chosen; track_usage=True
[ ] plan: probe auto="light" first, escalate only on >=2% lift, confirm on held-out test
```

### 4.4 — Cost budget heuristics

| Config | Rough cost | Use when |
|---|---|---|
| `LabeledFewShot` / `BootstrapFewShot` | cents–~$1 | Floor; ≤50 examples |
| `MIPROv2(auto="light")` | ~$2–3, 6–20 min, ~3.2k calls | First probe, always |
| `MIPROv2(auto="medium")` | single–low-tens of $ | Light showed ≥2% lift |
| `MIPROv2(auto="heavy")` | tens of $, hours | Only if data ≥300 + held-out test + budget |
| `GEPA` (~10+ examples) | low, sample-efficient | Textual feedback available |

Source: [dspy.ai/faqs/]; [github.com/stanfordnlp/dspy/issues/1596]; [arxiv.org/abs/2507.19457].

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — Optimizer cost vs gain: is compiling even worth it?

**困境**: A 3-stage RAG pipeline already hits 72% on dev after manual prompt tuning. `MIPROv2(auto="heavy")` would
cost ~$40 and 4 hours. Worth it? (Adapted from `[[agentsop-dspy]]` Case A.)

**约束**:
- 250 labeled examples (above the MIPROv2 200-floor) [dspy.ai/learn/optimization/optimizers/].
- Prompts already hand-iterated — diminishing returns suspected.
- Pipeline LM = GPT-4o; per-call cost compounds at trial scale.

**决策步骤**:
1. **Gate 1 first**: were the prompts ever scored against the metric, or just eyeballed? If only eyeballed, even
   `auto="light"` (~$2) often yields large lifts over hand-tuned baselines (paper reports 25%/65% over standard
   few-shot) [arxiv.org/abs/2310.03714] — the metric was never actually driving design.
2. **Probe `light` (~$2), never `heavy`** (OP-7). It is a cheap signal for whether more compute helps.
3. **<2% lift** → do NOT escalate to `heavy`. Return to program/metric: signature ambiguous? is 3-stage the right
   decomposition? (OP-8) [github.com/stanfordnlp/dspy/issues/1596].
4. **2–10% lift** → `medium`; `heavy` only if data ≥300 + a held-out test set distinct from val.
5. Use **gpt-4o-mini as the optimizer LM** even though the task LM is gpt-4o (OP-6) — community parity.

**结果**: The $40 `heavy` run is almost never the right first move. The $2 probe tells you whether to spend more or
to go fix the program. Often the answer is "fix the program/metric first."

**可提取的操作**: `OP-1`, `OP-6 CostBudgetGuard`, `OP-7 CheapProbeFirst`, `OP-8 EscalateOrReturn`. **Lesson: never
open at `heavy`. Probe `light` with a cheap optimizer LM, and treat <2% as a signal to fix the program, not to add
compute.**

### Dilemma 2 — Only 12 examples: GEPA inverts the data-scale assumption

**困境**: A code-fix agent has just **12 labeled examples**, but each failing run produces *rich textual feedback*:
the failing test diff, a schema-violation message, a linter error. The data-scale ladder says 12 < 30 → "STOP,
collect data, you can't optimize." Is that right?

**约束**:
- 12 examples is below the BootstrapFewShot (~30) and MIPROv2 (200) floors.
- Collecting 200+ labeled examples is weeks of effort.
- But the failures emit machine-readable *text* feedback, not just a pass/fail scalar.

**决策步骤**:
1. **Gate 1**: a metric exists — pass/fail on the test plus a textual `feedback` string. Validate it (the test is
   ground truth; spot-check the feedback strings are accurate). Pass.
2. **Gate 2 — do NOT apply the scalar-data ladder.** The presence of *textual feedback* changes which optimizer is
   legal. GEPA needs only ~10 examples because it reflects on the *content* of the feedback, not a scalar gradient
   [dspy.ai/tutorials/gepa_ai_program/; arxiv.org/abs/2507.19457]. 12 ≥ ~10 → GEPA is legal.
3. **Pick GEPA** (OP-5): return `dspy.Prediction(score=..., feedback="failing assert: expected X got Y")` from the
   metric; this is GEPA's superpower [dspy.ai/api/optimizers/GEPA/overview/].
4. **Probe cheap** (OP-7), confirm lift on the held-out examples (OP-8).

**结果**: A dataset that is far too small for MIPROv2/Bootstrap is *sufficient* for GEPA. The "you need 200 examples"
intuition is specific to scalar-feedback optimizers; textual feedback buys an order-of-magnitude in sample
efficiency. GEPA reported beating MIPROv2 by 10–13% on benchmarks while being more sample-efficient
[arxiv.org/abs/2507.19457].

**可提取的操作**: `OP-4 ExampleFloorCheck`, `OP-5 OptimizerByDataScale`. **Lesson: the example floor is per-optimizer.
If you can express *why* an output failed as text, GEPA inverts the data-scale assumption — ~10 examples suffice.
Do not reflexively gate out small datasets that carry rich feedback.**

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

### Anti-patterns

| # | Anti-pattern | Why it's wrong | Fix |
|---|---|---|---|
| AP-1 | **Compiling without a metric** | The optimizer has nothing to maximize; DSPy degenerates to verbose prompting | Refuse the compile; build a metric (`OP-2`, `[[agentsop-metric-design]]`) |
| AP-2 | **Compiling against an un-validated single LLM-judge** | The search faithfully chases the judge's length / self-preference / position bias [arxiv.org/pdf/2506.02592] | Validate ≥20 spot-checks; decompose the judge (`OP-3`) |
| AP-3 | **Compiling on <10 examples** (scalar feedback) | Below the floor you memorize, not train; "prompt-based optimizers overfit small sets" [dspy.ai/learn/optimization/overview/] | Collect data, or use `LabeledFewShot` as a floor — or GEPA *if* textual feedback (`OP-4`) |
| AP-4 | **Starting at `auto="heavy"`** | Tens of $ / hours before you know if compute even helps | Probe `auto="light"` first (`OP-7`) |
| AP-5 | **Escalating after a <2% probe lift** | The bottleneck is the program/metric; more compute won't fix it | Return to `[[agentsop-dspy]]` Stage 1 (`OP-8`) |
| AP-6 | **Using the expensive task LM as the optimizer LM** | Multiplies trial-scale cost for no documented gain | Cheap optimizer LM (gpt-4o-mini) (`OP-6`) |
| AP-7 | **Applying the scalar data-floor to a feedback-rich task** | Wrongly gates out GEPA-legal small datasets | Check for textual feedback before counting examples (`OP-5`) |
| AP-8 | **Reporting the gain on the val set used in optimization** | Overfit signal; not a real held-out improvement | Confirm on a held-out test set distinct from val (`OP-8`) |
| AP-9 | **Compiling while the Signature/I-O contract is still churning** | You pay compile cost for prompts you'll throw away | Stabilize the contract first (`signature-design` / `[[agentsop-dspy]]` §1) |

### Boundaries (when this skill cannot help)

- **No willingness to define any success criterion** — no metric can exist; the gate stays closed. Problem
  definition first (`[[agentsop-metric-design]]`, then `scientific-critical-thinking`).
- **Parse-safety, not quality** — if you only need a typed Signature so code can consume the output, that is the
  *promote* gate (`signature-design` / `[[agentsop-dspy]]` Stage 1), a different decision from *compile*.
- **HOW to write/run the optimizer** — class syntax, `compile()` args, save/deploy: that is `[[dspy]]` and
  `[[agentsop-dspy]]`, not this overlay.
- **Constructing the metric** — decomposition, bias probes, calibration receipts: that is `[[agentsop-metric-design]]`.
  This skill only checks the receipt exists.
- **Non-DSPy auto-optimization** — e.g. OpenAI fine-tuning is a *weights* path, not prompt compilation; the
  readiness logic (metric + data floor) still applies but the operators differ (§7).

---

## 7. 跨框架对照 (Cross-Framework Mapping)

The readiness *gate* (metric + data floor) is framework-agnostic; the *operators* differ.

| Concept | DSPy optimizers | Manual few-shot tuning | OpenAI fine-tuning |
|---|---|---|---|
| What is optimized | prompt instructions + demos (and optionally weights via `BootstrapFinetune`) | the prompt string, by hand | model weights |
| Metric required? | **Yes** — `metric(ex, pred) -> bool\|float` drives the search | implicit / eyeballed (the failure mode) | a held-out eval set + loss; eval suite recommended |
| Example floor | ~10 (GEPA+feedback) / ~30 (Bootstrap) / 200+ (MIPROv2) | none, but no guarantees | OpenAI guidance: ~50–100+ examples minimum, more is better |
| Cost shape | `num_trials × |trainset| × calls` ($2–$40+) [dspy.ai/faqs/] | human time | GPU/training-token cost + per-token inference savings |
| Readiness gate (this skill) | both gates apply directly | Gate 1 is exactly what's missing — you're "tuning" with no validated metric | both gates apply; "metric validated" = your eval set is trustworthy |
| When to prefer | metric + ≥10 examples + want a portable, recompilable artifact | one-shot, unstable contract, or audit-mandated verbatim prompts | task is stable, latency/cost matters at high volume, prompt optimization plateaued |

**Decision summary**: If you have a *validated metric* and *examples clearing a floor*, **compile** (DSPy). If you
have a metric but it's never been validated, you are doing **manual tuning dressed up** — close Gate 1 first. If
prompt optimization has plateaued *and* you have hundreds of stable examples *and* volume justifies it, consider
**fine-tuning** (or `BootstrapFinetune` to distill an already-compiled program into a smaller model).

**Combination patterns:**
- **prompt-compilation + `[[agentsop-metric-design]]`**: this skill's Gate 1 is satisfied by a `[[agentsop-metric-design]]`
  calibration receipt. No receipt → gate closed.
- **prompt-compilation + `[[agentsop-dspy]]`**: this overlay is the sharpened version of `[[agentsop-dspy]]` §3 Stage 2→3
  transition (the "are you allowed to compile yet?" boundary). After the gate opens, hand off to `[[agentsop-dspy]]` for
  the full compile/save/deploy workflow.
- **prompt-compilation + `[[dspy]]`**: `[[dspy]]` provides the optimizer APIs; this skill decides *whether* and
  *which*.

---

## References

- `references/R1-source-evidence.md` — every claim traced to the local `dspy-sop` skill and the upstream DSPy docs it cites; overlap check vs `[[dspy]]` and `[[agentsop-metric-design]]`.
- `intermediate/operation_candidates.json` — the 8 operations + tables in machine-readable form.

**Citations**: [dspy.ai/learn/optimization/overview/], [dspy.ai/learn/optimization/optimizers/],
[dspy.ai/api/optimizers/MIPROv2/], [dspy.ai/api/optimizers/GEPA/overview/], [dspy.ai/api/optimizers/BootstrapFinetune/],
[dspy.ai/learn/evaluation/metrics/], [dspy.ai/faqs/], [dspy.ai/cheatsheet/], [dspy.ai/tutorials/gepa_ai_program/],
[arxiv.org/abs/2310.03714], [arxiv.org/abs/2507.19457], [arxiv.org/pdf/2506.02592],
[github.com/stanfordnlp/dspy/issues/1596]. Primary source:
`/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`.
