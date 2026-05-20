# R2 — SOP Workflow

DSPy docs are explicit about a **three-stage gate** [dspy.ai/learn/]:

> "It's unproductive to launch optimization runs using a poorly designed program or a bad metric."

The stages are not optional. Each has an exit criterion.

---

## Stage 1 — Programming

**Goal**: a *working but un-optimized* program that produces plausible outputs.

### Steps

1. **Write the signature.**
   - Start inline: `"question -> answer"`.
   - Promote to class-based when types matter or fields need disambiguation.
   - Field names carry semantic load — they are the only hint the optimizer sees before data.
2. **Pick the module.**
   - Default: `dspy.ChainOfThought(Sig)`.
   - `Predict` for trivial; `ReAct` for tools; `ProgramOfThought` for math.
3. **Compose with Python**, subclassing `dspy.Module`.
4. **Configure the LM**: `dspy.configure(lm=dspy.LM('openai/gpt-4o-mini'))`.
5. **Hand-eyeball 5–10 examples** via `dspy.inspect_history(n=3)`.

### Exit criterion

Un-optimized program produces *plausible* (not great) outputs on 5+ examples. If outputs are nonsensical, the **program structure** is wrong — fix decomposition, not optimizer.

---

## Stage 2 — Evaluation

**Goal**: a metric the team trusts, plus a measured baseline.

### Steps

6. **Build a dev set.** Documented thresholds [dspy.ai/learn/optimization/overview/]:
   - 30 examples = minimum useful.
   - 300 examples = recommended.
   - 200+ = required floor for MIPROv2 to avoid overfit.
7. **Write a metric**:

   ```python
   def metric(example, pred, trace=None):
       return example.answer.lower() == pred.answer.lower()
   ```

   For multi-criteria: decompose into sub-judges, return `bool` when `trace is not None` (compile-time), `float` otherwise (eval-time).
8. **Spot-check the metric** against a human on 10–20 examples. >20% disagreement = fix the metric first.
9. **Measure baseline** with `dspy.Evaluate(devset=dev, metric=metric, num_threads=16)`.

### Exit criterion

Baseline is stable across two cache-free runs AND metric agrees with human on ≥80% of spot-checks.

---

## Stage 3 — Optimization (compile)

**Goal**: a compiled program that beats baseline on held-out test data.

### Steps

10. **Pick optimizer** (see R3 Case A + SKILL §4.1 table).
11. **Use unusual 20/80 split** for prompt-based optimizers [dspy.ai/learn/optimization/overview/]. GEPA uses standard ML splits.
12. **Pick optimizer LM ≠ task LM if budget tight**. Community evidence: gpt-4o-mini optimizing for gpt-4o gives comparable results at fraction of cost [github.com/stanfordnlp/dspy/issues/1596].
13. **Start `auto="light"`.** Never `heavy` first.
14. **Save with metadata**:

    ```python
    compiled.save("./v1/", save_program=True)   # whole program with deps
    # OR
    compiled.save("v1.json")                     # state only
    ```
15. **Evaluate on a held-out test set** (distinct from val).
16. **Deploy** [dspy.ai/tutorials/deployment/]:
    - FastAPI for lightweight: `dspy.asyncify(program)` then uvicorn.
    - MLflow for production: `mlflow.dspy.log_model(program, task="llm/v1/chat")`.
17. **Track usage in production**: `dspy.configure(track_usage=True)` and log `program.get_lm_usage()`.

### Exit criterion

Compiled program beats baseline on the held-out test set by task-relevant delta. Held-out set must NOT be the val set used by the optimizer.

---

## Decision points (one screen)

```
[Stage 1] Plausible un-optimized output?
              No  → fix signature / module / decomposition
              Yes ↓
[Stage 2] Metric agrees with human ≥ 80%?
              No  → decompose metric, sub-judges, length penalty
              Yes ↓
          Have ≥ 30 examples?
              No  → collect more, or use LabeledFewShot as floor
              Yes ↓
[Stage 3] Pick optimizer (see R3 Case A):
              ≤10 examples  → BootstrapFewShot
              30–50         → BootstrapFewShotWithRandomSearch
              200+          → MIPROv2(auto="light")
              Textual fb    → GEPA
          ↓
          auto="light" run. Gains > 5%?
              No  → return to Stage 1/2, the optimizer is not the bottleneck
              Yes → escalate to "medium"; if 300+ data, "heavy"
          ↓
          Evaluate on held-out test. Better than baseline?
              No  → return to Stage 1, fix program graph
              Yes → save, deploy
```

---

## What to do when optimization plateaus

The docs explicitly list the iteration questions [dspy.ai/learn/optimization/overview/]:

1. Is the task well-defined? (Signature too vague?)
2. Do you need more data?
3. Should your evaluation metric change?
4. Would a more sophisticated optimizer help? (← typically the **last** thing to try)
5. Does your program structure need revision? (Module choices, decomposition.)

The instinct to "try a different optimizer" is usually wrong. Go back to Stage 1.

---

## Cost-aware sub-protocol

Typical costs [dspy.ai/faqs/]:
- BootstrapFewShotWithRandomSearch on a small task: ~$3 USD, 6 minutes, 3200 API calls.
- MIPROv2 `auto="light"`: order of $2.
- MIPROv2 `auto="heavy"` on 1000+ examples: tens of dollars, hours.

Cost-control checklist before any compile:
- [ ] Use cheap LM (e.g. gpt-4o-mini) as `prompt_model` even if `task_model` is expensive.
- [ ] `auto="light"` first.
- [ ] Cap `max_bootstrapped_demos` and `max_labeled_demos` (defaults: 4 each).
- [ ] Set `num_threads` to a value your rate limits tolerate.
- [ ] Disable cache only if you actually need fresh runs: `dspy.LM(..., cache=False)`.
- [ ] In Lambda/serverless, set both `DSP_CACHEDIR` and `DSPY_CACHEDIR` to `/tmp` or disable.
