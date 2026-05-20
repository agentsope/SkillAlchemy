---
name: agentsop-dspy
version: 0.1.0
description: |
  Operating SOP for DSPy (Stanford NLP) — the declarative framework for "programming, not prompting" language models.
  Activate when the user says any of: "use DSPy", "compile a prompt", "optimize prompts/programs", "MIPRO/MIPROv2",
  "BootstrapFewShot", "GEPA", "Signatures + Modules", "teleprompter", "auto-tune prompts for a different LM",
  or whenever a brittle hand-crafted prompt pipeline needs to be turned into a *compiled*, measurable, swappable program.
  Do NOT activate for one-shot prompt tweaks, no-metric exploratory work, or pipelines where prompts must remain
  human-authored verbatim — use raw prompting or LangChain templates instead.
---

# DSPy SOP — Programming, Not Prompting

> *"DSPy isn't a prompt-optimization agent framework. It's the LLM compiler for the shortest, cleanest code."*
> — Eito Miyamura [eito.substack.com/p/dspy-the-most-misunderstood-agent]
>
> *"Prompts are effectively the weights of an LLM application."*
> — Core philosophy [arxiv.org/abs/2310.03714]

---

## 1. 何时激活 (When to activate)

Activate this skill when **any** of the following triggers are present in the user's intent or codebase:

| Trigger | Signal |
|---|---|
| Imports / mentions | `import dspy`, `dspy.Signature`, `dspy.ChainOfThought`, `dspy.ReAct`, `Predict`, `MIPROv2`, `BootstrapFewShot`, `GEPA`, `teleprompter`, `compile(` on an LM program |
| Tasks | "auto-tune this prompt", "I want to swap GPT-4 for a smaller model without re-engineering prompts", "I have 50/200/1000 labeled examples — optimize this", "compile a pipeline for our metric", "distill GPT-4 into Llama-3-8B" |
| Symptoms | Hand-written prompts grow past ~50 lines; brittleness on model swap; the team manually tunes few-shot examples; a metric exists but isn't being used to drive prompt design |
| Cross-skill bridges | LangGraph node calls an LLM and needs better prompts → wrap the node body in a DSPy module. LlamaIndex retriever feeds a reranker → DSPy-compile the reranker against a labeled set |

**Do NOT activate** when:
- The task is one-shot ("just answer this question once") — use raw `client.messages.create`.
- No evaluation metric is possible and none is willing to be built — DSPy without a metric is just verbose prompting.
- Prompts must remain human-authored verbatim for compliance, audit, or stylistic reasons.
- The team is in *rapid exploration* mode where the task signature itself is changing daily — compile only after the signature stabilizes [dspy.ai/learn/optimization/overview/].

---

## 2. 核心心智模型 (Core mental model)

DSPy's full name is **D**eclarative **S**elf-improving **Py**thon. The three primitives form a PyTorch-like compile chain [arxiv.org/abs/2310.03714]:

```
┌─────────────┐    ┌──────────┐    ┌──────────────┐    ┌─────────┐
│  Signature  │ →  │  Module  │ →  │ Teleprompter │ →  │ Compile │
│ (what)      │    │ (how)    │    │ (optimizer)  │    │ (tune)  │
└─────────────┘    └──────────┘    └──────────────┘    └─────────┘
   I/O spec       Predict/CoT/      MIPROv2/GEPA/      Bake demos
   field names     ReAct/PoT        BootstrapFewShot   + instructions
   = semantic     = strategy        = search algorithm  into JSON
```

**Three mental shifts** the agent must internalize:

1. **Prompts are weights.** The prompt string is not the artifact you ship — the *compiled program* (a JSON of demonstrations + instructions + structural choices) is. You ship `program.json`, not a `.txt` prompt [dspy.ai/tutorials/saving/].

2. **Signatures carry semantic load.** `question -> answer` is not the same as `query -> response`. DSPy uses the *field names* as the only natural-language hint the optimizer has about intent before it sees data. Name them like you'd name function parameters in well-written code [dspy.ai/learn/programming/signatures/].

3. **Compile is a hyperparameter search, not a one-shot call.** Compilation runs hundreds-to-thousands of LM calls (typically $2–$3 USD, 6–20 minutes, 3.2k API calls in the reference run). Costs scale with `num_trials × |trainset| × |program LM calls|` [dspy.ai/faqs/].

**The PyTorch analogy** is load-bearing. Signatures ≈ `nn.Module.forward()` shape contract. Modules ≈ `nn.Linear` / `nn.Transformer`. Teleprompters ≈ `torch.optim.Adam`. `compile()` ≈ training loop. `save()/load()` ≈ checkpoint.

---

## 3. SOP 工作流 (SOP workflow)

The DSPy team is explicit about a **three-stage gate** [dspy.ai/learn/]:

> "It's unproductive to launch optimization runs using a poorly designed program or a bad metric."

Do not skip stages. Each stage has an exit criterion.

### Stage 1 — Programming (no optimizer yet)

1. **Pin the task as a Signature.** Start inline (`"question -> answer"`); upgrade to a class-based `dspy.Signature` with `InputField(desc=...)` / `OutputField(desc=...)` when types matter or fields need disambiguation.
2. **Pick the lowest-power Module that works.** Default to `dspy.ChainOfThought`. Use `dspy.Predict` for trivial classification, `dspy.ReAct` only when tools are needed, `dspy.ProgramOfThought` for arithmetic-heavy tasks [dspy.ai/learn/programming/modules/].
3. **Compose with plain Python control flow.** Subclass `dspy.Module`, instantiate sub-modules in `__init__`, call them in `forward()`. No special DSL.
4. **Run zero-shot on 5–10 hand-picked examples.** Look at outputs with `dspy.inspect_history(n=3)`.

**Exit criterion:** the un-optimized program produces *plausible* outputs on 5+ examples. Not great — plausible.

### Stage 2 — Evaluation (no optimizer yet)

5. **Build a dev set.** Documented sweet spot: **30 examples = minimum useful, 300 = recommended, 200+ required for MIPROv2** to avoid overfitting [dspy.ai/learn/optimization/overview/].
6. **Write a metric**: `def metric(example, pred, trace=None) -> float|bool`. Start with exact-match; only escalate to LLM-as-judge when the task demands it (open-ended generation, multi-criteria).
7. **Run `dspy.Evaluate(devset=dev, metric=metric, num_threads=16)`** and record a baseline score.

**Exit criterion:** baseline score is stable across two runs (cache-free) AND the metric agrees with human judgment on 10 spot-checks.

### Stage 3 — Optimization (compile)

8. **Pick optimizer by data + signal regime** (Section 4 table). Decide *which model optimizes vs. which model is the task model* — they can differ.
9. **Use the unusual 20/80 split** (20% train, 80% val) for prompt-based optimizers. GEPA uses standard ML splits (maximize train) [dspy.ai/learn/optimization/overview/].
10. **Start `auto="light"`.** Only escalate to `"medium"`/`"heavy"` if dev-set gains flatten and budget allows.
11. **Save the compiled program**: `compiled.save("v1.json")` for state, or `compiled.save("./v1/", save_program=True)` for whole-program (preferred for production with metadata) [dspy.ai/tutorials/saving/].
12. **Deploy** via FastAPI (`dspy.asyncify`) or MLflow (`mlflow.dspy.log_model`) [dspy.ai/tutorials/deployment/].

**Exit criterion:** compiled program beats baseline on a *held-out* test set (not the val set used in optimization) by ≥ task-relevant delta.

### When to iterate back

Loop to Stage 1 if optimization plateaus. Per the docs: "Is your task well-defined? Do you need more data? Should your evaluation metric change?" — these are the questions to re-ask, not "should I try a different optimizer?" [dspy.ai/learn/optimization/overview/].

---

## 4. 操作模型 (Trigger / Action / Output / Evidence)

### 4.1 Choose the optimizer

| Trigger | Action | Output | Evidence |
|---|---|---|---|
| ≤10 labeled examples | `BootstrapFewShot(metric=m, max_bootstrapped_demos=4, max_rounds=1)` | Compiled program with self-generated demos | [dspy.ai/learn/optimization/optimizers/] |
| 30–50 examples | `BootstrapFewShotWithRandomSearch` | Best-of-N candidate programs | [dspy.ai/learn/optimization/optimizers/] |
| 200+ examples, willing to spend compute | `MIPROv2(metric=m, auto="light")` then escalate | Jointly-tuned instructions + few-shot demos via Bayesian optimization | [dspy.ai/api/optimizers/MIPROv2/] |
| Need zero-shot prompts (no demos in final) | `MIPROv2(..., max_bootstrapped_demos=0, max_labeled_demos=0)` | Instruction-only optimization | [dspy.ai/learn/optimization/optimizers/] |
| Have textual error feedback (test diffs, schema violations, judge rationales) | `dspy.GEPA(metric=m_with_feedback)` | Reflection-evolved prompts; sample-efficient | [dspy.ai/tutorials/gepa_ai_program/], [arxiv.org/abs/2507.19457] |
| Already optimized with MIPROv2 / want to ship a smaller model | Chain into `BootstrapFinetune(student=small_lm, teacher=optimized)` | Finetuned weights (not just prompts) | [dspy.ai/api/optimizers/BootstrapFinetune/] |
| Just want labeled demos in prompt (no search) | `LabeledFewShot(k=8)` | Trivial — fastest, cheapest, weakest | [dspy.ai/cheatsheet/] |

### 4.2 Module selection

| Trigger | Action | Why |
|---|---|---|
| Simple input → output | `dspy.Predict(Sig)` | Lowest overhead |
| Reasoning helps | `dspy.ChainOfThought(Sig)` | **Default choice** per docs |
| Math / counting / parsing | `dspy.ProgramOfThought(Sig)` | Code execution grounds the answer |
| Tools (search, calc, API) | `dspy.ReAct(Sig, tools=[...])` | Built-in tool loop |
| Ensemble for hard cases | `dspy.MultiChainComparison` or `dspy.majority` | Vote across N CoT samples |

### 4.3 Metric design

| Trigger | Action | Caveat |
|---|---|---|
| Exact answer expected | `lambda ex, pred: ex.answer.lower() == pred.answer.lower()` | Cheap, deterministic |
| Open-ended generation | LLM-as-judge with `dspy.ChainOfThought(JudgeSig)` | Watch for self-preference bias, recency bias, score-ID bias [arxiv.org/pdf/2509.26072] |
| Multi-criteria (factuality + tone + length) | Sub-judge each dim, return **`bool` during optimization (`trace is not None`) and `float` during evaluation** | Documented pattern [dspy.ai/learn/evaluation/metrics/] |
| Have rich error context | Return `dspy.Prediction(score=..., feedback="missing field X")` and use **GEPA** | Textual feedback is GEPA's superpower [dspy.ai/api/optimizers/GEPA/overview/] |

### 4.4 Cost guardrails

| Trigger | Action | Reference |
|---|---|---|
| Before any `MIPROv2` call | Estimate: `auto="light"` ≈ a few $; `auto="heavy"` on 1000+ examples can hit tens of $ | [dspy.ai/faqs/] |
| Budget tight | Use a **cheap optimizer LM** (e.g. gpt-4o-mini) to optimize prompts for a more expensive task LM — community-reported parity [github.com/stanfordnlp/dspy/issues/1596] |
| Compile stuck mid-trial | Check issue #1970 pattern; reduce `minibatch_size` or kill and restart with smaller `num_trials` |
| Need reproducibility | `dspy.configure(track_usage=True)` + log `program.get_lm_usage()` |

---

## 5. 困境决策案例 (Dilemma cases — ≥3)

### Case A — "Optimizer cost vs gain: when is it worth compiling?"

**困境 (Dilemma):** User has a 3-stage RAG pipeline. Hand-tuned prompts already hit 72% on dev. MIPROv2 `auto="heavy"` would cost ~$40 and 4 hours. Worth it?

**约束 (Constraints):**
- 250 labeled examples (above MIPROv2 200-example floor) [dspy.ai/learn/optimization/optimizers/].
- Prompts already manually iterated — diminishing returns suspected.
- Pipeline LM = GPT-4o ($-per-call adds up at trial scale).

**决策步骤 (Decision steps):**
1. Check whether the prompts were ever validated against the metric, or just eye-balled. If eye-balled, even `auto="light"` (~$2) typically yields 10–30%+ on hand-tuned baselines per the paper's GPT-3.5/Llama2 results (25%/65% lift over standard few-shot) [arxiv.org/abs/2310.03714].
2. Run **`auto="light"` first** as a cheap signal. The docs explicitly recommend "start with moderate values, observe behavior, and scale up only if you see clear gains" [github.com/stanfordnlp/dspy issue #1596].
3. If `light` gives <2% lift, do **not** escalate to `heavy`. Instead, revisit Stage 1: is the signature ambiguous? Is the program structure (3 stages) actually right?
4. If `light` gives 5–10% lift, run `medium`. Only escalate to `heavy` if data ≥ 300 *and* you have a held-out test set distinct from val.
5. Use **gpt-4o-mini as the optimizer LM** even when the task LM is gpt-4o. Community evidence: parity at fraction of cost [github.com/stanfordnlp/dspy issue #1596].

**结果 (Outcome):** Typical: `light` exposes whether more compute helps. Often the answer is "no — fix the program/metric first."

**可提取的操作 (Extractable operation):** **Never start compilation at `auto="heavy"`. Always probe with `light` and use a cheap optimizer LM.**

---

### Case B — "Swap the underlying LM: recompile, transfer, or both?"

**困境:** Compiled program for GPT-4o works at 85%. Need to switch to Llama-3-8B for cost. Re-use the GPT-4o-compiled `program.json` or recompile?

**约束:**
- Compiled program contains demos + instructions that may exceed the smaller model's context coherence.
- Recompile cost ≈ another $2–5.
- The DSPy doctrine: "If you optimize a complex pipeline for GPT-4, it usually breaks on a smaller model like Llama-3-8b" [acldigital.com — Death to Prompting].

**决策步骤:**
1. **Always recompile when changing the task LM family.** This is the headline value prop of DSPy: "swap the LLM definition and re-compile your program" [ganeshkedari.substack.com/p/stop-writing-prompts-a-guide-to-dspy].
2. The optimizer will discover the smaller model needs **more examples / simpler reasoning steps** and adjusts automatically — you do not edit prompts.
3. Use **`BootstrapFinetune`** as a follow-on: optimize prompts on the big model, then distill into a 1B–7B student. Typical setup: `student=Llama-3.2-1B-Instruct`, `teacher=gpt-4o-mini` [dspy.ai/api/optimizers/BootstrapFinetune/].
4. If demos in the saved program reference GPT-4o-style verbose CoT, the small model may parrot length without reasoning. Recompile is mandatory, not optional.
5. Keep both `program.gpt4o.json` and `program.llama8b.json` checked in; A/B in production.

**结果:** Recompiled programs typically recover 70–90% of the larger-model performance at 1/10–1/50 the per-call cost. The "transfer without recompile" path is reliably worse.

**可提取的操作:** **Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the artifact — recompile.**

---

### Case C — "Metric design: proxy correctness vs ground truth"

**困境:** Open-ended customer-support response task. No exact-match metric possible. LLM-as-judge "feels right" but the team worries the judge will be biased toward verbose, hedged outputs.

**约束:**
- 400 labeled examples with a *reference response* (not the unique correct response — one acceptable response).
- Production users penalize verbosity.
- DSPy will optimize *toward whatever the metric rewards*. A bad metric becomes a bad program at scale.

**决策步骤:**
1. **Refuse to ship a single-LLM-judge as the optimization metric.** Document evidence: LLM judges exhibit self-preference, recency, rubric-order, and provenance biases [arxiv.org/pdf/2506.02592, arxiv.org/pdf/2509.26072].
2. **Decompose the judge** into orthogonal sub-judges, each a `dspy.Predict(Assess)` call with a single yes/no question (factual? on-topic? concise? non-hedging?). Documented pattern [dspy.ai/learn/evaluation/metrics/].
3. **Use `trace is not None` to return bool during compile, float during eval** — same metric function, two modes. Avoids the optimizer overfitting to score noise.
4. **Spot-check the metric on 20 examples with a human judge first.** If sub-judges disagree with human on >20% of cases, fix the metric before compiling. Garbage metric → garbage compiled program.
5. **If sub-judge feedback is rich (e.g. "answer was verbose"), pipe textual feedback into `dspy.GEPA`** instead of MIPROv2 — GEPA leverages text feedback for faster, more sample-efficient convergence [dspy.ai/api/optimizers/GEPA/overview/, arxiv.org/abs/2507.19457].
6. Add a **length penalty** as a separate scalar in the metric — don't rely on the judge to penalize verbosity (judges over-prefer length).

**结果:** Multi-dimension metric with explicit length penalty + GEPA's textual feedback typically beats single-judge + MIPROv2 by 10–13% on AIME-style benchmarks [arxiv.org/abs/2507.19457] and is the empirically robust path.

**可提取的操作:** **Never compile against a metric you haven't human-validated on ≥ 20 spot-checks. Decompose multi-criteria metrics. Prefer GEPA when you can express textual feedback.**

---

### Case D — "Compile-time hang / stuck trial — abort or wait?"

**困境:** MIPROv2 compile stuck mid-trial (no progress logs for 30 min). Reported pattern in issue #1970 [github.com/stanfordnlp/dspy/issues/1970]. Abort and restart, or wait?

**约束:**
- $15 spent so far on the run.
- Sunk cost vs. wasted further spend.
- Possible causes: a single example triggers rate limits / context-length overflow / a tool call hangs.

**决策步骤:**
1. Check `dspy.inspect_history(n=3)` — does the last LM call show truncation or rate-limit error?
2. If context-length: reduce `max_bootstrapped_demos` and `max_labeled_demos` (default 4 each); the docs explicitly cite this as the #1 context-length fix [dspy.ai/faqs/].
3. If rate-limit: lower `num_threads` in the underlying Evaluate; add retry/backoff in the LM client.
4. If neither, **abort**. Restart with smaller `minibatch_size` (default 35; try 16) and smaller `num_trials`. Hanging is a known failure mode without graceful resume.
5. Save partial progress: even mid-compile, `student` retains best demo candidates — check `compiled._predictors` state.

**可提取的操作:** **Compile is not atomic. Treat long hangs as failure. The cost of restart < cost of indefinite wait.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **Compiling without a metric.** Without a metric, DSPy collapses to verbose prompt templating. The Predict module *requires* nothing; the optimizers *require* a metric. If you cannot write a metric, you cannot optimize, period [dspy.ai/learn/optimization/overview/].
2. **Compiling on 5 examples.** Below ~30 examples, you're not training — you're memorizing. The 20/80 train/val split exists *because* "prompt-based optimizers often overfit to small training sets" [dspy.ai/learn/optimization/overview/].
3. **Editing the compiled JSON by hand.** It's plain JSON and readable — but human edits invalidate the assumption that the artifact was metric-optimized. Re-compile or don't touch.
4. **Using LLM-as-judge as the *only* metric for any open-ended task.** See Case C. Biases are documented and reproducible [arxiv.org/pdf/2506.02592].
5. **Starting at `auto="heavy"`.** Always probe with `light` first [Case A].
6. **Treating DSPy modules as agents.** ReAct is a thin tool-loop, not a multi-agent framework. For long-running, stateful, branching workflows: combine DSPy with LangGraph (see Section 7).
7. **Ignoring program structure when optimization stalls.** If MIPROv2 light + medium both flatline, the bottleneck is almost always the **program graph** (wrong decomposition, wrong module choice) not the optimizer [dspy.ai/learn/optimization/overview/].
8. **Re-using GPT-4-compiled programs on Llama-8B.** See Case B.
9. **Skipping the unusual 20/80 split.** The reversed ratio is intentional and prevents prompt-overfitting [dspy.ai/learn/optimization/overview/].
10. **Forgetting `cache=False` in Lambda / stateless deploys.** Caches default to a writable dir and break in serverless [dspy.ai/faqs/].

### Boundaries (when NOT to use DSPy)

- **One-shot tasks.** "Summarize this email once" → raw API call. The compile loop has no payoff.
- **The task signature is still changing daily.** Compile only after the I/O contract stabilizes; otherwise you're paying compile cost for prompts you'll throw away.
- **Compliance/audit requires verbatim human-authored prompts.** Optimized prompts are machine-generated artifacts; some regulated contexts disallow this.
- **No labeled data and no labelable proxy.** Without a metric, the framework can't help you. (Note: even 30 examples can work — but you need *some* signal.)
- **You need rich agent observability with LangFuse-style traces today.** Native integration is limited; bolt-on via MLflow tracing works but is not first-class [eito.substack.com].
- **Streaming partial outputs is essential.** DSPy supports `dspy.streamify` from 2.6.0+ but it's newer than the rest of the stack — verify your version [dspy.ai/tutorials/deployment/].

---

## 7. 生态对照 (Ecosystem context)

### Layer positioning

DSPy is **not** the same layer as LangChain / LlamaIndex / LangGraph. It sits *underneath* them as a compiler for the individual LM calls inside those orchestration layers [langwatch.ai/blog/best-ai-agent-frameworks-in-2025-...].

```
┌──────────────────────────────────────────────┐
│  Orchestration:  LangGraph, CrewAI            │ ← graphs, agents, state
├──────────────────────────────────────────────┤
│  Retrieval:      LlamaIndex                   │ ← ingestion, indexing
├──────────────────────────────────────────────┤
│  Compiler:       DSPy                         │ ← signatures, modules, compile
├──────────────────────────────────────────────┤
│  Generation:     Guidance, LMQL, Outlines     │ ← single-call grammar control
├──────────────────────────────────────────────┤
│  Inference:      vLLM, llama.cpp, Anthropic   │ ← serving
└──────────────────────────────────────────────┘
```

### vs LangChain

- **LangChain**: orchestration, batteries-included, hand-authored prompts. 71 lines for a typical agent.
- **DSPy**: compile-the-prompt, 30 lines for the same task [eito.substack.com — code comparison].
- **Together**: rare. LangChain's prompt templates collide with DSPy's compilation model. Pick one per pipeline; if you must combine, isolate DSPy modules behind clean Python interfaces inside LangChain chains.

### vs LangGraph

- **LangGraph** = stateful graph orchestration (nodes, edges, checkpointing, human-in-loop).
- **DSPy** = the LM call *inside* a node.
- **Together**: highly complementary. Pattern: each LangGraph node's body invokes a compiled DSPy program. LangGraph handles state and routing; DSPy handles prompt quality [rajapatnaik.com/blog/2025/10/23/langgraph-dspy-gepa-researcher]. Quote from acldigital.com: "DSPy fits into the Prompt Management & Optimization layer—bringing software engineering discipline to prompting" while LangGraph fits the orchestration layer.

### vs LlamaIndex

- **LlamaIndex** = data ingestion + retrieval + query engines.
- **DSPy** = optimizes the *generator / reranker / synthesizer* component.
- **Together**: standard pattern. LlamaIndex retrieves passages → DSPy-compiled `Predict(context, question -> answer)` synthesizes. JetBlue's chatbot uses exactly this split — retrieval quality + answer quality as separate metrics, DSPy optimizes both [databricks.com/blog/optimizing-databricks-llm-pipelines-dspy].

### vs Guidance / LMQL / Outlines

- These control **one LM call** at the token level (grammars, regex, JSON schema).
- **DSPy** controls **multi-call programs** at the optimization level.
- **Together**: orthogonal. Use Outlines for "force valid JSON"; use DSPy for "make the JSON-emitting prompt good." DSPy's typed `OutputField` already pushes the LM toward structure but doesn't guarantee grammar conformance [dspy.ai/faqs/].

### vs raw prompt engineering

- Raw prompts win when: one-shot, signature unstable, no metric, audit constraints (Section 6).
- DSPy wins when: pipeline ≥ 2 LM calls, you have ≥ 30 labeled examples, you'll swap models or scale, you have a metric (even an LLM-judge one — but harden it per Case C).

### Production case study evidence

- **JetBlue + Databricks**: RAG chatbot. Before DSPy = manual prompt tuning on retrieval/answer quality metrics. After = DSPy directly optimizes those metrics, faster development cycle [tastytechbytes.com/databricks-dspy-jetblue-ai-chatbot].
- **Haize Labs**: automated LLM red-teaming.
- **In production at**: Shopify, Databricks, Dropbox, JetBlue, Moody's, AWS, Sephora, VMware [dspy.ai].
- **Tobi Lütke (Shopify CEO)**: "Both DSPy and (especially) GEPA are currently severely under hyped in the AI context engineering world" [eito.substack.com].

---

## Quick-reference appendix

### Minimal end-to-end (verbatim from cheatsheet) [dspy.ai/cheatsheet/]

```python
import dspy

# 1. Signature
class BasicQA(dspy.Signature):
    """Answer questions with short factoid answers."""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="often between 1 and 5 words")

# 2. Module
qa = dspy.ChainOfThought(BasicQA)

# 3. Metric
def metric(ex, pred, trace=None):
    return ex.answer.lower() in pred.answer.lower()

# 4. Compile
from dspy.teleprompt import MIPROv2
optimizer = MIPROv2(metric=metric, auto="light")
compiled = optimizer.compile(qa, trainset=trainset)

# 5. Save / load
compiled.save("v1.json")
```

### Decision tree (one screen)

```
Have a metric? ─── No ──► Stop. Build a metric first. (Or skip DSPy.)
   │
   Yes
   │
Have ≥ 30 examples? ─── No ──► Stop. Collect more data, or use LabeledFewShot(k=8) as floor.
   │
   Yes
   │
Have textual error feedback? ─── Yes ──► dspy.GEPA
   │
   No
   │
≤ 10 examples? ──► BootstrapFewShot
30–50?         ──► BootstrapFewShotWithRandomSearch
50–200?        ──► MIPROv2(auto="light", max_bootstrapped_demos=4)
200+?          ──► MIPROv2(auto="light" → "medium" if gains; "heavy" only if 300+ and budget)
Need to ship small model? ──► chain BootstrapFinetune after MIPROv2
```

### Anatomy of a compiled `program.json`

After `compiled.save("v1.json")`, the file is plain JSON. Per-predictor it contains [dspy.ai/tutorials/saving/]:

```json
{
  "predictor_name": {
    "signature_instructions": "Given the context, answer the question with a short factoid...",
    "signature_prefix": "Answer:",
    "extended_signature_instructions": "...",
    "demos": [
      {"question": "...", "reasoning": "...", "answer": "..."},
      ...
    ],
    "signature": {
      "instructions": "...",
      "fields": [{"prefix": "Question:", "description": "..."},  ...]
    }
  }
}
```

What changes when you compile:
- **Instructions** are rewritten by the optimizer (MIPROv2 proposes; Bayesian search picks).
- **Demos** are bootstrapped: the teacher program is run on trainset, metric filters keep the good ones.
- **Signature shape** does NOT change — that's your code's job.

What does NOT change between LMs (so you can read across artifacts):
- The signature field names.
- The metric.
- The program's Python structure (which modules call which).

What DOES change between LMs (so you can't reuse):
- The instructions (smaller LMs need simpler, more explicit wording).
- The demos (smaller LMs benefit from more, simpler demos; larger LMs benefit from fewer, richer ones).

### Constraint primitives — `dspy.Assert` vs `dspy.Suggest`

For self-refining pipelines [dspy.ai/learn/programming/7-assertions/, arxiv.org/pdf/2312.13382]:

```python
# Hard: halts after max retries with dspy.AssertionError
dspy.Assert(len(pred.answer) < 100, "Answer must be < 100 chars")

# Soft: retries with feedback in prompt, logs failure, continues
dspy.Suggest(is_valid_json(pred.output), "Output must be valid JSON")
```

When a constraint fails, DSPy backtracks to the previous module and re-runs with the error message injected into the prompt. This is *self-refinement at inference time* — distinct from compile-time optimization.

Use `Assert` during development (catch bugs hard). Use `Suggest` in production (degrade gracefully).

### Key citations

- DSPy paper (ICLR 2024): [arxiv.org/abs/2310.03714]
- GEPA paper (ICLR 2026 oral): [arxiv.org/abs/2507.19457]
- DSPy Assertions paper: [arxiv.org/pdf/2312.13382]
- Docs hub: [dspy.ai/learn/]
- Optimizer guide: [dspy.ai/learn/optimization/optimizers/]
- FAQ: [dspy.ai/faqs/]
- Deployment: [dspy.ai/tutorials/deployment/]
- JetBlue case study: [databricks.com/blog/optimizing-databricks-llm-pipelines-dspy]
- Misunderstanding piece (Miyamura): [eito.substack.com/p/dspy-the-most-misunderstood-agent]
- MIPROv2 community Q&A: [github.com/stanfordnlp/dspy/issues/1596]
- Compile hang pattern: [github.com/stanfordnlp/dspy/issues/1970]
- LangGraph vs DSPy issue: [github.com/stanfordnlp/dspy/issues/1078]
