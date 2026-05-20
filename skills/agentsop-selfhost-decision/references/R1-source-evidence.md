# R1 — Source Evidence for selfhost-decision

Every load-bearing claim in SKILL.md, traced to a source SOP in this repo or a primary doc. Phase-D enhancement-overlay skill **D6**. No fabricated numbers; price/quality figures are quoted as published and date-stamped May 2026.

---

## 1. Dify — the canonical self-host vs cloud dilemma

**Source SOP**: `output/dify-sop-skill/SKILL.md` — Case 3 ("Self-host 还是 Cloud——什么时候值得自己运维？"), §6.2 (performance boundaries), §6.4 (governance/license).
**Primary**: architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host ; github.com/langgenius/dify/discussions/32254

### 1.1 The cost decision matrix (OP-1, Dilemma 2)
Quoted from dify SKILL Case 3 决策矩阵:

| Condition | Cloud | Self-host |
|---|---|---|
| Team ≤ 3, small usage | ✅ ($59–159/mo cheaper than 养 DevOps) | ❌ |
| Compliance / data-residency (finance, medical) | ❌ | ✅ |
| High usage (millions of API calls) | ❌ (subscription overruns infra) | ✅ |
| Air-gapped / intranet | ❌ | ✅ |
| Custom vector store / model | partial | ✅ full control |
| Don't want to manage backup / scaling | ✅ | ❌ |

Extracted: the cost crossover is real (small team → Cloud; millions of calls → self-host), **but** it is gated by compliance and conditioned on ops capacity. This is the empirical basis for §2's "two axes" model and OP-1's `V*`.

### 1.2 Ops burden — "not docker compose up" (OP-3, anti-pattern "compose up = production")
Quoted from dify SKILL Case 3 实操要点:
- "自部署不是 'docker compose up' 完事——需要反向代理 + HTTPS + 备份 + 监控 + 升级策略"
- "生产 self-host 用 Kubernetes + Helm + 外部 PostgreSQL/Redis/Vector DB（不要用容器内置的）"

⇒ The `ops_labor` term in `V*` is non-zero and the bundled stateful containers are not production-grade. Basis for OP-3 and §6.1.

### 1.3 Same-image finding (OP-6, anti-pattern "same-image Enterprise tier")
Quoted from dify SKILL Case 3:
- "⚠️ Community / Premium / Enterprise 用同一 Docker image, 差异在环境变量" [github.com/langgenius/dify/discussions/32254]

⇒ Paid self-host tiers buy *support*, not *capability*; the open image is often technically sufficient. Basis for OP-6 and §7.2.

### 1.4 Throughput ceiling (OP-4, §2.5, Dilemma 2)
Quoted from dify SKILL §6.2:
- "~10 QPS / pod (1 CPU 2GB)——超过需水平扩 worker"
- "每节点单独 DB query——长 workflow 累积延迟" [memo.d.foundation/breakdown/dify]

⇒ The "high volume justifies self-host" assumption must account for the **replica count** to clear ~10 QPS/pod, which feeds back into the GPU+ops term of `V*`. Basis for OP-4 and the §3 Step-4 feedback loop.

### 1.5 License caveat (OP-6, §6.2 boundary)
Quoted from dify SKILL §6.4:
- "Apache 2.0-like license（'not really'）——商业重度依赖前确认条款" [memo.d.foundation/breakdown/dify]

⇒ License is a lock-in cost line in OP-6.

---

## 2. vLLM — self-serving trade-offs

**Source SOP**: `output/vllm-sop-skill/SKILL.md` — OP-4 (prefix-cache privacy), OP-5 (live triage), Dilemma 2 (tiered serving), Anti-pattern 6 (CPU provisioning), §7 (ecosystem / lock-in).
**Primary**: docs.vllm.ai/en/stable/configuration/optimization/ ; developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance

### 2.1 Throughput ceilings / triage (OP-4)
Quoted from vllm SKILL OP-5 (5-step Red Hat triage):
- watch Prometheus `num_requests_waiting`, KV cache occupancy, preemption count; "KV cache occupancy near 100% with rising preemption count → drop `--max-num-seqs` or quantize KV to FP8."

⇒ A self-hosted engine has a per-replica ceiling gated by KV-cache, not just QPS — the vLLM analogue of Dify's ~10 QPS/pod. Basis for OP-4 (compute replica count, re-feed into cost).

### 2.2 CPU provisioning bites before the GPU (OP-3)
Quoted from vllm SKILL Anti-pattern 6:
- "vLLM needs minimum `2 + N` physical CPU cores for N GPUs; under-provisioning CPUs makes the API server, tokenizer, and detokenizer the bottleneck before the GPU is touched" [docs.vllm.ai optimization]

⇒ Self-host ops is more than the GPU; mis-provisioning the host wastes the GPU you paid for. Basis for OP-3's "honest capacity" framing and §6.1.

### 2.3 Tiered / hybrid serving (OP-5)
Quoted from vllm SKILL Dilemma 2 resolution + Step 7:
- "Mixed: serve two replicas — FP8 for premium tier, AWQ for free tier."
- "Latency SLA violated under load? → add a replica (data parallelism across pods)."

⇒ Generalizes to the hybrid topology: self-host the steady floor, burst/overflow to managed, and split premium/compliance vs bulk by tier. Basis for OP-5.

### 2.4 Multi-tenant privacy (OP-2 caveat)
Quoted from vllm SKILL OP-4 caveats:
- "Multi-tenant privacy: use **cache salting** to avoid cross-tenant prefix collisions" [github.com/vllm-project/vllm/issues/16016]

⇒ Even on a managed-but-shared path, cross-tenant data exposure is a compliance consideration — supports treating compliance as a gate (OP-2). Basis for Dilemma 1 evidence.

### 2.5 Vendor lock-in vs neutrality (OP-6, §7.2)
Quoted from vllm SKILL §7:
- "TensorRT-LLM … Up to 30–50% higher throughput than vLLM in high-concurrency NVIDIA-only deployments; 1–2 weeks setup; **vendor lock-in**" [n1n.ai 2026]

⇒ Lock-in is a real cost line; vendor-neutral engines (vLLM + open weights) keep the managed↔self-host door open. Basis for OP-6 and the §7.2 one-liner.

### 2.6 Staged, reversible choices (OP-7)
Quoted from vllm SKILL §7 common pattern:
- "develop on Ollama → benchmark with vLLM → consider SGLang … consider TensorRT-LLM only if NVIDIA-locked"

⇒ Implies the siting decision is staged and reversible — basis for OP-7's flip-trigger + thin-abstraction guidance.

---

## 3. The unification claim

The self-host vs managed decision reduces to **two asymmetric axes plus two side-conditions**:

1. **Compliance gate (binary, first)** — a hard data-residency / air-gap / contractual boundary fails the managed path regardless of cost [dify Case 3]. Caveat: a managed in-region/BAA/VPC tier can satisfy the boundary and re-open the cheaper path.
2. **Volume slider (continuous)** — `V* = fixed / (managed_$tok − marginal_$tok)`; below it managed wins, above it self-host wins [dify Case 3 cost matrix; architjn.com pricing].
3. **Side-condition: utilization** — idle GPUs invert the unit-cost math; "above V*" holds only at high steady utilization [vllm Dilemma 2 / Step 7 → hybrid].
4. **Side-condition: ops capacity** — self-host is reverse-proxy + HTTPS + backups + monitoring + upgrades + external DBs, not "compose up" [dify Case 3 实操要点; vllm Anti-pattern 6].

Plus a **throughput feedback loop** (per-replica ceilings → replica count → back into the GPU term of `V*`) [dify §6.2; vllm OP-5] and a **reversibility design choice** (thin OpenAI-compatible abstraction + flip trigger) [vllm §7].

Phase B catalogued the self-host-vs-cloud question inside the Dify and vLLM SOPs as a per-framework concern. This overlay names the shape once, framework-independent: **gate before slider, cost the ops, re-feed throughput, plan the flip.**
