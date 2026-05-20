# llm-artifact-versioning (Phase D, enhancement overlay, medium-frequency)

Enhancement overlay for versioning the **whole deployable LLM-app artifact** as one bundle so a
deploy is reproducible and rollback is atomic. Activate when preparing to deploy, when nobody
can answer "what exactly is running in prod?", when a deploy must be reproducible later, or
when an incident needs a clean rollback.

## Core claim

**An LLM app artifact ≠ an ML model.** An ML model is one weights file. An LLM app artifact is a
**manifest** over many independently-mutable parts: prompts + compiled programs + model snapshot
pins + retrieval config + eval-set version. Version them **together** (one bundle, one tag) or
you cannot reproduce a deploy — and you cannot roll back without producing a never-tested
combination of components.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main overlay SOP. 7 sections: when to activate / mental model (LLM artifact ≠ ML model) / 5-step workflow / 8 operations / 2 dilemma cases / 8 anti-patterns + boundaries / cross-framework comparison. ~360 lines. |
| `references/R1-source-evidence.md` | Quotes and citations: prompts-as-weights, DSPy save_program & the triple, snapshot-vs-alias identity, silent provider drift, eval-set-as-identity, config-as-artifact, MLflow registry analogy & limit, atomic rollback. |
| `intermediate/operation_candidates.json` | 8 operation candidates (OP-1..OP-8); 5 selected for SKILL §4 as required. |

## Operations (8; 5 surfaced as required: manifest, snapshot pinning, config-as-code, rollback, eval-set linkage)

1. **OP-1 ArtifactManifest** — one `manifest.<version>.json` enumerating every behavior component.
2. **OP-2 ModelSnapshotPinning** — dated snapshots at every call site; never an alias or `latest`.
3. **OP-3 ConfigAsCode** — every behavior knob in VCS; dashboards are not artifacts.
4. **OP-4 EvalSetLinkage** — pin `eval_set_sha`; scores are meaningful only against a fixed set.
5. **OP-5 BundleAndVersion** — one monotonic bundle id/tag covering the whole manifest.
6. **OP-6 RollbackRecipe** — deploy reads the bundle tag; rollback restores all components atomically.
7. **OP-7 ComponentDriftAudit** — manifest field-diff classifies prompt/model/config/eval/retrieval drift.
8. **OP-8 RetrievalConfigBinding** — pin index pointer + embed model + dim; loader guards on mismatch.

## Two dilemma cases

- **A. Provider silently updates** — output drift on an unchanged snapshot; pin is necessary but
  not sufficient; eval-linked canary catches it; mint a new bundle even with no human-authored change.
- **B. Prompt shipped without an eval** — out-of-band edit breaks reproducibility and rollback;
  roll back by **bundle tag** (atomic), re-land the fix behind the gate, add a manifest-matches-live guard.

## Cross-framework

- **DSPy `save_program`** versions one compiled prompt — a single bundle component.
- **LangChain Hub** is a prompt viewer; no model pin, eval binding, or gate.
- **MLflow Registry** gives the right primitives (versioning, stages, reproduce) but is built
  for one model; the LLM bundle is a composite.
- **git + manifest** is the lightweight default and IS the recipe (manifest + tag + gate).

## Companion skills (cross-linked)

- `[[agentsop-per-model-artifacts]]` (`d-per-model-artifacts-skill/`) — NARROWER sibling: versions ONE
  compiled prompt as a (program × LM × dataset) triple. This overlay wraps it as one bundle component.
- `[[agentsop-regression-gate]]` (`d-regression-gate-skill/`) — the CI mechanism that re-runs the pinned
  eval set on new bundle vs parent and fails the PR on regression. This overlay requires it.
- `dspy-sop-skill/` — the compile loop that produces the compiled-program component.
