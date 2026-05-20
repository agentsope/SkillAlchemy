# DSPy SOP Skill — Package README

This package distills DSPy (Stanford NLP) into an actionable SOP skill for coder-agents. It is **not** API documentation — it is a *decision system* for *when* and *how* to apply DSPy primitives in real engineering work.

## Contents

```
dspy-sop-skill/
├── SKILL.md                    # main skill — 7 sections, frontmatter, 4 dilemma cases
├── README.md                   # this file
├── references/
│   ├── R1-architecture.md      # Signatures / Modules / Teleprompters / Compile mental model
│   ├── R2-sop-workflow.md      # 3-stage gate workflow with exit criteria
│   ├── R3-dilemma-cases.md     # 4 extended dilemma cases with citations
│   ├── R4-anti-patterns.md     # 10 anti-patterns + boundaries
│   └── R5-ecosystem-context.md # DSPy vs LangChain/LangGraph/LlamaIndex/Guidance
└── intermediate/
    └── operation_candidates.json   # structured Trigger/Action/Output/Evidence operations
```

## How to use

A coder-agent should load `SKILL.md` when any activation trigger in §1 fires. The `references/` files are deeper drill-downs for sub-tasks (e.g. when the user asks "explain GEPA vs MIPROv2", the agent loads `R3-dilemma-cases.md` Case C and §4.1 of SKILL.md).

The `intermediate/operation_candidates.json` is machine-readable for the meta-pipeline that synthesizes across the 7-project landscape (LangGraph, LlamaIndex, DSPy, CrewAI, vLLM, Aider, Dify).

## Provenance & quality notes

- **No fabrication.** Every claim has an inline citation: `[dspy.ai/...]`, `[arxiv.org/...]`, `[github.com/stanfordnlp/dspy/issues/...]`, or named third-party (Databricks blog, Miyamura substack, langwatch comparison).
- **Real dilemma cases.** Cases A–D draw from community-reported issues (#1596, #1970, #1078) and documented production case studies (JetBlue, Databricks, Haize Labs).
- **Coverage caveats**:
  - Discord war stories are paraphrased from community write-ups; raw Discord transcripts were not fetched (private).
  - The DSPy v3.x API surface (post v3.2.1) was sampled via docs as of research date 2026-05-19; minor API drift possible.
  - GEPA is recent (ICLR 2026 oral) — practitioner war stories are thinner than for MIPROv2.

## Version

- **Skill version**: 0.1.0
- **DSPy version referenced**: v3.2.1 (per GitHub README at research time)
- **Last research**: 2026-05-19
