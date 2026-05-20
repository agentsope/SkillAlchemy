# R1 — Architecture & Mental Model

## The four primitives

DSPy = **D**eclarative **S**elf-improving **Py**thon. The architecture deliberately mirrors PyTorch [arxiv.org/abs/2310.03714].

| DSPy primitive | PyTorch analog | What it specifies |
|---|---|---|
| **Signature** | Tensor shape contract / `forward()` interface | What inputs go in, what outputs come out, with semantically-meaningful field names |
| **Module** | `nn.Module` (Linear, Transformer) | How to turn inputs into outputs (Predict / ChainOfThought / ReAct / ProgramOfThought) |
| **Teleprompter** (Optimizer) | `torch.optim.Adam`, `lr_scheduler` | Search algorithm over instruction strings + few-shot demos |
| **Compile** | Training loop | Bakes optimized instructions + demos into a state-dict (JSON) |

## Signatures — the declarative spec

Two forms [dspy.ai/learn/programming/signatures/]:

**Inline (string)**: `"question -> answer"`, `"context: list[str], question: str -> answer: str"`, `"sentence -> sentiment: bool"`. Quick prototyping. Field names carry semantics; rename them like function parameters in good code.

**Class-based**:

```python
class Emotion(dspy.Signature):
    """Classify emotion."""
    sentence: str = dspy.InputField()
    sentiment: Literal['joy', 'anger', 'fear'] = dspy.OutputField()
```

Use class form when you need:
- Docstring (becomes part of the prompt).
- `desc=...` hints on individual fields.
- Literal/enum constraints on output types.
- Pydantic models as fields.

**Crucial insight**: the signature is the *only* natural-language hint the optimizer has *before* seeing data. Bad field names ("input1", "output") hobble the optimizer.

## Modules — strategy primitives

Built-in modules [dspy.ai/learn/programming/modules/]:

| Module | What it does | When to use |
|---|---|---|
| `dspy.Predict` | Bare LM call, no extras | Trivial classification, well-specified extraction |
| `dspy.ChainOfThought` | Adds intermediate reasoning field | **Default choice per docs** |
| `dspy.ProgramOfThought` | LM emits code; code is executed; result feeds final output | Math, parsing, anything where computation grounds the answer |
| `dspy.ReAct` | Tool-using loop (Reason + Act) | When the LM needs to call external tools |
| `dspy.MultiChainComparison` | Compare N CoT outputs to produce refined answer | Hard cases where consistency matters |
| `dspy.majority` | Vote across multiple predictions | Quick ensemble |

**Composition** is plain Python:

```python
class RAG(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=3)
        self.generate = dspy.ChainOfThought("context, question -> answer")
    def forward(self, question):
        ctx = self.retrieve(question).passages
        return self.generate(context=ctx, question=question)
```

DSPy traces every sub-module's LM call during compile [dspy.ai/learn/programming/modules/].

## Teleprompters — the optimizers

These are **search algorithms over (instruction text × few-shot demo set)** for every predictor in your program. Names + algorithm summary [dspy.ai/learn/optimization/optimizers/]:

- **LabeledFewShot(k)** — trivial: pick k labeled examples, stuff into prompt.
- **BootstrapFewShot** — teacher (= student by default) generates candidate demos; metric filters them.
- **BootstrapFewShotWithRandomSearch** — same + random search over multiple bootstrap rounds.
- **MIPROv2** — Bayesian optimization over (proposed instructions × bootstrapped demos). Three auto modes: `light`, `medium`, `heavy` [dspy.ai/api/optimizers/MIPROv2/].
- **COPRO** — coordinate-ascent over instructions only.
- **GEPA** — reflective evolution; uses textual feedback, not just scalar metric. Best sample efficiency [arxiv.org/abs/2507.19457].
- **BootstrapFinetune** — distills a compiled program into weight updates for a smaller LM.
- **SIMBA**, **InferRules**, **KNNFewShot**, **BetterTogether** — specialized variants.

## Compile — what actually happens

`teleprompter.compile(student, trainset=...)` runs:

1. Generate candidate demonstrations by running the *teacher* program on training examples, keeping outputs that pass the metric.
2. Propose candidate instructions (for MIPROv2/GEPA: data-aware and demo-aware).
3. Score combinations on a validation minibatch.
4. Full-validate the top candidates.
5. Return a `compiled` program whose `Predict` sub-modules have updated `instructions` and `demos` attributes.

The artifact is `program.json` — plain text [dspy.ai/tutorials/saving/]. It contains, per predictor: `signature_instructions`, `demos`, `signature` schema.

## The PyTorch analogy in full

```
PyTorch                  DSPy
─────────────────────    ──────────────────────────
nn.Module               dspy.Module
forward()               forward()
nn.Linear, nn.Conv2d    dspy.Predict, dspy.ChainOfThought
loss_fn                 metric(example, pred) -> score
torch.optim.Adam        dspy.MIPROv2 / GEPA / BootstrapFewShot
optimizer.step()        teleprompter.compile()
state_dict              compiled.dump_state() → JSON
model.eval()            (just call the compiled program)
```

The analogy clarifies the most-asked question: **why compile, not write?** Same reason you don't hand-tune neural-net weights. The combinatorial space of (instruction × demo set) is too large for a human to search; an algorithm does it better given a metric [Khattab, Scale By the Bay 2023].

## What "prompt as program" actually means

Three concrete commitments:

1. **The prompt is generated artifact, not source.** You author signatures + modules + metrics. The optimizer authors the prompt.
2. **The program has parameters.** Instructions and demos are the "weights." They change when you compile.
3. **The program is portable across LMs — but each LM needs its own compile.** A compiled artifact is a `(program × LM × dataset)` triple. Change any, recompile.
