# R1 — Source evidence for module-shape-selection

This overlay's claims trace to two local skills and the DSPy docs. Each row below pins a
SKILL.md claim to its source.

## Source A — local `dspy-sop` SKILL.md
Path: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`

| Overlay claim | Source location | Quoted/paraphrased evidence |
|---|---|---|
| "Pick the lowest-power Module that works. Default to ChainOfThought." | §3 Stage 1, step 2 (line 79) | "Pick the lowest-power Module that works. Default to `dspy.ChainOfThought`. Use `dspy.Predict` for trivial classification, `dspy.ReAct` only when tools are needed, `dspy.ProgramOfThought` for arithmetic-heavy tasks." |
| Module selection card (the four shapes) | §4.2 Module selection (lines 124–132) | Table: Simple in→out → `Predict` (lowest overhead); Reasoning helps → `ChainOfThought` (**default**); Math/counting/parsing → `ProgramOfThought` (code execution grounds); Tools → `ReAct` (built-in tool loop). |
| Escalation: vote across N CoT samples | §4.2 (line 131) | "Ensemble for hard cases → `dspy.MultiChainComparison` or `dspy.majority` → Vote across N CoT samples." |
| Shape is chosen in Stage 1, before optimizer | §3 Stage 1 (lines 76–83) | Programming stage occurs before Evaluation/Optimization; module pick is step 2 of Stage 1. |
| "An optimizer cannot repair a wrong shape" | §6 anti-pattern 7 (line 252) | "If MIPROv2 light + medium both flatline, the bottleneck is almost always the **program graph** (wrong decomposition, wrong module choice) not the optimizer." |
| Inspect outputs on 5–10 examples before escalating | §3 Stage 1, step 4 (line 81) | "Run zero-shot on 5–10 hand-picked examples. Look at outputs with `dspy.inspect_history(n=3)`." |
| ReAct is a thin tool-loop, not an agent framework | §6 anti-pattern 6 (line 251) | "ReAct is a thin tool-loop, not a multi-agent framework." |

## Source B — local lib `dspy` SKILL.md (frontmatter + body)
Path: `~/.claude/skills/dspy/SKILL.md`

| Overlay claim | Source location | Quoted/paraphrased evidence |
|---|---|---|
| Lib skill lists four modules without a selection rubric | Core Concepts §2 (lines 110–161) | Sections for `dspy.Predict`, `dspy.ChainOfThought`, `dspy.ReAct`, `dspy.ProgramOfThought` — each shown with code, none with a "choose this when" criterion beyond prose. |
| Predict = basic prediction, lowest overhead | §2 dspy.Predict (lines 114–121) | "Basic prediction module." |
| CoT emits a reasoning/rationale field | §2 dspy.ChainOfThought (lines 123–131) | "Generates reasoning steps before answering" → `result.rationale`. |
| ReAct = agent-like reasoning *with tools* | §2 dspy.ReAct (lines 133–151) | "Agent-like reasoning with tools"; constructed as `ReAct(SearchQA, tools=[search_tool])`. |
| PoT generates AND executes code | §2 dspy.ProgramOfThought (lines 153–160) | "Generates and executes code for reasoning"; `# Generates: answer = 240 * 0.15`. |
| "Start with Predict, add CoT if needed" (the under-specified default) | Best Practices §1 (lines 485–496) | "Start with Predict / Add reasoning if needed / Add optimization when you have data." — never operationalizes "if needed", which this overlay supplies. |
| Frontmatter (overlap avoidance) | Frontmatter (lines 1–9) | `name: dspy`, declarative-programming description, dependencies `[dspy, openai, anthropic]`. Overlay reuses none of the install/API content. |

## Source C — DSPy docs (cited inline in both local skills)

| Overlay claim | Citation |
|---|---|
| Module semantics & "default to ChainOfThought" line | [dspy.ai/learn/programming/modules/] |
| Shape chosen in Programming stage, before metric/compile | [dspy.ai/learn/] |
| Optimizer operates on the given program graph | [dspy.ai/learn/optimization/overview/] |

## Overlap-avoidance note

The lib skill [[dspy]] owns: install, signature syntax, LM-provider wiring, module APIs,
optimizer code examples. The SOP skill [[agentsop-dspy]] owns: optimizer/teleprompter choice,
metric design, compile-cost guardrails, deployment. This overlay owns **only** the upfront
shape-selection rubric (classify task → pick shape → measure cost), which neither source
surfaces as a standalone decision.
