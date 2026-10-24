# R2: Trajectory → Semantic-Ops SOP Workflow

## The seven phases

### Phase 1 — Collect

Gather the last N rounds of `results.jsonl` (scores + fail reasons) plus each trajectory. **Collect only, do not mutate.** Scores without trajectories = symptoms without diagnosis; trajectories without scores = events without verdicts.

### Phase 2 — Compress (trajectory → text)

Turn `actions[]` into `动作 → 观察` text. **Prioritize failed steps (`exit≠0`) first**, then take the tail. Truncate on budget (default 6000 chars, `OPT_HISTORY_CHARS` override).

The grounded function is `_trajectory_text()` in `testbed/opt_common.py`: it walks actions, emits `[command] … exit=N 观察: …`, and prefers the failing step as the anchor.

### Phase 3 — Classify

Per-task trend, five classes:

```
persistent_fail    0 across recent rounds → most severe, place first
regressed          was passing, now failing
flat_partial       stuck at partial credit
improved           improved this round
stable_success     stable full score → skip (don't spend budget)
```

Order the material by severity: `persistent_fail → regressed → flat_partial`.

### Phase 4 — Synthesize (build material)

Assemble scores + per-task trends + failed trajectories into one markdown block, wrapped in explicit markers:

```
<!-- SKILLOPT_HISTORY_START -->
# 历史执行证据（第 N 轮优化材料）
## 各轮整体表现  | 轮次 | 实验名 | 平均得分 |
## 逐题分数与趋势 | 任务 | r1 | r2 | 完成 | 类别 |
## 失败任务的真实轨迹
### financial_276（persistent_fail，最近 0.000）
  - [Bash] python … 观察: WROTE output.csv ROWS 10
<!-- SKILLOPT_HISTORY_END -->
```

### Phase 5 — Inject → optimize

Attach the material to the skill body and hand it to the optimizer (SkillOpt: bounded text edits + validation gate + reject-bad-edit + slow update). Prefer **bundle** over flat injection: put the material in `references/history_material.md` so the main file stays lean.

| Form | Main-file chars |
|---|---|
| Flat injection (deprecated) | 9873 |
| Bundle (references/) | **3877** |

The executor loads the bundle with the main file as entrypoint and the reference loaded on demand.

### Phase 6 — Strip

Remove the material block from the optimizer output, producing a clean `SKILL.md`. Inject → strip must round-trip byte-identical (`filecmp` passes). The wrapper markers make the strip a single contiguous delete.

### Phase 7 — Accept

Four acceptance questions (from the project's assessment §九):

1. Do held-out **same-distribution** tasks improve?
2. Do **unseen datasets/domains** improve?
3. Do **new combinations** of seen operations improve?
4. Does the gain survive a **second model / harness / benchmark**?

## Function cheat-sheet (grounded in `testbed/opt_common.py`)

```
round_name(kind, mode, r)        reproduce experiment naming → reverse-lookup artifacts
load_round_result / summary      read scores + actions + summary
task_prompt_text                 read a failing task's prompt
_trajectory_text                 actions → 动作/观察 text, prefer exit≠0
classify                         five-way trend
collect_history(window N)        last N rounds of scores + trajectories
build_history_material           markdown block
make_history_skill_init          attach material to skill tail
strip_history_text               peel material off the product
report_rollout()                 emit report.md + report.csv
```

## Environment correctness (easy to get wrong)

- **Path mapping**: a trajectory/prompt written on the host with `D:\…` paths breaks inside a Linux container. Map workspace → `/workspace` (and fix leftover `\`) before the agent reads it.
- **Shell**: host PowerShell vs container bash changes quoting. The grounded failure was a nested-quote `SyntaxError` under PowerShell that vanished under bash.
- **Token accounting**: container gateway may not report usage → fall back to `tiktoken` estimate; host gateway reports real usage. Don't mix the two scales.

## Verification checklist per round

- [ ] history read (window correct, scores + trajectories both present)
- [ ] classification correct (severity order, stable_success skipped)
- [ ] material ≤ budget (chars)
- [ ] inject → strip byte-identical
- [ ] main file contains no `SKILLOPT_HISTORY` residue
- [ ] report covers trajectory + score + elapsed + tokens(in/out) + request count

## References

- `AgenticDataBench/testbed/SKILLOPT_HISTORY_PATCH.md` (§一–§十二: every function above)
- `AgenticDataBench/testbed/SkillOpt_两种优化方式分析.md` (13×3 vs 13×1 evidence)
