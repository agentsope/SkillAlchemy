# aider-sop — Aider as an Operating System for Coder-Agents

A distilled SOP skill for using **Aider** (https://github.com/Aider-AI/aider) as a terminal-based AI pair programmer. Part of a 7-project landscape research (LangGraph, LlamaIndex, DSPy, CrewAI, vLLM, Aider, Dify) extracting the decision OS behind each tool.

## What this skill teaches

Aider's *operating system* — the four primitives, the decision rules that resolve dilemmas, the boundaries of when not to use it, and the place it occupies in the coding-agent ecosystem.

## File map

```
aider-sop-skill/
├── SKILL.md                       # main skill (7 sections, ~500 lines, Chinese-language SOP)
├── README.md                      # this file
├── references/
│   ├── R1-architecture.md         # repo-map + edit formats + git commits + REPL
│   ├── R2-sop-workflow.md         # 7-phase workflow + command cheat-sheet
│   ├── R3-dilemma-cases.md        # 6 grounded decision cases
│   ├── R4-anti-patterns.md        # when NOT to use; common mistakes
│   └── R5-ecosystem-context.md    # vs Cline / Cursor / Continue / OpenHands
└── intermediate/
    └── operation_candidates.json  # extracted operation/decision atoms for synthesis
```

## How to consume

- **Coder-agent runtime**: read `SKILL.md`. The 7 sections are self-contained.
- **Horizontal synthesis (across 7 projects)**: load `intermediate/operation_candidates.json` — each entry has `dimension`, `operation`, `trigger`, `decision_rule`, `evidence_cite`.
- **Deep dive on a single dimension**: open `references/R{1-5}-*.md`.

## Provenance

- All quoted text traceable to aider.chat (docs + blog) or GitHub (Aider-AI/aider).
- Benchmark numbers (20→61% udiff, 79.7→85% architect, 70.3% repo-map hit, 55.1→64% Sonnet refactor, JSON degradation) come from Paul Gauthier's published posts.
- No fabricated commands or APIs. Where docs were ambiguous, the SKILL flags it.

## Caveats

- Leaderboard numbers move quickly. The top-model table in R2 reflects what was on aider.chat/docs/leaderboards/ at fetch time; treat as illustrative, not canonical.
- Some specific feature flags (e.g., exact default edit format per model) change with each Aider release. Always cross-check with the live docs for production decisions.
- The skill focuses on **how to operate Aider**, not how Aider is implemented internally (e.g., the precise PageRank scoring weights are not documented publicly).
