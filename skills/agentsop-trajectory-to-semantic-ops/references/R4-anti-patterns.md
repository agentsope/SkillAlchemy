# R4: Anti-Patterns, Mistakes & Hard Boundaries

## When NOT to do trajectory → semantic-ops extraction

| Situation | Alternative |
|---|---|
| You only have a single run, no held-out set | You can't separate mechanism from noise; collect more before extracting |
| The error is an environment artifact (PowerShell quoting, `D:\` path in Linux container) | Fix the harness, not the skill — a skill edit can't fix a broken executor |
| The task is one-off and never recurs | A pasted answer "works" but a reusable operator is wasted effort |
| You want to *prove* "progressive disclosure helps" without a flat-load baseline | You're testing organization, not knowledge; need same-content structure control |

## Common mistakes

1. **Writing instance answers / task IDs / test-set column names into the skill.** Overfits, pollutes the operator, leaks evaluation. Constraint survives task change; an answer does not.
2. **Injecting history material and forgetting to strip it.** The main file balloons (9873 chars) and blows the executor timeout. Always `strip_history_text()`.
3. **Gating on 4 single-run tasks.** ±0.22 noise ≈ the signal you're trying to detect. Accept/reject becomes a coin flip.
4. **Reversing the previous generation's rule.** Rules fighting across generations is a direct cause of oscillation. Forbid reversals, cap diff size.
5. **Treating "invocation count" as "adoption".** Count discovery / activation / load / adoption / outcome separately.
6. **Claiming "verified" where you only did a type/row-count check.** Fuzzy-match semantic correctness is only partially caught by such checks.
7. **Using single-run training scores to steer optimization.** ±0.125 per-task noise drowns the signal; use repeat ≥ 3.
8. **Reading `exit_code=0` as "correct".** The agent can return 0 while computing the wrong granularity, unit, or window.

## Hard boundaries

- **Produce constraints, not answers.** The operator's value is a cross-task decision rule; a pasted pipeline implementation is not knowledge.
- **Oracle routing is diagnosis, not a result.** Using gold skills / gold code / gold dependencies to route is an oracle diagnostic — never fold it into the main reported score.
- **Don't preset "deeper disclosure is better".** Progressive-disclosure benefit depends on scale and harness (Skill Blocks, SkillJuror). It's a hypothesis to test, not an axiom.
- **Correlation ≠ mechanism.** Score moving with invocation count proves nothing about *why*. Isolate content, organization, and invocation.
- **Freeze the environment before comparing.** Model, harness, image, dependencies, task interface, plotting protocol, timeout, retry — fix them, then vary only the skill. Otherwise the gain is unattributable.
- **Honor the train/gate/test split.** Never reuse the same tasks across them; group by data-source family to avoid leakage, not by random task split.

## References

- `AgenticDataBench/docs/research/IDEA_ASSESSMENT_2026-09-19.md` (§四–§九)
- `AgenticDataBench/testbed/SkillOpt_两种优化方式分析.md` (bloat, gate noise, reversal)
- `AgenticDataBench/testbed/SKILLOPT_HISTORY_PATCH.md` (bundle vs flat, strip round-trip)
