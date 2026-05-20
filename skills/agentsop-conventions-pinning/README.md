# conventions-pinning skill

A coder-agent skill for **writing, loading, and evolving** a project's convention file (CONVENTIONS.md / CLAUDE.md / .cursor/rules / .clinerules / AGENTS.md) so the agent reliably respects style choices on every session.

**Version**: 0.1.0
**Status**: Tool-agnostic; covers Aider, Claude Code, Cursor, Cline, CrewAI.

## What this skill answers

- What goes in a conventions file (and what bloats context for zero value).
- How to load it: Aider `--read`, Claude Code ancestor-walk, Cursor `.mdc` glob-scoped rules, Cline `.clinerules/` folder, CrewAI `backstory=`.
- How to evolve it: when to add a rule, when to delete a stale one, how to split into glob-scoped sub-rules.
- How to handle conflicts: CONVENTIONS.md says A, existing code shows B — what wins, and how to declare precedence.
- How to verify the agent actually loaded the file (the most common silent failure).

## Files

- `SKILL.md` — main skill (7 sections, ~440 lines, tool-agnostic SOP)
- `references/R1-source-evidence.md` — verbatim source quotes per claim
- `references/R2-tool-equivalents.md` — side-by-side comparison of CLAUDE.md / .cursorrules / .clinerules / AGENTS.md / CONVENTIONS.md / backstory
- `intermediate/operation_candidates.json` — 8 operations in Trigger / Action / Output / Evidence form

## Quick start

If you just want to pin one project today:

1. Read `SKILL.md` §3 Phase 1 (the template).
2. Write 5–15 bullets. Stop. Do not write more.
3. Save at the canonical path for your primary tool (see `SKILL.md` §3 Phase 1 table).
4. Wire the load mechanism for your tool (§3 Phase 2).
5. A/B test (§3 Phase 3): ask the agent to do something the rule covers, confirm it follows.

## Source basis

- Aider docs on `--read CONVENTIONS.md` ([aider.chat/docs/usage/conventions.html])
- Claude Code memory docs on CLAUDE.md, .claude/rules/, ancestor-walk, AGENTS.md interop ([code.claude.com/docs/en/memory])
- Cursor rules docs on `.mdc` format and migration from `.cursorrules` ([cursor.com/docs/rules])
- Cline rules docs on `.clinerules/` + memory-bank ([docs.cline.bot/customization/cline-rules])
- CrewAI docs on agent backstory ([docs.crewai.com/en/concepts/agents])
- Research on context-file bloat ([developer.upsun.com/posts/ai/agents-md-less-is-more], [blakecrosley.com/blog/agents-md-patterns])
