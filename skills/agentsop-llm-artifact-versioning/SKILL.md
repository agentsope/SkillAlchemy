---
name: agentsop-llm-artifact-versioning
version: 0.1.0
description: >-
  Enhancement overlay — version the WHOLE deployable LLM-app artifact as one bundle: prompts
  + compiled programs + model snapshot pins + retrieval config + eval-set version, versioned
  together so a deploy is reproducible and rollback is atomic. Activate when preparing to
  deploy an LLM app, when asking "what exactly is running in prod right now?", when a deploy
  must be reproducible months later, or when an incident needs a clean rollback. The core
  reframe: an LLM app artifact is NOT an ML model — it is a manifest over many
  independently-mutable parts, not one weights file. Do NOT activate for one-off prompt
  edits with no deploy, for a single-component demo, or where a vendor owns the whole prompt
  lifecycle. For versioning ONE compiled prompt use [[agentsop-per-model-artifacts]]; for
  the CI comparison mechanism use [[agentsop-regression-gate]]. Search keywords: prompt
  versioning, reproducible deploy, what is running in prod, rollback LLM app, model pinning,
  prompt registry, version prompts and config.
---

# Versioned, Reproducible LLM Artifact — Overlay SOP

> *"Prompts are effectively the weights of an LLM application."*
> — DSPy core philosophy [arxiv.org/abs/2310.03714] (R1 §1)
>
> *"Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the
> artifact — recompile."*
> — dspy-sop SKILL, Dilemma Case B (R1 §2)

This is an **enhancement overlay**, not a framework SOP. It sits on top of whatever stack you
use (DSPy, LangChain, raw API) and adds one discipline: **define, pin, and version the entire
deployable bundle as a unit.** It is the broad sibling of [[agentsop-per-model-artifacts]] — that skill
versions one compiled prompt; this one versions everything that ships together.

---

## 1. 何时激活 (When to activate)

Activate when **any** of these appears in the user's intent, codebase, or workflow:

| Trigger | Signal |
|---|---|
| Preparing to deploy | "ship this to prod", a `Dockerfile`/`deploy.yaml`/serving entrypoint wrapping an LLM app, a release checklist |
| "What is running in prod?" | Nobody can name the exact prompt text + model snapshot + retriever config currently serving traffic |
| Reproducibility need | "reproduce the deploy from last quarter", an audit, a regulator asking what produced an output |
| Rollback need | Incident: prod behavior changed and the team needs the last known-good *combination* of components back |
| Drift symptoms | Score moved, no code change merged; or "we updated the prompt but forgot which model it was tuned for" |
| Multi-component apps | RAG + reranker + synthesizer + judge, each naming its own model/config, none bundled |
| Cross-skill bridges | DSPy `save_program` produced a compiled program → it is *one component* of the bundle; pin the rest. Per-prompt lifecycle handled by [[agentsop-per-model-artifacts]] → wrap as a bundle component here. |

**Do NOT activate** when:
- One-off prompt edit with no deploy and no reproduction requirement — just edit and run.
- A single-component proof-of-concept where there is exactly one prompt, one model, no
  retrieval, and it will never be reproduced. Flat `v1.json` is fine.
- A vendor owns the whole lifecycle (OpenAI Prompt Library, Anthropic Workbench managed
  prompts, fully vendor-managed RAG) — let them version it.
- The team rewrites the app daily during exploration — bundle versioning has no shelf life
  until the app shape stabilizes (same boundary as dspy-sop "signature still changing").

---

## 2. 核心心智模型 (Core mental model)

### An LLM app artifact ≠ an ML model

The single most common mistake is reasoning about an LLM app the way you reason about a
trained model. They are not the same shape.

| ML model | LLM app artifact |
|---|---|
| One weights file (`.pt`, `.safetensors`) | A **manifest** over many parts |
| Identity = file hash | Identity = hash of the *whole bundle* |
| Mutates only on retrain | Each part mutates independently and silently |
| Versioned by a model registry | Versioned by a bundle manifest + tag |

The deployable artifact is:

```
            ┌──────────────── DEPLOYABLE BUNDLE (one tag) ────────────────┐
            │                                                             │
  prompts       compiled        model pins        retrieval       eval-set
  (text +       programs        (snapshot id      config          version
   hashes)      (program.json)   per call site)   (index ptr,     (sha256)
            │                    embed model,                             │
            │                    top_k, reranker)                        │
            │                                                             │
            └── version them TOGETHER, or you can't reproduce a deploy ──┘
```

**The load-bearing claim:** the deployable artifact = prompts + compiled programs + model pins
+ retrieval config + eval-set version. **Version them together or you cannot reproduce a
deploy** — and you cannot roll back without producing a never-tested combination.

### Why "together" is non-negotiable

Each part can change without touching the others (R1 §3, §4, §6):

- A model **alias** rolls forward server-side (`gpt-4o` → new snapshot) — prompt unchanged,
  behavior changed.
- A model **snapshot** gets a silent server-side patch (R1 §4) — pin unchanged, behavior
  changed.
- A retriever knob moves in a dashboard (top_k 5→10) — no commit, behavior changed.
- The eval set gains 50 examples — the "same" score now means something different (R1 §5).

If these are versioned separately, "the deploy" is not a thing you can name. If they are
versioned as one bundle with one id, the deploy is reproducible and rollback is atomic (R1 §8).

### The registry analogy and its limit (R1 §7)

MLflow's Model Registry gives the right *primitives*: versioning, stage transitions
(Staging/Production/Archived), reproduce-from-config, compare-versions
[`~/.claude/skills/mlflow/SKILL.md`]. Borrow those primitives. But the analogy breaks on
**heterogeneity**: a registry versions one model + signature + run; the LLM bundle is a
*composite* of many models, prompts, configs, and an eval set. You can log the manifest into
MLflow as one "model", but the registry was built for the single-weights case. The overlay
exists to make the composite explicit.

---

## 3. SOP 工作流 (SOP workflow)

Five steps. Each has an exit criterion. The output is one versioned, reproducible bundle.

### Step 1 — Enumerate artifact components

List every component that affects behavior at runtime. Nothing implicit:
- Every prompt / system-prompt file (path + content hash).
- Every compiled program (`program.json` or `save_program` dir + sha).
- Every model call site (router, synthesizer, reranker, judge) and its model.
- Retrieval config: which index, its embed model + dim, top_k, reranker on/off, chunking.
- The eval set that produced the bundle's scores.
- Framework versions (dspy, langchain, llama-index, python).

**Exit:** a written component inventory — no "and whatever the dashboard says" gaps.

### Step 2 — Pin each component

- Models: dated **snapshot**, never an alias, never `latest`, at every call site (OP-2,
  R1 §3). Cross-link [[agentsop-per-model-artifacts]] for per-prompt swap-test detail.
- Prompts: content sha256, committed to VCS.
- Compiled programs: path + sha; prefer `save_program=True` for portability (R1 §2).
- Config: move every knob into version-controlled config (OP-3, config-as-code). Dashboards
  are not artifacts.
- Eval set: sha256 over canonical eval bytes (R1 §5).

**Exit:** every component has an immutable identifier. Grep for aliases finds none.

### Step 3 — Bundle + version

Write a single `manifest.<version>.json` (OP-1) referencing every pinned component, and assign
one monotonic bundle id (OP-5). Components keep their own internal versions; the **bundle** has
one id production deploys atomically.

**Exit:** `deploy/manifest.v<n>.json` exists and a `git tag deploy/v<n>` points to it.

### Step 4 — Tie to eval-set version

Record `eval_set_sha` + scores in the manifest (OP-4). A bundle without a pinned eval set has
no reproducible score. Cross-link [[agentsop-regression-gate]]: the gate re-runs **this exact eval set**
on the new bundle vs the parent bundle at PR time, and fails the PR on regression.

**Exit:** manifest shows `eval_set_sha` and the scores measured on it; the regression gate is
wired to that eval-set version.

### Step 5 — Enable rollback

Production deploy reads the **bundle tag**, not HEAD (OP-6, R1 §8). Keep prior bundles tagged
and reachable. Rollback = re-point the deploy to the previous tag, which restores
prompts + model + config + index pointer **together** — never a partial revert.

**Exit:** one-command rollback (`deploy deploy/v<n-1>`) restores a known-good combination.

### Maintenance loop

- Canary re-run the eval set against pinned snapshots periodically — catches silent
  server-side drift the snapshot pin cannot (R1 §4).
- On any provider deprecation, re-bundle (the per-prompt swap-test lives in
  [[agentsop-per-model-artifacts]]; the bundle re-version lives here).

---

## 4. 操作模型 (Trigger / Action / Output / Evidence)

### OP-1 — Artifact manifest

| | |
|---|---|
| **Trigger** | Preparing to deploy; "what exactly is running in prod?" |
| **Action** | Write one `deploy/manifest.<version>.json` enumerating every behavior-affecting component with an immutable id (prompt hashes, compiled-program path+sha, model snapshots per call site, retrieval config, eval_set_sha, framework versions). The manifest IS the deployable unit. |
| **Output** | One grep-able answer to "what is in prod" — the bundle id resolves all components. |
| **Evidence** | R1 §1 (LLM app ≠ one weights file); R1 §7 (registry analogy + limit); [[agentsop-per-model-artifacts]] extends the (program × LM × dataset) triple to the full bundle. |

### OP-2 — Model-snapshot pinning

| | |
|---|---|
| **Trigger** | Any call site naming a model; CI sees an alias or `latest`. |
| **Action** | Pin dated snapshots everywhere (`gpt-4o-2024-08-06`, `claude-3-7-sonnet-20250219`); record each call site in the manifest. See [[agentsop-per-model-artifacts]] OP-2 for the per-prompt detail. |
| **Output** | `manifest.models[]` with provider/snapshot per call site; zero aliases. |
| **Evidence** | R1 §3: "the snapshot, not the alias, is the identity"; Anthropic does not roll aliases, OpenAI does — both bite silently. |

### OP-3 — Config-as-code

| | |
|---|---|
| **Trigger** | A behavior knob lives in a dashboard, env var, or notebook cell. |
| **Action** | Move every knob (top_k, chunk size, reranker on/off, temperature, system-prompt path, index pointer) into version-controlled config; manifest references `config_sha`. |
| **Output** | `config/` under git; nothing behavioral outside VCS. |
| **Evidence** | R1 §6: Aider edit-format and LlamaIndex Settings are config artifacts too — "'artifact' generalizes beyond compiled JSON." |

### OP-4 — Eval-set linkage

| | |
|---|---|
| **Trigger** | Bundling a version; about to tag a release. |
| **Action** | Record `eval_set_sha` (sha256 of canonical eval bytes) + the scores measured on it. The regression gate ([[agentsop-regression-gate]]) re-runs THIS eval set on new bundle vs parent. |
| **Output** | manifest `eval_set_sha` + scores; reproducible "this bundle scored X on eval-set Y." |
| **Evidence** | R1 §5: a score is meaningful only relative to a fixed eval set; dspy-sop dev-set sizing; per-model-artifacts dataset_sha256_8. |

### OP-5 — Bundle-and-version

| | |
|---|---|
| **Trigger** | All components pinned; ready to ship. |
| **Action** | Assign one monotonic bundle id (`git tag deploy/v<n>` → `manifest.v<n>.json`). Components keep internal versions; the bundle deploys atomically. |
| **Output** | `deploy/v7` tag resolving the whole manifest. |
| **Evidence** | R1 §8; per-model-artifacts OP-10 (per-prompt tag) elevated to a whole-bundle tag; MLflow stage-promotion analogy (R1 §7). |

### OP-6 — Rollback recipe

| | |
|---|---|
| **Trigger** | Prod incident; need last known-good behavior. |
| **Action** | Deploy reads the bundle tag, not HEAD. Rollback = re-point to the previous tag (`git checkout deploy/v6`), restoring prompts + model + config + index pointer together. |
| **Output** | One-command atomic rollback; no "prompt reverted but model didn't." |
| **Evidence** | R1 §8: deploy reads the tag; the bundle tag makes the unit the whole combination, not one part. |

### OP-7 — Component-drift audit (supporting)

| | |
|---|---|
| **Trigger** | Score regressed; need a root-cause class. |
| **Action** | Diff manifest vN vs vN-1 field-by-field: prompt_sha → prompt drift; model snapshot → model drift; config_sha → config drift; eval_set_sha → apples-vs-oranges; index pointer → retrieval drift. |
| **Output** | Root-cause class from a manifest diff, before re-running anything. |
| **Evidence** | per-model-artifacts §4.4 lineage ops (classify dataset/config/framework/environment drift). |

### OP-8 — Retrieval-config binding (supporting)

| | |
|---|---|
| **Trigger** | App uses RAG; index built with a specific embedding model. |
| **Action** | Pin the index pointer + embed model + dim in the manifest; loader refuses to start if runtime embed model ≠ manifest embed model. |
| **Output** | `manifest.retrieval = {index_path, embed_model, dim, corpus_sha8, top_k, reranker}`. |
| **Evidence** | R1 §6; per-model-artifacts Case C: embedding model is part of index identity; mixing spaces is the worst-case silent failure. |

---

## 5. 困境决策案例 (Dilemma cases)

### Case A — "Model provider silently updates: output drift with no version bump"

**困境 (Dilemma):** A RAG app has shipped on `gpt-4o-2024-08-06` for the synthesizer. No code,
prompt, config, or model pin has changed in three months — every component's id in the
manifest is identical. Yet the quarterly canary on the pinned eval set drops from 78% to 73%.
Support escalations are rising. What changed, and what is the fix when *nothing in the bundle
moved*?

**约束 (Constraints):**
- The snapshot string is unchanged — the pin did its job.
- OpenAI's policy is "snapshots are stable," but server-side safety/throughput/hallucination
  patches ship without a snapshot bump (R1 §4).
- Reverting the model is impossible: the canary IS the latest behavior on the same snapshot.
- The eval-set version is pinned, so the score drop is a true behavior shift, not a
  measurement artifact (OP-4) — apples vs apples.

**决策步骤 (Decision steps):**
1. **Confirm it is drift, not measurement.** Because the manifest pins `eval_set_sha`, the
   73% and the old 78% were measured on the *same* eval set. Rule out apples-vs-oranges first
   (OP-7) — a changed `eval_set_sha` would be the more boring explanation.
2. **Compare sample-output hashes.** Store sample-output hashes per bundle at build time
   (R1 §4); re-run the same sample inputs and diff. Divergence with an unchanged snapshot
   confirms silent server-side drift.
3. **Re-bundle, do not edit in place.** Recompile/re-tune the prompt component against the new
   server behavior (per-prompt mechanics live in [[agentsop-per-model-artifacts]]), then mint a **new
   bundle** `deploy/v<n+1>` even though the model snapshot string is unchanged. The
   `built_at` field carries the temporal lineage the snapshot string cannot.
4. **Gate the new bundle.** [[agentsop-regression-gate]] re-runs the pinned eval set on v(n+1) vs the
   v(n) parent; merge only if it recovers above the gate threshold.
5. **Tighten the canary cadence** to weekly for 30 days post-incident; revert to quarterly
   when stable. The canary against the pinned eval set is the *only* true contract with the
   provider (R1 §4) — the pin alone is necessary but not sufficient.

**结果 (Outcome):** Re-bundling recovers to ~79%. The pin protected against alias rollover and
most drift; the eval-set-linked canary caught what the pin missed. Crucially, the bundle id
incremented even though no human-authored component "changed" — the *behavior* changed, so the
*bundle* changed.

**可提取的操作 (Extractable operation):** **A snapshot pin is necessary but not sufficient.
Tie every bundle to a pinned eval set and canary against it; when behavior drifts on a stable
snapshot, mint a new bundle version rather than mutating the live one.**

---

### Case B — "Prompt change shipped without an eval — and now we can't reproduce or roll back cleanly"

**困境:** Under deadline pressure, an engineer edits the synthesizer system prompt directly in
the running config to fix one bad answer, redeploys, and moves on. No new bundle, no eval run,
no tag. A week later a *different* regression appears in prod, and a model-snapshot rollover
also landed in the same window. Now: which prompt is live? Was it ever evaluated? Can we roll
back to before the prompt edit without also reverting unrelated changes?

**约束:**
- The live prompt no longer matches any committed bundle manifest — the manifest is stale.
- The model alias rolled forward in the same window, so even "revert the prompt" leaves an
  untested (old-prompt × new-model) combination.
- No eval was run on the edited prompt, so there is no score to compare against — the
  regression gate was bypassed entirely.
- Customers are affected; time pressure is real again.

**决策步骤:**
1. **Stop the bleeding with a bundle rollback, not a prompt rollback.** Deploy the last
   *tagged* bundle `deploy/v<n>` (OP-6, R1 §8). Because the bundle pins prompt **and** model
   **and** config together, this restores a known-good *combination* — it does not produce the
   untested (old-prompt × new-model) Frankenstein that a prompt-only revert would.
2. **Reconstruct what was live.** The ad-hoc prompt edit is the root cause of the
   reproducibility loss: behavior was changed outside the bundle. Capture the edited prompt's
   content hash now so it is at least recoverable, then delete the out-of-band path.
3. **Re-introduce the fix the right way.** Put the prompt fix into VCS (config-as-code, OP-3),
   bump the model pin to the dated snapshot it will actually run on (OP-2), and build a new
   bundle `deploy/v<n+1>`.
4. **Run the gate.** [[agentsop-regression-gate]] runs the pinned eval set on v(n+1) vs the parent. The
   original one-bad-answer case should be in the eval set now (turn the incident into a test).
   Merge only on pass.
5. **Add a pre-deploy guard.** Refuse to deploy if the live prompt hashes do not match the
   tagged bundle's manifest — converts "someone edited prod directly" from a silent
   reproducibility hole into a deploy-time error.

**结果:** Rollback restores service immediately because the bundle is atomic. The fix re-lands
behind the gate. The lesson the team internalizes: a prompt change shipped without an
eval-linked bundle is invisible to rollback and reproduction — it is exactly the failure mode
this overlay exists to prevent.

**可提取的操作:** **No behavior-affecting change ships outside a versioned, eval-linked bundle.
Roll back by bundle tag (atomic) — never by reverting one component, which yields untested
combinations.**

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

### Anti-patterns

1. **Versioning code but not prompts/configs.** Git tracks the Python; the prompt text lives
   in a dashboard and the model id in an env var. The "deploy" is then unreproducible — the
   committed code does not determine behavior. Prompts are weights (R1 §1); version them.
2. **`"latest"` (or any alias) model pin.** `gpt-4o`, `claude-3-5-sonnet`, `latest` are moving
   targets that change behavior with no version bump (R1 §3). Pin dated snapshots at every
   call site (OP-2).
3. **No eval-set linkage.** A bundle that records a score but not the eval set that produced it
   cannot be compared to its successor — "score went up" across two eval sets is meaningless
   (R1 §5, OP-4). Pin `eval_set_sha`.
4. **Per-component tags instead of one bundle tag.** Tagging prompts, models, and configs
   separately makes rollback non-atomic — you revert one part and ship a never-tested
   combination (R1 §8, OP-6). One bundle, one tag.
5. **Editing live prod components out of band.** A "quick" dashboard prompt edit (Case B)
   breaks reproducibility and rollback silently. All behavior changes flow through a new
   bundle.
6. **Treating the bundle like a single ML model.** Logging just the compiled program and
   calling it "the artifact" drops the model pins, retrieval config, and eval set. The artifact
   is a composite (R1 §7) — `save_program` captures one component, not the bundle (R1 §2).
7. **Retrieval config left implicit.** Index pointer, embed model, and top_k unbundled means a
   re-embed or a knob change silently alters answers (OP-8, R1 §6). Pin them in the manifest.
8. **Deleting old bundles to "save space."** Disk is cheap; rollback targets are precious.
   Keep prior bundle tags reachable.

### Boundaries (when this overlay is overkill)

- **Single-component PoC.** One prompt, one model, no retrieval, never reproduced — a flat
  `v1.json` is enough. Adopt this overlay at the second component or the first real deploy.
- **Vendor owns the lifecycle.** OpenAI Prompt Library / Anthropic Workbench / managed RAG —
  let the vendor version it.
- **Pre-stabilization exploration.** If the app shape changes daily, bundle versioning has no
  shelf life yet — stabilize first (same boundary as dspy-sop).
- **Versioning ONE compiled prompt.** Use [[agentsop-per-model-artifacts]] directly; this overlay only
  adds value once there are multiple components to bundle.
- **The CI comparison mechanism itself.** This overlay *requires* a regression gate but does
  not implement it — see [[agentsop-regression-gate]].

---

## 7. 跨框架对照 (Cross-framework comparison)

How four mechanisms handle (or fail to handle) the **whole-bundle** versioning problem. None of
them natively version the composite; each covers a slice.

### DSPy `save_program` — one component, not the bundle

- **Stores:** per-predictor instructions, bootstrapped demos, signature shapes (R1 §2)
  [dspy.ai/tutorials/saving/].
- **Does NOT store:** model identity, dataset, metric, retrieval config, eval-set version.
- **Role in the bundle:** `program.json` (or a `save_program=True` dir) is *one* component the
  manifest references. The overlay pins the rest. Per-prompt lifecycle of this component →
  [[agentsop-per-model-artifacts]].

### LangChain Hub — versioned text templates, model as a hint

- **Stores:** prompt template text, partial variables, model name as a non-enforced hint.
- **Does NOT store:** eval scores, dataset binding, retrieval config, recompile lineage.
- **Role in the bundle:** a viewer/diff tool for the prompt component. It does not pin a model,
  bind an eval set, or run a gate. Use Hub as the prompt *viewer*; the bundle manifest is the
  *source of truth*. `hub.pull("user/rag-qa:v3")` resolves a prompt version, not a deploy.

### MLflow Model Registry — the closest analogy, built for one model

- **Stores:** pickled model/program, param + metric history per run, signature, versions with
  explicit **Stage** labels (None/Staging/Production/Archived)
  [`~/.claude/skills/mlflow/SKILL.md`, mlflow.org/docs/latest/model-registry.html].
- **Does NOT store natively:** the heterogeneity — many model snapshots, multiple prompts,
  retrieval config, eval-set hash (add via params/tags).
- **Role in the bundle:** borrow the *primitives* — versioning, stage promotion, reproduce,
  compare (R1 §7). Press it into service by logging the whole manifest as one "model" with
  components as params/artifacts. The gap: it was built for the single-weights case; the LLM
  bundle is a composite. The analogy holds for versioning + promotion + rollback, not for the
  artifact's shape.

### Plain git + manifest — the lightweight default

- **Stores:** whatever you put in `deploy/manifest.<version>.json` — prompt hashes, compiled
  program shas, model snapshots per call site, retrieval config, `eval_set_sha`, framework
  versions.
- **Strengths:** zero infra, fully grep-able and git-blame-able; the bundle tag (`deploy/v<n>`)
  gives atomic deploy + rollback (R1 §8); the regression gate ([[agentsop-regression-gate]]) wires to
  the pinned eval set in CI.
- **Limitations:** no UI, no RBAC, no built-in compare. Scales to small/medium teams.
- **Decision rule:** start here. Migrate the *registry* layer to MLflow when you exceed team
  scale; keep the manifest discipline regardless.

### Summary

| Mechanism | What it versions | Bundle gap this overlay fills |
|---|---|---|
| DSPy `save_program` | One compiled prompt | Model pins, retrieval config, eval-set, bundling |
| LangChain Hub | Prompt templates (diff UI) | Model pin enforcement, eval linkage, gate, bundling |
| MLflow Registry | One model + signature + run | Composite of many components; eval-set hash; one bundle tag |
| git + manifest | Whatever you list | Nothing — this overlay IS the recipe (manifest + tag + gate) |

### Companion skills

- **[[agentsop-per-model-artifacts]]** — versions ONE compiled prompt as a (program × LM × dataset)
  triple. This overlay wraps that as one component of the whole bundle. Use it for per-prompt
  swap-tests, snapshot churn, and dataset-hash discipline.
- **[[agentsop-regression-gate]]** — the CI mechanism that re-runs the pinned eval set on new bundle vs
  parent and fails the PR on regression. This overlay *requires* it (Step 4, OP-4) but does not
  implement it.
- **dspy-sop** — the compile loop that produces the compiled-program component.

---

## Quick-reference appendix

### Manifest skeleton

```jsonc
{
  "bundle_version": "v7", "built_at": "...", "commit": "<git-sha>", "parent_bundle": "v6",
  "prompts": [{"name": "synth_system", "path": "prompts/synth_system.txt", "sha256": "..."}],
  "compiled_programs": [{"name": "rag_synth", "path": "artifacts/rag_synth/.../v3.json", "sha256": "..."}],
  "models": [
    {"call_site": "router",      "provider": "openai",    "snapshot": "gpt-4o-mini-2024-07-18"},
    {"call_site": "synthesizer", "provider": "openai",    "snapshot": "gpt-4o-2024-08-06"},
    {"call_site": "judge",       "provider": "anthropic", "snapshot": "claude-3-7-sonnet-20250219"}
  ],
  "retrieval": {"index_path": "indices/kb/.../<corpus-sha8>/", "embed_model": "text-embedding-3-small",
                "dim": 1536, "top_k": 8, "reranker": "bge-reranker-v2", "corpus_sha8": "a8f1c2e9"},
  "eval_set_sha": "9c3f...", "scores": {"dev": 0.81, "test": 0.79},
  "frameworks": {"dspy": "2.6.1", "python": "3.11.8"}
}
```

### Decision tree

```
Preparing to deploy / "what's in prod?" ─► Step 1-3 (enumerate, pin, bundle)
   │
Score regressed, nothing committed changed? ─► Case A: confirm eval_set unchanged,
   │                                            check sample-hashes, re-bundle, gate
Prompt edited live without eval? ──────────► Case B: roll back by BUNDLE tag (atomic),
   │                                            re-land fix behind the gate
Need rollback? ─────────────────────────────► OP-6: deploy previous bundle tag
   │
Only ONE compiled prompt to version? ───────► use [[agentsop-per-model-artifacts]] instead
Need the CI comparison itself? ─────────────► use [[agentsop-regression-gate]]
```

### Pre-deploy guards (recommended)

- `no-alias-pin`: fail if any manifest model id lacks a date suffix or is `latest` (OP-2).
- `manifest-matches-live`: fail deploy if live component hashes ≠ tagged bundle (Case B).
- `eval-set-pinned`: fail bundle if `eval_set_sha` missing or scores recorded without it (OP-4).
- `regression-gate`: re-run pinned eval set on new bundle vs parent — see [[agentsop-regression-gate]].

### Key references

- DSPy save_program / (program × LM × data) triple: `dspy-sop-skill/SKILL.md` (R1 §1, §2).
- Per-prompt artifact lifecycle, snapshot pinning, silent drift, config-as-artifact:
  `d-per-model-artifacts-skill/SKILL.md` (R1 §3–§6).
- Registry analogy (versioning, stage transitions, reproduce): `~/.claude/skills/mlflow/SKILL.md` (R1 §7).
- OpenAI deprecations: platform.openai.com/docs/deprecations
- Anthropic deprecations: docs.anthropic.com/en/docs/about-claude/model-deprecations
- This skill's evidence file: `references/R1-source-evidence.md`.
