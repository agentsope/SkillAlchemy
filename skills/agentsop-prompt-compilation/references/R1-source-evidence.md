# R1 — Source evidence for `prompt-compilation`

Each claim `S1`–`S10` cited in `SKILL.md` is grounded below. Primary source is the local
`dspy-sop-skill/SKILL.md` (which itself cites upstream DSPy docs and papers); secondary sources are the upstream
URLs that skill quotes. This overlay adds **no new library facts** — it re-frames existing facts into a *compile-
readiness gate*, so every factual claim traces to material already in the local `dspy-sop` skill.

Provenance of primary source: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`.

---

## S1 — A bad program/metric makes optimization unproductive (the gate's reason to exist)

> "It's unproductive to launch optimization runs using a poorly designed program or a bad metric."

- Source: `dspy-sop-skill/SKILL.md` §3, quoting [dspy.ai/learn/].
- Use in overlay: the core mental model, Gate 1, and the entire framing of compilation as a *gate* not a step.

## S2 — The optimizer maximizes the metric; a bad metric becomes a bad program at scale

> "DSPy will optimize toward whatever the metric rewards. A bad metric becomes a bad program at scale."

- Source: `dspy-sop-skill/SKILL.md` §5 Case C, constraint bullet.
- Use in overlay: "garbage metric in, garbage prompt out" mental model; AP-1, AP-2.

## S3 — Compilation is an expensive hyperparameter search (the cost the gate protects)

> "Compile is a hyperparameter search, not a one-shot call. Compilation runs hundreds-to-thousands of LM calls
> (typically $2–$3 USD, 6–20 minutes, 3.2k API calls in the reference run). Costs scale with
> `num_trials × |trainset| × |program LM calls|` [dspy.ai/faqs/]."

- Source: `dspy-sop-skill/SKILL.md` §2, mental shift #3.
- Use in overlay: §2 "cost reality", §3 Step 4 Budget, OP-6 CostBudgetGuard, §4.4 cost table.

## S4 — Data thresholds: 30 minimum / 300 recommended / 200+ for MIPROv2

> "Documented sweet spot: **30 examples = minimum useful, 300 = recommended, 200+ required for MIPROv2** to avoid
> overfitting [dspy.ai/learn/optimization/overview/]."

- Source: `dspy-sop-skill/SKILL.md` §3 Stage 2 step 5.
- Use in overlay: Gate 2, OP-4 ExampleFloorCheck, §4.2 table, AP-3.

## S5 — Prompt-based optimizers overfit small training sets (why the floor is hard)

> "Below ~30 examples, you're not training — you're memorizing. The 20/80 train/val split exists *because*
> 'prompt-based optimizers often overfit to small training sets' [dspy.ai/learn/optimization/overview/]."

- Source: `dspy-sop-skill/SKILL.md` §6 anti-pattern #2 and #9.
- Use in overlay: Gate 2 framing as a hard floor; AP-3; readiness checklist 20/80 note.

## S6 — Optimizer-by-data-scale ladder

> "≤10 labeled examples → `BootstrapFewShot`; 30–50 → `BootstrapFewShotWithRandomSearch`; 200+ → `MIPROv2`; …
> `LabeledFewShot(k=8)` — Trivial — fastest, cheapest, weakest."

- Source: `dspy-sop-skill/SKILL.md` §4.1 optimizer table and the §-appendix decision tree.
- Use in overlay: §4.2 optimizer-by-data-scale table, OP-5 OptimizerByDataScale.

## S7 — GEPA needs textual feedback and is sample-efficient (the data-scale inversion)

> "Have textual error feedback (test diffs, schema violations, judge rationales) → `dspy.GEPA(metric=m_with_feedback)`
> → Reflection-evolved prompts; sample-efficient [dspy.ai/tutorials/gepa_ai_program/], [arxiv.org/abs/2507.19457]."

and

> "If sub-judge feedback is rich (e.g. 'answer was verbose'), pipe textual feedback into `dspy.GEPA` … GEPA leverages
> text feedback for faster, more sample-efficient convergence."

- Source: `dspy-sop-skill/SKILL.md` §4.1 optimizer table; §4.3 metric table; §5 Case C step 5.
- Use in overlay: Dilemma 2 (GEPA inverts the data-scale assumption), §4.2 GEPA row, OP-5, AP-7. The "~10 examples
  suffice with textual feedback" framing is the task-given source claim, consistent with this skill's GEPA row.

## S8 — Never start at `auto="heavy"`; probe `light` first; escalate only on gains

> "Run **`auto="light"` first** as a cheap signal. The docs explicitly recommend 'start with moderate values,
> observe behavior, and scale up only if you see clear gains' [github.com/stanfordnlp/dspy issue #1596]."
> … "If `light` gives <2% lift, do **not** escalate to `heavy`. Instead, revisit Stage 1."

- Source: `dspy-sop-skill/SKILL.md` §5 Case A decision steps 2–4; §6 anti-pattern #5.
- Use in overlay: §3 Step 5/6, OP-7 CheapProbeFirst, OP-8 EscalateOrReturn, AP-4, AP-5, Dilemma 1.

## S9 — Use a cheap optimizer LM even when the task LM is expensive

> "Use a **cheap optimizer LM** (e.g. gpt-4o-mini) to optimize prompts for a more expensive task LM —
> community-reported parity [github.com/stanfordnlp/dspy/issues/1596]."

- Source: `dspy-sop-skill/SKILL.md` §4.4 cost guardrails; §5 Case A step 5.
- Use in overlay: §3 Step 4, OP-6 CostBudgetGuard, AP-6, Dilemma 1 step 5.

## S10 — Compile only after the I/O contract stabilizes; never compile without a metric

> "The team is in *rapid exploration* mode where the task signature itself is changing daily — compile only after
> the signature stabilizes." and "Compiling without a metric. … the optimizers *require* a metric. If you cannot
> write a metric, you cannot optimize, period [dspy.ai/learn/optimization/overview/]."

- Source: `dspy-sop-skill/SKILL.md` §1 "Do NOT activate"; §6 anti-pattern #1; Boundaries.
- Use in overlay: §1 Do-NOT-activate, AP-1, AP-9, Boundaries.

## S11 — Human-validate the metric on ≥20 spot-checks before compiling

> "Spot-check the metric on 20 examples with a human judge first. … Never compile against a metric you haven't
> human-validated on ≥ 20 spot-checks. … Garbage metric → garbage compiled program."

- Source: `dspy-sop-skill/SKILL.md` §5 Case C steps 4 and 可提取的操作.
- Use in overlay: Gate 1, OP-3 MetricValidatedCheck, readiness checklist, AP-2.

## S12 — Confirm the gain on a held-out test set, not the optimization val set

> "Exit criterion: compiled program beats baseline on a *held-out* test set (not the val set used in optimization)."

- Source: `dspy-sop-skill/SKILL.md` §3 Stage 3 exit criterion.
- Use in overlay: §3 Step 6, OP-8, AP-8.

---

## Overlap check vs the local `[[dspy]]` library skill and `[[agentsop-metric-design]]`

This overlay deliberately holds **only the decision layer**:

- **Defers to `[[dspy]]` / `[[agentsop-dspy]]`**: optimizer class syntax, `compile()` arguments, Signature/module
  authoring, save/load, deployment, the compile-hang debugging case. None of that is restated here — it would
  duplicate the library skill.
- **Defers to `[[agentsop-metric-design]]`**: how to *build* a metric — decomposition, bias probes (length / self-preference
  / position / rubric-order), bool-during-compile/float-during-eval, calibration receipts. This overlay only
  *checks the receipt exists* (Gate 1 / OP-3) and uses the metric as a gate; it does not re-teach metric construction.
- **Net-new framing (the reason this overlay exists)**: collapsing the scattered facts above into a single **two-gate
  readiness check** (metric-validated AND examples-clear-floor) that must pass *before* any optimizer compute is
  spent — plus the explicit "GEPA inverts the data-scale floor" branch. The library skill states all the pieces but
  never presents them as a single go/no-go gate.

## Cross-framework claim (S13) — manual few-shot vs OpenAI fine-tuning

The §7 cross-framework table's DSPy column is fully grounded above (S3–S9). The manual-few-shot column reflects S2
(eyeballed/implicit metric = the failure mode) and S10. The OpenAI fine-tuning column is general public guidance
(fine-tuning is a *weights* path requiring a held-out eval set; commonly ~50–100+ examples as a practical minimum) —
flagged as framework-general, not sourced from the local `dspy-sop` skill, and used only to contrast *operators*; the
readiness *gate logic* (metric + data floor) is the sourced, transferable part.
