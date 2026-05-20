---
name: agentsop-conventions-pinning
version: 0.1.0
description: SOP for writing, loading, and evolving a project-level convention file (CONVENTIONS.md / CLAUDE.md / .cursor/rules / .clinerules / AGENTS.md) so that a coder-agent reliably respects your codebase's style choices every session. Tool-agnostic; covers the four load mechanics (read-only attachment, ancestor-walk auto-load, glob-scoped rules, agent backstory) and the conflict resolution between pinned conventions and the existing code.
domain: coder-agent infrastructure / context engineering
audience: coder-agents and engineers configuring them, on any project lived in for > 1 day
trigger_keywords:
  - "conventions file"
  - "CONVENTIONS.md"
  - "CLAUDE.md"
  - ".cursorrules"
  - ".clinerules"
  - "AGENTS.md"
  - "coding standards for AI"
  - "style guide for agent"
  - "agent ignored my rule"
  - "pin my coding style"
when_to_use:
  - "any project you (or your agent) will return to more than once"
  - "the same correction has been typed into chat more than twice"
  - "code review (human or LLM) keeps catching style violations the agent should know"
  - "onboarding a new agent / new teammate; they need the project's tacit rules in writing"
  - "you switch coder-tools and want one canonical style source across Aider, Claude Code, Cursor, Cline"
when_not_to_use:
  - "one-off / throwaway scripts where the cost of writing rules > the cost of the work"
  - "true greenfield where conventions ARE being invented as code; pin AFTER the first 2-3 modules stabilise"
  - "you need hard enforcement (lint/format/CI) — conventions are guidance, hooks/precommit are enforcement"
  - "the project already has a lint config that fully encodes the rule — point at the lint config instead"
---

# Conventions Pinning — Writing a Style Guide Your Coder-Agent Will Actually Read

> One line: a conventions file is **the system prompt of your codebase**. Treat it like a system prompt, not like a README. Anti-patterns: writing prose, narrating history, marketing the project. Patterns: command-first, verifiable, "prefer X over Y", < 200 lines.

---

## 1. 何时激活 (When to Activate)

### 1.1 Direct triggers
- The user (human or upstream agent) asks "how do I make Claude/Cursor/Cline/Aider respect our style?".
- The same correction has been typed in chat ≥ 2 times this week ("use httpx not requests", "add type hints", "no comments on every line"). Claude Code's docs codify this rule: *"Add to it when Claude makes the same mistake a second time."* [code.claude.com/docs/en/memory]
- A new project is past the "first 2 modules" phase — there are now style choices implicit in the code that an outsider (or fresh-context agent) can't see.
- The team is switching coder-tools (Aider → Claude Code, or adding Cursor) and conventions are scattered in chat history.
- An AI code review caught the same anti-pattern twice.

### 1.2 Reverse triggers (skip)
- **One-off / throwaway scripts**. The write-cost of a conventions file is fixed; the savings are proportional to session count. < 3 sessions → don't bother.
- **True greenfield**. The first 2-3 files of a project ARE the convention. Pinning style before the style exists locks in arbitrary choices.
- **Hard enforcement needed**. A conventions file is *context*, not a *hook*. Claude Code's docs are explicit: *"CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer."* [code.claude.com/docs/en/memory] If the rule must run every time (e.g. "must `make lint` before commit"), write a hook / precommit / CI check.
- **The rule is already in a config that the agent can read** — `.eslintrc`, `pyproject.toml`, `.editorconfig`, `tsconfig.json`. Point the agent at the config; don't duplicate.

### 1.3 Mental check
> A conventions file earns its tokens only if it contains **information that is not already in the repository**. The research is unambiguous on this: *"Developer-written context files performed better for exactly the reason you'd guess: they contained information that wasn't already in the repository — tooling preferences, workflow requirements, conventions that existed in developers' heads but not in any documentation."* [developer.upsun.com/posts/ai/agents-md-less-is-more]

If everything you would write into CONVENTIONS.md is already discoverable from `package.json`, `pyproject.toml`, `.eslintrc`, the test directory, and obvious code patterns — don't write the file. The agent will pre-cache it itself.

---

## 2. 核心心智模型 (Mental Model)

### 2.1 Convention as compile-time, code-review as runtime

```
+-------------------------------------+   +-------------------------------------+
|  COMPILE-TIME (conventions file)    |   |  RUNTIME (code review / lint / CI)  |
|                                     |   |                                     |
|  - Loaded once per session          |   |  - Runs on every change             |
|  - Shapes generation                |   |  - Catches violations after-the-fact|
|  - Cheap to update, free to ignore  |   |  - Costly to set up, hard to ignore |
|  - "Prefer X over Y" lives here     |   |  - "X must always hold" lives here  |
|  - Style + intent + preferences     |   |  - Invariants + safety + correctness|
+-------------------------------------+   +-------------------------------------+
        ^                                            ^
        |        Conventions guide;                  |
        |        review enforces.                    |
        |        Both are needed; they fail          |
        |        in different ways.                  |
```

Conventions fail by **silent drift**: agent ignores the rule once, no one notices, code is merged. Review fails by **late catch**: violation is found post-PR, expensive to fix. The two complement, not substitute.

### 2.2 The four load mechanics across the ecosystem

Every coder-tool has settled on one of four mechanics for getting persistent context into the agent. Knowing which mechanic your tool uses is the difference between "agent reads my rules" and "agent silently ignores them."

| Mechanic | Examples | How it works |
|---|---|---|
| **Read-only attach (explicit)** | Aider `--read CONVENTIONS.md` | You explicitly attach the file. Loaded read-only every session, cacheable. [aider.chat/docs/usage/conventions.html] |
| **Ancestor-walk auto-load** | Claude Code `CLAUDE.md`, `./.claude/CLAUDE.md`, `~/.claude/CLAUDE.md` | Tool walks from cwd up to root, concatenates every `CLAUDE.md` it finds, plus `CLAUDE.local.md` per directory. Subdirectory files load on-demand when files in that dir are read. [code.claude.com/docs/en/memory] |
| **Glob-scoped rules dir** | Cursor `.cursor/rules/*.mdc`, Claude Code `.claude/rules/*.md` with `paths:` frontmatter, Cline `.clinerules/*.md` with `paths` frontmatter | Multiple small files. Each can declare a `paths:` glob; rule loads only when the agent touches a matching file. [cursor.com/docs/rules], [docs.cline.bot/customization/cline-rules] |
| **Agent backstory** | CrewAI agent `backstory=` field, single-agent system-prompt suffix | Style/preferences embedded into the agent's persona at construction time. Per-agent, not per-project. [docs.crewai.com/en/concepts/agents] |

A project that uses multiple tools should pick **one source of truth** and have the other tools `@`-import or symlink to it. Claude Code 2.x docs explicitly recommend this: *"If your repository already uses AGENTS.md for other coding agents, create a CLAUDE.md that imports it ... `@AGENTS.md`."* [code.claude.com/docs/en/memory]

### 2.3 Three rules for what goes in (and what doesn't)

| ✅ Put in | ❌ Keep out |
|---|---|
| "Prefer httpx over requests." [aider.chat/docs/usage/conventions.html] | "We've been using Python since 2019 ..." (project narrative) |
| "Use 2-space indentation." | "Run `npm install` then `npm test`." (already in package.json) |
| "API handlers live in `src/api/handlers/`." [code.claude.com/docs/en/memory] | "Format code properly." (unverifiable) |
| "Add type hints everywhere; ruff `ANN*` rules are on." | "Be careful with database connections." (ambiguous) |
| Anti-pattern: "Never use `os.system`; use `subprocess.run`." | "TODO: write better docs here." (file is not a TODO list) |
| Workflow that's not in a script: "Before commit, run `make fmt && make test`." | The output of `make help` (the agent can `make help` itself) |

**The litmus test**: *would this information be discoverable by a competent developer who spent 30 minutes browsing the repo?* If yes — leave it out, the agent will discover it too. If no — pin it. [developer.upsun.com/posts/ai/agents-md-less-is-more]

### 2.4 Size budget: 200 lines, hard

Claude Code documentation: *"Target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."* [code.claude.com/docs/en/memory]

Cursor docs: *"Keep rules concise: under 500 lines. ... A 1,000-word always-apply rule is expensive, so trim aggressively or convert it to auto-attached with appropriate globs."* [cursor.com/docs/rules]

Aider docs: *"Above about 25k tokens of context, most models start to become distracted."* [aider.chat/docs/troubleshooting/edit-errors.html] — and CONVENTIONS.md is one chunk competing for that budget against the actual code.

When the file passes ~200 lines, split it: glob-scoped rules (Cursor, Claude Code `paths:`), per-language file (`python.md`, `react.md`), or move detail into a skill that loads on demand.

### 2.5 The conflict precedence rule

You will eventually hit: **CONVENTIONS.md says A, the existing code shows B.** What wins?

Default precedence the major tools converge on:

```
managed/org policy   >  user (~/.claude/)  >  project (./)  >  local (gitignored)
                          (loaded in order; later overrides for conflicts)
existing code in repo  ⟂  conventions file   ← these don't have built-in precedence;
                                                you must declare it explicitly
```

The agent does **not** know which one you want to win unless you tell it. Two patterns:

1. **Convention wins, refactor the drift.** Add to CONVENTIONS.md: *"If existing code conflicts with these rules, flag it as drift and propose a refactor, do not propagate the old pattern."*
2. **Code wins, archive the rule.** If the codebase has irrevocably moved past a rule, delete the rule. Stale rules are worse than no rules — they cost tokens and create silent contradictions.

Claude Code docs warn about this directly: *"If two rules contradict each other, Claude may pick one arbitrarily. Review your CLAUDE.md files ... periodically to remove outdated or conflicting instructions."* [code.claude.com/docs/en/memory]

---

## 3. SOP 工作流 (Standard Operating Procedure)

### Phase 0: Decide whether to write one at all

```
[Q1] Will this codebase be touched in ≥ 3 future sessions?
       no  -> skip; pin nothing.
       yes -> continue.

[Q2] Are there style/library choices NOT already encoded in config files
     (pyproject, eslintrc, editorconfig, tsconfig)?
       no  -> point the agent at the existing configs; skip a conventions file.
       yes -> continue.

[Q3] Is the rule something the agent should DO (guidance) or something that
     MUST hold (invariant)?
       must hold -> write a hook/precommit/CI check instead.
       guidance  -> conventions file is the right tool. Continue.
```

### Phase 1: Write — the first cut

Start with **5–15 bullets, max**. Aider's documented example is exactly this minimal: two bullets ("prefer httpx over requests" + "use types everywhere"). [aider.chat/docs/usage/conventions.html]

Structure template (copy this):

```markdown
# <Project> Conventions

## Language & versions
- Python 3.12+ (no 3.11 syntax workarounds).
- Node 20 LTS, TypeScript strict mode.

## Libraries — prefer / avoid
- HTTP client: prefer `httpx` over `requests`.
- Date math: prefer `pendulum` over stdlib `datetime` for tz-aware ops.
- Avoid: `os.system` (use `subprocess.run`), `eval`, raw f-strings in logging.

## Style
- Type hints everywhere (`ANN*` ruff rules are on).
- 2-space indent (TS), 4-space (Python).
- No inline comments unless explaining "why not how".

## Layout
- API handlers: `src/api/handlers/`
- Shared types: `src/types/`
- Tests mirror source: `tests/<module>/test_<file>.py`

## Workflow
- Before commit: `make fmt && make test`.
- Conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`.

## When this file disagrees with existing code
- Treat existing code as drift; propose a refactor in a separate commit.
```

Save it at the **canonical location for the primary tool**:

| Tool | Location |
|---|---|
| Aider | `CONVENTIONS.md` at repo root (loaded with `--read`) |
| Claude Code | `./CLAUDE.md` or `./.claude/CLAUDE.md` |
| Cursor (modern) | `.cursor/rules/main.mdc` (one rule file) |
| Cursor (legacy) | `.cursorrules` at repo root (deprecated but still works) |
| Cline | `.clinerules/coding.md` |
| Multi-tool | `AGENTS.md` at repo root; have CLAUDE.md / .cursorrules / .clinerules import or symlink |

### Phase 2: Load — make sure the agent actually reads it

This is where most projects fail silently.

| Tool | Load command / config |
|---|---|
| Aider | `aider --read CONVENTIONS.md` per invocation, OR put `read: CONVENTIONS.md` into `.aider.conf.yml`. [aider.chat/docs/usage/conventions.html] |
| Claude Code | Automatic. `CLAUDE.md` in cwd and all ancestor dirs are loaded at session start. Verify with `/memory` — it lists every loaded file. [code.claude.com/docs/en/memory] |
| Cursor | `.mdc` files in `.cursor/rules/` auto-attach. Use `alwaysApply: true` or `globs:` in frontmatter. [cursor.com/docs/rules] |
| Cline | All `.md`/`.txt` files in `.clinerules/` are concatenated and loaded automatically. [docs.cline.bot/customization/cline-rules] |
| CrewAI | Paste relevant rules into each agent's `backstory=` string at construction time. [docs.crewai.com/en/concepts/agents] |

**Verify the load worked, every time you change tools or environments**:

- Aider: `/tokens` shows the file in the context budget.
- Claude Code: `/memory` lists it.
- Cursor: hover the rule in the sidebar — it shows which conversation it's active in.
- Cline: the rules panel in the Cline sidebar shows the loaded set.

If the file isn't shown — the agent isn't reading it. Don't proceed.

### Phase 3: Enforce — close the loop with a test

Pin one **specific, verifiable** rule (e.g. "use httpx not requests"). Then ask the agent to write a new HTTP call from scratch. If it uses `requests`, the load failed or the rule is too vague. Fix and retest.

This is the same test Aider documents: their example explicitly shows `httpx` + type hints get used *with* CONVENTIONS.md and `requests` + no types get used *without*. [aider.chat/docs/usage/conventions.html] If you cannot produce that A/B in your own setup, the load is broken.

### Phase 4: Evolve — when to add a rule, when to delete one

**Add a rule when** (codified from Claude Code docs): [code.claude.com/docs/en/memory]
1. Agent makes the same mistake twice in a session, or twice across sessions.
2. A code reviewer catches something the agent should have known about *this* codebase.
3. A new teammate would need the same context to be productive.
4. You re-explain the same correction in chat a third time.

**Delete a rule when**:
1. The codebase has moved past it — the rule says "use X" but every new file uses Y and the team agrees.
2. Lint/CI now enforces it (move from convention to enforcement).
3. The rule is too vague to verify and has produced no measurable behavior change ("be careful with concurrency").
4. The file is over ~200 lines and this rule has the lowest hit rate.

**Split a rule when** it only applies to part of the codebase: use glob-scoped rules. Claude Code `.claude/rules/api.md` with `paths: ["src/api/**/*.ts"]`. Cursor: per-`.mdc` `globs:` field. This shrinks the always-on context budget. [code.claude.com/docs/en/memory], [cursor.com/docs/rules]

### Phase 5: Review — periodic audit (monthly or per major refactor)

```
1. Run `/memory` (or equivalent) — list what's loaded.
2. For each rule:
     - Has it been triggered? (grep recent PRs / chat for the keyword)
     - Does the codebase still follow it? (grep code for violations)
     - If both no → delete.
     - If first no, second yes → the rule is enforced by gravity; consider deleting.
     - If first yes, second no → drift; either fix code or kill rule.
3. Check size: > 200 lines → split into glob-scoped rules.
4. Check for contradictions across files (project + user + ancestor).
```

---

## 4. 操作模型 (Operation Model)

Eight reusable operations. Each is Trigger / Action / Output / Evidence. Detailed JSON form in `intermediate/operation_candidates.json`.

| # | Operation | Trigger | Action | Output |
|---|---|---|---|---|
| OP-1 | **Decide-to-pin** | User asks how to make agent respect style, OR same correction typed ≥ 2× | Run Phase 0 decision tree | `pin` / `skip` / `use-hooks-instead` |
| OP-2 | **Write first cut** | Decision = pin | Fill the 6-section template (Language / Libraries / Style / Layout / Workflow / Conflict-rule), 5–15 bullets total | `CONVENTIONS.md` (or tool-equivalent) at canonical path |
| OP-3 | **Wire load mechanism** | File written | Pick tool's load path: `--read` flag, ancestor-walk, glob `paths:`, or backstory string | File appears in agent's loaded-files list |
| OP-4 | **Verify with A/B test** | Load wired | Ask agent to perform a task that triggers a specific bullet (e.g. HTTP call); confirm rule was followed | Pass/fail; if fail go back to OP-3 |
| OP-5 | **Add a rule** | Same mistake twice OR review caught project-specific knowledge | Add bullet that is concrete, verifiable, and not already encoded in lint/config | Updated file, < 200 lines |
| OP-6 | **Delete a stale rule** | Codebase moved past it, OR rule is unenforceable, OR file > 200 lines and rule has lowest hit rate | Remove the bullet; if it now lives in lint/CI, note that in commit msg | Slimmer file |
| OP-7 | **Split into glob-scoped rule** | Rule applies only to subset (e.g. only `src/api/`); main file passing 200 lines | Move rule into per-glob file with `paths:` frontmatter (Claude Code rules / Cursor `.mdc` `globs:`) | New scoped file; main file shrinks |
| OP-8 | **Cross-tool unification** | Project uses multiple coder-tools (e.g. Claude Code + Cursor + Aider) | Make one file canonical (`AGENTS.md` at root is the cross-tool convention); have other tools `@`-import or symlink to it | One source of truth, multiple thin pointers |

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 — "I added `--read CONVENTIONS.md` but the agent still uses requests instead of httpx"

**Symptom**: rule is loaded (Aider `/tokens` shows it; Claude Code `/memory` lists it), but generation ignores it.

**Differential diagnosis** (cheapest first):

1. **Token budget exceeded**. Aider: *"Above about 25k tokens of context, most models start to become distracted."* [aider.chat/docs/troubleshooting/edit-errors.html] Drop irrelevant files; `/tokens` to confirm.
2. **Conflicting nearby example**. The agent is reading existing code in the same session that uses `requests`. Code-in-context is a stronger demonstration than a one-line rule. *"If two rules contradict each other, Claude may pick one arbitrarily."* [code.claude.com/docs/en/memory] Fix: add the conflict-resolution clause to CONVENTIONS.md ("if existing code uses requests, treat as drift and propose refactor"), or `/drop` the conflicting files.
3. **Rule is too vague**. "Prefer modern HTTP libs" is ignorable; "Use `httpx.Client` with `timeout=10.0`; do not import `requests`" is not.
4. **Multiple conventions files contradict**. User-level (`~/.claude/CLAUDE.md`) says one thing, project says another. Claude Code loads them in a defined order (managed → user → project → local) [code.claude.com/docs/en/memory] — but if both have the same rule wording with different answers, the merge is ambiguous. Verify with `/memory`.
5. **Stale cache**. Aider caches the read file across the session; restart if you edited it.

**Resolution rule**: if cases 1–4 don't resolve it, the rule belongs in **enforcement** (lint, precommit), not **guidance**. Add a ruff rule to `pyproject.toml` that bans `import requests`. The conventions file is not a hammer.

### Case 2 — "Style drift across files: half use `httpx`, half use `requests`. Fix in conventions or in code?"

**Trigger**: codebase has visible inconsistency. Agent will mirror whichever file it reads first.

**Decision rule**:

| If ... | Then ... |
|---|---|
| The team has decided httpx is the future, no exceptions | (a) Add rule to CONVENTIONS.md; (b) write a single PR that migrates all `requests` callsites; (c) add a lint rule forbidding `requests` |
| There's a *reason* the old code uses requests (e.g. a sync-only library inside) | Document the exception in CONVENTIONS.md ("`requests` allowed in `src/legacy/`, banned elsewhere") and consider a glob-scoped rule |
| Half-and-half because no one decided | Make the decision, then case (a). The conventions file is the wrong place to record an *unresolved* choice |

**The anti-pattern to avoid**: writing "agents should use httpx going forward" without doing the migration. The agent will see 50% requests in the existing code, ignore your rule, and the drift continues. Conventions describe **the codebase you have**, not the one you wish you had. If the rule contradicts > ~30% of the existing code, **fix the code first, pin the rule second**.

### Case 3 — "I'm using Claude Code AND Cursor on the same repo. Two conventions files? Or one?"

**Decision**: one. Two files = two truths = silent disagreement.

**Implementation** (Claude Code 2.x's recommended pattern): [code.claude.com/docs/en/memory]

```
repo/
├── AGENTS.md                  # canonical, ~80 lines
├── CLAUDE.md                  # one line: "@AGENTS.md"
├── .cursor/rules/main.mdc     # frontmatter alwaysApply: true; body: contents copied or symlinked
└── .clinerules/main.md        # symlink → ../AGENTS.md (Cline reads .md transparently)
```

For Cursor (`.mdc` files require frontmatter, can't symlink raw), either:
- Generate the `.mdc` from `AGENTS.md` in a pre-commit hook, OR
- Keep the rule body short enough that copying it across 3 tools is tolerable.

**Surprising finding from the research**: Claude Code's `/init` reads existing `.cursorrules` and `.windsurfrules` and incorporates them into the generated `CLAUDE.md`. [code.claude.com/docs/en/memory] So if you already have a `.cursorrules`, Claude Code will not silently ignore it on first init — it pulls it in.

### Case 4 — "My CONVENTIONS.md is now 600 lines. Adherence is dropping."

**Diagnosis**: violating both Aider's 25k-distraction threshold (in aggregate context) and Claude Code's 200-line per-file recommendation. [code.claude.com/docs/en/memory], [aider.chat/docs/troubleshooting/edit-errors.html] Cursor's docs are even more explicit: *"if you're hitting context limits, look at your always-apply rules first."* [cursor.com/docs/rules]

**Resolution sequence** (cheapest first):

1. **Audit for stale rules**. Delete any rule the codebase no longer follows. Delete any rule covered by lint/CI now.
2. **Split by file scope**. Move language-specific rules to glob-scoped files (Claude Code `.claude/rules/python.md` with `paths: ["**/*.py"]`; Cursor `.mdc` with `globs:` field). Only the rules matching files-in-this-session load.
3. **Move detail into skills / playbooks**. Workflows that aren't always-on (e.g. "release procedure") belong in a skill or runbook the agent loads on demand, not in CONVENTIONS.md.
4. **Demote prose**. Any paragraph longer than 2 sentences is probably narrative. Rewrite as bullets or delete.

Target after pruning: < 150 lines, every line a verifiable directive.

### Case 5 — "Greenfield: my coder-agent is writing the project from scratch. Should I pin conventions?"

**Decision**: **not yet**. Pinning conventions before the conventions exist forces premature decisions and the agent will fight you on them.

**Right sequence**:
1. Let the agent write 2–4 modules with minimal guidance (just language + framework version).
2. Read what it produced. Pick the choices you want to keep.
3. *Now* write CONVENTIONS.md with those choices, plus the libraries you've added.
4. Future modules inherit the now-pinned style.

The exception: **policy-level** rules that aren't about code style but about constraints — "never call external APIs without explicit approval", "no secrets in git history", "all functions need docstrings". Those can be pinned from day 0 because they don't depend on emergent style.

### Case 6 — "Agent ignored a rule despite a perfect load. What now?"

The unintuitive bit: CONVENTIONS.md is **context, not enforcement**. Claude Code documents this explicitly: *"CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself. Claude reads it and tries to follow it, but there's no guarantee of strict compliance, especially for vague or conflicting instructions."* [code.claude.com/docs/en/memory]

Tiered response:

| Tier | Action |
|---|---|
| 1 | Rewrite the rule to be more specific. "Format properly" → "Use 2-space indent, double quotes, no trailing comma in JSON" |
| 2 | Move it earlier in the file (recency in context matters) and bold it |
| 3 | Add a counter-example: "Wrong: `requests.get(url)`. Right: `httpx.get(url, timeout=10)`" |
| 4 | If the rule MUST hold, demote it to a hook / lint / CI gate. Conventions are guidance, not contracts |

---

## 6. 反模式与边界 (Anti-Patterns and Boundaries)

### Anti-patterns (do not do these)

1. **Project narrative in CONVENTIONS.md**. "Our team started this in 2020 ..." costs tokens, produces zero behavior change. The research is clear: prose paragraphs *"reliably get ignored."* [blakecrosley.com/blog/agents-md-patterns]
2. **Duplicating what's in `package.json` / `pyproject.toml`**. The agent reads those. *"Context files generated by /init commands are doing little more than pre-caching information the agent would discover on its own."* [developer.upsun.com/posts/ai/agents-md-less-is-more] If it's already there, leave it out.
3. **Ambiguous directives**: "be careful with concurrency", "write good code", "follow best practices". These are observably ignored. [blakecrosley.com/blog/agents-md-patterns]
4. **Contradictory rules across user + project + ancestor**. Two CLAUDE.md files in the directory chain saying different things — Claude picks arbitrarily. Audit with `/memory`. [code.claude.com/docs/en/memory]
5. **TODO list inside conventions**. The file is *what the agent reads every session*, not your roadmap. TODOs cost tokens and the agent treats them as background noise.
6. **Pinning before stabilising**. Greenfield: write 2–4 modules first, then capture the choices.
7. **Using conventions as enforcement**. If a rule MUST hold, write a hook/precommit/CI. Conventions degrade gracefully; enforcement doesn't.
8. **Letting the file pass 200 lines unsplit**. Adherence drops, distraction rises. Glob-scope or trim.
9. **One file per micro-rule** (the opposite extreme). 30 files in `.cursor/rules/` each with one bullet is a different kind of bloat. Group by topic; aim for 3–8 files if you split, not 30.
10. **Forgetting to load the file**. Aider users: not adding `--read CONVENTIONS.md` to `.aider.conf.yml` means new shells silently lose it. Cursor: not setting `alwaysApply: true` means the rule sits inert. Always verify load with the tool's introspection (`/tokens`, `/memory`, sidebar).

### Hard boundaries (what CONVENTIONS.md cannot do)

- **Cannot guarantee compliance.** It's context, not config. Use lint/hooks for guarantees.
- **Cannot cross repositories.** A repo-local conventions file is local. User-level (`~/.claude/CLAUDE.md`) helps for personal prefs but is not shared.
- **Cannot replace code review.** The agent's adherence is probabilistic. Review catches what conventions miss.
- **Cannot store secrets / paths to private things.** CONVENTIONS.md is committed to the repo. Use `CLAUDE.local.md` (Claude Code, gitignored) or env files for personal paths.

---

## 7. 跨框架对照 (Cross-Tool Comparison)

| | Aider | Claude Code | Cursor | Cline | CrewAI |
|---|---|---|---|---|---|
| Canonical filename | `CONVENTIONS.md` (any name; convention by community) | `CLAUDE.md`, `CLAUDE.local.md` | `.cursor/rules/*.mdc` (legacy: `.cursorrules`) | `.clinerules/*.md` (and `memory-bank/`) | `Agent.backstory` field (in code, not a file) |
| Location convention | Repo root | `./` or `./.claude/`, plus ancestors auto-walked | `.cursor/rules/` (nested dirs supported) | `.clinerules/` directory | Agent constructor, not filesystem |
| Load mechanic | Explicit `--read CONVENTIONS.md` (or in `.aider.conf.yml`) [aider.chat/docs/usage/conventions.html] | Automatic ancestor-walk; subdirectory files load on-demand [code.claude.com/docs/en/memory] | Auto-attach by `alwaysApply: true` or `globs:` frontmatter [cursor.com/docs/rules] | All `.md`/`.txt` in `.clinerules/` concatenated automatically [docs.cline.bot/customization/cline-rules] | Embedded into agent prompt at instantiation [docs.crewai.com/en/concepts/agents] |
| Multi-file support | Multiple `--read` flags; or list in YAML config | Native — `.claude/rules/*.md` with optional `paths:` frontmatter | Native — multiple `.mdc` files; nested `.cursor/rules/` in subdirs | Native — all files in folder, numeric prefix for ordering | None — re-instantiate agents |
| Scope control | Global to the session | Ancestor-walk + path-scoped rules via `paths:` frontmatter | `globs:` frontmatter, nested dirs, `alwaysApply` toggle | YAML frontmatter with `paths` glob | Per-agent |
| Read/write boundary | Read-only (cannot be edited by agent) [aider.chat/docs/usage/conventions.html] | Loaded as user message, treated as context | Loaded as rule (system-prompt-ish) | Loaded into rules section of system prompt | Part of agent's persona |
| Personal vs team layer | Team commits `CONVENTIONS.md`; no per-user layer | `CLAUDE.md` (team) + `CLAUDE.local.md` (personal, gitignored) + `~/.claude/CLAUDE.md` (user-global) + managed policy | `.cursor/rules/` (team) + user rules in settings | `.clinerules/` (workspace) + global rules; workspace wins on conflict [docs.cline.bot/customization/cline-rules] | Code-level; no built-in personal layer |
| Hard size budget | 25k-token total-context threshold (whole context, not just rules) [aider.chat/docs/troubleshooting/edit-errors.html] | < 200 lines per CLAUDE.md recommended; full file loaded regardless [code.claude.com/docs/en/memory] | < 500 lines per `.mdc` rule; always-apply rules trimmed aggressively [cursor.com/docs/rules] | Concatenated total; same context-pressure rules apply | Limited by LLM context; backstory is part of system prompt |
| Conflict precedence | None built-in; later `--read` wins by recency | managed > user > project > local; later files in walk override earlier | Always-apply > globs-matched > manually attached | workspace > global on conflict [docs.cline.bot/customization/cline-rules] | Per-agent only |
| Cross-tool import | `--read AGENTS.md` works | `@AGENTS.md` import syntax [code.claude.com/docs/en/memory] | Must duplicate (or generate from a build step) | Plain markdown, can symlink to `AGENTS.md` | Read external file in Python at construction time |
| Verifiable load check | `/tokens` (in-session) | `/memory` lists all loaded files | Sidebar shows active rules | Sidebar shows loaded rules | Inspect agent object in code |

### What's idiosyncratic to each tool

- **Aider** is the only tool requiring **explicit load**. This is also its strength — the load is unambiguous and the cache hits are documented.
- **Claude Code** is the only one with **ancestor-walk** and a **personal-vs-team file split** in the same directory. CLAUDE.local.md is uniquely useful for personal sandbox URLs / test data that shouldn't be committed.
- **Cursor** standardized on **glob-scoped `.mdc` files**. The legacy `.cursorrules` (single file) is deprecated; you migrate piece by piece. [cursor.com/docs/rules]
- **Cline** uniquely combines **`.clinerules/` (style/preferences) with `memory-bank/` (mutable working memory)**. Memory bank is read at the start of every task — *"this is not optional"* — and includes `projectBrief.md`, `activeContext.md`, `progress.md`. [docs.cline.bot/customization/cline-rules] This is a different mechanism than conventions; do not conflate them.
- **CrewAI** is the outlier — style lives in code (`backstory=` argument), not on the filesystem. This means style is per-agent (not per-project) and cannot be edited by non-engineers. Trade-off: more programmatic control, less convenient for teams.

### When to use which mechanism if you have a choice

| Need | Best fit |
|---|---|
| One small project, one tool, simple rules | Single-file `CONVENTIONS.md` (Aider) or `CLAUDE.md` (Claude Code) |
| Monorepo with per-language conventions | Glob-scoped: Claude Code `.claude/rules/` with `paths:` or Cursor `.mdc` with `globs:` |
| Personal preferences across all projects | `~/.claude/CLAUDE.md` (Claude Code) or `~/.claude/rules/` |
| Multiple coder-tools on one repo | `AGENTS.md` canonical, others import/symlink |
| Style is part of an agent's identity (multi-agent system) | CrewAI `backstory=` |
| Working memory that the agent updates as it goes | Cline `memory-bank/` (none of the others has a clean equivalent) |

---

## References

### Primary (Aider — the `--read CONVENTIONS.md` pattern)
- [aider.chat/docs/usage/conventions.html] — the canonical CONVENTIONS.md doc, including the httpx-vs-requests A/B example
- [aider.chat/docs/troubleshooting/edit-errors.html] — 25k-token distraction threshold
- [aider.chat/docs/usage/commands.html] — `/read`, `/tokens`, `/clear`

### Primary (Claude Code — CLAUDE.md auto-load + rules dir)
- [code.claude.com/docs/en/memory] — full CLAUDE.md spec: locations, ancestor-walk, `@`-imports, `.claude/rules/` with `paths:` frontmatter, 200-line guideline, AGENTS.md interop, /init reading of `.cursorrules`

### Primary (Cursor — `.cursor/rules/` migration)
- [cursor.com/docs/rules] — `.mdc` format, frontmatter, alwaysApply, globs
- [vibecodingacademy.ai/blog/cursor-rules-complete-guide] — 2026 best practices, < 500 lines per rule
- [forum.cursor.com/t/best-practices-cursorrules/41775] — community-curated patterns

### Primary (Cline — `.clinerules/` + memory-bank)
- [docs.cline.bot/customization/cline-rules] — folder structure, workspace-vs-global precedence, YAML `paths` frontmatter for conditional rules
- [github.com/cline/prompts/blob/main/.clinerules/memory-bank.md] — the memory-bank pattern

### Primary (CrewAI — backstory as style)
- [docs.crewai.com/en/concepts/agents] — `role + goal + backstory` triplet, backstory as primary style lever

### Research on context-file bloat
- [developer.upsun.com/posts/ai/agents-md-less-is-more] — context files can *hurt* if they duplicate already-discoverable info; +20% inference cost shown
- [blakecrosley.com/blog/agents-md-patterns] — what actually changes agent behavior (command-first, verifiable, closure-defined) vs what gets ignored (prose, ambiguity)
- [hyperdev.matsuoka.com/p/why-your-ai-agents-need-contextual] — the case FOR conventions when the info isn't already in the repo

### Cross-tool ecosystem
- [github.com/Aider-AI/conventions] — community conventions repository
- [github.com/PatrickJS/awesome-cursorrules] — `.cursorrules` template gallery
- [github.com/cline/prompts] — official Cline rules patterns

### Adjacent skills in this workspace
- `/Users/5imp1ex/Desktop/Skill-Workplace/output/aider-sop-skill/SKILL.md` §2.2, §3 Phase 1, §6 anti-pattern #7
- `/Users/5imp1ex/Desktop/Skill-Workplace/output/crewai-sop-skill/SKILL.md` §2.2 (backstory as style lever)
- `/Users/5imp1ex/Desktop/Skill-Workplace/output/dify-sop-skill/SKILL.md` (system-prompt patterns in visual workflows)
