# R3 — Dilemma Cases (Decision Rules)

Five real dilemmas drawn from CrewAI GitHub Issues, Community Forum, and engineering blog post-mortems. Each has a decision rule the agent can apply.

---

## DC-1 — Agent stuck looping: fix prompt or split the agent?

### Scenario
Writer agent self-critiques 5 iterations, output still poor. Pass-through reviewers find inconsistency between sections.

### Forces in tension
- **Refactor prompt** (cheap, in-place)
- **Add a second agent** (more structure, +50% token)

### Diagnostic
1. Run 5 failed cases. Categorize failure mode:
   - **Style inconsistent** → fix backstory (single-agent problem)
   - **Missing checklist items, factual slips, format violations** → split agent (need a dedicated reviewer with structured rubric)
2. If iteration count consistently >3 to converge → split signal

### Decision rule
> **Default = split.** When unsure, split. CrewAI's edge is single-responsibility roles. The cost of an extra agent (1 LLM call) is far less than the debugging cost of a confused multi-responsibility agent.

### Counter-evidence
> "Single-agent is right for approximately 80% of cases; the trap is reaching for multi-agent because it sounds more capable. But once you've committed to multi-agent, the next trap is putting too much in one agent."  [daily.dev]

→ The 80%/20% rule applies at task-level. Once you're in the multi-agent regime, lean toward more splits, not fewer.

### Sources
- [docs.crewai.com/en/concepts/agents]
- [medium.com/@armankamran/anti-patterns-in-multi-agent-gen-ai-solutions]

---

## DC-2 — Sequential vs Hierarchical: when is manager overhead worth it?

### Scenario
5 agents, task order mostly fixed, occasionally need to skip a task based on upstream output.

### The trap
Intuition says "hierarchical should auto-route". **Empirically, default hierarchical executes all tasks anyway** — even when triage clearly indicates skip. Documented failure case from Towards Data Science  [towardsdatascience.com Manager-Worker fails]:

```
Query: "Why is my laptop overheating?" (technical-only)
Expected: triage → technical_support → done
Actual hierarchical: triage → technical → billing → ... → last task's
                     output OVERWRITES the technical answer
```

Root cause: CrewAI's hierarchical scheduler is not truly conditional — the manager queues all tasks and the last completion wins.

### Four paths

| Option | Effort | Reliability | Token cost |
|---|---|---|---|
| A. Sequential, run all tasks | Low | High | Baseline |
| B. Hierarchical + default `manager_llm` | Low | **LOW (broken)** | +30-50% |
| C. Hierarchical + custom `manager_agent` with explicit conditional backstory | Medium | Medium | +30-50% |
| D. CrewAI Flow with `@listen` conditional routing | Medium | High | Near baseline |

### Decision rule
1. Can routing logic be expressed in 5 lines of Python? → **D (Flow)**
2. Routing genuinely needs LLM semantic judgment? → **C** (never B). Use Claude 3.5 Sonnet / GPT-4o for manager, not mini.
3. Unsure → **A**. Measure perf; if acceptable, stop optimizing.

### Red line
**Never** ship production routing on default `manager_llm`. Even the CrewAI team acknowledges hierarchical mode's limitations in Discussion #1220.

### Sources
- [docs.crewai.com/en/learn/hierarchical-process]
- [github.com/crewAIInc/crewAI/discussions/1220]
- [towardsdatascience.com/why-crewais-manager-worker-architecture-fails-and-how-to-fix-it/]
- [community.crewai.com/t/5710] (shopping chatbot case where MaxMoura recommended Flow over hierarchical)

---

## DC-3 — Tools: share across agents or scope per-role?

### Scenario
Three tools (web_search, code_executor, db_query), three agents (researcher, analyst, reporter).

### Options
- **A. All-share** — each agent gets all tools. Agents "wander" — researcher invokes code_executor, defeating role separation.
- **B. Role-scoped** — researcher=[search], analyst=[exec, db], reporter=[]. Clearer responsibility, easier debug.

### Decision rule
**Always B.** Tool *definitions* are shared (one BaseTool class), but *bindings* are role-specific. If you find an agent misusing a tool, the fastest fix is removing it from the agent's tool list.

> CrewAI's official guidance: "write once, use everywhere" (definitions) + assign tools to agents based on role responsibility  [docs.crewai.com/en/concepts/tools, community.crewai.com/t/5919].

### Sources
- [docs.crewai.com/en/concepts/tools]
- [community.crewai.com/t/tool-best-practice-assign-to-agent-or-task/5919]

---

## DC-4 — Memory: default-off or always-on?

### Scenario
A customer-service crew. Should `memory=True`?

### The hidden cost
Enabling `memory=True` triggers **automatic "memory LLM" calls** to classify and store interactions. Token spend often doubles. False recalls add another debugging layer.

### Decision rule
1. **Intra-kickoff** context → use explicit task `context=[...]`, not memory
2. **Cross-kickoff** persistence required → enable `memory=True` (long-term mainly, SQLite)
3. **High-frequency production** → don't use default LanceDB; swap to Mem0 backend  [mem0.ai/blog/crewai-memory-production-setup-with-mem0]
4. **Debugging period** → always `memory=False`; traces are easier

### Red line
Don't conflate "agent forgot X" with "we need memory". 99% of the time, the task description didn't explicitly include X or didn't list it in `context=[...]`.

### Sources
- [docs.crewai.com/en/concepts/memory]
- [mem0.ai/blog/crewai-memory-production-setup-with-mem0]

---

## DC-5 — allow_delegation: on or off?

### Scenario
Hierarchical mode. Should worker agents also get `allow_delegation=True`?

### The pitfall — "Delegation Ping-Pong"
Multiple agents with delegation enabled → A delegates to B, B delegates back to A, infinite loop. Token usage explodes, context window saturates, kickoff crashes via OOM or context-summarization corruption.

### Root causes (documented)
1. **Circular delegation** — multiple agents with `allow_delegation=True`  [github.com/crewAIInc/crewAI/issues/330]
2. **DelegateWorkTool schema mismatch** — tool expects string context, modern LLMs pass dict → silent validation failure → retry storm  [github.com/crewAIInc/crewAI/issues/2606 ref]
3. **max_iter is per-agent, not cross-handoff** — protection doesn't span the delegation chain  [azguards.com delegation-ping-pong]

### Decision rule
1. Default `allow_delegation=False` on **every worker agent**
2. Only the explicit `manager_agent` gets delegation
3. Even in hierarchical, at least one agent in the chain must have `allow_delegation=False` to break potential cycles
4. Wrap `kickoff()` in outer timeout + token-budget guard
5. For complex routing, prefer **Flow** — let Python control delegation, not LLM

### Red line
If your design *requires* LLMs deciding who to delegate to in a loop, you're probably outside CrewAI's reliability envelope. Move to Flow with explicit handoff or LangGraph.

### Sources
- [github.com/crewAIInc/crewAI/issues/330]
- [azguards.com/the-delegation-ping-pong]
- [inkog.io/glossary/crewai-infinite-loop]
