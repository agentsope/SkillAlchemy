# structured-output-picker skill

Cross-library **enhancement overlay** for **structured-output enforcement** —
when an LM output is consumed by code, decide *which* enforcement mechanism
(Outlines / Instructor / Guidance / provider-native) and *how* to handle a
malformed output (Assert hard-fail vs Suggest soft-nudge).

This is an **M4 gap skill** in the Phase-D enhance pass. The local libs
`outlines`, `instructor`, and `guidance` each work in isolation, but no single
lib skill answers the cross-library question: *which one + how to handle
failures*. That decision is hit every time LM output is parsed/typed by code.
This is that skill.

## Scope

- **Activation**: an LM output feeds a parser / Pydantic model, and the shape was
  already decided to be "typed/validated object" by `[[agentsop-output-format-by-model]]`.
- **Core insight**: *constraint at decode (grammar) vs constraint at validate
  (retry) — pick by how costly a malformed output is, gated by whether you control
  the decoder.* Then pick the failure stance: **Assert** vs **Suggest**.
- **Date stamp**: May 2026. Re-verify provider structured-output APIs each quarter.

## Layout

```
d-structured-output-picker-skill/
├── SKILL.md                          # 7-section SOP (activation → cross-framework table)
├── README.md                         # this file
├── references/
│   └── R1-source-evidence.md         # every cited claim resolved to a source SKILL line
└── intermediate/
    └── operation_candidates.json     # raw trigger/action/output/evidence operations
```

## Key claim

> "Make the model emit valid structure" splits into two distinct mechanisms:
> **decode-time** grammar (Outlines/Guidance/provider strict-mode) cannot emit an
> invalid shape but needs decoder access; **validate-time** retry
> (Instructor/DSPy) catches a bad output and re-asks but can run on any API model.
> Pick by the cost of a malformed output and by decoder access; then pick the
> failure stance (Assert vs Suggest). Enforcement never buys back *content*
> quality — that is decided earlier by the output *shape*.

The skill encodes the decode-vs-validate axis, the two prerequisites (decoder
access, code-shaped content), the Assert/Suggest stance, an 8-row picker table,
2 dilemma cases (Instructor-retries-vs-Outlines on an API model; local batch with
no retry budget), 8 anti-patterns, and the cross-framework mapping
(Outlines / Instructor / Guidance / provider-native / DSPy stance).

## ENHANCE overlay

This skill is an **overlay**, not a replacement. For each library's API it
cross-links the base skill inline as `[[name]]`:

- `[[outlines]]` — decode-time regex / CFG / JSON-schema for local models.
- `[[instructor]]` — validate-time Pydantic + auto-retry + streaming for API models.
- `[[guidance]]` — decode-time grammar + Pythonic control flow for local models.
- `[[agentsop-output-format-by-model]]` — sibling Phase-D skill; decides the *shape* first.

Activate this skill for the *enforcement decision*; descend to the base skill for
the API surface.

## Method

Mined from the three local lib skills (`~/.claude/skills/{outlines,instructor,
guidance}/SKILL.md`), the DSPy Assert/Suggest primitives in `dspy-sop-skill`, and
the sibling `d-output-format-by-model-skill`. Every load-bearing claim carries an
inline `[[source]]` tag and resolves in `references/R1-source-evidence.md`. No
fabricated APIs.

## Position in the Phase-D inventory

- **Sibling overlay it composes with**: `d-output-format-by-model-skill` — that
  skill picks the output *shape* (code vs JSON vs prose vs typed); this skill
  picks the *enforcement* once the shape is "typed". They chain:
  shape → enforcement → stance.
- **Boundary**: if the shape decision lands on code / reasoning / prose, this
  skill does **not** apply — go back to `[[agentsop-output-format-by-model]]`. Grammar-
  constraining code yields valid JSON containing degraded code.
