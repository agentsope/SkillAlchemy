---
name: agentsop-observability-setup
version: 0.1.0
description: |
  Enhancement-overlay skill — the DECISION + WIRING layer for LM observability that the
  single-backend skills [[langsmith]], [[phoenix]], [[mlflow]] do NOT cover. Each of those
  installs one backend; none of them help you DECIDE which backend fits your stack/scale/budget,
  nor give you a one-line autolog that turns it on fast. Use when starting any LM project,
  before the first deploy, or the moment someone asks "why did it do that?" and there are no traces
  to answer with. The skill picks a backend by stack (LangSmith for LangChain/LangGraph; Phoenix
  for OSS/local OpenTelemetry; MLflow for ML-shops already on MLflow; Langfuse for self-host),
  wires one-line autolog, verifies traces land, and adds eval hooks — instrumenting BEFORE you
  need it. Cross-links the first-debug-move skill [[agentsop-prompt-history-inspect]]. Do NOT activate to
  re-teach a backend you already chose (defer to its own skill), or for non-LM ML experiment
  tracking with no LLM calls (that is plain MLflow).
---

# Observability Setup — Which Backend + One-Line Autolog

> *"Instrument before you need it. The cheapest debugging session is a trace you already have."*

This is an **ENHANCE overlay**. The local skills [[langsmith]], [[phoenix]] and [[mlflow]] each
teach **one** backend deeply. This skill sits one level up: it answers the question those skills
cannot — *which one, and how do I turn it on in a single line right now* — then hands off to the
chosen backend's own skill for depth.

---

## 1. 何时激活 (When to activate)

Activate at one of three moments — earlier is always cheaper:

| Trigger | Signal |
|---|---|
| **Starting any LM project** | First `dspy.LM` / `ChatOpenAI` / `LlamaIndex` / agent graph in the repo, and no tracing wired yet |
| **Before first deploy** | About to ship an LM feature to real users with no trace UI — the AP-15 trap (§6) |
| **"Why did it do that?" with no traces** | A bug surfaced, you reach for history, and there is nothing recorded — you are debugging blind |
| **Multi-component pipeline** | Retriever + reranker + LLM + tools; per-call printing ([[agentsop-prompt-history-inspect]]) is no longer enough |
| **Cost / latency regression** | Need aggregate token & latency dashboards across runs, not a single printout |

**Do NOT activate** when:
- You have already chosen a backend and just need its API — defer to [[langsmith]] / [[phoenix]] / [[mlflow]] directly.
- The task is classic ML experiment tracking with **no LLM calls** — that is plain MLflow, no decision needed.
- You only need to read **one** rendered prompt right now — that is [[agentsop-prompt-history-inspect]] (the cheaper first move).

The relationship to [[agentsop-prompt-history-inspect]]: that skill is the *reactive* first move (dump one
prompt, no setup). This skill is the *proactive* layer — wire persistent tracing so the next "why"
is answered by a trace that already exists, not a frantic re-run.

---

## 2. 核心心智模型 (Core mental model)

```
   Instrument BEFORE you need it
   ───────────────────────────────────────────────
   pick backend      one-line          verify         add eval
   by constraints →  autolog turns  →  a trace    →   hooks (judge,
   (stack/scale/      it on            actually        datasets,
    budget)           (~1 line)        landed          alerts)
   ───────────────────────────────────────────────
   cost of skipping each stage compounds: a missing trace at deploy
   becomes a multi-hour blind-debug later (AP-15, §6).
```

Three load-bearing ideas:

1. **Choosing is the hard part, not wiring.** Every modern backend offers ~one-line autolog
   (`langsmith` env vars, `px.launch_app()`, `mlflow.<framework>.autolog()`). The real cost is
   picking the one that won't lock you in or under-serve you at scale (§4 decision table, §5 cases).
2. **The cheapest debugging is a trace you already have.** A trace recorded proactively costs
   near-zero; reconstructing one after a production bug costs hours and may be impossible (no repro).
3. **One backend, owned end-to-end.** Don't wire two trace backends "to be safe" — pick one,
   standardize on it, and let OpenTelemetry GenAI semantics keep you portable if you outgrow it (§7).

---

## 3. SOP (Standard operating procedure)

A five-step path. Each step gates the next.

### Step 1 — Pick the backend by constraints
Run the decision table in §4 (OP-1). Inputs: **stack** (is it LangChain/LangGraph? OSS-only? already on MLflow?), **scale** (dev-only vs high-volume production), **budget/hosting** (managed-OK vs must-self-host). Output: exactly one backend.

### Step 2 — One-line autolog
Wire the single call/env-var for the chosen backend (OP-2). Resist building a custom tracing layer first — autolog gets you a trace today; you can refine later.

### Step 3 — Verify traces actually land
Run one real LM call, then open the trace UI and confirm the call appears with inputs, outputs, latency, and token counts (OP-3). A backend that is "configured" but shows no traces is the #1 silent failure (wrong project name, env var not exported, sampling at 0).

### Step 4 — Add eval hooks
Once raw traces flow, attach what makes them actionable: an LLM-as-judge or rule evaluator, a dataset built from real traces for regression testing, and basic cost/latency alerts (OP-4). This is what turns "we have logs" into "we catch regressions before users do."

### Step 5 — Hand off to the backend skill
Hand off to the chosen backend's own skill ([[langsmith]] / [[phoenix]] / [[mlflow]]) for the deep API once tracing and evals are flowing (OP-6).

**Step gating, explicitly.** Do not start Step *n+1* until Step *n* is observably true. The
most common failure is jumping from Step 2 (wired) straight to Step 4 (evals) without Step 3
(verify) — you build evaluators on top of a trace stream that was silently empty the whole time.
Each step has a one-line proof: Step 1 → a backend name written down; Step 2 → an autolog call
in the code; Step 3 → one trace visible in the UI with token counts; Step 4 → one evaluator
firing on that trace. If any proof is missing, you are not at that step yet.

---

## 4. 操作模型 (Operational model — Trigger / Action / Output / Evidence)

### OP-1 · Backend decision table  *(the core of this skill)*
- **Trigger**: Stage 1 — you have an LM project and no backend chosen yet.
- **Action**: Match your dominant constraint to a row. First matching row wins; ties broken by the "tie-breaker" column.

| If your situation is… | Choose | Why | Tie-breaker / caveat |
|---|---|---|---|
| Stack is **LangChain / LangGraph** (or LlamaIndex) and managed SaaS is acceptable | **LangSmith** → [[langsmith]] | First-class, zero-glue integration; "same team builds both" so tracing is native ([R1] swarnendu.de / langgraph AP-15) | Vendor lock-in; pricing scales with trace volume — see Case B (§5) |
| **OSS-only / local-first**, want OpenTelemetry, no vendor lock-in | **Phoenix (Arize)** → [[phoenix]] | OTel-based, self-hosted with SQLite/Postgres, framework-agnostic ([R1] phoenix SKILL frontmatter) | Self-host = you run the infra; managed Arize Cloud exists if you outgrow it |
| You are an **ML-shop already running MLflow** (model registry, experiments) | **MLflow** → [[mlflow]] | One pane of glass: LLM traces alongside existing runs/registry; `mlflow.<fw>.autolog()` ([R1] mlflow SKILL; dspy-sop deploy line) | LLM-trace UI is younger than purpose-built LLM tools; fine if MLflow is already your hub |
| Must **self-host** a purpose-built LLM-observability product (data-residency, privacy) | **Langfuse** | Self-hostable LLM-native tracing + evals; the common DSPy/CrewAI bolt-on ([R1] dspy-sop "LangFuse-style traces"; crewai obs) | Not a local skill here — install per Langfuse docs; OTel-compatible |
| Mixed stack, want **maximum portability**, framework churn expected | **OpenTelemetry GenAI** semantics under any of the above | Standard span schema → swap backends without re-instrumenting | More wiring; pick a concrete backend (Phoenix is OTel-native) to actually view spans |

- **Output**: Exactly one backend name + its skill to hand off to.
- **Evidence**: backend frontmatter in [[langsmith]]/[[phoenix]]/[[mlflow]]; langgraph-sop AP-15; llamaindex-sop "LangSmith / Phoenix for observability"; dspy-sop MLflow + LangFuse lines. See `references/R1-source-evidence.md`.

### OP-2 · One-line autolog per backend
- **Trigger**: Stage 2 — backend chosen, turn it on.
- **Action**: Use the *minimal* turn-on for the chosen backend:
  ```python
  # LangSmith — env vars only, no code change (auto-traces LangChain/LangGraph):
  #   export LANGSMITH_TRACING=true
  #   export LANGSMITH_API_KEY=...   export LANGSMITH_PROJECT=my-app
  # (raw SDK / non-LangChain: wrap calls with langsmith.wrappers.wrap_openai or @traceable)

  # Phoenix — launch local app + auto-instrument:
  import phoenix as px; px.launch_app()
  from phoenix.otel import register
  register(auto_instrument=True)        # picks up installed framework instrumentors

  # MLflow — one autolog call per framework:
  import mlflow
  mlflow.set_tracking_uri("http://localhost:5000")
  mlflow.dspy.autolog()                 # or mlflow.langchain / mlflow.openai / mlflow.crewai
  ```
- **Output**: Traces start flowing on the next LM call — no per-call instrumentation written by hand.
- **Evidence**: [[langsmith]]/[[phoenix]]/[[mlflow]] quick-start sections; dspy-sop `mlflow.dspy.log_model` deploy line; prompt-history-inspect op-001 (`mlflow.dspy.autolog`).

### OP-3 · Verify a trace actually landed
- **Trigger**: Stage 3 — autolog wired, before trusting it.
- **Action**: Run one real call, open the UI (LangSmith project / `px` localhost / MLflow `:5000`), confirm the run shows **inputs + outputs + latency + token count**. If empty: check project name, that the env var is exported in *this* process, and that sampling ≠ 0.
- **Output**: One verified trace = the backend is real, not just configured.
- **Evidence**: AP "configured-but-empty" is the most common silent failure; verify-before-trust is standard SOP (`references/R2`).

### OP-4 · Add eval hooks on top of raw traces
- **Trigger**: Stage 4 — traces flow; make them actionable.
- **Action**: Attach (a) an evaluator — LLM-as-judge (Phoenix) or dataset evaluators (LangSmith) or logged metrics (MLflow); (b) a dataset built **from real traces** for regression testing; (c) cost/latency alerts. Defer the deep API to the chosen backend's skill.
- **Output**: Traces become a regression-catching system, not just a log.
- **Evidence**: [[langsmith]]/[[phoenix]] evaluation sections; llamaindex-sop "eval loop is what surfaces failures"; dspy-sop metric pattern.

### OP-5 · What to trace (minimum payload)
- **Trigger**: Deciding what each span should capture.
- **Action**: At minimum capture, per LM call: **rendered prompt, response, model id, latency, token in/out, and the upstream context** (for RAG: `query + retrieved_nodes + scores + index_id`; for agents: tool name + args + observation).
- **Output**: A span that can answer "why did it do that" without a re-run.
- **Evidence**: llamaindex-sop line 159 ("tracing captures query + retrieved_nodes + scores + index_id + LLM prompt for every failure"); prompt-history-inspect §what-to-dump.

  **Quick decision: how much to capture.** Default to the minimum payload above on *every* span,
  plus full request/response bodies on **errors and a sampled fraction of successes**. Capturing
  full bodies on 100% of high-volume traffic is the over-instrumenting trap (§6) and the cost
  driver in Case B. Capturing *less* than the minimum recreates AP-15 in slow motion — you have
  traces, but they cannot answer the "why."

### OP-6 · Handoff to backend skill
- **Trigger**: Backend wired and verified; need depth (custom evaluators, datasets, dashboards, alerting).
- **Action**: Stop here and invoke the chosen backend's own skill — [[langsmith]], [[phoenix]], or [[mlflow]]. This overlay deliberately does not duplicate their APIs.
- **Output**: Clean separation — decision/wiring here, depth there.
- **Evidence**: overlay design; this skill's boundary (§6).

---

## 5. 困境决策案例 (Dilemma cases / worked examples)

### Case A — Vendor lock-in: LangSmith vs OSS Phoenix
**Situation**: A team building on LangGraph wants tracing before launch. LangSmith is one env-var
away and natively integrated; Phoenix is OSS/OTel but needs self-hosting.
**Tension**: Speed-to-trace + native integration (LangSmith) vs no vendor lock-in + data control
(Phoenix). The langgraph-sop is explicit that LangSmith integration is first-class — "the same team
builds both" ([R1] AP-15).
**Resolution**: If you are **LangChain/LangGraph-first and SaaS is acceptable**, take LangSmith
now — the integration tax of Phoenix is real and AP-15 warns against shipping with *no* tracing far
more loudly than against the lock-in. If **data must stay in-house** or you have a mixed/OSS stack,
take Phoenix and accept the self-host cost. The wrong move is to dither and ship with neither
(AP-15). Either choice beats no choice; OTel semantics (§7) keep migration possible.

### Case B — Trace volume at scale (the Replit problem)
**Situation**: A product graduates from dev to high traffic. Per-trace pricing on a managed backend
turns "nice dashboards" into a line item that scales linearly with users; full-fidelity tracing of
every call becomes both expensive and noisy.
**Tension**: Full observability vs cost & signal-to-noise at production volume. High-volume LLM
products (the Replit-class case — agent products generating millions of LM calls) cannot afford to
trace 100% on a metered SaaS plan, but turning tracing *off* recreates AP-15.
**Resolution**: Don't binary-choose between "trace all" and "trace none." (1) **Sample** —
full-fidelity on errors and a small % of successes; (2) move to a **self-hosted** backend (Phoenix /
Langfuse) where marginal cost is infra, not per-trace fees, once volume crosses the break-even; (3)
keep eval datasets curated from sampled traces so regression coverage survives the sampling. Decide
the sampling/hosting policy *before* the bill or the noise forces a panicked migration — instrument
before you need it, but scale the instrumentation deliberately.

---

## 6. 反模式与边界 (Anti-patterns & boundaries)

**Anti-patterns**

- **AP-15 · No observability in production** *(the headline trap)*. Shipping an LM feature with no
  trace UI. "Replaying a checkpoint locally only goes so far; production needs the trace UI"
  ([R1] langgraph-sop AP-15). Symptom: a user hits a bug, you have nothing to inspect, and you
  cannot reproduce it. Fix: this skill's Stage 1–3 *before* deploy.
- **Over-instrumenting**. Wiring two trace backends "to be safe," tracing every internal function
  as a span, or building a bespoke tracing layer before trying one-line autolog. Cost: noise,
  double bills, maintenance burden. Fix: one backend, autolog first, add detail only where a real
  question demands it.
- **Configured-but-empty**. Declaring victory after wiring autolog without verifying a trace landed
  (OP-3). The env var wasn't exported in the running process, the project name is wrong, or sampling
  is 0 — and you discover it only when you need a trace and there is none.
- **Tracing the prompt but not the response / context**. Truncation, refusal, and bad-retrieval
  bugs live in the response and the upstream nodes, not the prompt (OP-5).
- **Leaving full-fidelity tracing on at scale without a cost plan** (Case B).

**Boundaries** (when this skill is the wrong tool)

- Backend already chosen → use [[langsmith]] / [[phoenix]] / [[mlflow]] directly; this overlay adds nothing.
- Need to read **one** prompt right now, no setup → [[agentsop-prompt-history-inspect]] is the cheaper move.
- Pure ML experiment tracking, no LLM calls → plain MLflow; there is no backend *decision* to make.
- Pre-call infra failure (auth/network/import) → fix infra; there is nothing to trace yet.

---

## 7. 跨框架对照 (Cross-backend comparison)

| Backend | Hosting | Stack fit | One-line turn-on | Lock-in | Local skill |
|---|---|---|---|---|---|
| **LangSmith** | Managed SaaS (self-host enterprise) | LangChain / LangGraph / LlamaIndex first-class | `export LANGSMITH_TRACING=true` (+ key + project) | High (proprietary) | [[langsmith]] |
| **Phoenix (Arize)** | Self-host (SQLite/Postgres) or Arize Cloud | OSS / any framework via OTel | `px.launch_app()` + `register(auto_instrument=True)` | Low (OSS, OTel) | [[phoenix]] |
| **MLflow** | Self-host / managed (Databricks) | ML-shops; framework-agnostic, registry + runs | `mlflow.<framework>.autolog()` | Low (Apache-2.0) | [[mlflow]] |
| **Langfuse** | Self-host (LLM-native) or cloud | DSPy / CrewAI bolt-on; privacy/data-residency | `from langfuse import Langfuse` + framework callback | Low (OSS) | *(no local skill — per docs)* |
| **OpenTelemetry GenAI** | Backend-agnostic span schema | Any — portability layer under the above | Instrument with OTel GenAI conventions, export to chosen backend | None | *(standard, not a product)* |

**Reading the table**: pick by the *dominant* constraint, not a feature checklist. Stack-coupling
(LangSmith), OSS/lock-in aversion (Phoenix), existing-MLflow-investment (MLflow), and
hosting/privacy (Langfuse) are the four forces; OpenTelemetry is the escape hatch that keeps any
choice reversible. Then hand off to the matching local skill for depth.

---

*Overlay note: this skill intentionally stops at decision + one-line wiring + verification + eval
hooks. For backend-specific APIs (custom evaluators, dataset management, dashboards, alerting),
defer to [[langsmith]], [[phoenix]], [[mlflow]]. For the reactive single-prompt dump, see
[[agentsop-prompt-history-inspect]].*
