# R1 — Source Evidence

Traceable evidence behind every claim in `SKILL.md`. Two source classes: (1) the Phase A SOP skills
that reference observability, (2) the per-backend skill frontmatter that defines the choices.

## A. Phase A SOPs referencing observability

### A1. langgraph-sop — the AP-15 anchor
File: `/Users/5imp1ex/Desktop/Skill-Workplace/output/langgraph-sop-skill/references/R4-anti-patterns.md:103`

> **AP-15 · Don't skip LangSmith in production**
> "Replaying a checkpoint locally only goes so far; production needs the trace UI
> ([swarnendu.de/blog/langgraph-best-practices](https://www.swarnendu.de/blog/langgraph-best-practices/)).
> The same team builds both — integration is first-class."

Used for: §6 headline anti-pattern (AP-15), §4 LangSmith row ("same team builds both" → first-class
integration), Case A resolution, §1 "before first deploy" trigger.

### A2. llamaindex-sop — backend pairing + what-to-trace
File: `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`

- L406: "Most production teams converge on: **LlamaIndex for retrieval & ingestion; LangGraph (or
  LlamaIndex Workflows) for orchestration; LangSmith / Phoenix for observability**."
- L159: "Tracing/observability captures `query + retrieved_nodes + scores + index_id + LLM prompt`
  for every failure."
- L126: "Most RAG failures in production trace to weak retrieval or sloppy ingestion — not the LLM.
  The eval loop is what surfaces them."

Used for: §4 decision table (LangSmith vs Phoenix as the canonical pair), OP-5 (minimum trace
payload for RAG), Stage 4 / OP-4 (eval loop surfaces failures).

### A3. dspy-sop — MLflow + LangFuse-style traces
File: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`

- L99: "**Deploy** via FastAPI (`dspy.asyncify`) or MLflow (`mlflow.dspy.log_model`)."
- L263: "**You need rich agent observability with LangFuse-style traces today.** Native integration
  is limited; bolt-on via MLflow tracing works but is not first-class."

Used for: §4 MLflow row (`mlflow.dspy.autolog` / `log_model` path for DSPy/ML-shops), §4 Langfuse
row ("LangFuse-style traces" as the self-host LLM-native option, "bolt-on" framing).

### A4. prompt-history-inspect (neighbor overlay) — the reactive counterpart
File: `/Users/5imp1ex/Desktop/Skill-Workplace/output/d-prompt-history-inspect-skill/...`

- op-001 limitation: "Layer with `mlflow.dspy.autolog` for full pipeline."
- op-009 (`production_inspect`): "framework: langsmith | langfuse | phoenix | mlflow … Open the
  trace UI for the configured platform."
- crewai op-004 limitation: "production needs Langtrace/OpenLIT/AgentOps/MLflow autolog in addition."

Used for: §1 relationship to [[agentsop-prompt-history-inspect]] (reactive single-prompt vs proactive
persistent), the four-backend choice set, OP-6 handoff boundary.

## B. Per-backend skill frontmatter (the choices)

### B1. LangSmith — `~/.claude/skills/langsmith/SKILL.md`
> name: langsmith-observability — "LLM observability platform for tracing, evaluation, and
> monitoring." Integrations: "OpenAI, Anthropic, LangChain, LlamaIndex." Alternatives noted:
> "MLflow: general ML lifecycle, model registry focus."

Used for: §4 LangSmith row (LangChain/LlamaIndex first-class), §7 table, OP-2 env-var turn-on.

### B2. Phoenix — `~/.claude/skills/phoenix/SKILL.md`
> name: phoenix-observability — "Open-source AI observability platform … OpenTelemetry-based trace
> collection for any LLM framework … Self-hosted with PostgreSQL or SQLite … Self-hosted
> observability without vendor lock-in." Alternatives: "LangSmith: Managed platform with
> LangChain-first integration."

Used for: §4 Phoenix row (OSS / OTel / no lock-in / self-host), §7 table, OP-2 `px.launch_app()` +
`register(auto_instrument=True)`, Case A (OSS vs SaaS).

### B3. MLflow — `~/.claude/skills/mlflow/SKILL.md`
> name: mlflow — "framework-agnostic ML lifecycle platform … Track ML experiments … Manage model
> registry … Integrate with any ML framework." 20,000+ orgs, Apache 2.0. `mlflow ui` at :5000.

Used for: §4 MLflow row (ML-shops already on MLflow, one pane of glass), §7 table, OP-2
`mlflow.<framework>.autolog()`, OP-3 verify at :5000.

## C. Derived / synthesized claims (no single source line)

- **One-line autolog exists for every backend** — synthesized from B1–B3 quick-start sections plus
  dspy-sop `mlflow.dspy.log_model`; the "choosing is harder than wiring" framing (§2) is the
  overlay's own thesis built on these.
- **Trace-volume-at-scale / Replit case (Case B)** — generalized from the high-volume agent-product
  pattern; the *mitigations* (sampling, self-host break-even, curated eval datasets) are standard
  observability practice, presented as a decision rather than cited to one document.
- **OpenTelemetry GenAI as portability layer (§7)** — Phoenix frontmatter establishes OTel basis;
  the "escape hatch keeps any choice reversible" framing is overlay synthesis.

## D. Backend choice set (final)

LangSmith (stack-coupled SaaS) · Phoenix (OSS/OTel/self-host) · MLflow (ML-shop hub) ·
Langfuse (self-host LLM-native) · OpenTelemetry GenAI (portability layer). Drawn from A1–A4 + B1–B3.
