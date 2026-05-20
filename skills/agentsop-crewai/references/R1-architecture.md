# R1 — CrewAI Architecture & Mental Model

## 1. The four primitives

CrewAI's entire abstraction surface is four concepts. Mastering the boundaries between them is 80% of the skill.

```
Agent  →  Task  →  Crew  →  Process
                            (+ Flow for event-driven orchestration)
```

### 1.1 Agent — "who"
- **role** (required): noun-phrase title. e.g., "Senior AI Research Analyst"
- **goal** (required): individual objective with `{template_vars}` and verifiable criteria
- **backstory** (required): persona/experience text. Shapes judgment, tone, biases.
- `allow_delegation` (default `False` post-2024): whether this agent can hand work to others
- `max_iter` (default 20–25): hard ceiling on agent self-loop steps
- `max_rpm`: rate limit guard
- `memory`: per-agent memory scope
- `verbose`: log every step (dev essential)
- `tools`: list of BaseTool / @tool functions
- `respect_context_window` (default True): auto-summarize on overflow
- `reasoning`, `inject_date`: newer flags

> "Role, goal, and backstory are required and shape the agent's behavior."  [docs.crewai.com/en/concepts/agents]

### 1.2 Task — "what"
- **description** (required): what to do (NOT how)
- **expected_output** (required): the "test assertion" — agent stops when this is met
- **agent**: who runs it (optional in hierarchical mode — manager assigns)
- **context**: explicit list of prior tasks whose outputs feed in
- `output_pydantic` / `output_json`: structured output enforcement
- `async_execution`: run in parallel
- `callback`: post-completion hook
- `output_file`: persist to disk

> "In crewAI, the output of one task is automatically relayed into the next one, but you can specifically define what tasks' output… should be used as context."  [docs.crewai.com/en/concepts/tasks]

**Subtle gotcha**: the implicit auto-relay means a 5-task pipeline by default puts task[0]'s output in task[4]'s prompt. For non-trivial flows, **always specify `context=[...]` explicitly**.

### 1.3 Crew — "how to assemble"
- `agents`: list of Agent
- `tasks`: list of Task
- `process`: `Process.sequential` (default) or `Process.hierarchical`
- `manager_llm` or `manager_agent` (only when hierarchical)
- `memory`: enable framework memory subsystem (off by default)
- `verbose`, `max_rpm`, `embedder`, `planning`, `step_callback`

### 1.4 Process — "control flow"

| Mode | Routing | Token cost | Reliability |
|---|---|---|---|
| `Process.sequential` | Static list order | Baseline | Highest |
| `Process.hierarchical` | LLM manager assigns at runtime | +30–50% | Has known failure modes |

> "In a hierarchical process, a manager agent allocates tasks among crew members based on their roles and capabilities, and the manager evaluates outcomes."  [docs.crewai.com hierarchical-process]

### 1.5 Flow — the event-driven layer (added 2025)
- Class with `@start()`, `@listen(prior_method)` decorators
- State via `self.state` (unstructured) or Pydantic BaseModel (structured)
- Each step can be plain Python, single LLM call, or `crew.kickoff()`
- Provides the deterministic spine that Crews (autonomous, role-based) lack

> "Crews provide autonomous agent collaboration; Flows offer precise, event-driven control."  [docs.crewai.com/en/concepts/flows]

## 2. The "why role-based?" question

João Moura's design bet: **LLMs perform better when role-playing**. Three reasons surfacing in interviews and docs:
1. Role-playing recruits coherent priors (a "senior researcher" persona triggers more rigorous chain-of-thought than "an AI assistant")
2. Backstory injects judgment biases the LLM can't infer from goal alone — e.g., "distrusts hype" → fewer marketing fluff outputs
3. Naming roles makes the system human-debuggable; a PM can read `crew.yaml` and discuss agents like teammates

> "An agent needs agency, otherwise it's just another script."  [softwareengineeringdaily.com/2025/06/03/crew-ai-with-joao-moura]

This is also why hierarchical mode is philosophically consistent — letting an LLM manager decide routing IS the agency thesis. The practical issues (DC-2) come from current LLM reliability, not the philosophy.

## 3. No-LangChain stance
CrewAI is explicitly **built from scratch, independent of LangChain**. Practical implications:
- Faster import, smaller dep tree
- Fewer prebuilt integrations (compensate via crewai-tools repo)
- Some pydantic v1/v2 friction when mixing langchain tools
- Internal logging is sparse (must add MLflow / Maxim / Datadog for production)

[github.com/crewAIInc/crewAI README, README quote: "completely independent of LangChain or other agent frameworks"]

## 4. Version snapshot (capture date 2026-05)
- Current: 1.14.5 (May 18, 2026)
- 51.7k GitHub stars, 7.2k forks
- Flows feature stabilized 2025
- Memory system unified into single `Memory` class with scope-based hierarchy (replaces prior short/long/entity/contextual split in API)
