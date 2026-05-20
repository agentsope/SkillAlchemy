# R1 — Source evidence: versioned, reproducible LLM artifact

Evidence base for the `llm-artifact-versioning` enhancement-overlay skill. Every load-bearing
claim in `SKILL.md` traces to a quote here. This overlay is **broader** than its sibling
`per-model-artifacts`: that skill versions a single compiled prompt; this one versions the
**whole deployable bundle** (prompts + compiled programs + model pins + retrieval config +
eval-set version).

---

## §1 — "Prompts are the weights" (the foundational reframe)

> *"Prompts are effectively the weights of an LLM application."*
> — DSPy core philosophy [arxiv.org/abs/2310.03714]

> *"The prompt string is not the artifact you ship — the compiled program (a JSON of
> demonstrations + instructions + structural choices) is. You ship `program.json`, not a
> `.txt` prompt."*
> — dspy-sop SKILL §2, claim 1
> [`/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md` lines 58]

**Overlay consequence:** if prompts are weights, then an LLM app is more like a *trained
pipeline* than a single weights file. The deployable thing is a **set** of weights-like
components, not one. That is the core distinction this skill encodes:
**an LLM app artifact ≠ an ML model.** An ML model is one `.pt`/`.safetensors` file. An LLM
app artifact is a manifest over heterogeneous, separately-mutable parts.

---

## §2 — DSPy `save_program` and the (program × LM × data) triple

DSPy's two save modes [dspy.ai/tutorials/saving/], from dspy-sop SKILL §3 step 11 and
Quick-reference appendix:

- `compiled.save("v1.json")` — state JSON; needs the source Python at load time. Code-review
  friendly diffs.
- `compiled.save("./v1/", save_program=True)` — pickled whole program + state + metadata;
  portable across source-tree refactors (until Python/DSPy version mismatch).

> *"Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the
> artifact — recompile."*
> — dspy-sop SKILL Dilemma Case B, extractable operation
> [`dspy-sop-skill/SKILL.md` line 195]

**What DSPy stores vs. does NOT store** (dspy-sop appendix "Anatomy of a compiled
`program.json`", lines 379–411):
- Stores: per-predictor instructions, bootstrapped demos, signature shapes.
- Does NOT store: the LM identity, the dataset, the metric, the run cost, the retrieval
  config, the eval-set version.

**Overlay consequence:** `save_program` captures *one* component (the compiled prompt). The
deployable bundle needs all the others bolted on by a manifest. This is exactly the gap the
sibling `per-model-artifacts` fills for one prompt — and the gap this overlay fills for the
whole app.

---

## §3 — The snapshot, not the alias, is the identity

From per-model-artifacts SKILL §2 claim 2
[`/Users/5imp1ex/Desktop/Skill-Workplace/output/d-per-model-artifacts-skill/SKILL.md` lines 64]:

> *"`gpt-4o` is a moving alias; `gpt-4o-2024-08-06` is an immutable identifier. Pinning to the
> alias means your behavior changes silently when OpenAI rolls the alias forward. Anthropic
> does not even roll aliases — Sonnet 3.5 (`claude-3-5-sonnet-20240620`) and Sonnet 3.5 v2
> (`claude-3-5-sonnet-20241022`) are different models with different behavior; the org that
> pinned the wrong one in 2024-10 ate a regression in 2025-10 when the older one was retired."*

Anti-pattern reference (per-model-artifacts §6 #3): aliases `gpt-4o`, `claude-3-5-sonnet`,
`llama-3-8b-instruct` are all moving targets. The `"latest"` tag is the worst offender.

- OpenAI deprecation policy: platform.openai.com/docs/deprecations
- Anthropic model deprecations: docs.anthropic.com/en/docs/about-claude/model-deprecations

**Overlay consequence:** a deployable bundle may name a model at *several* call sites (a cheap
router model, an expensive synthesizer, a judge). Each must be a dated snapshot in the
manifest. A single `"latest"` anywhere breaks bundle reproducibility.

---

## §4 — Silent provider drift on a stable snapshot

From per-model-artifacts Dilemma Case B
[`d-per-model-artifacts-skill/SKILL.md` lines 216–235]:

> *"OpenAI's policy is 'snapshots are stable' but in practice server-side mitigations (safety,
> hallucination patches, throughput) ship without bumping the snapshot ID."*

Mitigation: store **sample-output hashes** per artifact at compile time; a periodic canary
re-runs the eval set against the pinned snapshot and compares.

> *"The snapshot string is necessary but not sufficient. A periodic canary against held-out
> test data is the only true contract with the model provider."*
> — per-model-artifacts Case B, extractable operation

**Overlay consequence:** the manifest pins the snapshot string, which protects against MOST
drift but not silent server-side patches. The eval-set linkage (OP-4) + a canary is the only
contract. This is why the bundle must tie to an eval-set version, not just a score number.

---

## §5 — Eval set as part of identity (the dataset/eval-set hash)

From dspy-sop SKILL §3 Stage 2 (lines 85–91): documented dev-set sweet spot — **30 examples =
minimum useful, 300 = recommended, 200+ required for MIPROv2.** A score is only meaningful
*relative to a fixed eval set*.

From per-model-artifacts SKILL §2 claim 3 (lines 66):

> *"Two artifacts compiled from the 'same dataset' that turn out to differ by 50 examples
> produce silently different programs. A `sha256` over canonicalized dataset bytes, embedded
> in the artifact path, makes this impossible to confuse."*

**Overlay consequence:** the bundle records `eval_set_sha`. When the regression gate
(see §7, cross-link `[[agentsop-regression-gate]]`) compares bundle vN against vN-1, it MUST run the
same eval-set version, or the comparison is meaningless. "Score went up" across two different
eval sets is not a signal — it is apples vs oranges.

---

## §6 — Config and retrieval bindings are artifacts too

From per-model-artifacts cross-framework §7:

- **Aider** (lines 353–357): `.aider.conf.yml` per-model edit format is a per-model artifact
  "even though it's a string in YAML. Treat it like one." Aider's udiff edit format moved a
  model from 20%→61% on its edit benchmark — a config string with large behavioral weight.
- **LlamaIndex** (lines 359–363): vector store + doc store + index store are "all bound to one
  specific embedding model + dimension." Per-index `manifest.json` with `embed_model`, `dim`,
  `corpus_sha8`; loader refuses to query on mismatch.

> *"'artifact' generalizes beyond compiled JSON."*
> — per-model-artifacts SKILL §7 Aider lesson

**Overlay consequence:** the deployable bundle's `retrieval` block pins the index pointer,
its embed model + dim, top_k, and reranker config. Config-as-code (OP-3): every behavior knob
lives in VCS and is referenced by the manifest. A dashboard slider is not an artifact.

---

## §7 — Registry analogy: MLflow Model Registry

MLflow frontmatter [`~/.claude/skills/mlflow/SKILL.md` lines 2–24]:

> *"Track ML experiments, manage model registry with versioning, deploy models to production,
> and reproduce experiments with MLflow — framework-agnostic ML lifecycle platform."*
> Capabilities listed include: **manage model registry with versioning and stage transitions**,
> **reproduce experiments with project configurations**, **compare model versions**.

From per-model-artifacts SKILL §7 MLflow row:
- Stores: pickled DSPy program via `mlflow.dspy.log_model`, full param/metric history per run,
  signature, version with explicit Stage labels (None / Staging / Production / Archived).
- Does NOT store natively: dataset hash binding (add as a param), provider-snapshot-deprecation
  calendar (add via tags).

**Overlay consequence — the analogy and its limit:** MLflow versions a *model*
(weights + signature + run). The LLM app bundle is a *composite* — many models, prompts,
configs, and an eval set. You can press MLflow into service by logging the whole manifest as
one "model" with the components as params/artifacts, but the registry was built for the
single-weights case. The mental gap MLflow does not close on its own: **the bundle has many
independently-mutable parts**; the registry analogy holds for *versioning + stage promotion +
rollback*, not for the heterogeneity of the artifact.
[mlflow.org/docs/latest/model-registry.html]

---

## §8 — Rollback requires the whole bundle, atomically

From per-model-artifacts OP-10 / SKILL §4.1 (lines 157):

> *"`git tag prompt/<program>/<snapshot>/v<n>`. Deploy reads the tag, not main HEAD. Atomic
> rollback via `git checkout <tag>`."*

**Overlay consequence:** if you tag prompts and models and configs *separately*, rollback is
not atomic — you can revert the prompt but leave the new model pinned, producing a
never-tested combination. The bundle tag (`deploy/v<n>`) resolves ALL component versions at
once, so rollback restores a known-good *combination*, not a Frankenstein.

---

## §9 — Cross-link map

| This skill cites | Sibling skill | Relationship |
|---|---|---|
| Per-prompt artifact identity, snapshot pinning, swap-test | `[[agentsop-per-model-artifacts]]` | NARROWER sibling: versions one compiled prompt. This overlay wraps it as one component of the bundle. |
| Re-running the eval set on new bundle vs parent; fail on Δ | `[[agentsop-regression-gate]]` | The gate is the CI mechanism that enforces eval-set linkage (OP-4) at PR time. |
| Compile loop that produces the compiled-program component | dspy-sop | Upstream producer of one bundle component. |

---

## §10 — Source files

- `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md` — save_program, the
  (program × LM × data) triple, dev-set sizing, compiled-JSON anatomy.
- `/Users/5imp1ex/Desktop/Skill-Workplace/output/d-per-model-artifacts-skill/SKILL.md` —
  sibling Phase D skill; per-prompt artifact lifecycle, snapshot pinning, silent drift,
  config-as-artifact, MLflow comparison.
- `~/.claude/skills/mlflow/SKILL.md` — registry analogy (versioning, stage transitions,
  reproduce experiments).
- OpenAI deprecations: platform.openai.com/docs/deprecations
- Anthropic deprecations: docs.anthropic.com/en/docs/about-claude/model-deprecations
- DSPy save: dspy.ai/tutorials/saving/
- MLflow registry: mlflow.org/docs/latest/model-registry.html
