# R1. Source Evidence — query-routing claims resolved to source SKILLs

Every load-bearing claim in `SKILL.md` resolves here to a line in one of the
three source skills. This is an ENHANCE overlay; no new external APIs are
introduced beyond what the source skills already document. Source skills live at
`/Users/5imp1ex/Desktop/Skill-Workplace/output/{name}-sop-skill/SKILL.md`.

Citation tags in SKILL.md: `[[llamaindex]]`, `[[agentsop-dify]]`, `[[agentsop-langgraph]]`.

---

## Principle 1 — One retriever cannot serve all query types

- **Claim**: `SummaryIndex` = small fan-out synthesis; `VectorStoreIndex` =
  top-k semantic lookup; they are not interchangeable.
- **Source**: `[[llamaindex]]` Principle 3 "Indices are not interchangeable"
  table — `VectorStoreIndex` "semantic Q&A over chunks; ~90% of RAG cases";
  `SummaryIndex` "Summarize this whole doc — small, fan-out synthesis".
- **Claim**: text-to-SQL answers aggregate/compute queries no chunk contains.
- **Source**: `[[llamaindex]]` Boundary B2 "Pure structured/tabular data →
  DuckDB/SQL/BI. (LlamaIndex only when NL2SQL+RAG hybrid.)"; `[[agentsop-langgraph]]`
  Dilemma 1 / OP-9 use "text-to-SQL agent" as the running example.
- **Claim**: a `RouterQueryEngine` over per-task indices is often the correct
  top-level shape, not a single monolithic `VectorStoreIndex`.
- **Source**: `[[llamaindex]]` Principle 3 final paragraph (verbatim).

## Principle 2 — Route first, retrieve second

- **Claim**: routing is a classification step that runs before retrieval and
  emits a destination, not an answer; bounds latency/cost.
- **Source**: `[[agentsop-langgraph]]` Principle 3 "Graph topology is just routing logic
  over state. Edges are … conditional (a function reads state and picks a next
  node)"; `[[llamaindex]]` Stage 4 "Compose for query heterogeneity" (route to a
  primitive per query shape); `[[agentsop-dify]]` §2.4 Question Classifier is an LLM node
  feeding branches.

## Principle 3 — A router is only as good as its destinations' descriptions

- **Claim**: the `QueryEngineTool.description` is "the only signal the
  router/agent sees".
- **Source**: `[[llamaindex]]` Dilemma 3 step 5 (verbatim) + OP-06 "Carefully
  author each `QueryEngineTool.description`" + Stage 6 "tune the `description=`
  carefully — it is the only signal the router/agent reads".
- **Claim**: a misroute is usually a bad description, fix it before swapping the
  router.
- **Source**: derived from `[[llamaindex]]` Dilemma 3 (fix supervisor before
  switching paradigms) and `[[agentsop-langgraph]]` OP-9 / Case 1 ("hitting the limit
  indicates an underlying design flaw" — fix the logic, not the knob).

---

## §3 SOP — router families

- **Keyword / rule router**: `[[agentsop-dify]]` §2.4 IF/ELSE node (control flow over the
  query); `[[agentsop-langgraph]]` OP-? conditional edge as a pure predicate
  (`add_conditional_edges`, Principle 3 "a function reads state and picks").
- **Embedding / semantic router**: `[[llamaindex]]` selector families — the
  source lists LLM and Pydantic selectors under `RouterQueryEngine`/router docs
  (OP-06); embedding selector is the documented `EmbeddingSingleSelector`
  member of that family.
- **LLM / selector router**: `[[llamaindex]]` OP-06 RouteByQueryType "a
  `RouterQueryEngine` with LLM or Pydantic selector"; `[[agentsop-dify]]` §2.4 Question
  Classifier node (LLM); `[[agentsop-langgraph]]` Principle 3 conditional edge function
  may call an LLM.

## §3 Stage 4 — fallback / confidence threshold

- **Claim**: every router needs a default for the unrouteable query; below
  threshold → fallback, not best-guess.
- **Source**: `[[agentsop-dify]]` Question Classifier has an inherent "other/else" class
  and §2.4 IF/ELSE has an ELSE branch; `[[agentsop-langgraph]]` conditional-edge mapping
  can include a default branch (topology over state, Principle 3).
- **Claim**: log every routing decision so misroutes are observable.
- **Source**: `[[agentsop-dify]]` Phase 7 "tracking 7 类 trace: Workflows / Messages / …
  Dataset Retrieval / Tools"; `[[agentsop-langgraph]]` OP-8 streaming + Step 7 "Wire
  LangSmith from day one".

---

## §5 Dilemmas

### Dilemma 1 (misroute: classifier vs fallback)
- **Diagnose-before-fix + fix-descriptions-first logic**: `[[llamaindex]]`
  Dilemma 3 (anchor on constraints, fix the existing pattern before switching);
  `[[agentsop-langgraph]]` Case 1 ("Reject the temptation to just raise recursion_limit
  — that masks the bug"; fix the logic).

### Dilemma 2 (LLM latency vs cheap keyword)
- **Tiering / "cheapest sufficient" ladder**: `[[llamaindex]]` Stage 3
  "prompts first, reranking last … exhaust cheap knobs first" and Step-2/3
  "promote upward as needed"; `[[agentsop-langgraph]]` §生态对照 "Pick the smallest one
  that fits the requirements; promote upward as needed".
- **Latency boundaries**: `[[agentsop-langgraph]]` Boundaries "Latency budget < 200ms per
  call: checkpoint serialisation adds overhead"; `[[agentsop-dify]]` when_not_to_use
  "sub-second latency / real-time streaming pipelines — workflow engine overhead
  dominates" + §6.2 "每节点单独 DB query — 长 workflow 累积延迟".

### Dilemma 3 (single vs multi-select)
- **Don't fan out for fixed-cardinality work**: `[[agentsop-langgraph]]` anti-pattern
  "Don't fan out with `Send` for fixed-cardinality work. … Reserve `Send` for
  genuinely runtime-variable workloads"; OP-4 `Send` dynamic fan-out.
- **Multi-selector exists**: `[[llamaindex]]` selector family includes
  `LLMMultiSelector` (router docs referenced in OP-06).

---

## §7 Cross-framework table — verbatim anchors

- **LlamaIndex** `RouterQueryEngine` + `LLMSingleSelector` /
  `EmbeddingSingleSelector` / `LLMMultiSelector` / `PydanticSingleSelector` +
  `SelectorPromptTemplate`: `[[llamaindex]]` OP-06, Stage 4, Principle 3,
  frontmatter primitive list (`RouterQueryEngine`).
- **Dify** Question Classifier / Parameter Extractor / IF-ELSE nodes:
  `[[agentsop-dify]]` §2.4 Node taxonomy table (LLM row: "LLM, Question Classifier,
  Parameter Extractor"; 逻辑 row: "IF/ELSE").
- **LangGraph** `add_conditional_edges`, conditional edge as router, `Send`
  fan-out: `[[agentsop-langgraph]]` Principle 3, OP-4 (`Send`), Case/anti-pattern on
  `Send`.

---

## Boundary vs multi-tenant-rag (B2 / A6)

- **Claim**: routing by tenant/ACL is filtering, not query routing.
- **Source**: companion skill `d-multi-tenant-rag-skill/SKILL.md` — its entire
  thesis is "filter at the vector store query" keyed on `tenant_id`. That is a
  *who-asks* split; this skill is a *what-is-asked* split. They compose.

---

## Provenance note

All three source SKILLs were read in full on 2026-05-20. No claim in this
overlay asserts an API or behavior absent from those sources. Where SKILL.md
names a specific selector class (e.g. `EmbeddingSingleSelector`,
`LLMMultiSelector`), it is a member of the LlamaIndex selector family the source
references under "LLM or Pydantic selector" + router docs; re-verify exact class
names against current LlamaIndex docs before pasting into code (May 2026).
