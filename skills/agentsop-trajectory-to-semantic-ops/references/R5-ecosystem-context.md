# R5: Ecosystem Context — Where "Trajectory → Semantic Ops" Sits

> This SOP is not a new claim of "first to optimize data-science skills from trajectories." It is the *feeding-and-constraint* layer around existing optimizers, and its contribution lives in making **data semantics between operations checkable**.

## Direct relatives (must cite, must differentiate)

| Work | What it already covers | This SOP's angle |
|---|---|---|
| SkillOpt (2026-05) | Bounded text edits from trajectories, gate validation, reject-edit memory, slow updates | The history-material front-end: *which* failed steps to feed and *how* to keep them out of the body |
| SemPipes (2026-02) | NL-defined tabular ops + pipeline context + evolutionary search | Why optimize *transferable operation knowledge*, not one pipeline's implementation |
| EvoDS (KDD 2026) | Executable skill acquisition/validation/reuse + SFT + agentic RL | Frozen-model, portable-knowledge, compositional-generalization as comparison axes |
| EvoSkill (2026-03) | Discover/revise skill catalog from failures | "Multi-file skill from failure" alone is not the novelty |
| Bilevel MCTS (2026-04) | Outer structure search + inner content optimization | "Jointly optimize disclosure structure and content" has a direct prior |
| SkillJuror (2026-06) | Controls skill knowledge amount; flat vs progressive; checks actual reads | Must control for knowledge amount — new knowledge ≠ disclosure gain |
| Skill Blocks (2026-08) | Whole-preload vs chunk-on-demand vs references vs hybrid | Cost must count cache + extra tool rounds |
| Progressive Disclosure (2026-07) | Layer-count vs retrieval on long docs | Don't preset "deeper is better"; benefit is scale/harness-dependent |
| Repo-To-Skill / AREX-Skill (2026-09) | Distill + validate many skills from ML repos | "Release a broad ML/DS skill library" faces strong scale priors |
| COBRA-Skills (2026-09) | Budget-constrained skill-candidate evaluation; claims cheaper than SkillOpt | The new cost baseline if efficiency is your claim |

## Semantic-data lineage (different layer, must acknowledge)

- **LOTUS** (2024): NL-described semantic operators with input data, NL condition, reference impl, optimized behavior — batch semantic data processing.
- **DocETL** (2024) / **Abacus** (2025): pipeline rewrite + cost optimization in semantic data processing.
- **Declarative Data Services** (2026): typed constraints + operator DAG + system skills + error attribution for data backends.

These mean "constraint + DAG + skill" as an abstraction cannot be claimed as first. The differentiation must be **mechanism + experiment**, not a new noun.

## Earlier agent/skill lineage

DS-Agent (case reuse vs no-skill), Data Interpreter (hierarchical task graph + iterative verification), GEPA / ACE (feedback-driven prompt optimization), Memento-Skills (routing + catalog update), SkillsBench (benefit is heterogeneous; auto-generated skills are not always effective).

## The defensible research narrowing

> In a frozen model under a constrained execution budget, can operation skills **with explicit data-semantic constraints** — via **state-dependent disclosure + local repair** — beat a same-knowledge whole skill and plain retrieval on **unseen datasets and unseen operation combinations**?

The mechanism to prove: data-state and check-feedback signals decide *what to load* better than the initial task text alone, and this holds after controlling for knowledge amount, model, budget, and the checker.

## Comparison axes for any new result

1. Same-knowledge full-load (flat) vs modular on-demand.
2. Initial-task retrieval vs state/check-feedback-driven disclosure.
3. Remove the semantic checker → isolate checker value from disclosure value.
4. Local update vs whole-skill update.

## References

- `AgenticDataBench/docs/research/IDEA_ASSESSMENT_2026-09-19.md` (full survey + arxiv IDs)
- Cited IDs: LOTUS 2407.11418, AgenticDataBench 2607.01647, SkillOpt 2605.23904, SemPipes 2602.05134, EvoDS 2606.03841, EvoSkill 2603.02766, MCTS 2604.15709, SkillJuror 2606.11543, Skill Blocks 2608.14943, Progressive Disclosure 2607.17598, Repo-To-Skill 2609.02749, COBRA-Skills 2609.11682, SkillsBench 2602.12670
