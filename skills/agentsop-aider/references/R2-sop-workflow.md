# R2: Aider SOP Workflow

## The canonical loop

```
git status clean? --> launch aider --> /ask plan --> /add files --> /code edit --> review diff --> auto-commit --> /test --> /undo or continue
                                            ^                                                                                 |
                                            +---------------------- /clear when topic shifts ---------------------------------+
```

## Phase 1 — Bootstrap

### Pre-flight checks (do this every session)
1. `cd` into the repo root. Aider expects a git repo. If none, `git init` first or pass `--no-git` (loses safety story).
2. Commit any in-flight work or stash it. Aider will auto-commit dirty files but you want a clean baseline.
3. Pick the model. `aider --model <name>` or set in `.aider.conf.yml`. Top-tier today: `gpt-5`, `claude-3.7-sonnet`, `o3-pro`, `gemini-2.5-pro` [aider.chat/docs/leaderboards/].
4. Optional: `--read CONVENTIONS.md` to pin coding style.

### Launch patterns

| Pattern | Command | When |
|---|---|---|
| Empty session, let LLM navigate via repo-map | `aider` | Exploratory; small/medium repo |
| Pre-add known target files | `aider src/auth.py tests/test_auth.py` | You already know the scope |
| Architect+editor split | `aider --architect --model o1 --editor-model gpt-4o` | Hard reasoning + cheap precise edits |
| Large repo subset | `aider --subtree-only` (from a subdirectory) | Monorepo [aider.chat/docs/faq.html] |
| Read-only convention file | `aider --read CONVENTIONS.md` | Persistent style guide [aider.chat/docs/usage/conventions.html] |
| Auto-test loop | `aider --test-cmd "pytest" --auto-test` | Test-driven refactor [aider.chat/docs/usage/lint-test.html] |

## Phase 2 — Scope (the `/add` discipline)

> "Just add the files you think need to be edited" … "Adding a bunch of files that are mostly irrelevant to the task at hand will often distract or confuse the LLM." [aider.chat/docs/usage/tips.html, aider.chat/docs/faq.html]

**Rule of thumb**: keep added files under 25k tokens.

> "Above about 25k tokens of context, most models start to become distracted." [aider.chat/docs/troubleshooting/edit-errors.html]

**Decision tree for scope**:
```
Do you know which files to change?
  yes -> /add those files (only those)
  no  -> /ask "which files implement X?"   (LLM uses repo-map to answer)
         /add the files it names
```

`/read <file>` for files that should provide context but NOT be edited (configs, schemas, conventions).
`/drop <file>` aggressively when a file is no longer in scope — context space is precious.

## Phase 3 — Discuss before editing (`/ask` then `/code`)

> "Use ask mode to discuss what you want to do, get suggestions or options from aider and provide feedback on the approach. Once aider understands the mission, switch to code mode to have it start editing your files." [aider.chat/docs/usage/modes.html]

Aider's recommended workflow:

1. `/ask How is auth currently handled? What would break if I switched to JWT?`
2. Critique, refine, agree on plan.
3. `/code Implement the JWT switch we discussed.` (or simply remove the `/ask` prefix and say "go ahead")
4. Review the proposed diff.
5. Accept (auto-commit) or `/undo`.

For multi-step work: **"Break your goal down into bite sized steps. Do them one at a time."** [aider.chat/docs/usage/tips.html]

## Phase 4 — Architect mode (when reasoning > editing)

Use when the model that reasons best is not the model that edits best. Example pairings from the benchmark:

| Architect | Editor | Pass@2 | Note |
|---|---|---|---|
| o1-preview | o1-mini | 85% | "SOTA significantly above the previous best" [aider.chat/2024/09/26/architect.html] |
| o1-preview | Sonnet | 82.7% | "An entirely practical configuration" |
| Claude 3.5 Sonnet | Sonnet | 80.5% | Up from 77.4% solo |
| GPT-4o | GPT-4o | 75.2% | Up from 71.4% solo |

> "Especially useful with OpenAI's o1 models, which are strong at reasoning but less capable at editing files." [aider.chat/docs/usage/modes.html]

Activation: `--architect` flag, or `/architect` in-chat. Aider will set `--editor-edit-format` to `editor-diff` / `editor-whole` automatically.

Caveat: o1-preview + DeepSeek with `whole` format is "quite slow, so probably not practical for interactive use." [aider.chat/2024/09/26/architect.html] Use Sonnet as the editor for interactive sessions.

## Phase 5 — Verification (lint, test, run)

> "Aider will try and fix any errors if the command returns a non-zero exit code." [aider.chat/docs/usage/lint-test.html]

| Command | Purpose | Auto variant |
|---|---|---|
| `/lint` | Run lint on edited files | `--auto-lint` (on by default) |
| `/test <cmd>` | Run tests; non-zero exit feeds output back to LLM | `--test-cmd X --auto-test` |
| `/run <cmd>` | Run anything; optionally attach output | `!<cmd>` alias |
| `/diff` | Show diff since last message | manual |

Pair-program rhythm: edit -> auto-lint -> auto-test. If tests fail, Aider sees the failure and proposes a fix.

## Phase 6 — Context hygiene

When the conversation drifts or token usage balloons:

| Symptom | Action |
|---|---|
| Token count above ~25k | `/drop` files no longer relevant, `/tokens` to confirm |
| Topic shifted | `/clear` (keeps files, clears chat) |
| Want fresh start | `/reset` (drops files AND clears chat) |
| Model edits wrong file | check it's `/add`-ed (LLM can only edit added files); inspect `/ls` |
| Edit format errors recurring | switch model, or `--edit-format whole` [aider.chat/docs/troubleshooting/edit-errors.html] |

## Phase 7 — Wrap-up

- `git log --oneline` to see the session's commits.
- Squash if you want a single feature commit: `git rebase -i HEAD~N`.
- Open PR with aider commits intact — commit messages are conventional-commits style.

## Key in-chat commands cheat-sheet

> Source: [aider.chat/docs/usage/commands.html]

```
/add <files>       add files to chat (LLM may edit)
/read <file>       add as read-only (LLM may NOT edit)
/drop <files>      remove from chat
/ls                list files known and in-chat
/ask <question>    discuss without editing
/code <request>    edit (or just type)
/architect <req>   architect+editor mode
/model <name>      switch main model
/clear             clear chat history (keep files)
/reset             drop files AND clear chat
/tokens            show token usage
/map               print current repo-map
/diff              diff since last message
/undo              revert last aider commit
/commit            commit out-of-chat changes
/run <cmd>         shell; optionally attach output (alias: !)
/test <cmd>        run test; attach output on failure
/web <url>         scrape page into chat
/copy              copy last assistant message
/help <q>          ask about aider itself
```

## Configuration files

- `.aider.conf.yml` — persistent CLI defaults (model, edit-format, read files).
- `.aiderignore` — exclude paths from repo-map (similar to `.gitignore`).
- `CONVENTIONS.md` (or any name) — load with `--read` for style guides.

## References

- [aider.chat/docs/usage.html]
- [aider.chat/docs/usage/tips.html]
- [aider.chat/docs/usage/modes.html]
- [aider.chat/docs/usage/commands.html]
- [aider.chat/docs/usage/conventions.html]
- [aider.chat/docs/usage/lint-test.html]
- [aider.chat/docs/troubleshooting/edit-errors.html]
- [aider.chat/2024/09/26/architect.html]
- [aider.chat/docs/leaderboards/]
