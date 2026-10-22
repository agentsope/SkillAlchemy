# R2: Claude Code SOP Workflow

Seven steps, each with a verifiable output. Execute in order; jump back to an earlier step when a later one fails.

## Step 1 — Establish context

- Check for `CLAUDE.md`. If absent and the task is non-trivial, run `/init` or describe the project structure in a few lines.
- Map the tree with Glob instead of guessing where files live.

**Output:** you can state the project layout and the task's goal in one sentence.

## Step 2 — Locate before reading

- Grep for a keyword / Glob for a filename to get a concrete `file:line`.
- Read with `offset`/`limit` to pull only the relevant region.

**Output:** you know exactly which files and which lines are in scope.

## Step 3 — Decompose into verifiable steps

- Split a large task into 2–5 steps, each with a done-criterion: test passes, command exits 0, error message gone.

**Output:** a short list of steps, each independently checkable.

## Step 4 — Edit minimally, match surrounding style

- Use Edit for the smallest diff; mirror the surrounding naming, comment density, and idiom.
- Read the target region first when unsure.

**Output:** a minimal, style-consistent diff.

## Step 5 — Verify every change

- Run the targeted test or command after each edit.
- Report the real output; do not claim success without evidence.

**Output:** a passing test / command, or a real error fed back to the model.

## Step 6 — Context hygiene

- Topic switch or long history → `/clear`.
- Want to keep the thread but reduce volume → `/compact`.
- Move durable rules into `CLAUDE.md` instead of restating them.

**Output:** a session that is only carrying what the current task needs.

## Step 7 — Close out

- `git status` / `git diff` to confirm the scope is as intended.
- Commit and push only when the user asks; do not push unprompted.

**Output:** a reviewed, intended diff; nothing extra committed or pushed.

## Command cheat sheet

Run `/help` in-session for the authoritative current list. Core commands you will use:

| Command | Purpose |
|---|---|
| `/help` | List commands and usage |
| `/clear` | Clear conversation history (keeps files) |
| `/compact` | Compress the conversation, keeping the main thread |
| `/init` | Create/refresh a project `CLAUDE.md` |
| `/model` | Switch the active model |
| `/config` | Edit configuration and permissions |
| `/permissions` | Review/adjust permission rules |
| `/add-dir` | Add a working directory |

Skills are invoked by name (for example `/code-review`, `/security-review`, `/simplify`); the available set is listed in-session and can be extended with project or personal skills. CLI flags live in `claude --help`.
