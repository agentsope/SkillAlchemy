# metric-design skill

A Phase-D **tool skill** for designing the metric an LLM optimizer maximizes. The
core idea: **the metric IS the model** — a DSPy/GEPA/MIPRO optimizer is a
black-box search that chases whatever the metric rewards, so a bad metric beats a
good optimizer every time. This skill decomposes a holistic LLM-as-judge into 3-6
orthogonal yes/no sub-judges, returns `bool` during compile and `float` during
eval (`trace is not None`), bakes length in as a deterministic scalar (judges
over-prefer length), uses a cross-family judge to dodge self-preference,
runs a bias-probe suite (length / self-preference / position / rubric-order), and
**human-calibrates on >=20 spot-checks before any compile** — producing a metric
function plus a calibration receipt that DSPy compilers, the LlamaIndex
Faithfulness/Relevancy/Retriever triad, RAGAS, and TruLens consume.

**Version**: 0.1.0 - **Phase**: D - **Tier**: core - **Status**: opinionated

## Files

- `SKILL.md` — main skill (7 sections: 何时激活 / 核心心智模型 / SOP / 操作模型 /
  困境决策案例 / 反模式与边界 / 跨框架对照)
- `references/R1-source-evidence.md` — each load-bearing claim traced to its
  source (dspy-sop Case C + ops op-004/op-024/op-030; llamaindex-sop OP-10
  triad; judge-bias papers) with verbatim quotes.
- `references/R2-judge-bias-catalog.md` — catalog of LLM-as-judge biases
  (length, self-preference, positional, rubric-order, score-ID, hedging) with a
  detection probe and mitigation op per bias.
- `intermediate/operation_candidates.json` — the 10 operations (OP-M01…OP-M10)
  in id / name / trigger / action / output / evidence form.

## Cross-links

- `[[agentsop-dspy]]` — the optimizer side; consumes this metric (Case C, op-030).
- `[[agentsop-llamaindex]]` — RAG evaluator triad reused as sub-judges (OP-M06).
- `[[agentsop-domain-eval-set]]` — defines *what* is scored; this skill defines *how*.
- `[[agentsop-regression-gate]]` — consumes the calibrated metric as the per-PR gate.

## Source basis

- DSPy SOP — metric mode switch, decomposition, calibration, GEPA pairing
  (`output/dspy-sop-skill/`) [dspy.ai/learn/evaluation/metrics/]
- LlamaIndex SOP — Faithfulness/Relevancy/Retriever evaluator triad, OP-10
  (`output/llamaindex-sop-skill/SKILL.md`)
  [developers.llamaindex.ai/python/framework-api-reference/evaluation/]
- Judge-bias research — [arxiv.org/pdf/2506.02592], [arxiv.org/pdf/2509.26072];
  GEPA [arxiv.org/abs/2507.19457]
