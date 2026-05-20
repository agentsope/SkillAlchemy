---
name: agentsop-output-format-by-model
version: 0.1.0
description: >-
  Pick an LM output format per (task x consumer x model) rather than by reflex: different formats carry different cognitive load (e.g. code-in-JSON makes the same model write worse code than plain-text+diff, while asking for prose when you need a typed object fails the other way). Use when designing or debugging an LM's output schema, choosing between plain text / diff / JSON / tool-call / grammar-constrained output, or when a model's quality drops after wrapping its output in a structured format.
domain: LM output schema design for coder-agents and any LM workflow whose output is consumed by code
source: |
  Aider's "code-in-JSON" benchmark + unified-diff post + edit-format docs;
  DSPy adaptor system; "Let Me Speak Freely?" (arXiv 2408.02442);
  StructEval (arXiv 2505.20139); Anthropic text-editor tool / writing-tools-for-agents;
  OpenAI structured outputs + tool_use docs; Outlines/Guidance grammar libs.
audience: |
  Anyone designing an LM output format — coder-agent authors, RAG pipeline builders,
  tool-use harness designers, prompt engineers shipping typed objects.
status: tool-skill
---

# Output-Format-by-Model — 让格式服务于任务，而不是反过来

> **One-liner**: Different output formats carry different cognitive load for the model. Code-in-JSON is the canonical proof: the same model writes worse code when wrapped in a JSON tool-call than when emitted as plain text + diff. The reverse failure (asking for prose when you need a typed object) is just as common. Pick format per (task × consumer), not by reflex.

---

## 1. 何时激活 (When to activate)

Activate this skill **before** committing to an output schema in any of these situations:

| Trigger | Signal |
|---|---|
| Designing a coder-agent | "should the model return a `apply_patch` tool call or plain-text diff?" |
| Adding a tool to an existing agent | "tool input has a `code` / `query` / `sql` / `regex` field — should I nest it in JSON or leave it as a string?" |
| Building extraction / classification | "should I use `dspy.Predict` typed fields, Pydantic + `response_format=json_schema`, or just markdown?" |
| Wiring an evaluator | "the metric needs a number — but the model also has to *reason* to produce it" |
| Migrating a working prompt to "structured outputs" | someone said "let's make it safer with JSON schema" |
| Tool-call harness adds latency / errors | repeated `json.JSONDecodeError`, escaping bugs, truncated outputs |

**Anti-triggers** (skip this skill):
- The format is fixed by an external API (e.g. you must return OpenAI function-call JSON — no choice).
- One-shot exploratory prompting where no consumer parses the output yet.
- The task is *itself* about JSON (e.g. "fix this malformed JSON") — see §6.

---

## 2. 核心心智模型 (Core mental model)

### 2.1 Three-layer claim

```
            ┌──────────────────────────────────────────────────┐
            │ FORMAT FOLLOWS FUNCTION                          │
            │                                                  │
            │  Some formats add cognitive load to the model    │
            │  and measurably degrade quality on the           │
            │  *content* the format is supposed to wrap.       │
            └──────────────────────────────────────────────────┘
                         ▲                          ▲
                         │                          │
         What's being consumed?       Who consumes it?
         (code? prose? entities?      (human reader? parser?
          number? action selection?)   downstream LM? compiler?)
                         │                          │
                         └──────────┬───────────────┘
                                    ▼
                       FORMAT SELECTION
                  (text+diff | markdown | JSON | tool_use
                   | grammar-constrained | typed field)
```

Aider's `code-in-json` benchmark is the load-bearing empirical anchor:
- GPT-4 Turbo refactor benchmark with **unified diff**: **61%** pass.
- Same model with **JSON-wrapped code**: **20%** pass.
- That is a **3×** swing from format alone, not from model choice or prompt rewording. [aider.chat/2023/12/21/unified-diffs.html, aider.chat/2024/08/14/code-in-json.html]
- The pattern holds across every major model tested in 2024 (Claude Sonnet, DeepSeek Coder, GPT-4o). Even with OpenAI strict-mode JSON validity enforced, **the code *inside* the JSON degraded** — more `SyntaxError` / `IndentationError`. Sonnet kept syntax clean but still scored lower overall. [aider.chat/2024/08/14/code-in-json.html]

Academic generalization, same year:
- "Let Me Speak Freely?" (arXiv 2408.02442) — **format-restricted reasoning drops 10–15%** on math and complex analysis vs free-form-then-convert. [arxiv.org/abs/2408.02442]
- StructEval (arXiv 2505.20139) — even o1-mini only scores 75.58 average on structural-output generation. [arxiv.org/html/2505.20139v1]

### 2.2 The two reflexes to unlearn

| Reflex | When it's wrong |
|---|---|
| "Structured output is always safer." | False for code, multi-step reasoning, free-form prose. Strictness ≠ quality of contents. |
| "Markdown is only for humans." | False — markdown is *also* the highest-fidelity wire format for many LM-to-LM hand-offs (Aider uses it; DSPy's default chat adaptor uses field-marked markdown over JSON for many signatures). |

### 2.3 Mental model: format as a *tax* on the generation surface

Every formatting requirement consumes some of the model's attention budget. The tax is:
- **Low** for formats the model has seen millions of times in pretraining (markdown, unified diff, Python).
- **Medium** for JSON containing simple scalar fields (entity extraction, dates, booleans).
- **High** for JSON containing code, multi-line strings with escapes, or deeply nested reasoning. Each `\n` becomes `\\n`; each quote becomes `\"`; the model has to track this *while also* solving the actual problem.

⇒ Heuristic: **the more semantically dense the content, the cheaper the format must be.**

---

## 3. SOP 工作流 (Decision workflow)

Three questions, in order:

### Step 1 — What's being consumed?

| Content type | Default format | Why |
|---|---|---|
| Source code edits | **plain text + diff format** (SEARCH/REPLACE, unified diff, or `str_replace` tool with code as a *single string field*) | Aider 20%→61% on GPT-4 Turbo; same direction across all models. [aider.chat/2024/08/14/code-in-json.html] |
| Source code (full file rewrite) | **plain text or markdown fenced block** | Same reason. JSON-wrap adds escaping tax. |
| Structured data extraction (entities, dates, IDs, classifications) | **JSON / Pydantic / typed `OutputField`** | Schema *helps* here — fields are the task. |
| Action selection (which tool to call) | **JSON tool_use** | Tool name + scalar args. The decision is structured by definition. |
| Action *body* (SQL, regex, code, file contents) | **single string field inside tool_use** — do not sub-structure | Same code-in-JSON penalty applies to any code-shaped payload. |
| Reasoning / intermediate steps | **markdown or Python-style scratchpad** | CoT in JSON measurably degrades; see "Let Me Speak Freely?" [arxiv.org/abs/2408.02442] |
| Numeric answer with reasoning | **markdown reasoning + final answer in fenced block or final-line convention** | Don't force the reasoning into a JSON `reasoning` field — it shortens and stiffens. |
| Free-form prose (summary, explanation, customer reply) | **markdown** | Native to instruction-tuned models. |
| Mixed (e.g., extract entities AND rewrite the document) | **split into two calls or two passes** — see §5 Case B | One format can't serve two contents well. |

### Step 2 — Who consumes the output?

| Consumer | Constraint | Implication |
|---|---|---|
| Human in a chat UI | Render-friendly | Markdown wins. JSON is hostile. |
| `json.loads` / Pydantic parser | Must be valid | JSON with schema, or a known-safe envelope (`<result>...</result>`) with markdown body. |
| Downstream LM (LM-to-LM pipeline) | Reads what was written | Markdown is *more* robust than JSON when content includes code/math; the next LM ingests it natively. |
| Compiler / interpreter (PoT, code-exec sandbox) | Must be a valid program | Output **as code** in a fenced block, not as a JSON `program` field. |
| Tool dispatcher (function calling) | Needs tool name + args | JSON tool_use with **scalar args**; multi-line bodies go in a single string field. |
| Diff applier (Aider, git apply, str_replace) | Must apply cleanly | Format dictated by the applier: SEARCH/REPLACE for Aider diff, unified diff for git, `str_replace` for Anthropic editor tool. |

### Step 3 — Which model am I targeting?

Format support is **model-specific**. Aider maintains a per-model edit-format default precisely because of this. [aider.chat/docs/more/edit-formats.html]

| Model family | Best code-edit format | Notes |
|---|---|---|
| GPT-4 Turbo / GPT-4o | `udiff` or SEARCH/REPLACE diff | 20%→61% with udiff on refactor. [aider.chat/2023/12/21/unified-diffs.html] |
| Claude 3.5/3.7 Sonnet | SEARCH/REPLACE diff | Tendency to write *too much* — instruct minimal blocks. [aider.chat/2024/07/01/sonnet-not-lazy.html] |
| Gemini family | `diff-fenced` | Path inside the fence. [aider.chat/docs/more/edit-formats.html] |
| GPT-4.1 / OpenAI patch tool | `patch` protocol | OpenAI-specific, multi-action robust. |
| Weak / local models (Llama-3-8B class, GPT-3.5) | `whole` file rewrite | Diff parsing failures dominate; whole-file is dumb-but-stable. |
| Reasoning models (o1, o3) as architect | architect mode: reasoner emits prose plan → editor model emits diff | o1-preview alone: 79.7%; o1-preview + Sonnet editor: 82.7%. [aider.chat/2024/09/26/architect.html] |

Combined decision tree:

```
                    What's being emitted?
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
      code              structured           free-form
      edits              data fields          prose/reasoning
        │                   │                   │
        ▼                   ▼                   ▼
   diff/SEARCH-       JSON / Pydantic /    markdown
   REPLACE/           tool_use scalar
   str_replace,       args
   code as string
        │                   │                   │
        ▼                   ▼                   ▼
   pick per-model   wrap any code-          do NOT
   edit format      shaped payload in        force into
   (Aider table)    a single string field    JSON schema
```

---

## 4. 操作模型 (Task → format pairs)

Ten concrete operations. Format choice is *not* arbitrary — each citation is the empirical anchor.

| # | Task | Recommended format | Rationale / Evidence |
|---|---|---|---|
| 1 | "Edit `auth.py` to use JWT" (coder-agent core loop) | Plain-text SEARCH/REPLACE diff in markdown fence | Aider's measured 3× on GPT-4 Turbo, generalizes across models. [aider.chat/2024/08/14/code-in-json.html] |
| 2 | "Apply this patch to a file via Claude's text-editor tool" | Anthropic `str_replace` tool — old_str / new_str as **string fields**, no JSON sub-structure inside the code | Matches Anthropic's published tool-design guidance: fields should be high-signal scalars, not low-level identifiers. [docs.anthropic.com text-editor-tool] |
| 3 | "Extract invoice fields (vendor, amount, date, line items)" | JSON / Pydantic / DSPy typed `OutputField` | Schema **is** the task. Structured-output benchmarks show high accuracy here. [arxiv.org/html/2505.20139v1] |
| 4 | "Classify ticket priority (P0/P1/P2/P3)" | Single-token output or JSON `{"priority": "..."}` | Trivial; structure helps determinism. |
| 5 | "Answer a math word problem" | Markdown reasoning + final answer in `\boxed{}` or fenced final line | "Let Me Speak Freely?" — 10–15% degradation when locked into JSON reasoning. [arxiv.org/abs/2408.02442] |
| 6 | "Decide which tool to call next" | JSON tool_use with tool name + scalar args | Action selection is *intrinsically* structured. |
| 7 | "Generate the SQL query for that tool" | Tool args contain `{"sql": "SELECT ..."}` — SQL as a **raw single string**, no further JSON sub-structure | Same family as code-in-JSON; SQL is code-shaped. |
| 8 | "Write a customer-support reply" | Markdown | Native to instruction tuning; JSON-wrap costs nothing useful. |
| 9 | "Summarize a paper and return key claims as a list" | Markdown prose + a fenced `claims:` YAML or JSON block at the end (two-zone output) | Best of both: prose flows freely, downstream parser reads the trailing block. |
| 10 | "Rewrite a long document AND extract entities" | **Two passes**: pass 1 rewrite (markdown), pass 2 extract (JSON, fed the pass-1 output) | One call cannot serve both contents at peak quality. |

---

## 5. 困境决策案例 (Dilemma cases / worked examples)

### Case A — "I'm writing an extractor for invoice fields. Plain text or JSON?"

**Trigger**: New extraction pipeline. Fields = `vendor_name`, `total_amount`, `invoice_date`, `line_items[]`.

**Constraints**:
- Output is consumed by a downstream Python parser.
- Some line items contain free-text descriptions with newlines and quotes.
- Pydantic validation is desired.

**Decision steps**:
1. The content is **structured data**, not code. JSON tax is low here — fields are short scalars or short strings.
2. Use Pydantic + OpenAI `response_format=json_schema` or DSPy typed `OutputField`s. Field names carry the semantic load (DSPy's "Signatures carry semantic load" principle [dspy.ai/learn/programming/signatures]).
3. For `line_items[].description` containing free-text: still inside JSON — descriptions are *prose data*, not code. Escaping cost is real but bounded.
4. Watch for: extraction-then-rewrite mission creep. If a future spec says "also rewrite the invoice text in cleaner language" → switch to Case B's two-pass approach.

**Outcome**: JSON wins. Schema validation catches missing fields cheaply; no measurable degradation expected on this content shape.

### Case B — "Same task but the extractor *also* rewrites the invoice text"

**Trigger**: PM adds requirement — "and produce a cleaned-up version of the invoice document body."

**Constraints**:
- "Cleaned text" is multi-paragraph prose with embedded numbers, possibly tables.
- Putting `cleaned_text: "..."` inside the same JSON forces multi-paragraph escaping and competes with the extraction reasoning for attention.

**Decision steps**:
1. Recognize this as the **mixed-content trap**. One LM call cannot serve both contents at peak.
2. Two solutions, choose by latency budget:
   - **Two-pass** (preferred): Call 1 returns `{vendor, amount, date, line_items}` as JSON. Call 2 receives the original doc + extracted JSON, returns markdown rewrite.
   - **Two-zone single call**: Prompt requests markdown rewrite first, then `===EXTRACTION===` separator, then a fenced JSON block. Parser splits on the separator. Cheaper but more fragile.
3. Do not nest the markdown rewrite as a JSON string field. The model will compress it and lose structure.

**Outcome**: Plain text + JSON split, not unified JSON. **Format follows content**, even within one logical task.

---

### Case C — "Tool call decision, but the tool's input is SQL"

**Trigger**: Building a data-analyst agent. One tool is `run_query(sql: str)`.

**Constraints**:
- The agent must decide *which* tool to call (structured choice).
- The agent must *write SQL* (code-shaped content).
- Provider is OpenAI / Anthropic tool_use.

**Decision steps**:
1. The **tool-selection layer** is intrinsically structured — use JSON tool_use. The model picks `run_query` vs `read_file` vs `list_tables`.
2. The **tool body** is code. Per Aider's findings, code in JSON degrades. Mitigations:
   - Make `sql` a **single top-level string field**. Don't sub-structure it (`{from: ..., where: ...}`). Let the model write idiomatic SQL.
   - Keep other args as scalars (e.g. `dry_run: bool`).
   - Expect *some* quality hit vs returning SQL as plain text; budget for retry/repair.
3. If quality is unacceptable: switch the architecture. Generate SQL in a *separate* plain-text LM call (markdown fenced ```sql block), then a thin downstream agent wraps it into the tool call. This is the Aider "architect" pattern transplanted to data tools. [aider.chat/2024/09/26/architect.html]

**Outcome**: JSON for the decision; single string for the SQL body; consider a two-step generate-then-dispatch if quality matters.

---

### Case D — "Reviewer says 'use structured output everywhere for safety'"

**Trigger**: Eng-org-wide push to add `response_format=json_schema` to every LM call.

**Constraints**:
- The org has been bitten by `json.loads` failures.
- Some calls produce code; some produce prose; some produce typed objects.
- The reviewer is conflating "schema-valid" with "quality."

**Decision steps**:
1. Surface the empirical finding: **JSON validity ≠ content quality.** Cite Aider's 20%→61% (unified diff vs JSON) [aider.chat/2024/08/14/code-in-json.html] and "Let Me Speak Freely?" [arxiv.org/abs/2408.02442].
2. Audit each call by content type using §3 Step 1 table.
3. For code-emitting calls: keep markdown; add a defensive parser (regex extract from fenced block). The robustness cost is small; the quality gain is large.
4. For typed-object calls: yes, add `json_schema`. This is where structured output earns its keep.
5. Document the policy: **"Structured output is mandatory for typed-data extraction; forbidden for code edits and multi-step reasoning; optional for everything else."**

**Outcome**: Reject the blanket policy; replace it with a content-type-driven one. This is the inverse of the "JSON everywhere" reflex.

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **"JSON everywhere" reflex.** Structured ≠ better. Code, multi-step reasoning, long-form prose all degrade inside JSON envelopes — Aider measured 3× on code; arXiv 2408.02442 measured 10–15% on reasoning. Use JSON where the *content itself is structured*.
2. **"Markdown only when a human reads it" reflex.** Markdown is also an excellent LM-to-LM wire format and often the highest-quality format for the producing model. DSPy's default chat adaptor uses field-marked markdown for many signatures even with no human in the loop. [dspy.ai/learn/programming/signatures/]
3. **Wrapping code in JSON tool calls without budgeting quality loss.** If your harness *requires* tool calls, fine — but **acknowledge the tax** and put the code in a single string field. Don't sub-structure it into `{language, lines: [...], imports: [...]}`. Every level of nesting compounds the escape tax.
4. **Forcing reasoning into a `reasoning` JSON field.** Models compress and stiffen when reasoning is inside JSON — they treat it as a label rather than as thinking. Prefer free markdown reasoning followed by a structured tail.
5. **Using JSON schema as a substitute for prompt engineering.** Schema enforces *shape*. It does nothing for *correctness of contents*. Write the prompt as if there were no schema, then add the schema for safety.
6. **Asking for typed data as freeform prose, then post-hoc parsing with regex.** The inverse mistake. If the consumer is a parser and the fields are scalars, use a schema — the model is happy to oblige.
7. **Mixing code and prose in one JSON document.** Use two-zone output (prose followed by fenced block) or two passes.
8. **Ignoring per-model edit-format defaults.** Aider's defaults exist because the same edit format performs differently across models. Don't override without an A/B. [aider.chat/docs/more/edit-formats.html]
9. **Treating tool-use schemas as documentation-free zones.** Anthropic's tool-writing guide emphasizes high-signal field names (`name`, `file_type`) over technical identifiers (`uuid`, `mime_type`). The model reads your schema as part of its prompt. [anthropic.com/engineering/writing-tools-for-agents]
10. **"The task is fixing JSON, so format doesn't matter."** Counter-edge case: when the *content itself is JSON* (e.g. "fix this malformed JSON"), output it as a fenced ```json block in markdown — not as a JSON tool-call wrapping JSON-as-string. Even here, the rule holds: code-shaped content goes in a plain string surface, not nested escapes. [arxiv.org/html/2510.04717v1 — JSON Whisperer]

### Boundaries (when format choice doesn't matter much)

- The model is overwhelmingly capable for the task (GPT-5-class on entity extraction with 4 scalar fields). The format tax is dwarfed by headroom.
- The output is one token / one number / yes-no. Any format works; pick by parser convenience.
- The pipeline is one-shot exploration with no downstream consumer.
- You're forced into a format by an external contract (e.g. publishing to a webhook expecting JSON). Then your job is mitigation (single string fields for code-shaped payloads), not format choice.

---

## 7. 跨框架对照 (Ecosystem cross-reference)

How major frameworks implement format selection. Use this to translate the principles into the stack you're already in.

### Aider edit formats [aider.chat/docs/more/edit-formats.html]

| Format | Wire shape | When |
|---|---|---|
| `whole` | Full file in markdown fence | Weak models, fallback |
| `diff` (SEARCH/REPLACE) | Two fences per edit, byte-exact match | GPT-4o, Sonnet, most strong models — **default** |
| `diff-fenced` | Path inside fence | Gemini |
| `udiff` | GNU unified-diff style | GPT-4 Turbo — **the empirical anchor: 20%→61%** |
| `patch` | OpenAI patch protocol | GPT-4.1 |
| `editor-diff` / `editor-whole` | Slim prompt for sub-model | Architect mode editor |

**No JSON-wrapped edit format exists** — it was tested and rejected. [aider.chat/2024/08/14/code-in-json.html]

### DSPy adaptors [dspy.ai/learn/programming/signatures/]

DSPy's `Signature → Module` pipeline ships with multiple adaptors that materialize the same logical I/O contract into different wire formats:

- **`ChatAdapter`** (default): field-marked **markdown** with `[[ ## field_name ## ]]` headers. Used even for typed outputs because models reliably emit it.
- **`JSONAdapter`**: schema-enforced JSON. Used when the consumer must parse strictly (e.g., feeding another typed pipeline).
- **`TwoStepAdapter`**: free-form generation, then a second cheaper call reformats into JSON. Direct application of the "Let Me Speak Freely?" finding — generate freely, format separately. [arxiv.org/abs/2408.02442]

DSPy's recommendation: stay on ChatAdapter unless a downstream consumer demands JSON. The framework itself encodes the principle of this skill.

### Outlines / Guidance / LMQL (grammar libs)

- Token-level grammar enforcement (regex, CFG, JSON schema). Guarantees *validity*, not *quality of content*.
- Best used for: forced enums, numeric ranges, valid JSON shells around scalar fields.
- Worst used for: forcing code or long prose through a JSON grammar — you'll get valid JSON containing degraded code.
- Pair with this skill: choose format using §3, then use Outlines to *enforce* whichever format you chose.

### OpenAI tool_use / function calling

- Tool **selection**: structured by definition. Use it.
- Tool **arguments**: keep scalar where possible; wrap code-shaped payloads in a single string field.
- `response_format=json_schema` for typed extraction: yes. For code generation: avoid; if forced, single string field with `code` as the type.
- "Strict mode" (`strict: true`) guarantees schema validity but **does not fix content degradation** — Aider tested this explicitly. [aider.chat/2024/08/14/code-in-json.html]

### Anthropic tool_use / text-editor tool [docs.anthropic.com text-editor-tool]

- Built-in `text_editor` tool: commands `view`, `str_replace`, `create`, `insert`, `undo_edit`. **`str_replace` takes `old_str` and `new_str` as single string fields** — explicitly avoiding the JSON-nests-code anti-pattern. This is the principle of this skill made into a first-party API.
- Tool-writing guidance: high-signal scalar field names; avoid low-level identifiers in tool schemas. [anthropic.com/engineering/writing-tools-for-agents]

### Cross-framework summary

```
Layer                  | Format mechanism
-----------------------|-----------------------------------
Generation grammar     | Outlines / Guidance — enforce
Per-task adaptor       | DSPy ChatAdapter vs JSONAdapter
Per-model edit format  | Aider's edit-format table
Tool envelope          | OpenAI / Anthropic tool_use
Wire serialization     | markdown vs JSON vs YAML
```

Every layer can independently make a wrong format choice. This skill operates at the **per-task** layer: decide first *what format the content wants*, then let each lower layer enforce it.

---

## Quick reference card

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FORMAT DECISION CARD                          │
├──────────────────────────────────────────────────────────────────────┤
│ Code edits          → text + diff (per-model: udiff/SEARCH/whole)    │
│                       [Aider: 20% → 61% on GPT-4 Turbo]              │
│ Code generation     → markdown fenced block                          │
│ SQL / regex / shell → string field inside tool_use, NOT sub-JSON     │
│ Entity extraction   → JSON / Pydantic / typed OutputField            │
│ Classification      → single token or JSON {label}                   │
│ Action selection    → JSON tool_use                                  │
│ Reasoning + answer  → markdown CoT + fenced final answer             │
│                       [Format-restricted reasoning: -10 to -15%]     │
│ Prose / explanation → markdown                                       │
│ Mixed content       → two passes OR two-zone output                  │
├──────────────────────────────────────────────────────────────────────┤
│ NEVER:                                                               │
│  • Nest code inside JSON sub-structure                               │
│  • Force CoT reasoning into a JSON "reasoning" field                 │
│  • Use schema as substitute for prompt engineering                   │
│  • Assume strict-mode JSON fixes content quality                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 引用源 (Citations)

**Primary empirical anchors:**
- Aider code-in-JSON benchmark: [aider.chat/2024/08/14/code-in-json.html] — "All of the models did worse on the benchmark when asked to return code in a structured JSON response."
- Aider unified diff vs JSON: [aider.chat/2023/12/21/unified-diffs.html] — GPT-4 Turbo refactor 20% → 61% with udiff; "lazy comments" cut to 1/3.
- Aider edit-format docs: [aider.chat/docs/more/edit-formats.html]
- Aider architect mode: [aider.chat/2024/09/26/architect.html] — o1-preview alone 79.7% → o1-preview + Sonnet editor 82.7%.
- Aider Sonnet-not-lazy: [aider.chat/2024/07/01/sonnet-not-lazy.html]

**Academic generalization:**
- "Let Me Speak Freely?" — arXiv 2408.02442 [arxiv.org/abs/2408.02442] — Format restrictions cause 10–15% drop on reasoning tasks.
- StructEval — arXiv 2505.20139 [arxiv.org/html/2505.20139v1] — Even o1-mini 75.58 avg on structural-output generation.
- JSON Whisperer (JSON-editing) — arXiv 2510.04717 [arxiv.org/html/2510.04717v1]
- To Diff or Not to Diff (2025 edit-format study) — [arxiv.org/html/2604.27296]

**Framework / API docs:**
- DSPy Signatures + adaptors: [dspy.ai/learn/programming/signatures/]
- DSPy FAQ on structure vs free-form: [dspy.ai/faqs/]
- Anthropic text-editor tool: [docs.anthropic.com/en/docs/agents-and-tools/tool-use/text-editor-tool]
- Anthropic writing-tools-for-agents: [anthropic.com/engineering/writing-tools-for-agents]
- OpenAI structured outputs: [platform.openai.com/docs/guides/structured-outputs]

**Companion skills in this collection:**
- `aider-sop-skill/SKILL.md` — full edit-format treatment in coder-agent context.
- `dspy-sop-skill/SKILL.md` — adaptor selection within compiled programs.
