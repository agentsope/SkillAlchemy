# R1 — Source Evidence

Every load-bearing claim in `SKILL.md` resolved to its source. Primary sources
are the two base SKILLs:

- `[[llamaindex]]` — `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`
- `[[dspy]]` — `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`

Line numbers are against those files as read. The gap framing is from
`/Users/5imp1ex/Desktop/Skill-Workplace/output/phase-c-gap-analysis.md` (E2).
External claims are grounded on the topics named in the task brief; verify
tool/feature names quarterly.

## A — Claims sourced from the llamaindex SKILL

| SKILL claim | Source (llamaindex-sop-skill/SKILL.md) |
|---|---|
| "Build the eval loop **before** optimizing anything" | Stage 2 heading — line 114 |
| `DatasetGenerator.from_documents(docs).generate_dataset_from_nodes(num=50)` produces labelled QA pairs | Stage 2 code — lines 117-121 |
| Track {MRR, hit-rate, faithfulness, relevancy, p95}; "Every subsequent change must be gated on these numbers" | Stage 2 — lines 122-124 |
| "Most RAG failures trace to weak retrieval or sloppy ingestion — not the LLM. The eval loop is what surfaces them." | Stage 2 note — line 126 |
| `OP-10 EvalLoop`: gate continuously; "Quantitative regression test for every chunking / embedding / retriever / prompt change" | OP-10 — lines 232-236 |
| Faithfulness + Relevancy + RetrieverEvaluator(["mrr","hit_rate"]) as the metric triad | OP-10 Action — line 234 |
| Anti-pattern A3: "No eval loop; debug by anecdote" → stand up evaluators first | Anti-pattern table A3 — line 348 |
| Per-query-type taxonomy (motivates slicing) | Dilemma 2 step 1 — line 280 |

## B — Claims sourced from the dspy SKILL

| SKILL claim | Source (dspy-sop-skill/SKILL.md) |
|---|---|
| Held-out test gate: compiled program "beats baseline on a *held-out* test set (not the val set used in optimization) by ≥ task-relevant delta" | Stage 3 exit criterion — line 101 |
| Dev-set sizing: "30 examples = minimum useful, 300 = recommended, 200+ required for MIPROv2" | Stage 2 step 5 — line 87 |
| Metric signature `def metric(example, pred, trace=None) -> float\|bool` | Stage 2 step 6 — line 88 |
| Exit criterion Stage 2: "baseline score is stable across two runs (cache-free)" | Stage 2 exit — line 91 |
| Reversed 20/80 train/val split for prompt-based optimizers (optimizer concern, not the gate) | Stage 3 step 9 — line 96; AP-9 — line 254 |
| "If you optimize a complex pipeline for GPT-4, it usually breaks on a smaller model like Llama-3-8b" (model change = behavior change) | Case B 约束 — line 184 |
| "Keep both program.gpt4o.json and program.llama8b.json checked in; A/B" (versioned-artifact discipline → baseline ratchet) | Case B step 5 — line 191 |
| Human-validate metric on ≥20 spot-checks before compiling (curation/calibration discipline) | Case C step 4 — line 212 |
| AP-10: "Forgetting cache=False in stateless deploys" (CI caching hazard) | Anti-patterns — line 255 |
| Boundary: one-shot task → raw API call (no gate needed) | Boundaries — line 259 |
| Boundary: signature changing daily → compile/gate only after I/O contract stabilizes | Boundaries — line 260 |
| Exact-match metric example | §4.3 Metric design — line 137 |

## C — Gap framing

| SKILL claim | Source |
|---|---|
| E2 = "Eval set generation + regression gate"; common; weak coverage in llamaindex (DatasetGenerator) + a 3.6K vendor regression-testing skill; verdict ENHANCE; "Cross-framework regression-gate setup deserves its own SOP" | phase-c-gap-analysis.md line 96 |
| E2 fusion intent: "fuse skill.sh ai-regression-testing with DSPy/LlamaIndex split-train-eval recipes" | phase-c-gap-analysis.md line 155 |
| E7 boundary: "Held-out 50-200 domain-set SOP is distinct from public-bench harnesses" (motivates the `[[agentsop-domain-eval-set]]` cross-link and the lm-evaluation-harness boundary B4) | phase-c-gap-analysis.md line 101 |

## D — External claims (grounding topics; verify quarterly)

Well-established facts grounded on the topics named in the task brief
("llm regression testing CI", "promptfoo", "eval set generation"). They do not
depend on any single fabricated API.

| SKILL claim | Grounding topic | Note |
|---|---|---|
| A regression gate runs an eval suite in CI and fails the build (non-zero exit) when a metric breaches a threshold | "llm regression testing CI" | Standard CI-gate pattern (mirror of unit-test gating) |
| promptfoo is CI-native: `promptfoo eval` runs a `tests:` suite of `assert`s (equals / contains / llm-rubric / javascript) and exits non-zero on failure; supports `--fail-on` style thresholds | "promptfoo" | Verify exact CLI flags / assert types against current promptfoo docs |
| promptfoo can synthesize test cases from prompts (generation step) | "promptfoo" / "eval set generation" | Verify current generation feature name |
| LangSmith provides managed Datasets, evaluator functions / LLM-as-judge, and regression alerts with CI integration | "llm regression testing CI" | Verify current LangSmith dataset/eval API |
| Held-out, curated domain eval sets (50–200) catch regressions that public benchmarks (MMLU/HumanEval) do not | "eval set generation" | Distinct from `lm-evaluation-harness` capability benchmarks |
| Generated eval sets inherit the generator model's blind spots and skew easy; curation + edge-case injection is required for trust | "eval set generation" | Self-preference leakage; mirrors metric-design judge bias |
| LLM outputs are nondeterministic → gates flap; mitigate with temperature=0, seeds, disabled caching, and N-run averaging | "llm regression testing CI" | Δ must exceed measured run-to-run noise |

## E — Cross-skill links (overlay)

| Link | Why | Resolves to |
|---|---|---|
| `[[agentsop-metric-design]]` | This skill *consumes* a metric; it does not design one. The gate's trustworthiness equals the metric's calibration. | `/Users/5imp1ex/Desktop/Skill-Workplace/output/d-metric-design-skill/SKILL.md` (OP-M01/M02/M03/M05) |
| `[[agentsop-domain-eval-set]]` | Forward link: domain-specific held-out set construction (E7) is a distinct SOP this gate hands off to. | not yet authored (forward reference) |
| `[[agentsop-cost-tiered-models]]` | Dilemma 2: cost wins at equal quality should pass a *quality* gate; cost is tracked on its own axis. | `/Users/5imp1ex/Desktop/Skill-Workplace/output/d-cost-tiered-models-skill/` |
| `[[llamaindex]]`, `[[dspy]]` | The eval-loop and split+metric substrates this overlay assembles into a CI gate. | base SKILLs above |

## Verification status

- **A / B / C** — fully traceable to source SKILL / gap-analysis line numbers above. No fabrication.
- **D** — established regression-testing facts grounded on the named topics; tool
  feature names (promptfoo asserts/flags, LangSmith dataset API) are
  time-sensitive (May 2026) — re-verify against current vendor docs before
  relying on exact names.
- **E** — `[[agentsop-domain-eval-set]]` is an intentional forward cross-link; the skill is
  not yet authored (it is gap E7 in the same Phase-D pass).
