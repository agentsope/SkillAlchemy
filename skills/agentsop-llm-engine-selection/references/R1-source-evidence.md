# R1. Source Evidence — engine comparisons cited in SKILL.md

All performance claims in SKILL.md resolve here. Numbers are 2025–2026 vintage; re-verify in subsequent quarters.

## Headline performance gaps

### vLLM vs HuggingFace Transformers
- **Claim**: 14–24× higher throughput for Llama models on NVIDIA GPUs.
- **Source**: yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared (2026).
- **Mechanism**: PagedAttention + continuous batching close the 20–40% pre-vLLM GPU memory utilization gap to ~100% [arxiv.org/abs/2309.06180].

### vLLM vs early TGI
- **Claim**: 2.2–3.5× higher throughput at vLLM launch.
- **Source**: yottalabs.ai 2026.
- **Caveat**: TGI added continuous batching later; gap narrowed before TGI entered maintenance mode.

### SGLang vs vLLM on shared-context
- **Claim**: ~29% higher throughput when requests share prefix.
- **Source**: explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13.
- **Mechanism**: RadixAttention prefix tree caches at a finer granularity than vLLM's hash-based APC for shared-instruction workloads (chatbots, agents, RAG).
- **Boundary**: parity on pure-batch workloads; SGLang wins specifically when prefix-share fraction is high.

### TensorRT-LLM vs vLLM
- **Claim**: +30–50% throughput in NVIDIA-only high-concurrency settings.
- **Source**: explore.n1n.ai 2026; spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks.
- **Cost**: 1–2 weeks per-model setup; engine rebuild on (model × precision × max-batch × max-seq) change; NVIDIA proprietary license.

### llama.cpp vs vLLM at scale
- **Claim**: vLLM wins decisively serving many concurrent users; llama.cpp wins single-user.
- **Source**: aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi.
- **Mechanism**: llama.cpp's per-request overhead does not amortize across requests; no PagedAttention / continuous batching analog.

### Ollama vs vLLM in production
- **Claim**: "Best dev UX, worst throughput" — pair Ollama (dev) with vLLM (prod).
- **Source**: contracollective.com/blog/llama-cpp-vs-mlx-ollama-vllm-apple-silicon-2026.
- **Boundary**: Ollama added concurrent-request support mid-2025; small clusters viable, but >10 QPS production wastes 80–95% of GPU vs vLLM.

## Hardware-topology evidence

### Tensor parallel requires NVLink
- **Claim**: PCIe Gen4 x16 (~32 GB/s) is ~28× slower than NVLink (~900 GB/s) for the all-reduce after every layer.
- **Source**: spheron.network 2026; docs.vllm.ai parallelism_scaling.
- **Implication**: PCIe-only TP collapses; use pipeline parallelism or independent replicas.

### Cross-NUMA pitfalls
- **Claim**: Cross-NUMA all-reduce on the same node is as bad as PCIe-only.
- **Source**: docs.vllm.ai multi-gpu guidance; developers.redhat.com 2026 step-5.

## License / lock-in evidence

### TensorRT-LLM proprietary
- **Source**: NVIDIA developer license terms; spheron.network 2026.
- **Implication**: hard filter for open-core / air-gapped / regulated shops.

### TGI maintenance status
- **Claim**: HuggingFace themselves now recommend vLLM or SGLang over TGI.
- **Source**: yottalabs.ai 2026.
- **Implication**: do not pick TGI for new projects in 2026.

## Quantization evidence

### FP8 near-lossless on Hopper/Ada+
- **Claim**: FP8 weights + KV cache produce effectively zero quality drop across model scales.
- **Source**: arxiv.org/abs/2411.02355 ("Give Me BF16 or Give Me Death").
- **Boundary**: requires Hopper / Ada / Blackwell hardware.

### AWQ-4 vs GPTQ-4
- **Claim**: ~1.6 point average benchmark drop at 4-bit; AWQ slightly more stable, GPTQ slightly better on code tasks. INT3 collapses (~6 point drop).
- **Source**: arxiv.org/abs/2411.02355.
- **Implication**: AWQ-4 / GPTQ-4 are viable; INT3 is not.

## Default-engine evidence

### vLLM as 2026 default
- **Sources**: yottalabs.ai 2026 (HF endorsement); github.com/vllm-project/vllm README (vendor-neutral hardware support: NVIDIA, AMD, Intel Gaudi, Google TPU, Huawei Ascend, x86/ARM/PowerPC CPU, Apple Silicon experimental); 200+ supported architectures including MoE and multimodal.

## Apple Silicon evidence

### MLX vs vLLM on Mac
- **Claim**: vLLM's Metal/MPS support is experimental as of 2026; MLX or llama.cpp Metal is the production-grade Mac path.
- **Source**: contracollective.com 2026; aimadetools.com 2026.

## Cited URLs (full list)

- https://www.yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared
- https://explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13
- https://aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/
- https://contracollective.com/blog/llama-cpp-vs-mlx-ollama-vllm-apple-silicon-2026
- https://developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case
- https://developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance
- https://spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks
- https://arxiv.org/abs/2309.06180
- https://arxiv.org/abs/2411.02355
- https://github.com/vllm-project/vllm
- https://sglang.ai/blog
- https://docs.vllm.ai/en/stable/
- https://marktechpost.com/2025/11/07/comparing-the-top-6-inference-runtimes-for-llm-serving-in-2025/
