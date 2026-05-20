# d-repo-state-gating-skill

A 5-minute gate the coder-agent runs at project kickoff to classify the repo and pick the right tool/strategy *before* writing the first prompt.

## What it answers

> "Am I in a greenfield, brownfield, mid-size familiar, or library/SDK repo? And what does that imply for tool choice, context primitive, and autonomy?"

## Why it exists

Phase C gap analysis (`output/phase-c-gap-analysis.md` row A1) flagged this as a `new_distill` gap: **medium frequency, high savings-per-event**. No local skill, no skill.sh match. The wrong tool at kickoff wastes 1–3 hours.

Phase B inventory: every coder SOP except the most autonomous ones implicitly assumes a state, but **none gates explicitly**.

## What's inside

- `SKILL.md` — the operational doc. 7 sections, ~400 lines. Triggers, mental model, 5-step SOP, 8 ops, 4 cases, anti-patterns, cross-framework table.
- `references/R1-state-taxonomy.md` — definitions and edge cases for the 4 states (greenfield / brownfield-large / mid-size-familiar / library-SDK).
- `references/R2-gate-questions.md` — the 5 question rubric + decision tree, and what to do with multi-state monorepos.
- `intermediate/operation_candidates.json` — 8 ops in machine-readable form (gate-classify, per-state strategies, reclassify, multi-state, mismatch-rescue).

## Lineage

- **Primary**: `output/aider-sop-skill/` (R4 anti-pattern §1 — "Aider's edge assumes existing code; for greenfield repo-map is empty.")
- **Secondary**: `output/dify-sop-skill/` (code-escape-hatch — visual builder helps greenfield prototypes; brownfield wants raw code).
- **Tertiary**: `output/dspy-sop-skill/` ("don't compile until the signature stabilizes" — same shape as "don't choose a brownfield tool until the repo *is* brownfield").
- **External**: BMAD greenfield-vs-brownfield, GSD /gsd-map-codebase workflow, "The Brownfield Problem" (jjmasse 2026), 2026 AI coding tool comparison surveys.

## When to use

Trigger at every:

- new `cd` into a repo for an agent session
- post-merge or post-scaffold inflection point
- "should I use Cursor or Aider here?" hesitation moment

Skip if you already gated this repo today and nothing changed.

## Frontmatter

```
name: repo-state-gating
version: 0.1.0
```

Tool skill (decision artifact, not a deep library doc). Intended to be ~5 min to apply.
