---
name: agentsop-structured-output-picker
version: 0.1.0
description: >-
  Decide where to enforce structured LM output (constrain at decode time with Outlines vs validate-and-retry with Instructor vs grammar with Guidance) and which failure stance to take (Assert/hard-fail vs Suggest/soft-retry). Use when an LM's output is parsed or typed by downstream code and you must pick one enforcement library plus its failure handling, when malformed output is burning tokens on retries, or when choosing between decode-time vs validation-time constraints for local vs API models.
domain: choosing and configuring a structured-output enforcement layer when LM output is consumed by code
overlay: true
enhances: [outlines, instructor, guidance]
source: |
  Local lib skills outlines / instructor / guidance (frontmatter + "When to Use");
  DSPy Assert/Suggest constraint primitives (dspy-sop-skill, arXiv 2312.13382);
  sibling Phase-D skill output-format-by-model (cross-link, not duplicate);
  provider docs for OpenAI structured outputs + Anthropic tool_use.
audience: |
  Coder-agents and pipeline authors wiring an LM whose output is parsed/typed by
  downstream code; anyone who has outlines / instructor / guidance installed and
  must pick one + decide failure handling.
status: tool-skill
---

# Structured-Output-Picker — 在解码处约束，还是在校验处约束？

> **One-liner**: Three local libraries (Outlines, Instructor, Guidance) plus
> provider-native structured outputs all "make the model emit valid structure",
> but they enforce at *different points* and *fail differently*. Pick by **how
> costly a malformed output is** and **whether you control the decoder**. Then
> pick the failure stance — **Assert** (hard-fail + retry) vs **Suggest** (soft
> nudge, degrade gracefully) — borrowed from DSPy's constraint primitives.

This is an **ENHANCE overlay**. The four enforcement mechanisms each have a
working local skill; what no single one provides is the cross-library *which-one
+ how-to-handle-failure* decision. That gap is hit every time an LM output is
consumed by code. For **what shape the content should take** (code vs JSON vs
prose), descend first to `[[agentsop-output-format-by-model]]` — this skill assumes the
shape is already chosen and asks only **how to enforce it**.

---

## 1. 何时激活 (When to activate)

Activate **after** you have decided the output *shape* (via
`[[agentsop-output-format-by-model]]`) and the answer was "a typed/validated object", and
**before** you write the parsing code.

| Trigger | Signal |
|---|---|
| LM output feeds a parser | `json.loads(resp)` / `Model.model_validate(...)` is in the next line of code |
| You picked a typed shape | format-by-model said "JSON / Pydantic / typed field" — now: who enforces it? |
| Repeated parse failures | `JSONDecodeError`, `ValidationError`, truncated/extra-prose responses in logs |
| Library is already installed | `outlines`, `instructor`, or `guidance` is in the env and you must choose between them |
| An enum / regex / range must hold | output must be one of N labels, a valid date, a bounded int |
| You must decide failure stance | "if the model returns garbage, do I crash, retry, or accept-and-flag?" |

**Anti-triggers** (skip this skill):
- The content is **code / multi-step reasoning / long prose** — go back to
  `[[agentsop-output-format-by-model]]`; enforcing a JSON grammar on code is the headline
  anti-pattern there (Aider 61%→20%). Enforcement strength is the wrong question
  when the *shape* is wrong.
- No code consumes the output yet (one-shot exploration).
- The shape is one token / one number — any parser works; no library needed.

---

## 2. 核心心智模型 (Core mental model)

### 2.1 The axis: where is the constraint applied?

```
   PROMPT ──────► DECODE ──────► RAW TEXT ──────► VALIDATE ──────► TYPED OBJECT
     │              │                                │
     │         constraint at DECODE             constraint at VALIDATE
     │         (grammar masks tokens)           (parse, check, retry on fail)
     │              │                                │
  ask nicely    Outlines / Guidance /          Instructor / DSPy Suggest /
  (weakest)     provider strict-mode           hand-rolled retry loop
                  ↑                                  ↑
            CANNOT emit invalid               CAN emit invalid, then
            structure — masked at             catches it and re-asks
            the logit level                   with the error injected
```

**The pick is governed by one question: how costly is a malformed output?**

- **A malformed output is cheap to recover from** (one extra API round-trip is
  fine; the model is strong; failures are rare) → **constrain at validate**
  (Instructor-style retry). Simpler, model writes more naturally, no decoder
  access needed.
- **A malformed output is expensive or impossible to recover from** (no retry
  budget, hard real-time, the output *must* be in a fixed enum/grammar, a single
  bad token corrupts a batch job) → **constrain at decode** (Outlines / Guidance
  grammar, or provider strict-mode). The model *cannot* emit invalid structure.

### 2.2 Two prerequisites that gate the choice

1. **Do you control the decoder?** Grammar/token-masking (Outlines, Guidance)
   requires logit access — i.e. **local/open weights** (Transformers, vLLM,
   llama.cpp) [[outlines]] [[guidance]]. Closed API models (GPT, Claude) expose
   only *their own* native structured-output / tool_use; you cannot bolt
   Outlines onto them. Instructor works *on top of* the API by parse-and-retry
   [[instructor]].
2. **Is the content code-shaped?** If yes, stop — see §1 anti-triggers and
   `[[agentsop-output-format-by-model]]`. Grammar-constraining code yields *valid JSON
   containing degraded code*: enforcement cannot buy back content quality.

### 2.3 Failure stance is orthogonal — Assert vs Suggest

Independent of *which* library, you choose what happens on a constraint
violation. DSPy names the two stances [dspy-sop-skill §Constraint primitives;
arxiv.org/pdf/2312.13382]:

| Stance | Behavior on violation | Use when |
|---|---|---|
| **Assert** (hard) | retry up to N; then **raise / halt** | Dev-time bug-catching; downstream cannot tolerate a bad value; correctness > availability |
| **Suggest** (soft) | retry with error injected; then **log + continue** with best effort | Production; partial result beats no result; availability > strict correctness |

> Decode-time grammar (Outlines/Guidance) is *itself* a hard guarantee on
> **shape** — but semantic checks (range, cross-field, business rules) still need
> an Assert/Suggest stance layered on top.

---

## 3. SOP 工作流 (Decision workflow)

Three ordered steps. Each presupposes `[[agentsop-output-format-by-model]]` already said
"typed/validated object".

### Step 1 — Decide enforcement strength (how costly is malformed?)

```
malformed output cost?
   │
   ├── cheap to recover (retry OK, strong model, rare failures)
   │        └──► VALIDATE-time enforcement   (weakest sufficient — prefer this)
   │
   ├── must never escape (enum/regex/grammar is a hard contract)
   │        └──► DECODE-time grammar          (only if you control the decoder)
   │
   └── no retry budget / hard real-time / batch where 1 bad token poisons many
            └──► DECODE-time grammar          (or provider strict-mode if API)
```

Heuristic: **start at the weakest layer that meets the cost constraint.** Validate
+ retry is cheaper to build, keeps the model's generation natural, and needs no
decoder access. Escalate to decode-time grammar only when retry is too costly or
the contract is absolute.

### Step 2 — Pick the library (gated by decoder access + provider)

| You have | Output goes to | Pick |
|---|---|---|
| Closed API model (GPT/Claude) + Pydantic schema | typed object, retries acceptable | **Instructor** — validate-time, Pydantic + auto-retry [[instructor]] |
| Closed API model + provider supports native | typed object, want zero extra deps | **provider native structured outputs / tool_use** (then Instructor or hand-parse on top) |
| Local/open weights + must guarantee JSON/regex/enum | hard contract, no retry budget | **Outlines** — decode-time grammar/regex/JSON-schema [[outlines]] |
| Local/open weights + interleaved gen + control flow | multi-step / fill-in-the-middle / mixed text+constrained | **Guidance** — decode-time + Pythonic control flow [[guidance]] |
| Any model + only semantic checks needed (shape already valid) | range / cross-field / business rules | retry loop with **Assert/Suggest** stance (DSPy or hand-rolled) |

### Step 3 — Choose the failure stance (Assert vs Suggest)

- Default **Suggest** in production (degrade gracefully; log the violation).
- Use **Assert** in dev/test and on values whose corruption is unacceptable
  downstream (IDs that index a DB, money amounts, irreversible actions).
- Decode-time grammar covers *shape* for free; still wrap *semantic* checks in a
  stance. Set a finite retry cap on either stance — an unbounded retry loop is an
  outage.

---

## 4. 操作模型 (Picker table — task → mechanism + stance)

| # | Task | Mechanism | Stance | Rationale / Evidence |
|---|---|---|---|---|
| 1 | Extract invoice fields from GPT-4o, retry on miss | **Instructor** (Pydantic + max_retries) | Suggest | API model → validate-time; auto-retry on `ValidationError` [[instructor]] |
| 2 | Classify into a fixed 4-label enum on a local Llama | **Outlines** regex/choice | Assert | enum is a hard contract; one masked decode guarantees it [[outlines]] |
| 3 | Local model must emit schema-valid JSON, no retry budget (batch) | **Outlines** JSON-schema | Suggest (log shape always holds) | decode-time guarantee; a bad token in a 100k batch is too costly to catch later [[outlines]] |
| 4 | Interleave reasoning text + a constrained `{action, arg}` block, local | **Guidance** (control flow + grammar) | Suggest | Guidance interleaves free text and constrained spans in one program [[guidance]] |
| 5 | Closed API, want typed output with zero new deps | **provider native** structured outputs / tool_use | Assert on parse | provider strict-mode guarantees schema validity (not content quality) |
| 6 | Output shape already valid; need `0 <= score <= 1` and `start < end` | **retry loop**, no grammar | Assert (dev) / Suggest (prod) | semantic, not shape — grammar can't express cross-field; needs a check + stance [dspy 2312.13382] |
| 7 | Local model, must match a date/email regex | **Outlines** regex | Assert | regex is a decode-time native; cheaper than parse-and-retry [[outlines]] |
| 8 | Streaming partial Pydantic objects from an API as they arrive | **Instructor** streaming | Suggest | Instructor streams partial validated objects [[instructor]] |

---

## 5. 困境决策案例 (Dilemma cases / worked examples)

### Case A — "Instructor keeps retrying and burning tokens; should I switch to Outlines?"

**Trigger**: An extraction service on GPT-4o uses Instructor with `max_retries=5`.
Latency p95 spiked; logs show 15% of calls retry ≥2× on the same nested schema.

**Constraints**:
- Closed API model — **no decoder access**, so Outlines is *not available* for
  GPT-4o [[outlines]] [[instructor]].
- The schema is deeply nested with several free-text fields.
- The cost being paid is *retries*, i.e. malformed output is currently expensive.

**Decision steps**:
1. Outlines is off the table for an API model (Step-1 prerequisite §2.2(1)). The
   real lever is reducing the validate-time failure rate.
2. Inspect *what* fails. If the model emits valid JSON but wrong *content*, no
   enforcement layer helps — that's a prompt/format problem; check whether a
   free-text field is being squeezed into JSON (`[[agentsop-output-format-by-model]]`
   mixed-content trap).
3. If the failure is *shape* (extra prose, truncation): switch the API call to
   **provider native structured outputs / tool_use** (strict-mode guarantees
   schema validity at the API), then keep Instructor only for the Pydantic typing
   layer. Retries collapse because shape is now guaranteed upstream.
4. Lower `max_retries` to 2 and flip the stance to **Suggest** with a logged
   fallback object, so a stubborn case degrades instead of inflating p95.

**Outcome**: Don't "switch to Outlines" (impossible here). Move shape-enforcement
to the provider's native layer, keep Instructor for typing, cap retries, Suggest.

---

### Case B — "Local model, 200k-row batch extraction; a few rows come back malformed"

**Trigger**: Nightly batch over a local vLLM-served model. ~0.3% of rows produce
JSON that fails to parse, poisoning the downstream load.

**Constraints**:
- **Local weights** → decoder access available (Outlines/Guidance both viable).
- Batch job, **no interactive retry budget** — re-running the whole batch is the
  only "retry", which is hugely expensive. Malformed output is *very* costly.
- The structure is a flat JSON schema; no interleaved free text.

**Decision steps**:
1. Step-1: malformed output is expensive and there is no per-row retry budget →
   **decode-time grammar**. This is exactly the case validate-time loses.
2. Step-2: local weights + pure JSON shape + no interleaving → **Outlines**
   JSON-schema. (Guidance would be the pick only if rows needed interleaved
   free-text + constrained spans, Case D-style.) [[outlines]] [[guidance]]
3. Shape is now *guaranteed* per row — the 0.3% parse failures go to zero by
   construction. Stance for shape becomes moot.
4. Layer a **Suggest** semantic check (e.g. `amount >= 0`) and write violators to
   a quarantine table rather than failing the batch — availability of the 99.7%
   beats halting on outliers.

**Outcome**: Decode-time Outlines grammar removes the shape failures the retry
model couldn't afford to catch; a Suggest semantic check quarantines the rest.

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **Grammar-constraining when a retry suffices.** Reaching for Outlines/Guidance
   on a strong API model with rare failures buys complexity (and may be
   *impossible* — no decoder access) when an Instructor retry would have been two
   lines. Start at the weakest sufficient layer (§3 Step 1).
2. **Assert where Suggest is enough → over-rejection.** Hard-failing the whole
   request because one optional field violated a soft preference throws away a
   usable answer. In production, default to Suggest; reserve Assert for values
   whose corruption is unacceptable [dspy 2312.13382].
3. **Enforcing structure on code/prose content.** The headline cross-skill
   anti-pattern: a JSON grammar produces *valid JSON containing degraded code*.
   Enforcement cannot recover content quality — fix the shape first via
   `[[agentsop-output-format-by-model]]`.
4. **Assuming provider strict-mode fixes content.** Native structured outputs
   guarantee schema *validity*, not field *correctness* — same lesson as Aider's
   strict-mode JSON test [[agentsop-output-format-by-model]].
5. **Unbounded retry loop.** Validate-time enforcement without a finite cap turns
   a flaky field into an availability outage. Always cap N.
6. **Stacking Outlines on a closed API model.** Token-masking needs logits;
   GPT/Claude expose none. Mixing the mental models wastes a debugging cycle
   (§2.2(1)).
7. **Using a grammar for cross-field/semantic rules.** Grammars constrain *token
   shape*, not relationships like `start < end` or "id exists in DB". Those need a
   validate-time check + stance, regardless of how shape was enforced.
8. **Picking the library before deciding strength + stance.** The library is the
   *third* decision, after "how costly is malformed" and "Assert or Suggest".

### Boundaries (when this skill doesn't apply)

- **Output is code / reasoning / prose** → `[[agentsop-output-format-by-model]]`, not here.
- **One token / one number / yes-no** → any parser; no enforcement library.
- **No code consumes the output** → one-shot exploration, defer.
- **Provider contract is fixed** (must emit a specific webhook JSON) → enforcement
  is mandatory by definition; the only remaining choice is the failure stance.
- **The fix is prompt-level** (model emits valid-but-wrong values) → no
  enforcement layer helps; this is a prompt/format problem.

---

## 7. 跨框架对照 (Ecosystem cross-reference)

Where each mechanism sits on the **decode vs validate** axis, and what it
guarantees. Cross-link `[[agentsop-output-format-by-model]]` for the prior *shape* decision.

| Mechanism | Constraint point | Needs decoder access? | Works on closed API? | Native failure model | Best for |
|---|---|---|---|---|---|
| **Outlines** [[outlines]] | Decode (token mask: regex / CFG / JSON-schema) | Yes (Transformers/vLLM/llama.cpp) | No | Cannot emit invalid shape — no failure to handle for *shape* | Local models; hard enum/regex/JSON guarantee; batch w/o retry budget |
| **Instructor** [[instructor]] | Validate (parse → Pydantic → auto-retry) | No | Yes | Catches `ValidationError`, re-asks with error; streaming partials | API models; Pydantic typing + graceful retry |
| **Guidance** [[guidance]] | Decode (grammar) + interleaved control flow | Yes | No | Constrained spans can't be invalid; free spans unconstrained | Local; interleaved text + constrained blocks; multi-step programs |
| **Provider native** (OpenAI structured outputs / Anthropic tool_use) | Decode (provider strict-mode) | N/A (provider-side) | Yes (that provider only) | Schema-valid guaranteed; content quality not | API models; zero extra deps; tool-call args |
| **DSPy Assert/Suggest** [dspy 2312.13382] | Validate (assertion + backtrack) | No | Yes | Assert raises after N; Suggest logs + continues | The *stance* layer on top of any of the above |

```
            DECODE-TIME                         VALIDATE-TIME
   (guarantee shape, need logits)        (catch + retry, model-agnostic)
   ┌─────────────┬──────────────┐        ┌──────────────┬─────────────┐
   │  Outlines   │   Guidance   │        │  Instructor  │ DSPy Assert/ │
   │ (regex/CFG/ │ (grammar +   │        │ (Pydantic +  │   Suggest    │
   │  JSON-sch.) │  control flow│        │  auto-retry) │ (stance)     │
   └─────────────┴──────────────┘        └──────────────┴─────────────┘
   ┌────────────────────────────┐
   │ Provider native strict-mode│  (decode-time, but provider-side; API only)
   └────────────────────────────┘
```

**How the two skills compose:**

```
[[agentsop-output-format-by-model]]  →  decides the SHAPE   (code? JSON? prose? typed?)
                                       │
                  shape == "typed/validated object"
                                       ▼
[[agentsop-structured-output-picker]] (this) →  decides ENFORCEMENT
                                       │
              Step1 strength → Step2 library → Step3 Assert/Suggest
```

`[[agentsop-output-format-by-model]]` already lists Outlines/Guidance under "grammar libs"
and provider tool_use under its §7 — it says *choose the format first, then let a
lower layer enforce it*. **This skill is that lower layer made into a decision.**

---

## Quick reference card

```
┌────────────────────────────────────────────────────────────────────┐
│                  STRUCTURED-OUTPUT ENFORCEMENT CARD                 │
├────────────────────────────────────────────────────────────────────┤
│ 0. Shape already "typed object"? If not → [[agentsop-output-format-by-model]]│
│ 1. How costly is a malformed output?                               │
│      cheap to recover  → VALIDATE-time (Instructor / retry)        │
│      must never escape → DECODE-time grammar (need decoder access) │
│ 2. Pick library:                                                   │
│      API model + Pydantic + retry ok   → Instructor                │
│      API model, zero deps              → provider native           │
│      local + hard enum/regex/JSON      → Outlines                  │
│      local + interleaved text+constr.  → Guidance                  │
│      only semantic/cross-field checks  → retry loop + stance       │
│ 3. Failure stance:                                                 │
│      prod default → Suggest (log + continue, capped retries)       │
│      dev / unrecoverable value → Assert (raise after N)            │
├────────────────────────────────────────────────────────────────────┤
│ NEVER:                                                             │
│  • Bolt Outlines/Guidance onto a closed API model (no logits)      │
│  • Grammar-constrain code/prose (valid JSON, degraded content)     │
│  • Assume strict-mode fixes content correctness                    │
│  • Run an uncapped retry loop                                      │
│  • Assert where Suggest suffices (over-rejection)                  │
└────────────────────────────────────────────────────────────────────┘
```

---

## 引用源 (Citations)

**Source lib skills (local):**
- `[[outlines]]` — decode-time grammar/regex/JSON-schema; local models
  (Transformers/vLLM/llama.cpp); `~/.claude/skills/outlines/SKILL.md`.
- `[[instructor]]` — validate-time Pydantic + auto-retry + streaming partials;
  OpenAI/Anthropic; `~/.claude/skills/instructor/SKILL.md`.
- `[[guidance]]` — decode-time grammar + Pythonic multi-step control flow; local;
  `~/.claude/skills/guidance/SKILL.md`.

**Constraint-stance source:**
- DSPy `Assert` vs `Suggest` — `dspy-sop-skill/SKILL.md` §Constraint primitives;
  DSPy Assertions paper [arxiv.org/pdf/2312.13382];
  [dspy.ai/learn/programming/7-assertions/].

**Sibling Phase-D skill (cross-link, not duplicated):**
- `[[agentsop-output-format-by-model]]` — `d-output-format-by-model-skill/SKILL.md`. Decides
  the *shape*; this skill decides *enforcement*. Anchors the "strict-mode ≠ content
  quality" and "don't grammar-constrain code" claims (Aider code-in-JSON 61%→20%).

**Provider docs (named, re-verify before pasting code, May 2026):**
- OpenAI structured outputs: [platform.openai.com/docs/guides/structured-outputs].
- Anthropic tool_use: [docs.anthropic.com/en/docs/agents-and-tools/tool-use].

All source SKILLs read on 2026-05-20. This overlay introduces **no API absent
from the sources**; see `references/R1-source-evidence.md`.
