# R3. Dilemma Cases

Five real production-grade dilemmas a coder-agent must navigate when deploying vLLM. Each has authentic evidence pointers — most are sourced from vLLM docs, GitHub issues/forums, or peer-reviewed benchmarks.

---

## Dilemma 1 — Throughput vs Latency: how aggressively to batch?

**Concrete situation**: Team serves Llama-3-70B-FP8 on 2×H100. P50 TTFT 250 ms (fine), but P99 spikes to 4 s under bursts. They consider raising `--max-num-seqs` from 64 to 256.

**The tension**:
- Higher `max_num_seqs` → more concurrency → higher throughput, BUT more contention for KV cache → preemption + head-of-line blocking on prefills.
- Higher `max_num_batched_tokens` → better TTFT (more prefill per step), BUT worse ITL for streaming requests already mid-decode [medium.com/@kaige.yang0110].

**Resolution heuristic**:
- Inspect Prometheus first [developers.redhat.com 2026]:
  - If P99 spike correlates with `num_requests_waiting > 0` AND KV occupancy < 80% → **raise** `max_num_seqs`.
  - If KV occupancy hits 100% AND **preemption counter rises** → DO NOT raise; instead: quantize KV to FP8, shorten `max_model_len`, or add a replica.
- For latency-sensitive interactive workloads: **lower** `max_num_batched_tokens` (e.g. 2048) — favors decode/ITL.
- For batch/offline: **raise** `max_num_batched_tokens` (≥8192) — favors TTFT/throughput [docs.vllm.ai optimization; anyscale.com].

**Evidence**:
- developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance
- docs.vllm.ai/en/stable/configuration/optimization/
- medium.com/@kaige.yang0110/vllm-throughput-optimization-1

---

## Dilemma 2 — 4-bit AWQ vs FP8: is the quality drop worth the VRAM?

**Concrete situation**: Deploying Qwen-72B on a single H100 (80 GB). At BF16, model = 144 GB → doesn't fit. Options:
- (a) **FP8** → 72 GB → fits with tight KV budget.
- (b) **AWQ-4** → 36 GB → comfortable KV budget, larger batches.

**The tension**:
- FP8 is empirically **near-lossless** across all model scales (W8A8-FP) [arxiv.org/abs/2411.02355], but leaves little KV headroom on single 80 GB → smaller batches → less throughput.
- AWQ-4 frees ~36 GB for KV → 2–3× more concurrent sequences → higher throughput, but **~1.6 average-point drop** on benchmarks, larger on reasoning/long-context tasks [arxiv 2411.02355].
- Real-world coding-task quality gaps can exceed academic-benchmark gaps [arxiv 2411.02355].

**Resolution heuristic**:
- **Quality-critical** (legal, medical, coding agent): FP8 + accept smaller batch, OR move to 2×H100 TP=2 and stay at BF16.
- **Throughput-critical** (bulk classification, summarization, search re-ranking): AWQ-4 wins; validate on **your** eval set, not generic benchmarks.
- **Mixed traffic**: run two replicas — FP8 for premium tier, AWQ for free tier.
- **Avoid INT3** entirely (~6 pt avg drop, not justified).

**Evidence**:
- arxiv.org/abs/2411.02355 ("Give Me BF16 or Give Me Death")
- docs.gpustack.ai/2.0/performance-lab/references/the-impact-of-quantization-on-vllm-inference-performance/
- vrlatech.com/llm-quantization-explained-int4-int8-fp8-awq-and-gptq-in-2026/

---

## Dilemma 3 — TP=4 single replica vs 2×TP=2 replicas

**Concrete situation**: 4×A100-80GB with NVLink, serving a 70B model. Choose: one big replica at TP=4, or two replicas at TP=2?

**The tension**:
- **TP=4** lowers single-request latency (model layers parallelized further), BUT all-reduce overhead grows with degree, and on saturated workloads the marginal throughput per added GPU diminishes.
- **2×TP=2** doubles independent throughput (each replica handles its own batch), survives one-replica failures, BUT no single request can go faster than TP=2.

**Resolution heuristic**:
- If P99 latency SLA is the binding constraint and single-request decode latency is the bottleneck → **TP=4**.
- If throughput-per-dollar is binding, requests are independent, average request latency at TP=2 is acceptable → **2×TP=2 replicas** (Red Hat triage step-5 recommendation [developers.redhat.com 2026]).
- Always check **NVLink topology** — across-NUMA TP=4 over PCIe degrades faster than two NVLink-paired TP=2 islands [servermo.com vLLM multi-gpu].
- Benchmark with `vllm bench serve` on representative ISL/OSL.

**Evidence**:
- docs.vllm.ai/en/stable/serving/parallelism_scaling/
- docs.jarvislabs.ai/blog/scaling-llm-inference-dp-pp-tp
- developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance
- servermo.com/howto/vllm-multi-gpu-setup/

---

## Dilemma 4 — Prefix caching ROI: is the held KV worth it?

**Concrete situation**: Production RAG service. Each request: ~2 KB system prompt + 4–16 KB context + short user query. Should they `--enable-prefix-caching`?

**The tension**:
- APC reduces **prefill** time on cache-hit. If 90% of requests share a system prompt, prefill of those tokens is free → big TTFT win.
- Cached blocks **stay resident** in KV memory → fewer free blocks for new requests → can trigger preemption under burst traffic.
- APC accelerates **prefill only** — if outputs are long and prefixes don't repeat, gain ≈ 0 [docs.vllm.ai automatic_prefix_caching].

**Resolution heuristic**:
- **Enable** when shared-prefix fraction ≥ ~30% AND outputs are short-to-medium.
- **Disable / tune** when requests are unique and long-output-dominated.
- For multi-replica deployments: pair with **prefix-aware routing** so requests with same prefix land on same replica; otherwise you pay cache cost N times for 1/N hit rate [llm-d.ai/blog/kvcache-wins-you-can-see].
- For multi-tenant: enable **cache salting** to prevent cross-tenant prefix-hit leakage [github.com/vllm-project/vllm/issues/16016].

**Evidence**:
- docs.vllm.ai/en/stable/design/prefix_caching/
- llm-d.ai/blog/kvcache-wins-you-can-see
- bentoml.com/llm/inference-optimization/prefix-caching
- github.com/vllm-project/vllm/issues/16016 (RFC: cache salting)
- github.com/vllm-project/vllm/discussions/10841 ("Why caching sharing only works for shared prefix prompt?")

---

## Dilemma 5 — Speculative decoding: worth the complexity?

**Concrete situation**: Single-user, latency-sensitive coding assistant on Llama-3-70B. Decode dominates total latency.

**The tension**:
- **EAGLE-3** can deliver up to **2.5× decode speedup** for low-QPS workloads [developers.redhat.com 2025 eagle3], but requires a trained EAGLE head, increases VRAM, and is sensitive to hyperparameters.
- **n-gram** speculation is cheap (no extra weights) but only **~1.17× speedup** [jarvislabs.ai].
- At high QPS, the GPU is already saturated by real batch work; speculative compute steals capacity instead of filling idle cycles.
- **Bad hyperparameters can degrade cost-per-token by up to 175%** [arxiv 2601.11580].

**Resolution heuristic**:
- **Low QPS, single-stream latency-bound, EAGLE/MTP head available** → enable model-based speculation. Worth the engineering cost.
- **No draft weights, want easy win** → try n-gram first; if speedup < ~1.1×, disable.
- **High QPS / throughput-bound** → skip speculation, invest in quantization + parallelism instead.
- Always A/B against non-speculative baseline on representative traffic.

**vLLM official guidance** on when it doesn't help [docs.vllm.ai/en/latest/features/speculative_decoding/]:
- Designed for "medium-to-low QPS workloads."
- High-batch-size scenarios show reduced benefit.

**Evidence**:
- docs.vllm.ai/en/latest/features/speculative_decoding/
- developers.redhat.com/articles/2025/07/01/fly-eagle3-fly-faster-inference-vllm-speculative-decoding
- jarvislabs.ai/blog/speculative-decoding-vllm-faster-llm-inference
- arxiv.org/pdf/2601.11580 ("Speculative Decoding: Performance or Illusion?")
- aws.amazon.com/blogs/machine-learning/p-eagle-faster-llm-inference-with-parallel-speculative-decoding-in-vllm/
