# prompt-history-inspect — Package README

This package distills the **first move in any LM-debugging session**: dump the actual rendered prompt the framework sent to the model, *before* changing anything else.

It is a **tool skill** (not an SOP for a framework). It enforces a 30-second inspect step across every LM-using framework — DSPy, LangChain, LangGraph, CrewAI, LlamaIndex, Aider, and raw OpenAI / Anthropic SDKs.

## Why this skill exists

Phase B of the coder-agent skill inventory marked prompt-history inspection as **core-tier, high-frequency** (5/7 SOPs depend on it). The existing skill.sh `promptex/prompt-history` package is thin (15 installs); local `langsmith` / `phoenix` skills cover the trace UI but not the *inspect-first* SOP. This skill closes the gap by:

1. Framing the SOP as a **30-second first move**, not a deep ritual.
2. Providing a **cross-framework cheat sheet** (§7) so the agent doesn't have to remember which framework uses which command.
3. Pinning down the **mental model** — "the prompt you wrote ≠ the prompt the LM received" — so the agent stops trusting its source code as ground truth.

## Contents

```
d-prompt-history-inspect-skill/
├── SKILL.md                          # main skill (7 sections, 10 ops, 4 dilemma cases)
├── README.md                         # this file
├── references/
│   ├── R1-mental-model.md            # the three layers (you wrote / rendered / LM saw)
│   └── R2-framework-cheat-sheet.md   # extended per-framework commands with code
└── intermediate/
    └── operation_candidates.json     # structured Trigger/Action/Output/Evidence
```

## How to use

The agent should load `SKILL.md` the moment any LM call produces an unexpected output. The activation trigger is universal: *any* surprise from the model → inspect first.

For drill-downs:
- "Help me understand the three-layer model" → load `R1-mental-model.md`.
- "What's the command for X framework?" → load `R2-framework-cheat-sheet.md`.
- Machine consumption (meta-pipeline, eval) → `intermediate/operation_candidates.json`.

## Provenance & quality notes

- **All commands cite official docs.** DSPy `inspect_history` → dspy.ai. LangChain `set_debug`/`set_verbose` → python.langchain.com/api_reference. LangGraph time-travel → langchain-ai.github.io/langgraph. CrewAI `step_callback` → docs.crewai.com. Aider commands → aider.chat/docs. OpenAI/Anthropic SDK logging → official GitHub READMEs.
- **The API-key-leak warning** for `OPENAI_LOG=debug` and `ANTHROPIC_LOG=debug` is cited from a real openai-python GitHub issue (#1196, #1082). This is a load-bearing safety boundary in §6.
- **Dilemma Case D** (production thread inspection) explicitly cites the LangGraph time-travel doc's caveat that `invoke(None, config=...)` re-executes LM calls and incurs cost — a common foot-gun.

## Version

- **Skill version**: 0.1.0
- **Frameworks covered**: DSPy 2.6+ / 3.x, LangChain 0.3+, LangGraph 1.x, CrewAI 0.80+, Aider 0.x, OpenAI Python SDK 1.x, Anthropic Python SDK 0.x
- **Last research**: 2026-05-19

## Related skills

- `langsmith`, `phoenix`, `langfuse`, `mlflow` — provide the *UI* for inspecting production traces; this skill provides the *SOP* and command lookup.
- `dspy-sop`, `langgraph-sop`, `crewai-sop`, `aider-sop` — framework-level SOPs that *use* this skill's commands inside their own debug workflows.
