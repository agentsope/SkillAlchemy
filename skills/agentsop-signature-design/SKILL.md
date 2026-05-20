---
name: agentsop-signature-design
version: 0.1.0
description: >-
  Decision rubric for promoting a prose prompt into a typed DSPy Signature. This is an
  ENHANCE overlay on top of the [[dspy]] library skill: it does NOT teach DSPy syntax — it
  answers the coder-agent decision "when do I stop hand-writing a prompt string and declare
  it as a `dspy.Signature`, and how do I name/describe its fields so the optimizer and the
  calling code both get a clean contract." Activate when: a prompt string grows past ~50
  lines; the LM output is consumed by code (parsed, branched on, stored) rather than read by
  a human; the same prompt is reused across >1 call site; or a teammate asks "should this be
  a Signature?". Do NOT activate for one-shot throwaway prompts, or for HOW-TO questions
  about DSPy modules /optimizers/compile — defer those to the [[dspy]] skill and the
  [[agentsop-dspy]] workflow skill. Search keywords: typed prompt, structured prompt, DSPy
  Signature, prompt as a function, prompt contract, when to formalize a prompt.
---

# Signature-Design — Promote Prose → Typed Contract

> *"DSPy uses the field names as the only natural-language hint the optimizer has about intent before it sees
> data. Name them like you'd name function parameters in well-written code."*
> — derived from [dspy.ai/learn/programming/signatures/], see `references/R1-source-evidence.md`

This skill is the **decision layer**, not the library layer. It tells you *when* a prose prompt has become
"load-bearing" enough to deserve a typed Signature, and *how* to shape its fields. For the actual API
(`dspy.Signature`, `InputField`, `OutputField`, `Predict`, `ChainOfThought`, compile, save) defer to the
**[[dspy]]** skill; for the full program→evaluate→optimize SOP defer to **[[agentsop-dspy]]**.

---

## 1. 何时激活 (When to activate)

Activate this overlay the moment a hand-written prompt crosses **any one** of three load-bearing thresholds.

| Trigger | Concrete signal | Why it matters |
|---|---|---|
| **Length** | A single prompt string grows past **~50 lines** of f-string / template | Long prose prompts hide their I/O contract inside narration; the [[agentsop-dspy]] skill names this exact symptom: "hand-written prompts grow past ~50 lines; brittleness on model swap" (`R1`, claim S1) |
| **Code-consumed output** | The LM response is **parsed, branched on, or stored** by downstream code (not just shown to a human) | If code reads the output, the output has a *type*. An untyped prompt forces brittle regex/JSON-scraping at every call site |
| **Reuse** | The same prompt (or a copy-pasted variant) is called from **>1 call site** or in a loop | Reuse means the contract is now an API surface. Drift between copies is a guaranteed bug source |

Secondary signals (each strengthens, none alone is sufficient):
- The prompt is about to be **model-swapped** (GPT → Llama) and you fear it will break — Signatures + recompile is the documented fix (`R1`, claim S6; see [[agentsop-dspy]] Case B).
- A **metric already exists** for this task — you are one step from optimization, and optimizers require a Signature.
- The prompt mixes **task instruction + few-shot demos + format spec** in one blob — Signatures separate these cleanly.

**Do NOT activate** when:
- The prompt is **one-shot** ("summarize this one email") — keep it as a raw string; the contract has no second reader.
- The task **signature is still changing daily** — promoting now just churns boilerplate. Wait for the I/O to stabilize (`R1`, claim S7).
- The question is **HOW to write the Signature class / pick a module / compile** — that is the **[[dspy]]** skill's job, not this rubric's.
- Output **must be free-form human prose** with no downstream parsing and no reuse — a Signature buys nothing.

---

## 2. 核心心智模型 (Core mental model)

**A Signature is a typed function contract for a single LM call.** Promote a prose prompt to a Signature exactly
when the prompt becomes *load-bearing* — when something other than a one-time human reader depends on its shape.

Think of the progression as the same lifecycle a script goes through when it earns a function:

```
prose prompt string          →   typed Signature
─────────────────────────        ─────────────────────────
"You are an expert... given     class Classify(dspy.Signature):
 the ticket below, output           """Route a support ticket."""
 the category and a one-line        ticket: str  = dspy.InputField()
 reason. Categories are..."         category: Literal[...] = dspy.OutputField()
                                     reason: str  = dspy.OutputField(desc="<=15 words")
inline narration of I/O          explicit, named, typed I/O
human reads / eyeballs           code parses category, logs reason
each caller copies the blob      one contract, N callers import it
optimizer sees nothing           optimizer rewrites instructions, keeps field names
```

Three load-bearing ideas (all sourced; see `references/R1-source-evidence.md`):

1. **Field names are the contract.** Before the optimizer ever sees data, the only intent signal it has is the
   field names. `question -> answer` ≠ `query -> response`. Name fields like function parameters in clean code
   (`R1`, claim S2). This is *the* reason promotion is worth it: you convert narration into a machine-readable
   intent signal.

2. **The Signature shape is YOUR code; the prompt text is the optimizer's.** When you compile, the optimizer
   rewrites *instructions* and *demos* — but it never changes field names, field count, or types (`R1`, claim
   S5). So the Signature is the stable seam between "what I own" and "what the compiler owns." A prose prompt has
   no such seam — everything is tangled.

3. **Promote on load-bearing, not on aspiration.** A Signature you optimize a 5-line one-shot prompt into is pure
   overhead. The payoff appears only when the prompt is long, code-consumed, or reused. Below that line, raw
   prompting wins (`R1`, claims S7, S1).

The PyTorch analogy from [[agentsop-dspy]] holds: a Signature ≈ a `forward()` shape contract. You don't write a
`nn.Module` for a one-line lambda; you write one when the shape is reused and trained.

---

## 3. SOP 工作流 (The promotion SOP)

A four-step gate. Run it top-to-bottom; each step has an exit criterion. Implementation of any step lives in the
**[[dspy]]** skill — this SOP only tells you *what decision* to make at each step.

### Step 0 — Gate: is this prompt load-bearing?
Run the §1 trigger table. If **zero** triggers fire → **stop, keep the prose prompt.** Promotion is overhead.
**Exit:** at least one of {>50 lines, code-consumed output, reused} is true.

### Step 1 — Identify inputs and outputs
Read the prose prompt and extract every *variable* thing the LM is given (inputs) and every *distinct* thing it
must return (outputs). A common smell: the prose says "output the category **and** a confidence **and** a reason"
— that is **three** output fields, not one paragraph to regex later.
**Exit:** you can list inputs and outputs as a flat set of named slots, each with a Python type.

### Step 2 — Name fields semantically
Rename each slot to read like a function parameter. `text → ticket`, `out → category`, `resp → reason`.
The name carries the optimizer's only pre-data intent signal (`R1`, claim S2). Avoid generic `input`/`output`.
**Exit:** every field name would be self-explanatory to a teammate reading only the field list.

### Step 3 — Add descriptions *only where the name underspecifies*
Add `InputField(desc=...)` / `OutputField(desc=...)` **only** when the field name alone is ambiguous or the value
needs a constraint the name can't carry (format, length, units, allowed values). The DSPy cheatsheet's own example
adds a desc on output (`answer`, `desc="often between 1 and 5 words"`) but leaves the input bare (`R1`, claim S3).
Over-describing every field bloats the prompt and fights the optimizer. **Exit:** descriptions exist for exactly
the fields that need disambiguation, and no others.

### Step 4 — Hand off module choice to [[dspy]]
Picking `Predict` vs `ChainOfThought` vs `ReAct`, then evaluating and compiling, is **out of scope** for this
decision skill — that is the [[dspy]] skill (modules) and [[agentsop-dspy]] (Stage 1–3 workflow). Your deliverable from
this skill is a *well-shaped Signature*, handed to those skills. **Exit:** Signature is named, typed, minimally
described, and committed; you have switched contexts to [[dspy]].

### When to iterate back
If, after compiling (in [[dspy]]), the optimizer plateaus, the most common root cause is an **ambiguous
Signature** — not a bad optimizer (`R1`, claim S8). Loop back to Step 1: are inputs/outputs really separated? Are
field names carrying intent?

---

## 4. 操作模型 (Operations — Trigger / Action / Output / Evidence)

Eight operations. The first two are the gate; the rest are the shaping rubric. Full Trigger/Action/Output/Evidence
records are in `intermediate/operation_candidates.json`.

### 4.1 Promote-trigger checklist (the gate)

Promote prose → Signature when you can check **≥1** box. Each box maps to a §1 trigger:

```
[ ] LENGTH      prompt string > ~50 lines
[ ] CONSUMED    LM output is parsed / branched on / stored by code (not just human-read)
[ ] REUSED      same prompt called from > 1 site, or inside a loop
[ ] (bonus) about to model-swap, OR a metric already exists, OR blob mixes instruction+demos+format
```
Zero boxes → **do not promote.** One box → promote. (Source: §1 triggers; `R1` S1, S6, S7.)

### 4.2 Operation table

| # | Trigger | Action | Output | Evidence |
|---|---|---|---|---|
| OP-1 | Prompt crosses a §1 threshold | Run the §4.1 checklist | `promote` / `keep-prose` decision | `R1` S1, S7 |
| OP-2 | Decision = `promote` | Extract variable inputs + distinct outputs into named slots | Flat list of typed slots | `R1` S2 |
| OP-3 | Slots listed | Rename each to a semantic, parameter-style name | Field names that read as intent | `R1` S2 |
| OP-4 | Names set | Add `desc=` **only** to underspecified fields | Minimal descriptions | `R1` S3 |
| OP-5 | Output has fixed value set | Type the output field (`Literal[...]` / `bool` / `int`) instead of `str` | Typed `OutputField` | `R1` S3, S5 |
| OP-6 | Reasoning would help quality | Note "needs CoT" but **defer module choice to [[dspy]]** | Hand-off note | `R1` S4 (module table is dspy's) |
| OP-7 | Optimizer plateaus later | Loop back: re-audit Signature for ambiguity before blaming optimizer | Revised Signature | `R1` S8 |
| OP-8 | Output consumed by code AND must be machine-valid | Pair the Signature with a grammar/JSON enforcer (Outlines) — Signature shapes intent, enforcer guarantees syntax | Signature + enforcement layer | `R1` S9 |

### 4.3 Field-naming rules (the heart of this skill)

1. **Name like a function parameter, not like a prompt.** `customer_email`, not `the text the user pasted`.
2. **Inputs are nouns the LM receives; outputs are nouns the LM produces.** Don't smuggle an output into an input name.
3. **One concept per field.** "category_and_reason" is two fields. Split it (OP-2).
4. **Prefer the most specific type the value can hold.** `Literal["bug","billing","other"]` over `str` when the
   set is closed (OP-5) — the type *is* documentation and a parse guard.
5. **Reserve `desc=` for what the name can't say**: format, length, units, allowed values, edge-case handling.

### 4.4 When InputField vs OutputField descriptions matter

| Side | Add a `desc` when… | Skip the `desc` when… |
|---|---|---|
| **InputField** | The input has a non-obvious format/source ("raw OCR text, may contain noise"), or the LM tends to misread which input is which | The field name fully explains it (`question`, `ticket`) — the cheatsheet leaves `question` bare (`R1` S3) |
| **OutputField** | You need to constrain the value: length ("≤15 words"), format ("ISO-8601 date"), or allowed set | The output type already constrains it (e.g. `Literal[...]` or `bool` carries the spec) |

Rule of thumb: **input descs prevent confusion; output descs prevent malformed values.** Default to fewer descs;
add one only when you can name the specific failure it prevents.

---

## 5. 困境决策案例 (Dilemma cases)

### Case A — "The 80-line mega-prompt: promote whole, or split first?"

**困境:** A support-triage prompt is 80 lines: persona + 4 categories with examples + output-format spec +
edge-case rules. The output ("category, confidence, escalate?") is parsed by routing code. Promote it verbatim
into one Signature, or restructure first?

**约束:**
- Output is **code-consumed** (routing branches on `category` and `escalate`) → §1 CONSUMED trigger fires.
- The 80 lines mix instruction + demos + format → the optimizer should own most of that text, not you.
- Three distinct return values are currently scraped from one free-text blob.

**决策步骤:**
1. **Promote — the gate is satisfied** (CONSUMED + LENGTH). This is exactly the load-bearing case (`R1` S1).
2. **Do NOT copy the 80 lines into one giant docstring.** Inputs = `ticket: str`. Outputs = `category:
   Literal[...]`, `confidence: float`, `escalate: bool` (OP-2, OP-5). The four category descriptions and examples
   are **demos/instructions the optimizer will own** — drop them from your code (mental model #2, `R1` S5).
3. **Type the outputs** so the router stops regex-scraping (OP-5). `escalate: bool` replaces parsing the word
   "yes" out of prose.
4. Add a `desc` only on `confidence` ("0–1, calibrated") since the name underspecifies the range (OP-4, §4.4).
5. **Hand to [[dspy]]** to pick `ChainOfThought` (reasoning helps category choice) and to compile against the
   existing routing-accuracy metric.

**结果:** An 80-line blob collapses to a 5-field typed contract; the router drops all string-scraping; the prose
that *was* the prompt becomes optimizer-owned instructions/demos.

**可提取的操作:** **When promoting a mega-prompt, keep only the I/O shape in code; let the instruction/demo prose
become the optimizer's territory. Split fused outputs; type closed-set and boolean outputs.**

---

### Case B — "One-shot prompt someone wants to 'make robust' — promote or refuse?"

**困境:** A teammate has a 6-line prompt that runs **once** in a migration script ("classify these 200 rows once,
then we throw the script away") and asks you to "make it a proper Signature so it's robust."

**约束:**
- Runs once, script is disposable → §1 LENGTH, REUSED both **fail**.
- Output *is* consumed by code (it writes a column) → CONSUMED **fires**.
- No metric, no model-swap planned, signature won't be reused.

**决策步骤:**
1. CONSUMED fires, so the gate technically passes — but weigh it. The output is consumed, yet the contract has
   **no second reader over time** (disposable script). This is the boundary the [[agentsop-dspy]] skill flags: compile
   only after the I/O contract stabilizes and will be reused (`R1` S7).
2. **Compromise:** declare a *minimal* Signature for the type-safety of the one column (OP-5 — a `Literal`
   output stops bad values landing in the DB), but **do not optimize/compile it.** A typed `dspy.Predict(Sig)`
   with no compile is cheap and gives the parse guard without the compile-loop overhead.
3. **Refuse the "robust"/optimize ask.** Optimizing a one-shot, no-metric prompt is the documented anti-pattern —
   DSPy without a metric is just verbose prompting (`R1` S10). Say so explicitly.

**结果:** A 10-line typed Signature with no compile: enough to make the written column type-safe, not enough to
waste a compile budget on a script that's about to be deleted.

**可提取的操作:** **CONSUMED alone justifies a *typed* Signature (parse safety) but NOT optimization. Separate
"promote to typed contract" from "compile/optimize" — they have different gates.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **Over-signaturizing one-off prompts.** A Signature (let alone a compiled one) for a 5-line throwaway prompt is
   pure boilerplate. If no §1 trigger fires, the prose prompt is the *correct* artifact (`R1` S7).
2. **Under-specifying field semantics.** `class Sig: input: str; output: str` defeats the entire point — the
   optimizer gets zero intent signal and code still can't trust the output shape. Field names ARE the contract
   (`R1` S2). Generic names are the most common silent failure.
3. **One blob output that should be N fields.** Returning a single `result: str` and regex-scraping three values
   out of it re-creates the fragility you were escaping. Split into typed fields (OP-2, OP-5).
4. **Copying the whole prose prompt into the docstring.** The instruction/demo text is the *optimizer's* to own;
   freezing it in your Signature both bloats your code and fights the compiler (mental model #2, `R1` S5).
5. **Promoting before the I/O contract is stable.** If you're still adding/removing outputs daily, you're churning
   boilerplate. Stabilize first (`R1` S7).
6. **Adding `desc=` to every field reflexively.** Descriptions you can't tie to a specific prevented failure are
   noise that bloats the prompt; the cheatsheet leaves obvious inputs bare (`R1` S3).
7. **Confusing "promote to Signature" with "guarantee valid JSON".** A typed `OutputField` *pushes* toward
   structure but does not *enforce* grammar — pair with Outlines/Guidance when machine-validity is mandatory
   (`R1` S9, OP-8).

### Boundaries (when this skill is NOT the right layer)

- **HOW to write the class / pick a module / compile** → [[dspy]] (library) and [[agentsop-dspy]] (workflow). This
  skill stops at "the Signature is shaped."
- **Free-form human-read prose with no parsing and no reuse** → keep raw prompting; a Signature buys nothing.
- **Token-level format guarantees** (strict JSON/regex/grammar) → that's the generation layer (Outlines, Guidance,
  LMQL), orthogonal to Signature design (`R1` S9).
- **Non-DSPy stacks** → the *decision* ("is this prompt load-bearing enough to deserve a typed contract?")
  transfers, but the implementation does not (see §7 for the cross-framework mapping).

---

## 7. 跨框架对照 (Cross-framework comparison)

The **decision** ("promote prose → typed contract when the prompt becomes load-bearing") is framework-agnostic.
Only the *artifact* differs. This overlay's rubric (§4) tells you when to reach for any column below.

| Approach | What the "contract" is | Optimizable? | Enforces output syntax? | Best when |
|---|---|---|---|---|
| **Raw prompt string** | None — narration only | No | No | One-shot, human-read, unstable, no reuse (§6 boundary) |
| **DSPy Signature** | Named + typed I/O fields; field names carry intent for the optimizer (`R1` S2) | **Yes** — instructions/demos rewritten on compile, field shape preserved (`R1` S5) | Pushes toward structure, no hard guarantee (`R1` S9) | Load-bearing prompt + a metric exists / model-swap planned. **Implementation: [[dspy]]** |
| **Pydantic output model** | A typed schema the response is *validated against* after generation | No (it's validation, not prompt-tuning) | Yes — validation raises on mismatch | You need a hard post-hoc type check but are not optimizing the prompt |
| **instructor** (Pydantic + LLM) | Pydantic model used both as prompt scaffold and parse target; auto-retries on validation failure | No prompt-optimization loop; retries only | Yes — re-asks the LM until the schema validates | You want structured-output-with-retries on a raw provider SDK, no compile pipeline |

How they compose (not mutually exclusive):
- **DSPy Signature + Outlines/Guidance**: Signature shapes intent and gets optimized; Outlines guarantees the
  output is valid JSON/grammar at the token level (`R1` S9, OP-8).
- **DSPy Signature ≈ instructor's Pydantic model** at the "declare the I/O shape" step — but DSPy adds the
  *optimizer* that instructor lacks, and instructor adds *validation-retry* that a bare Signature lacks. Pick
  DSPy when you have a metric and want to compile; pick instructor when you just need structured output + retries
  on a raw SDK.
- **Pydantic** is the validation primitive the others build on; reach for it directly when you only need a hard
  type gate with no prompt machinery.

**Bottom line:** this skill decides *whether* the prompt deserves a typed contract. If yes **and** you're in DSPy
with a metric → the contract is a Signature, and you continue in **[[dspy]]** / **[[agentsop-dspy]]**. If you only need
validation → Pydantic/instructor. If the prompt isn't load-bearing → no contract at all.

---

## Cross-skill links

- **[[dspy]]** — the library skill: Signature/Module/optimizer API, how to actually write and compile. This
  overlay defers ALL implementation to it.
- **[[agentsop-dspy]]** — the full DSPy operating workflow (program → evaluate → optimize, 3-stage gate, optimizer
  selection, cost guardrails). This overlay is the narrow "should this prose become a Signature" slice of its
  Stage 1.

## Source basis

All claims tagged `S1`–`S10` are sourced verbatim in `references/R1-source-evidence.md`, drawn from the local
`dspy-sop-skill/SKILL.md` Signatures material and the upstream DSPy docs it cites
([dspy.ai/learn/programming/signatures/], [dspy.ai/cheatsheet/], [arxiv.org/abs/2310.03714]).
