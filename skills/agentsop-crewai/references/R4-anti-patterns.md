# R4 — Anti-Patterns & Boundaries

## 1. The Five Big Anti-Patterns

### AP-1 — Agent Inflation (>5 agents)
- **Symptom**: Coordination failures, token costs balloon, debugging time goes nonlinear
- **Why it happens**: "More agents = smarter system" intuition; resume-driven design
- **Fix**: Collapse near-duplicate roles. If you can't articulate the *unique* judgment of each agent in one sentence, merge them. Beyond 7 agents, switch to Flow for structural backbone.
- Reference: [medium.com/@armankamran/anti-patterns-in-multi-agent-gen-ai-solutions]

### AP-2 — Anemic Backstory
- **Symptom**: Bland output, no editorial voice, agents feel interchangeable
- **Why it happens**: Treating backstory as cosmetic, copy-paste "You are a helpful assistant"
- **Fix**: Inject experience ("a decade at frontier AI labs"), biases ("distrusts hype"), taboos ("refuses to cite blog posts when papers exist"). 2-4 sentences minimum.
- Reference: [docs.crewai.com/en/concepts/agents]

### AP-3 — Default Hierarchical Manager (`manager_llm=`)
- **Symptom**: Manager executes all tasks instead of routing; last task's output overwrites everything
- **Why it happens**: Following the simplest example in docs; assuming the framework handles delegation
- **Fix**: Always supply a custom `manager_agent` with detailed routing backstory. Or — better — use Flow with explicit `@listen` branches.
- Reference: [towardsdatascience.com Manager-Worker fails], [github.com/crewAIInc/crewAI/discussions/1220]

### AP-4 — Global `allow_delegation=True`
- **Symptom**: Infinite delegation ping-pong, OOM, ballooning token cost, silent retries
- **Why it happens**: Copying examples from blog posts that mass-enable delegation; not realizing schema mismatch triggers silent retry loops
- **Fix**: Default OFF. Only the manager_agent gets delegation. Wrap kickoff in outer timeout.
- Reference: [github.com/crewAIInc/crewAI/issues/330], [azguards.com delegation-ping-pong]

### AP-5 — No Observability in Production
- **Symptom**: Bug reports without trace; cannot reproduce; "agent did something weird"
- **Why it happens**: CrewAI's internal logging is sparse; print statements inside Task don't surface cleanly
- **Fix**: `mlflow.crewai.autolog()` minimum. Production: Maxim / Langfuse / Datadog. Always pass `step_callback=`.
- Reference: [docs.crewai.com/en/observability/overview]

## 2. Other common mistakes

| Mistake | Sign | Fix |
|---|---|---|
| Procedural `description` ("first call tool X, then Y") | Treating Task like a function | Write *what*, let agent decide *how* |
| Missing `expected_output` | Unstable convergence | Treat it as test assertion |
| Implicit auto-context | Prompt size explodes after 3+ tasks | `context=[...]` explicit always |
| Memory enabled by default | Token spend 2× + flaky recalls | `memory=False` until you have evidence you need it |
| Mini model for manager | Hierarchical routing fails | gpt-4o or Claude 3.5 Sonnet minimum |
| `print()` for debugging | Output never appears | Use `step_callback` or external trace tool |
| YAML template var typo | Literal `{topic}` in prompts | Always pass via `kickoff(inputs={...})` |

## 3. When NOT to use CrewAI

| Need | Better fit | Why |
|---|---|---|
| Single agent + tool use | Plain SDK (Anthropic/OpenAI) + Instructor/Outlines | No orchestration overhead |
| State machine, cycles, interrupts, replays | **LangGraph** | Graph-first, durable execution |
| Free conversation, group debate | **AutoGen** (but in maintenance — consider LangGraph + custom) | Chat-as-primitive |
| Lightweight handoff | OpenAI Swarm / Anthropic patterns | Even lower overhead |
| Data-heavy RAG (300+ connectors) | **LlamaIndex** | Data-centric primitives |
| Sub-second latency | None of the multi-agent frameworks | Multi-agent handshakes always add 100s of ms |
| Deterministic routing with strict SLA | **LangGraph** or plain code | CrewAI hierarchical is non-deterministic |
| Production at scale with high reliability | **LangGraph** | Stated as "production leader" in 2025-2026 comparisons  [datacamp, latenode] |

## 4. CrewAI's structural caveats (acknowledge openly)

1. **Hierarchical mode** has known correctness issues with default manager — even maintainers point users to Flow for routing
2. **Observability** is weak by default — must bolt on
3. **State management** shallower than LangGraph
4. **Eval tooling** less mature than LangSmith integration
5. **Logging from inside Task** is unreliable

## 5. When CrewAI IS the right choice (positive boundaries)

- ✅ 2–5 distinct expert roles with clear handoffs
- ✅ Content pipelines (research → write → edit → publish)
- ✅ Prototyping speed matters; PM/ops need to read prompts
- ✅ Flows + Crews hybrid where you want both spine and agency
- ✅ Teams already using YAML-driven prompt iteration
- ✅ Workflows where "team metaphor" aligns with how stakeholders think
