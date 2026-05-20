# regression-gate skill

Cross-framework **enhancement overlay** for the **regression gate** of an LLM
application — the discipline of building a held-out eval set, running it on every
prompt/model/retriever change, and **blocking regressions in CI**.

This is the **E2 gap skill** in the Phase-D enhance pass. The regression-gate SOP
existed only as scattered fragments — `[[llamaindex]]` `OP-10 EvalLoop` ("gate
every change"), `[[dspy]]` train/dev/test split + metric — plus a vendor-tied
`ai-regression-testing` skill. It was never assembled as a standalone,
framework-agnostic SOP, so it earns its own overlay (per `phase-c-gap-analysis.md`
line 96).

## Core insight

> **An LM change is a code change. Gate it with a test suite: eval set + metric +
> threshold, wired into CI.** A prompt edit or a model swap shifts behavior
> statistically, so it slips through code review — the gate is the missing unit
> test for LM behavior.

The gate is three separable, version-controlled artifacts plus a wiring step:

1. **Eval set** — held-out, generated *then curated* into a golden set, frozen.
2. **Metric** — consumed from `[[agentsop-metric-design]]`, never invented here.
3. **Threshold** — an absolute floor and/or a relative no-regression Δ set
   *above measured run-to-run noise*.
4. **CI wiring** — a job that runs the eval at the PR's config and fails the
   build on a threshold breach.

## Scope

- **Activation**: any prompt/model/retriever change you want to ship safely;
  recurring "it got worse" surprises; CI setup for an LLM app with no eval job.
- **Not for**: one-shot tasks, unstable signatures, no-metric refusals, or
  public-benchmark capability evals (use `lm-evaluation-harness`).
- **Date stamp**: May 2026. Re-verify promptfoo assert/flag names and LangSmith
  dataset/eval APIs quarterly.

## Layout

```
d-regression-gate-skill/
├── SKILL.md                          # 7-section SOP (activation → cross-framework table)
├── README.md                         # this file
├── references/
│   └── R1-source-evidence.md         # every cited claim resolved to a source line
└── intermediate/
    └── operation_candidates.json     # raw trigger/action/output/evidence operations
```

The skill encodes: the "LM change is a code change" mental model; the held-out /
metric / threshold three-artifact decomposition; a 6-stage SOP (build → split →
metric → threshold → CI → flaky handling); 8 operations; 2 dilemma cases
(generated vs curated eval set; threshold too strict blocks good changes); 10
anti-patterns + 4 boundaries; and the cross-framework mapping (LlamaIndex
DatasetGenerator + evaluators, DSPy split + metric, promptfoo CI asserts,
LangSmith datasets).

## ENHANCE overlay

This skill is an **overlay**, not a replacement. It cross-links inline as
`[[name]]`:

- `[[agentsop-metric-design]]` — the metric the gate consumes. The gate's trustworthiness
  equals the metric's calibration; an uncalibrated gate is worse than none.
- `[[agentsop-domain-eval-set]]` — forward link: domain-specific held-out set construction
  (gap E7) is a distinct SOP this gate hands off to.
- `[[llamaindex]]` / `[[dspy]]` — the eval-loop and split+metric substrates this
  overlay assembles into a CI gate.
- `[[agentsop-cost-tiered-models]]` — Dilemma 2: a cost win at equal quality should pass a
  *quality* gate; cost is tracked on its own axis.

Activate this skill for the *gating decision* (what set, what threshold, how to
wire CI, how to handle flakiness); descend to the base skill for the eval-runner
API surface.

## Method

Mined primarily from the `[[llamaindex]]` and `[[dspy]]` source SKILLs under
`/Users/5imp1ex/Desktop/Skill-Workplace/output/`, with the E2/E7 framing from
`phase-c-gap-analysis.md`, and external grounding on "llm regression testing CI",
"promptfoo", and "eval set generation". Every load-bearing claim carries an
inline `[[source]]` or `[file:line]` tag and resolves in
`references/R1-source-evidence.md`. No fabricated APIs.

## Position in the Phase-D inventory

- **Sibling overlays**: `d-metric-design-skill` (the metric this gate consumes),
  `d-cost-tiered-models-skill` (the cost axis Dilemma 2 separates from quality).
- **Boundary vs `metric-design`**: metric-design *builds and calibrates* the
  scoring function; regression-gate *deploys* it as a CI gate over a held-out set.
  They compose — metric in, gate out.
- **Boundary vs `domain-eval-set`** (E7, forward): domain-eval-set is the
  *construction* SOP for a domain-specific held-out set; regression-gate is the
  *enforcement* SOP that runs any such set in CI.
