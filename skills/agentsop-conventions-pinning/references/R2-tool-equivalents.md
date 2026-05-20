# R2 — Tool equivalents for project-level conventions

Side-by-side comparison of the five mechanisms a coder-agent ecosystem uses to pin project conventions.

---

## At a glance

| Tool | Filename / location | Load mechanic | Multi-file? | Glob scoping? | Personal layer? |
|---|---|---|---|---|---|
| Aider | `CONVENTIONS.md` (any name, by convention) at repo root | Explicit: `--read FILE` or `.aider.conf.yml read:` | Multiple `--read` flags | No (file is global to session) | No built-in user layer |
| Claude Code | `CLAUDE.md`, `.claude/CLAUDE.md`, `CLAUDE.local.md` | Auto: walks cwd → root, concatenates | Native via `.claude/rules/*.md` | Yes (`paths:` YAML frontmatter) | Yes (`~/.claude/CLAUDE.md`, `CLAUDE.local.md`) |
| Cursor | `.cursor/rules/*.mdc` (legacy: `.cursorrules`) | Auto-attach via `alwaysApply` or `globs:` | Native; nested `.cursor/rules/` per subdir | Yes (`globs:` in `.mdc` frontmatter) | User-level rules in settings |
| Cline | `.clinerules/*.md` and `.clinerules/*.txt` | Auto: all files in folder concatenated | Native (any number of files, optional numeric prefix for order) | Yes (`paths:` YAML frontmatter, glob array) | Yes (global rules; workspace wins on conflict) |
| CrewAI | Agent `backstory=` string in Python code | Embedded into agent's system prompt at construction | One backstory per agent (multiple agents = multiple backstories) | No (style is per-agent, not per-file) | None built-in |

---

## Detailed mechanic-by-mechanic

### 1. Aider — explicit read-only attach

**Filename**: by convention `CONVENTIONS.md`, but anything works.

**Activation**:
```bash
aider --read CONVENTIONS.md src/foo.py
# or
/read CONVENTIONS.md  # inside a running session
```

**Persistent config** (`.aider.conf.yml` in repo root):
```yaml
read: CONVENTIONS.md
# or:
read: [CONVENTIONS.md, docs/style.md]
```

**Why read-only**: keeps the agent from editing it; enables prompt caching across turns. *"This way it is marked as read-only, and cached if prompt caching is enabled."* [aider.chat/docs/usage/conventions.html]

**Verification**: `/tokens` lists the file in the budget breakdown.

**Failure mode**: forgetting to add `--read` on a new shell. Solution: pin in `.aider.conf.yml`.

---

### 2. Claude Code — ancestor-walk auto-load

**Filenames**:
- `./CLAUDE.md` (project, committed)
- `./.claude/CLAUDE.md` (project, committed, alternative location)
- `./CLAUDE.local.md` (project, gitignored, personal)
- `~/.claude/CLAUDE.md` (user-global)
- Managed policy: `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS), `/etc/claude-code/CLAUDE.md` (Linux/WSL), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows)

**Activation**: automatic. Claude Code walks from cwd up to the filesystem root, picks up every CLAUDE.md and CLAUDE.local.md it finds, concatenates them in order (root first, cwd last; within a directory, CLAUDE.md before CLAUDE.local.md).

Subdirectory CLAUDE.md files are **not** loaded at session start; they're loaded on-demand when Claude reads a file in that subdirectory.

**Multi-file pattern via `.claude/rules/`**:
```
your-project/
├── .claude/
│   ├── CLAUDE.md           # always-loaded base
│   └── rules/
│       ├── code-style.md   # always-loaded (no paths frontmatter)
│       ├── api.md          # loaded only when src/api/** is touched
│       └── tests.md        # loaded only when tests/** is touched
```

Path-scoped rule example:
```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/api/**/*.tsx"
---
# API rules
- All endpoints validate input with zod
- Return errors via the standard error envelope
```

**Imports** (loaded at launch in full):
```markdown
@README.md
@AGENTS.md
```
Max 5 hops of recursive imports. Approval dialog on first encounter.

**Verification**: `/memory` lists every file loaded into the current session.

**Failure mode**: contradictions across the ancestor chain (parent CLAUDE.md says X, project CLAUDE.md says Y). Claude picks arbitrarily. Audit with `/memory` and `claudeMdExcludes` setting.

---

### 3. Cursor — `.mdc` glob-scoped rules

**Filenames** (modern):
- `.cursor/rules/<topic>.mdc` — one file per topic
- Nested `.cursor/rules/` per subdirectory for scoped rules

**Filenames** (legacy, deprecated):
- `.cursorrules` at repo root

**Activation**: automatic. Each `.mdc` has YAML frontmatter that controls when it loads:
```yaml
---
description: Python style rules for our backend
alwaysApply: false       # only attach when glob matches
globs:
  - "**/*.py"
  - "src/**/*.py"
---
# Python style
- 4-space indent
- Type hints everywhere; ruff enforces ANN*
```

Three attachment modes:
- `alwaysApply: true` — loaded into every conversation
- `globs:` — loaded when Cursor opens a matching file
- Manual — referenced via @-mention in chat

**Limit**: ~500 lines per rule recommended; aggressively trim always-apply rules. [cursor.com/docs/rules]

**Verification**: Cursor sidebar shows active rules per conversation.

**Migration from `.cursorrules`**: incremental — keep the legacy file working while moving sections one-by-one into `.mdc` files. [vibecodingacademy.ai/blog/cursor-rules-complete-guide]

---

### 4. Cline — `.clinerules/` folder with optional glob frontmatter

**Filenames**:
- `.clinerules/coding.md`
- `.clinerules/testing.md`
- `.clinerules/architecture.md`
- (optional numeric prefixes: `01-coding.md`, `02-testing.md` for ordering)

**Activation**: automatic. All `.md` and `.txt` files in `.clinerules/` are read at the start of every conversation, concatenated into a unified rule block.

**Conditional rules**:
```markdown
---
paths:
  - "src/**/*.tsx"
  - "components/**/*.tsx"
---
# React component rules
- Functional components only
- Hooks at top of function body
```

**Layered rules**: workspace (`<project>/.clinerules/`) + global (user-level). On conflict, **workspace wins**. [docs.cline.bot/customization/cline-rules]

**Memory bank — separate mechanism**:
- Folder: `memory-bank/`
- Files: `projectBrief.md`, `activeContext.md`, `progress.md`, etc.
- Cline reads **all** memory bank files at the start of **every** task. *"This is not optional."*
- Mutable: the agent writes back to memory-bank during work.

`.clinerules/` is stable preferences. `memory-bank/` is working memory. Do not conflate.

**Verification**: Cline sidebar shows loaded rules and memory-bank files.

---

### 5. CrewAI — backstory as system-prompt suffix

**Location**: in Python code, at agent construction:
```python
researcher = Agent(
    role="Senior Data Researcher",
    goal="Uncover cutting-edge developments in {topic}",
    backstory="""You are a seasoned researcher with a knack for
    finding obscure connections in dense technical literature.
    You favor citation density over rhetoric. You distrust unsourced
    claims. Always provide source URLs.""",
    allow_delegation=False,
    max_iter=8,
    verbose=True,
)
```

**Style is per-agent**, not per-project. A team of 3 agents has 3 backstories.

**No file-based equivalent** built into CrewAI. To pin project-wide style, you read a file in Python and inject it:
```python
with open("PROJECT_STYLE.md") as f:
    style = f.read()

researcher = Agent(..., backstory=f"{base_backstory}\n\nProject conventions:\n{style}")
```

**Verification**: inspect the agent object's `system_prompt` attribute (or trace via mlflow/Maxim).

---

## Cross-tool unification — `AGENTS.md` pattern

If a repo is used with multiple coder-tools, pick one canonical file and have the others point at it.

```
repo/
├── AGENTS.md              # canonical — ~80 lines, the actual rules
├── CLAUDE.md              # one line: @AGENTS.md (loads it at session start)
├── .cursorrules           # legacy — keep until full Cursor migration
├── .cursor/rules/
│   └── main.mdc           # frontmatter alwaysApply: true; body copies/imports AGENTS.md
├── .clinerules/
│   └── main.md            # symlink → ../AGENTS.md
└── .aider.conf.yml        # `read: AGENTS.md` so Aider picks it up
```

Cursor's `.mdc` requires frontmatter, so it can't be a plain symlink to AGENTS.md — either (a) duplicate the body, or (b) regenerate via a pre-commit hook.

Claude Code's `/init` reads existing `.cursorrules` / `.windsurfrules` / `AGENTS.md` automatically [code.claude.com/docs/en/memory], so you can start with the legacy file and let Claude Code pick it up.

---

## What none of these handle well

- **Cross-machine personal preferences**. CLAUDE.local.md is local to its directory; if you have 5 worktrees, you write it 5 times. Workaround: `@~/.claude/my-prefs.md` import in CLAUDE.md.
- **Truly cross-tool guarantees**. Each tool's adherence is probabilistic and tool-specific. The unification above gets you *one source of truth*, not *uniform behavior*.
- **Secrets / private URLs**. None of these are secret-safe (CONVENTIONS.md is committed). Use `CLAUDE.local.md` (gitignored) for personal sensitive paths.
- **Mutable working memory** — only Cline's `memory-bank/` has a built-in answer. For the others, working memory has to be reconstructed each session from the rules + the code.
