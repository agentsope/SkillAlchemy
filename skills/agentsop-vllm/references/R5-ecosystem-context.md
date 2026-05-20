# R5. Ecosystem Context — vLLM vs Peers

## The competitive landscape as of 2026

| Engine | Origin / sponsor | Sweet spot | Status |
|---|---|---|---|
| **vLLM** | UC Berkeley Sky Lab → broad community + Red Hat | Production GPU serving, mixed traffic, vendor-neutral | Industry default for open-source LLM serving |
| **SGLang** | UC Berkeley → LMSYS | Heavy prefix sharing, agent state machines, structured gen | Co-recommended with vLLM by HF for production [yottalabs.ai 2026] |
| **TensorRT-LLM** | NVIDIA | NVIDIA-only, max throughput, large eng-budget tuning | +30–50% over vLLM in high-concurrency NVIDIA setups [n1n.ai 2026] |
| **TGI** (Text Generation Inference) | HuggingFace | Was the HF default | **Maintenance mode**; HF themselves now recommend vLLM or SGLang [yottalabs.ai 2026] |
| **llama.cpp** | ggerganov | CPU, edge, Apple Silicon, GGUF, minimal deps | Best for ≤1 concurrent user / no-GPU [aimadetools.com 2026] |
| **Ollama** | Wraps llama.cpp | Local dev, prototyping, model switching | "Best dev UX, worst throughput" — pair with vLLM for prod [contracollective.com 2026] |
| **MLX / vllm-mlx** | Apple | Apple Silicon | The Mac path; vLLM core's Metal support is still experimental in 2026 [macgpu.com] |

## Headline performance comparisons (2025–2026 vintage)

- **vLLM vs HF Transformers**: vLLM is **14–24× higher throughput** for Llama models on NVIDIA GPUs [yottalabs.ai 2026].
- **vLLM vs early TGI**: vLLM was **2.2–3.5× higher throughput** for Llama at launch [yottalabs.ai 2026].
- **SGLang vs vLLM**: SGLang often outperforms vLLM in throughput and TTFT, with **~29% higher throughput when requests share context** (chatbots, RAG, agents) thanks to RadixAttention prefix tree [n1n.ai 2026].
- **TensorRT-LLM vs vLLM**: In high-concurrency, TRT-LLM can be **30–50% higher throughput**, but demands **1–2 weeks of setup** and **vendor lock-in** [n1n.ai 2026].
- **llama.cpp vs vLLM** (serving many concurrent users): vLLM wins decisively; llama.cpp's per-request overhead does not scale.

## Why vLLM wins by default

1. **Vendor neutrality**: NVIDIA, AMD, Intel Gaudi, Google TPU, Huawei Ascend, x86/ARM/PowerPC CPU, Apple Silicon (experimental) [github.com/vllm-project/vllm README].
2. **Model breadth**: 200+ architectures, including MoE (Mixtral, DeepSeek-V3), hybrid (Mamba), multimodal (LLaVA, Qwen-VL).
3. **OpenAI-compatible API**: drop-in replacement for hosted-API clients.
4. **Ecosystem momentum**: tight integrations with Ray Serve, KServe, llm-d, BentoML, NVIDIA Triton, vLLM Production Stack, plus the original PagedAttention research backing.
5. **HF blessing**: HF themselves recommend vLLM over their own (now-maintenance-mode) TGI.

## When to reach past vLLM

### → SGLang
- Workload is **agent-heavy / RAG-heavy** with stable prefixes (RadixAttention's prefix-tree caching is more aggressive than vLLM's hash-based APC).
- Need complex structured-output state machines beyond what vLLM's `guided_decoding` covers.

### → TensorRT-LLM
- **NVIDIA-only** deployment, **NVIDIA-only** roadmap.
- Throughput-per-GPU is the dominant cost; engineering budget for 1–2 weeks of model conversion + tuning is acceptable.
- Willing to accept vendor lock-in.

### → llama.cpp / Ollama
- **No GPU** OR **≤1 concurrent user** OR **edge / mobile / Apple Silicon**.
- Minimal-dependency deploy (single binary, GGUF file).
- "Just want to run a model on my laptop."

### → TGI
- Existing HF-stack deployment that already runs TGI and isn't broken. Don't migrate just to migrate — but for new projects in 2026, default to vLLM or SGLang.

## The common production pattern in 2026

```
Local development       → Ollama (model switching, prototyping)
                          ↓
Production benchmarking  → vLLM (default)
                          ↓
If prefix-heavy workload → A/B with SGLang
                          ↓
If NVIDIA-locked + 1–2wk → A/B with TensorRT-LLM
                          ↓
If CPU/edge segment      → llama.cpp/GGUF for that segment
```

vLLM occupies the **default production slot** for open-weights LLM serving in 2026.

## Sources

- yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared
- explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13
- aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/
- contracollective.com/blog/llama-cpp-vs-mlx-ollama-vllm-apple-silicon-2026
- marktechpost.com/2025/11/07/comparing-the-top-6-inference-runtimes-for-llm-serving-in-2025/
- spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks/
- developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case
- github.com/vllm-project/vllm (README)
