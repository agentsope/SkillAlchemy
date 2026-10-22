# R5: Ecosystem Context — Claude Code vs. Cursor / Aider / Cline / Codex / Copilot

## The landscape, framed by interaction model

```
             HUMAN-IN-LOOP (steered)                 AUTONOMOUS
                        |                                   |
  +---------------------+--------+-----------+-------------+-----+
  | Terminal / CLI      | IDE inline | IDE chat | Sandbox / cloud |
  +---------------------+------------+----------+-----------------+
  | CLAUDE CODE, AIDER  | CURSOR     | CLINE    | CODEX (cloud)   |
  |                     | (fork IDE) | (VS Code |                 |
  |                     |            |  ext)    |                 |
  +---------------------+------------+----------+-----------------+
```

Claude Code and Aider stake out the **terminal/CLI + human-in-loop** corner; the IDE tools trade terminal purity for visual, inline editing.

## Side-by-side

| Aspect | Claude Code | Aider | Cursor | Cline | Codex |
|---|---|---|---|---|---|
| Vendor / open | Anthropic (proprietary) | Open source (Apache 2.0) | Closed-source (VS Code fork) | Open source | OpenAI (proprietary) |
| Surface | CLI + IDE ext + desktop | Terminal REPL | IDE (VS Code fork) | VS Code extension | CLI + cloud |
| Editing primitive | Tool loop: Read/Edit/Write + Bash | Diff/udiff/whole text + per-edit git commit | Composer, inline multi-file edits | Tool calls, per-step approval | Tool loop + cloud sandbox |
| Context strategy | CLAUDE.md + on-demand reads | tree-sitter repo-map + selective `/add` | Full-repo indexing | On-demand tool reads | On-demand + cloud workspace |
| Human approval | Permission gate on tools | Per turn (you press enter) | Per Composer apply | Per tool call | Configurable |
| Git integration | Native (git via Bash) | Auto-commit per edit | Manual | Via terminal | Cloud workspace |
| Model access | Claude-first | BYOM (many) | Multiple | Multiple | OpenAI-first |
| Extensibility | Skills, hooks, MCP, memory, subagents | Scriptable (`--message`, config) | Extensions | Extensions | — |

Note: this table describes qualitative differences, not benchmark results. No pass-rate numbers are asserted here; see each vendor's own documentation for current specifics.

## When to reach for Claude Code

- You are on Claude models and want the deepest integration (CLAUDE.md, skills, hooks, MCP, memory, subagents).
- You want a terminal/CLI agent that is also available in IDE and desktop forms.
- You value a permission-gated, verifiable loop with a project-memory file as the source of truth.

## When to reach for the alternatives

- **Aider** — you live in the terminal and want per-edit git commits and a repo-map; strong published experiments on edit formats and architect/editor splits.
- **Cursor** — you want visual, autocomplete-heavy, inline multi-file editing in a forked IDE.
- **Cline** — you want per-step approval gating inside VS Code.
- **Codex** — you want an OpenAI-native CLI agent with a cloud sandbox.
- **GitHub Copilot** — you want autocomplete + chat + agent features inside GitHub's ecosystem.

## The tool-agnostic core

Whatever front end you pick, the discipline is the same: feed the right context, decompose into verifiable steps, verify every change, and keep the context lean. That is the part that transfers, and it is what this skill encodes.
