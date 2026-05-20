# query-routing skill

Cross-framework **enhancement overlay** for **query-type routing** — sending a
query to the right index / tool / engine *before* retrieving, not after. A
summary query goes to a summary index; a fact lookup goes to a vector index; a
SQL-able ("how many…") query goes to a text-to-SQL engine.

This is the **C8 gap skill** in the Phase-D enhance pass. Routing exists inside
several per-framework skills (LlamaIndex `RouterQueryEngine`, Dify Question
Classifier, LangGraph conditional edges) but there was no standalone skill
teaching the *cross-framework routing discipline*. This is that skill.

## Scope

- **Activation**: a single answering surface fronts ≥2 handlers and inbound
  queries differ in *kind* (lookup vs summarize vs compute vs compare).
- **Core insight**: *one retriever cannot serve all query types; route first,
  retrieve second.*
- **Date stamp**: May 2026. Re-verify selector APIs each quarter.

## Layout

```
d-query-routing-skill/
├── SKILL.md                          # 7-section SOP (activation → cross-framework table)
├── README.md                         # this file
├── references/
│   └── R1-source-evidence.md         # every cited claim resolved to a source SKILL line
└── intermediate/
    └── operation_candidates.json     # raw trigger/action/output/evidence operations
```

## Key claim

> A retriever is shaped by the query type it was built for. A `SummaryIndex`, a
> `VectorStoreIndex`, and a text-to-SQL engine are not interchangeable — so
> classify the query and route to the structurally-correct handler, then
> retrieve. A router with no fallback is the most common failure.

The skill encodes the three router families (keyword/rule, embedding/semantic,
LLM/selector), the confidence-threshold + fallback discipline, 8 operations,
3 dilemma cases (misroute: classifier vs fallback; LLM latency vs cheap keyword;
single vs multi-select), 9 anti-patterns, and the cross-framework mapping
(LlamaIndex / Dify / LangGraph).

## ENHANCE overlay

This skill is an **overlay**, not a replacement. For the per-framework API it
cross-links the base skills inline as `[[name]]`:

- `[[llamaindex]]` — `RouterQueryEngine`, selector families, `SelectorPromptTemplate`.
- `[[agentsop-dify]]` — Question Classifier node, IF/ELSE node.
- `[[agentsop-langgraph]]` — conditional edges (`add_conditional_edges`), `Send` fan-out.

Activate this skill for the *routing decision*; descend to the base skill for
the API surface.

## Method

Mined directly from the three source SKILLs under
`/Users/5imp1ex/Desktop/Skill-Workplace/output/`:
`llamaindex-sop-skill`, `dify-sop-skill`, `langgraph-sop-skill`. Every
load-bearing claim carries an inline `[[source]]` tag and resolves in
`references/R1-source-evidence.md`. No fabricated APIs.

## Position in the Phase-D inventory

- **Sibling overlays**: `d-multi-tenant-rag-skill` (filter by *who*, not *what*),
  `d-llm-engine-selection-skill`, `d-map-reduce-fanout-skill`,
  `d-state-reducer-skill`.
- **Boundary vs `d-multi-tenant-rag-skill`**: that skill routes by tenant/ACL;
  this skill routes by query *kind*. They compose (route by kind, filter by tenant).
