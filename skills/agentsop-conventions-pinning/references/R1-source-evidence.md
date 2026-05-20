# R1 — Source evidence for the conventions-pinning skill

Verbatim quotes from primary sources, organised by the claim they support.

---

## Claim 1: Aider's CONVENTIONS.md is loaded read-only via `--read`

Source: [aider.chat/docs/usage/conventions.html]

> "Sometimes you want GPT to be aware of certain coding guidelines, like whether to provide type hints, which libraries or packages to prefer, etc."

> "It's best to load the conventions file with `/read CONVENTIONS.md` or `aider --read CONVENTIONS.md`. This way it is marked as read-only, and cached if prompt caching is enabled."

Example given in the docs:
- Conventions: "Prefer httpx over requests for making HTTP requests" + "Use types everywhere possible"
- A/B result: with conventions → `httpx` + type hints; without → `requests` + no types

Persistent config form in `.aider.conf.yml`:
```yaml
read: CONVENTIONS.md
# or multiple
read: [CONVENTIONS.md, anotherfile.txt]
```

Community repository: [github.com/Aider-AI/conventions]

---

## Claim 2: Aider's 25k-token distraction threshold

Source: [aider.chat/docs/troubleshooting/edit-errors.html]

> "Above about 25k tokens of context, most models start to become distracted."

Implication for conventions: the conventions file competes for that budget with actual code. A large conventions file is self-defeating.

---

## Claim 3: Claude Code's CLAUDE.md auto-loads from cwd up the ancestor chain

Source: [code.claude.com/docs/en/memory]

> "Claude Code reads CLAUDE.md files by walking up the directory tree from your current working directory, checking each directory along the way for `CLAUDE.md` and `CLAUDE.local.md` files."

> "All discovered files are concatenated into context rather than overriding each other. Across the directory tree, content is ordered from the filesystem root down to your working directory."

Location precedence (from broadest to most specific):
- Managed policy: `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS), `/etc/claude-code/CLAUDE.md` (Linux/WSL), `C:\Program Files\ClaudeCode\CLAUDE.md` (Windows)
- User: `~/.claude/CLAUDE.md`
- Project: `./CLAUDE.md` or `./.claude/CLAUDE.md`
- Local (gitignored): `./CLAUDE.local.md`

Subdirectory CLAUDE.md files: load on demand when Claude reads files in those directories (not at session start).

---

## Claim 4: Claude Code recommends < 200 lines per CLAUDE.md

Source: [code.claude.com/docs/en/memory]

> "Size: target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."

Plus the structural guidance:

> "Use markdown headers and bullets to group related instructions. Claude scans structure the same way readers do."

> "Specificity: write instructions that are concrete enough to verify. For example: 'Use 2-space indentation' instead of 'Format code properly'."

---

## Claim 5: CLAUDE.md is context, not enforcement

Source: [code.claude.com/docs/en/memory]

> "CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer."

> "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself. Claude reads it and tries to follow it, but there's no guarantee of strict compliance, especially for vague or conflicting instructions."

Adherence remediation:
> "If the instruction is something that must run at a specific point, such as before every commit or after each file edit, write it as a hook instead. Hooks execute as shell commands at fixed lifecycle events and apply regardless of what Claude decides to do."

---

## Claim 6: Conflicting rules cause arbitrary picks

Source: [code.claude.com/docs/en/memory]

> "Consistency: if two rules contradict each other, Claude may pick one arbitrarily. Review your CLAUDE.md files, nested CLAUDE.md files in subdirectories, and `.claude/rules/` periodically to remove outdated or conflicting instructions."

---

## Claim 7: When to add to CLAUDE.md

Source: [code.claude.com/docs/en/memory]

> "Treat CLAUDE.md as the place you write down what you'd otherwise re-explain. Add to it when:
> - Claude makes the same mistake a second time
> - A code review catches something Claude should have known about this codebase
> - You type the same correction or clarification into chat that you typed last session
> - A new teammate would need the same context to be productive"

---

## Claim 8: Claude Code reads AGENTS.md, .cursorrules, .windsurfrules at /init

Source: [code.claude.com/docs/en/memory]

> "Running `/init` in a repo that already has an `AGENTS.md` reads it and incorporates the relevant parts into the generated `CLAUDE.md`. It also reads other tool configs like `.cursorrules` and `.windsurfrules`."

Cross-tool import syntax:
> "Claude Code reads CLAUDE.md, not AGENTS.md. If your repository already uses AGENTS.md for other coding agents, create a CLAUDE.md that imports it so both tools read the same instructions without duplicating them."

```markdown
@AGENTS.md

## Claude Code
Use plan mode for changes under `src/billing/`.
```

---

## Claim 9: Cursor migrated from .cursorrules to .cursor/rules/

Source: [cursor.com/docs/rules], [vibecodingacademy.ai/blog/cursor-rules-complete-guide]

> "The `.cursorrules` file in your project root is still supported but will be deprecated, and Cursor recommends migrating to Project Rules for more control, flexibility, and visibility."

> "A single `.cursorrules` file has no scope control—every rule loads for every conversation regardless of relevance, which is wasteful on context tokens and makes rules harder to maintain as projects grow."

Migration is incremental: keep `.cursorrules` alongside `.cursor/rules/*.mdc` until full migration.

---

## Claim 10: Cursor 500-line per-rule recommendation

Source: [vibecodingacademy.ai/blog/cursor-rules-complete-guide], [cursor.com/docs/rules]

> "Keep rules concise: under 500 lines. Always-apply rules can kill context window—if Cursor feels slow or you're hitting context limits, look at your always-apply rules first; a 1,000-word always-apply rule is expensive, so trim aggressively or convert it to auto-attached with appropriate globs."

Nested rules:
> "Nested rules automatically attach when files in their directory are referenced. You can organize rules by placing them in `.cursor/rules` directories throughout your project, with subdirectories able to include their own `.cursor/rules` directory scoped to that folder."

---

## Claim 11: Cline's .clinerules/ is a folder of concatenated rule files

Source: [docs.cline.bot/customization/cline-rules]

> "The .clinerules folder is located at your project root and Cline processes all .md and .txt files inside it, combining them into a unified set of rules."

> "A typical workspace organization includes files like coding.md for coding standards, testing.md for test requirements, and architecture.md for structural decisions. Numeric prefixes (like 01-coding.md) help organize files but are optional."

> "When both workspace and global rules exist, Cline combines them, with workspace rules taking precedence when they conflict with global rules."

Conditional rules via YAML frontmatter:
> "You can add YAML frontmatter to the top of any rule file with path conditions using glob patterns, where paths is the currently supported conditional that takes an array of glob patterns to control when rules activate."

---

## Claim 12: Cline's memory-bank is separate from .clinerules

Source: [docs.cline.bot/customization/cline-rules], [github.com/cline/prompts/blob/main/.clinerules/memory-bank.md]

> "The Memory Bank is located in a folder called 'memory-bank', and you should create it if it does not already exist. Cline MUST read ALL memory bank files at the start of EVERY task — this is not optional."

> "The Memory Bank consists of core files and optional context files, all in Markdown format, with files building upon each other in a clear hierarchy starting from projectBrief.md to context files to activeContext.md and progress.md."

Note: memory-bank is mutable working memory the agent updates as it goes; .clinerules are stable style/preference rules. These are different mechanisms and should not be conflated.

---

## Claim 13: CrewAI uses backstory as the primary style lever

Source: [docs.crewai.com/en/concepts/agents]

Agent has three style-bearing fields:
- **role**: functional identity ("Senior Data Researcher") — sets prompt subject
- **goal**: individual objective ("Uncover cutting-edge developments in {topic}") — directs decisions
- **backstory**: experience/character — calibrates tone and judgment

> "Backstory provides depth to the agent's persona, enriching its motivations and engagements within the crew."

Key insight (from the crewai-sop-skill in this workspace):
> "Backstory is not decoration. It is the largest lever on system prompt — same role+goal, different backstory will significantly change output quality and style."

---

## Claim 14: Context files can hurt when they duplicate already-discoverable info

Source: [developer.upsun.com/posts/ai/agents-md-less-is-more] (citing arxiv research on AGENTS.md effectiveness)

> "Context files tend to reduce task success rates compared to providing no repository context, while also increasing inference cost by over 20%. This suggests that bloated context is actually harmful."

> "When researchers removed all documentation files (.md files, the docs/ folder, example code) from repositories, LLM-generated context files suddenly became helpful. So context files generated by /init commands are doing little more than pre-caching information the agent would discover on its own. For well-documented repositories, that pre-caching adds cost and constraints without adding value."

> "Developer-written context files performed better for exactly the reason you'd guess: they contained information that wasn't already in the repository — tooling preferences, workflow requirements, conventions that existed in developers' heads but not in any documentation."

---

## Claim 15: What makes context files effective (and what doesn't)

Source: [blakecrosley.com/blog/agents-md-patterns]

Effective patterns:
- Command-first (exact invocations, not descriptions)
- Task-organized (coding, review, release sections)
- Closure-defined (explicit "done" criteria)

Anti-patterns that reliably get ignored:
- Prose paragraphs
- Ambiguous directives ("be careful")
- Contradictory priorities

---

## Claim 16: Sources of pre-built convention templates

- [github.com/Aider-AI/conventions] — Aider community conventions
- [github.com/PatrickJS/awesome-cursorrules] — awesome-cursorrules gallery
- [github.com/cline/prompts] — official Cline rules

These are useful as starting points but every line should pass the "is this in our repo already?" test before being copied.
