# R4. Anti-Patterns & Boundaries

The recurring mistakes that show up in vLLM GitHub issues, forum threads, and production post-mortems.

## Anti-pattern 1: `max_model_len` set to the model's architectural max

Llama-3.1 supports 128k. If your real workload tops out at 4k prompts but you launch with `--max-model-len 131072`, vLLM **reserves KV-cache slots for the worst case** — block-pool sizing assumes any sequence might reach the configured max. Result: tiny batches, throughput collapse, OOM during warmup.

**Fix**: set `--max-model-len` to `realistic_max_prompt + realistic_max_output + safety_margin`.

Evidence: markaicode.com/errors/vllm-out-of-memory-fix/ (2026); docs.vllm.ai/en/stable/configuration/conserving_memory/.

---

## Anti-pattern 2: Prefix caching as a panacea

APC accelerates **only the prefill phase**. If outputs are long and prefixes don't repeat, the gain is ~0 — and you've consumed KV memory for cached-but-never-hit blocks, which can starve live requests during bursts.

**Fix**: measure shared-prefix fraction. Enable when ≥~30% of requests share a prefix AND outputs are short-to-medium. For unique-prompt, long-output workloads, prefix caching is overhead.

Evidence: docs.vllm.ai/en/stable/design/prefix_caching/; docs.vllm.ai/en/v0.7.0/features/automatic_prefix_caching.html.

---

## Anti-pattern 3: Tensor parallelism across PCIe-only GPUs

Tensor parallelism issues an all-reduce after each layer. NVLink (≈900 GB/s bidirectional) handles it; PCIe Gen4 x16 (≈32 GB/s, **~28× slower**) does not — the all-reduce becomes the serial bottleneck.

**Fix**: on L40S / consumer cards / cross-NUMA setups, use **pipeline parallelism** or **independent replicas** instead. vLLM docs explicitly call this out: "leverage pipeline parallelism instead of tensor parallelism for higher throughput and lower communication overhead" [docs.vllm.ai parallelism_scaling].

Evidence: docs.vllm.ai/en/stable/serving/parallelism_scaling/; spheron.network/blog/vllm-production-deployment-2026/; servermo.com/howto/vllm-multi-gpu-setup/.

---

## Anti-pattern 4: Picking quantization off academic benchmarks alone

Academic benchmarks (MMLU, HellaSwag) routinely show AWQ-4 ≈ GPTQ-4 ≈ FP16. Real-world workloads — especially **coding tasks** — can show meaningfully larger gaps:
- GPTQ shows notable improvements over AWQ on real-world coding benchmarks.
- INT3 collapses ~6 points avg.
- FP8 (W8A8-FP) is the only genuinely near-lossless option across all model scales.

**Fix**: always validate on your domain eval set, not just generic leaderboards.

Evidence: arxiv.org/abs/2411.02355 ("Give Me BF16 or Give Me Death"); ionio.ai/blog/llm-quantize-analysis.

---

## Anti-pattern 5: Using vLLM for the wrong workload

| Wrong workload | Right tool |
|---|---|
| 1 user, 1 GPU, dev laptop | Ollama (5-min setup) [contracollective.com 2026] |
| CPU-only / edge / no GPU | llama.cpp (GGUF) [aimadetools.com 2026] |
| Apple Silicon production | llama.cpp / MLX — vLLM Metal/MPS is experimental as of 2026 |
| Embedding-only service | TEI (Text Embeddings Inference) or sentence-transformers server |
| Single-vendor NVIDIA, 1–2 weeks setup time, max throughput | TensorRT-LLM (+30–50% throughput, vendor lock-in) [n1n.ai 2026] |
| Heavy prefix sharing / agent state machines | SGLang (~29% higher throughput on shared-context) [n1n.ai 2026] |

vLLM is overkill below ~10 concurrent requests with stable request length — the scheduler overhead doesn't pay off.

Evidence: aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/; developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case.

---

## Anti-pattern 6: Under-provisioned CPUs

vLLM official guidance: minimum **`2 + N` physical CPU cores for N GPUs**. CPU is needed for the API server, tokenizer, detokenizer, scheduler, and Python orchestration. Under-provisioned CPUs make the API server the bottleneck before the GPU is touched — leading to "fast GPU, low throughput" confusion.

**Fix**: provision CPUs accordingly; use `--api-server-count` to parallelize input processing if CPU still bottlenecks.

Evidence: docs.vllm.ai/en/stable/configuration/optimization/.

---

## Anti-pattern 7: `--enforce-eager` as a steady-state production setting

`--enforce-eager` disables CUDA graph capture → slower decode (CUDA graphs amortize kernel-launch overhead). It's a **debugging / OOM-workaround** flag, not a production setting.

**Fix**: if you needed it to avoid OOM, fix the underlying cause (`max_model_len`, `max_num_seqs`, `kv_cache_dtype fp8`) and re-enable CUDA graphs.

Evidence: docs.vllm.ai/en/stable/configuration/conserving_memory/; markaicode.com (2026).

---

## Anti-pattern 8: Ignoring CUDA-graph reservation under variable sequence lengths

vLLM records static CUDA graphs for the decode phase. The reservation is permanent; under wildly-varying sequence lengths, the graph's allocation becomes fragmented, leading to **OOMs even when `nvidia-smi` shows free memory** [markaicode.com 2026].

**Fix**: tune `compilation_config.cudagraph_capture_sizes` to match your real batch-size distribution; or disable graphs (`--enforce-eager`) during triage to isolate the cause.

---

## Anti-pattern 9: Multi-tenant prefix-cache collisions

If two tenants happen to issue the same prefix tokens, they hit each other's cached KV — a side-channel privacy/auditing concern.

**Fix**: enable **cache salting** (per-tenant salt prepended to cache key) — RFC tracked in github.com/vllm-project/vllm/issues/16016.

---

## Boundary conditions — when vLLM IS the right tool

- ✅ **≥10 concurrent requests** OR variable request length OR shared prefixes.
- ✅ NVIDIA or AMD GPU(s) with sufficient combined VRAM.
- ✅ Decoder-only or supported architecture (Llama, Qwen, Mixtral, DeepSeek, Gemma, Phi, multimodal: LLaVA / Qwen-VL).
- ✅ Goal is **throughput, cost-per-token, or P50 latency under load**.

## Boundary conditions — when vLLM IS NOT

- ❌ Single user, single stream, dev laptop → Ollama.
- ❌ CPU / edge / mobile / no GPU → llama.cpp.
- ❌ Architecture not yet supported (check the model list; Mamba/hybrid coverage is growing but incomplete).
- ❌ Need tighter structured generation than vLLM's `guided_decoding` (consider SGLang/Outlines for state-machine generation).
- ❌ Apple Silicon production deployment (as of 2026, vLLM MPS is experimental).
