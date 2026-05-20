# agent-topology-selection skill

Cross-framework **enhancement overlay** for **multi-agent topology selection** —
deciding *whether* to use multiple agents at all, and if so, *which* topology
(single-agent / sequential / supervisor / swarm / hierarchical) **before** writing
any agent code.

This is the **O6 gap skill** in the Phase-D enhance pass. CrewAI exposes
`sequential` / `hierarchical` and LangGraph exposes supervisor / swarm, but no
skill surfaces the *selection rubric* that should drive the choice. This is that
skill.

## The rubric (binary questions)

```
Q0  Is single-agent + tools enough?              → YES: single-agent. STOP.
Q1  Do agents need to know about each other?     → NO:  supervisor / sequential
Q2  Must the output speak with one voice?         → YES: supervisor  / NO: swarm
≥6 specialists grouping into teams                → hierarchical (grouping only)
```

## Core insight

> Most "multi-agent" problems are single-agent + tools. Add agents only when
> *context isolation* or *parallel expertise* genuinely demands it. The single
> agent is the baseline every topology must beat — defend it first.

## The nuance that matters

LangGraph's *own* benchmark found swarm slightly beats supervisor on accuracy and
uses fewer tokens — **yet they ship supervisor as the recommended default.** The
default encodes *third-party-agent safety* (single audit funnel), not accuracy. A
coder agent copying the default blindly leaves accuracy and tokens on the table.
The rubric forces the decision onto the two binary questions instead.

## Layout

```
d-agent-topology-selection-skill/
├── SKILL.md                          # 7-section SOP (activation → cross-framework table)
├── README.md                         # this file
├── references/
│   └── R1-source-evidence.md         # every cited claim resolved to a source SKILL line
└── intermediate/
    └── operation_candidates.json     # raw trigger/action/output/evidence operations
```

## Contents

8 operations (defend-baseline, single-vs-multi gate, static-order gate, the two
binary gates, the supervisor-default caveat, tune-before-switch, bound-the-loop),
2 dilemma cases (swarm-beats-supervisor-but-ship-supervisor; CrewAI hierarchical is
structurally broken for routing), 6 anti-patterns, and the cross-framework mapping
(CrewAI sequential/hierarchical, LangGraph supervisor/swarm, OpenAI Swarm handoff,
single-agent + tools baseline).

## ENHANCE overlay

This is an **overlay**, not a replacement. For the per-framework API it cross-links
the base skills inline as `[[name]]`:

- `[[crewai]]` — `Process.sequential` / `Process.hierarchical`, `manager_agent`,
  `allow_delegation`, the broken-hierarchical-router finding.
- `[[agentsop-langgraph]]` — supervisor / swarm / hierarchical-teams decision tree, the
  multi-agent benchmark.
- `[[agentsop-bounded-loop]]` — any runtime-handoff topology must be bounded before ship.

Activate this skill for the *topology decision*; descend to the base skill for the API.

## Method

Mined directly from the source SKILLs under
`/Users/5imp1ex/Desktop/Skill-Workplace/output/`: `crewai-sop-skill`,
`langgraph-sop-skill` (frontmatter cross-checked against `~/.claude/skills/crewai`).
Every load-bearing claim carries an inline `[[source · section]]` tag resolving in
`references/R1-source-evidence.md`. No fabricated APIs.

## Position in the Phase-D inventory

- **Sibling overlays**: `d-query-routing-skill` (routes by query *kind* — composes
  with this skill's routing/coordination distinction), `d-bounded-loop-skill`
  (bounds the chosen topology), `d-llm-engine-selection-skill`.
- **Boundary vs `d-query-routing-skill`**: that skill picks a *handler for a query*;
  this skill picks an *agent topology for a task*. Routing (control flow) is a
  reason **not** to use hierarchical (see Dilemma Case 2).
- **Boundary vs `[[agentsop-bounded-loop]]`**: this skill picks the topology; bounded-loop
  guarantees it terminates.
