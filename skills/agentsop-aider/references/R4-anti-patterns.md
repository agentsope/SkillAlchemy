# R4: Anti-Patterns & Boundaries

## When NOT to use Aider

### 1. Greenfield projects with no codebase yet
Aider's edge — repo-map, git-aware editing — assumes existing code. For "build me a new project from scratch" the repo-map is empty and the safety guarantees (per-edit commit on top of a known baseline) provide no marginal value. Cursor / a chat-only LLM / a scaffolder is fine.

### 2. Cross-cutting refactors over thousands of files
Aider works "one chat session" at a time, and the **25k-token sweet spot** for added files is real:

> "Above about 25k tokens of context, most models start to become distracted." [aider.chat/docs/troubleshooting/edit-errors.html]

For a rename-this-symbol-in-2000-files refactor, use `sed`/AST tools/IDE refactor first, then bring Aider in to fix the residual semantic issues.

### 3. Non-git workflows
Aider can run with `--no-git` but you lose:
- per-edit auto-commit (the safety story)
- the dirty-file separation guarantee
- `/undo` as a one-shot rollback
- the commit log as audit trail

If git is not an option (binary asset workflow, Perforce-only shop), Aider is the wrong tool.

### 4. Tasks requiring browser/IDE awareness
Aider has no view of:
- IDE diagnostics (errors, type hints in your editor)
- Browser console / network traces
- Live debugger state
- Visual UI

You must feed these manually via `/run`, `/test`, or paste. If your workflow is heavily visual or IDE-driven, an in-IDE tool (Cline, Continue, Cursor) trades terminal-purity for those signals.

### 5. Autonomous "give me a PR" workflows
Aider is by design human-in-loop. The blog post explicitly contrasts this with SWE-Bench's autonomous setup:

> "Aider's interactive approach outperforming complex agentic systems... the pragmatic, user-controlled design was unexpectedly effective." [aider.chat/2024/05/22/swe-bench-lite.html]

For "read this issue, produce a PR, no human" workflows, OpenHands / Devin / Claude Code agents are designed for that mode. Aider can be scripted around (`--message`, `--yes`) but it's not its strength.

## Common mistakes (and the fix)

### Mistake 1: Adding too many files "to give context"

**Symptom**: Edit errors, hallucinated paths, slow responses, model picking wrong file.

**Fix**: `/drop` aggressively. Trust the repo-map. The data:
> "Aider successfully identified the correct file to edit in 70.3% of the benchmark tasks." [aider.chat/2024/05/22/swe-bench-lite.html]
The repo-map already shows the LLM what exists. `/add` only what you actually want to edit.

### Mistake 2: Ignoring the repo-map

**Symptom**: Model says "I don't have access to that file." You assume it's blind. You start `/add`-ing everything.

**Fix**: The repo-map is on by default. Run `/map` to see what the LLM already sees. If a relevant symbol shows up there, the LLM can ask for the file or you can `/ask` "where is X defined?" rather than dumping everything.

### Mistake 3: Using a weak model as editor in architect mode

**Symptom**: Architect produces a great plan; editor mangles the SEARCH/REPLACE.

**Fix**: The editor must be a competent **edit-format follower** even if it's a weaker reasoner. From the benchmark, "DeepSeek is surprisingly effective as an Editor model" [aider.chat/2024/09/26/architect.html] — Sonnet and GPT-4o are also strong editors. Never pair an o1-class architect with GPT-3.5-class editor.

### Mistake 4: Skipping `/clear` between unrelated tasks

**Symptom**: Performance degrades over a long session. Model "remembers" wrong things from earlier.

**Fix**: When the topic shifts, `/clear` to drop chat history (files stay). `/reset` for a clean slate (drops files too).

### Mistake 5: Disabling auto-commit "to keep history clean"

**Symptom**: You hit `/undo`, nothing happens — there's no commit to undo. Or you lose work because you forgot what changed.

**Fix**: Leave auto-commit on. **Squash later** with `git rebase -i HEAD~N` before opening a PR. The intermediate commits are your undo stack; squashing destroys it but you don't pay until the work is done.

### Mistake 6: Wrapping code edits in JSON tool-calls

**Symptom**: Building an agent harness; choosing structured tool-calls because "they're more reliable."

**Fix**: For code specifically, plain-text diff outperforms JSON. From Aider's own benchmark: "All of the models did worse on the benchmark when asked to return code in a structured JSON response." [aider.chat/2024/08/14/code-in-json.html]

### Mistake 7: Treating CONVENTIONS.md as optional

**Symptom**: Model keeps using `requests` when you want `httpx`; keeps omitting type hints; keeps changing import order.

**Fix**: `--read CONVENTIONS.md`. Aider's own example:
> "With CONVENTIONS.md: Claude used httpx with type hints. Without conventions: Claude used requests without type annotations." [aider.chat/docs/usage/conventions.html]
This single file persists style decisions across sessions.

### Mistake 8: Letting auto-lint surprise you with format-on-save loops

**Symptom**: Lint command rewrites files on every run; Aider thinks it's an error.

**Fix**: "Wrap them in a shell script that runs twice — the first pass reformats, the second verifies no actual errors exist." [aider.chat/docs/usage/lint-test.html]

## Hard boundaries (what Aider intentionally doesn't do)

| Boundary | Why |
|---|---|
| No IDE rendering | Stays terminal-pure; can pipe with tmux + editor |
| No vector embedding index | Avoids index staleness; repo-map is regenerated on demand |
| No autonomous loop by default | Keeps human in the loop, which Paul argues is the productivity win |
| No multi-repo session | One git repo per session; cross-repo work needs orchestration above Aider |
| No persistent memory across sessions | Each session starts fresh; persistence is via CONVENTIONS.md, .aider.conf.yml, and git history |

## References

- [aider.chat/docs/troubleshooting/edit-errors.html]
- [aider.chat/docs/troubleshooting/token-limits.html]
- [aider.chat/docs/usage/tips.html]
- [aider.chat/docs/usage/conventions.html]
- [aider.chat/docs/usage/lint-test.html]
- [aider.chat/docs/faq.html]
- [aider.chat/2024/05/22/swe-bench-lite.html]
- [aider.chat/2024/09/26/architect.html]
- [aider.chat/2024/08/14/code-in-json.html]
