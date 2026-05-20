# R3 — Dilemma Cases (extended)

Each case is a real decision point sourced from docs, GitHub issues, papers, and production write-ups. Format: dilemma / constraints / decision steps / outcome / extractable operation.

---

## Case A — Optimizer cost vs gain: when is it worth compiling?

**Source**: [github.com/stanfordnlp/dspy/issues/1596], [arxiv.org/abs/2310.03714], [dspy.ai/faqs/]

**Dilemma**: A 3-stage RAG pipeline already hits 72% on dev with hand-tuned prompts. MIPROv2 `auto="heavy"` would cost ~$40 and run 4 hours. Worth the spend?

**Constraints**
- 250 labeled examples (above MIPROv2 floor of 200).
- Prompts already manually iterated → diminishing returns suspected.
- Pipeline LM is GPT-4o; trial scale matters.
- Reference data point: paper reports 25%/65% improvement over standard few-shot for GPT-3.5/Llama2-13B [arxiv.org/abs/2310.03714].

**Decision steps**
1. **Question the premise**: were the manual prompts ever validated against the metric, or just eye-balled? If eye-balled, `auto="light"` (~$2) is highly likely to yield 10%+.
2. **Run `auto="light"` first.** Docs: "start with moderate values, observe behavior, scale up only if you see clear gains" [issue #1596].
3. **Cheap optimizer LM trick**: set `prompt_model=gpt-4o-mini` while keeping `task_model=gpt-4o`. Community evidence shows parity at a fraction of cost [issue #1596].
4. **Decision rule**:
   - `light` gives < 2% → do NOT escalate. The bottleneck is program structure or metric, not optimizer.
   - `light` gives 5–10% → run `medium`.
   - `medium` flatlines or data < 300 → stop. Don't `heavy`.
5. **Return on Stage 1**: if no optimizer helps, re-examine signature ambiguity and program decomposition.

**Outcome**: Typical pattern is that `light` reveals whether more compute helps. The "compile is magic" frame often hides a deeper issue with the program graph.

**Extractable operation**: **Always probe with `auto="light"`. Use a cheap optimizer LM. Escalate only when light gives clear lift.**

---

## Case B — Swap the underlying LM: recompile, transfer, or both?

**Source**: [acldigital.com/blogs/death-to-prompting-long-live-programming], [ganeshkedari.substack.com/p/stop-writing-prompts-a-guide-to-dspy], [dspy.ai/api/optimizers/BootstrapFinetune/]

**Dilemma**: A program compiled for GPT-4o achieves 85%. Cost pressure demands switching to Llama-3-8B. Can the existing `program.json` be re-used?

**Constraints**
- Compiled programs encode demos + instructions that may exceed small-model context coherence.
- Recompile costs ~$2–5 again.
- DSPy doctrine: "If you optimize a complex pipeline for GPT-4, it usually breaks on Llama-3-8b" [acldigital].

**Decision steps**
1. **Always recompile when changing LM family.** This is DSPy's headline value: "swap the LLM definition and re-compile" [ganeshkedari]. The optimizer will discover the small model needs more examples or simpler reasoning steps and adapt.
2. **Don't reuse demos verbatim across families.** GPT-4o-style verbose CoT demos cause Llama-8B to mimic length without reasoning.
3. **If cost is extreme, distill**: chain MIPROv2 → BootstrapFinetune. Optimize prompts on the strong model, finetune a 1B–7B student. Typical setup: `student=Llama-3.2-1B-Instruct`, `teacher=gpt-4o-mini` [dspy.ai/api/optimizers/BootstrapFinetune/].
4. **Version artifacts**: ship both `program.gpt4o.json` and `program.llama8b.json`; A/B test in production.

**Outcome**: Recompiled programs typically recover 70–90% of the larger model's performance at 1/10–1/50 the per-call cost. "Transfer without recompile" reliably underperforms.

**Extractable operation**: **Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the artifact — recompile, don't migrate.**

---

## Case C — Metric design: proxy correctness vs ground truth

**Source**: [dspy.ai/learn/evaluation/metrics/], [arxiv.org/pdf/2506.02592], [arxiv.org/pdf/2509.26072], [arxiv.org/abs/2507.19457] (GEPA)

**Dilemma**: Open-ended customer-support response task. No exact-match metric. LLM-as-judge "feels right" but the team worries about bias toward verbose, hedged outputs.

**Constraints**
- 400 labeled examples with *acceptable* (not unique-correct) reference responses.
- Production users penalize verbosity.
- DSPy will optimize toward whatever the metric rewards. A biased metric → biased program at scale.
- Documented LLM-judge biases: self-preference, recency, rubric order, score ID, provenance hierarchy [arxiv.org/pdf/2506.02592, arxiv.org/pdf/2509.26072].

**Decision steps**
1. **Reject single-LLM-judge as the optimization metric.** Cite the bias literature.
2. **Decompose**: build sub-judges, each a `dspy.Predict(Assess)` answering one yes/no question (factual? on-topic? concise? non-hedging?). Documented pattern [dspy.ai/learn/evaluation/metrics/].
3. **Mode-switching return**: `bool` during compile (`trace is not None`), `float` during eval. Standard idiom.
4. **Spot-check on 20 examples with a human judge before compiling.** >20% disagreement → fix metric.
5. **Add an explicit length penalty as a separate scalar.** Judges over-prefer length; don't trust the judge to penalize verbosity.
6. **If you have rich textual feedback** (sub-judge rationales, schema violations, test diffs) — **prefer GEPA over MIPROv2**. GEPA leverages text feedback; MIPROv2 only sees scalar score [arxiv.org/abs/2507.19457]. GEPA outperforms MIPROv2 by 10–13% on AIME-2025 with 35× fewer rollouts.

**Outcome**: Multi-dimension metric with length penalty + GEPA's textual feedback is the empirically robust path. Single judge + MIPROv2 is fragile and likely produces verbose, hedging compiled programs.

**Extractable operation**: **Never compile against a metric that hasn't been human-validated. Decompose multi-criteria metrics into sub-judges with explicit penalties. Prefer GEPA when textual feedback can be produced.**

---

## Case D — Compile-time hang / stuck trial: abort or wait?

**Source**: [github.com/stanfordnlp/dspy/issues/1970], [dspy.ai/faqs/]

**Dilemma**: MIPROv2 compile shows no progress for 30 minutes mid-trial. $15 already spent. Wait or kill?

**Constraints**
- Compile is not atomic; no graceful resume from arbitrary point.
- Common causes: (a) single example triggers context-length overflow; (b) rate limits; (c) tool call hang in ReAct.

**Decision steps**
1. **Inspect**: `dspy.inspect_history(n=3)`. Look for truncation, rate-limit errors, tool errors.
2. **If context-length**: reduce `max_bootstrapped_demos` and `max_labeled_demos` (defaults: 4). The docs cite this as the #1 fix [dspy.ai/faqs/].
3. **If rate-limit**: lower `num_threads`; add backoff in the LM client.
4. **If neither identifiable**: kill and restart with smaller `minibatch_size` (default 35 → try 16) and smaller `num_trials`.
5. **Salvage partial state** if possible: inspect `compiled._predictors` for best-so-far demos before killing.

**Outcome**: Indefinite waits are pure cost. Aborting and restarting smaller is the dominant strategy.

**Extractable operation**: **Compile is not atomic. Treat long hangs as failure. Restart smaller; the cost of restart < cost of indefinite wait.**

---

## Cross-case pattern

A consistent theme across A–D: **the optimizer is rarely the bottleneck.** When DSPy underperforms:

- Most often → metric is wrong (Case C).
- Next → program graph is wrong (Case A's plateau path).
- Next → LM change invalidates the artifact (Case B).
- Operational → compile hung due to data/program edge case (Case D).

The instinct to "try another optimizer" is almost always misplaced.
