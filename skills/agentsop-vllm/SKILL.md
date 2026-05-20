---
name: agentsop-vllm
description: Decision SOP for serving LLMs with vLLM. Covers PagedAttention mental model, quantization/parallelism/batching tradeoffs, OOM triage, and when NOT to use vLLM. Activates when a coder-agent is choosing or tuning an inference engine, debugging vLLM throughput/latency/OOM, or comparing vLLM against TGI/SGLang/TensorRT-LLM/llama.cpp.
domain: high-throughput LLM inference serving
version: 1.0
sources:
  - https://arxiv.org/abs/2309.06180
  - https://docs.vllm.ai/en/stable/
  - https://github.com/vllm-project/vllm
  - https://developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance
---

# vLLM Serving SOP

## 1. 何时激活 (When to activate)

Activate this skill when any of the following hold:

- The user wants to **serve an LLM in production** (multi-user, concurrent requests, throughput-oriented) and has GPU infrastructure.
- The user is **comparing inference engines** (vLLM vs TGI vs SGLang vs TensorRT-LLM vs llama.cpp/Ollama).
- The user reports a **vLLM operational issue**: CUDA OOM, low throughput, high TTFT, request preemption, multi-GPU setup, quantization choice.
- The user is **sizing hardware** for an open-weights model (Llama / Qwen / Mixtral / DeepSeek-V3) and asking about tensor/pipeline parallelism.
- The user mentions PagedAttention, prefix caching, continuous batching, chunked prefill, or speculative decoding.

**Do NOT activate** for: training/fine-tuning (use accelerate/deepspeed/trl), CPU-only edge inference (use llama.cpp/Ollama), Apple Silicon production (vLLM Metal/MPS is experimental, not production-ready as of 2026) [aimadetools.com 2026], API-only consumption of hosted models (just call the OpenAI/Anthropic SDK).

---

## 2. 核心心智模型 (Core Mental Model)

### 2.1 The OS abstraction: KV cache as virtual memory

vLLM's defining insight (Kwon et al., SOSP 2023) is that **LLM serving's bottleneck was not compute — it was KV-cache memory fragmentation**. Pre-vLLM systems pre-allocated a contiguous KV-cache slot per request, sized for the maximum possible output length; in early 2023, inference engines used only **20–40% of available GPU memory** because of internal+external fragmentation [arxiv.org/abs/2309.06180; zilliz.com/learn].

PagedAttention applies classic OS paging to KV cache:

- **Block** = fixed-size chunk of KV cache (default 16 tokens; ~12.8 KB for a 13B model) [medium.com/@mandeep0405].
- **Logical blocks** per request → **block table** → **physical blocks** in GPU memory (analogous to virtual→physical page table).
- Blocks need not be contiguous. The attention kernel reads scattered physical blocks via the block table and presents them as a logical contiguous sequence.
- **Copy-on-write** + **prefix sharing**: multiple requests that share a prefix (e.g. a system prompt, few-shot examples) share KV blocks; a write triggers a per-request copy [arxiv.org/abs/2309.06180].

**Result**: near-zero memory waste → larger batch sizes → **2–4× throughput** vs FasterTransformer/Orca at equal latency [arxiv.org/abs/2309.06180]; **14–24×** vs vanilla HuggingFace Transformers [yottalabs.ai 2026].

### 2.2 The scheduler: iteration-level (continuous) batching

vLLM inherits Orca's iteration-level scheduling (OSDI 2022, **36.9× over FasterTransformer** [medium.com/byte-sized-ai]). Instead of waiting for a static batch to finish, the scheduler reassigns batch slots **every decode step**: a request that finishes early frees its slot to a waiting request. Static batching is dead; continuous batching is table stakes.

### 2.3 Prefill vs decode are different beasts

- **Prefill** (processing the prompt): compute-bound, high SM utilization, scales with input length.
- **Decode** (generating tokens one-at-a-time): memory-bandwidth-bound, low SM utilization.
- A long prefill blocks all decodes on the GPU → **head-of-line blocking** → high inter-token latency (ITL) for already-streaming requests.
- **Chunked prefill** breaks long prefills into pieces interleaved with decode steps [docs.vllm.ai/en/stable/configuration/optimization/].

**Takeaway**: when tuning, separate TTFT (time-to-first-token, gated by prefill+queue) from ITL (gated by decode bandwidth and batch interference).

### 2.4 Three throughput levers, in order of impact

Per Red Hat's tuning hierarchy [developers.redhat.com 2026]:
1. **Right-size the model** (smallest adequate).
2. **Scale hardware** (more replicas; better-bandwidth GPUs).
3. **Quantize** (FP8 weights + KV cache).
4. **Speculative decoding** (model-based: EAGLE-3 / MTP).
5. **Refine parallelism** (TP degree, replicas vs higher TP).

---

## 3. SOP 工作流 (SOP Workflow)

```
[Step 0] Confirm vLLM is the right tool
   ├─ Production, GPU-backed, concurrent users? → continue
   └─ Else → see §7 (ecosystem) and stop

[Step 1] Pick the model + precision
   ├─ Model fits in single-GPU VRAM at BF16?         → keep BF16, TP=1
   ├─ Need 50% VRAM cut, ~zero quality loss?         → FP8 (Hopper/Ada+) [arxiv 2411.02355]
   ├─ Need 4× VRAM cut, tolerate ~1.6pt avg drop?    → AWQ-4 or GPTQ-4
   └─ Reasoning-heavy / coding workload?             → favor FP8 > AWQ; verify on eval set

[Step 2] Choose parallelism
   ├─ Fits 1 GPU                                     → TP=1, PP=1
   ├─ Fits 1 node, NVLink present                    → TP=#GPUs/node
   ├─ Fits 1 node, only PCIe (e.g. L40S)             → PP within node (TP-only over PCIe collapses)
   ├─ Multi-node                                     → TP=GPUs/node, PP=#nodes
   └─ MoE model (Mixtral, DSv3)                      → DP attention + EP/TP for MoE layers

[Step 3] Set memory/batch envelope
   ├─ --gpu-memory-utilization 0.90 (default; 0.85 if sharing GPU)
   ├─ --max-model-len = (longest realistic prompt + output) — NOT model max!
   ├─ --max-num-seqs (start 256; lower if preemption logs appear)
   └─ --max-num-batched-tokens (raise for TTFT; lower for ITL)

[Step 4] Turn on the free wins
   ├─ enable_prefix_caching=True            → if any system-prompt/few-shot reuse
   ├─ enable_chunked_prefill=True (V1: default on) → tame long-prompt HoL blocking
   └─ kv_cache_dtype="fp8"                  → +KV headroom, Ampere+ only

[Step 5] Optional: speculative decoding
   ├─ Low QPS, latency-bound, have draft/EAGLE weights? → EAGLE-3 or MTP (high gain)
   ├─ No draft model, zero setup cost?                  → n-gram (modest gain, ~1.17×)
   └─ High QPS / large batch?                           → skip; gains shrink, complexity rises

[Step 6] Benchmark on YOUR workload
   ├─ Replay representative ISL/OSL distribution
   ├─ Watch Prometheus: num_requests_waiting, KV cache occupancy, preemption count
   └─ Tune in this order: §3 Step 3 → Step 4 → Step 5 → reconsider Step 2

[Step 7] Scale out
   ├─ Latency SLA violated under load? → add a replica (data parallelism across pods)
   ├─ Tail TTFT high?                  → prefix-aware routing; pin prefix to replica
   └─ Cost too high?                   → revisit quantization, smaller model, draft model
```

---

## 4. 操作模型 (Operation Model: Trigger / Action / Output / Evidence)

### OP-1: Diagnose vLLM CUDA OOM at startup
- **Trigger**: log shows `torch.OutOfMemoryError: CUDA out of memory` during engine init or warmup.
- **Action**:
  1. Lower `--max-model-len` to the realistic max (`prompt + output`), not the model's architectural max [markaicode.com 2026].
  2. Lower `--gpu-memory-utilization` to `0.85` if other processes share the GPU; raise to `0.95` if vLLM is alone and KV cache is too small.
  3. Add `--kv-cache-dtype fp8` (Ampere+) or `--enforce-eager` (skip CUDA-graph reservation).
  4. Reduce `--max-num-seqs` (e.g. 256 → 64 → 16).
  5. If still OOM at TP=1: bump `--tensor-parallel-size` to shard the model.
- **Output**: engine starts; KV cache occupancy logged at boot is non-zero and <100%.
- **Evidence**: [docs.vllm.ai/en/stable/configuration/conserving_memory/]; [discuss.vllm.ai/t/cuda-failure-out-of-memory/524]; [github.com/vllm-project/vllm/issues/188].

### OP-2: Pick quantization for an open-weights model
- **Trigger**: deploying a model that doesn't fit at BF16, or where cost/throughput matters more than peak quality.
- **Action**:
  1. **Hopper/Ada/Blackwell GPU available?** → prefer **FP8** (effectively lossless across model scales) [arxiv.org/abs/2411.02355].
  2. **No FP8 hardware, need 4× compression?** → AWQ-4 (better stability at 4-bit) or GPTQ-4 (slightly better on code tasks) [arxiv.org/abs/2411.02355].
  3. **Avoid INT3 / 3-bit**: ~6-point average drop, not worth it.
  4. Verify on a held-out eval set in your domain before shipping.
- **Output**: chosen `--quantization {fp8|awq|gptq|...}` flag; documented expected accuracy delta.
- **Evidence**: [arxiv.org/abs/2411.02355 "Give Me BF16 or Give Me Death"]; [docs.gpustack.ai vLLM quantization].

### OP-3: Configure tensor/pipeline parallelism
- **Trigger**: model too large for one GPU; multi-GPU or multi-node deployment.
- **Action**:
  1. **One node + NVLink**: `--tensor-parallel-size=<GPUs in node>`, PP=1.
  2. **One node + only PCIe** (e.g. L40S, consumer cards): consider `--pipeline-parallel-size` instead of large TP — all-reduce over PCIe will tank TP throughput [docs.vllm.ai parallelism_scaling].
  3. **Multi-node**: `TP=GPUs/node`, `PP=#nodes`. Use InfiniBand if possible.
  4. **MoE (Mixtral/DSv3)**: combine **DP attention + EP/TP on MoE layers**.
  5. Test TP=2 vs TP=4 vs 2×replicas-of-TP=2 — replicas often win on throughput-per-dollar when one replica already saturates [developers.redhat.com 2026 step 5].
- **Output**: chosen TP/PP/DP/EP config with measured tokens/s on real workload.
- **Evidence**: [docs.vllm.ai/en/stable/serving/parallelism_scaling/].

### OP-4: Enable prefix caching
- **Trigger**: workload has repeated prefixes (shared system prompt, few-shot examples, RAG with stable instructions, multi-turn chat with same persona).
- **Action**: launch with `--enable-prefix-caching` (in V1, often on by default).
- **Output**: prefill TTFT drops on cache-hit requests; KV occupancy may rise (cached blocks held longer).
- **Caveats**:
  - APC accelerates **prefill only**; if outputs are long and prefixes don't repeat, gain ≈ 0 [docs.vllm.ai automatic_prefix_caching].
  - In multi-replica clusters, naive round-robin scatters prefix-sharing requests → use **prefix-aware routing** (e.g. Ray Serve LLM, llm-d) [llm-d.ai/blog/kvcache-wins-you-can-see].
  - Multi-tenant privacy: use **cache salting** to avoid cross-tenant prefix collisions [github.com/vllm-project/vllm/issues/16016].
- **Evidence**: [docs.vllm.ai/en/stable/design/prefix_caching/].

### OP-5: Triage live performance (TTFT vs ITL)
- **Trigger**: SLA miss, user complaints, queueing alerts.
- **Action** (5-step Red Hat triage):
  1. **Split symptom**: high TTFT vs high ITL? (Prometheus histograms.)
  2. **Saturation**: `num_requests_waiting` > 0 sustained → engine queue-bound; check `num_requests_running`.
  3. **KV health**: KV cache occupancy near 100% with rising preemption count → drop `--max-num-seqs` or quantize KV to FP8.
  4. **Sequence-length correlation**: ITL ~40 ms/token implies ~40 s per 1000 tokens output — sometimes the workload is the answer.
  5. **Interconnect check**: PCIe-only with TP=4? Drop to TP=2 + 2 replicas.
- **Output**: identified bottleneck class (queue / compute / memory / interconnect) and one targeted change.
- **Evidence**: [developers.redhat.com 2026 5-steps-triage].

### OP-6: Decide on speculative decoding
- **Trigger**: latency-bound workload, model ≥ 13B, low/medium QPS.
- **Action**:
  - If draft/EAGLE-3 weights exist for the target model → enable; expect up to **2.5×** decode speedup [developers.redhat.com 2025 eagle3].
  - If not → try **n-gram** (~1.17×, no extra weights, ~zero risk) [jarvislabs.ai].
  - **Skip** speculative decoding if QPS is high (large batches already saturate compute → speculation wastes capacity).
  - Always benchmark: poor hyperparameter tuning can degrade cost-per-token by up to **175%** [arxiv.org/pdf/2601.11580].
- **Output**: `--speculative-config` JSON, with measured tokens/s delta on representative traffic.
- **Evidence**: [docs.vllm.ai/en/latest/features/speculative_decoding/].

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1: Throughput vs Latency — how aggressively to batch?

**Situation**: A team serves Llama-3-70B-FP8 on 2×H100. P50 TTFT is fine at 250 ms, but P99 spikes to 4 s when traffic bursts. They consider raising `--max-num-seqs` from 64 to 256 to handle bursts.

**Tension**:
- Higher `max_num_seqs` → more concurrency → higher throughput, but also more contention for KV cache → preemption + head-of-line blocking on prefills.
- Higher `max_num_batched_tokens` → better TTFT (more prefill per step) → worse ITL for streaming requests already mid-decode.

**Resolution heuristic**:
- If P99 spike correlates with `num_requests_waiting > 0` and KV occupancy < 80%: raise `max_num_seqs`.
- If KV occupancy hits 100% and **preemption counter rises**: do NOT raise; either quantize KV to FP8, add a replica, or shorten `max_model_len`.
- For latency-sensitive interactive workloads: **lower** `max_num_batched_tokens` (e.g. 2048) to favor decode/ITL; for batch/offline: **raise** (≥8192) to favor TTFT/throughput [docs.vllm.ai optimization; anyscale.com].

**Evidence**: [developers.redhat.com 2026 5-steps-triage]; [medium.com/@kaige.yang0110].

### Dilemma 2: 4-bit AWQ vs FP8 — is the quality drop worth the VRAM?

**Situation**: Deploying Qwen-72B on a single H100 (80 GB). At BF16, model is 144 GB → doesn't fit. Options: (a) FP8, 72 GB → fits with tight KV budget; (b) AWQ-4, 36 GB → comfortable KV budget, larger batches.

**Tension**:
- FP8 is empirically **near-lossless** across all model scales [arxiv.org/abs/2411.02355], but leaves little KV headroom on a single H100 → smaller batches → less throughput.
- AWQ-4 frees ~36 GB for KV → 2–3× more concurrent sequences → higher throughput, but loses ~1.6 average points on benchmarks (more on reasoning-heavy/long-context tasks).

**Resolution heuristic**:
- **Quality-critical** (legal, medical, coding agent): FP8 + accept smaller batch, or move to 2×H100 with TP=2 and stay at BF16.
- **Throughput-critical** (bulk classification, summarization, search re-ranking): AWQ-4 wins; validate on YOUR eval set, not generic benchmarks (real-world drop on code can exceed academic-benchmark drop) [arxiv.org/abs/2411.02355].
- **Mixed**: serve two replicas — FP8 for premium tier, AWQ for free tier.

**Evidence**: [arxiv.org/abs/2411.02355]; [docs.gpustack.ai vLLM quantization].

### Dilemma 3: TP=4 single replica vs 2×TP=2 replicas for a 70B model

**Situation**: 4×A100-80GB available, NVLink. Choice: one big replica (TP=4, max single-request latency optimized) or two replicas (TP=2, more concurrency).

**Tension**:
- **TP=4** lowers single-request latency (model layers parallelized further), but all-reduce overhead grows quadratically; on saturated workloads, marginal throughput per added GPU diminishes.
- **2×TP=2** doubles independent throughput (each replica handles its own batch) and survives one-replica failures, but a single request can never go faster than TP=2.

**Resolution heuristic**:
- If P99 latency SLA is the binding constraint and single-request decode is the bottleneck → **TP=4**.
- If throughput-per-dollar is the constraint, requests are independent, and average request latency at TP=2 is acceptable → **2×TP=2 replicas**; this is the Red Hat triage step-5 recommendation [developers.redhat.com 2026].
- Always check NVLink topology: across-NUMA TP=4 on PCIe degrades faster than two NVLink-paired TP=2 islands [servermo.com vLLM multi-gpu].
- Benchmark with `vllm bench serve` on representative ISL/OSL.

**Evidence**: [docs.vllm.ai parallelism_scaling]; [docs.jarvislabs.ai scaling-llm-inference-dp-pp-tp].

### Dilemma 4: Prefix caching ROI — is the RAM cost justified?

**Situation**: Production RAG service. Each request has a 2 KB system prompt + 4–16 KB context + short user query. They wonder whether `enable_prefix_caching` helps enough to justify the held KV blocks.

**Tension**:
- APC reduces **prefill** time on cache-hit; if 90% of requests share the system prompt, prefill of those tokens is free → big TTFT win.
- Cached blocks **stay resident** in KV memory → fewer free blocks for new requests → can trigger preemption on bursty traffic.

**Resolution heuristic**:
- **Enable** when shared-prefix fraction ≥ ~30% and outputs are short-to-medium (APC helps prefill, not decode) [docs.vllm.ai automatic_prefix_caching].
- **Disable / tune** when requests are unique and long-output dominated — caching just consumes KV with no hit-rate.
- For multi-replica deployments: pair with **prefix-aware routing** so requests with the same prefix land on the same replica; otherwise you pay the cache cost N times for 1/N hit-rate [llm-d.ai/blog/kvcache-wins-you-can-see].
- For multi-tenant: enable **cache salting** for privacy [github.com/vllm-project/vllm/issues/16016].

**Evidence**: [docs.vllm.ai/en/stable/design/prefix_caching/]; [bentoml.com/llm/inference-optimization/prefix-caching].

### Dilemma 5: Speculative decoding — when is the complexity worth it?

**Situation**: Single-user, latency-sensitive coding assistant on Llama-3-70B. Decode dominates total latency.

**Tension**:
- EAGLE-3 can deliver up to **2.5× decode speedup** for low-QPS workloads [developers.redhat.com 2025 eagle3], but requires a trained EAGLE head, increases VRAM, and is sensitive to hyperparameters (bad config → -175% cost) [arxiv 2601.11580].
- n-gram speculation is cheap (no extra weights) but only ~1.17× speedup [jarvislabs.ai].
- At high QPS, the GPU is already saturated by real batch work; speculative compute steals capacity instead of filling idle cycles.

**Resolution heuristic**:
- **Low QPS, single-stream-latency-bound, EAGLE/MTP head available** → enable model-based speculation. Worth the engineering cost.
- **No draft weights, want easy win** → try n-gram first; if speedup < ~1.1×, disable.
- **High QPS / throughput-bound** → skip speculation, invest in quantization + parallelism instead.
- Always A/B against the non-speculative baseline on representative traffic.

**Evidence**: [docs.vllm.ai/en/latest/features/speculative_decoding/]; [developers.redhat.com 2025 fly-eagle3-fly].

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Anti-pattern 1: Setting `max_model_len` to the model's architectural max "just in case"
A Llama-3.1 model supports 128k context. If you serve 4k-prompt workloads but set `--max-model-len 131072`, vLLM reserves KV-cache slots for the worst case → smaller batches → throughput collapse. **Set it to your realistic max** (longest_prompt + longest_output + safety margin) [markaicode.com 2026].

### Anti-pattern 2: Treating prefix caching as a panacea
APC accelerates **prefill only**. If outputs are long and prefixes don't repeat, gain ≈ 0 — and you've consumed KV memory for nothing [docs.vllm.ai automatic_prefix_caching]. Measure shared-prefix fraction before enabling for high-pressure workloads.

### Anti-pattern 3: TP across PCIe-only GPUs
Tensor parallelism issues an all-reduce after each layer. NVLink (≈900 GB/s bidirectional) handles it; PCIe Gen4 x16 (≈32 GB/s, ~28× slower) does not [spheron.network 2026]. On L40S / consumer cards / cross-NUMA setups, **use pipeline parallelism or independent replicas instead** [docs.vllm.ai parallelism_scaling].

### Anti-pattern 4: Picking quantization off academic benchmarks alone
Academic benchmarks (MMLU, HellaSwag) show GPTQ ≈ AWQ; **real coding workloads can show meaningfully larger gaps** between methods, and quality at INT3 collapses (~6-point drop) [arxiv.org/abs/2411.02355]. Always test on your eval set.

### Anti-pattern 5: Using vLLM for the wrong workload
- **Small models / hobby use / 1 user, 1 GPU**: Ollama or llama.cpp give you 5-minute setup; vLLM's scheduler overhead doesn't pay off [aimadetools.com 2026].
- **CPU-only / edge / Apple Silicon production**: llama.cpp (GGUF) is the right tool; vLLM's Metal/MPS support is experimental as of 2026 [aimadetools.com 2026].
- **Embedding-only workloads**: vLLM supports embedding endpoints, but TEI (Text Embeddings Inference) or sentence-transformers servers are often simpler/faster for that single purpose.
- **Pure throughput, single-vendor NVIDIA, willing to spend 1–2 weeks tuning**: TensorRT-LLM can beat vLLM by 30–50% on throughput but locks you in [n1n.ai 2026].

### Anti-pattern 6: Ignoring CPU provisioning
vLLM needs minimum **`2 + N` physical CPU cores for N GPUs**; under-provisioning CPUs makes the API server, tokenizer, and detokenizer the bottleneck before the GPU is touched [docs.vllm.ai/en/stable/configuration/optimization/]. Scale CPU and use `--api-server-count` when needed.

### Anti-pattern 7: `--enforce-eager` in production "for stability"
`--enforce-eager` skips CUDA graph capture → slower decode. It's a debugging/memory-OOM workaround, not a steady-state production setting. Fix the underlying OOM (KV dtype, max_model_len, max_num_seqs) and re-enable CUDA graphs.

### Boundaries

vLLM is the right tool when:
- ✅ ≥10 concurrent requests OR variable request length OR shared prefixes.
- ✅ NVIDIA / AMD GPU with ≥1 device of sufficient VRAM.
- ✅ Decoder-only or supported architecture (Llama, Qwen, Mixtral, DeepSeek, Gemma, Phi, multimodal: LLaVA / Qwen-VL).
- ✅ Throughput, cost-per-token, or P50 latency under load is the goal.

vLLM is the **wrong** tool when:
- ❌ Single user, single stream, dev laptop.
- ❌ CPU/edge/mobile, no GPU.
- ❌ Architecture not yet supported (check the model list — Mamba/hybrid coverage is growing but incomplete).
- ❌ You need state-machine-driven structured generation tighter than vLLM's `guided_decoding` (consider SGLang for complex agent state machines).

---

## 7. 生态对照 (Ecosystem Comparison)

| Engine | Sweet spot | When to pick over vLLM |
|---|---|---|
| **vLLM** | Production GPU serving, mixed traffic, open weights, vendor-neutral | Default first choice for throughput-oriented LLM serving in 2026 |
| **TGI** (HuggingFace) | Was the HF default | Officially in maintenance mode; HF themselves now recommend vLLM or SGLang [yottalabs.ai 2026] |
| **SGLang** | Heavy prefix sharing, agent/RAG state machines, structured generation | ~29% higher throughput than vLLM when requests share context (chatbots, RAG, agents) thanks to RadixAttention prefix tree [n1n.ai 2026] |
| **TensorRT-LLM** | Single-vendor NVIDIA, max throughput, willing to invest setup | Up to 30–50% higher throughput than vLLM in high-concurrency NVIDIA-only deployments; 1–2 weeks setup; vendor lock-in [n1n.ai 2026] |
| **llama.cpp** | CPU, edge, Apple Silicon, single-user, GGUF | No GPU available; ≤1 concurrent user; minimal-deps deploy [aimadetools.com 2026] |
| **Ollama** | Local dev, prototyping, model switching | Developer ergonomics over throughput; 5-minute setup [contracollective.com 2026] |

**Common pattern**: develop on Ollama → benchmark with vLLM → consider SGLang if prefix-sharing workload → consider TensorRT-LLM only if NVIDIA-locked and engineering budget is large.

---

## Quick-start reference command

A production-ish vLLM serve for Llama-3.1-70B-Instruct-FP8 on 2×H100 with NVLink, RAG-style workload:

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

Then triage with the §4 OP-5 5-step workflow on real traffic before tuning further.

---

## Cited sources (primary)

- PagedAttention paper: https://arxiv.org/abs/2309.06180
- vLLM docs: https://docs.vllm.ai/en/stable/
- vLLM GitHub: https://github.com/vllm-project/vllm
- Quantization tradeoffs: https://arxiv.org/abs/2411.02355
- Performance triage: https://developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance
- EAGLE-3 results: https://developers.redhat.com/articles/2025/07/01/fly-eagle3-fly-faster-inference-vllm-speculative-decoding
- Engine comparison: https://www.yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared
