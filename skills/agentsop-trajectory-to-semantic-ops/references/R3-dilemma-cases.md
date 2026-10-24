# R3: Dilemma Decision Cases

Every case below is grounded in the AgenticDataBench repo's own experiments and failure notes.

### Case 1 — "Invocation count rose, so the skill works" (trap)

**Trigger**: skill call count and score moved together; you want to claim the mechanism works.

**Diagnosis**: In the v2/v3 runs, the 6 tasks that invoked the skill gained ~1.51 together, but the 4 tasks that *didn't* invoke it also gained ~0.46. The top-level Read/Bash traces showed no actual reads of `references/` files.

**Decision rule**: split the measurement — 发现 (discovery) → 激活 (activation) → 正文/资源加载 (load) → 实际采用 (adoption) → 结果收益 (outcome). Zero explicit invocation ≠ zero effect (description may already be in context); a successful invocation ≠ correct adoption.

### Case 2 — "4-task gate with single runs is a coin flip"

**Trigger**: using a 4-task × 1-run gate to accept/reject each skill edit.

**Diagnosis**: same skill measured twice differed by 0.00…0.50 (one extreme: 0.25 vs 0.75). Mean absolute difference 0.156, 38% of pairs flipped. 4 tasks with a ceiling task (`financial_167` always 1.0) and a floor task (`financial_84` ~0) leaves ~2 discriminative tasks → 95% interval ≈ ±0.22.

**Decision rule**: expand to ≥8 tasks × 2 runs, or 4 tasks × 3 runs; replace ceiling/floor tasks with ones where g0 scores 0.33–0.67.

### Case 3 — "Skill bloats every generation and rules fight"

**Trigger**: 9 generations, +92/−6 lines (128→218), 6 generations with zero deletion, two generations *reversing* a prior rule.

**Diagnosis**: gen06 overwrote gen05's unit rule; gen07 reversed g0's "merge-report needs explicit ask" into "merge by default". Length and score were non-monotonic — 163 lines stayed stable while 218 lines regressed.

**Decision rule**: constrain per-generation diff (e.g. ≤8 lines), forbid reversing the previous generation's rule, prefer minimal additions. A stable 163-line skill beat a bloated 218-line one.

### Case 4 — "Train set looks flat, test set improved"

**Trigger**: no visible training improvement, but test improvement.

**Diagnosis**: train set was high-baseline + low-resolution (single run, per-task noise ±0.125); test set was low-baseline + high-resolution (3-run average). Same g0 skill scored 0.513 on 3-run train vs 0.692 on 1-run train — a 0.18 gap from sampling alone.

**Decision rule**: fix `repeat ≥ 3`; treat train/gate/test as disjoint (train score is really "another sample", not fit); group by data-source/task family, not random task split.

### Case 5 — "References linked but never read"

**Trigger**: SKILL.md points to `references/…` but the trace shows no read of those files.

**Diagnosis**: a body link proves an *entry point exists*, not that the resource was *loaded*. v2/v3 top-level traces showed no reference reads (v3 listed the skill dir once).

**Decision rule**: measure "resource actually read" as its own metric. Don't count the link as adoption.

### Case 6 — "join row-count changed" is not automatically a bug

**Trigger**: a checker flags row-count change after a join.

**Diagnosis**: one-to-many may be exactly what the task requires; normalization can merge keys that were meant to differ. A blanket "output rows < input rows" rule is internally inconsistent (window/rolling keeps row count).

**Decision rule**: compare against the *pre-bound* expected relationship. With no evidence, output "unverified", not "wrong". Type/row-count checks find only *some* semantic errors — don't claim formal completeness.

## References

- `AgenticDataBench/testbed/SkillOpt_两种优化方式分析.md` (cases 2, 3, 4)
- `AgenticDataBench/docs/research/IDEA_ASSESSMENT_2026-09-19.md` (cases 1, 5, 6)
- `AgenticDataBench/testbed/SKILLOPT_HISTORY_PATCH.md` (classification + material structure)
