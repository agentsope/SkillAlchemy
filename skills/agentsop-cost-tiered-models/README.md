# cost-tiered-models skill

Cost-aware model/role split — **"strong reasoner + cheap executor"**. A multi-call LM workflow has uneven cognitive load: a few calls need reasoning, most are mechanical. Use a strong model to *decide*, a cheap model to *execute* — and most calls are execution.

This is a **Phase-D enhance skill (M7)**. Phase B found this exact pattern recurring across **4 SOPs under 4 different names**. No existing skill unified it. This one does.

## The unified pattern

> Split by cognitive demand, not by "which model is more accurate". A strong model decides; a cheap model executes; an escalation valve catches the long tail.

Four frameworks, one shape:

| Framework | Local name | Strong (decide) | Cheap (execute) |
|---|---|---|---|
| **Aider** | architect + editor | architect (o1-preview) | editor (Sonnet / o1-mini) |
| **DSPy** | optimizer-LM vs task-LM | task-LM (gpt-4o) — *mirror* | optimizer-LM (gpt-4o-mini) |
| **LangGraph** | supervisor + worker | supervisor (route/synthesize) | worker sub-agents |
| **vLLM** | speculative draft + target | target (verify) | draft (EAGLE / n-gram) |

The headline evidence is Aider's published Polyglot Pass@2 numbers: o1-preview alone **79.7%**, o1-preview + Sonnet **82.7%**, o1-preview + o1-mini **85%** — two cheap specialized calls beat one expensive all-in-one call [aider.chat/2024/09/26/architect.html].

## Scope

- **Activation**: any multi-call LM workflow where some calls need reasoning and others are mechanical (rewrite / extract / format / apply a decided plan / draft).
- **Not for**: single-call workflows (no roles to split), tiny workflows (split overhead > savings), quality-only / unlimited-budget settings, or "which inference engine" questions (that is the `llm-engine-selection` skill).
- **Date stamp**: May 2026. Model lineups and price/quality frontiers move fast; re-measure the quality delta on your own task before committing.

## Layout

```
d-cost-tiered-models-skill/
├── SKILL.md                          # 7-section SOP (activation → cross-framework table)
├── README.md                         # This file
├── references/
│   └── R1-source-evidence.md         # Cited claims traced to the 4 source SOPs + primary docs
└── intermediate/
    └── operation_candidates.json     # Raw trigger / action / output / evidence for OP-1..7
```

## What's in SKILL.md

- **§1 何时激活** — uneven-cognitive-load multi-call workflows; the "all-in-one strong model" reflex to challenge.
- **§2 核心心智模型** — Tier-S (decide, few calls, strongest reasoner) vs Tier-E (execute, most calls, cheap); why "strong reasoner, weak executor" is the norm; the escalation valve.
- **§3 SOP** — list calls → label cognitive load → assign tiers → measure quality delta → add escalation valve → tune the split point.
- **§4 操作模型** — 7 ops: role-tier mapping, the architect+editor recipe, fallback-escalation, format-by-tier, cheap-optimizer/expensive-task, distill-after-split, supervisor/worker tiering.
- **§5 困境决策案例** — (1) is Aider architect mode worth the cost? (2) when does a cheap executor degrade enough to escalate?
- **§6 反模式与边界** — one-model-for-everything; over-splitting tiny workflows; splitting without measuring delta; format overload on the cheap model; no escalation valve; split-as-switch; not recalibrating after a model swap.
- **§7 跨框架对照** — the four-name / one-shape table, the three shared structures, and why DSPy is a *mirror* of the same principle.

## Method

Mined from four sibling SOP skills in this repo (`dspy-sop-skill`, `aider-sop-skill`, `langgraph-sop-skill`, `vllm-sop-skill`). Every load-bearing number carries an inline `[source]` tag resolving to a primary doc or the source SOP. Aider's Polyglot figures are quoted as published. No fabrication.

## Position in the Phase-D enhance set

- **Companion decision skill**: `llm-engine-selection` (which runtime), `output-format-by-model` (which edit format) — orthogonal axes to this one (which *tier* per call).
- **Per-framework deep dives**: the four source SOP skills remain authoritative for their own knobs; this skill is the cross-framework abstraction that fires when the decision is "how to tier", regardless of stack.
