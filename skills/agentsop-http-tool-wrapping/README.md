# http-tool-wrapping

SOP skill for **wrapping a REST / GraphQL / RPC API as a tool an LLM agent can
call**. Phase D coder-agent skill (high-frequency: ~80% of agent tools in
production are HTTP wrappers, and no unified skill existed for the pattern).

## Core thesis

> **The tool surface is an LM-friendly subset of the API surface — one tool per
> intent, not one per endpoint.**

A REST API is built for programmers who read docs and compose calls. An agent
tool is built for a language model that sees only a name, a description, and a
JSON schema. The surface must be *re-cut* for that audience, not mirrored.

## What's here

| File | Purpose |
|---|---|
| `SKILL.md` | The skill. 7 sections: activation, mental model, SOP, operation models (OP-1…10), dilemma cases (DC-1…3), anti-patterns, cross-framework table. |
| `references/R1-source-evidence.md` | Every inline citation with quoted evidence, grouped by topic. |
| `references/R2-pattern-library.md` | Copy-pasteable code shapes: typed schema, retry+timeout client, pagination, error contract, auth injection, framework-binding snippets. |
| `intermediate/operation_candidates.json` | Structured capture of the 10 operations, anti-patterns, dilemma cases, and key quotes used to build `SKILL.md`. |

## How to use

1. **Triage** the API to ≤10 intent-bearing operations (SKILL §3 Step 1 / OP-1).
2. **Name** each tool by intent, define a **typed flattened schema** with
   model-facing field descriptions (Steps 2–3).
3. Build the wrapper's robustness layer: **error translation, response shaping,
   pagination, auth injection, retry/timeout** (Steps 4–6, OP-5…8).
4. For mutating tools, add an **idempotency key** and defer the full protocol to
   the sibling **`llm-tool-idempotency`** skill (Step 7 / OP-9).
5. **Bind** the one Pydantic schema into your framework — OpenAI / Anthropic /
   MCP / LangChain / CrewAI all consume `model_json_schema()` (OP-10, §7).

## Relationship to sibling skills

- `langgraph-sop`, `crewai-sop` — decide *whether/where* tools run and how the
  graph/crew orchestrates them. This skill decides *what shape each tool takes*.
- `llm-tool-idempotency` — owns side-effect safety (exactly-once, dedup).
  This skill only flags the hook on mutating tools (OP-9).
- Bounded-loop skill — owns agent loop bounding; referenced for paginated /
  polling tools (OP-6, DC-3).

## Source material

Built from `langgraph-sop` (tool definition + binding) and `crewai-sop`
(per-agent tool scoping), plus official docs: OpenAI function calling, Anthropic
`tool_use`, MCP / FastMCP, LangChain tools, CrewAI tools — and external evidence
on rate limits, retries, pagination, idempotency, and tool-schema design (see
`R1`).

`name: http-tool-wrapping` · `version: 0.1.0`
