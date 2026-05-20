# prompt-compilation skill

An **enhancement-overlay** coder skill that surfaces one decision the broad `[[dspy]]` library skill buries under
its API surface: **have you earned the right to run a prompt optimizer yet, and which one?**

**Version**: 0.1.0
**Layer**: enhance overlay (decision rubric only — defers all implementation to `[[dspy]]`, `[[agentsop-dspy]]`, `[[agentsop-metric-design]]`)

## What this skill answers

- **The compile-readiness gate**: two hard preconditions before any optimizer compute is spent —
  1. a **metric** that exists *and* is human-validated (≥20 spot-checks), and
  2. **enough labeled examples** for the optimizer you intend to run.
- **Which optimizer** by data scale: `LabeledFewShot` (<10) / `GEPA` (~10+ with textual feedback) /
  `BootstrapFewShot` (~30–50) / `MIPROv2` (200+).
- **The GEPA inversion**: textual feedback (test diffs, schema violations, judge rationales) lets ~10 examples
  suffice — the "you need 200 examples" rule is specific to scalar-feedback optimizers.
- **Cost discipline**: probe `auto="light"` first, never start at `heavy`, use a cheap optimizer LM, escalate only
  on ≥2% lift, confirm on a held-out test set.

## What this skill does NOT do

It is **not** a DSPy tutorial and not a metric-construction guide. It defers:

- **`[[dspy]]`** — the library skill (HOW to write a Signature / module / `compile()`).
- **`[[agentsop-dspy]]`** — the full operating workflow (program → evaluate → optimize, save, deploy).
- **`[[agentsop-metric-design]]`** — building, decomposing, bias-probing, and calibrating the metric. This overlay only
  *checks the metric exists and is validated*, then uses it as the gate.

This overlay is the sharpened "are you allowed to compile yet?" boundary inside `[[agentsop-dspy]]` §3 (Stage 2 → Stage 3).

## The mental model

> "Compile when you can measure. The optimizer maximizes your metric — garbage metric in, garbage prompt out."

An optimizer is a black-box search with no taste. It chases whatever the metric rewards, biases and all. So the
metric and the example count are *preconditions*, not tunables — hence a **gate**, not a step.

## Files

- `SKILL.md` — main skill, 7 sections: 何时激活 / 核心心智模型 (two-gate picture) / SOP (Gate 1 metric → Gate 2 data
  → pick → budget → probe → decide) / 操作模型 (8 ops + optimizer-by-data-scale table + readiness checklist + cost
  budget) / 困境决策案例 (2: optimizer cost-vs-gain; GEPA inverts the data-scale assumption) / 反模式与边界 / 跨框架对照
  (DSPy optimizers vs manual few-shot vs OpenAI fine-tuning).
- `references/R1-source-evidence.md` — every claim traced to the local `dspy-sop` skill and the upstream DSPy docs
  it cites; overlap check vs `[[dspy]]` and `[[agentsop-metric-design]]`.
- `intermediate/operation_candidates.json` — the 8 operations in Trigger / Action / Output / Evidence form, plus the
  optimizer table, dilemma cases, and anti-patterns.

## Quick start

To decide one pipeline today:

1. **Gate 1 — metric**: does a `metric(ex, pred) -> bool|float` exist, validated against a human on ≥20 spot-checks
   at ≥80% agreement? No → STOP, route to `[[agentsop-metric-design]]`.
2. **Gate 2 — data**: count labeled examples; is it above the floor of the optimizer you want? (GEPA ~10 + textual
   feedback / Bootstrap ~30–50 / MIPROv2 200+.) No → drop to a lower-floor optimizer or collect data.
3. Both gates pass → probe `auto="light"` with a cheap optimizer LM. Escalate only on ≥2% lift; confirm on a
   held-out test set. Hand off the compile/deploy mechanics to `[[agentsop-dspy]]`.

## Source basis

- Primary: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md` — optimizers, Dilemma Case A
  (optimizer cost vs gain), GEPA (~10 examples suffice with textual feedback), the three-stage gate, cost guardrails.
- Upstream (as cited by the primary): [dspy.ai/learn/optimization/overview/], [dspy.ai/learn/optimization/optimizers/],
  [dspy.ai/api/optimizers/GEPA/overview/], [dspy.ai/faqs/], [arxiv.org/abs/2507.19457] (GEPA), [arxiv.org/abs/2310.03714].
