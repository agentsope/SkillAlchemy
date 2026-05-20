# code-execution-decision

**Enhancement-overlay coder skill — T2: Code execution decision (emit-code-vs-reason).**

When should an LM agent write-and-run code (Program-of-Thought / code interpreter) versus
reason in natural language? This skill is the **decision rubric**. It overlays the `dspy` skill,
which ships the `ProgramOfThought` *mechanism* but not the *when*.

## Core claim

> LMs are unreliable calculators but reliable coders. Emit code when the answer needs
> determinism/precision (arithmetic, exact data manipulation, deterministic transforms);
> reason in prose when it needs judgment.

- **Under-coding** (reasoning through arithmetic) fails *silently* — a plausible wrong number.
- **Over-coding** (sandboxing a judgment task) fails *loudly and cheaply* — a wasted round-trip.

## The gate (one line)

> Is there a single verifiable answer a program could check?
> **YES → emit + run code → feed result back into the LM. NO → reason in prose. MIXED → decompose.**

## Contents

| File | Purpose |
|---|---|
| `SKILL.md` | The skill: 7 sections (activate / mental model / SOP / operations / dilemma cases / anti-patterns / cross-framework). |
| `references/R1-source-evidence.md` | Source evidence map — claims traced to DSPy docs, PoT/PAL papers, framework tool docs. |
| `intermediate/operation_candidates.json` | Candidate operations distilled during authoring (provenance for §4). |

## Cross-links

- `[[agentsop-output-format-by-model]]` — sibling: once you decide to emit code, how to serialize it (never nest code in JSON).
- `[[agentsop-test-fix-loop]]` — the bounded execute → error → retry loop this skill defers to.
- `dspy` — supplies `ProgramOfThought`; this overlay supplies the decision rubric it lacks.

## Framework mechanisms covered

DSPy `ProgramOfThought` · OpenAI Code Interpreter · Anthropic code-execution tool · LangChain `PythonREPLTool` (note: unsandboxed).

`name: code-execution-decision` · `version: 0.1.0`
