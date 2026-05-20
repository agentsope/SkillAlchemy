# vllm-sop skill

Decision SOP for serving LLMs with **vLLM** — extracted as a tool skill for coder-agent use.

This is one of seven projects in a horizontal landscape study of LLM-app frameworks (LangGraph, LlamaIndex, DSPy, CrewAI, vLLM, Aider, Dify). The goal across the set is to capture each tool's **operating system** — its decision patterns, when-to-use logic, and dilemma resolution — rather than its API surface.

## Scope

- **Domain**: high-throughput LLM inference serving on GPU.
- **Anchors**: PagedAttention (Kwon et al., SOSP 2023, arxiv 2309.06180), continuous batching (Orca-style iteration-level scheduling), prefix caching, tensor/pipeline/expert parallelism, quantization (FP8/AWQ/GPTQ), speculative decoding.
- **Activation**: when a coder-agent is choosing or tuning an inference engine, debugging vLLM throughput/latency/OOM, or comparing vLLM against TGI/SGLang/TensorRT-LLM/llama.cpp.

## Layout

```
vllm-sop-skill/
├── SKILL.md                          # Main SOP — 7 sections (activation → ecosystem)
├── README.md                         # This file
├── references/
│   ├── R1-architecture.md            # PagedAttention, scheduler, prefill/decode split
│   ├── R2-sop-workflow.md            # 7-step deploy workflow with decision points
│   ├── R3-dilemma-cases.md           # 5 cited dilemma cases
│   ├── R4-anti-patterns.md           # 7 anti-patterns + boundary conditions
│   └── R5-ecosystem-context.md       # vLLM vs TGI/SGLang/TensorRT-LLM/llama.cpp/Ollama
└── intermediate/
    └── operation_candidates.json     # Raw trigger/action/output/evidence operations
```

## Method

Source mining used WebSearch + WebFetch against: the PagedAttention paper, docs.vllm.ai, the vLLM GitHub README, Red Hat tuning guides, comparison benchmarks (2025–2026 vintage), and a quantization-tradeoffs preprint (arxiv 2411.02355). Every load-bearing claim in SKILL.md carries an inline `[source]` tag. No fabrication.

## Surprises worth noting

1. The bottleneck was never compute — it was KV-cache fragmentation. Pre-vLLM engines used 20–40% of GPU memory.
2. TP=4 across PCIe is often slower than 2 independent TP=2 replicas. Interconnect topology beats parallelism degree.
3. Speculative decoding can make things 175% worse with bad hyperparameters, despite the up-to-2.5× best-case headline.
