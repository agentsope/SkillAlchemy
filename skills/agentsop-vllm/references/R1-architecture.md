# R1. Architecture & Mental Model

## The problem vLLM solved

Before vLLM, LLM serving engines (HuggingFace Transformers, FasterTransformer, naive batching) pre-allocated a contiguous KV-cache slot per request, sized for the **maximum possible output length**. This caused two pathologies:

- **Internal fragmentation**: a request reserved 2048 token-slots but used 100 → 1948 wasted slots, frozen for the lifetime of the request.
- **External fragmentation**: variable-length allocations across requests left unusable gaps.

The empirical consequence: **early-2023 inference engines used only 20–40% of GPU memory** [arxiv.org/abs/2309.06180; zilliz.com/learn]. That ceiling on effective KV memory was the ceiling on batch size, which was the ceiling on throughput.

## PagedAttention: KV cache as virtual memory

vLLM's defining contribution (Kwon, Li, Zhuang, et al., SOSP 2023) applies classical OS paging to KV cache:

| OS analogy | vLLM concept |
|---|---|
| Page | **Block** (fixed-size; default 16 tokens, ~12.8 KB for a 13B model) |
| Virtual address space | Logical block sequence per request |
| Page table | **Block table** per request |
| Physical memory | GPU HBM, allocated as fixed-size physical blocks |
| Copy-on-write | Per-request CoW on shared prefix blocks |
| Page sharing | Prefix sharing across requests with common prompt prefix |

The PagedAttention kernel reads physically-scattered blocks via the block table and presents them to the attention computation as a logically contiguous KV sequence. Crucially, no block is held back for "potential future tokens" — physical blocks are allocated on demand, one block per ~16 new tokens.

**Result**: near-zero KV-memory waste → larger batch sizes → **2–4× throughput** vs FasterTransformer and Orca at equal latency [arxiv.org/abs/2309.06180]; **14–24× vs vanilla HuggingFace Transformers** [yottalabs.ai 2026].

### Block size tradeoff

Default block size is 16 tokens. Larger blocks → more parallel positions per kernel call → better GPU utilization, but also more internal fragmentation (a request whose length is not a multiple of block_size wastes the tail). Smaller blocks → less fragmentation but more kernel-launch and pointer-chasing overhead [medium.com/@mandeep0405]. 16 is the empirical sweet spot for most modern GPUs; the parameter is exposed but rarely changed.

## The scheduler: iteration-level (continuous) batching

vLLM inherits Orca's iteration-level scheduling (OSDI 2022) [medium.com/byte-sized-ai]:

- Static batching: one "batch" runs to completion; if request A generates 500 tokens and request B generates 20, B waits and the GPU idles on B's slot for 480 steps.
- Continuous batching: every decode step, the scheduler can swap a finished request out and admit a waiting one. The batch composition changes per iteration.

Orca alone gave **36.9× throughput** over FasterTransformer at equal latency targets [medium.com/byte-sized-ai]. vLLM stacks PagedAttention on top — taking control of dynamic memory allocation that Orca couldn't — for further gains.

## Prefill vs decode: two different workloads

| Phase | Compute character | Bottleneck | Scales with |
|---|---|---|---|
| **Prefill** | Compute-bound, very high SM utilization | FLOPs | Input length |
| **Decode** | Memory-bandwidth-bound, low SM utilization | HBM bandwidth | Batch size |

A long prefill (e.g. 8k-token RAG context) executed in one shot blocks all running decode steps → **head-of-line blocking** → ITL spikes for already-streaming requests [arxiv.org/pdf/2602.16603 FlowPrefill; docs.vllm.ai optimization].

**Chunked prefill** breaks long prefills into smaller chunks (e.g. 512 tokens) interleaved with decode steps in the same iteration. This trades a slight TTFT increase for sustained low ITL across concurrent streams. In vLLM V1, chunked prefill is default-on [docs.vllm.ai/en/stable/configuration/optimization/].

## Memory hierarchy actually used in production

```
GPU HBM
├── Model weights (BF16/FP8/INT4 depending on quantization)
├── KV cache (PagedAttention block pool — largest share when weights are quantized)
├── Activations (transient)
└── CUDA graph reservation (~hundreds of MB for captured graph)
```

`gpu_memory_utilization=0.90` means: reserve 90% of total HBM after model load for the **block pool + activations + CUDA graphs**. Lower it (0.85) when other processes share the GPU. Raise (0.95) when the engine is alone and KV is the bottleneck [docs.vllm.ai conserving_memory].

## Mental model summary

> **vLLM is a memory allocator with an LLM glued on top.** The PagedAttention block pool and the iteration-level scheduler are the actual product. Everything else (quantization, parallelism, spec decoding) feeds those two by making weights smaller, KV smaller, or filling decode bubbles.

## Sources

- arxiv.org/abs/2309.06180 (PagedAttention paper)
- medium.com/byte-sized-ai (Orca + continuous batching)
- medium.com/@mandeep0405 (block-size analysis)
- zilliz.com/learn (memory-fragmentation framing)
- docs.vllm.ai/en/stable/configuration/optimization/
- docs.vllm.ai/en/stable/configuration/conserving_memory/
- arxiv.org/pdf/2602.16603 (FlowPrefill, prefill scheduling)
