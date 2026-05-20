# R1 · Source Evidence

Every load-bearing claim in `SKILL.md` resolves here to a specific section/line in
the source SKILLs. No claim is invented; where a claim is a *synthesis* across
sources it is marked **[synthesis]**.

Source files:
- `[[crewai]]` = `/Users/5imp1ex/Desktop/Skill-Workplace/output/crewai-sop-skill/SKILL.md`
- `[[agentsop-langgraph]]` = `/Users/5imp1ex/Desktop/Skill-Workplace/output/langgraph-sop-skill/SKILL.md`
- Frontmatter cross-check = `~/.claude/skills/crewai/SKILL.md`

---

## Single-agent baseline (~80%)

- **Claim**: most "multi-agent" problems are single-agent + tools; ~80% of cases
  are single-agent.
- **Source**: `[[crewai]]` DC-1, quoting daily.dev AI agents guide:
  > "Single-agent is right for approximately 80% of cases; the trap is reaching for
  > multi-agent because it sounds more capable. But once you've committed to
  > multi-agent, the next trap is putting too much in one agent."
- Also `[[crewai]]` §1.2 "单 agent + tool-use 就够 → 直接用 SDK"; §6.2 "单 agent
  就够（80% 任务）".
- Also `[[agentsop-langgraph]]` Step 1 / 反模式: "use a plain RunnableSequence or raw API
  calls and exit. Over-graphing simple flows is the #1 anti-pattern."

## The two split-justifying forces (context isolation, parallel expertise)

- **[synthesis]** — distilled from `[[crewai]]` DC-1 (split when failure mode is a
  missed checklist / two-jobs-in-one-prompt) and §2.2 ("一个 agent 同时 research +
  write，质量必劣于两个专家", Phase 1.1). Named here as "context isolation" and
  "parallel expertise" for the rubric.

## "An agent needs agency"

- **Source**: `[[crewai]]` §1.3, João Moura:
  > "An agent needs agency, otherwise it's just another script."
  Plus "如果你能用 if/else 提前写死流程，不要用 Crew."

## Sequential = 1× tokens, low debug cost

- **Source**: `[[crewai]]` §2.3 table — Sequential: Token 开销 1× 基线, 调试难度 低,
  何时用 "80% 场景默认". Hierarchical: 1.3–1.5× (manager overhead), 调试难度 高.

## Supervisor / swarm / hierarchical decision tree

- **Source**: `[[agentsop-langgraph]]` SOP Step 4 "Choose the multi-agent topology",
  sourced there from LangChain's own benchmark `[lc-blog/benchmark]`:
  ```
  Is there exactly one "user-facing" persona?
  ├─ YES → Supervisor (sub-agents are tools; highest token cost; safest with
  │        third-party agents; LangChain's current recommended default)
  └─ NO  → Do sub-agents know about each other?
           ├─ YES → Swarm (dynamic handoff; lower tokens; slightly higher accuracy;
           │        bad fit for third-party agents)
           └─ NO  → Hierarchical Teams (use only when ≥6 specialists need grouping)
  ```

## Swarm beats supervisor on the benchmark, yet supervisor is the default

- **Source**: `[[agentsop-langgraph]]` Step 4:
  > swarm "slightly outperformed supervisor across all scenarios"; supervisor
  > "consistently uses more tokens than swarm" because of the telephone-game
  > translation overhead `[lc-blog/benchmark]`.
  And the same section names supervisor "LangChain's *current recommended default*"
  and "Safest with third-party agents"; swarm is a "Bad fit for third-party agents".
- The benchmark: LangChain, *Benchmarking Multi-Agent Architectures*,
  `www.langchain.com/blog/benchmarking-multi-agent-architectures` (resolved in
  `[[agentsop-langgraph]]` citation index as `[lc-blog/benchmark]`).

## The three supervisor fixes (~50% improvement)

- **Source**: `[[agentsop-langgraph]]` Step 4 and Case 2:
  > LangChain "fix the supervisor (remove handoff messages, add a
  > forwarding-messages tool, tune tool names) for 'a nearly 50% increase in
  > performance'" `[lc-blog/benchmark]`.

## Pick on the two questions, not aesthetics

- **Source**: `[[agentsop-langgraph]]` Case 2 可提取的操作:
  > "Don't pick supervisor vs. swarm on aesthetics — anchor on (a) whether
  > sub-agents can know each other, (b) whether one user-facing voice is mandated.
  > Then optimise the chosen pattern with LangChain's own published fixes before
  > switching paradigms."

## CrewAI hierarchical is structurally broken for routing

- **Source**: `[[crewai]]` DC-2:
  > "实测 hierarchical 会执行所有 task，不会真的按 triage 结果跳过"
  > `[towardsdatascience.com Manager-Worker fails]`. Worked example:
  > Query "Why is my laptop overheating?" → expected triage→technical→done; actual
  > hierarchical runs technical→billing→… and the last task's output overwrites.
- **Source**: `[[crewai]]` OP-4 / DC-2 red line:
  > "永远不要把生产路由依赖默认 manager_llm"; use custom `manager_agent` or a Flow
  > `@listen`/`@router` conditional. Also §6.1 AP-3 "依赖默认 hierarchical
  > manager_llm → manager 执行所有 task / 路由错乱".
- Frontmatter cross-check `[[crewai · frontmatter]]` when_not_to_use:
  > "deterministic routing with strict SLA (CrewAI hierarchical executes tasks
  > sequentially regardless of triage)".

## Routing logic in ~5 lines → use Flow / conditional edge

- **Source**: `[[crewai]]` DC-2 判断规则: "路由逻辑可以用 5 行 Python 表达？→ 用
  Flow"; "路由真的需要 LLM 语义理解 → Hierarchical + 自定义 manager".

## Delegation ping-pong; allow_delegation default off

- **Source**: `[[crewai]]` DC-5 and §6.1 AP-4:
  > multiple agents with `allow_delegation=True` → "delegation ping-pong … token
  > 爆炸 + 超时" (GitHub issues #330 #4783 #2606). Rule: "默认 allow_delegation=False
  > 在所有 worker agent 上; 仅 manager_agent 开 delegation". `max_iter` may not hold
  > across hierarchical handoff; add outer timeout.

## >5 agents → coordination failure

- **Source**: `[[crewai]]` §6.1 AP-1 "Agent 数量爆炸 (>5 个 agent) → 协调失败、token
  飞涨、debug 困难"; Phase 1.1 "2–5 个 agent 是甜区。≥7 个开始出现协调失败".

## Hierarchical teams used for grouping at ≥6 specialists

- **Source**: `[[agentsop-langgraph]]` Step 4 tree: Hierarchical Teams "Use only when ≥6
  specialists need grouping". Reinforced by `[[agentsop-langgraph]]` Case 3 (subgraphs to make
  hundreds of steps navigable).

## OpenAI Swarm is experimental / handoff baseline

- **Source**: `[[agentsop-langgraph]]` 生态对照 table — OpenAI Swarm: "Minimal handoff
  routine", Production-ready **No** (explicitly experimental); decision heuristic
  "Reach for Swarm only when: studying multi-agent concepts as reference code."

## Latency < 200ms / single call → no multi-agent framework

- **Source**: `[[agentsop-langgraph]]` 反模式 hard boundaries "Latency budget < 200ms per
  call"; `[[crewai]]` §1.2 "延迟敏感（<500ms）→ 多 agent 编排不适合".

## Bounded-loop cross-link

- **[synthesis]** — termination discipline (state-based exit counter, trust nothing
  the LLM does to stop) drawn from `[[agentsop-langgraph]]` OP-9 / Case 1 (text-to-SQL retry
  bug, recursion_limit is a safety net not control flow) and `[[crewai]]` DC-5;
  delegated to the `[[agentsop-bounded-loop]]` overlay.
