# domain-eval-set skill

An **ENHANCE overlay** coder-agent skill for building and governing a **50–200
example domain-specific held-out benchmark** — sampled from real traffic,
human-labeled, sealed, versioned.

**Version**: 0.1.0
**Phase**: D · **Tier**: core · **Status**: opinionated · **Overlay**: ENHANCE

## The one idea

> Public benchmarks (MMLU, HumanEval, GSM8K) measure **general capability**.
> A 50–200 example held-out **domain** set measures **YOUR task**.
> Only the latter predicts production.

`[[lm-evaluation-harness]]` covers the public-benchmark axis. This skill covers the
domain held-out axis — the number you actually gate deployment on. They are
complementary, not substitutes.

## What this skill answers

- How to **source** eval examples from real traffic (stratified, edge-case-heavy)
  instead of trusting a demo or an MMLU score.
- How to **label and curate** with inter-annotator agreement on the hard cases.
- **Hold-out discipline**: the test split is sealed — never to the optimizer,
  never as a few-shot demo, never to pick chunk size / model, never in fine-tune
  data.
- **Sizing**: why 50–200 (and why <30 is noise).
- **Versioning + leak audit**: hash/date/rubric the set; diff it against demos and
  training data so the number isn't contaminated.
- **Refresh**: how an eval set goes stale as the domain drifts ("green but on
  fire") and how to refresh + re-version.
- **When NOT to use it**: pure capability comparison → `[[lm-evaluation-harness]]`;
  objective oracle exists → just run the oracle.

## Files

- `SKILL.md` — main skill (7 sections: 何时激活 / 核心心智模型 / SOP / 操作模型 /
  困境决策案例 / 反模式与边界 / 跨框架对照)
- `references/R1-source-evidence.md` — verbatim source quotes per claim
- `intermediate/operation_candidates.json` — 8 operations (OP-DE01…OP-DE08) in
  Trigger / Action / Output / Evidence form

## Cross-links

- `[[lm-evaluation-harness]]` — public-benchmark runner; the capability-floor axis.
- `[[agentsop-regression-gate]]` — consumes this set as the per-PR gate (produce vs enforce).
- `[[agentsop-metric-design]]` — defines the scoring function applied to each held-out
  example (decomposed, calibrated, bool/float).

## Source basis

- DSPy SOP — train/dev/test discipline, held-out distinct from val, sizing floor
  (`output/dspy-sop-skill/SKILL.md`) [dspy.ai/learn/optimization/overview/]
- LlamaIndex SOP — eval loop built from the corpus, gated on every change,
  versioned artifacts (`output/llamaindex-sop-skill/SKILL.md`)
  [developers.llamaindex.ai/python/framework-api-reference/evaluation/]
- lm-evaluation-harness — the PUBLIC-benchmark skill this overlay distinguishes
  itself from (`~/.claude/skills/lm-evaluation-harness/SKILL.md`)
