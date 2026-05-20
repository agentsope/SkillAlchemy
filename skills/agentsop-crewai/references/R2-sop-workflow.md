# R2 — SOP Workflow (Phases 0→4)

## Phase 0 — Should you even use CrewAI?

Two filter questions, both must pass:

1. **Multi-role check**: Does the task genuinely need ≥2 distinct *expert viewpoints* collaborating?
   - "Research then write" — yes
   - "Extract entity from PDF" — no, single agent
   - "Loop over rows of a CSV and classify" — no, batch over single agent
2. **Control-flow check**: Is the flow linear or lightly branching (no cycles, no human-in-the-loop interrupts)?
   - Yes → CrewAI is a fit
   - No → use LangGraph; OR use CrewAI **Flow** as the spine with small Crews per step

If either filter fails, **do not use Crew**. Production data: single-agent fits ~80% of tasks  [daily.dev/blog/ai-agents-guide-for-developers-langchain-crewai].

## Phase 1 — Agent Design

### 1.1 Split principles
- **One verb per agent**: research / analyze / write / review / decide
- Avoid generalists (single agent doing multiple verbs)
- **2–5 agents is the sweet spot**. 7+ → coordination failures dominate

### 1.2 The role/goal/backstory triplet — concrete rules

**role** — high-signal title
- Bad: "Assistant"
- Good: "Senior AI Research Analyst", "Lead Editor", "Financial Compliance Officer"
- Include seniority signals ("Senior", "Lead", "Principal") — they elevate priors

**goal** — measurable objective with template vars
- Bad: "Help with research"
- Good: "Surface 3 emerging trends in {topic} from 2025–2026 with ≥2 verifiable citations per trend"
- Include `{template_vars}` substituted via `kickoff(inputs={...})`

**backstory** — judgment injection
- Bad: "You are a helpful AI assistant."
- Good: "You're a meticulous researcher with a decade at frontier AI labs. You distrust hype and demand primary sources. You refuse to cite blog posts when papers exist."
- 2–4 sentences. Inject: experience, biases, taboos, preferred sources

### 1.3 Default safety params
```python
agent = Agent(
    role=..., goal=..., backstory=...,
    allow_delegation=False,   # default False; only turn on for manager
    max_iter=8,               # explicit, do not rely on default 20-25
    max_rpm=30,               # set globally on Crew too
    verbose=True,             # dev essential
    tools=[...],              # ONLY tools relevant to this role
)
```

### 1.4 YAML-first for production
Use `@CrewBase` + `config/agents.yaml` + `config/tasks.yaml`. Benefits:
- Non-engineers can iterate prompts
- Version-controllable text diffs
- `{template_vars}` substituted at `kickoff(inputs={...})`

[docs.crewai.com YAML Configuration]

## Phase 2 — Task Design

### 2.1 description = "what" not "how"
- `description="Analyze the search results for {topic} and identify 3 emerging trends"` ✓
- `description="First call the search tool, then for each result extract …"` ✗ (this is procedural code, defeats agency)

### 2.2 expected_output is the contract
- This is your **test assertion**. Write it as if a downstream parser will check it.
- Example: `"A markdown report with 3 H2 sections, each containing: trend name, ≤200-word summary, ≥2 citations as [title](url)"`
- For programmatic chains, attach `output_pydantic=MyModel`

### 2.3 context — explicit > implicit
- Implicit auto-relay is convenient at first, lethal at scale (prompt bloat)
- Always declare: `context=[research_task, fact_check_task]`
- For long pipelines, the dependency graph becomes self-documenting

### 2.4 Async & callbacks
- `async_execution=True` for parallel tasks; later task references via `context=[]`
- `callback=fn` for side effects (notify, save, eval-log)

[docs.crewai.com/en/concepts/tasks]

## Phase 3 — Assemble Crew

```python
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analyze_task, write_task],
    process=Process.sequential,    # default; read DC-2 before changing
    memory=False,                  # default off; see DC-4
    verbose=True,
    max_rpm=30,
    planning=False,                # 0.80+ experimental, test before prod
    step_callback=my_observer,     # log every step
)
result = crew.kickoff(inputs={"topic": "agentic RAG"})
```

### 3.1 If hierarchical
- Never use bare `manager_llm="gpt-4o"` for production routing (see DC-2)
- Always provide `manager_agent=Agent(role="Manager", backstory="<detailed routing logic>")`
- Pin manager to strong model (gpt-4o or Claude 3.5 Sonnet); mini models fail at delegation reasoning  [markaicode.com/crewai-hierarchical-process]

### 3.2 If Flow
- Subclass `Flow[StateModel]`
- Decorate entry with `@start()`
- Chain via `@listen(prior_method)`
- Inside steps, call `MyCrew().crew().kickoff(inputs=…)`

## Phase 4 — Observability & Convergence

### 4.1 Mandatory observability
CrewAI's internal logging is thin. **Before any production**:
- `mlflow.crewai.autolog()` — easiest local
- Maxim / Langfuse / Datadog — production-grade
- `step_callback` for custom action logs
[docs.crewai.com/en/observability/overview]

### 4.2 Cost/iteration caps
- `max_iter` per agent (default 20-25 is too high for prod)
- `max_rpm` on Crew
- **Outer timeout** wrapping `kickoff()` — CrewAI does not enforce wall-clock
- Hierarchical: budget 1.3–1.5× sequential token spend

### 4.3 Eval-driven iteration
- Every failed kickoff → eval case
- LLM-as-judge to check `expected_output` contracts
- Track regression as backstories evolve
