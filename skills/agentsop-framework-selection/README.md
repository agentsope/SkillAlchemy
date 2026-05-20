# framework-selection (Phase D capstone skill)

A **neutral**, framework-agnostic decision tree for the question every LLM/agent/RAG
project opens with: *"which framework should I reach for?"*

This is the most-cited skill at project kickoff. Unlike vendor documentation and
the LangChain-biased `framework-selection` already on skill.sh, this skill takes
**no side** — it synthesizes the ecosystem (R5) sections of 7 landmark-project SOPs
and surfaces where they *disagree* rather than papering over it.

## Core stance

**Frameworks are layers, not competitors.** A real project usually combines:

```
DSPy (compile L1) + LlamaIndex (retrieve L2) + LangGraph (orchestrate L3)
+ vLLM (serve L6) + optionally Dify (app platform L7)
```

You choose **one framework per layer**, then check interop — you do not crown a
single winner.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | The skill: 7 sections — when to activate, layered mental model, 3-pass SOP, per-layer pick rubrics (G0 + OP-1..8), 4 dilemma cases, anti-patterns, full cross-framework map. |
| `references/R1-decision-tree.md` | Source evidence: the layered decision trees, the comparison matrices, and every inline source tag (`<sop> · <id>`) used in SKILL.md, resolved to the 7 SOPs' R5 docs and the Phase B inventory. |
| `intermediate/operation_candidates.json` | Structured atom inventory: layers, operations (G0, OP-1..8), dilemma cases, anti-patterns, with triggers/actions/outputs/evidence. |

## How it composes with sibling Phase D skills

- `[[agentsop-llm-engine-selection]]` — owns the L6 serving sub-tree (vLLM/SGLang/TGI/…).
  This skill defers there the moment self-hosting is needed.
- `[[agentsop-agent-topology-selection]]` — owns the L3 single-vs-multi-agent + topology
  sub-tree. This skill gates through it before any orchestrator pick.
- `[[agentsop-repo-state-gating]]` — owns the coding-agent applicability gate (existing
  repo vs greenfield). This skill gates through it before any Aider/Cline/Cursor
  pick.

## Source material

Synthesized from the R5 ecosystem-context sections of:
LangGraph, LlamaIndex, DSPy, CrewAI, vLLM, Aider, Dify SOPs — plus the
"where the 7 SOPs disagree" section of `phase-b-coder-agent-skill-inventory.md`
(capability **A7**, the project-kickoff framework-fit check, `core` 5/7).

Version 0.1.0.
