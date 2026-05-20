---
name: agentsop-domain-eval-set
version: 0.1.0
phase: D
tier: core
frequency: high
status: opinionated
overlay: ENHANCE
description: Build and govern a 50-200 example domain-specific held-out benchmark sampled from real traffic. Distinct from public benchmarks (MMLU/HumanEval/GSM8K via lm-evaluation-harness) which measure GENERAL capability. Only a held-out domain set predicts whether THIS system works on YOUR data. Collect real examples, label, hold out (never train/prompt on it), size 50-200, version it, refresh on drift.
---

# domain-eval-set — Your Held-Out Domain Benchmark

> "Compiled program beats baseline on a *held-out* test set (not the val set used in optimization)."
> — DSPy SOP exit criterion [dspy.ai/learn/optimization/overview/]

> "Build the eval loop **before** optimizing anything. Every subsequent change must be gated on these numbers."
> — LlamaIndex SOP Stage 2

This is an **ENHANCE overlay** skill. It produces one artifact — a versioned,
sealed, human-labeled set of 50–200 examples drawn from *your* domain — that
other skills consume: `[[agentsop-regression-gate]]` enforces it on every PR,
`[[agentsop-metric-design]]` defines the scoring function applied to each example, and
`[[lm-evaluation-harness]]` runs the *complementary* public-capability axis. The
core claim: **public benchmarks tell you the model is smart in general; only a
held-out domain set tells you it works on your task.** The latter is the one that
predicts production.

---

## 1. 何时激活 (When to Activate)

Activate when **any** of these is true:

- **"Does THIS system work on OUR data?"** — someone is about to ship or trust an
  LLM/RAG/agent system and the only evidence is vibes, a demo, or a public
  benchmark number. You need a quantitative answer on the real distribution.
- **A public-benchmark number is being used as a deployment gate.** Someone cites
  "92% on MMLU" or "passes HumanEval" to justify go-live. That measures general
  capability, not your task fit (AP-1). Force a domain set into the decision.
- **A model / prompt / retriever / chunking change needs a regression gate** and
  no domain test set exists yet to gate against. You must build the set before
  `[[agentsop-regression-gate]]` can do its job.
- **Switching models** (GPT-4o → a cheaper or local model). The public-bench gap
  may be small while the domain gap is large, or vice versa. Only your held-out
  set tells you which.
- **Production complaints don't match your eval scores.** Either the set is stale
  (refresh, OP-DE06) or it never reflected the domain (rebuild from real traffic).

**Do NOT activate for:**

- **Pure capability comparison / academic reporting.** "Which model is best at
  MMLU/GSM8K?" → that is `[[lm-evaluation-harness]]`, not this skill.
- **One-off throwaway prototypes** where no decision rides on quality and nothing
  ships. Don't build a benchmark for a script you'll delete tomorrow.
- **Tasks with an objective oracle already** (compiler passes, exact DB match,
  schema validity gives ≥95% of signal) — the "eval set" is just running the
  oracle; you don't need curated held-out examples. Don't gold-plate.

---

## 2. 核心心智模型 (Core Mental Model)

### **"Public benchmarks measure general capability. A 50–200 example held-out domain set measures YOUR task. Only the latter predicts production."**

Two orthogonal axes, constantly confused:

| Axis | What it measures | Tool | Predicts production? |
|---|---|---|---|
| **General capability** | Reasoning, knowledge, coding *in general*, on shared public tasks | `[[lm-evaluation-harness]]` (MMLU, HumanEval, GSM8K, TruthfulQA) | **No** — a proxy at best |
| **Domain task fit** | Whether the system answers *your* users on *your* data | this skill (held-out domain set) | **Yes** — this is the signal |

A model can score 90% on MMLU and 40% on your insurance-claims triage. A model
can score *below* SOTA on HumanEval and be perfect at your internal codebase's
patterns. The public number and the domain number are nearly uncorrelated once
you're past a basic capability floor. **The public bench is a sanity check; the
domain set is the decision.**

Three corollaries (each maps to an SOP stage):

1. **Real beats synthetic.** The set is sampled from *real* domain traffic
   (tickets, queries, logs, transactions), stratified, with edge cases pulled
   deliberately. Auto-generated QA pairs (LlamaIndex `DatasetGenerator`) are a
   fine *bootstrap*, but a model can ace generated questions and still fail real
   user phrasing. Generated sets do not replace a real held-out set (§7).

2. **Held out means SEALED.** The held-out split is never shown to the optimizer,
   never pasted into a prompt as a few-shot demo, never used to pick chunk size
   or reranker, never in the fine-tune data. The moment it leaks, the number is
   inflated and meaningless (AP-2, OP-DE07). Per DSPy: the test set must be
   *distinct from the val set used in optimization* [dspy.ai/learn/optimization/overview/].

3. **Small but significant.** 50–200 examples. Below ~30 you are "memorizing, not
   training" [dspy.ai/learn/optimization/overview/] and differences are noise. The
   set is small enough to label by hand and large enough to detect ~5–10pp
   regressions and to slice by segment.

---

## 3. SOP (Standard Operating Procedure)

```
0. Confirm activation (§1) — is the question "does this work on OUR data"?
1. COLLECT  — sample real domain examples; stratify; pull edge cases       (OP-DE01)
2. LABEL    — gold answer / reference / pass-fail; 2 annotators on subset  (OP-DE02)
3. HOLD OUT — split train/dev/test; SEAL the test split                    (OP-DE03)
4. SIZE     — land at 50-200; per-segment counts                           (OP-DE04)
5. VERSION  — hash + date + rubric; freeze as an artifact                  (OP-DE05)
6. LEAK-AUDIT — diff held-out vs demos / train / fine-tune data            (OP-DE07)
7. PAIR     — report alongside public bench; gate on the domain set        (OP-DE08)
   (later) REFRESH on domain shift                                         (OP-DE06)
```

### Stage 1 — Collect from real traffic

Pull from where the real distribution lives: support tickets, search/query logs,
user transcripts, transaction records, bug reports. **Stratify** so the set
covers the production mix — by query type (lookup / summary / compare), by
segment (tenant, language, product area), by difficulty. Then **deliberately
over-sample edge cases and known failures** — the head of the distribution is
easy; the tail is where systems break.

Target a raw pool ≥ 2× the final size (you'll drop ambiguous items in labeling).
Record provenance and timestamp per example (needed later for drift refresh).

**Exit:** a candidate pool ≥ 2× target, with provenance, spanning the real mix.

### Stage 2 — Label and curate

Attach ground truth per example: a gold answer, an *acceptable reference*
response (not "the unique correct" one for open-ended tasks — see
`[[agentsop-metric-design]]`), or a pass/fail label. For RAG, **also label the gold
passage** so `RetrieverEvaluator(["mrr","hit_rate"])` can run [LlamaIndex OP-10].

Have **two annotators label a subset**, measure agreement, resolve disagreements,
and **drop genuinely ambiguous items** — an example two experts can't agree on
will only add noise. Record the rubric. (This is the data-side analogue of DSPy's
"human-validate the metric on ≥20 spot-checks" discipline [DSPy Case C].)

**Exit:** labeled set with inter-annotator agreement noted, rubric recorded,
ambiguous items logged as rejected.

### Stage 3 — Hold-out discipline (the load-bearing stage)

Split into **train / dev / test**. The **test (held-out) split is sealed**:

- NEVER shown to an optimizer (DSPy trainset, MIPRO/GEPA).
- NEVER pasted into a prompt as a few-shot demo.
- NEVER used to pick chunk size / reranker / hybrid alpha / model.
- NEVER in fine-tune data.

Store it in a separate file/location with an access note. Per DSPy, the
exit-gate test set must be "distinct from the val set used in optimization"
[dspy.ai/learn/optimization/overview/]. The dev split is what you tune against;
the test split is the one number you trust at decision time.

**Exit:** sealed held-out test split + train/dev splits; access policy written.

### Stage 4 — Size for 50–200

- **50** — minimum for a coarse production go/no-go signal.
- **100–200** — stable enough to detect ~5–10pp regressions and to slice per
  segment (each slice needs its own ≥~30 to be meaningful).
- **<30** — do not bother gating on it; the variance swamps the signal
  [dspy.ai/learn/optimization/overview/].

Size **up** (toward 200, or split into per-segment sets each ~50) when you need
per-segment confidence. LlamaIndex's `DatasetGenerator` default of `num=50` sits
at the low end of this band — fine to bootstrap, then curate.

### Stage 5 — Version it

Freeze the set as a **versioned artifact** — `eval_v1.jsonl` plus a manifest with
a content **hash**, **creation date**, and the **labeling rubric**. Score every
model / prompt / retriever change against the *same* version; keep a results
table keyed by `(eval_version, system_version)`; bump only on a deliberate
refresh, never silently. DSPy ships `program.json` as a versioned artifact
[dspy.ai/tutorials/saving/]; LlamaIndex versions indices as deployment artifacts
(SOP Stage 5) — the eval set deserves the same rigor.

### Stage 6 — Leak audit

Before any release, and whenever few-shot demos or fine-tune data are assembled,
**diff the held-out set** against (a) prompt few-shot demos, (b) fine-tune /
training data, (c) the optimizer trainset. Any overlap = contamination → the
held-out number is inflated and worthless (AP-2). Remove the overlap or rebuild
the split — the same provenance discipline as `[[agentsop-metric-design]]`'s calibration
receipt (OP-M10).

### Stage 7 — Pair with the public bench, gate on the domain set

Run `[[lm-evaluation-harness]]` for the **capability floor** (sanity check: is the
model fundamentally competent?). Run the domain held-out set for the **decision**.
Report both side by side. **If they disagree, the domain set wins the go/no-go.**
Hand the sealed set to `[[agentsop-regression-gate]]` to enforce on every subsequent PR.

### Refresh — when the domain shifts

Domains drift: new product line, new user segment, seasonal change. When held-out
scores stop tracking production complaints, **refresh** (OP-DE06): add fresh real
examples from recent traffic, retire stale ones, re-label edge cases production
surfaced, bump the version, keep the old version for back-comparison. Cadence:
quarterly *or* on any major domain change, whichever comes first. (This mirrors
LlamaIndex's live-corpus reconciliation, A10.)

---

## 4. 操作模型 (Operations)

Each operation: **Trigger → Action → Output [Evidence]**. Full Trigger/Action/
Output/Evidence form in `intermediate/operation_candidates.json`.

- **OP-DE01 SourceFromRealTraffic** — No curated set, traffic available → sample
  real inputs (logs/tickets/queries/transactions), stratify by type/segment/
  difficulty, over-sample edge cases → raw pool ≥2× target with provenance.
  [DSPy dev-set discipline; LlamaIndex OP-10 eval-from-corpus]

- **OP-DE02 LabelAndCurate** — Raw pool collected → attach gold/reference/pass-fail
  per item; two annotators on a subset, resolve disagreement, drop ambiguous,
  record rubric; for RAG label the gold passage → curated labeled set with
  agreement noted. [DSPy Case C ≥20 spot-checks; LlamaIndex `RetrieverEvaluator`]

- **OP-DE03 HoldOutDiscipline** — Set about to be used → split train/dev/test; seal
  the test split (never to optimizer, never as few-shot demo, never to pick
  chunking/reranker/model, never in fine-tune data) → sealed test + train/dev.
  [DSPy "held-out distinct from val"; Case A step 4]

- **OP-DE04 SizeFor50to200** — Deciding size → target 50–200 (50 = coarse signal;
  100–200 = detect ~5–10pp regressions + per-segment slices; <30 = noise) → sized
  set with per-segment counts. [DSPy "30 min, 200+ for MIPROv2"; LlamaIndex num=50]

- **OP-DE05 VersionTheSet** — Set finalized → freeze as `eval_v1.jsonl` + manifest
  (hash, date, rubric); score every change vs the same version; results keyed by
  `(eval_version, system_version)`; bump only on deliberate refresh → versioned
  artifact. [DSPy `program.json` versioning; LlamaIndex versioned indices]

- **OP-DE06 RefreshOnDomainShift** — Domain drifts; scores stop tracking complaints
  → add fresh recent-traffic examples, retire stale, re-label edge cases, bump
  version, keep old for comparison (quarterly or on major change) → new version +
  drift log. [LlamaIndex live-corpus reconciliation A10]

- **OP-DE07 LeakAudit** — Before release / when demos or fine-tune data assembled →
  diff held-out vs few-shot demos, fine-tune data, optimizer trainset; any overlap
  = contamination → remove or rebuild → leak-audit report (0 overlap). [DSPy
  held-out-distinct rule; metric-design provenance OP-M10]

- **OP-DE08 PairWithPublicBench** — Public-bench number used to justify deployment →
  treat public bench as capability floor/sanity check, require the domain held-out
  set as the decision gate; report both, on disagreement the domain set wins →
  two-axis report gated on domain. [`[[lm-evaluation-harness]]` covers public, not
  your domain]

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — "We don't have enough labeled domain data to build a held-out set"

**困境**: A team wants to ship a contract-review assistant. They have thousands of
raw contracts but only ~25 examples a lawyer has labeled with gold answers.
25 < the 50 floor and well below the 30 "memorizing, not training" line
[dspy.ai/learn/optimization/overview/]. They're tempted to (a) skip the held-out
set and ship on MMLU/legal-bench numbers, or (b) auto-generate 200 QA pairs with
LlamaIndex `DatasetGenerator` and call that the held-out set.

**约束**: Lawyer labeling time is the bottleneck (~$$/hour, scarce). Public legal
benchmarks exist but don't reflect this firm's contract templates. Auto-generated
questions risk testing "what the corpus says" rather than "what real reviewers
ask".

**决策步骤**:
1. **Refuse to gate on the public bench alone** (AP-1). A legal-bench number is a
   capability floor, not proof the assistant handles *these* contracts.
2. **Use auto-generation to bootstrap the DEV set, never the held-out test set.**
   `DatasetGenerator` (LlamaIndex Stage 2) gives a cheap dev set for iteration —
   but it is synthetic, so it cannot be the trusted held-out number (§7 caveat).
3. **Spend the scarce labeling budget on the held-out set, not the dev set.** Have
   the lawyer label the *50 hardest real examples* (stratified, edge-case-heavy,
   OP-DE01/02) rather than 200 easy generated ones. 50 real-labeled > 200
   synthetic for the decision gate.
4. **Two-annotator a subset** (OP-DE02) so you trust the gold labels; drop the
   ambiguous ones rather than padding the count.
5. **Seal those 50** (OP-DE03), version them (OP-DE05). Iterate against the
   synthetic dev set; report the go/no-go on the 50 real held-out.
6. **Grow it on real traffic** post-launch (OP-DE06) — pilot usage is the cheapest
   source of new labeled examples.

**结果**: A 50-example human-labeled, sealed held-out set built from the hardest
real contracts predicts production far better than 200 synthetic questions or any
public legal benchmark. The synthetic set still earns its keep — as the dev set
you tune against, never as the number you trust.

**可提取的操作**: `OP-DE01`, `OP-DE02`, `OP-DE03`, `OP-DE04`. **Lesson: spend scarce
labels on a small REAL held-out set; let synthetic generation cover the dev set;
never let a public bench be the gate.**

### Dilemma 2 — "Our eval set went stale; scores are green but production is on fire"

**困境**: A support-triage classifier shows 0.91 on `eval_v1` (built 9 months ago)
and every PR passes `[[agentsop-regression-gate]]`. Yet production accuracy collapsed and
users are escalating. The eval set says everything is fine.

**约束**: `eval_v1` is versioned and trusted; nobody wants to "move the goalposts".
The domain shifted — a new product line generates a third of current tickets, and
none of those ticket types existed when `eval_v1` was built. Rebuilding costs
annotator time.

**决策步骤**:
1. **Diagnose drift, not regression.** Slice production traffic by ticket type and
   compare against `eval_v1`'s segment counts. The new product line is ~33% of live
   traffic and **0%** of the eval set → the eval set no longer represents the
   domain. The green score is measuring an obsolete distribution.
2. **Do NOT just lower the threshold** — the metric isn't wrong, the *data* is
   stale. (Compare metric-design AP-8: changing the yardstick mid-stream without
   re-grounding.)
3. **Refresh** (OP-DE06): sample recent real tickets — especially the new product
   line and recent escalations — label them, retire ticket types that no longer
   occur, and build `eval_v2`.
4. **Bump the version** (OP-DE05), keep `eval_v1` for back-comparison. Re-score the
   current system on `eval_v2`: it drops to 0.63 — now matching reality.
5. **Re-gate** `[[agentsop-regression-gate]]` on `eval_v2`. Add a **drift check** to the
   refresh cadence: quarterly, compare live segment mix vs eval segment mix; if any
   segment drifts >X%, trigger a refresh.

**结果**: The "green-but-on-fire" gap was a stale held-out set, not a model
regression. A versioned refresh (`eval_v2`) restored the eval as a true production
predictor; the back-comparison against `eval_v1` documented exactly how much the
domain moved.

**可提取的操作**: `OP-DE06 RefreshOnDomainShift`, `OP-DE05 VersionTheSet`. **Lesson:
a held-out set is a snapshot of a moving distribution. Schedule drift checks; an
old green score can be the most dangerous number you have.**

---

## 6. 反模式与边界 (Anti-Patterns & Boundaries)

### Anti-patterns

| # | Anti-pattern | Why it's wrong | Fix |
|---|---|---|---|
| AP-1 | **Public bench as proxy for domain performance** ("92% MMLU → ship it") | Public benches measure *general capability*; near-uncorrelated with task fit past a floor | Build a domain held-out set; gate on it (`OP-DE08`) |
| AP-2 | **Eval set leaks into prompt / training / trainset** | Held-out number is inflated and meaningless; you're testing on the train set | Seal it; leak-audit before release (`OP-DE03`, `OP-DE07`) |
| AP-3 | **Set too small to be significant** (<30 examples) | "Memorizing, not training" [dspy.ai/learn/optimization/overview/]; variance swamps signal | Target 50–200 (`OP-DE04`) |
| AP-4 | **Synthetic-only held-out** (auto-generated QA *is* the test set) | Tests "what the corpus says", not real user phrasing; flatters the system | Synthetic = dev set bootstrap only; real-labeled = held-out (§7, Dilemma 1) |
| AP-5 | **Never refreshing** as the domain drifts | Green scores on an obsolete distribution; "green but on fire" (Dilemma 2) | Schedule drift checks; refresh + version (`OP-DE06`) |
| AP-6 | **Unversioned set silently edited** | Can't compare across system versions; results table is meaningless | Hash + date + rubric; bump on deliberate refresh (`OP-DE05`) |
| AP-7 | **No stratification / edge cases** (only easy head-of-distribution) | Passes eval, fails the tail where systems actually break | Stratify by segment/type; over-sample edge cases (`OP-DE01`) |
| AP-8 | **Tuning chunk size / reranker / model against the held-out set** | That makes it a val set, not held-out; the trust is gone | Tune on dev; touch held-out only at decision time (`OP-DE03`) |

### Boundaries (when this skill is the wrong tool)

- **You only need general capability comparison / academic reporting.** "Which
  model is best at reasoning?" → `[[lm-evaluation-harness]]` (MMLU/GSM8K/etc.),
  not this skill. This skill is for *your* task, not the leaderboard.
- **An objective oracle already exists** (compiler passes, exact DB match, schema
  validity gives ≥95% of signal). The "eval set" is just running the oracle on
  inputs — you don't need curated human-labeled held-out examples. Don't
  gold-plate.
- **Nothing ships and no decision rides on quality** (throwaway prototype). The
  cost of building and labeling a real set has no payoff.
- **You have zero access to real domain data and no path to any** (pre-product,
  cold start). Bootstrap with synthetic + public benches transparently, label
  *as soon as* pilot traffic appears, and treat early numbers as provisional.
- **Scoring each example is itself the hard part** (open-ended generation, no
  reference answer) — building the *set* is necessary but not sufficient. Pair
  with `[[agentsop-metric-design]]` to define a defensible, calibrated scoring function.

---

## 7. 跨框架对照 (Cross-Framework Mapping)

When does each kind of eval set apply? They are **complementary axes**, not
substitutes — a mature pipeline uses all three.

| Concept | Held-out domain set (this skill) | `[[lm-evaluation-harness]]` (public) | LlamaIndex `DatasetGenerator` (synthetic) |
|---|---|---|---|
| **What it measures** | Task fit on *your* data | General capability | Coverage of *your corpus's* content |
| **Data source** | Real traffic, human-labeled | Public academic datasets (MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag) | LLM-generated QA from your docs |
| **Size** | 50–200 | thousands (fixed by benchmark) | arbitrary (default `num=50`) |
| **Contamination risk** | You control it (leak-audit) | High — public benches leak into pretraining | Low (your private corpus) but synthetic |
| **Predicts production?** | **Yes** (the decision gate) | No (capability floor / sanity check) | Partially (dev-set iteration, not the gate) |
| **When to use** | Go/no-go on shipping to *your* users; per-PR regression gate | Model selection on raw capability; academic reporting; training-progress tracking | Bootstrap a dev set fast before you've labeled real data |
| **Invocation** | `eval_vN.jsonl` + scoring fn from `[[agentsop-metric-design]]` | `lm_eval --tasks mmlu,gsm8k,...` | `DatasetGenerator.from_documents(docs).generate_dataset_from_nodes(num=50)` |

**Decision rubric:**

```
Q1. Are you deciding whether to SHIP / SWITCH on YOUR users' data?
    YES → held-out domain set is the gate (this skill). Public bench = sanity check only.
Q2. Are you comparing raw model capability or reporting academic numbers?
    YES → lm-evaluation-harness (MMLU/HumanEval/GSM8K). Not this skill.
Q3. Do you have NO real labeled data yet but a corpus exists?
    YES → DatasetGenerator to bootstrap a DEV set; label real held-out as soon as traffic appears.
Q4. Is there an objective oracle (tests/schema/exact-match)?
    YES → run the oracle; no curated set needed.
DEFAULT → build + version a 50-200 real held-out set; gate via [[agentsop-regression-gate]];
          score via [[agentsop-metric-design]]; pair with [[lm-evaluation-harness]] for the floor.
```

**Combination patterns:**

- **this skill + `[[agentsop-regression-gate]]`**: this skill *produces* the sealed,
  versioned set; regression-gate *enforces* it on every PR (chunking / embedding /
  prompt / model change). Division of labor: produce vs enforce.
- **this skill + `[[agentsop-metric-design]]`**: this skill defines *what's in the set*;
  metric-design defines *how each example is scored* (decomposed sub-judges,
  bool-during-compile/float-during-eval, human-calibrated, length-penalized).
  A set with no defensible scoring function is half a benchmark.
- **this skill + `[[lm-evaluation-harness]]`**: report both axes side by side
  (OP-DE08). Public bench answers "is the model competent?"; the domain set
  answers "does it work for us?". On disagreement, the domain set wins go/no-go.
- **this skill + DSPy**: the held-out test split is the DSPy exit-gate set —
  "compiled program beats baseline on a *held-out* test set (not the val set)"
  [dspy.ai/learn/optimization/overview/]. The DSPy trainset/valset come from the
  *non-held-out* splits.

**Opinionated default**: build the held-out set in plain `jsonl` (transparent,
diffable, hashable), label it with humans on the hardest real examples, seal it,
version it, and treat the public-benchmark number as a sanity check you report
but never gate on.

---

## References

- `references/R1-source-evidence.md` — verbatim source quotes (DSPy held-out
  discipline, LlamaIndex eval-loop, lm-evaluation-harness public scope)
- `intermediate/operation_candidates.json` — 8 operations in Trigger / Action /
  Output / Evidence form

**Cross-links**: `[[lm-evaluation-harness]]` (public-benchmark axis),
`[[agentsop-regression-gate]]` (per-PR enforcement), `[[agentsop-metric-design]]` (scoring function).

**Citations**: [dspy.ai/learn/optimization/overview/], [dspy.ai/learn/optimization/optimizers/], [dspy.ai/learn/evaluation/metrics/], [dspy.ai/tutorials/saving/], [developers.llamaindex.ai/python/framework-api-reference/evaluation/], [llamaindex.ai/blog/evaluating-the-ideal-chunk-size-for-a-rag-system-using-llamaindex-6207e5d3fec5], `~/.claude/skills/lm-evaluation-harness/SKILL.md`.
