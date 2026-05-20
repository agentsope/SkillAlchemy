---
name: agentsop-code-execution-decision
version: 0.1.0
description: >-
  Decision rubric for when an LM agent should write-and-run code (Program-of-Thought / code
  interpreter) versus reason in natural language: classify each step as deterministic-
  computable (emit + execute code, feed the result back) vs judgment (stay in prose). Use
  when designing or debugging an agent step that does arithmetic/parsing/data transforms,
  when prose reasoning hallucinates a computation (under-coding), or when a sandbox round-
  trip is wasted on a judgment task (over-coding). Search keywords: code interpreter, agent
  does math wrong, calculator hallucination, when to run code vs reason, program of thought,
  PoT, tool vs reasoning.
domain: |
  Deciding when an LM agent should write-and-run code (Program-of-Thought / code interpreter)
  versus reason in natural language. An enhancement overlay on top of DSPy's ProgramOfThought
  module, which ships the mechanism but not the decision rubric.
type: enhancement-overlay
source: |
  DSPy ProgramOfThought module + docs [dspy.ai/learn/programming/modules/];
  "Program of Thoughts" (Chen et al., arXiv 2211.12588);
  PAL: Program-aided Language Models (Gao et al., arXiv 2211.10435);
  OpenAI Code Interpreter / Assistants code-tool docs;
  Anthropic code-execution tool docs;
  LangChain PythonREPLTool;
  sibling skill output-format-by-model (PoT for math/parse content shape).
audience: |
  Coder-agent authors, tool-use harness designers, RAG/eval pipeline builders deciding
  whether a step should emit executable code or stay in prose.
status: tool-skill
---

# Code-Execution Decision — emit-code-vs-reason

> **One-liner**: LMs are unreliable calculators but reliable coders. When the answer needs
> determinism and precision — arithmetic, exact data manipulation, deterministic transforms —
> emit code and run it. When the answer needs judgment, taste, or open-ended synthesis, reason
> in natural language. The cost of getting this gate wrong is silent: prose arithmetic
> *hallucinates a plausible-looking wrong number*, and over-coding a judgment task burns a
> sandbox round-trip for nothing.

This is an **enhancement overlay**. DSPy already gives you `dspy.ProgramOfThought` (PoT) —
the *mechanism* for write-then-execute. What it does not give you is the *decision rubric* for
when to reach for it. That rubric is this skill. Cross-link the sibling
[[agentsop-output-format-by-model]] (which decides *how* code-shaped content should be serialized) and
[[agentsop-test-fix-loop]] (which closes the execute → error → retry loop).

---

## 1. 何时激活 (When to activate)

Activate this skill **before** committing a step to a reasoning strategy whenever the task has a
**verifiable, deterministic core** — or whenever you catch an agent doing arithmetic in prose.

| Trigger | Signal |
|---|---|
| Arithmetic / math | "compute the compound interest", "what's 17.5% of $4,392.18", multi-step word problems, unit conversions, date deltas |
| Precise data manipulation | "sort these 240 rows by the third column", "dedupe and count", "join these two lists on id", "parse this CSV and sum column B" |
| Deterministic transforms | regex extraction, string reformatting, base conversion, hashing, sorting, set operations |
| Symbolic / combinatorial | "how many distinct permutations", "solve this system of equations", calendar/scheduling math |
| You see a model doing math in prose | "Let me add: 1,204 + 8,991 + ... = 10,195" — almost always worth a code check |
| Choosing a DSPy module | deciding between `ChainOfThought` and `ProgramOfThought` for a signature [dspy.ai/learn/programming/modules/] |

**Anti-triggers** (do NOT reach for code execution):
- The task is **judgment**: tone, summarization, ranking by quality, "is this reply empathetic?", design tradeoffs, open-ended explanation.
- The "computation" is trivial and within the model's reliable range (single-digit arithmetic, a 3-item count) — the sandbox round-trip costs more than it saves.
- No sandbox is available and the determinism requirement is soft.
- The output's *consumer* is a human reading prose, and an approximate answer is acceptable.

---

## 2. 核心心智模型 (Core mental model)

> **LMs are unreliable calculators but reliable coders.**

A language model predicts the *next token*, not the *correct value*. When you ask it to add
`48,217 + 9,884` in prose, it emits the most *plausible-looking* digit sequence — which is
frequently wrong, and wrong in a way that looks right. The same model can write
`48217 + 9884` as a Python expression flawlessly, because emitting the *program* is a
pattern-matching task it is genuinely good at, and the *Python interpreter* is a deterministic
oracle. This decoupling — model writes the recipe, interpreter computes the result — is the
entire thesis of Program-of-Thought (PoT) [arXiv 2211.12588] and PAL [arXiv 2211.10435].

```
            ┌────────────────────────────────────────────────────────┐
            │  THE GATE: does this answer need determinism/precision?  │
            └────────────────────────────────────────────────────────┘
                       │                                  │
              YES (computable)                     NO (judgment)
                       │                                  │
                       ▼                                  ▼
            ┌─────────────────────┐            ┌─────────────────────┐
            │ EMIT CODE           │            │ REASON IN PROSE     │
            │ model writes recipe │            │ model is the engine │
            │ interpreter = oracle│            │ no oracle exists    │
            └─────────────────────┘            └─────────────────────┘
                       │
                       ▼
            sandbox → run → feed result back into LM → LM narrates/uses it
```

**Two failure modes the gate prevents:**

| Failure | Mechanism | Symptom |
|---|---|---|
| **Under-coding** (reason when you should compute) | LM hallucinates a calculation it cannot reliably perform | A confident, wrong, plausible-looking number; off-by-one counts; arithmetic that "looks" right |
| **Over-coding** (compute when you should reason) | LM wraps a judgment task in a sandbox round-trip that adds no determinism | Wasted latency + cost; brittle code that encodes a subjective rubric as if it were a formula; `print("the tone is friendly")` |

**Why the asymmetry matters.** Under-coding fails *silently* — the wrong number propagates
downstream and no exception fires. Over-coding fails *loudly and cheaply* — you notice the
useless sandbox call. So the default lean, when genuinely uncertain and a verifiable core
exists, is **toward code**. But "genuinely uncertain" is the operative phrase: most judgment
tasks are not close calls.

The **format corollary** (from [[agentsop-output-format-by-model]]): once you decide to emit code, emit
it as *code in a fenced block / single string field* — never nested inside JSON sub-structure.
Code-in-JSON measurably degrades the code itself (Aider: 61%→20% on GPT-4 Turbo). The
execution decision and the serialization decision are two separate gates; pass both.

---

## 3. SOP 工作流 (Decision workflow)

A three-step gate. Run it per *step*, not per *task* — one task can have computable steps and
judgment steps interleaved.

### Step 1 — Classify the step: deterministic-computable vs judgment

Ask: **"Is there a single correct answer that a program could verify?"**

- **Yes → computable.** Arithmetic, sorting, parsing, counting, set/regex ops, symbolic math, anything with a checkable ground truth. → Step 2.
- **No → judgment.** Quality ranking, tone, summarization, design choice, open synthesis. → reason in prose. Stop here.
- **Mixed → decompose.** "Summarize these sales and tell me the total" = a judgment summary step + a computable total step. Route each independently. The total goes to code; the summary stays prose.

A useful tiebreaker for the "trivial computable" gray zone: **if the model would be embarrassed
to get it wrong and you'd reach for a calculator yourself, emit code.** If you'd do it in your
head without a second thought, prose is fine.

### Step 2 — If computable, emit + run code

1. Emit the computation as a real program (Python is the PoT default; the interpreter is the oracle).
2. Keep the code **minimal and side-effect-free** for the computation — read inputs, compute, `print`/return the result. No network, no filesystem unless the task *is* I/O.
3. Serialize the code per [[agentsop-output-format-by-model]]: fenced block or single string field, **not** JSON-nested.

### Step 3 — Sandbox → run → feed result back into the LM

1. **Sandbox choice** (see §4 op #3, cross-link [[agentsop-output-format-by-model]] for the wire shape): DSPy `ProgramOfThought` uses a Python interpreter (Deno/PythonInterpreter sandbox in recent versions); OpenAI Code Interpreter runs in a managed container; Anthropic code-execution tool runs in a sandboxed VM; LangChain `PythonREPLTool` runs **in-process and is unsandboxed** — treat as untrusted-input-hostile.
2. **Run** the code in the sandbox; capture stdout / return value / traceback.
3. **Feed the result back into the LM** — this is the step under-coders forget. The code produces a *value*; the LM must consume it to narrate, format, or chain into the next step. PoT is "code computes, LM contextualizes," not "code replaces the LM."
4. **Error → retry** (cross-link [[agentsop-test-fix-loop]]): on traceback, feed the error back to the LM, regenerate the code, re-run. Bound the retries (DSPy `ProgramOfThought` defaults to `max_iters` ≈ 3). After the bound, fall back to prose reasoning or surface the failure — do not loop forever.

**Exit criterion:** the step produces either (a) a code-derived value the LM has consumed, or
(b) a prose judgment, with the gate decision recorded so a reviewer can audit *why* code was or
wasn't used.

---

## 4. 操作模型 (Operations: Trigger → Action → Output → Evidence)

Seven operations. Each row is a reusable move.

| # | Op | Trigger | Action | Output | Evidence |
|---|---|---|---|---|---|
| 1 | **Computable-vs-judgment gate** | Any step about to be reasoned | Apply §3 Step 1: single verifiable answer? | Route to code or prose | PoT premise: decouple compute from reasoning [arXiv 2211.12588] |
| 2 | **Decompose mixed steps** | Step has both a number and a narrative | Split into computable sub-step (code) + judgment sub-step (prose) | Two routed sub-steps | Mirrors mixed-content split in [[agentsop-output-format-by-model]] §5 Case B |
| 3 | **Sandbox choice** | Decided to emit code | Pick interpreter by trust + capability: DSPy PoT (Python sandbox), OpenAI Code Interpreter (managed container), Anthropic code-exec (VM), LangChain `PythonREPLTool` (**unsandboxed, in-process**) | Chosen runtime | DSPy modules [dspy.ai/learn/programming/modules/]; LangChain PythonREPLTool docs |
| 4 | **Result-back-into-LM** | Code produced a value | Inject stdout/return value into the next LM turn so the model narrates/uses it | LM-consumed result | PoT design: code computes, LM contextualizes [arXiv 2211.12588] |
| 5 | **Error retry (bounded)** | Code raised a traceback | Feed error to LM, regenerate, re-run; cap at `max_iters` (~3) then fall back | Fixed code or graceful fallback | DSPy `ProgramOfThought` `max_iters`; see [[agentsop-test-fix-loop]] |
| 6 | **Precision escalation** | Prose answer involves multi-step arithmetic | Re-route the arithmetic to code even if prose started it | Code-verified number | "LMs are unreliable calculators" — PAL [arXiv 2211.10435] |
| 7 | **Over-coding veto** | About to sandbox a judgment task | Stop: no deterministic core → reasoning, not code | Prose reasoning, no sandbox call | §5 Case B; avoids wasted round-trip |

In DSPy terms, op #1 is exactly the choice between `dspy.ChainOfThought` (prose reasoning) and
`dspy.ProgramOfThought` (emit+run) for a signature — the dspy skill lists the modules but this
overlay supplies the *when*.

---

## 5. 困境决策案例 (Dilemma cases)

### Case A — Arithmetic in prose hallucinates → PoT fixes it (under-coding)

**Trigger**: A finance-summary agent step: "Given these 14 line items, compute the total,
the 8.25% tax, and the grand total." The agent is a `dspy.ChainOfThought` module emitting prose.

**Constraints**:
- 14 multi-digit addends + a percentage + a sum-of-sums. Well outside reliable mental-math range.
- The number flows into an invoice — wrong is *expensive* and *silent*.
- A Python sandbox is available.

**Decision steps**:
1. **Gate (§3 Step 1):** "Is there a single verifiable answer?" Yes — the total is a fact, not a judgment. → computable.
2. **Recognize the under-coding failure mode.** Prose chain-of-thought will emit a plausible
   running sum that is frequently off by some digits, and *no exception will fire*. This is the
   silent failure the gate exists to prevent.
3. **Switch the module from `ChainOfThought` to `ProgramOfThought`.** The model now emits
   `subtotal = sum([...]); tax = round(subtotal * 0.0825, 2); total = subtotal + tax` and the
   interpreter computes it exactly.
4. **Feed the result back (op #4):** the LM receives `total = 4,217.93` and narrates the invoice
   line. Code computed; LM contextualized.
5. **Serialize per [[agentsop-output-format-by-model]]:** the generated code goes in a fenced block, not a
   JSON `program` field — code-in-JSON would degrade it.

**Outcome**: The arithmetic is now deterministic and auditable. PoT-style code execution is the
documented fix for exactly this class of error [arXiv 2211.12588, arXiv 2211.10435].

**Extractable operation**: **Multi-step arithmetic in prose is a smell. Re-route it to code (op #6).**

---

### Case B — Over-coding a judgment task wastes a sandbox round-trip (over-coding)

**Trigger**: A support-triage agent step: "Read this customer message and decide whether the
tone is hostile, neutral, or warm." An over-eager engineer wires it through `ProgramOfThought`
because "code is more reliable."

**Constraints**:
- "Tone" has no single verifiable answer — it is a judgment.
- The sandbox round-trip adds latency + cost.
- Forcing it into code produces something like `if "!!!" in msg: tone = "hostile"` — a brittle
  rule that *encodes a subjective rubric as if it were a formula*, and is worse than the model's
  native judgment.

**Decision steps**:
1. **Gate (§3 Step 1):** "Single verifiable answer a program could check?" No — tone is
   judgment. → reason in prose. Stop.
2. **Invoke the over-coding veto (op #7).** There is no deterministic core to delegate to an
   oracle. Code adds *no determinism* — it just relocates the same judgment into worse,
   hard-coded heuristics.
3. **Cost it out.** The sandbox call adds a full round-trip (and a code-gen + parse step) for
   zero precision gain. This is pure waste — the loud, cheap failure mode.
4. **Keep it as `ChainOfThought`** (or `Predict`). The LM *is* the right engine for judgment.
5. **Counter-check:** if a later spec adds "and count how many exclamation marks" — *that*
   sub-step is computable; decompose (op #2) and route the count to code, the tone to prose.

**Outcome**: No sandbox call. The judgment stays where judgment belongs. Over-coding is a real
and common anti-pattern: not everything benefits from an interpreter, only things with a
verifiable deterministic core.

**Extractable operation**: **No verifiable answer → no code. Veto the sandbox round-trip (op #7).**

---

### Case C — Mixed step: summary + total (decompose)

**Trigger**: "Summarize this quarter's sales narrative and give me the exact total revenue."

**Constraints**: One sentence contains both a judgment (summary) and a computation (total).

**Decision steps**:
1. **Gate → mixed.** Decompose (op #2).
2. Route the **total** to `ProgramOfThought`: code sums the figures, interpreter verifies.
3. Route the **summary** to `ChainOfThought`: prose synthesis, no oracle exists.
4. **Feed the code result back** into the prose step so the narrative cites the exact, verified total.

**Outcome**: Each sub-step uses its correct engine. This is the execution-decision analogue of
the mixed-content two-pass pattern in [[agentsop-output-format-by-model]] §5 Case B.

**Extractable operation**: **One task ≠ one strategy. Gate per step, decompose mixed steps.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **Code for everything ("code is always more reliable").** False. Code is more reliable only
   where a *deterministic, verifiable* answer exists. For judgment tasks, code just hard-codes a
   subjective rubric and adds a wasted round-trip (Case B). The interpreter is an oracle only for
   computable questions.
2. **Reasoning for arithmetic ("the model can just add it").** The headline failure. LMs are
   unreliable calculators; multi-step prose arithmetic hallucinates plausible wrong numbers,
   *silently* (Case A). Any non-trivial computation → code [arXiv 2211.12588].
3. **Emitting code but never feeding the result back.** PoT is "code computes, LM contextualizes."
   If the value never re-enters the LM turn, you have a dangling computation the agent can't use
   or narrate (op #4).
4. **Unbounded error-retry loops.** On a traceback, regenerate-and-rerun is correct — but cap it
   (`max_iters` ≈ 3) and fall back to prose or surface the failure. Infinite code-repair loops
   burn cost. See [[agentsop-test-fix-loop]].
5. **Nesting generated code inside JSON sub-structure.** The execution decision says *emit code*;
   [[agentsop-output-format-by-model]] says emit it as a fenced block / single string, never as nested
   JSON — code-in-JSON degrades the code (Aider 61%→20%). Pass both gates.
6. **Treating LangChain `PythonREPLTool` as a safe sandbox.** It runs **in-process, unsandboxed**.
   Fine for trusted self-authored code; hostile to untrusted input. Use a real sandbox
   (OpenAI Code Interpreter container, Anthropic code-exec VM, DSPy's interpreter) when inputs are untrusted.
7. **Over-decomposing trivial computation.** A 3-item count or single-digit add does not need a
   sandbox round-trip; the tax exceeds the benefit. The gate is for *non-trivial* computation.

### Boundaries (when this gate doesn't fire)

- **No sandbox available and determinism is soft.** Sometimes you must reason in prose because
  there is no interpreter; accept the precision risk and flag it.
- **The model is overwhelmingly capable for a tiny computation.** Frontier models reliably handle
  small arithmetic; the round-trip isn't worth it below a complexity threshold.
- **The task is one-shot exploration** with no downstream consumer of the precise value.
- **Latency-critical paths** where a sandbox round-trip violates a hard SLA and an approximate
  answer is acceptable — a deliberate, documented tradeoff, not a default.

---

## 7. 跨框架对照 (Ecosystem cross-reference)

How major frameworks expose the emit-code-vs-reason mechanism. This skill operates at the
**decision** layer; each framework supplies the **mechanism**.

### DSPy `ProgramOfThought` [dspy.ai/learn/programming/modules/]

The canonical declarative version. A signature compiled with `dspy.ProgramOfThought(Sig)`
makes the LM emit Python, runs it in an interpreter sandbox, and feeds the result back —
with bounded retry on error (`max_iters`). The sibling **dspy skill** lists `ChainOfThought`
vs `ProgramOfThought` as module choices but does **not** give the decision rubric; *this overlay
is that rubric*. Use `ProgramOfThought` exactly when §3 Step 1 returns "computable."

### OpenAI Code Interpreter / Assistants code tool

A managed container that the model can write Python into and execute, with files and state
persisted across turns. Heavier and stateful — good for data-analysis sessions (load CSV,
compute, plot). Same gate applies: route computable steps in, keep judgment in chat.

### Anthropic code-execution tool

A sandboxed VM exposed as a tool; the model emits code, it runs, results return to the
conversation. First-party, sandboxed — safe for untrusted inputs. The execution-decision gate
maps directly: offer the tool, but the *model/agent* should only invoke it for computable steps.

### LangChain `PythonREPLTool`

A tool wrapping a Python REPL. **Runs in-process and is unsandboxed** — powerful and dangerous.
Use only for trusted, self-authored computation; never expose it to untrusted input without an
external sandbox. The decision rubric is identical; the *safety* profile is worst-in-class.

### Cross-framework summary

```
Framework            | Mechanism                | Sandbox     | Result-back
---------------------|--------------------------|-------------|------------
DSPy PoT             | ProgramOfThought module  | Python intp | automatic (max_iters)
OpenAI Code Interp.  | Assistants code tool     | container   | persisted state
Anthropic code-exec  | code-execution tool      | VM (safe)   | into conversation
LangChain            | PythonREPLTool           | NONE (proc) | manual wiring
```

Every framework can be *mis-invoked* — pointed at a judgment task (over-code) or skipped for a
computation (under-code). This overlay is the gate that decides invocation, regardless of which
mechanism is underneath.

---

## Quick reference card

```
┌──────────────────────────────────────────────────────────────────────┐
│                  EMIT-CODE-VS-REASON DECISION CARD                   │
├──────────────────────────────────────────────────────────────────────┤
│ Single verifiable answer a program could check?                      │
│   YES → EMIT CODE → sandbox → run → feed result back into LM         │
│   NO  → REASON IN PROSE (no oracle exists for judgment)              │
│   MIXED → decompose; route each sub-step independently               │
├──────────────────────────────────────────────────────────────────────┤
│ Arithmetic / parse / sort / count / regex / symbolic → CODE          │
│ Tone / quality / summary / design / synthesis        → PROSE         │
│ "summary AND total"                                  → SPLIT         │
├──────────────────────────────────────────────────────────────────────┤
│ LMs are unreliable calculators but reliable coders.                  │
│ Under-coding fails SILENTLY (wrong plausible number).                │
│ Over-coding fails LOUDLY+CHEAPLY (wasted sandbox round-trip).        │
│ When genuinely uncertain AND a verifiable core exists → lean CODE.   │
├──────────────────────────────────────────────────────────────────────┤
│ NEVER:                                                               │
│  • code a judgment task (over-coding veto)                          │
│  • do multi-step arithmetic in prose (under-coding)                 │
│  • forget to feed the code result back into the LM                  │
│  • nest generated code in JSON (see [[agentsop-output-format-by-model]])     │
│  • loop code-repair unbounded (see [[agentsop-test-fix-loop]])               │
│  • trust LangChain PythonREPLTool on untrusted input (unsandboxed)  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 引用源 (Citations)

**Primary anchors:**
- Program of Thoughts (PoT) — Chen et al., arXiv 2211.12588 — decouple computation from reasoning; LM writes code, interpreter computes.
- PAL: Program-aided Language Models — Gao et al., arXiv 2211.10435 — LM as coder, runtime as deterministic solver.
- DSPy `ProgramOfThought` module — [dspy.ai/learn/programming/modules/] — emit+run+retry mechanism.

**Framework / API docs:**
- OpenAI Code Interpreter / Assistants code tool — [platform.openai.com/docs/assistants/tools/code-interpreter]
- Anthropic code-execution tool — [docs.anthropic.com/en/docs/agents-and-tools/tool-use/code-execution-tool]
- LangChain `PythonREPLTool` — [python.langchain.com/docs/integrations/tools/python] (unsandboxed; in-process).

**Companion / overlaid skills:**
- `dspy-sop-skill/SKILL.md` — ships `ProgramOfThought` but not this decision rubric (the gap this overlay fills).
- `d-output-format-by-model-skill/SKILL.md` — sibling: once you emit code, how to serialize it (PoT for math/parse; code never nested in JSON). Cross-linked as [[agentsop-output-format-by-model]].
- `test-fix-loop` — the execute → error → retry loop this skill defers to for bounded code repair. Cross-linked as [[agentsop-test-fix-loop]].
