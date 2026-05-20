# selfhost-decision skill

A **project-kickoff rubric** for the one question every LLM/platform project hits: **should we run our own inference/platform, or pay for a managed API/cloud?**

This is a **Phase-D enhancement-overlay skill (D6)**. It does not deep-dive any framework — it fires *first*, at kickoff, decides *where to run*, and hands off to the per-framework SOPs once a side is chosen.

## The core idea

> **Self-host trades ops burden for control + unit-cost-at-scale. Managed trades $/token for zero ops. The crossover is a function of two axes — volume and compliance — that are not symmetric.**

- **Compliance is a GATE** — binary, evaluated **first**. A hard data-residency / air-gap requirement fails the managed path *regardless of how cheap it is*.
- **Volume is a SLIDER** — a continuous cost crossover `V*`. Below it managed wins; above it self-host wins, **but only if** utilization stays high and you actually have the ops capacity to run a GPU box.

```
V* = (GPU + ops_labor + infra_fixed) / ($/token_managed − $/token_marginal)
```

The term people forget is **`ops_labor`** — self-host is *not* "docker compose up." It is reverse proxy + HTTPS + backups + monitoring + upgrades + on-call, and production needs external Postgres/Redis/VectorDB.

## Scope

- **Activation**: at kickoff, choosing where an LLM / platform runs (managed API vs your own GPUs); or mid-project when **cost** or **data-residency** pressure forces a re-evaluation.
- **Not for**: *which engine* to self-host (→ `[[agentsop-llm-engine-selection]]`), *how to build* the Dify app (→ `[[agentsop-dify]]`), single-user/hobby workloads, or training/fine-tuning siting.
- **Date stamp**: May 2026. Managed $/token, GPU rates, and tier pricing move fast — **re-measure `V*` on your own numbers** before committing.

## Layout

```
d-selfhost-decision-skill/
├── SKILL.md                          # 7-section rubric (activation → cross-framework table)
├── README.md                         # This file
├── references/
│   └── R1-source-evidence.md         # Every claim traced to the source SOPs + primary docs
└── intermediate/
    └── operation_candidates.json     # Raw trigger / action / output / evidence for OP-1..7
```

## What's in SKILL.md

- **§1 何时激活** — kickoff "where to run" question; cost or compliance pressure; the "running our own is cheaper/more serious" reflex to challenge.
- **§2 核心心智模型** — the trade in one line; **two asymmetric axes** (compliance gate evaluated *before* volume slider); the `V*` crossover formula; the two side-conditions (utilization, ops capacity) that invalidate "above V* → self-host"; the throughput feedback loop; reversibility as a design choice.
- **§3 SOP** — gate (compliance) → slider (volume crossover) → honest ops-capacity check → throughput-headroom re-feed → hybrid option → fallback plan. Ordering is load-bearing.
- **§4 操作模型** — 7 ops: volume-crossover calc, compliance gate, honest ops-capacity check, throughput-headroom reality check, hybrid (self-host floor + managed burst), same-image/lock-in audit, fallback/exit plan.
- **§5 困境决策案例** — (1) low volume but data-residency requires self-host (gate overrides slider, but right-size it); (2) the canonical Dify self-host vs cloud ops-cost case (~10 QPS/pod, external DBs, same-image finding).
- **§6 反模式与边界** — self-host for prestige at low volume; managed when compliance forbids; GPU-only costing; "compose up = production"; ignoring per-replica ceilings; over-provisioning for peaks; same-image Enterprise tier; one-way bets; treating the decision as permanent.
- **§7 跨框架对照** — managed (OpenAI/Anthropic/**Bedrock**) vs self-host (**vLLM**/**Dify**) vs hybrid; Bedrock as a compliance escape hatch; how the axes map back to the source SOPs.

## Method

Mined from two sibling SOP skills in this repo: `dify-sop-skill` (the self-host-vs-cloud dilemma case, the ~10 QPS/pod bottleneck, the same-Docker-image finding) and `vllm-sop-skill` (self-serving trade-offs: CPU provisioning, KV-cache ceilings, tiered serving, vendor lock-in). Every load-bearing claim carries an inline `[source]` tag resolving to a source SOP or a primary doc. No fabricated numbers.

## Position in the Phase-D enhance set

- **Companion / hand-off skills**: `[[agentsop-llm-engine-selection]]` (which runtime, *after* you've decided to self-host) and `[[agentsop-dify]]` (how to build/operate self-hosted Dify). This overlay decides **whether**; they decide **what** and **how**.
- **Orthogonal axis**: this is a *where-to-run* economics decision, distinct from *which-tier-per-call* (`cost-tiered-models`) or *which-engine* siting.
