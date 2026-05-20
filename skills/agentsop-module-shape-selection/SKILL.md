---
name: agentsop-module-shape-selection
version: 0.1.0
description: >-
  ENHANCE overlay on [[dspy]] — the upfront rubric for choosing a reasoning SHAPE (Predict /
  ChainOfThought / ReAct / ProgramOfThought) BEFORE you write a prompt or pick an optimizer.
  The local `dspy` skill lists the modules but never surfaces the *selection criterion*:
  reasoning shape is chosen by task structure, not by reflexively defaulting to CoT.
  Activate every time a new LM-calling node/step is added to a pipeline. Do NOT activate for
  one-shot prompts, optimizer/teleprompter choice (that is the dspy SOP's job), or non-LM
  control flow. Search keywords: chain of thought vs ReAct, when to use CoT, reasoning type,
  ReAct vs CoT vs PoT, which dspy module, predict vs chain of thought.
---

# M2 — Module-Shape Selection (CoT / ReAct / PoT / Predict)

> *"Pick the lowest-power Module that works. Default to ChainOfThought."*
> — DSPy docs [dspy.ai/learn/programming/modules/]
>
> This overlay sharpens that line into a **rubric**: the default is not a law. The
> shape is a function of the *task structure*, and CoT is only one of four answers.

This is an **enhancement overlay**. It assumes the [[dspy]] library skill is loaded
(it provides `dspy.Predict`, `dspy.ChainOfThought`, `dspy.ReAct`,
`dspy.ProgramOfThought` APIs and install). This file adds only the *decision* the lib
skill leaves implicit. Cross-link: [[dspy]], and the optimizer SOP `[[agentsop-dspy]]`.

---

## 1. 何时激活 (When to activate)

Activate the instant you are about to **add or wrap an LM-calling step**:

| Trigger | Signal |
|---|---|
| New node | A LangGraph/CrewAI node body, or a `forward()` line, is about to call an LM |
| New `dspy.<Module>(Sig)` | You are typing `dspy.ChainOfThought(...)` on reflex — stop and run the rubric |
| Refactor | An existing `Predict` "feels weak" or a `ChainOfThought` "feels wasteful" |
| Pipeline growth | A multi-stage program adds a stage; each stage needs its own shape decision |
| Tool appears | A function/API/search/calculator is now available to the step |

**Do NOT activate** when:
- The work is a **one-shot prompt** — just call the LM; shape ceremony has no payoff.
- You are choosing the **optimizer / teleprompter** (MIPROv2, GEPA, BootstrapFewShot) —
  that is the [[agentsop-dspy]] workflow, a *later* stage. Shape comes first, optimizer second.
- The step is **non-LM control flow** (a `if`, a DB read, a deterministic transform).

Shape selection is **upstream of optimization**. You pick the shape in Stage 1
(Programming) of the dspy SOP, before any metric or compile [dspy.ai/learn/].

---

## 2. 核心心智模型 (Core mental model)

> **Reasoning shape is chosen by task structure, not by defaulting to CoT.**

The lib skill shows four modules side by side and a "Best Practices" note that says
"Start with Predict, add ChainOfThought if needed" [`~/.claude/skills/dspy` Best
Practices §1]. In practice that collapses into a **CoT-everywhere reflex**, because
"if needed" is never operationalized. This overlay operationalizes it.

A module's *shape* is the **control-flow contract** between the LM and your code:

```
                 does the answer need        is there a real
                 intermediate reasoning?      tool to call?
                         │                          │
   simple lookup ── no ──┤                          │
   /classify   ─────────►│ Predict                  │
                         │                          │
   analytic /   ── yes ──┤── no tool ──────────────►│ ChainOfThought
   judgement            │                          │
                         │                          │
   needs to act ─────────┼── yes, real tool ───────►│ ReAct(tools=[...])
   /look things up      │                          │
                         │                          │
   math / counting ──────┴── deterministic compute ►  ProgramOfThought
   / strict parsing                                   (code grounds answer)
```

Three shifts the agent must internalize:

1. **The default is a *probe*, not a *destination*.** "Default to CoT" means "when
   unsure, CoT is the safe baseline" — not "always ship CoT." Every CoT you ship that
   a Predict would have matched is pure token tax [dspy.ai/learn/programming/modules/].

2. **Shape is structural, optimizer is statistical.** Shape = which control flow
   (this overlay). Optimizer = which demos/instructions get baked in ([[agentsop-dspy]] §4).
   A wrong shape cannot be fixed by a better optimizer — MIPROv2 on the wrong shape
   just optimizes the wrong thing [dspy.ai/learn/optimization/overview/].

3. **Each shape has a cost signature.** Predict ≈ 1 call, no reasoning tokens. CoT ≈ 1
   call + a `reasoning`/`rationale` field (more output tokens). ReAct ≈ N calls (a
   tool loop). PoT ≈ 1 LM call + code execution. Shape choice *is* a cost choice.

---

## 3. SOP (Classify → Pick → Measure)

A three-step gate, run **per LM-calling step** (not per pipeline):

### Step 1 — Classify the task structure

Answer two yes/no questions about the step's *output*:

- **Q1: Does a correct answer require visible intermediate reasoning?**
  (Multi-hop inference, judgement, "why", trade-off weighing → yes. Lookup, label,
  format-conversion → no.)
- **Q2: Does producing the answer require *acting* — calling a tool, fetching data,
  or running deterministic computation?**
  (Search/API/DB → tool. Arithmetic/counting/strict-parse → computation. Neither → no.)

### Step 2 — Pick the shape from the selection card (§4)

Map the (Q1, Q2) answers straight onto the card. Do not negotiate with the reflex.

### Step 3 — Measure whether the shape earns its cost

A shape is only justified if it *beats the cheaper shape below it*. Before shipping
anything heavier than `Predict`:

1. Run the candidate shape and the next-cheaper shape on **5–10 hand-picked examples**.
2. Diff outputs with `dspy.inspect_history(n=3)` [dspy.ai/learn/programming/modules/].
3. **Keep the heavier shape only if it changes answers for the better.** If CoT and
   Predict produce the same labels on a classify task, ship Predict.
4. Record the call in `intermediate/operation_candidates.json` so the next node reuses
   the reasoning instead of re-deriving it.

**Exit criterion:** the chosen shape produces plausible outputs on 5+ examples AND no
cheaper shape matches it. Then — and only then — proceed to metric + optimizer ([[agentsop-dspy]]).

---

## 4. 操作模型 (Selection card)

### 4.1 The four shapes

| Task structure | Shape | DSPy module | Cost signature | Evidence |
|---|---|---|---|---|
| Lookup / classify / extract / format-convert (no reasoning needed) | **Predict** | `dspy.Predict(Sig)` | 1 call, no reasoning tokens — lowest overhead | [dspy.ai/learn/programming/modules/], lib `Predict` §2 |
| Analytic / judgement / multi-hop inference (reasoning helps, no tool) | **Chain of Thought** | `dspy.ChainOfThought(Sig)` | 1 call + `reasoning`/`rationale` field — **adds output tokens** | [dspy.ai/learn/programming/modules/], lib `ChainOfThought` §2 |
| Tool-use: search / API / DB / retrieval / calculator | **ReAct** | `dspy.ReAct(Sig, tools=[...])` | N calls — a think→act→observe loop | [dspy.ai/learn/programming/modules/], lib `ReAct` §2 |
| Math / counting / unit conversion / strict parsing | **Program of Thought** | `dspy.ProgramOfThought(Sig)` | 1 LM call → generated code → executed; answer grounded in execution | [dspy.ai/learn/programming/modules/], lib `ProgramOfThought` §2 |

### 4.2 Cost note — CoT is not free

`ChainOfThought` adds a generated `reasoning` field to **every** call. On a high-volume
classify step (e.g. routing 100k tickets/day), that reasoning field is pure cost with
zero accuracy gain if the labels don't change. The lib skill's "add CoT if needed"
[lib Best Practices §1] is correct but under-specified: *needed* means "Step 3 measured
a lift." Default to CoT when **unsure**; ship Predict when **measured equal**.

### 4.3 Tie-breakers and escalation

| Situation | Action | Why |
|---|---|---|
| Math task but you trust the LM's mental arithmetic | Still prefer **PoT** | Code execution removes arithmetic hallucination [dspy.ai/learn/programming/modules/] |
| Reasoning helps AND a tool exists | **ReAct** (it does CoT *inside* the loop) | ReAct subsumes CoT when tools are present |
| Hard analytic case, single CoT is unstable | `dspy.MultiChainComparison` / `dspy.majority` over N CoT samples | Vote across samples — escalation, not a base shape [dspy-sop §4.2] |
| "Tool" is actually a pure Python function with no I/O | Inline the function; use **CoT or Predict**, not ReAct | A ReAct loop with a trivial deterministic helper is wasted calls (Case B) |

### 4.4 Selection card as a one-liner

```
no reasoning, no tool        → Predict
reasoning, no tool           → ChainOfThought
any real tool / action       → ReAct(tools=[...])
math / count / strict parse  → ProgramOfThought
```

---

## 5. 困境决策案例 (Dilemma cases)

### Case A — "CoT on a simple classify wastes tokens"

**困境:** A pipeline routes incoming support tickets into 6 categories. The engineer's
reflex was `dspy.ChainOfThought("ticket -> category")` because "reasoning is always
safer." Volume is 100k tickets/day. Is the reasoning field earning its cost?

**约束:**
- The output is one of 6 fixed labels — a closed-set classification.
- Every CoT call emits a `reasoning` field (extra output tokens) × 100k/day.
- Accuracy target already met by a simpler shape in spot-checks (unverified).

**决策步骤 (Step 3 of the SOP, made concrete):**
1. Classify (Step 1): Q1 "needs visible reasoning?" → **no** (closed-set label). Q2
   "needs a tool/compute?" → **no**. The card says **Predict**.
2. The reflex said CoT. Run **both** on 10 hand-picked tickets, diff with
   `dspy.inspect_history(n=3)` [dspy.ai/learn/programming/modules/].
3. If the 6 labels come out identical, the reasoning field changed *nothing* — it is
   pure token tax at 100k/day. **Ship Predict.**
4. If CoT flips 1–2 ambiguous edge cases correctly, keep CoT *only for those* — or
   move ambiguity handling to a second, cheap Predict triage stage.

**结果:** On closed-set classification, Predict typically matches CoT. The CoT-everywhere
reflex would have shipped a per-call reasoning surcharge for no accuracy.

**可提取的操作:** **A closed-set classify/lookup step defaults to Predict. Promote to CoT
only after Step 3 measures a label change — never on reflex.**

---

### Case B — "ReAct without tools is just CoT (with extra failure modes)"

**困境:** An engineer wants an "agentic" answer step and writes
`dspy.ReAct("question -> answer", tools=[])` — or with a single trivial helper that
does no real I/O. Is this actually agentic?

**约束:**
- ReAct's value is the **think → act → observe** loop over *real* tools (search, API,
  DB) [dspy.ai/learn/programming/modules/, lib `ReAct` §2].
- With no real tool, the loop has nothing to observe; it degenerates to reasoning —
  i.e. CoT — but pays for loop overhead and added parsing/failure surface.

**决策步骤:**
1. Classify (Step 1): Q2 "needs a real tool/action?" → **no** (empty or trivial tools).
   The card routes away from ReAct.
2. Recognize that **ReAct with no real tools is just CoT** — the reasoning happens, but
   the action/observation steps are dead weight that can hang or mis-parse.
3. If reasoning genuinely helps → use **`dspy.ChainOfThought`** directly. If it doesn't →
   **`dspy.Predict`**.
4. Add `dspy.ReAct(tools=[...])` back **only** when a real external capability appears
   (web search, retrieval, calculator API). Then ReAct subsumes CoT inside its loop.

**结果:** Replacing tool-less ReAct with CoT removes loop overhead and a class of
tool-parsing failures while preserving the reasoning. No capability is lost because none
existed.

**可提取的操作:** **ReAct earns its loop only when at least one real, I/O-bearing tool
exists. Tool-less ReAct → downgrade to CoT (or Predict).**

---

### Case C — "Math step: trust CoT's arithmetic or ground it with PoT?"

**困境:** A step computes "15% of 240, then subtract the 3-item average." The reflex is
`ChainOfThought` because it "shows the math." Is shown arithmetic *correct* arithmetic?

**约束:**
- LMs hallucinate arithmetic even when the reasoning prose looks right.
- `ProgramOfThought` generates and **executes** code, grounding the number in a real
  computation [dspy.ai/learn/programming/modules/, lib `ProgramOfThought` §2].

**决策步骤:**
1. Classify (Step 1): Q2 "needs deterministic computation?" → **yes (math)**. Card →
   **ProgramOfThought**, not CoT.
2. Use `dspy.ProgramOfThought("question -> answer")`; it emits `answer = 240*0.15 - ...`
   and runs it [lib `ProgramOfThought` §2].
3. Reserve CoT for the *framing* ("which numbers matter") only if that itself is
   ambiguous — then compose: CoT to extract operands → PoT to compute.

**结果:** PoT removes arithmetic hallucination at the cost of one code execution. CoT on
the same step ships numbers that *look* derived but may be wrong.

**可提取的操作:** **Any step whose answer is a computed number/count/parse defaults to
PoT. CoT's prose is not a substitute for executed code.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **The CoT-everywhere reflex.** Reaching for `dspy.ChainOfThought` on every step
   "to be safe." Safe ≠ free; the reasoning field is a per-call token tax. CoT is the
   default *when unsure*, not the default *always* (Case A) [dspy.ai/learn/programming/modules/].
2. **ReAct with no real tools.** A `ReAct(tools=[])` or a ReAct over a trivial pure
   function is just CoT plus loop overhead and extra failure modes (Case B).
3. **CoT prose as a math guarantee.** Trusting a reasoning field's arithmetic instead of
   executing it. Use PoT for computed answers (Case C).
4. **Picking shape by feel after writing the prompt.** Shape is an *upfront* structural
   decision; choosing it post-hoc means the prompt was written against the wrong contract.
5. **Conflating shape with optimizer.** "MIPROv2 will fix it" — an optimizer cannot
   repair a wrong shape; it optimizes whatever shape you gave it [dspy.ai/learn/optimization/overview/].
6. **Predict on a genuinely analytic task.** Under-powering to save tokens when the task
   needs multi-hop reasoning — the mirror failure of the CoT reflex.
7. **One shape for the whole pipeline.** Each LM-calling step gets its own classify→pick;
   a retrieve→reason→format pipeline may be ReAct→CoT→Predict.

### Boundaries (where this overlay stops)

- **Optimizer / teleprompter choice** (BootstrapFewShot, MIPROv2, GEPA, finetune): not
  here — see [[agentsop-dspy]] §4. Shape first, optimizer second.
- **Signature design** (field names, types, `desc=`): the lib skill [[dspy]] Core
  Concepts §1. Shape assumes the signature exists.
- **Metric design and compile-cost guardrails:** [[agentsop-dspy]] §4.3–4.4.
- **One-shot / no-pipeline prompting:** out of scope; just call the LM.
- **Token-level output constraints** (force-valid-JSON): Outlines/Guidance, orthogonal
  to shape ([[agentsop-dspy]] §7).

---

## 7. 跨框架对照 (Cross-framework correspondence)

The shape decision is framework-independent; only the spelling changes.

| Reasoning shape | DSPy module | LangChain equivalent | Raw-prompting equivalent |
|---|---|---|---|
| **Predict** (lookup/classify, no reasoning) | `dspy.Predict(Sig)` | `LLMChain` / direct `model.invoke` with a plain template | Single prompt, "answer directly" — no scratchpad |
| **Chain of Thought** (analytic, no tool) | `dspy.ChainOfThought(Sig)` | `LLMChain` with a "think step by step" prompt; no agent | "Let's think step by step…" then answer |
| **ReAct** (tool-use loop) | `dspy.ReAct(Sig, tools=[...])` | `create_react_agent` / `AgentType.ZERO_SHOT_REACT_DESCRIPTION` + tools | Manual Thought/Action/Observation loop you parse yourself |
| **Program of Thought** (math/parse via code) | `dspy.ProgramOfThought(Sig)` | `PythonREPLTool` agent / `LLMMathChain` | "Write Python to compute the answer," then exec |

**Reading the table:** the *task-structure question* (reasoning? tool? compute?) is the
invariant. DSPy makes the choice a one-line module swap with a stable signature; LangChain
makes it an agent-type/chain choice; raw prompting makes it a scratchpad-format choice you
hand-maintain. The selection rubric in §3–§4 is the same in all three columns — only the
binding to code differs. This is why the overlay lives *above* [[dspy]]: the rubric
transfers even when you leave DSPy.

**Bridge to the rest of the stack:** once the shape is chosen here, hand off to
[[agentsop-dspy]] for metric + optimizer + compile, and to [[dspy]] for the module API,
signature syntax, and LM-provider wiring.

---

### Source map

- DSPy module semantics & "default to ChainOfThought" line: [dspy.ai/learn/programming/modules/]
- Local source `dspy-sop` SKILL.md §3 (Stage 1 module pick), §4.2 (module selection table)
- Local lib skill `~/.claude/skills/dspy/SKILL.md` §Core Concepts 2 (Predict/CoT/ReAct/PoT
  examples), Best Practices §1 ("start simple, iterate")
- Full evidence trace: `references/R1-source-evidence.md`
- Extracted operations: `intermediate/operation_candidates.json`
