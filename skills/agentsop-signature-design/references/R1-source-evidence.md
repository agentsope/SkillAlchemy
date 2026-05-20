# R1 — Source evidence for `signature-design`

Each claim `S1`–`S10` cited in `SKILL.md` is grounded below. Primary source is the local
`dspy-sop-skill/SKILL.md` (which itself cites upstream DSPy docs); secondary sources are the upstream URLs that
skill quotes. This overlay adds **no new library facts** — it only re-frames existing facts into a *decision*
rubric, so every factual claim traces to material already in the local `dspy-sop` skill.

Provenance of primary source: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`.

---

## S1 — Prompts past ~50 lines are a promotion symptom

> "Hand-written prompts grow past ~50 lines; brittleness on model swap; the team manually tunes few-shot
> examples; a metric exists but isn't being used to drive prompt design"

- Source: `dspy-sop-skill/SKILL.md` §1, "Symptoms" row of the activation table.
- Use in overlay: the **LENGTH** trigger (§1, §4.1). The ~50-line figure is taken directly from this row.

## S2 — Field names carry the optimizer's only pre-data intent signal

> "Signatures carry semantic load. `question -> answer` is not the same as `query -> response`. DSPy uses the
> *field names* as the only natural-language hint the optimizer has about intent before it sees data. Name them
> like you'd name function parameters in well-written code [dspy.ai/learn/programming/signatures/]."

- Source: `dspy-sop-skill/SKILL.md` §2, mental shift #2.
- Use in overlay: core mental model #1, OP-2/OP-3, the field-naming rules (§4.3), and anti-pattern #2. This is
  the load-bearing justification for the whole skill.

## S3 — Descriptions are added selectively; output desc constrains the value

> "Pin the task as a Signature. Start inline (`"question -> answer"`); upgrade to a class-based `dspy.Signature`
> with `InputField(desc=...)` / `OutputField(desc=...)` when types matter or fields need disambiguation."

and the cheatsheet example:

> ```python
> class BasicQA(dspy.Signature):
>     """Answer questions with short factoid answers."""
>     question: str = dspy.InputField()
>     answer: str = dspy.OutputField(desc="often between 1 and 5 words")
> ```

- Source: `dspy-sop-skill/SKILL.md` §3 Stage 1 step 1, and the Quick-reference appendix "Minimal end-to-end"
  block citing [dspy.ai/cheatsheet/].
- Use in overlay: Step 3 of the SOP, OP-4, and §4.4. Note the cheatsheet leaves `question` bare but adds a `desc`
  on `answer` — direct evidence for "describe only what the name underspecifies."

## S4 — Module choice is a separate decision (deferred to [[dspy]])

> "Pick the lowest-power Module that works. Default to `dspy.ChainOfThought`. Use `dspy.Predict` for trivial
> classification, `dspy.ReAct` only when tools are needed... [dspy.ai/learn/programming/modules/]"

- Source: `dspy-sop-skill/SKILL.md` §3 Stage 1 step 2, and §4.2 module-selection table.
- Use in overlay: SOP Step 4 / OP-6 explicitly **defer** this to the [[dspy]] skill. Cited to mark the scope
  boundary, not to duplicate the table.

## S5 — Compile rewrites instructions/demos but never the Signature shape

> "What does NOT change between LMs (so you can read across artifacts): The signature field names. The metric.
> The program's Python structure..."
> "Signature shape does NOT change — that's your code's job."

- Source: `dspy-sop-skill/SKILL.md` Quick-reference appendix, "Anatomy of a compiled `program.json`".
- Use in overlay: core mental model #2 (the Signature is the stable seam between your code and the optimizer's
  text), OP-5, and Case A step 2. This is why "don't freeze prose in the docstring" is correct.

## S6 — Model swap motivates Signatures + recompile

> "Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the artifact — recompile."
> "If you optimize a complex pipeline for GPT-4, it usually breaks on a smaller model like Llama-3-8b"

- Source: `dspy-sop-skill/SKILL.md` §5 Case B (incl. quote attributed to acldigital.com).
- Use in overlay: secondary activation signal in §1 ("about to model-swap") and the bonus box in §4.1.

## S7 — Don't promote/compile while the signature is still changing

> "The team is in *rapid exploration* mode where the task signature itself is changing daily — compile only after
> the signature stabilizes [dspy.ai/learn/optimization/overview/]."

and:

> "The task signature is still changing daily. Compile only after the I/O contract stabilizes; otherwise you're
> paying compile cost for prompts you'll throw away."

- Source: `dspy-sop-skill/SKILL.md` §1 "Do NOT activate" list, and §6 Boundaries.
- Use in overlay: the §1 "Do NOT activate" clause, anti-pattern #5, OP-1 `keep-prose` branch, and Case B step 1.

## S8 — Optimizer plateau usually means an ambiguous program/signature

> "Ignoring program structure when optimization stalls. If MIPROv2 light + medium both flatline, the bottleneck
> is almost always the **program graph** (wrong decomposition, wrong module choice) not the optimizer
> [dspy.ai/learn/optimization/overview/]."

- Source: `dspy-sop-skill/SKILL.md` §6 anti-pattern #7 (and the "When to iterate back" note in §3).
- Use in overlay: SOP "When to iterate back", OP-7. Re-framed from "program graph" to its sub-cause "ambiguous
  Signature / un-separated I/O", which is the part this skill owns.

## S9 — Typed OutputField pushes toward structure but does NOT guarantee grammar

> "Use Outlines for 'force valid JSON'; use DSPy for 'make the JSON-emitting prompt good.' DSPy's typed
> `OutputField` already pushes the LM toward structure but doesn't guarantee grammar conformance
> [dspy.ai/faqs/]."

- Source: `dspy-sop-skill/SKILL.md` §7 "vs Guidance / LMQL / Outlines".
- Use in overlay: OP-8, anti-pattern #7, §7 cross-framework "compose" notes, and the boundary on token-level
  format guarantees.

## S10 — No metric ⇒ DSPy is just verbose prompting (don't optimize one-shot prompts)

> "Compiling without a metric. Without a metric, DSPy collapses to verbose prompt templating... If you cannot
> write a metric, you cannot optimize, period [dspy.ai/learn/optimization/overview/]."

and the boundary:

> "One-shot tasks. 'Summarize this email once' → raw API call. The compile loop has no payoff."

- Source: `dspy-sop-skill/SKILL.md` §6 anti-pattern #1 and Boundaries.
- Use in overlay: Case B step 3 (refuse to optimize a one-shot, no-metric prompt) and the §1 one-shot exclusion.

---

## Overlap check vs the local `dspy` library skill

Frontmatter of `~/.claude/skills/dspy/SKILL.md` (read 2026-05-19) describes a broad library skill: "Build complex
AI systems with declarative programming, optimize prompts automatically, create modular RAG systems and agents."
Its "When to Use" section lists library capabilities (build systems, program declaratively, optimize, create
modular pipelines, build RAG/agents/classifiers). It is the **HOW-TO / library** layer.

This overlay deliberately holds a **disjoint** scope: it answers exactly one *decision* — "when does a prose
prompt deserve to become a typed Signature, and how do I shape its fields" — and defers every implementation
question (class syntax, module choice, evaluation, compile, save/deploy) to [[dspy]] and [[agentsop-dspy]]. No library
how-to is duplicated here.
