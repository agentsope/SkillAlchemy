# R1 — Source Evidence for cost-tiered-models

Every load-bearing claim in SKILL.md, traced to a source SOP in this repo or a primary doc. Phase-D enhance skill M7. No fabricated numbers.

---

## 1. Aider — architect + editor (the headline evidence)

**Source SOP**: `output/aider-sop-skill/SKILL.md` §4 Phase 4 + §7 research legacy.
**Primary**: aider.chat/2024/09/26/architect.html ; aider.chat/docs/leaderboards/

Published Polyglot Pass@2 numbers (quoted as-is):

| Combo | Polyglot Pass@2 | Note |
|---|---|---|
| o1-preview alone | **79.7%** | strong reasoner, but editing format dirty |
| o1-preview (architect) + o1-mini (editor, whole) | **85%** | SOTA at the time; slow, "probably not practical for interactive use" |
| o1-preview (architect) + Sonnet (editor) | **82.7%** | "entirely practical" |
| Sonnet + Sonnet | **80.5%** | up from 77.4% self-run |
| GPT-4o + GPT-4o | **75.2%** | up from 71.4% self-run |

Key extracted claim: **two cheap specialized calls beat one expensive all-in-one call** when the reasoner's *editing* (format compliance) is weaker than its *reasoning*. Even Sonnet self-paired improves (77.4% → 80.5%), showing the gain is structural, not just from a stronger editor.

Mechanism: architect emits a **natural-language plan**; editor turns it into a format-correct diff. Aider auto-switches the editor to `editor-diff` / `editor-whole` (leaner prompt, edit-focused).

**Supporting — JSON-wrapping harms reasoning** (OP-4, anti-pattern 4):
> "All of the models did worse on the benchmark when asked to return code in a structured JSON response." — aider.chat/2024/08/14/code-in-json.html
> "JSON-wrapping may distract or challenge models in a way that reduces their ability to reason about solving coding problems."
⇒ Cheap executors must be given the format they handle well (whole / simple schema), never code-in-JSON-tool-call.

**Supporting — escalation on edit failure** (OP-3, dilemma 2):
aider.chat/docs/troubleshooting/edit-errors.html — when SEARCH blocks fail to match, escalate the model or fall back to `--edit-format whole`; weaker models "more easily disregard the system prompt".

---

## 2. DSPy — optimizer-LM vs task-LM (the mirror)

**Source SOP**: `output/dspy-sop-skill/SKILL.md` §3 Stage (decide which model optimizes vs is the task model), §4.1 table, Case A, Case B.
**Primary**: github.com/stanfordnlp/dspy/issues/1596 ; dspy.ai/api/optimizers/BootstrapFinetune/

Claims used:

- DSPy explicitly separates **which model optimizes vs which model is the task model — they can differ** [dspy SKILL §3 Stage 2 step 8].
- **Cheap optimizer-LM, expensive task-LM** (OP-5): community evidence reports parity using gpt-4o-mini as the optimizer LM while the task LM stays gpt-4o, at a fraction of cost [github.com/stanfordnlp/dspy issue #1596; dspy SKILL Case A step 5].
- **Distill-after-split** (OP-6): `BootstrapFinetune(student=Llama-3.2-1B-Instruct, teacher=gpt-4o-mini)` — optimize on the big model, then distill into a 1B–7B student [dspy SKILL §4.1].
- **Recalibrate on model swap** (anti-pattern 7, OP-6 warning): "If you optimize a complex pipeline for GPT-4, it usually breaks on a smaller model like Llama-3-8b" → always recompile when changing the task-LM family; verbose GPT-4 CoT demos make small models "parrot length without reasoning" [dspy SKILL Case B].

**Why this is a mirror, not a contradiction** (§7.2): in DSPy the *cheap* role is the optimizer (scaffolding / meta layer that does not enter the final product); the *expensive* role is the task call (the product). The unifying rule holds: calls whose output enters the final product and need judgment → Tier-S; scaffolding / search / proposal calls → Tier-E.

---

## 3. LangGraph — supervisor + worker

**Source SOP**: `output/langgraph-sop-skill/SKILL.md` §3 multi-agent decision tree, OP-4 (`Send` dynamic workers), Case 2 (supervisor vs swarm).
**Primary**: langchain-ai.github.io/langgraph/concepts/multi_agent/

Claims used (OP-7, anti-pattern 2):

- Supervisor pattern: a single supervisor routes; sub-agents are tools/workers. "Highest token cost (supervisor 'translates' sub-agent output)" [langgraph SKILL §3 tree].
- Benchmark finding: swarm "slightly outperformed supervisor across all scenarios"; supervisor "consistently uses more tokens than swarm" because of the translation step [langgraph SKILL Case 2].
- Extracted: supervisor = Tier-S (decide/route/synthesize), workers = Tier-E (execute a subtask). The supervisor's translation overhead is a **fixed split cost** — relevant to anti-pattern 2 (over-splitting tiny workflows).

---

## 4. vLLM — speculative decoding draft + target

**Source SOP**: `output/vllm-sop-skill/SKILL.md` Step 5, OP-6, Dilemma 5.
**Primary**: docs.vllm.ai/en/latest/features/speculative_decoding/ ; developers.redhat.com/articles/2025/07/01/fly-eagle3-fly

Claims used (OP-3, dilemma 2 evidence):

- A cheap **draft** model (small model / EAGLE-3 / MTP / n-gram) proposes tokens; the expensive **target** model verifies and corrects against its true distribution.
- Up to **~2.5×** decode speedup with EAGLE-3 [developers.redhat.com 2025 eagle3]; n-gram (no draft weights) gives a modest ~1.17×.
- **The escalation/abort condition**: at high QPS the GPU is already saturated by real batch work, so speculation "steals capacity instead of filling idle cycles" — disable it [vllm SKILL Dilemma 5]. This is the hardware-layer analogue of "if escalation rate is too high, don't split" (dilemma 2, anti-pattern 6).

Speculative decoding is the cleanest proof that the pattern is structural (not LLM-prompting-specific): the same "cheap proposes, strong verifies, reject → correct with the strong model" shape appears one layer down in the inference stack.

---

## 5. The unification claim

All four reduce to: **frequency-asymmetric calls + decoupled reason/execute ability + a failure valve.**

1. **Frequency asymmetry** — execution-tier calls vastly outnumber decision-tier calls; cost is execution-dominated; downgrading execution is where the money is.
2. **Capability decoupling** — reasoning strength ≠ clean execution/output (Aider 79.7% reasoner is a poor editor; the split recovers up to +5.3pp).
3. **Failure valve** — Aider escalates the model, DSPy recompiles, LangGraph reroutes, vLLM rejects-and-corrects. Splitting is "cheap covers the common case + strong backstops the long tail", not one-way downgrade.

Phase B catalogued these as four separate SOP entries under four names. This skill names the shape once: **cost-tiered models**.
