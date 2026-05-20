# R1. Source Evidence — structured-output-picker claims resolved to sources

Every load-bearing claim in `SKILL.md` resolves here to a line in a source
skill. This is an ENHANCE overlay; no new external API is introduced beyond what
the source skills already document. Sources:

- Lib skills: `~/.claude/skills/{outlines,instructor,guidance}/SKILL.md`
- Stance: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`
- Shape (cross-link): `/Users/5imp1ex/Desktop/Skill-Workplace/output/d-output-format-by-model-skill/SKILL.md`

Citation tags in SKILL.md: `[[outlines]]`, `[[instructor]]`, `[[guidance]]`,
`[[agentsop-output-format-by-model]]`, and `[dspy 2312.13382]` for the stance paper.

---

## Principle — decode-time vs validate-time enforcement (§2.1)

- **Claim**: Outlines / Guidance enforce structure at *decode* by masking tokens;
  the model *cannot* emit an invalid shape.
- **Source**: `[[outlines]]` frontmatter "Guarantee valid JSON/XML/code structure
  **during generation**" + "Generate against JSON schemas automatically" +
  "Grammar-Based Generation" tag. `[[guidance]]` frontmatter "Control LLM output
  with regex and grammars", "Constrained Generation", "guarantee valid
  JSON/XML/code generation".
- **Claim**: Instructor enforces at *validate* by parsing into Pydantic and
  retrying on failure; the model *can* emit invalid output, which is then caught.
- **Source**: `[[instructor]]` frontmatter "Extract structured data … with
  Pydantic validation, **retry failed extractions automatically**" + "When to
  Use": "Validate outputs against Pydantic schemas automatically", "Retry failed
  extractions with automatic error handling", "Stream partial results".

## Prerequisite 1 — decoder access gates the grammar libraries (§2.2)

- **Claim**: token-masking grammar (Outlines/Guidance) needs logit access → local
  / open weights; not available on closed API models.
- **Source**: `[[outlines]]` "When to Use": "**Support local models**
  (Transformers, llama.cpp, vLLM)" + dependencies `[outlines, transformers,
  vllm, pydantic]`. `[[guidance]]` dependencies `[guidance, transformers]` (local
  HF stack). `[[instructor]]` dependencies `[instructor, pydantic, openai,
  anthropic]` — explicitly wraps the closed API providers, i.e. works without
  decoder access.

## Prerequisite 2 — don't enforce on code-shaped content (§2.2, §6 A3/A4)

- **Claim**: grammar-constraining code yields valid JSON containing degraded
  code; strict-mode JSON validity ≠ content quality.
- **Source**: `[[agentsop-output-format-by-model]]` §2.1 — Aider code-in-JSON benchmark
  GPT-4 Turbo 61%→20%; §7 "Strict mode (`strict: true`) guarantees schema
  validity but **does not fix content degradation** — Aider tested this
  explicitly." §7 grammar-libs row: "Worst used for: forcing code or long prose
  through a JSON grammar — you'll get valid JSON containing degraded code." Cross-
  linked, not duplicated.

## Stance — Assert vs Suggest (§2.3, §3 Step 3, §6 A2)

- **Claim**: Assert = hard fail/halt after N retries; Suggest = retry with error
  injected, then log + continue. Assert for dev / unrecoverable values; Suggest in
  production for graceful degradation.
- **Source**: `dspy-sop-skill/SKILL.md` §"Constraint primitives — `dspy.Assert`
  vs `dspy.Suggest`": "Hard: halts after max retries with dspy.AssertionError" /
  "Soft: retries with feedback in prompt, logs failure, continues" / "Use Assert
  during development (catch bugs hard). Use Suggest in production (degrade
  gracefully)." Paper [arxiv.org/pdf/2312.13382]. Backtrack-and-reprompt
  mechanism quoted verbatim from the same section.

## §3 SOP — start at the weakest sufficient layer

- **Claim**: prefer validate-time (cheaper to build, natural generation, no
  decoder access) and escalate to decode-time only when retry is too costly or the
  contract is absolute.
- **Source**: derived from `[[instructor]]` low-friction "retry automatically" +
  `[[outlines]]` "**zero-overhead** structured generation / maximize inference
  speed" (the decode-time path is the heavier guarantee). The "cheapest sufficient
  ladder, promote upward as needed" pattern mirrors the sibling Phase-D
  query-routing skill's tiering discipline.

## §4 Picker table — per-row anchors

- Rows 1, 8 (Instructor: Pydantic+retry, streaming): `[[instructor]]` "When to
  Use" bullets (validate, retry, stream partial results).
- Rows 2, 3, 7 (Outlines: choice/enum, JSON-schema, regex): `[[outlines]]`
  frontmatter "regex … JSON Schema … Type Safety" + "Generate against JSON
  schemas automatically", "Enforce structured formats (dates, emails, IDs)".
- Row 4 (Guidance: interleaved text + constrained block + control flow):
  `[[guidance]]` "When to Use": "Build multi-step workflows with Pythonic control
  flow" + "Control LLM output syntax with regex or grammars".
- Row 5 (provider native): provider docs (named in SKILL.md citations);
  `[[agentsop-output-format-by-model]]` §7 OpenAI/Anthropic tool_use + strict-mode rows.
- Row 6 (semantic/cross-field check + stance): `dspy 2312.13382` Assert/Suggest;
  grammars constrain token shape only.

## §5 Dilemmas

### Case A (Instructor retries vs Outlines on an API model)
- **Outlines unavailable on closed API**: prerequisite §2.2(1), sourced above.
- **Move shape to provider native, keep Instructor for typing**:
  `[[agentsop-output-format-by-model]]` §7 OpenAI/Anthropic native + strict-mode;
  `[[instructor]]` typing/validation role.
- **Cap retries + flip to Suggest**: `dspy` Suggest = log + continue.
- **Valid-but-wrong content is a shape/prompt problem**:
  `[[agentsop-output-format-by-model]]` mixed-content trap (§5 Case B there).

### Case B (local batch, no retry budget)
- **Decode-time grammar for no-retry-budget**: `[[outlines]]` decode-time
  guarantee + local-model support; the no-retry-budget framing is the §2.1 cost
  axis applied.
- **Outlines vs Guidance choice (flat JSON vs interleaved)**: `[[outlines]]`
  JSON-schema vs `[[guidance]]` multi-step/interleaved control flow.
- **Suggest semantic check + quarantine**: `dspy` Suggest "log + continue".

## §6 Anti-patterns — anchors

- A1 grammar-when-retry-suffices, A8 pick-library-last: derived from the weakest-
  sufficient-layer ladder (§3).
- A2 Assert-over-rejection: `dspy` "Use Suggest in production (degrade
  gracefully)".
- A3 enforce-on-code, A4 strict-mode-≠-content: `[[agentsop-output-format-by-model]]` §2.1
  + §7 (Aider 61%→20%, strict-mode tested).
- A6 Outlines-on-closed-API: prerequisite §2.2(1).
- A7 grammar-for-semantic-rules: grammars constrain token shape, not relations —
  `dspy` semantic assertions cover that gap.
- A5 unbounded-retry: implied by `[[instructor]]` retry having a `max_retries`
  bound; an uncapped loop is the failure mode.

## §7 Cross-framework table — verbatim anchors

- **Outlines** decode / regex / CFG / JSON-schema / local-only: `[[outlines]]`
  frontmatter + dependencies.
- **Instructor** validate / Pydantic / retry / streaming / API: `[[instructor]]`
  frontmatter + dependencies.
- **Guidance** decode + control flow / local: `[[guidance]]` frontmatter +
  dependencies.
- **Provider native** strict-mode / API-only: provider docs;
  `[[agentsop-output-format-by-model]]` §7.
- **DSPy Assert/Suggest** stance layer: `dspy-sop-skill` §Constraint primitives.

---

## Provenance note

All three lib SKILLs, the DSPy SOP skill, and the sibling output-format-by-model
SKILL were read on 2026-05-20. No claim in this overlay asserts an API or behavior
absent from those sources. Provider structured-output APIs (OpenAI structured
outputs, Anthropic tool_use) are named only; re-verify exact request fields
against current provider docs before pasting into code (May 2026).
