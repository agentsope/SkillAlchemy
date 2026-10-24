# trajectory-to-semantic-ops — Distilling Semantic Operators from Agent Execution Trajectories

A distilled SOP skill for turning an agent's execution trajectory (action/observation/exit-code stream + scores) into reusable **semantic operators**: data-science operation skills that carry explicit data-semantic constraints (input semantics, operation decision, output constraints, validation). Grounded in the local **AgenticDataBench** repo, whose `testbed/` contains a working trajectory → skill-optimization loop (SkillOpt + history-material injection).

## What this skill teaches

- The three-way distinction between LOTUS-style semantic operators, task-capability labels, and runtime SKILL.md skills — and why only the last is the carrier.
- The real **execution-trajectory schema** (`{kind: message|command, command, exit_code, output}`) and the three rules for reading it without being fooled by the agent's self-narration.
- The **five-field semantic-operator template** (applicability / input semantics / operation decision / output constraints / validation) and the eight high-error operation families.
- The **seven-phase extraction pipeline**: collect → compress → classify → synthesize → inject → optimize → strip.
- The grounded decision rules: prioritize `exit≠0` steps, five-way failure classification, bundle-over-flat history injection, gate-noise limits, and the "invocation count ≠ adoption" trap.

## File map

```
agentsop-trajectory-to-semantic-ops/
├── SKILL.md                       # main skill (7 sections, Chinese-language SOP)
├── README.md                      # this file
├── references/
│   ├── R1-architecture.md         # trajectory schema + semantic-op schema + pipeline topology
│   ├── R2-sop-workflow.md         # 7-phase workflow + function cheat-sheet
│   ├── R3-dilemma-cases.md        # grounded decision cases
│   ├── R4-anti-patterns.md        # when NOT to extract; common mistakes; hard boundaries
│   └── R5-ecosystem-context.md    # vs SkillOpt / LOTUS / EvoDS / Skill Blocks / …
└── intermediate/
    └── operation_candidates.json  # extracted operation/decision atoms for synthesis
```

## How to consume

- **Coder-agent runtime**: read `SKILL.md`. The 7 sections are self-contained.
- **Horizontal synthesis**: load `intermediate/operation_candidates.json` — each entry has `operation`, `trigger`, `decision_rule`, `evidence_cite`.
- **Deep dive on one dimension**: open `references/R{1-5}-*.md`.

## Provenance

- Trajectory schema, pipeline functions, and experiment numbers are read from the local `AgenticDataBench` repo (`testbed/opt_common.py`, `testbed/SKILLOPT_HISTORY_PATCH.md`, `testbed/SkillOpt_两种优化方式分析.md`, `docs/research/IDEA_ASSESSMENT_2026-09-19.md`) and sample `trajectory.json` / `agent_trace.txt` / `results.jsonl` artifacts.
- Related-work citations come from the project's own survey (`IDEA_ASSESSMENT_2026-09-19.md`), which cites arxiv IDs verbatim.
- No fabricated commands, APIs, or benchmark numbers. Where the project itself marks an estimate as an estimate (e.g. token counts from `tiktoken` vs gateway-reported), the skill preserves that caveat.

## Caveats

- The experiment numbers (baseline 0.315, v2 0.512, gate ±0.22, etc.) are single-run / small-sample observations on 10–13 tasks; treat them as directional evidence, not published results.
- The five-field operator template and eight operation families are the project's *prototype scope*, not a claim of optimal granularity.
- The optimizer-specific flags (SkillOpt `exec_timeout`, `num_epochs`, `use_slow_update`) drift with SkillOpt versions; cross-check live configs for production use.
