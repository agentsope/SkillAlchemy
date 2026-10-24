# R1: Trajectory → Semantic-Ops Architecture & Mental Model

## Core insight

The whole loop is **"collect the evidence, then translate it into constraints."** You never hand the raw trajectory back to the model; you first turn it into a *diagnosis* (what failed, and which layer it failed at), and only the diagnosis becomes a reusable operator field.

```
+-----------------------------------------------------------------------+
|  execution trajectory  (kind: message | command, exit_code, output)   |
|        |                                                              |
|        v                                                              |
|  compress   (动作 → 观察, 优先 exit≠0 步)                              |
|        |                                                              |
|        v                                                              |
|  classify   (persistent_fail / regressed / flat_partial / improved /  |
|              stable_success)                                          |
|        |                                                              |
|        v                                                              |
|  synthesize (分数 + 趋势 + 失败轨迹 → markdown 材料)                   |
|        |                                                              |
|        v                                                              |
|  inject → optimize (有界编辑 + 门控)  →  strip (剥除材料)              |
|        |                                                              |
|        v                                                              |
|  semantic operator (适用条件 / 输入语义 / 操作决策 / 输出约束 / 验证)   |
+-----------------------------------------------------------------------+
```

## The trajectory schema (grounded, not invented)

An execution trajectory is a JSON array of step objects. Two kinds appear:

```json
{"kind":"message","content":"... agent narration ..."}
{"kind":"command","command":"bash -lc 'python3 - <<PY ...'","exit_code":0,"output":"... observation ..."}
```

The same content is also persisted as human-readable `agent_trace.txt` (rendered as `[command] … exit=N 观察: …`) and scored in `results.jsonl` (fields `id` / `hard` / `soft` / `fail_reason` / `workspace`, plus timing/token metrics in later iterations).

Three reading rules:

| Rule | Why it matters |
|---|---|
| `exit_code` is where it *broke*, not where it *erred* | A step can return 0 yet compute the wrong granularity; a step can return 1 from a quote-escaping bug, not a data bug |
| `message` is self-narration, not ground truth | The agent says "已完成" while `output.csv` is missing — trust command/output/score over prose |
| `output` is the observation | `WROTE output.csv ROWS 677` (a self-readback) is far more reliable than a closing sentence |

## The semantic-operator schema (five fields)

From the project's assessment (`docs/research/IDEA_ASSESSMENT_2026-09-19.md` §六), every operator must record:

| Field | Content |
|---|---|
| 适用条件 (applicability) | when the operator applies |
| 输入语义 (input semantics) | row meaning, join keys, key uniqueness, time granularity, missing-key policy |
| 操作决策 (operation decision) | fuzzy-match needed? threshold source? one-to-many allowed? unmatched handling? |
| 输出约束 (output constraints) | output granularity, key relationships, join coverage, row-count change, new missing values |
| 验证与修复 (validation & repair) | key collision, many-to-many amplification, wrong match; which doc to load per failure class |

## The eight high-error operation families

`entity alignment` · `join cardinality` · `grouped/window statistics` · `time alignment` · `missingness` · `unit handling` · `train/test transformation` · `artifact validation`

These are the project's **prototype scope** (6–10 families), not an optimal-granularity claim. The point is to pick families that *actually* produce cross-task errors — not "can't write groupby" but "used the wrong group granularity", "duplicated rows", "mixed units", "misaligned time window", "leaked full-data preprocessing into train/test".

## Three concepts that must stay separate

| Concept | Role | Do NOT inherit blindly |
|---|---|---|
| LOTUS-style semantic operator | NL-described data transform, executed by a planner | naming a skill `sem_join` gives no guarantee of LOTUS's semantics |
| Task-capability label (AgenticDataBench skills) | annotates/organizes tasks by operation mode | a classification label ≠ a loadable runtime skill |
| SKILL.md runtime skill | provides flow/knowledge/code/resources at runtime | this is the carrier; value comes from its *mechanism* |

## Mental model to hold

1. **Trajectory is evidence, operator is hypothesis.** Evidence is noisy (single-run, ±0.125); hypothesis must be gated on held-out tasks.
2. **A join's row-count change is not an error by itself** — one-to-many may be exactly what the task asks. The checker must compare against the *pre-bound* expected relationship, and report "unverified" when there is no evidence.
3. **Operators carry constraints, not answers.** A reusable decision constraint survives task change; a pasted answer does not.
4. **"Invocation count" and "effectiveness" are different measurements.** Record discovery → activation → body/resource load → adoption → outcome separately.

## References

- `AgenticDataBench/docs/research/IDEA_ASSESSMENT_2026-09-19.md` (concept split, five-field schema, eight families)
- `AgenticDataBench/generator/data_classes.py` (Skill / SkillTree / FileProfile / EvalCase data shapes)
- `AgenticDataBench/testbed/traindata/_skillopt_*/…/trajectory.json` + `agent_trace.txt` + `results.jsonl` (schema)
- `AgenticDataBench/testbed/SKILLOPT_HISTORY_PATCH.md` (pipeline functions)
