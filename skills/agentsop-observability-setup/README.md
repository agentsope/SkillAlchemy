# observability-setup (E3 — Enhancement overlay)

**One line:** the *decision + one-line-wiring* layer for LM observability. Picks **which** backend
(LangSmith / Phoenix / MLflow / Langfuse / OpenTelemetry) and turns it on fast — the gap the
single-backend skills leave open.

## Why this exists

The local skills [[langsmith]], [[phoenix]], and [[mlflow]] each install and teach **one** backend
deeply. None of them helps a coder **decide which backend** fits their stack/scale/budget, or gives
a single-line autolog to turn it on before the first deploy. All 7 Phase A SOPs reference
observability (langgraph's AP-15 "don't skip LangSmith", llamaindex's "LangSmith / Phoenix",
dspy's MLflow + LangFuse lines) but assume the choice is already made. This overlay fills that gap,
then hands off to the chosen backend's own skill.

## Type

ENHANCE overlay — sits one level above the per-backend skills. Cross-links:
`[[langsmith]]`, `[[phoenix]]`, `[[mlflow]]`, `[[agentsop-prompt-history-inspect]]`.

## When it fires

- Starting any LM project (no tracing wired yet)
- Before the first deploy (the AP-15 trap)
- "Why did it do that?" asked, and there are no traces to answer with

## When it does NOT fire

- Backend already chosen → use that backend's skill directly
- Need to read one prompt right now → [[agentsop-prompt-history-inspect]]
- Pure ML experiment tracking, no LLM calls → plain MLflow

## Core idea

> Instrument before you need it. The cheapest debugging is a trace you already have.

## SOP

pick backend by stack/scale/budget → one-line autolog → verify a trace landed → add eval hooks → hand off.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The skill — 7 sections, decision table, 6 ops, 2 dilemma cases |
| `README.md` | This file |
| `references/R1-source-evidence.md` | Traceable citations from the Phase A SOPs + backend frontmatter |
| `intermediate/operation_candidates.json` | Machine-readable op + decision + anti-pattern inventory |

## Relationship to neighbors

- **[[agentsop-prompt-history-inspect]]** = reactive, single-prompt, no setup (first move on a bug).
- **observability-setup** (this) = proactive, persistent, decision + wiring (so the next "why" already has a trace).
- **[[langsmith]] / [[phoenix]] / [[mlflow]]** = the depth layer once a backend is chosen.
