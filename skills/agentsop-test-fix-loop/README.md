# test-fix-loop · Skill

A framework-agnostic SOP for wiring a **verify-then-fix loop** around any
code-editing LLM agent: edit → run lint/test → format output as feedback →
agent fixes → re-run, bounded by an iteration cap and an escalation rule.

> One-liner: **The test result IS the next prompt.** Wiring the verifier
> command is 20% of the work; framing its output as a useful feedback message
> is 80%.

## What this skill is for

Coder agents need to converge on a verifiable spec — "lint and tests are
green". The naive approach ("give the agent a bash tool and let it run
`pytest`") has four predictable failure modes:

1. **Context bloat**: raw pytest output past the 25k threshold tanks accuracy.
2. **Infinite loops**: no termination contract, no stall detection.
3. **No audit trail**: edits overwrite each other; can't bisect.
4. **Cheating**: agent passes by adding `@pytest.mark.skip`.

This skill encodes the 7-step SOP that fixes all four:

1. Wire the verifier command (one combined `lint && type && test`)
2. Capture stdout + stderr + exit code (all three; ANSI-stripped; byte-capped)
3. Format feedback (first error, last frame, anchor to last edit, ≤2k tokens)
4. Bound the loop (`MAX_ITERS` + stall detector)
5. Per-iteration git commit (the audit lever)
6. Detect success precisely (no false positives, no cheats)
7. Escalate or commit on exit

## When to activate

- Any code-edit flow with a verifiable success command (pytest, ruff, mypy,
  eslint, tsc, go test, cargo check).
- Wrapping a coding agent so it doesn't return until lint+tests are clean.
- SWE-Bench-style runs (one issue → patch → tests → fix → submit).
- CI guardrail where a PR must be green before the agent declares done.

## When **not** to activate

- Success is subjective ("looks good") — no signal to feed back.
- Verifier takes >5 min and you need interactive UX — async the loop instead.
- Human review is the gate — use a HITL skill.
- Edits are exploratory / WIP — the loop will fight incomplete code.

## File map

| Path | Purpose |
|---|---|
| `SKILL.md` | Main skill: 7 sections (activation → mental model → SOP → operations → dilemmas → anti-patterns → ecosystem). |
| `references/R1-source-material.md` | Distilled evidence: Aider auto-lint/test docs, OpenHands SWE-Bench harness, Cline auto-approve, LangGraph recursion-limit lessons. Inline citations resolve here. |
| `references/R2-feedback-formatting-recipes.md` | Concrete pre/post examples for distilling pytest, mypy, ruff, eslint, tsc output into ≤2k-token feedback messages. |
| `intermediate/operation_candidates.json` | The 8 operations (OP-1..OP-8) in structured form: trigger, action, output, evidence — for skill-fusion downstream. |

## Cross-framework cheat sheet

| Framework | How to enable | Key flag/file |
|---|---|---|
| Aider | `aider --auto-lint --auto-test --lint-cmd "ruff check ." --test-cmd "pytest -x --tb=short"` | `.aider.conf.yml` |
| OpenHands (SWE-Bench) | Set `max_iterations` per instance | `evaluation/benchmarks/swe_bench/config.toml` |
| Cline | Auto-approve allowlist with `npm test`, `pnpm build`, etc. | `cline.autoApprove.allowlist` in VS Code settings |
| Claude Code | Wire the loop manually around the `Bash` tool | a script that calls Claude with formatted feedback |
| LangGraph | Tool node returns `{stdout, stderr, exit_code}`; conditional edge routes to fix-node or `END`; retry counter in state | `StateGraph` + `Annotated[int, operator.add]` |

## Reading order

1. `SKILL.md` §1–2 — when to activate, the four-primitive mental model.
2. `SKILL.md` §3 — the 7-step SOP, with concrete commands.
3. `references/R2` — formatting recipes (the load-bearing skill).
4. `SKILL.md` §5–6 — dilemma cases and anti-patterns (don't skip; the
   cheat-detection case has saved real codebases).
5. `SKILL.md` §7 — pick the framework that fits.

## Frontmatter

```yaml
name: test-fix-loop
version: 0.1.0
```

## Source lineage

Distilled from three first-party sources and external research:

- **Primary**: `output/aider-sop-skill/SKILL.md` + `references/R2-sop-workflow.md`
  (`--auto-lint`, `--auto-test`, `--auto-commits`).
- **Secondary**: `output/langgraph-sop-skill/` (tool → state → conditional
  edge → tool again pattern, bounded loop discipline).
- **Tertiary**: `output/crewai-sop-skill/` (task → result → next-task with
  feedback).
- **External**: Aider lint-test docs, OpenHands SWE-Bench README + infinite-loop
  bug report, Cline auto-approve docs.
