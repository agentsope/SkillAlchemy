---
name: agentsop-per-model-artifacts
version: 0.1.0
description: >-
  Lifecycle SOP for **per-model prompt artifacts** — the compiled prompts, instructions,
  few-shot demos, edit-format pins, and embedding-bound indices that change behavior when
  the underlying LM, dataset, or framework version changes. Activate when adopting compiled
  prompts (DSPy, GEPA, BootstrapFewShot output), when supporting multiple LMs in production,
  when a provider deprecates a model snapshot, or when a framework deprecates a config
  surface (LlamaIndex `ServiceContext` → `Settings`, Aider edit-format defaults). Do NOT
  activate for one-off raw prompt edits or for truly model-agnostic system prompts that have
  been swap-tested. Search keywords: prompt portability, model swap, recompile prompt, model
  deprecation, prompt per model, prompt breaks on new model, version compiled prompts.
---

# Per-Model Prompt Artifacts — SOP

> *"Prompts are effectively the weights of an LLM application."*
> — DSPy core philosophy [arxiv.org/abs/2310.03714]
>
> *"Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the artifact — recompile."*
> — dspy-sop SKILL, Dilemma Case B

---

## 1. 何时激活 (When to activate)

Activate this skill when **any** of the following appears in the user's intent, codebase, or workflow:

| Trigger | Signal |
|---|---|
| Adopting compiled prompts | `compiled.save("v1.json")`, `dspy.load_program()`, `BootstrapFewShot`, `MIPROv2`, `GEPA`, LangChain Hub `hub.push/pull`, prompt files checked into `prompts/` or `artifacts/` |
| Multi-LM production | The same program runs against ≥2 of: `gpt-4o-*`, `gpt-4o-mini-*`, `gpt-4.1-*`, `claude-3-5-sonnet-*`, `claude-3-7-sonnet-*`, `claude-3-opus-*`, `Llama-3-*`, `Llama-3.1-*`, `DeepSeek-V3`, `gemini-2.5-pro` |
| Provider deprecation | OpenAI/Anthropic deprecation notice mentioning a pinned snapshot; alias rollover (`gpt-4o` → new dated snapshot); silent model behavior drift reports |
| Framework deprecation | LlamaIndex `ServiceContext` → `Settings`; LangChain `LLMChain` → LCEL; DSPy major version bump; aider edit-format default change |
| Symptoms | `prompts/system_prompt.txt` (no model in path), generic alias pins (`model="gpt-4o"`), missing `parent_artifact` lineage, hand-edited compiled JSON, no held-out test set re-runs |
| Cross-skill bridges | DSPy compile produced output → ship via this SOP. LlamaIndex index baked with embed model → tag artifact per this SOP. Aider edit-format pin → per-model config artifact per Recipe 6 (R2) |

**Do NOT activate** when:

- Raw, one-off prompt edits with no compile step and no production deploy.
- A genuinely model-agnostic system prompt that has been **swap-tested** across ≥3 LMs with <2-point dev metric drift.
- Prompts that must remain verbatim human-authored for compliance — versioning still matters, but the optimizer/recompile loop does not apply.
- The whole pipeline lives behind a vendor's managed prompt (e.g. OpenAI's Prompt Library) where the vendor owns the artifact.

---

## 2. 核心心智模型 (Core mental model)

### The artifact is a triple, not a string

```
                ┌────────── ARTIFACT ──────────┐
                │                              │
   program  ×   LM (snapshot)  ×   dataset (hash)   →   compiled.json + metadata
   (code)       (provider+date)    (canonical hash)
                │                              │
                └─ change any axis → new artifact ─┘
```

Three load-bearing claims:

1. **A compiled prompt is not portable.** The DSPy doctrine (sibling skill, Case B): swap the LM → recompile. Reusing GPT-4o-compiled `program.json` on Llama-3-8B typically loses 15–30 points (R1 §5). The asymmetry is real and documented.

2. **The snapshot, not the alias, is the identity.** `gpt-4o` is a moving alias; `gpt-4o-2024-08-06` is an immutable identifier. Pinning to the alias means your behavior changes silently when OpenAI rolls the alias forward. Anthropic does not even roll aliases — Sonnet 3.5 (`claude-3-5-sonnet-20240620`) and Sonnet 3.5 v2 (`claude-3-5-sonnet-20241022`) are different models with different behavior; the org that pinned the wrong one in 2024-10 ate a regression in 2025-10 when the older one was retired (R1 §4).

3. **The dataset is part of the identity.** Compiled prompts overfit their training distribution. Two artifacts compiled from the "same dataset" that turn out to differ by 50 examples produce silently different programs. A `sha256` over canonicalized dataset bytes, embedded in the artifact path, makes this impossible to confuse (OP-9).

### The PyTorch checkpoint analogy

| PyTorch checkpoint | Per-model prompt artifact |
|---|---|
| `.pt` weights file | `program.json` (compiled prompt) |
| Architecture (forward pass) | DSPy Signature + Module graph (source-of-truth Python) |
| Dataset version | `dataset_sha256_8` in path |
| Hyperparameters | optimizer config (`MIPROv2 auto="light"`, seed, demos) |
| Framework version | `dspy_version`, `python_version` in metadata |
| Eval score on val | `dev_score` in REGISTRY |
| Final test score | `test_score` in REGISTRY |
| Model registry (MLflow) | `artifacts/REGISTRY.jsonl` or MLflow (Recipe 5) |
| Promotion to prod | git tag `prompt/<program>/<snapshot>/v<n>` |

The same engineering discipline applies. Anyone who would not check a `.pt` into prod without a checkpoint registry should not check a compiled prompt into prod without an artifact registry.

### Why "alone is not enough"

A bare `compiled.save("v1.json")` produces a JSON file that, viewed in isolation, looks model-agnostic. The instructions and demos are text — they could be for any model. But they were *selected by an optimizer running calls against a specific LM*. The model's distributional response to the bootstrapping queries shaped which demos got kept. The artifact is implicitly LM-conditioned without saying so. The SOP exists to make this conditioning explicit and auditable.

---

## 3. SOP 工作流 (SOP workflow)

A five-stage lifecycle. Each stage has an exit criterion.

### Stage 1 — Initial compile

1. Source-of-truth Python module (`src/<program>/program.py`) defines the DSPy module graph.
2. Pin the **dated snapshot** of the LM (not the alias): `dspy.LM("openai/gpt-4o-2024-08-06")`.
3. Pin the dataset: canonicalize → `sha256` → use first 8 hex chars (`a8f1c2e9`) as the dataset tag.
4. Run the optimizer (start with `MIPROv2(auto="light")` per dspy-sop). Record `cost_usd`, `wall_seconds`.
5. Evaluate on a **held-out test set** (not the optimizer's val split).

**Exit:** Held-out test score recorded. No artifact saved yet.

### Stage 2 — Version (write artifact + registry)

6. Compute the path: `artifacts/<program>/<provider>/<model-snapshot>/<dataset>-<sha8>/v<n>.json` where `n` is the next integer after existing files in that directory.
7. `compiled.save(path)` for the JSON; optionally also `compiled.save(path_dir, save_program=True)` for whole-program reproducibility.
8. Append one line to `artifacts/REGISTRY.jsonl` with the schema in R2 Recipe 1.
9. Commit both the artifact AND the REGISTRY line in one PR (gated by Stage 3).

**Exit:** Artifact + REGISTRY entry on disk, both staged for PR.

### Stage 3 — Register (regression gate)

10. CI loads the new artifact, identifies its `parent_artifact` (previous artifact for same `program × model × dataset`), re-runs held-out test set, compares.
11. Fail PR if `new_test_score - parent_test_score < -GATE` (default `GATE = 0.02`, 2 points on 0-1 scale).
12. Block merge unless gate passes or a human attaches the `artifact-override` label (with justification in PR body).

**Exit:** PR merged to main, REGISTRY canonical.

### Stage 4 — Swap-test (on model swap or new snapshot)

13. New LM snapshot announced (e.g. `gpt-4o-2024-11-20` replacing `2024-08-06`). Or considering family swap (GPT-4o → Sonnet 3.5).
14. Load existing artifact unchanged. Configure DSPy to the new LM. Run held-out test set.
15. Compute Δ-score vs original.
   - `|Δ| ≤ 2 points`: tag artifact `transferable[old→new]` in REGISTRY. May ship without recompile.
   - `|Δ| > 2 points`: tag `recompile_required[old→new]`. Proceed to Stage 5.
16. Emit `swap-report-<old>-to-<new>.md` artifact regardless of outcome (audit trail).

**Exit:** Swap report committed, recompile decision recorded.

### Stage 5 — Recompile or accept

17. If `recompile_required`: re-run the same optimizer config against the new LM. Produces a new artifact at the new model's path. Increment `v<n>`.
18. If `transferable`: keep using the old artifact; mark in REGISTRY which model snapshots it's certified-transferable to.
19. Keep BOTH old and new artifacts checked in. Production deploy script reads the git tag, not HEAD.
20. Loop back to Stage 2 for the new artifact.

**Exit:** Production deploys an artifact whose REGISTRY entry shows passing test score against the model it will actually run on.

### Quarterly maintenance loop

- Run deprecation scan (R2 Recipe 4). Open issues for artifacts within 90 days of model retirement.
- Run canary re-eval: re-run held-out test set against the pinned snapshot to detect silent provider-side drift. Threshold same as regression gate.

---

## 4. 操作模型 (Trigger / Action / Output / Evidence)

### 4.1 Storage operations

| Trigger | Action | Output | Evidence |
|---|---|---|---|
| Compile finishes successfully | Path `<program>/<provider>/<snapshot>/<dataset-sha8>/v<n>.json`; append REGISTRY line with `parent_artifact` pointer | Grep-able path + lineage | R2 Recipe 1; OP-1, OP-9 |
| About to pin a model | Use **dated snapshot** never an alias: `gpt-4o-2024-08-06` not `gpt-4o`; `claude-3-5-sonnet-20241022` not `claude-3-5-sonnet` | Metadata header inside artifact + REGISTRY | R1 §4 (alias rollover); OP-2 |
| Multiple compiles share a program code | All keyed by `program` field in REGISTRY (string), `commit` field links to source-of-truth Python at compile time | Reproducible: `git checkout <commit>` restores the program code that produced it | OP-3 |
| Promoting to production | `git tag prompt/<program>/<snapshot>/v<n>`. Deploy reads the tag, not main HEAD | Atomic rollback via `git checkout <tag>` | MLflow Stage analogy (R1 §7); OP-10 |
| Need whole-program portability | `compiled.save(dir, save_program=True)` for pickled program + state; ship both | Self-contained; survives source-tree reorgs (until Python/DSPy version mismatch) | DSPy save_program docs [dspy.ai/tutorials/saving/] |

### 4.2 Swap-test operations

| Trigger | Action | Output | Evidence |
|---|---|---|---|
| Provider releases new snapshot | OP-4 swap-test old artifact against new model on held-out test set | Δ-score; recompile_required boolean | R2 Recipe 2 |
| Family swap candidate (GPT-4o → Sonnet) | Swap-test BOTH directions (artifact-from-A run on B; artifact-from-B run on A); record asymmetry | Two Δ-scores; choose recompile direction | R1 §5 (down-transfer 15-30pt drop) |
| Aider edit-format default change | Re-run aider edit benchmark on fixed task subset for affected model | edit-format-bench delta; pin if changed | aider SKILL line 302 (udiff 20→61%) |
| LlamaIndex `Settings.embed_model` change candidate | **Refuse to swap without rebuilding index.** Re-embed against full corpus; tag new index artifact | New `indices/<name>/openai__<embed-model>__<dim>/<corpus-sha8>/` | LlamaIndex SKILL anti-pattern A2; R2 Recipe 7 |

### 4.3 Gate operations

| Trigger | Action | Output | Evidence |
|---|---|---|---|
| PR touches `artifacts/**/v*.json` | CI regression-gate: re-run held-out test against new artifact and parent artifact | CI status `artifact-regression: pass\|fail\|overridden` | R2 Recipe 3; OP-5 |
| PR tries to add file under `artifacts/` without REGISTRY append | Pre-commit hook fails | Local hook error; can't push | OP-8 |
| PR pins a snapshot ≤90 days from deprecation | Pre-commit hook warns; CI fails unless override label | Surfaces deprecation debt at compile time | OP-7; R2 Recipe 4 |
| Hand edit to compiled JSON | Pre-commit hook fails: artifact files are read-only except via compile.py | Forces recompile path | OP-8; dspy-sop anti-pattern #3 |

### 4.4 Lineage operations

| Trigger | Action | Output | Evidence |
|---|---|---|---|
| Looking up "which artifact is in prod for this program?" | `git ls-remote --tags origin 'prompt/<program>/*'` | Tag list with snapshot + version | OP-10 |
| Reproducing a past compile | REGISTRY entry has `commit`, `dspy_version`, `optimizer_config`, `dataset_sha256_8`, seed; replay against original LM snapshot | Bit-identical or near-identical artifact | R2 Recipe 1; OP-3 |
| Auditing "what changed when score regressed" | Diff REGISTRY entries; if `dataset_sha256_8` changed → dataset drift; if `optimizer_config` changed → config drift; if `dspy_version` changed → framework drift; if `commit` changed without code changes → environment drift | Root-cause class identified | OP-3 |

---

## 5. 困境决策案例 (Dilemma cases)

### Case A — "GPT-4o deprecation: artifact loses 8 points on Sonnet 3.7"

**困境 (Dilemma):** Production runs a DSPy-compiled program against `gpt-4o-2024-05-13` at 82% test score. OpenAI announces deprecation in 60 days. The team wants to move to Sonnet 3.7 (`claude-3-7-sonnet-20250219`) for unrelated cost/latency reasons. Swap-test (OP-4) shows the unchanged artifact scores 74% on Sonnet 3.7 — Δ = −8 points. Recompile, accept, or hybrid?

**约束 (Constraints):**
- Recompile cost on Sonnet 3.7 (200-example trainset, MIPROv2 light): ~$4 and 20 minutes.
- Customer SLA is "≥80% on the public eval set".
- Sonnet 3.7 has extended thinking budget — different output distribution from GPT-4o.
- Old artifact's instructions reference "be terse" — Sonnet 3.7 with thinking ignores terseness hints.
- Team has 60 days, not 60 minutes.

**决策步骤 (Decision steps):**
1. **Do not accept the −8 swap as-is.** The artifact is below SLA on the target model. Per dspy-sop Case B doctrine, "Changing the LM invalidates the artifact — recompile" is the default.
2. **Recompile against Sonnet 3.7 with the same dataset.** Run `MIPROv2(auto="light")` first (R2 cost guardrail). If light gives ≥80%, stop. If <80%, escalate to `medium` only after Stage 1 review of the program/metric.
3. **Tune the optimizer for Sonnet 3.7 specifics.** Set `max_bootstrapped_demos` lower (Sonnet 3.7's thinking emits richer reasoning per-demo, so fewer richer demos > more thin demos — R1 §1).
4. **Keep BOTH artifacts** in `artifacts/<program>/`. The GPT-4o-2024-05-13 artifact stays available for canary-rollback during the cutover window.
5. **Git tag the new artifact** as `prompt/<program>/claude-3-7-sonnet-20250219/v1` only after the regression gate passes against the Sonnet 3.7 held-out test set.
6. **Emit `swap-report-gpt-4o-2024-05-13-to-claude-3-7-sonnet-20250219.md`** showing: transfer Δ −8, recompiled Δ +3 vs original. Audit trail.

**结果 (Outcome):** Recompiled Sonnet 3.7 artifact lands at 83% on the same held-out set. Cost: $4 + reviewer time. The +1 point over the GPT-4o original is bonus; the value was avoiding the −8 cliff.

**可提取的操作 (Extractable operation):** **A negative swap-test Δ exceeding the regression gate is a recompile signal, not a "ship anyway" signal. The artifact path makes both old and new available simultaneously — there is no migration risk to keeping both.**

---

### Case B — "Silent 4o-patch: same snapshot string, different behavior"

**困境:** Quarterly canary re-runs the held-out test set against the production artifact (`gpt-4o-2024-08-06`, no model change). Score dropped from 78% to 73% over three months. No code changed. No artifact changed. No registry entry changed. What happened?

**约束:**
- The pinned snapshot string did not change.
- OpenAI's policy is "snapshots are stable" but in practice server-side mitigations (safety, hallucination patches, throughput) ship without bumping the snapshot ID.
- Customer noticed before the team did. SLA at risk.
- Reverting the model is not possible — the canary IS the latest behavior on the same snapshot.

**决策步骤:**
1. **Verify the canary against a stored sample-output hash.** Per OP-2, REGISTRY entries log a sample-output hash from compile time. Re-run against the same 20 sample inputs; compare current outputs to stored hashes. Divergence → confirms behavior shifted on the same snapshot.
2. **Run the regression gate locally** with current canary outputs as the "new artifact" and compile-time outputs as "parent". This isolates whether the metric also dropped or just the outputs changed (semantically-equivalent rewrites would shift hashes but not score).
3. **Recompile against the same snapshot.** Even though the snapshot string is unchanged, recompiling lets the optimizer re-bootstrap demos against the new server-side behavior. Cost is the same $2–4 as initial light compile.
4. **Tag the new artifact as `v<n+1>`** under the same model directory: `artifacts/<program>/openai/gpt-4o-2024-08-06/<dataset-sha>/v<n+1>.json`. The `compiled_at` field in REGISTRY makes the temporal lineage clear even though the snapshot string is unchanged.
5. **Add the canary cadence to weekly** for 30 days post-incident; revert to quarterly when stable.
6. **File issue with OpenAI** (if support contract): provide REGISTRY entries showing same snapshot string, same code commit, same dataset hash, drift > regression gate.

**结果:** Recompile recovers score to 79% (+1 over baseline, because the optimizer found demos that work with the new server behavior). Lesson: snapshot pins protect against MOST drift but not all. Canary catches what pins miss.

**可提取的操作:** **The snapshot string is necessary but not sufficient. A periodic canary against held-out test data is the only true contract with the model provider. Store sample-output hashes per artifact so silent drift is detectable, not just inferable.**

---

### Case C — "LlamaIndex ServiceContext deprecation: which artifacts to migrate"

**困境:** Team upgrades from LlamaIndex 0.9.x to 0.11.x. `ServiceContext(llm=..., embed_model=...)` is deprecated in favor of `Settings.llm = ...` / `Settings.embed_model = ...` (LlamaIndex SKILL §4.4). There are 14 indices in production, each baked with various embed models including `text-embedding-ada-002` (deprecated) and `text-embedding-3-small` (current). What needs to be touched?

**约束:**
- Code-level migration: `ServiceContext` → `Settings` is mechanical, ~1 hour.
- Index-level migration: re-embedding the largest corpus (4M docs, `text-embedding-3-small`) is ~$200 and 6 hours.
- Indices on `text-embedding-ada-002` MUST be re-embedded — that model is going away (R1 §3).
- Mixing embedding spaces silently is the worst-case failure (LlamaIndex SKILL anti-pattern A2).

**决策步骤:**
1. **List every index and its manifest** (per R2 Recipe 7). If any index lacks a `manifest.json` with `embed_model` and `dim`, treat as unknown — must re-embed defensively.
2. **Bucket indices by embed model:**
   - On deprecated embed (`text-embedding-ada-002`): **must re-embed**. New artifact path `indices/<name>/openai__text-embedding-3-small__1536/<new-corpus-sha8>/`.
   - On current embed: **code-only migration** (ServiceContext → Settings). Index artifact unchanged. Update manifest with new `llama_index_version`.
3. **Refuse to start the new app** if `Settings.embed_model` at runtime doesn't match a loaded index's `manifest.embed_model` (R2 Recipe 7 loader guard). This converts a silent data-corruption bug into a startup error.
4. **For each re-embedded index, write a NEW manifest with a NEW corpus_sha8** even if the source corpus is unchanged — different model = different artifact, period.
5. **Keep the old index files for 30 days** under `indices/<name>/openai__text-embedding-ada-002__1536/_archived/`. Roll back if production answers degrade. (Anti-pattern: deleting the old index "to save space" before validating the new one.)
6. **Tag the new app version** only after at least one rep query per re-embedded index passes a regression test (top-3 results overlap with golden set ≥80%).

**结果:** 9 of 14 indices needed code-only migration; 5 needed re-embed. Total cost ~$300 and 1 engineer-day. The discipline of per-index manifests caught two indices that had been silently broken (ada-002 query vector against 3-small index from a botched earlier migration).

**可提取的操作:** **Framework deprecations cascade into per-artifact decisions. The "easy" code migration is rarely the full migration — interrogate every artifact's framework binding (embed model, edit format, tokenizer version) before declaring a deprecation handled.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **Assuming portability across models.** A `prompt.txt` or `compiled.json` with no model in its path or metadata is implicitly "for any model." Empirically, prompts transfer down (big → small) badly and sideways unpredictably (R1 §5). The artifact must encode its LM.

2. **No model in the artifact name/path.** `artifacts/v3.json` is unauditable. `artifacts/rag_synth/openai/gpt-4o-2024-08-06/devset-v3-a8f1c2e9/v3.json` is. Long paths are good; they replace metadata files no one reads.

3. **Pinning to an alias instead of a snapshot.** `gpt-4o`, `claude-3-5-sonnet`, `llama-3-8b-instruct` — all moving targets. Pin `gpt-4o-2024-08-06`, `claude-3-5-sonnet-20241022`, and an HF `revision` SHA respectively.

4. **No regression gate on artifact PRs.** Every artifact replacement is implicitly a behavior change. CI must re-run held-out test and compare to parent artifact. Without this, regressions land silently and surface in production.

5. **Hand-editing compiled JSON.** "Just one little instruction tweak" invalidates the metric-optimality the artifact carries. Either re-compile or don't touch. Pre-commit hook should enforce.

6. **Skipping the parent_artifact pointer.** Without lineage, you cannot answer "what was the last known-good artifact" during an incident. Every REGISTRY entry must reference its predecessor (or `null` for the very first).

7. **Single artifact, multiple LMs.** Production hits two LMs (e.g. failover routing GPT-4o ↔ Sonnet 3.5). Each LM needs its OWN artifact, with its own swap-tested score. A "shared" artifact biased toward whichever LM compiled it.

8. **No dataset hash.** Two "v3 devset" files that differ by 50 examples produce different artifacts that look identical in the registry. `dataset_sha256_8` in the path makes drift visible.

9. **Forgetting framework version.** A DSPy 2.4 artifact loaded by DSPy 2.6 may silently behave differently due to module-level changes. `dspy_version` in REGISTRY enables targeted rollback.

10. **Deleting old artifacts on new compile.** Disk is cheap, history is precious. Keep old artifacts checked in. Production deploys read git tags, not HEAD — the old artifact stays reachable for rollback.

11. **Treating LangChain Hub as the lifecycle.** Hub is a viewer + diff tool. It doesn't bind to model, dataset, or run a regression gate. Pair with REGISTRY.jsonl or MLflow (R1 §8).

12. **Promoting an artifact without swap-test on the actual production LM.** "It scored well in compile" — but compile was against the same LM that production uses, right? Not always: the optimizer LM can differ from the task LM (dspy-sop §4.4). Swap-test against the actual production LM before tagging.

### Boundaries (when this SOP is overkill)

- **One artifact, one LM, never changes.** A research demo or proof-of-concept can use `compiled.save("v1.json")` flat. Adopt this SOP when adding the second artifact or moving to a managed environment.
- **Pure inference-time prompts with no compile loop.** A system prompt manually authored and unchanging is just a config file — version it normally, but the regression gate and swap-test machinery are not load-bearing until the prompt is metric-optimized.
- **Provider with built-in artifact registry.** OpenAI's Prompt Library, Anthropic's Workbench saved prompts, vendor-managed RAG — let the vendor own the lifecycle. This SOP is for org-controlled artifacts.
- **Framework changes more often than the LM.** If you re-write the program every week, the compile artifact has no shelf life and the registry overhead exceeds the audit value. Stabilize the program first.

---

## 7. 跨框架对照 (Cross-framework comparison)

How four ecosystems handle the per-model artifact problem.

### DSPy — `save_program` is the artifact

- **What it stores:** instructions per predictor, bootstrapped demos, signature shapes (for whole-program save).
- **What it does NOT store:** the LM identity, the dataset, the metric, the run cost. These must be added by the SOP (REGISTRY.jsonl).
- **Two save modes:**
  - `compiled.save("v1.json")` — state JSON, needs source Python at load. Use for code-review-friendly diffs.
  - `compiled.save("v1/", save_program=True)` — pickled program + state. Use for portability across source-tree refactors.
- **Reload:** `program_cls().load("v1.json")` requires the Python class import; `dspy.load("v1/")` for whole-program.
- **Versioning practice:** DSPy docs leave it to the user. The dspy-sop SKILL Case B says "Treat the compiled program as a (program × LM) pair" but doesn't prescribe directory layout — this SOP fills that gap.

### LangChain Hub — versioned text templates

- **What it stores:** prompt template text, partial variables, model name as a hint (not enforced).
- **What it does NOT store:** evaluation scores, dataset binding, recompile lineage.
- **API:**
  ```python
  from langchain import hub
  hub.push("user/rag-qa", prompt, parent_commit_hash=last)
  hub.pull("user/rag-qa:v3")
  ```
- **Versioning practice:** Hub gives you a UI diff between versions but not a regression gate or model-pinning enforcement. Use Hub as the *viewer*; keep your local REGISTRY.jsonl as the *gate*.
- **Limitation:** Hub is org-shared; per-model variants pollute the namespace unless you name them `rag-qa-gpt4o` / `rag-qa-sonnet35`.

### Manual jsonl + git — lightweight, fully local

- **What it stores:** whatever you put in REGISTRY.jsonl. Recipe 1 schema (R2) covers model, dataset, metric, cost, lineage.
- **Strengths:** zero infra, fully grep-able, git-blame-able. Works for solo developers and small teams.
- **Limitations:** no UI, no multi-tenant access control, no eval-vs-baseline comparison out of the box (must script). Scales to ~50 artifacts before the jsonl gets unwieldy.
- **Decision rule:** start here. Migrate to MLflow when you exceed 50 artifacts OR have >5 contributing developers OR need a stage-promotion UI.

### MLflow Model Registry — org-scale

- **What it stores:** model artifact (pickled DSPy program via `mlflow.dspy.log_model`), full param/metric history per run, signature, version with explicit Stage labels (None / Staging / Production / Archived).
- **What it does NOT store natively:** dataset hash binding (must add as a param), provider-snapshot-deprecation calendar (add via tags).
- **API:**
  ```python
  with mlflow.start_run():
      mlflow.log_params({"model": MODEL, "dataset_sha8": SHA8})
      mlflow.log_metrics({"dev_score": d, "test_score": t})
      mlflow.dspy.log_model(compiled, "program",
                            registered_model_name=f"rag_synth-{MODEL}")
  client.transition_model_version_stage(
      name=f"rag_synth-{MODEL}", version=v, stage="Production")
  ```
- **Strengths:** UI, RBAC, multi-team. Promotion via stage labels replaces git tags.
- **Limitations:** infra overhead (Postgres + artifact store). Overkill for solo.

### Aider model defaults — config artifacts, not data artifacts

- **What it stores:** `.aider.conf.yml` per-model edit format, params (R2 Recipe 6).
- **Versioning practice:** This SOP applied to config: pre-commit hook + bench delta gate on changes.
- **Lesson:** "artifact" generalizes beyond compiled JSON. Aider's edit-format choice IS a per-model artifact even though it's a string in YAML. Treat it like one.

### LlamaIndex index files — embedding-bound artifacts

- **What it stores:** vector store, doc store, index store — all bound to one specific embedding model + dimension.
- **Versioning practice:** R2 Recipe 7. Per-index `manifest.json` with `embed_model`, `dim`, `corpus_sha8`. Loader refuses to query if `Settings.embed_model` at runtime mismatches manifest.
- **Lesson:** embedding model is part of index identity, identical in structure to LM being part of compiled-prompt identity. Same SOP applies.

### Summary table

| Layer | Native artifact mechanism | Gap this SOP fills |
|---|---|---|
| DSPy | `save_program` (JSON or pickled dir) | Adds LM/dataset/metric binding, registry, gate |
| LangChain Hub | Versioned text templates with diff UI | Adds model-pinning enforcement, eval gate |
| Manual jsonl + git | None — this SOP IS the recipe | Provides Recipe 1 schema and gate scripts |
| MLflow Model Registry | Stages, signatures, run history | Adds dataset_sha8 convention, deprecation scan |
| Aider | Per-model edit-format defaults in code | Adds change-gate (re-run bench on edit-format change) |
| LlamaIndex | Settings + index files | Adds manifest-based loader guard, embed-model in path |

---

## Quick-reference appendix

### Filesystem layout (canonical)

```
artifacts/
├── REGISTRY.jsonl
└── <program>/
    └── <provider>/
        └── <model-snapshot>/        # e.g. gpt-4o-2024-08-06
            └── <dataset>-<sha8>/    # e.g. devset-v3-a8f1c2e9
                ├── v1.json
                ├── v2.json
                └── v3.json
```

### REGISTRY.jsonl one-liner

```jsonl
{"path":"...","sha256":"...","program":"...","provider":"...","model":"...","dataset":"...","dataset_sha256_8":"...","optimizer":"...","optimizer_config":{...},"metric":"...","dev_score":0.0,"test_score":0.0,"cost_usd":0.0,"wall_seconds":0,"dspy_version":"...","compiled_at":"...","commit":"...","parent_artifact":null}
```

### Pre-commit hooks (required)

- `no-edit-artifact`: rejects any change under `artifacts/**` that doesn't also append to `REGISTRY.jsonl`.
- `no-alias-pin`: scans Python source for `model="gpt-4o"`, `model="claude-3-5-sonnet"` etc. with no date suffix; fails.
- `no-deprecated-pin`: scans for snapshots within 90 days of deprecation per `scripts/deprecation_table.py`; fails without override label.

### CI gates (required)

- `artifact-regression`: re-run held-out test on new artifact + parent; fail if Δ < −2 points.
- `swap-test-on-snapshot-change`: when a new provider snapshot is announced (via webhook or scheduled scan), open a PR running OP-4 against affected artifacts.

### Decision tree

```
New compile? ──► Stage 1-3 (compile, version, gate)
   │
New snapshot from provider? ──► Stage 4 swap-test
   │   ├── |Δ| ≤ 2 pts ──► tag transferable; ship
   │   └── |Δ| > 2 pts ──► Stage 5 recompile
   │
Framework deprecation? ──► R2 Recipe 7 pattern: list artifacts, bucket by binding, migrate per-artifact
   │
Canary score drift on stable snapshot? ──► Case B path: recompile against same snapshot
   │
Family swap (GPT-4o ↔ Sonnet)? ──► Stage 5 recompile, always; swap-test gives the magnitude, not the decision
```

### Key references

- DSPy compiled-prompt model dependency: `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md` Dilemma Case B.
- Aider per-model edit format defaults: `/Users/5imp1ex/Desktop/Skill-Workplace/output/aider-sop-skill/SKILL.md` §"edit format" table.
- LlamaIndex `ServiceContext` → `Settings` deprecation: `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md` §4.4 / anti-pattern A4.
- DSPy save_program API: dspy.ai/tutorials/saving/.
- MLflow Model Registry: mlflow.org/docs/latest/model-registry.html.
- OpenAI deprecation policy: platform.openai.com/docs/deprecations.
- Anthropic model deprecations: docs.anthropic.com/en/docs/about-claude/model-deprecations.
- This SOP's reference files: `references/R1-source-evidence.md`, `references/R2-versioning-recipes.md`.
