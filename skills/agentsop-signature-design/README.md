# signature-design skill

An **enhancement-overlay** coder skill that surfaces one decision the broad `dspy` library skill never states
outright: **when to promote a prose prompt into a typed `dspy.Signature`, and how to shape its fields.**

**Version**: 0.1.0
**Layer**: enhance overlay (decision rubric only — defers all implementation to `[[dspy]]` and `[[agentsop-dspy]]`)

## What this skill answers

- **When** a hand-written prompt has become "load-bearing" enough to deserve a typed contract (the promote
  trigger: > ~50 lines, output consumed by code, or reused across calls).
- **How** to shape the Signature: identify inputs/outputs, name fields semantically, add descriptions only where
  the name underspecifies, type closed-set/boolean outputs.
- **When NOT to**: one-shot throwaway prompts, free-form human prose, or while the I/O contract is still churning.
- **Where the line is** between "promote to a typed Signature" (parse safety) and "compile/optimize it" (needs a
  metric) — two different gates.

## What this skill does NOT do

It is **not** a DSPy tutorial. It deliberately defers every implementation question — class syntax, module choice
(`Predict`/`ChainOfThought`/`ReAct`), evaluation, compile, save/deploy — to the existing skills:

- **`[[dspy]]`** — the library skill (HOW to write/compile a Signature).
- **`[[agentsop-dspy]]`** — the full operating workflow (program → evaluate → optimize, 3-stage gate, optimizers, cost).

This overlay is the narrow "should this prose become a Signature?" slice of `[[agentsop-dspy]]`'s Stage 1.

## Files

- `SKILL.md` — main skill, 7 sections: 何时激活 / 核心心智模型 / SOP / 操作模型 (8 ops + naming rules) / 困境决策案例 (2) / 反模式与边界 / 跨框架对照.
- `references/R1-source-evidence.md` — every claim (S1–S10) traced verbatim to the local `dspy-sop` skill and the
  upstream DSPy docs it cites; includes the overlap check vs the local `dspy` library skill.
- `intermediate/operation_candidates.json` — the 8 operations in Trigger / Action / Output / Evidence form, plus
  field-naming rules, dilemma cases, and anti-patterns.

## Quick start

If you just want to decide one prompt today:

1. Run the **promote-trigger checklist** (`SKILL.md` §4.1): tick LENGTH / CONSUMED / REUSED. Zero ticks → keep the
   prose prompt, you're done.
2. One+ tick → run the SOP (§3): extract inputs/outputs → name fields semantically → add descriptions only where
   needed → type closed-set outputs.
3. Hand the shaped Signature to **`[[dspy]]`** for module choice + compile. This skill's job ends there.

## Source basis

- Primary: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md` (Signatures material).
- Upstream (as cited by the primary): [dspy.ai/learn/programming/signatures/], [dspy.ai/cheatsheet/],
  [dspy.ai/faqs/], [arxiv.org/abs/2310.03714].
- Overlap-avoidance: frontmatter of `~/.claude/skills/dspy/SKILL.md` confirms that skill is the broad library
  layer; this overlay holds a disjoint decision-only scope (see `references/R1-source-evidence.md`).
