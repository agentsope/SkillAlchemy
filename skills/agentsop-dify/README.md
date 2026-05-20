# dify-sop-skill

SOP skill distilling **Dify** — the open-source LLM application platform — into actionable decision patterns for coder agents.

## What's inside

| File | Purpose |
|---|---|
| `SKILL.md` | The main skill: 7 sections (activation, mental model, SOP, operation model, dilemmas, anti-patterns, ecosystem) |
| `references/R1-architecture.md` | 5-layer stack, app types, graph engine, plugins, RAG |
| `references/R2-sop-workflow.md` | Phase-by-phase build: idea → deploy → publish → monitor → iterate |
| `references/R3-dilemma-cases.md` | 6 real dilemma cases with decision matrices |
| `references/R4-anti-patterns.md` | Anti-pattern catalog, performance boundaries, when NOT to use |
| `references/R5-ecosystem-context.md` | vs Flowise/LangFlow/Coze/RAGFlow/n8n/LangGraph/LlamaIndex/CrewAI |
| `intermediate/operation_candidates.json` | Structured operation/decision candidates extracted during research |

## Quick activation guide

Use this skill when:
- Building LLM apps (chatbot / agent / workflow / RAG) and want to ship in days
- Team has mixed roles (PM + ops + engineers) needing a shared visual artifact
- Need self-hostable LLM platform with multi-tenant workspaces
- Want one box for UI + API + RAG + monitoring + auth

Skip this skill when:
- Pure engineering team already deep in LangChain/LangGraph
- Need >10 QPS sustained per pod
- Need pause-and-wait-for-user (LangGraph instead)
- Doing model training (Axolotl/LLaMA-Factory instead)
- Bottleneck is expressive depth, not scaffolding

## Domain

LLM application platform — sits between code frameworks (LangChain, LangGraph) and managed bots (Coze). Visual-first with code escape hatches.

## Versions covered

Dify v1.0 (plugin system) through v1.14 (May 2026 stable).
