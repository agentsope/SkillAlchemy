---
name: agentsop-selfhost-decision
version: 0.1.0
description: >-
  Project-kickoff rubric for the self-host vs managed-cloud decision — when is running your
  own inference engine / LLM platform worth the ops cost vs paying per-token for a managed
  API? Decide on two axes — VOLUME (a cost-crossover slider) and COMPLIANCE (a hard gate).
  Use at kickoff when choosing where to run inference, or when cost / data-residency
  pressure forces a re-evaluation.
domain: deployment-decision / infrastructure-economics
kind: enhancement-overlay (project-kickoff rubric)
phase: D-enhance (D6)
cross_links:
  - llm-engine-selection
  - dify-sop
trigger_keywords:
  - "self-host vs cloud"
  - "self-host vs API"
  - "managed API vs run our own"
  - "is it cheaper to self-host the model"
  - "data residency LLM"
  - "air-gapped LLM"
  - "on-prem inference"
  - "GPU cost vs API cost"
  - "Dify cloud vs self-host"
  - "when to self-host inference"
when_to_use:
  - "at project kickoff, deciding where an LLM / platform runs: managed API/cloud vs self-hosted GPU"
  - "cost pressure: monthly API spend is climbing and someone asks 'should we just run our own?'"
  - "compliance pressure: data-residency / air-gap / regulated-data requirement appears mid-project"
  - "evaluating a self-hostable platform's paid tiers (Dify Cloud vs Docker; managed vLLM vs your own GPUs)"
  - "designing a hybrid (self-host baseline + managed burst) topology"
when_not_to_use:
  - "WHICH inference engine to run once you've decided to self-host — that's [[agentsop-llm-engine-selection]]"
  - "HOW to build the Dify app once you've decided to self-host it — that's [[agentsop-dify]]"
  - "single-call / hobby / one-user workloads where the answer is trivially 'just call the API'"
  - "training / fine-tuning siting (different cost structure: burst GPU, not steady serving)"
---

# Self-host vs Managed-cloud Decision — A Project-Kickoff Rubric

> **Overlay, not a deep dive.** This skill answers *where to run* (self-host vs managed), not *which engine* ([[agentsop-llm-engine-selection]]) or *how to build the app* ([[agentsop-dify]]). It fires first, at kickoff, and hands off to those once the side is chosen.

---

## 1. 何时激活 (When to Activate)

### 1.1 直接信号 (Direct triggers)
- At kickoff you must decide **where an LLM or LLM platform runs**: a managed API/cloud (OpenAI / Anthropic / Bedrock / Dify Cloud) vs **your own GPUs / your own Docker** (vLLM, self-hosted Dify).
- **Cost pressure**: monthly managed spend is climbing; someone says *"should we just run our own and stop paying per token?"*
- **Compliance pressure**: a **data-residency / air-gap / regulated-data** requirement (finance, medical, gov, GDPR region-lock) appears and the managed path is suddenly in question.
- You're comparing a self-hostable platform's tiers — e.g. **Dify Cloud Pro ($59) vs self-deployed Docker** [architjn.com/blog/dify-cloud-pricing-plans], or managed-vLLM-as-a-service vs your own H100s.

### 1.2 反向信号 (Skip this rubric when)
- The decision is already *self-host*, and the open question is **which engine** → go to **[[agentsop-llm-engine-selection]]** (vLLM vs TGI vs SGLang vs TensorRT-LLM vs llama.cpp).
- The decision is already *self-host Dify*, and the open question is **how to build/operate it** → go to **[[agentsop-dify]]**.
- **Single user / hobby / one stream** — the answer is "just call the managed API"; no rubric needed.
- **Training / fine-tuning** siting — different cost structure (burst GPU, spot, not steady-state serving).

### 1.3 心智门槛 (Mental check)
> This rubric exists because the loud reflex — *"running our own is cheaper / more serious"* — is **true only above a volume crossover, and only if you have the ops capacity, and only if compliance hasn't already forced your hand.** The job is to evaluate the **gate before the slider**, and to cost the **ops burden**, not just the GPU.

判断公式:
- 如果你的瓶颈是 **per-token spend at high, predictable volume** → self-host *may* win (run OP-1).
- 如果你的瓶颈是 **data can't leave our boundary** → compliance gate decides (run OP-2), cost is secondary.
- 如果你的瓶颈是 **we don't have anyone to run a GPU box at 3am** → managed wins regardless of the GPU math (run OP-3).

---

## 2. 核心心智模型 (Core Mental Model)

### 2.1 The trade, in one line
> **Self-host trades ops burden for control + unit-cost-at-scale. Managed trades $/token for zero ops. The crossover is a function of two axes: volume and compliance.**

- **Managed**: you pay **$/token**, marginal, no fixed cost, no ops. Cost scales *linearly* with usage and never sleeps.
- **Self-host**: you pay a **fixed floor** (GPU + ops labor + infra) plus a tiny marginal cost. Cost is *flat-then-cheap-per-unit* — but only if utilization stays high.

### 2.2 Two axes, not one — and they are not symmetric

```
                COMPLIANCE  (a GATE — binary, evaluated FIRST)
                     │
   managed FORBIDDEN │  self-host (or in-region managed) MANDATORY
   ──────────────────┼──────────────────────────────────────────►  VOLUME
                     │                                    (a SLIDER —
   managed allowed   │   below V*: managed cheaper          continuous
                     │   above V*: self-host cheaper         crossover)
                     │   (IF utilization high + ops capacity exists)
```

- **Compliance is a GATE**: binary, evaluated **before** cost. A hard data-residency / air-gap NO **fails the managed path regardless of volume** [dify Case 3]. (Caveat: a managed in-region / VPC / BAA tier can re-open the gate.)
- **Volume is a SLIDER**: a continuous cost crossover `V*`. Below it managed wins; above it self-host wins — *conditionally*.

### 2.3 The crossover formula (OP-1)
```
managed_cost(V)   = V × $/token_managed
selfhost_cost(V)  = (GPU + ops_labor + infra_fixed) + V × $/token_marginal

V*  =  (GPU + ops_labor + infra_fixed) / ($/token_managed − $/token_marginal)
```
- **Below V***: managed total cost is lower → use managed.
- **Above V***: self-host total cost is lower → self-host *if* the two side-conditions hold.
- The term people forget is **`ops_labor`** — a fraction-of-FTE DevOps cost (backups, monitoring, upgrades, on-call). Cost it explicitly; it is rarely zero.

### 2.4 The two side-conditions that invalidate "above V* → self-host"
1. **Utilization** — idle GPUs invert the math. A GPU billed 24/7 but used 20% of the time has 5× the effective $/token. Self-host only wins at *high, steady* utilization.
2. **Ops capacity** — the GPU math assumes someone can actually run it. No DevOps owner → outage + opportunity cost erases the savings (OP-3).

### 2.5 The throughput feedback loop (OP-4)
Self-host volume isn't free of limits. A platform has a **per-replica ceiling** — Dify's is **~10 QPS/pod**, gated by per-node DB queries [dify §6.2]; vLLM's is gated by KV-cache occupancy + preemption [vllm OP-5]. To hit volume `V` you need `replicas = peak_QPS / ceiling`, and **that replica count feeds back into the GPU term of `V*`.** High volume can need so many replicas that the crossover moves against you.

### 2.6 Reversibility is a design choice (OP-7)
The decision is **not permanent**. Keep a **thin OpenAI-compatible API surface** on both sides so flipping managed↔self-host is a config change, not a migration. Define the **flip trigger** up front (spend > V* for N months; new compliance rule; lost ops owner). Re-evaluate quarterly — both your volume and the price/quality frontier move (May 2026 stamp; re-measure).

---

## 3. SOP 工作流 (Standard Operating Procedure)

```
[Step 0] Confirm this is a "where to run" question
   ├─ "which engine?"      → [[agentsop-llm-engine-selection]], stop
   ├─ "how to build Dify?" → [[agentsop-dify]], stop
   └─ "managed vs our own?"→ continue

[Step 1] COMPLIANCE GATE first  (OP-2)  ── binary, overrides cost
   ├─ Regulated / residency / air-gap / contract boundary?
   │     ├─ YES, and no managed in-region/BAA/VPC tier  → self-host MANDATORY → Step 3
   │     └─ YES, but a compliant managed tier exists     → managed re-opened → Step 2
   └─ NO  → Step 2

[Step 2] VOLUME SLIDER  (OP-1)  ── compute the crossover
   ├─ Estimate monthly volume (reqs × tokens)
   ├─ managed_cost  = V × $/token
   ├─ selfhost_cost = (GPU + OPS_LABOR + infra) + V × marginal      ← include ops!
   ├─ V* = fixed / (managed_$tok − marginal_$tok)
   ├─ V below V*  → managed wins → Step 5 (plan fallback)
   └─ V above V*  → self-host candidate → Step 3

[Step 3] HONEST OPS-CAPACITY CHECK  (OP-3)  ── the trap door
   ├─ DevOps / SRE / on-call owner exists?           ─ no → managed wins anyway → Step 5
   ├─ Can run external Postgres/Redis/VectorDB + K8s? ─ no → managed or hire first
   └─ yes → Step 4

[Step 4] THROUGHPUT-HEADROOM CHECK  (OP-4)  ── re-feed into cost
   ├─ replicas = peak_QPS / per-replica_ceiling (~10 QPS/pod Dify; KV-bound vLLM)
   ├─ Re-run V* with the TRUE replica count (GPU term grows)
   ├─ still favorable → self-host → Step 5
   └─ flipped unfavorable → reconsider managed or HYBRID (Step 4b)

[Step 4b] HYBRID option  (OP-5)  ── if volume is spiky or tiered
   └─ self-host the steady floor + burst/overflow to managed; or
      compliance/premium → self-host, bulk → managed

[Step 5] PLAN THE FALLBACK  (OP-6, OP-7)
   ├─ Lock-in / license audit (same-image? egress? contract minimums?)
   ├─ Thin OpenAI-compatible abstraction so the flip is config, not migration
   ├─ Define the bidirectional flip trigger
   └─ Schedule quarterly re-evaluation
```

> The ordering is load-bearing: **gate (Step 1) before slider (Step 2) before capacity (Step 3) before throughput (Step 4)**. A compliance NO short-circuits everything; a missing ops owner short-circuits a favorable GPU cost.

---

## 4. 操作模型 (Operation Model: Trigger / Action / Output / Evidence)

### OP-1: Volume-crossover calculation
- **Trigger**: cost is a stated pressure; you can estimate monthly volume.
- **Action**: estimate `V = reqs/mo × (in+out tokens)`; `managed = V × $/tok`; `selfhost = (GPU + ops_labor + infra) + V × marginal`; solve `V* = fixed / (managed_$tok − marginal_$tok)`. Place projected `V` relative to `V*`. **Include the ops-labor term** — do not assume it's zero.
- **Output**: a crossover `V*` and which side projected volume sits on, with ops labor explicit.
- **Evidence**: small team / small usage → Cloud $59–159/mo beats 养 DevOps; millions of calls → self-host [dify Case 3 决策矩阵; architjn.com/blog/dify-cloud-pricing-plans].

### OP-2: Compliance / data-residency gate
- **Trigger**: data is regulated, customer-confidential, or contractually region/boundary-bound.
- **Action**: ask whether any law/contract/cert (HIPAA, finance, GDPR residency, air-gap, gov) **forbids data leaving your boundary**. YES → managed path **fails** regardless of volume → self-host (or a managed in-region/BAA/VPC tier, if one satisfies the boundary — check before defaulting to self-host). Evaluate **before** the volume slider.
- **Output**: a pass/fail on the managed path from compliance alone, decided first.
- **Evidence**: 合规/数据驻留 (金融、医疗) → self-host; air-gapped/内网 → self-host [dify Case 3]. Multi-tenant prefix privacy → cache salting [vllm OP-4 caveat].

### OP-3: Honest ops-capacity check
- **Trigger**: self-host looks attractive on cost; validate you can actually run it.
- **Action**: self-host is **not** "docker compose up done" — it's reverse proxy + HTTPS + backups + monitoring + upgrade strategy + on-call. Score the team honestly: is there a DevOps/SRE owner? Production self-host means **external** PostgreSQL/Redis/Vector DB (not the bundled containers), K8s + Helm or equivalent, a tested upgrade path. No ops capacity → the "cheaper at scale" GPU math is a trap (outage + opportunity cost).
- **Output**: a go/no-go on self-host based on real ops capacity, with the unbundling requirement flagged.
- **Evidence**: 自部署 != docker compose up; 生产 K8s+Helm + 外部 PostgreSQL/Redis/Vector DB [dify Case 3 实操要点]. vLLM needs `2+N` CPU cores per N GPUs or the API server bottlenecks before the GPU [vllm Anti-pattern 6].

### OP-4: Throughput-headroom reality check (self-host)
- **Trigger**: self-host chosen on cost grounds; confirm the stack sustains the volume that justified it.
- **Action**: find the per-replica ceiling (Dify **~10 QPS/pod**, node-level DB-query bottleneck; vLLM KV-cache occupancy + preemption). Compute `replicas = peak_QPS / ceiling`, then **re-feed that replica count into OP-1's GPU+ops term**. If the replica count is large, re-run the crossover; the "cheaper at scale" assumption may not survive.
- **Output**: a replica count required for the volume, fed back into `V*`.
- **Evidence**: ~10 QPS/pod hard limit, 每节点单独 DB query [dify §6.2]; triage `num_requests_waiting` / KV occupancy / preemption [vllm OP-5].

### OP-5: Hybrid — self-host baseline + managed burst
- **Trigger**: volume justifies self-host for the baseline but traffic is spiky, or a premium/compliance tier coexists with a bulk tier.
- **Action**: provision self-host for the **steady-state floor** (high utilization keeps GPU $/token low); route **burst/overflow to a managed API** so you don't over-provision idle GPUs for peaks. Optionally split by tier: compliance/premium → self-host; bulk/non-sensitive → managed. Keep one gateway so the split is config, not a rewrite.
- **Output**: a baseline-self-host + burst-managed routing plan that keeps utilization high and caps over-provisioning.
- **Evidence**: two-replica tiering (FP8 premium / AWQ free) [vllm Dilemma 2]; add a replica / data-parallel pod when SLA violated under load [vllm Step 7].

### OP-6: Same-image / lock-in audit
- **Trigger**: evaluating a self-hostable platform's paid tiers, or worried about managed-vendor lock-in.
- **Action**: for self-hostable platforms, check whether **Community / Premium / Enterprise are the same Docker image** gated by env vars / license keys (then the open tier is often technically sufficient — the paywall buys *support*, not *capability*). For managed APIs, audit lock-in surface: proprietary model, proprietary fine-tune format, egress cost, contract minimums. Prefer vendor-neutral self-host engines (vLLM, open weights) so the door stays open both ways. Confirm the license permits your commercial use.
- **Output**: a lock-in / license assessment per candidate, plus whether paid self-host tiers differ in substance.
- **Evidence**: Community/Premium/Enterprise 用同一 Docker image, 差异在环境变量 [dify Case 3]; license 是 Apache-like "not really" — 确认条款 [dify §6.4]; TensorRT-LLM beats vLLM 30–50% but **locks you in** [vllm §7].

### OP-7: Fallback / exit plan
- **Trigger**: a decision is made (either way); de-risk before scaling on it.
- **Action**: if managed, define the **flip-to-self-host** trigger (spend > V* for N months; new compliance rule) and keep an open-weights equivalent identified. If self-host, define the **flip-to-managed** trigger (ops/outage cost exceeds savings; lost DevOps owner) and wire a managed fallback into the gateway. Keep the abstraction **thin (OpenAI-compatible)** so the flip is config, not migration. Re-evaluate quarterly.
- **Output**: a documented bidirectional flip trigger + a thin abstraction so reversing is cheap.
- **Evidence**: staged, reversible engine choices [vllm §7 common pattern]; bottleneck-driven re-evaluable decision [dify §1 判断公式].

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1: Low volume, but data-residency requires self-host

**Situation**: A regional healthcare startup runs a doc-grounded copilot. Volume is ~50k requests/mo — well **below** the cost crossover `V*`, where a managed API ($/token) would clearly be cheaper than buying and running a GPU. But patient data is bound by data-residency + air-gap rules.

**Tension**:
- The **volume slider** (OP-1) says *managed* — at this volume the GPU + ops floor is far more expensive than per-token spend.
- The **compliance gate** (OP-2) says *managed is forbidden* — data cannot leave the boundary.

**Resolution heuristic**:
- **The gate overrides the slider.** Evaluate compliance first; a hard residency/air-gap NO fails the managed path *regardless of how cheap it is* [dify Case 3: 合规/数据驻留, air-gapped → self-host].
- **But right-size it.** Compliance forcing self-host does **not** license self-host *scale*. Provision the **smallest adequate** stack — single replica, modest GPU — and accept the ops burden as the cost of compliance, not as an excuse to over-build (OP-1's `V*` still tells you how *small* you can go).
- **Check the escape hatch first**: if the managed provider offers an **in-region / VPC / BAA** tier that satisfies the boundary, that re-opens the (cheaper, zero-ops) managed path. Don't default to self-host before checking [OP-2].

**Evidence**: [dify Case 3 决策矩阵 (合规/数据驻留, air-gapped → self-host)]; [vllm OP-4 caveat (multi-tenant privacy / cache salting)].

### Dilemma 2: Dify self-host vs cloud — when is running your own worth the ops cost? (canonical)

**Situation**: A team is choosing between **Dify Cloud Pro/Team ($59–159/mo)** and **self-deploying Dify on Docker**. The pitch for self-host: "we own the data, and at scale it's cheaper than a subscription."

**Tension**:
- **Cost slider**: team ≤ 3, modest usage → Cloud ($59–159/mo) is **cheaper than diverting a DevOps engineer** [dify Case 3]. Millions of API calls → subscription cost **overruns infra** → self-host wins on raw unit cost [dify Case 3].
- **Hidden ops cost**: self-host is **not "docker compose up"** — it's reverse proxy + HTTPS + backups + monitoring + upgrades, and *production* needs **external** PostgreSQL/Redis/Vector DB (not the bundled containers), plus K8s + Helm [dify Case 3 实操要点].
- **Throughput ceiling**: Dify caps at **~10 QPS/pod** (per-node DB-query bottleneck) [dify §6.2] — so the "high volume" that justified self-host needs **many replicas**, which feeds back into the GPU+ops term and can move `V*` against you (OP-4).
- **The deflating finding**: Dify's **Community / Premium / Enterprise are the same Docker image**, differing only in env vars [dify Case 3]. The paid tier buys *support*, not *capability* — so "we need Enterprise to self-host properly" is usually false.

**Resolution heuristic**:
1. Run **OP-1 with the ops-labor term included** — not raw GPU price.
2. Run **OP-3's honest capacity check** — if there's no DevOps owner, managed wins even when the GPU math looks favorable.
3. Run **OP-4** — re-compute `V*` with the replica count needed to clear ~10 QPS/pod.
4. If volume is **spiky**, prefer **OP-5 hybrid**: self-host the steady floor, burst to Dify Cloud / a managed API.
5. Don't buy an Enterprise self-host tier for capability you already have in the open image (OP-6).

> Net: self-host Dify is worth the ops cost **only** above `V*` *and* with real ops capacity *and* after the replica-count math survives. Below any of those, the $59–159/mo subscription is the rational choice.

**Evidence**: [dify Case 3 决策矩阵 + 实操要点]; [architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host]; [dify §6.2 ~10 QPS/pod]; [dify §6.4 license caveat].

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### 6.1 常见反模式

| 反模式 | 症状 | 修法 |
|---|---|---|
| **Self-host for prestige at low volume** | "We run our own AI" with usage far below `V*` | Run OP-1; below `V*` managed wins — pay $/token, not GPU+ops |
| **Managed when compliance forbids it** | Cheaper plan chosen, then legal/audit blocks it | Run OP-2 **first** — the gate overrides the slider |
| **GPU-only costing** | `selfhost_cost` = GPU price, ops assumed free | Add the **`ops_labor`** term (backups, monitoring, on-call, upgrades) to `V*` |
| **"docker compose up = production"** | No reverse proxy / HTTPS / backups / external DBs | OP-3: production = external Postgres/Redis/VectorDB + K8s + upgrade path [dify Case 3] |
| **Ignoring per-replica ceilings** | "Cheaper at scale" math never counts replicas | OP-4: `replicas = peak_QPS / ~10 QPS-pod`, re-feed into `V*` [dify §6.2] |
| **Over-provisioning for peaks** | Idle GPUs billed 24/7 for spiky traffic | OP-5 hybrid: self-host floor + managed burst; idle GPUs invert unit cost |
| **Paying for same-image Enterprise tier** | Buy Enterprise to "unlock" self-host capability | OP-6: tiers are the same image gated by env vars — buy *support* only if needed [dify Case 3] |
| **One-way bet, no flip trigger** | No abstraction; reversing = migration project | OP-7: thin OpenAI-compatible surface + documented bidirectional trigger |
| **Treating the decision as permanent** | Decided once in 2024, never revisited | OP-7: re-evaluate quarterly — volume and price/quality frontier both move |

### 6.2 边界 (Hard boundaries)
- **Compliance is a gate, not a cost line.** A hard residency/air-gap requirement is binary and evaluated first; never trade it away for a cheaper bill [dify Case 3].
- **`V*` is utilization-conditional.** "Above `V*` → self-host" holds only at high, steady GPU utilization. Spiky traffic → hybrid (OP-5), not a fleet of idle GPUs.
- **Throughput ceilings are real.** ~10 QPS/pod (Dify) / KV-cache limits (vLLM) bound a single replica; volume → replica count → cost (OP-4).
- **Date-stamped (May 2026).** Managed $/token, GPU rental rates, and per-tier pricing move fast — **re-measure the crossover on your own numbers** before committing.

### 6.3 Where this rubric ends (hand-offs)
- Decided **self-host**, now choosing the **engine** → **[[agentsop-llm-engine-selection]]** (vLLM vs TGI vs SGLang vs TensorRT-LLM vs llama.cpp).
- Decided **self-host Dify**, now **building / operating** it → **[[agentsop-dify]]** (deploy, knowledge base, workflow, monitoring, the ~10 QPS/pod tuning).
- This skill does **not** size GPUs, pick quantization, or tune batching — those live in the per-framework SOPs.

---

## 7. 跨框架对照 (Cross-framework Comparison)

### 7.1 The three siting options

| Option | What you pay | Ops burden | Wins when | Examples |
|---|---|---|---|---|
| **Managed API / cloud** | $/token (marginal, no floor) | ~zero | below `V*`; no ops capacity; spiky/unpredictable volume; compliance satisfied by an in-region/BAA tier | OpenAI API, Anthropic API, **AWS Bedrock**, Dify Cloud |
| **Self-host** | GPU + ops labor + infra (fixed floor) + tiny marginal | high (DevOps, on-call, upgrades, backups) | above `V*` **with** high utilization **and** ops capacity; hard compliance/air-gap; vendor-neutrality required | **vLLM** + open weights ([[agentsop-llm-engine-selection]]); **self-hosted Dify** ([[agentsop-dify]]) |
| **Hybrid** | self-host floor + managed burst/tier | medium | high steady baseline **plus** spiky peaks, or premium/compliance tier + bulk tier | self-host baseline → burst to managed; compliance traffic self-host, bulk managed |

### 7.2 一行话对照 (one-liners)
- **Managed vs self-host**: managed is "$/token, zero ops, scales with usage"; self-host is "fixed floor + cheap-per-unit, but you run it." The crossover is **volume × compliance × ops-capacity** — never volume alone.
- **Bedrock (and similar)**: a managed API that can also be a **compliance escape hatch** — in-region / VPC / BAA tiers may satisfy a residency boundary without self-hosting (re-opens the cheaper path; check it in OP-2 before defaulting to self-host).
- **Self-host platform (Dify)**: the open Docker image is often *technically sufficient* — paid tiers are the **same image** gated by env vars [dify Case 3]; you pay for support, not capability (OP-6).
- **Self-host engine (vLLM)**: vendor-neutral, keeps the managed↔self-host door open; contrast with **TensorRT-LLM** — 30–50% faster but **locks you in** [vllm §7]. Lock-in is a cost line in OP-6.
- **Hybrid is the mature default at scale**: self-host the predictable floor for unit-cost, burst to managed for peaks — keeps GPU utilization high (the side-condition that makes `V*` real) and caps over-provisioning.

### 7.3 How the axes map to the source frameworks
- **Dify** [[agentsop-dify]] supplies the **canonical cost-vs-ops case** (Cloud $59–159/mo vs Docker), the **ops-burden reality** (external DBs, K8s, not "compose up"), the **throughput ceiling** (~10 QPS/pod), and the **same-image finding**. It is the worked example for OP-1/3/4/6.
- **vLLM** [[agentsop-llm-engine-selection]] supplies the **self-serving trade-offs**: CPU/throughput provisioning that bites before the GPU does, KV-cache/preemption ceilings (OP-4), tiered serving (OP-5 hybrid), and vendor lock-in vs neutrality (OP-6). It is the engine you reach for *after* this rubric says "self-host."
- Together they bracket the decision: this overlay decides **whether** to self-host; [[agentsop-dify]] and [[agentsop-llm-engine-selection]] decide **what** and **how** once you have.

---

## 附录: Cited sources

- Dify SOP (source skill): `output/dify-sop-skill/SKILL.md` — Case 3 (self-host vs cloud matrix, 实操要点), §6.2 (~10 QPS/pod), §6.4 (license caveat).
- vLLM SOP (source skill): `output/vllm-sop-skill/SKILL.md` — OP-4/OP-5 (throughput triage, prefix privacy), Dilemma 2 (tiered serving), Anti-pattern 6 (CPU provisioning), §7 (engine lock-in).
- Dify Cloud pricing / when to self-host: https://www.architjn.com/blog/dify-cloud-pricing-plans-free-tier-when-to-self-host
- Dify same-image tiers: https://github.com/langgenius/dify/discussions/32254
- Companion decision skills: `[[agentsop-llm-engine-selection]]` (which engine), `[[agentsop-dify]]` (how to build/operate self-hosted Dify).
