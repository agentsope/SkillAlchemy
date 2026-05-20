# module-shape-selection (M2)

**Enhancement overlay** on the [[dspy]] library skill. Surfaces the one decision the
lib skill leaves implicit: **which reasoning shape to pick before you write a prompt.**

## What it is

The local `dspy` skill lists four modules — `Predict`, `ChainOfThought`, `ReAct`,
`ProgramOfThought` — and advises "start simple, add CoT if needed." It never makes
*"if needed"* operational, so the practical result is a **CoT-everywhere reflex**.

This overlay is the missing rubric:

```
no reasoning, no tool        → Predict
reasoning, no tool           → ChainOfThought
any real tool / action       → ReAct(tools=[...])
math / count / strict parse  → ProgramOfThought
```

Core claim: **reasoning shape is chosen by task structure, not by defaulting to CoT.**

## When it fires

Every time a **new LM-calling step/node** is added to a pipeline (a `forward()` line,
a LangGraph/CrewAI node, a fresh `dspy.<Module>(Sig)`). Hit on every new node.

## When it does NOT fire

- One-shot prompts (no pipeline).
- Optimizer / teleprompter choice → that is `[[agentsop-dspy]]`.
- Non-LM control flow.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The overlay: 7 sections (activate / mental model / SOP / selection card / dilemma cases / anti-patterns / cross-framework). |
| `references/R1-source-evidence.md` | Line-cited evidence from the two source skills + DSPy docs. |
| `intermediate/operation_candidates.json` | Extracted, reusable selection operations. |

## Position in the stack

```
[[dspy]]        → module API, signatures, LM wiring   (HOW to call)
this overlay    → WHICH shape to call                 (WHAT shape, upfront)
[[agentsop-dspy]]    → metric + optimizer + compile         (HOW to tune it, later)
```

Shape first, optimizer second. An optimizer cannot repair a wrong shape.

## Relationship to other skills

- Depends on (cross-links): `[[dspy]]`, `[[agentsop-dspy]]`.
- Overlaps avoided: no install, no signature syntax, no optimizer tables (all live in
  the linked skills). This file adds only the selection decision.

Version 0.1.0.
