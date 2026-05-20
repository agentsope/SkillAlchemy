# R2 — Versioning Recipes: Concrete Layouts and Commands

Five recipes from minimal-viable to MLflow-grade. Pick by org size and audit needs.

---

## Recipe 1 — Minimal viable (single repo, <10 artifacts)

### Filesystem layout

```
repo/
├── src/
│   └── rag_synth/
│       ├── program.py              # DSPy module definitions (source of truth)
│       └── metric.py
├── data/
│   └── devset/
│       ├── v3.jsonl                # canonical labeled set
│       └── v3.sha256               # sha256 of jsonl (first 8 used in paths)
├── artifacts/
│   ├── REGISTRY.jsonl              # append-only registry
│   └── rag_synth/
│       ├── openai/
│       │   ├── gpt-4o-2024-08-06/
│       │   │   └── devset-v3-a8f1c2e9/
│       │   │       ├── v1.json
│       │   │       ├── v2.json
│       │   │       └── v3.json     # current
│       │   └── gpt-4o-mini-2024-07-18/
│       │       └── devset-v3-a8f1c2e9/
│       │           └── v1.json
│       └── anthropic/
│           └── claude-3-5-sonnet-20241022/
│               └── devset-v3-a8f1c2e9/
│                   └── v1.json
└── scripts/
    ├── compile.py                  # writes new artifact + appends REGISTRY
    ├── swap_test.py                # OP-4
    └── deprecation_scan.py         # OP-7
```

Why the deep nesting? Each path segment is grep-able. To find every Anthropic-compiled artifact for `rag_synth`: `ls artifacts/rag_synth/anthropic/`. To find everything compiled against the current dataset: `find artifacts -name 'devset-v3-*'`.

### REGISTRY.jsonl schema (one line per artifact)

```jsonl
{"path": "artifacts/rag_synth/openai/gpt-4o-2024-08-06/devset-v3-a8f1c2e9/v3.json", "sha256": "9f...", "program": "rag_synth", "provider": "openai", "model": "gpt-4o-2024-08-06", "dataset": "devset-v3", "dataset_sha256_8": "a8f1c2e9", "optimizer": "MIPROv2", "optimizer_config": {"auto": "light", "max_bootstrapped_demos": 4}, "metric": "exact_match", "dev_score": 0.78, "test_score": 0.74, "cost_usd": 2.30, "wall_seconds": 612, "dspy_version": "2.5.6", "compiled_at": "2025-04-12T14:22:01Z", "compiled_by": "ci@github-actions", "commit": "a1b2c3d", "parent_artifact": null}
{"path": "artifacts/rag_synth/openai/gpt-4o-mini-2024-07-18/devset-v3-a8f1c2e9/v1.json", "sha256": "1c...", "program": "rag_synth", "provider": "openai", "model": "gpt-4o-mini-2024-07-18", "dataset": "devset-v3", "dataset_sha256_8": "a8f1c2e9", "optimizer": "MIPROv2", "optimizer_config": {"auto": "light"}, "metric": "exact_match", "dev_score": 0.71, "test_score": 0.68, "cost_usd": 0.42, "wall_seconds": 380, "dspy_version": "2.5.6", "compiled_at": "2025-04-12T15:01:44Z", "compiled_by": "alex@local", "commit": "a1b2c3d", "parent_artifact": null}
```

### compile.py skeleton

```python
import json, hashlib, os, time, subprocess
from datetime import datetime, timezone
from pathlib import Path
import dspy

PROGRAM = "rag_synth"
MODEL   = "gpt-4o-2024-08-06"
PROVIDER = "openai"
DATASET_PATH = Path("data/devset/v3.jsonl")
DATASET_SHA8 = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()[:8]
DATASET_TAG = f"devset-v3-{DATASET_SHA8}"

OUT_DIR = Path(f"artifacts/{PROGRAM}/{PROVIDER}/{MODEL}/{DATASET_TAG}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# next version number
existing = sorted(OUT_DIR.glob("v*.json"))
next_v = (int(existing[-1].stem[1:]) + 1) if existing else 1
out_path = OUT_DIR / f"v{next_v}.json"

# ... configure dspy.LM(MODEL), load dataset, build program, run MIPROv2 ...
# compiled = optimizer.compile(program, trainset=train)
t0 = time.time()
compiled.save(str(out_path))
wall = time.time() - t0

sha256 = hashlib.sha256(out_path.read_bytes()).hexdigest()
entry = {
    "path": str(out_path),
    "sha256": sha256,
    "program": PROGRAM,
    "provider": PROVIDER,
    "model": MODEL,
    "dataset": "devset-v3",
    "dataset_sha256_8": DATASET_SHA8,
    "optimizer": "MIPROv2",
    "optimizer_config": {"auto": "light", "max_bootstrapped_demos": 4},
    "metric": "exact_match",
    "dev_score": dev_score,
    "test_score": test_score,   # held-out
    "cost_usd": cost,
    "wall_seconds": int(wall),
    "dspy_version": dspy.__version__,
    "compiled_at": datetime.now(timezone.utc).isoformat(),
    "commit": subprocess.check_output(["git","rev-parse","HEAD"]).decode().strip(),
    "parent_artifact": str(existing[-1]) if existing else None,
}
with open("artifacts/REGISTRY.jsonl", "a") as f:
    f.write(json.dumps(entry) + "\n")
```

---

## Recipe 2 — Swap test (OP-4)

```python
# scripts/swap_test.py
import json, dspy
from pathlib import Path

OLD_ARTIFACT = "artifacts/rag_synth/openai/gpt-4o-2024-08-06/devset-v3-a8f1c2e9/v3.json"
NEW_MODEL    = "gpt-4o-2024-11-20"   # candidate

testset = load_held_out_test()
program_cls = import_program("rag_synth")

# Load old artifact
old = program_cls()
old.load(OLD_ARTIFACT)

# Run unchanged artifact against NEW model
dspy.configure(lm=dspy.LM(NEW_MODEL))
score_transfer = dspy.Evaluate(devset=testset, metric=metric)(old)

# Original score
old_meta = next(json.loads(l) for l in open("artifacts/REGISTRY.jsonl") if OLD_ARTIFACT in l)
score_original = old_meta["test_score"]

delta = score_transfer - score_original
print(f"Transfer Δ = {delta:+.3f}")

GATE = 0.02     # 2 points on a 0-1 scale
if abs(delta) > GATE:
    print(f"RECOMPILE REQUIRED (Δ {delta:+.3f} > gate {GATE})")
    exit(1)
print("Transfer acceptable.")
```

Emit `swap-report-<old-model>-to-<new-model>.md` alongside.

---

## Recipe 3 — Regression gate in CI

`.github/workflows/artifact-gate.yml`

```yaml
name: artifact-regression
on: { pull_request: { paths: ["artifacts/**"] } }
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - run: pip install -r requirements.txt
      - name: Identify changed artifacts
        run: |
          git diff --name-only origin/main...HEAD -- 'artifacts/**/v*.json' > changed.txt
      - name: Re-evaluate held-out test set
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: python scripts/regression_gate.py changed.txt
```

`scripts/regression_gate.py` reads each changed artifact, looks up its predecessor in REGISTRY.jsonl (`parent_artifact` field), re-runs the held-out test set, and fails with non-zero if `new_test_score - parent_test_score < -GATE`.

---

## Recipe 4 — Deprecation scan (OP-7)

```python
# scripts/deprecation_scan.py
from datetime import date, timedelta
import json, re

# Hand-curated table; update on provider announcements.
DEPRECATIONS = {
    "claude-3-5-sonnet-20240620": date(2025, 10, 22),
    "claude-3-opus-20240229":     date(2026,  3,  4),
    "gpt-4-0613":                 date(2024,  6, 13),
    # ...
}

today = date.today()
warn_window = timedelta(days=90)

with open("artifacts/REGISTRY.jsonl") as f:
    for line in f:
        e = json.loads(line)
        d = DEPRECATIONS.get(e["model"])
        if d and (d - today) <= warn_window:
            days = (d - today).days
            print(f"[{days:+4d}d] {e['path']} — model {e['model']} retires {d.isoformat()}")
```

Run nightly via cron. Open a GitHub issue per artifact within the 90-day window.

---

## Recipe 5 — MLflow Model Registry (org-scale)

When >50 artifacts or >5 teams, switch from REGISTRY.jsonl to MLflow:

```python
import mlflow, mlflow.dspy

mlflow.set_tracking_uri("http://mlflow.internal:5000")
mlflow.set_experiment("rag_synth")

with mlflow.start_run(run_name=f"compile-{MODEL}-{DATASET_TAG}"):
    mlflow.log_params({"model": MODEL, "dataset": DATASET_TAG,
                       "optimizer": "MIPROv2", "auto": "light"})
    mlflow.log_metrics({"dev_score": dev_score, "test_score": test_score,
                        "cost_usd": cost})
    mlflow.dspy.log_model(compiled, artifact_path="program",
                          registered_model_name=f"rag_synth-{MODEL}")

# Promote to Production once swap_test + regression_gate pass
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name=f"rag_synth-{MODEL}", version=3, stage="Production",
    archive_existing_versions=True)
```

The `registered_model_name` includes the snapshot — one logical name per `(program, model)` pair. Stage labels (None / Staging / Production / Archived) replace git tags as promotion mechanism.

---

## Recipe 6 — Aider per-model config artifacts

Aider's case is lighter-weight (config, not a JSON blob), but the same discipline applies. In `.aider.conf.yml`:

```yaml
# Per-model edit format pins. Do not change without running benchmark.
models:
  gpt-4-1106-preview:
    edit_format: udiff           # 20% → 61% on refactor [aider.chat/2023/12/21]
  gpt-4o-2024-08-06:
    edit_format: diff
  claude-3-5-sonnet-20241022:
    edit_format: diff
  claude-3-7-sonnet-20250219:
    edit_format: diff
    extra_params: { thinking: { budget_tokens: 8000 } }
  gpt-4.1-2025-04-14:
    edit_format: patch           # OpenAI patch protocol
```

Commit this file. Treat changes to it as Recipe-3-style regressions: re-run aider's edit benchmark on a small fixed task set before merging.

---

## Recipe 7 — LlamaIndex Settings + index artifacts

For an index baked with a specific embedding model:

```
indices/
└── support_kb/
    └── openai__text-embedding-3-small__1536/
        └── corpus-2025-04-12-7a2c/
            ├── docstore.json
            ├── vector_store.json
            ├── index_store.json
            └── manifest.json     # {embed_model, dim, corpus_sha8, settings_snapshot, llama_index_version}
```

`manifest.json` is the per-artifact metadata. Loader refuses to query an index if `Settings.embed_model` at runtime doesn't match `manifest.embed_model` — prevents the "swap embed model without re-embed" failure (LlamaIndex SKILL anti-pattern A2).

```python
def load_index(name):
    mf = json.load(open(f"indices/{name}/manifest.json"))
    if Settings.embed_model.model_name != mf["embed_model"]:
        raise RuntimeError(f"Embed mismatch: index baked with {mf['embed_model']}, "
                           f"Settings has {Settings.embed_model.model_name}. Rebuild required.")
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=f"indices/{name}"))
```

---

## Summary: which recipe when

| Scale | Artifacts | Recipe |
|---|---|---|
| Solo / prototype | <5 | Recipe 1 + Recipe 2 |
| Small team | 5–50 | Recipe 1 + 2 + 3 + 4 |
| Multi-team org | >50 | Recipe 5 (MLflow) + 4 |
| Aider deployment | n/a | Recipe 6 alongside any of above |
| LlamaIndex deployment | n/a | Recipe 7 alongside any of above |
