---
name: agentsop-llm-engine-selection
description: Cross-engine decision rubric for self-hosting or recommending an LLM serving stack. Picks among vLLM, SGLang, TensorRT-LLM, TGI, llama.cpp, Ollama, and MLX as a function of (hardware × workload × constraint), not "which is fastest". Activates whenever a coder-agent must choose, defend, or migrate a serving runtime.
domain: LLM inference engine selection
version: 0.1.0
dated: 2026-05
sources:
  - https://www.yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared
  - https://explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13
  - https://developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case
  - https://aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/
  - https://contracollective.com/blog/llama-cpp-vs-mlx-ollama-vllm-apple-silicon-2026
  - https://arxiv.org/abs/2309.06180
---

# LLM Engine Selection SOP

> **State-of-the-art warning.** This skill is dated **May 2026**. The inference-engine landscape moves in 3–6 month cycles (TGI exited maintenance into deprecation in late 2025; SGLang's RadixAttention regressed vLLM's lead in 2024; TensorRT-LLM dropped its proprietary-engine requirement in 2025; Ollama added concurrent-request support mid-2025). Re-verify before betting a quarter of eng budget on any choice below.

---

## 1. 何时激活 (When to activate)

Activate this skill any time a coder-agent must:

- **Pick** a serving stack for a new project (production hosting / batch / edge / dev laptop / multi-tenant SaaS / structured-output service).
- **Defend** an existing stack against a "let's switch to X" pressure.
- **Migrate**: justify or block a swap (e.g. TGI → vLLM, Ollama → vLLM, vLLM → TensorRT-LLM).
- **Mix**: design a multi-tier deployment (e.g. premium tier on TensorRT-LLM, free tier on vLLM-AWQ, dev on Ollama).
- **Audit** a recommendation that smells like benchmark-cherry-picking ("X is 5× faster").

Do **not** activate for:
- Tuning a single chosen engine — defer to the dedicated skill (`vllm`, `sglang`, `tensorrt-llm`, `llama-cpp`).
- Training/fine-tuning runtime selection — different problem class (`accelerate`, `deepspeed`, `axolotl`).
- Hosted-API procurement (OpenAI / Anthropic / Bedrock) — engine choice doesn't apply.

---

## 2. 核心心智模型 (Core Mental Model)

**Engine choice is a function of (hardware × workload × constraint), not "which is fastest".**

There is no global ranking. Every "X beats Y by N%" headline holds only inside an unstated (hardware, batch size, ISL/OSL, model, quantization, concurrency) tuple. Change any axis and the ranking flips.

### 2.1 The four-axis decision space

1. **Hardware axis** — NVIDIA H100/A100 (NVLink) ≠ NVIDIA L40S/RTX (PCIe-only) ≠ AMD MI300 ≠ Apple Silicon ≠ CPU-only. The interconnect topology matters as much as raw FLOPS [spheron.network 2026]. PCIe-only tensor parallelism collapses; NVLink rescues it.
2. **Workload axis** — production multi-user (throughput) vs latency-bound single-stream vs offline batch vs edge single-user vs structured-output service vs multi-LoRA SaaS. Each has a different winner.
3. **Constraint axis** — license (Apache vs proprietary), vendor lock-in tolerance, engineering budget (1 day vs 2 weeks setup), commercial-use clauses, on-prem vs cloud, P50 vs P99 SLA.
4. **Maturity axis** — the engine's coverage of YOUR model family. A 2025-launched MoE may run on vLLM day-1 but need a 3-month wait for TensorRT-LLM, and may never get a stable GGUF.

### 2.2 The default in 2026

For **GPU-backed, multi-user, open-weights** serving, the default is **vLLM**. It owns the production slot because it is vendor-neutral (NVIDIA/AMD/Intel/TPU/Apple-experimental), supports 200+ architectures including MoE/multimodal, ships an OpenAI-compatible API, and HuggingFace themselves recommend it over their own (now-maintenance-mode) TGI [yottalabs.ai 2026; vllm-project README].

You only reach past vLLM when one of three conditions binds:
- **Workload-binding** (heavy prefix sharing or structured generation → SGLang).
- **Hardware-binding** (NVIDIA-only + max throughput goal → TensorRT-LLM; CPU/edge/Apple → llama.cpp/MLX/Ollama).
- **Operator-binding** (dev laptop, want 5-min setup → Ollama; ≤1 concurrent user → llama.cpp).

### 2.3 "Fastest" is a category error

Throughput-per-GPU, throughput-per-dollar, P50 TTFT, P99 ITL, and developer-time-to-first-request are **five different goals**, and the engines optimize for different combinations:

| Engine | What it optimizes for |
|---|---|
| vLLM | Throughput-per-GPU across mixed traffic, model breadth |
| SGLang | Throughput when requests share prefix; structured-gen TPS |
| TensorRT-LLM | Peak throughput on NVIDIA at saturation; per-token cost at scale |
| TGI | Was generic; now mostly a migration source |
| llama.cpp | Single-user TPS on CPU/Apple/edge; minimal-deps install |
| Ollama | Developer-time-to-first-request (5 min) |
| MLX | Apple Silicon throughput and Apple-native dev UX |

Pick by **which axis your project is binding on**, not by which engine has the most stars.

---

## 3. SOP 工作流 (SOP Workflow)

```
[Step 0] Define the four-axis constraint vector
   ├─ Hardware: GPU vendor, count, interconnect (NVLink? PCIe?), VRAM/GPU
   ├─ Workload: # concurrent users, ISL/OSL distribution, shared-prefix %, structured-out %
   ├─ Constraint: license, vendor-lock tolerance, eng-days budget, P50/P99 SLA
   └─ Model: family (Llama/Qwen/Mixtral/DeepSeek/Mamba/...), size, quantization preference

[Step 1] Eliminate incompatible engines (hard filters)
   ├─ No NVIDIA GPU?            → drop TensorRT-LLM
   ├─ CPU/Apple/edge only?      → drop vLLM (production), TGI, TensorRT-LLM
   ├─ Need OSS-permissive only? → drop TensorRT-LLM (NVIDIA license)
   ├─ Mamba / brand-new arch?   → check vLLM+SGLang coverage; likely drop others
   └─ Multi-LoRA hot-swap?      → vLLM (best), TensorRT-LLM (good), SGLang (good); others drop

[Step 2] Map workload to engine strength
   ├─ Throughput + mixed traffic         → vLLM
   ├─ Shared prefixes (chatbot, agent)   → SGLang (≈29% over vLLM on shared-context [n1n.ai 2026])
   ├─ Structured JSON/regex at scale     → SGLang (RadixAttention + state machines)
   ├─ Peak throughput, NVIDIA-only, big budget → TensorRT-LLM (+30–50% over vLLM [n1n.ai 2026])
   ├─ Single user, dev laptop            → Ollama
   ├─ CPU/Apple/edge/embedded            → llama.cpp / MLX
   └─ Multi-tenant SaaS with LoRA fleet  → vLLM (multi-LoRA mature) or SGLang

[Step 3] Sanity-check hardware topology
   ├─ TP requires NVLink (≈900 GB/s) — not PCIe Gen4 (≈32 GB/s, ~28× slower)
   ├─ PCIe-only box → smaller TP + replicas, or PP, or switch engines
   ├─ Cross-NUMA across the same node → as bad as PCIe; pin to NUMA-local GPUs
   └─ Multi-node → require IB / RoCE, not Ethernet

[Step 4] Benchmark top 2 on YOUR workload
   ├─ Replay representative ISL/OSL distribution (NOT MMLU prompts)
   ├─ Measure P50 + P99 TTFT, P50 + P99 ITL, tokens/s/GPU, $/M-tokens
   ├─ Watch saturation: queue depth, KV occupancy, preemption count
   └─ Decide; document the constraint vector that justified the pick

[Step 5] Plan the escape hatch
   ├─ Note the workload threshold that would force a switch
   ├─ Keep the OpenAI-compatible API layer so swaps are mechanical
   └─ Re-evaluate every 6 months — engines evolve in quarters, not years
```

---

## 4. 操作模型 (Operation Model)

### OP-1: Decision matrix lookup by (hardware, workload)

- **Trigger**: User asks "what should we serve X on?" and gives hardware + workload.
- **Action**: Look up the row in §7 table; eliminate by Step 1 hard filters; pick by Step 2 strength match.
- **Output**: A primary engine + a fallback, with the constraint vector that justified the pick.
- **Evidence**: §7 cross-framework matrix; [yottalabs.ai 2026]; [aimadetools.com 2026].

### OP-2: Detect "wrong-tool-for-the-job" symptoms

- **Trigger**: A team is using engine E but reporting one of: low throughput despite tuning, unsupported model architecture, structured-output workarounds, single-user pain on a multi-user engine.
- **Action**: Match symptom → engine mismatch:
  - vLLM stuck below expected throughput on PCIe-only L40S → switch to PP or 2× independent TP=2 replicas (engine isn't the problem; topology is).
  - vLLM with heavy `guided_decoding` overhead on agent traffic → A/B SGLang.
  - TGI deployment, HF themselves now recommend vLLM/SGLang → plan migration.
  - Ollama in "production" with ≥10 concurrent users → graduate to vLLM.
  - llama.cpp on a serving-many-users box → graduate to vLLM.
- **Output**: Migration recommendation with cited reason.
- **Evidence**: [yottalabs.ai 2026]; [contracollective.com 2026].

### OP-3: Quantization-driven engine pick

- **Trigger**: Quantization format dictates engine; team has GGUF / AWQ / GPTQ / FP8 weights already.
- **Action**:
  - **GGUF only** → llama.cpp / Ollama / LM Studio. vLLM has experimental GGUF; not production-grade.
  - **AWQ / GPTQ** → vLLM (first-class), SGLang (good), TensorRT-LLM (supported, needs engine rebuild).
  - **FP8 (Hopper/Ada+)** → vLLM, SGLang, TensorRT-LLM all support; near-lossless [arxiv 2411.02355].
  - **MLX format (Apple)** → MLX / mlx-lm; not portable to other engines.
- **Output**: Engine shortlist gated by available weights format.
- **Evidence**: [docs.vllm.ai/quantization]; [arxiv.org/abs/2411.02355].

### OP-4: Structured-output workload routing

- **Trigger**: ≥30% of requests need JSON / regex / grammar-constrained output, OR the project is an agent with tool-call state machines.
- **Action**: Default to **SGLang**. RadixAttention + first-class state machines beat vLLM's `guided_decoding` at scale. If staying on vLLM, expect throughput hit on constrained requests; budget for it.
- **Output**: SGLang shortlisted as primary; vLLM as fallback if SGLang doesn't support the model.
- **Evidence**: [sglang.ai blog]; [n1n.ai 2026 SGLang +29% on shared-context].

### OP-5: Apple Silicon / edge routing

- **Trigger**: Target platform is M-series Mac, iPhone/iPad, Jetson, Raspberry Pi, or other ARM/edge.
- **Action**:
  - **M-series Mac, dev/local**: Ollama (best UX) or MLX (best perf, Apple-native).
  - **M-series Mac, production server**: llama.cpp Metal backend or MLX. vLLM Metal/MPS is experimental as of 2026; do not ship on it [aimadetools.com 2026; contracollective.com 2026].
  - **Jetson / ARM Linux**: llama.cpp (broadest hardware support) or TensorRT-LLM if Jetson Orin.
  - **CPU-only x86 server**: llama.cpp with AVX-512; expect single-digit users.
- **Output**: Apple/edge-specific engine pick with format requirement (GGUF / MLX).
- **Evidence**: [contracollective.com 2026]; [aimadetools.com 2026].

### OP-6: Multi-tier deployment design

- **Trigger**: Project has both interactive (premium, latency-bound) and batch (free, throughput-bound) tiers.
- **Action**: Run heterogeneous engines:
  - Premium / interactive on **TensorRT-LLM** (if NVIDIA-locked + budget) or **vLLM FP8** with prefix caching.
  - Free / batch on **vLLM AWQ-4** (high concurrency, lower cost) or **SGLang** if prefix-sharing.
  - Dev / staging on **Ollama** for fast model swaps.
  - Edge / on-device client on **llama.cpp** (GGUF).
- **Output**: 2–3 engine deployment plan with a single OpenAI-compatible gateway in front.
- **Evidence**: Common production pattern documented in [yottalabs.ai 2026; contracollective.com 2026].

### OP-7: Bench-then-pick when the choice is close

- **Trigger**: Two engines both pass Step 1 + 2; team disagrees.
- **Action**: Run a 1-day benchmark with replayed traffic. Required metrics: P50 + P99 TTFT, P50 + P99 ITL, tokens/s/GPU, $/M-tokens, peak memory, model-load time. **Do not benchmark on MMLU-style prompts**; use real production ISL/OSL.
- **Output**: A decision memo with the constraint vector + measured numbers + the threshold that would flip the decision.
- **Evidence**: Standard practice; all cited comparison reports note that workload-specific benchmarks override published numbers.

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1: Team wants vLLM, but only has a PCIe-only 4-GPU box

**Situation**: A team standardized on vLLM but their cluster is 4× L40S on PCIe Gen4 (no NVLink). They configure `--tensor-parallel-size 4` for Llama-3-70B-FP8 and see throughput collapse — single-replica TPS is ~30% of what the H100×4 benchmark advertises.

**Tension**:
- vLLM is the right *engine*, but TP=4 over PCIe is the wrong *topology*. The all-reduce after every layer chokes on the ~32 GB/s PCIe link vs the ~900 GB/s NVLink the benchmarks assumed [spheron.network 2026].
- Switching engines doesn't help — the same all-reduce penalty hits TensorRT-LLM and SGLang.

**Resolution**:
- **First**: drop to `TP=2 × 2 replicas` (each replica uses an NVLink-paired or NUMA-local pair, if any), or use pipeline parallelism `PP=4, TP=1`. Replicas eliminate the cross-GPU all-reduce on the hot path [developers.redhat.com 2026 step-5].
- **Second**: if 70B doesn't fit at TP=2 with FP8 on L40S (48 GB/GPU), step down to AWQ-4 or use Llama-3-8B until hardware upgrades.
- **Third**: if neither works, swap to TGI (similar PCIe penalty but lower TP-coupling overhead in some configs) or accept a switch to llama.cpp for low-concurrency workloads.
- **Key lesson**: the bottleneck was hardware topology, not engine choice. Always check interconnect before blaming the engine.

**Evidence**: [docs.vllm.ai parallelism_scaling]; [developers.redhat.com 2026]; [spheron.network 2026].

### Dilemma 2: Structured JSON output at scale — SGLang vs vLLM

**Situation**: An agent platform serves Qwen-2.5-32B-Instruct with ~70% of requests demanding strict JSON schema output (tool-calling, function arguments). On vLLM with `guided_decoding`, throughput drops ~40% vs unconstrained baseline; P99 TTFT regresses.

**Tension**:
- vLLM has the broader model + production track record; team already operates it.
- SGLang's RadixAttention + native state-machine compilation gives ≈29% higher throughput on shared-context workloads and meaningful gains on constrained decoding [n1n.ai 2026]; agent traffic has both properties.
- Migration cost is real: deployment scripts, observability, ops runbooks.

**Resolution**:
- **A/B**: run SGLang as a sidecar on a fraction of traffic. Measure constrained-output TPS + correctness rate on real JSON schemas (not toy schemas).
- **If SGLang wins ≥25%** on YOUR traffic → migrate the structured-output path; keep vLLM for unconstrained traffic, OR consolidate on SGLang if it covers all your models.
- **If SGLang model coverage misses** a key model in your fleet → stay on vLLM, optimize `guided_decoding` (xgrammar backend), and re-evaluate next quarter.
- **Heuristic**: structured-output workload share above ~30% justifies SGLang shortlisting; above ~50% it usually wins.

**Evidence**: [sglang.ai/blog]; [n1n.ai 2026]; [yottalabs.ai 2026].

### Dilemma 3: NVIDIA shop with 2-week budget — vLLM or TensorRT-LLM?

**Situation**: NVIDIA-only cluster (8×H100, NVLink-full), single-tenant, throughput-per-GPU is the dominant cost line. Team has 2 weeks of senior eng time. TensorRT-LLM promises +30–50% throughput [n1n.ai 2026] but requires engine build per (model × precision × max-batch × max-seq) tuple.

**Tension**:
- **TensorRT-LLM wins** on saturated throughput and is the right tool when GPU-hours are the binding cost.
- **It loses** on agility: every model update or context-length change requires an engine rebuild (10 min – 2 hours); architecture support lags vLLM by 3–6 months for new releases; vendor lock-in if you ever consider AMD/TPU.
- vLLM tolerates new models on day-1 and supports any NVIDIA + AMD + Intel hardware.

**Resolution**:
- **If model is stable for ≥3 months and throughput dominates cost** → TensorRT-LLM is correct. Spend the 2 weeks.
- **If model churn is monthly OR you ship new models often OR you want vendor optionality** → vLLM. The +30–50% throughput is rarely worth the agility loss.
- **Hybrid**: vLLM during model-fit phase; freeze a winning model into a TensorRT-LLM engine for steady-state production.

**Evidence**: [n1n.ai 2026]; [yottalabs.ai 2026]; [spheron.network 2026].

### Dilemma 4: "We want one engine for laptop dev → cloud prod"

**Situation**: A small team wants the same engine for local dev on M-series Macs AND production on cloud NVIDIA. They are tempted to standardize on Ollama (since it runs everywhere) or vLLM (since it's the prod default).

**Tension**:
- **Ollama everywhere**: great dev UX, but tops out at single-digit concurrent users; vLLM-class throughput is unreachable. Using Ollama in cloud production wastes 10–20× the GPU spend [contracollective.com 2026].
- **vLLM everywhere**: production-grade, but Metal/MPS is experimental on Mac; dev velocity is worse than Ollama; single-user latency is no better than llama.cpp.

**Resolution**:
- Do **not** standardize on one engine. Standardize on the **API contract** (OpenAI-compatible HTTP).
- **Local dev**: Ollama (M-series) or vLLM (if devs have NVIDIA workstations). The OpenAI compatibility means application code is identical.
- **Production**: vLLM (default) or SGLang/TensorRT-LLM (if Step 2 binds).
- **Edge / on-device**: llama.cpp with GGUF.
- The "one engine" goal is the wrong abstraction; the right abstraction is "one API, multiple runtimes" — same pattern as JVM languages, same pattern as POSIX [yottalabs.ai 2026 common pattern].

**Evidence**: [contracollective.com 2026]; [yottalabs.ai 2026].

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Anti-pattern 1: Pick by GitHub stars or community vibes

vLLM has ~50k stars, llama.cpp has ~70k, TensorRT-LLM has ~10k. Stars do not predict fit for YOUR workload. A 70-star project may be the only thing that runs your model on your hardware. Pick by the constraint vector (§3 Step 0), not by popularity.

### Anti-pattern 2: Pick by the tutorial you read last week

The "X is 5× faster than Y" blog you skimmed had specific (hardware, model, batch, ISL/OSL) parameters. Most blogs do not state them. Treat every comparison as ungeneralizable until you've replicated it with YOUR parameters.

### Anti-pattern 3: Ignore hardware topology

PCIe-only TP. Cross-NUMA all-reduce. Ethernet between nodes for tensor-parallel. Each of these turns a "fastest engine" into a slowest engine. The engine isn't the variable; the interconnect is. Check the topology before blaming the engine [spheron.network 2026].

### Anti-pattern 4: Confuse single-user latency with throughput

Ollama and llama.cpp can give you a faster first token on a single request than vLLM's cold path. This proves nothing about serving 50 users. Benchmark at YOUR concurrency, not at concurrency=1.

### Anti-pattern 5: Forget the license

TensorRT-LLM ships under NVIDIA's proprietary license. If your shop forbids non-OSS in the inference path (e.g. air-gapped, regulated, or open-core-only orgs), this is a hard filter — no benchmark matters. Same caveat for any Triton-integrated engine that pulls in NVIDIA-proprietary components.

### Anti-pattern 6: Standardize on TGI in 2026

HuggingFace themselves moved their internal recommendation to vLLM and SGLang; TGI is in maintenance mode [yottalabs.ai 2026]. Existing TGI deployments are fine if they meet SLA, but new projects in 2026 should not pick TGI.

### Anti-pattern 7: Treat Ollama as production-grade

Ollama has added concurrent-request support, but its sweet spot is local dev. A production deployment on Ollama at 10+ QPS wastes 80–95% of GPU capacity vs vLLM [contracollective.com 2026; aimadetools.com 2026]. Use Ollama for dev, swap to vLLM for prod.

### Boundaries

This skill is **correct** when:
- You are picking, defending, or migrating an inference engine for a new or existing deployment.
- The four-axis constraint vector (§3 Step 0) is knowable.
- The user can run a 1-day benchmark on representative traffic.

This skill is **not** the right tool when:
- The choice has already been made and the question is *how to tune* — defer to `vllm`, `sglang`, `tensorrt-llm`, `llama-cpp` skills.
- The workload is a hosted-API consumer; engine choice doesn't apply.
- The choice is training/fine-tuning runtime, not inference.

---

## 7. 跨框架对照 (Cross-framework Comparison)

### 7.1 Vendor matrix

| Engine | Best for | Hardware | License | One-line strength | One-line weakness |
|---|---|---|---|---|---|
| **vLLM** | Production GPU serving, mixed traffic, open weights | NVIDIA / AMD / Intel / TPU / Apple (exp.) | Apache 2.0 | Vendor-neutral, broadest model coverage, HF-blessed default | Not the fastest in any single niche |
| **SGLang** | Shared-prefix workloads, agents, RAG, structured generation | NVIDIA / AMD | Apache 2.0 | RadixAttention prefix tree + native state machines; ~29% over vLLM on shared-context | Smaller model coverage; smaller ecosystem |
| **TensorRT-LLM** | Peak NVIDIA throughput at saturation | NVIDIA only | NVIDIA proprietary | +30–50% over vLLM in NVIDIA-only deployments | Vendor lock-in; 1–2 weeks setup; per-config engine rebuild |
| **TGI** | Existing HF-stack deployments | NVIDIA / AMD | HFOIL (Apache-restricted) | Was the HF default | Maintenance mode; HF now recommends vLLM/SGLang |
| **llama.cpp** | CPU / Apple Silicon / edge / single user / GGUF | x86 / ARM / Apple / consumer GPU / CUDA / Vulkan | MIT | Runs anywhere; minimal deps; GGUF ecosystem | Per-request overhead doesn't scale to many concurrent users |
| **Ollama** | Local dev, prototyping, model switching | Wraps llama.cpp | MIT | 5-minute install; best dev UX | Concurrent throughput is poor vs vLLM-class engines |
| **MLX / vllm-mlx** | Apple Silicon native | M-series only | MIT | Apple's first-party path; best Mac throughput | Mac-only; smaller ecosystem |

### 7.2 Headline performance gaps (2025–2026 vintage)

- **vLLM vs HF Transformers**: 14–24× higher throughput for Llama on NVIDIA [yottalabs.ai 2026].
- **vLLM vs early TGI**: 2.2–3.5× higher throughput at launch [yottalabs.ai 2026].
- **SGLang vs vLLM**: ~29% higher throughput when requests share prefix [n1n.ai 2026]; pure-batch parity.
- **TensorRT-LLM vs vLLM**: +30–50% in saturated NVIDIA-only high-concurrency [n1n.ai 2026].
- **vLLM vs llama.cpp** at many-user concurrency: vLLM wins decisively [aimadetools.com 2026].
- **llama.cpp vs vLLM** at concurrency=1 on consumer GPU/CPU: llama.cpp wins on simplicity and often on TPS.

All numbers assume the engine's preferred topology (NVLink for vLLM/TRT-LLM, etc.). Cross-topology comparisons are meaningless.

### 7.3 The default decision flow

```
GPU-backed multi-user production?
├─ Yes
│  ├─ Heavy shared prefixes or structured-out >30%?  → SGLang
│  ├─ NVIDIA-locked + max throughput + 2wk budget?   → TensorRT-LLM
│  ├─ Multi-LoRA SaaS / multi-tenant?                → vLLM (or SGLang)
│  └─ Default / mixed traffic / new model            → vLLM
└─ No
   ├─ Dev laptop / 5-min setup?                      → Ollama
   ├─ CPU / Apple / edge / single user?              → llama.cpp (or MLX on Mac)
   ├─ Apple production server?                       → MLX or llama.cpp Metal
   └─ Existing TGI that works?                       → stay; plan migration to vLLM
```

### 7.4 Common production pattern in 2026

```
Local dev          → Ollama
Prod benchmark     → vLLM (default)
If prefix-heavy    → A/B with SGLang
If NVIDIA-only +   → A/B with TensorRT-LLM
   eng budget
Edge / on-device   → llama.cpp + GGUF
Apple-native       → MLX
```

vLLM occupies the **default production slot** for open-weights LLM serving in 2026; everything else is a workload-justified deviation.

---

## Cited sources (primary)

- yottalabs.ai/post/best-llm-inference-engines-in-2026-vllm-tensorrt-llm-tgi-and-sglang-compared
- explore.n1n.ai/blog/llm-inference-engine-comparison-vllm-tgi-tensorrt-sglang-2026-03-13
- aimadetools.com/blog/vllm-vs-ollama-vs-llamacpp-vs-tgi/
- contracollective.com/blog/llama-cpp-vs-mlx-ollama-vllm-apple-silicon-2026
- developers.redhat.com/articles/2025/09/30/vllm-or-llamacpp-choosing-right-llm-inference-engine-your-use-case
- spheron.network/blog/vllm-vs-tensorrt-llm-vs-sglang-benchmarks
- arxiv.org/abs/2309.06180 (PagedAttention)
- arxiv.org/abs/2411.02355 ("Give Me BF16 or Give Me Death", quantization tradeoffs)
- github.com/vllm-project/vllm (README)
- sglang.ai/blog
