# R1 — Source Evidence Map

Traceability for every load-bearing claim in `SKILL.md`. Grouped by section.

---

## Core thesis: "LMs are unreliable calculators but reliable coders"

| Claim | Source | Note |
|---|---|---|
| Decouple computation from reasoning: LM writes code, interpreter computes the result | Program of Thoughts (PoT), Chen et al., **arXiv 2211.12588** | The foundational PoT paper. Frames numerical reasoning as program generation + external execution; outperforms chain-of-thought on math/financial QA precisely because the LM stops being the calculator. |
| LM as coder, runtime as the deterministic solver | PAL: Program-aided Language Models, Gao et al., **arXiv 2211.10435** | Independent confirmation: offload the *solving* to a Python interpreter; the LM only emits the program. The asymmetry (good at writing code, bad at arithmetic) is the empirical premise of this skill. |
| Next-token prediction ≠ correct-value computation | Synthesis of PoT + PAL | The mechanism for why prose arithmetic hallucinates plausible-but-wrong digits. |

---

## §1 / §3 — Activation triggers and the gate

| Claim | Source | Note |
|---|---|---|
| Module choice `ChainOfThought` vs `ProgramOfThought` for a signature | DSPy modules docs — [dspy.ai/learn/programming/modules/] | DSPy lists both modules and says PoT is for "math/counting/parsing." It supplies the mechanism and a one-line hint, but **not** a decision rubric — the gap this overlay fills. Confirmed against the dspy-sop SKILL.md §4.2 module-selection table. |
| "computable = single verifiable answer" gate | Derived from PoT/PAL premise | A question with a checkable ground truth is one a program can verify; one without is judgment. |

---

## §3 / §4 — SOP + operations

| Claim | Source | Note |
|---|---|---|
| Emit code → sandbox → run → feed result back into LM | PoT design, arXiv 2211.12588 + DSPy `ProgramOfThought` runtime | PoT is "code computes, LM contextualizes." The result-back step is intrinsic, not optional. |
| Bounded retry on error (`max_iters` ≈ 3) | DSPy `ProgramOfThought` module behavior — [dspy.ai/learn/programming/modules/] | PoT regenerates code on traceback up to a capped iteration count, then stops. Defers to `test-fix-loop` for the general pattern. |
| Sandbox choice / safety profiles | Framework tool docs (below) | DSPy uses a Python interpreter sandbox; OpenAI/Anthropic are managed/VM-sandboxed; LangChain PythonREPLTool is in-process and unsandboxed. |

---

## §6 / §7 — Anti-patterns + cross-framework

| Claim | Source | Note |
|---|---|---|
| Generated code must not be nested in JSON | Sibling skill `output-format-by-model` (Aider code-in-JSON: 61%→20% on GPT-4 Turbo) — [aider.chat/2024/08/14/code-in-json.html] | The serialization gate is separate from the execution gate; both must pass. Cross-linked as `[[agentsop-output-format-by-model]]`. |
| OpenAI Code Interpreter = managed container, stateful | OpenAI Assistants code tool docs — [platform.openai.com/docs/assistants/tools/code-interpreter] | Files + state persist across turns; suited to data-analysis sessions. |
| Anthropic code-execution tool = sandboxed VM, first-party | Anthropic docs — [docs.anthropic.com/en/docs/agents-and-tools/tool-use/code-execution-tool] | Safe for untrusted inputs; results return to the conversation. |
| LangChain `PythonREPLTool` runs in-process, unsandboxed | LangChain tool docs — [python.langchain.com/docs/integrations/tools/python] | Documented warning that it executes arbitrary code in-process; treat as untrusted-input-hostile. Worst safety profile of the four. |

---

## Cross-skill provenance

| Cross-link | Relationship |
|---|---|
| `dspy-sop-skill/SKILL.md` | Ships `ProgramOfThought` (mechanism); §4.2 names it for "math/counting/parsing" but gives no when-to-use-vs-reason rubric. This overlay supplies that rubric. |
| `d-output-format-by-model-skill/SKILL.md` | Sibling on the *format* of code-shaped content (PoT for math/parse; code never in JSON). Decides *how* to serialize once *whether-to-code* is settled here. |
| `test-fix-loop` | The bounded execute → error → retry loop; §3 Step 3 and §6 anti-pattern #4 defer to it. |

---

## Notes on confidence

- **High confidence**: PoT/PAL papers and DSPy module docs are stable, primary sources for the core thesis and mechanism.
- **Medium confidence**: exact `max_iters` default (~3) varies by DSPy version — cited as approximate.
- **Cross-linked, not re-derived**: the Aider code-in-JSON 61%→20% figure is owned by the sibling `output-format-by-model` skill and cited here only to justify the no-nest-in-JSON anti-pattern.
