# R3: Dilemma Cases

Grounded decision cases for the situations that most often stall a Claude Code session.

## Case 1 — "Did the model break anything?"

**Trigger:** the edit is done, but correctness is uncertain.

**Decision rule:**

1. `git diff` to see the actual change set.
2. Run the targeted test / command.
3. On failure, feed the real error back to the model; never let it guess blind.

## Case 2 — "The context is long and the model is getting forgetful"

**Trigger:** slow or truncated responses; the model drops earlier constraints.

**Decision rule (cheapest first):**

1. `/clear` — anything already written to code is safe to lose from chat.
2. Move still-needed rules into `CLAUDE.md`.
3. `/compact` to compress while keeping the thread.
4. Split into fresh sessions, one subtask each.

## Case 3 — "Do it inline, or spawn a subagent?"

**Trigger:** the task decomposes into independent parts.

**Decision rule:**

- Delegate only clearly independent, parallelizable subtasks (Agent).
- A handful of lookups is cheaper done inline — do not spawn agents just to appear parallel.
- Once delegated, wait for the result instead of redoing the work.

## Case 4 — "How do I read a multi-thousand-line file?"

**Trigger:** facing a very large file.

**Decision rule:**

- Grep to the symbol/region first, then Read with `offset`/`limit`.
- Full reads only when a whole-file understanding is genuinely required (use sparingly).

## Case 5 — "The model is running find/cat/grep in Bash"

**Trigger:** search/read happening through the shell.

**Decision rule:** redirect to Glob / Grep / Read — they surface in the permission UI and cite `file:line`.

## Case 6 — "What belongs in CLAUDE.md?"

**Trigger:** you find yourself repeating the same instruction.

**Decision rule:** if it is said more than once, persist it to `CLAUDE.md` and stop restating it in chat.
