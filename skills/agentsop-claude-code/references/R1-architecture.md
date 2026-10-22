# R1: Claude Code Architecture & Mental Model

## Core insight

Claude Code is an **agentic loop wrapped around three things**: a model that reads context, a tool surface (Read / Edit / Write / Glob / Grep / Bash / Agent / …), and a permission gate in front of irreversible and outward-facing actions. Efficiency is not about typing faster — it is about feeding the right context and verifying every step.

```
+-----------------------------------------------------------------+
|  Claude Code (CLI / IDE / desktop)                              |
|                                                                 |
|   user request  -->  model reads context (CLAUDE.md + history)  |
|                              |                                   |
|                              v                                   |
|                      choose a tool (Read/Edit/Glob/Grep/Bash/…) |
|                              |                                   |
|                              v                                   |
|                      observe the result                         |
|                              |                                   |
|                              v                                   |
|                      decide next step  -->  (repeat until done) |
+-----------------------------------------------------------------+
```

Every one of the "best practices" in this skill is a consequence of this loop: give the model instructions it can verify from tool output, keep the context small enough to stay relevant, and let each turn's result decide the next turn.

## The three context layers

| Layer | Content | Who controls it |
|---|---|---|
| System + CLAUDE.md | Project memory, rules, conventions | You (write into CLAUDE.md) |
| Session history | Accumulated conversation and tool results | You (`/clear`, `/compact`) |
| Transient reads | Files/regions read this turn | The model (reads on demand) |

The first principle of context economy: **push anything recurring into CLAUDE.md** so the session history stays lean, and **let the model read files on demand** instead of pre-loading everything.

## The tool surface

Claude Code exposes dedicated file tools that beat the equivalent shell commands on three axes: they integrate with the permission UI, they can be cited precisely as `file:line`, and they cost less context.

| Purpose | Preferred tool | Why not the shell |
|---|---|---|
| Find files by name | Glob | `find` output is noisy and untyped |
| Search content | Grep (ripgrep) | `grep -r` bypasses the permission model |
| Read a file | Read (offset/limit) | `cat` dumps the whole file |
| Edit precisely | Edit (old/new) | whole-file rewrites are error-prone |
| Create a file | Write | — |

Bash remains the right tool for **running** things — builds, tests, git, package managers — not for *finding* things.

## Permissions, memory, skills, and hooks

- **Permissions** gate tools into allow / ask / deny. Irreversible or outward-facing actions (delete, overwrite, push, publish) should be confirmed before running.
- **Memory** is persistent, file-based, and per-project/per-user; it holds facts and preferences that outlive a session.
- **Skills** package reusable instructions (with optional bundled files) that the model loads on demand; the user or project can add their own.
- **Hooks** run automated actions around tool calls and events, configured in `settings.json`.

The relevant reference for all of the above is the official documentation at `code.claude.com/docs` and the in-session `claude --help` / `/help`.
