# SkillAlchemy Technical Overview

SkillAlchemy turns a short capability brief and open-world sources into an
installable, evidence-grounded agent skill. The implementation follows the
three-stage method described in the paper.

## System Components

SkillAlchemy consists of three installable skills:

- **SkillAlchemy** is the user-facing entry point. It normalizes the request,
  routes the workflow, and handles user checkpoints.
- **Lens** discovers candidate operational factors and creates paired acquisition
  targets for omitted requirements.
- **LEAP** collects evidence, admits supported procedures, and renders the final
  skill package.

The root `SKILL.md` coordinates Lens and LEAP. The two engines do not replace the
host agent; they provide structured instructions that the host agent executes.

## Stage 1: Implicit Requirement Discovery

Lens maps a brief to candidate operational factors and paired contexts
`<d, x, x'>`. The pair changes factor `d` while holding the remaining task
conditions fixed as far as possible.

Research agents collect source-grounded treatments for four procedural
components:

- condition
- action
- recovery
- verification

The merge step records each component as `changed`, `invariant`, or `unresolved`.
A factor becomes an implicit requirement only when evidence supports a treatment
change in at least one component. Insufficient or conflicting evidence remains
explicitly unresolved.

Primary artifacts:

- `evidence_matrix.json`
- `contrast_records.json`
- `contradiction_report.json`
- `merge_report.json`

## Stage 2: Evidence-Grounded Procedure Admission

LEAP groups findings by the procedural decision they inform and induces candidates
with condition, action, recovery, verification, and evidence provenance.

Each candidate receives an admission record containing supporting findings,
conflicting findings, and the widest evidence-supported scope. The procedure is
then classified as:

- **General** — supported, consistent, and justified beyond one source-local case;
- **Scoped** — supported and consistent, but justified only in a limited context;
- **Exclude** — unsupported or affected by an unresolved conflict.

Primary artifacts:

- `operation_candidates.json`
- `admission_records.json`
- `admitted_general.json`
- `admitted_scoped.json`
- `excluded_candidates.json`

## Stage 3: Skill Package Compilation

Compilation maps admitted procedures into `SKILL.md` and optional bundled
resources. It uses `skills/LEAP/references/skill-grammar.md` to guide structure,
metadata, progressive disclosure, and package-relative references.

Compilation may organize or clarify admitted content, but it may not:

- create a new procedure;
- fill an unsupported component;
- promote an excluded candidate; or
- broaden the admitted scope.

There is no separate post-compilation validation or repair stage in the current
method implementation. The grammar guides presentation rather than acting as an
independent source of task knowledge.

## Exemplar Retrieval

When permitted by the source-access specification, LEAP searches public skills and
uses `score_skill.py` to rank structural exemplars. Exemplars may influence package
organization and presentation only. They cannot introduce task procedures or
override evidence admission.

## Repository Layout

```text
.
├── SKILL.md
├── skills/
│   ├── Lens/
│   │   ├── SKILL.md
│   │   └── skill.json
│   ├── LEAP/
│   │   ├── SKILL.md
│   │   ├── domains/
│   │   ├── references/
│   │   ├── scripts/
│   │   └── skill.json
│   └── agentsop-*/
├── package.json
└── skill.json
```

The `agentsop-*` directories are ready-to-install skills distributed with the
product repository. They are not additional stages of the SkillAlchemy method.
