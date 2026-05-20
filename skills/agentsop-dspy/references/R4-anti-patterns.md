# R4 — Anti-patterns & Boundaries

## Anti-patterns (in order of frequency)

### 1. Compiling without a metric
DSPy without a metric collapses to verbose prompt templating. Optimizers *require* a metric function. If you cannot articulate one — even a noisy LLM-judge — DSPy provides no advantage over a hand-authored prompt [dspy.ai/learn/optimization/overview/].

### 2. Compiling on too few examples (< 30)
Below ~30 labeled examples, the optimizer memorizes the training set. The unusual 20/80 (train/val) split exists precisely *because* "prompt-based optimizers often overfit to small training sets" [dspy.ai/learn/optimization/overview/]. MIPROv2 specifically wants 200+.

### 3. Starting at `auto="heavy"`
`auto="heavy"` on a large trainset can be tens of dollars and hours. Always probe with `light` first. If `light` doesn't help, `heavy` won't either — the bottleneck is upstream [Case A].

### 4. Single-LLM-judge as the *only* metric
LLM judges exhibit documented self-preference, recency, score-ID, and rubric-order biases [arxiv.org/pdf/2506.02592, arxiv.org/pdf/2509.26072]. Decompose into sub-judges and add explicit penalties (especially length) [Case C].

### 5. Editing the compiled JSON by hand
The artifact is readable JSON. Hand-editing invalidates the metric-optimization guarantee. Either recompile or leave it alone.

### 6. Reusing a GPT-4-compiled program on a smaller model
Compiled programs are `(program × LM)` pairs. The demos and instructions are tuned to a model's quirks. Smaller models often need *more* and *simpler* demos — recompile [Case B].

### 7. Treating DSPy modules as agents
`dspy.ReAct` is a thin tool-use loop, not a multi-agent orchestration framework. For stateful, branching, long-running workflows, combine with LangGraph; don't try to bend DSPy into that shape [R5].

### 8. Ignoring program structure when optimization stalls
If MIPROv2 light + medium both flatline, the bottleneck is the program graph (decomposition, module choice), not the optimizer. Trying yet another optimizer is the wrong next step [dspy.ai/learn/optimization/overview/].

### 9. Skipping the unusual 20/80 split
The reversed train/val ratio is intentional. Standard 80/20 splits enable prompt overfitting. Note: GEPA differs — it follows standard ML splits (maximize train) [dspy.ai/learn/optimization/overview/].

### 10. Forgetting cache config in serverless
DSPy caches default to a writable disk path; this breaks in AWS Lambda and similar. Set `cache=False` in `dspy.LM()` or set `DSP_CACHEDIR` / `DSPY_CACHEDIR` to `/tmp` [dspy.ai/faqs/].

### 11. Confusing `dspy.Assert` with `dspy.Suggest`
`Assert` halts execution after max retries (use during development). `Suggest` logs failure and continues (use during evaluation). They have different semantics; swapping them silently masks issues [dspy.ai/learn/programming/7-assertions/].

### 12. Not pinning DSPy version in production
The API has shifted across 2.x → 3.x (e.g. `dspy.LM` replaced older client patterns; cache env var names changed). Pin the version in `pyproject.toml`; record it in the saved program's directory (whole-program save mode includes dep versions) [dspy.ai/tutorials/saving/].

---

## Boundaries — when NOT to use DSPy

### Hard "no"

- **One-shot tasks**: "summarize this one email" → raw API. Compile loop has no payoff.
- **No metric and none is achievable**: without signal, optimization is impossible. (Note: an LLM-judge metric counts as a metric — but harden it per Case C.)
- **Compliance / regulated audit requires verbatim human-authored prompts**: compiled prompts are machine-generated artifacts.

### Soft "no" / "not yet"

- **Task signature is still changing daily**: stabilize the I/O contract before paying compile costs.
- **You need first-class LangFuse / OpenLLMetry observability today**: native integration is limited; works via MLflow tracing but is bolt-on [eito.substack.com].
- **The team has zero ML/PyTorch background**: the "compile" mental model is foreign. Education cost is real. Start with `LabeledFewShot` (trivial) to climb the ladder.

### Boundary case — both useful

- **You have a stable LangChain agent today**: DSPy can replace specific *LLM-call nodes* within it. But mixing DSPy compilation with LangChain's hand-authored prompt templates inside the same node is friction. Isolate DSPy modules behind clean function interfaces.

---

## "DSPy is the right tool" checklist

Use DSPy when *all* of these are true:
- [ ] Pipeline has ≥ 2 LM calls (or one critical call worth tuning).
- [ ] You have or can build ≥ 30 labeled examples.
- [ ] You have or can build a metric (exact match, multi-judge, or text feedback).
- [ ] You will swap models, scale, or iterate the pipeline multiple times.
- [ ] You can afford ~$2–$10 and 5–60 minutes per compile cycle.
- [ ] No regulatory/audit constraint requires verbatim human prompts.

Three or more "no" → reconsider. All "yes" → DSPy is high-leverage.
