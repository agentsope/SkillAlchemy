# crewai-sop-skill

SOP-style skill distilled from **CrewAI** (the multi-agent orchestration framework by João Moura / crewAIInc) — intended to guide a coder-agent in deciding **when, how, and when NOT to use CrewAI** for role-based multi-agent systems.

Part of a 7-framework landscape research package (LangGraph, LlamaIndex, DSPy, **CrewAI**, vLLM, Aider, Dify).

## Why this skill exists

CrewAI is the most intuitive multi-agent framework in the ecosystem — role + goal + backstory + task + crew — but it has known structural pitfalls (hierarchical-manager failures, delegation ping-pong, weak observability). This skill packages the decision logic and SOP so an agent doesn't fall into the common traps.

## Layout

```
crewai-sop-skill/
├── SKILL.md                    # main, 400-600 lines, 7 sections
├── README.md                   # you are here
├── references/
│   ├── R1-architecture.md      # Agent/Task/Crew/Process/Flow primitives
│   ├── R2-sop-workflow.md      # Phase 0→4 SOP
│   ├── R3-dilemma-cases.md     # 5 dilemmas with decision rules
│   ├── R4-anti-patterns.md     # 5 AP + boundaries
│   └── R5-ecosystem-context.md # vs LangGraph / AutoGen / Swarm
└── intermediate/
    └── operation_candidates.json
```

## How to use

A coder-agent should read `SKILL.md` first; references provide deeper rationale and cited evidence.

Activate when the user signals: "multi-agent crew", "role-based agents", "researcher + writer + reviewer pipeline", or explicitly mentions CrewAI.

## Quality notes

- All claims cite docs.crewai.com, github.com/crewAIInc/crewAI, community.crewai.com, or named third-party engineering posts
- 5 Dilemma Cases (exceeds ≥3 requirement), each with decision rules
- Web research date: 2026-05; CrewAI version 1.14.5 at time of capture
