# R2. SOP Workflow — From "We Want To Serve A Model" To Production

A 7-step workflow for taking an open-weights model to a tuned vLLM deployment, with the decision points at each step.

## Step 0 — Sanity check: is vLLM the right tool?

| Condition | Use vLLM? |
|---|---|
| Production, GPU available, concurrent users | ✅ Yes |
| Single dev laptop, ≤1 user, want 5-minute setup | ❌ Ollama / llama.cpp |
| CPU-only, edge | ❌ llama.cpp (GGUF) |
| Apple Silicon production | ❌ As of 2026, Metal/MPS support is experimental [aimadetools.com] |
| NVIDIA-only, willing to invest 1–2 weeks tuning, max throughput | Consider TensorRT-LLM (30–50% higher throughput possible) [n1n.ai 2026] |
| Heavy prefix sharing / agent state machines | Consider SGLang (~29% higher throughput on shared-context workloads) [n1n.ai 2026] |

## Step 1 — Pick model + precision

```
Does the model fit in 1 GPU's VRAM at BF16?
├── Yes  → BF16, TP=1.   Skip to Step 3.
└── No   → Quantize OR scale parallelism. Continue.

Quantization decision:
├── Hopper / Ada / Blackwell GPU?
│   └── FP8 — effectively lossless across model scales [arxiv 2411.02355]
├── Older Ampere or no FP8, need 4× compression?
│   ├── AWQ-4   — stable at 4-bit, ~1.6pt avg drop [arxiv 2411.02355]
│   └── GPTQ-4  — slightly better on real coding tasks [arxiv 2411.02355]
├── Need 50% of FP8 cost & happy on H100?
│   └── MXFP4 / NVFP4 (vLLM 2026 supports) [github.com/vllm-project/vllm README]
└── DO NOT use INT3 — ~6pt avg drop, not worth it [arxiv 2411.02355]
```

**Always verify on your domain eval set** — academic benchmarks (MMLU, HellaSwag) under-report real-world coding-task drops.

## Step 2 — Choose parallelism strategy

Per vLLM official guidance [docs.vllm.ai/en/stable/serving/parallelism_scaling/]:

```
Model fits 1 GPU?              → TP=1, PP=1     (don't distribute)
Fits 1 node + NVLink?          → TP=#GPUs/node, PP=1
Fits 1 node + only PCIe?       → PP within node (TP over PCIe collapses)
Multi-node?                    → TP=GPUs/node, PP=#nodes
MoE (Mixtral, DeepSeek-V3)?    → DP attention + EP/TP for MoE layers
```

**Anti-pattern**: TP=4 across PCIe-only or cross-NUMA. NVLink ≈ 900 GB/s bidirectional; PCIe Gen4 x16 ≈ 32 GB/s — about **28× slower** [spheron.network 2026]. The per-layer all-reduce becomes the bottleneck.

**Replica vs TP tradeoff**: Two replicas at TP=2 often beats one replica at TP=4 on throughput-per-dollar [developers.redhat.com 2026 step 5]. Only choose larger TP when single-request latency SLA is binding.

## Step 3 — Memory & batch envelope

| Param | Start | Lower when… | Raise when… |
|---|---|---|---|
| `--gpu-memory-utilization` | 0.90 | sharing GPU / OOM | engine alone, KV is bottleneck (→0.95) |
| `--max-model-len` | longest_realistic_prompt + longest_output | OOM, model-arch max is much larger | clipping legitimate requests |
| `--max-num-seqs` | 256 | preemption logs appear | KV occupancy <70%, want more concurrency |
| `--max-num-batched-tokens` | 8192 (V1 default-ish) | want better ITL (latency) | want better TTFT (throughput) |

The **single biggest OOM mistake** is leaving `max_model_len` at the architectural max (e.g. 128k for Llama-3.1) when real prompts are 4k. vLLM reserves KV for the worst case [markaicode.com 2026].

## Step 4 — Turn on free wins

```bash
--enable-prefix-caching         # if any system-prompt/few-shot reuse
--enable-chunked-prefill        # V1: default on; keeps long prefills from blocking decode
--kv-cache-dtype fp8            # +headroom in KV (Ampere+ GPU)
```

**Prefix caching caveat**: only helps prefill. If outputs are long and prefixes don't repeat, gain ≈ 0 and you've consumed KV memory for cached-but-unhit blocks [docs.vllm.ai automatic_prefix_caching].

## Step 5 — Optional: speculative decoding

```
Workload                                                         | Pick
-----------------------------------------------------------------+-------------
Low QPS, latency-bound, EAGLE/MTP head available for your model  | EAGLE-3 / MTP  (up to 2.5× decode) [redhat 2025]
No draft weights, want zero-effort try                            | n-gram speculation (~1.17×) [jarvislabs.ai]
High QPS / large batch                                            | skip — gains shrink, compute is already saturated
```

Always A/B against the non-speculative baseline. Bad hyperparameters can degrade cost-per-token by up to **175%** [arxiv 2601.11580].

## Step 6 — Benchmark on YOUR workload

Don't trust generic benchmarks. Use `vllm bench serve` or a load tool (locust, k6) with:

- Real ISL (input-sequence-length) and OSL (output-sequence-length) distributions from logs.
- Real concurrency curve (steady state + bursts).
- Real prompt distribution (so prefix caching gets a realistic hit rate).

Watch Prometheus metrics [developers.redhat.com 2026]:
- `num_requests_running` and `num_requests_waiting` — queue depth.
- KV cache occupancy %.
- Preemption count (should stay near zero in steady state).
- TTFT and ITL histograms (P50, P95, P99).

Tune in this order: Step 3 → Step 4 → Step 5 → reconsider Step 2.

## Step 7 — Scale out

| Symptom | Action |
|---|---|
| Throughput maxed, latency SLA still ok | Add replicas (data-parallel across pods, behind a load balancer) |
| Tail TTFT high, prefix caching enabled | **Prefix-aware routing** — pin requests with same prefix to same replica [llm-d.ai/blog/kvcache-wins-you-can-see] |
| Cost too high | Smaller model / quantize harder / try draft model / consider TensorRT-LLM |
| One-node failure SLA | Always ≥2 replicas |
| Multi-tenant privacy | **Cache salting** to prevent cross-tenant prefix-hit leakage [github.com/vllm-project/vllm/issues/16016] |

## Reference command (production-ish Llama-3.1-70B)

```bash
vllm serve meta-llama/Llama-3.1-70B-Instruct \
  --quantization fp8 \
  --tensor-parallel-size 2 \
  --max-model-len 8192 \
  --max-num-seqs 256 \
  --max-num-batched-tokens 8192 \
  --gpu-memory-utilization 0.90 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --kv-cache-dtype fp8
```

## Sources

- docs.vllm.ai/en/stable/serving/parallelism_scaling/
- docs.vllm.ai/en/stable/configuration/optimization/
- docs.vllm.ai/en/stable/configuration/conserving_memory/
- developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance
- arxiv.org/abs/2411.02355
- markaicode.com/errors/vllm-out-of-memory-fix/
- llm-d.ai/blog/kvcache-wins-you-can-see
