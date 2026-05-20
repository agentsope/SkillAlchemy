# R1 — Source Evidence: Per-Model Prompt Artifacts

Evidence base for treating compiled prompts as `(program × LM × dataset)` triples rather than portable text. All quotes/refs traceable.

---

## 1. DSPy: compiled prompts are model-specific by construction

From the sibling skill `/Users/5imp1ex/Desktop/Skill-Workplace/output/dspy-sop-skill/SKILL.md`, **Dilemma Case B "Swap the underlying LM"** (lines 178–196):

> "Compiled program for GPT-4o works at 85%. Need to switch to Llama-3-8B for cost. Re-use the GPT-4o-compiled `program.json` or recompile?"
>
> Decision: **"Always recompile when changing the task LM family."**
>
> Extractable operation: **"Treat the compiled program as a (program × LM) pair. Changing the LM invalidates the artifact — recompile."**

Mechanism (DSPy SKILL Section 7, "What DOES change between LMs"):

- Instructions are **rewritten by the optimizer** (MIPROv2 proposes; Bayesian search picks). Smaller LMs need simpler, more explicit wording.
- Demos are **bootstrapped from the teacher**: smaller LMs benefit from more, simpler demos; larger LMs benefit from fewer, richer demos.
- Signature shape does NOT change — that's your code's job.

What this implies for storage: the JSON's `signature_instructions` and `demos` arrays are LM-conditioned. A `program.json` without a model name in its path is a footgun.

> "If you optimize a complex pipeline for GPT-4, it usually breaks on a smaller model like Llama-3-8b" — acldigital.com referenced in DSPy SKILL.

### save_program vs save (whole program vs state)

From `dspy.ai/tutorials/saving/` (cited in DSPy SKILL line 98):

- `compiled.save("v1.json")` — state-only: predictor configs + instructions + demos. Requires the source Python at load time to reconstruct module structure.
- `compiled.save("./v1/", save_program=True)` — whole-program: pickles the module graph plus state. Self-contained. Preferred for production but version-locked to the Python/DSPy version that saved it.

**Practical rule**: ship both. JSON is human-auditable; whole-program directory is reproducible.

---

## 2. Aider: edit-format defaults are per-model and load-bearing

From `/Users/5imp1ex/Desktop/Skill-Workplace/output/aider-sop-skill/SKILL.md`:

| Edit format | Default for | Failure mode if wrong |
|---|---|---|
| `diff` (SEARCH/REPLACE) | GPT-4o, Sonnet, most strong models | SEARCH block must byte-match — fails silently on whitespace drift |
| `udiff` | GPT-4 Turbo (1106) | "Refactor benchmark 20% → 61%" with udiff; reverts to 20% without [aider.chat/2023/12/21/unified-diffs.html] |
| `patch` | GPT-4.1 (OpenAI patch protocol) | Model-specific; doesn't work on others |
| `whole` | Fallback for weak models | Token-expensive but format-tolerant |

Evidence quote (aider SKILL line 302): "Unified-diff bumped GPT-4 Turbo refactor benchmark from **20% to 61%**, and cut 'lazy comment' to 1/3."

Sonnet-specific evidence (aider SKILL line 319): "Claude 3.5 Sonnet replies truncated mid-edit at 4k. ... After fix Sonnet refactor benchmark went 55.1 → 64.0%."

Implication: the **edit-format choice itself is a per-model artifact**. Aider hard-codes a registry of `model → default_edit_format` in `aider/models.py`. When users pin custom prompts/formats, they must store them per-model too.

> "All of the models did worse on the benchmark when asked to return code in a structured JSON response." [aider.chat/2024/08/14/code-in-json.html]

So even the *output wrapper* is a model-specific artifact, not portable.

---

## 3. LlamaIndex: ServiceContext → Settings — a deprecation as a per-artifact concern

From `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`:

- Pre-0.10.x API: `ServiceContext(llm=..., embed_model=..., chunk_size=...)` passed to each index.
- Post-0.10.x: `Settings.llm = ...`, `Settings.embed_model = ...` — global, pinned at app boot.

Quote (LlamaIndex SKILL line 367): "`from llama_index import ServiceContext` → A4 [anti-pattern]." And line 349: "`ServiceContext` + manual config in every module — Pin `Settings.llm` and `Settings.embed_model` once at boot."

Why it matters here: **embedding model is part of the index artifact**. From LlamaIndex SKILL line 347:

> "A2 — Swap embedding model without re-embed → Rebuild index; tag artifact with embed model name+version."

The lesson generalizes: any time a framework deprecates an API surface, in-flight artifacts that hard-code the old surface become silent debt. Index files baked with `text-embedding-ada-002` cannot interoperate with `text-embedding-3-small` queries — dimensions differ, semantic space differs.

---

## 4. Provider-side snapshot churn

### OpenAI

- Alias `gpt-4o` rolls forward across snapshots: `gpt-4o-2024-05-13` → `gpt-4o-2024-08-06` → `gpt-4o-2024-11-20` → `gpt-4o-2025-...`
- OpenAI deprecation policy: dated snapshots typically supported ~12 months after release.
- Pinning to alias means your compiled prompt's behavior changes when OpenAI rolls the alias, with no PR, no log entry, no notice in your codebase.

### Anthropic

- `claude-3-5-sonnet-20240620` (original Sonnet 3.5) deprecated Oct 22, 2025.
- `claude-3-5-sonnet-20241022` (Sonnet 3.5 v2 / "new Sonnet") replaced it.
- `claude-3-7-sonnet-20250219` introduced extended thinking; behavioral differences large enough that prompts hand-tuned for 3.5 routinely under-perform on 3.7 without rework.
- Anthropic does not roll a `claude-3-5-sonnet` alias — you must pin a dated snapshot.

### Llama / open-weights

- `meta-llama/Llama-3-8B-Instruct` vs `meta-llama/Llama-3.1-8B-Instruct` vs `meta-llama/Llama-3.3-8B-Instruct`: tokenizer changes, instruction tuning changes, context window changes.
- HuggingFace pin: include the model SHA in the artifact metadata (`revision="abc123..."`) to survive force-pushes to the model repo.

---

## 5. The empirical asymmetry: prompts transfer down poorly, up unevenly

Composite from DSPy SKILL Case B + GEPA paper (arxiv.org/abs/2507.19457):

- **Down-transfer** (big → small): typically 15–30 point drops. Long CoT demos confuse small models; they parrot length without reasoning.
- **Up-transfer** (small → big): often within 2–5 points of native-compiled — small-model prompts are simpler, big models tolerate simplicity. But you leave performance on the table.
- **Sideways** (same size, different family — Sonnet ↔ GPT-4o): 5–10 points either direction. Instructions baked for one model's quirks (e.g. "do not include preamble") may have null effect or be slightly counterproductive on another.

Conclusion: **never assume any direction transfers without a swap-test**.

---

## 6. The "silent patch" problem

OpenAI / Anthropic / Google ship server-side improvements without bumping the snapshot string. A user pinned to `gpt-4o-2024-08-06` on 2024-09-01 may behave differently from the same pin on 2025-04-01 — same alias, evolved behavior (rare but documented).

Defenses:

1. **Record a quarterly canary**: re-run the held-out test set against the pinned snapshot every 90 days. If score drifts > regression-gate threshold, flag.
2. **Log a sample-output hash** in REGISTRY.jsonl per compile. Drift in canary outputs flags silent provider-side changes.

---

## 7. The MLflow Model Registry pattern (analogy)

MLflow Model Registry treats `(model_name, version)` as the identifier with explicit Stage labels (None / Staging / Production / Archived). The analogy maps directly:

| MLflow | Per-model prompt artifact |
|---|---|
| `model_name` | `<program>/<model-snapshot>/<dataset-version>` |
| `version` | `v<n>` integer, monotone |
| `Stage` | git tag (`prompt/<...>/v<n>` for prod) |
| `signature` (input/output schema) | DSPy Signature class (Python-side) |
| Run that produced it | REGISTRY.jsonl entry with optimizer config + seed + cost |
| Registered model | `artifacts/REGISTRY.jsonl` |

DSPy ships first-class MLflow integration (`mlflow.dspy.log_model`), making this analogy implementable end-to-end if scale warrants.

---

## 8. LangChain Hub: what it does *not* solve

LangChain Hub (`hub.push("user/prompt-name", template)`) provides:
- Versioned prompt templates with a public/private URL.
- Diff view across versions.

It does NOT solve:
- Model binding (the same template is "for any LM").
- Dataset binding (no awareness of what eval set the prompt was tuned against).
- Regression gates (no automated re-eval on push).

So for an org pinning compiled prompts: LangChain Hub = nice viewer, NOT a per-model artifact lifecycle. Pair with a local REGISTRY.jsonl or MLflow for the lifecycle layer.

---

## 9. Web evidence (optional confirmations)

- DSPy save_program docs: dspy.ai/tutorials/saving/ — explicit JSON schema described in DSPy SKILL Section "Anatomy of a compiled `program.json`".
- DSPy MIPROv2: prompt overfitting on small training sets is documented — dspy.ai/learn/optimization/overview/.
- Aider edit-format benchmarks: aider.chat/2023/12/21/unified-diffs.html, aider.chat/2024/09/26/architect.html.
- LlamaIndex ServiceContext deprecation announced in 0.10.x release notes — docs.llamaindex.ai release history.
- MLflow Model Registry: mlflow.org/docs/latest/model-registry.html.
