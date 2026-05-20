# llm-engine-selection skill

Cross-engine decision rubric for **picking an LLM serving stack** — vLLM, SGLang, TensorRT-LLM, TGI, llama.cpp, Ollama, or MLX — as a function of `(hardware × workload × constraint)`, not "which is fastest".

This is the **D5 gap skill** in the Phase-B coder-agent skill inventory. Individual engines have their own skills (`vllm`, `sglang`, `tensorrt-llm`, `llama-cpp`); this skill teaches the *cross-engine decision*.

## Scope

- **Activation**: any time a coder-agent picks, defends, or migrates an inference engine for production / batch / edge / dev / multi-tenant SaaS / structured-output workloads.
- **Decision axes**: hardware (GPU vendor + interconnect), workload (concurrency + ISL/OSL + prefix-share + structured-out), constraint (license + lock-in + eng-budget + SLA), model (family + size + quantization).
- **Date stamp**: May 2026. State-of-the-art moves in 3–6 month cycles; re-verify before committing.

## Layout

```
d-llm-engine-selection-skill/
├── SKILL.md                              # 7-section SOP (activation → cross-framework matrix)
├── README.md                             # This file
├── references/
│   ├── R1-source-evidence.md             # Cited benchmarks and primary-source claims
│   └── R2-decision-flowchart.md          # Decision tree + worked examples
└── intermediate/
    └── operation_candidates.json         # Raw trigger / action / output / evidence operations
```

## Key claim of the skill

> Engine choice is a function of `(hardware × workload × constraint)`, not "which is fastest".

Concretely, in 2026:
- **vLLM** owns the production default slot (vendor-neutral, broadest models, HF-blessed).
- **SGLang** wins on shared-prefix workloads (+~29% vs vLLM) and structured generation.
- **TensorRT-LLM** wins on saturated NVIDIA throughput (+30–50% vs vLLM), at the cost of 1–2 weeks setup + vendor lock-in.
- **TGI** is in maintenance mode; new projects in 2026 should not pick it.
- **llama.cpp / Ollama / MLX** own the CPU / Apple / edge / single-user slot.

The skill encodes how to map a constraint vector to one of these slots, plus 4 dilemma cases (PCIe-only vLLM box, structured-JSON-at-scale, NVIDIA shop with 2-week budget, laptop-to-cloud parity) and 7 anti-patterns.

## Method

Primary mining: the `vllm-sop-skill/references/R5-ecosystem-context.md` source-of-truth comparison plus frontmatter from the four engine skills (`vllm`, `sglang`, `tensorrt-llm`, `llama-cpp`) under `~/.claude/skills/`. Every load-bearing performance claim carries an inline `[source]` tag and resolves to the cited-sources list. No fabrication.

## Position in the Phase-B inventory

- **Companion skills (per-engine deep dives)**: `vllm`, `sglang`, `tensorrt-llm`, `llama-cpp`.
- **Sibling decision skill**: `vllm-sop` covers the same selection logic from the vLLM-centric view; this skill is engine-agnostic and is the right activation when the choice is genuinely open.
- **Date sensitivity**: Phase-B medium-frequency, specialized. Re-skill every 2 quarters.
