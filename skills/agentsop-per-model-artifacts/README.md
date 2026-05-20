# per-model-artifacts (Phase D, medium-frequency)

Lifecycle SOP for versioning **compiled prompts and model-specific config artifacts** per `(program × LM × dataset)` triple. Activate when adopting compiled prompts (DSPy, GEPA, BootstrapFewShot), running multi-LM in production, or absorbing a provider/framework deprecation.

## Core claim

A compiled prompt is not a string — it is a triple. Same JSON behaves differently on different LMs, different datasets, or different framework versions. The artifact lifecycle must encode the triple, gate replacements with a regression test, and survive provider snapshot churn.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Main SOP. Seven sections: when to activate / mental model / 5-stage workflow / operation model / 3 dilemma cases / 12 anti-patterns / cross-framework comparison. |
| `references/R1-source-evidence.md` | Quotes and citations: DSPy Case B doctrine, aider edit-format benchmarks, LlamaIndex ServiceContext deprecation, OpenAI/Anthropic snapshot churn, MLflow analogy. |
| `references/R2-versioning-recipes.md` | 7 concrete recipes: filesystem layout, REGISTRY.jsonl schema, compile.py, swap_test.py, CI gate YAML, deprecation scanner, MLflow upgrade path, aider config artifacts, LlamaIndex manifest pattern. |
| `intermediate/operation_candidates.json` | 10 operation candidates (OP-1..OP-10) extracted before SOP write. |

## Operation summary (10)

1. **OP-1 TripleNameArtifact** — encode `(program, model_snapshot, dataset_sha8)` in path.
2. **OP-2 PinModelSnapshot** — never pin to a moving alias; always a dated snapshot.
3. **OP-3 RegisterArtifact** — append-only `REGISTRY.jsonl` with metadata + lineage pointer.
4. **OP-4 SwapTest** — load old artifact, re-eval on new LM; Δ vs gate decides recompile.
5. **OP-5 RegressionGate** — CI re-runs held-out test; fail PR if Δ < −2 points.
6. **OP-6 RecompileOnSwap** — when swap-test fails the gate, re-run optimizer against new LM.
7. **OP-7 DeprecationCalendar** — quarterly scan; block new pins within 90 days of deprecation.
8. **OP-8 ImmutableArtifact** — pre-commit hook forbids hand edits to `artifacts/**`.
9. **OP-9 DatasetHashInPath** — sha256 first-8 of canonical dataset bytes in path.
10. **OP-10 GitTagOnRelease** — promotion to production via `prompt/<program>/<snapshot>/v<n>` tag.

## Three dilemma cases

- **A. GPT-4o deprecation, −8 Δ on Sonnet 3.7** — recompile, don't accept the cliff; keep both artifacts checked in.
- **B. Silent 4o-patch on stable snapshot** — canary catches what pins miss; sample-output hashes per artifact.
- **C. LlamaIndex ServiceContext→Settings cascade** — interrogate every artifact's framework binding before declaring a deprecation handled.

## Cross-framework

- **DSPy** `save_program` is the artifact mechanism; SOP fills LM/dataset/metric binding.
- **LangChain Hub** is a viewer; pair with local REGISTRY for the gate.
- **Manual jsonl + git** is the lightweight default (≤50 artifacts).
- **MLflow Model Registry** is the org-scale upgrade path (`mlflow.dspy.log_model`).
- **Aider** edit-format defaults are per-model config artifacts; same discipline applies.
- **LlamaIndex** index files are embedding-bound; per-index `manifest.json` enforces match.

## Companion skills

- `dspy-sop-skill/` — compile-loop framework whose output this skill manages downstream.
- `aider-sop-skill/` — model-specific edit-format defaults, a sibling form of per-model artifact.
- `llamaindex-sop-skill/` — `Settings` and embedding-bound indices, a sibling form of per-artifact framework binding.
