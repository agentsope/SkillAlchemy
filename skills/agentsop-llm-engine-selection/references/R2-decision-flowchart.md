# R2. Decision Flowchart — engine selection by constraint vector

A more granular version of SKILL.md §7.3, with worked examples.

## Top-level flow

```
START
  │
  ▼
[Q1] GPU-backed multi-user production?
  │
  ├─ NO ────────────────────────────────────────────────► [LANE-B: non-GPU / single-user]
  │
  └─ YES ───────────────────────────────────────────────► [LANE-A: GPU production]

================================================================
LANE-A: GPU production
================================================================
[Q2] Shared-prefix fraction ≥30% OR structured-out ≥30%?
  │
  ├─ YES ────────────────────────────────────────────► SGLang (primary), vLLM (fallback)
  │
  └─ NO ─────────────────────────────────────────────► next
                                                        │
[Q3] NVIDIA-only + max throughput + ≥2 wk eng budget?  │
  │                                                    │
  ├─ YES ──────────────────────────────────────► TensorRT-LLM (primary), vLLM (fallback)
  │
  └─ NO ──────────────────────────────────────► vLLM (primary), SGLang (A/B candidate)

================================================================
LANE-B: non-GPU / single-user
================================================================
[Q4] Apple Silicon target?
  │
  ├─ YES ──► [Q4a] Dev or prod?
  │            ├─ Dev / local  → Ollama (best UX) or MLX (best perf)
  │            └─ Prod server  → MLX (Apple-native) or llama.cpp Metal
  │
  └─ NO ───► [Q5] CPU-only / edge / embedded?
                ├─ YES → llama.cpp (broadest hardware) + GGUF
                └─ NO  → [Q6] Dev laptop with NVIDIA?
                           ├─ YES → Ollama (fast UX) or vLLM (matches prod)
                           └─ NO  → re-check Q1
```

## Hard filters (apply before flowchart)

| Filter | If true, eliminate |
|---|---|
| No NVIDIA GPU | TensorRT-LLM |
| OSS-permissive-only license | TensorRT-LLM (proprietary), TGI (HFOIL) |
| Mamba / brand-new architecture | check vLLM + SGLang coverage; likely eliminate llama.cpp / TGI / TensorRT-LLM |
| Multi-LoRA hot-swap required | eliminate llama.cpp, Ollama (limited) |
| Apple Silicon production | eliminate vLLM (Metal experimental), TGI, TensorRT-LLM |
| Air-gapped on-prem + closed-source forbidden | eliminate TensorRT-LLM |
| GGUF weights only | eliminate vLLM (experimental), TGI, TensorRT-LLM (no GGUF) |
| MLX weights only | eliminate all except MLX-native |

## Hardware-topology filter

After the flowchart picks an engine, sanity-check:

```
[T1] Multi-GPU TP planned?
   ├─ YES → NVLink present?
   │         ├─ YES → proceed with TP
   │         └─ NO  → drop to TP=2 + replicas, OR pipeline parallel,
   │                  OR switch to a smaller model. Engine doesn't matter.
   └─ NO  → no topology constraint.

[T2] Multi-node planned?
   ├─ YES → InfiniBand / RoCE present?
   │         ├─ YES → proceed
   │         └─ NO  → do not multi-node; scale via independent replicas.
   └─ NO  → no constraint.
```

## Worked example 1 — Production RAG on 4×L40S (PCIe-only)

- **Q1 YES** → LANE-A.
- **Q2 YES** (RAG = high shared-prefix fraction) → SGLang primary.
- **T1** L40S = PCIe-only → drop TP=4; do `TP=2 × 2 replicas` OR `PP=4`.
- **Final pick**: SGLang × 2 replicas, each replica is TP=2 over NVLink-paired or NUMA-local pair. Fallback: vLLM with `--enable-prefix-caching` + prefix-aware routing.

## Worked example 2 — Coding-agent SaaS on 8×H100 (NVLink-full)

- **Q1 YES** → LANE-A.
- **Q2**: ~50% structured-output (tool calls), ~70% shared system prompts → YES → SGLang primary.
- **T1**: NVLink-full → TP=8 viable; but consider 2×TP=4 for replica redundancy.
- **Final pick**: SGLang with TP=4 × 2 replicas. A/B vs vLLM with xgrammar guided decoding.

## Worked example 3 — NVIDIA-only inference service, single stable model, 16×H100

- **Q1 YES** → LANE-A.
- **Q2 NO** (mixed traffic, no strong prefix signal) → skip SGLang.
- **Q3 YES** (NVIDIA, throughput-bound, 2-week budget) → TensorRT-LLM primary.
- **Caveat**: model must be stable for ≥3 months to amortize engine-rebuild cost.
- **Final pick**: TensorRT-LLM with vLLM as the model-fit / shadow-traffic fallback.

## Worked example 4 — On-device assistant on iPad

- **Q1 NO** → LANE-B.
- **Q4 YES** Apple. **Q4a** prod-on-device.
- **Final pick**: MLX or llama.cpp Metal with GGUF. Quantize to ≤4-bit. Single concurrent user.

## Worked example 5 — Dev laptop M3 Max, mirror cloud vLLM

- **Q1 NO** locally → LANE-B.
- **Q4 YES** Apple. **Q4a** dev.
- **Pick**: Ollama for local. Production cloud stays on vLLM. Standardize on OpenAI-compatible API contract, not on engine.

## Re-evaluation triggers

Re-run this flowchart when:
- New model release breaks prior assumptions (new architecture, new size).
- Hardware refresh changes topology (added NVLink, switched to AMD).
- Workload mix shifts ≥20% (more agents, more structured-out, more concurrent users).
- License policy changes.
- The chosen engine's release cadence indicates a major shift (e.g. TGI maintenance → vLLM migration).

Cadence: every 2 quarters, or when one of the above fires.
