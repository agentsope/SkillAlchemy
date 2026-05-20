---
name: agentsop-test-fix-loop
version: 0.1.0
description: |
  Decision protocol for wiring a verify-then-fix loop around a code-editing LLM
  agent. The agent edits → runs lint/test → reads the output → fixes → re-runs,
  bounded by an iteration cap and an escalation rule. Activates whenever a coder
  agent has a verifiable success criterion (exit code, type-checker output,
  failing assertion) and the user wants the agent to converge to "green" on its
  own. Framework-agnostic — wraps Aider's `--auto-lint`/`--auto-test`, an
  OpenHands SWE-Bench loop, a manual LangGraph cycle, or Claude Code's bash
  tool just the same.
domain: coder-agent / tool-result-feedback
audience: engineers wiring LLM agents that must converge on a verifiable spec
trigger_keywords:
  - "auto-lint"
  - "auto-test"
  - "test-fix loop"
  - "fix until tests pass"
  - "verify-then-fix"
  - "iterate until green"
  - "agent feedback loop"
  - "iteration cap"
when_to_use:
  - "any code-edit flow with a verifiable success command (pytest, ruff, mypy, eslint, tsc, go test, cargo check)"
  - "wrapping a coding agent so it doesn't return until lint+tests are clean"
  - "SWE-Bench-style runs (one issue → patch → tests → fix → submit)"
  - "CI guardrail where a PR must be green before the agent declares done"
when_not_to_use:
  - "the success criterion is subjective ('looks good') — there's no signal to feed back"
  - "the verifier takes >5 min and you need the agent interactive — async the loop"
  - "human review is the gate (use HITL skill instead)"
  - "edits are exploratory / WIP — the loop will fight the user's incomplete code"
---

# Test-Fix Loop · SOP

> One-liner: **The test result IS the next prompt.** Wiring the verifier is
> 20% of the work; framing its output as a useful feedback message is 80%.

---

## 1. 何时激活 (Activation Rules)

Activate this skill when **any** of the following triggers fire:

- The user says "have the agent fix until tests pass", "run lint and tests
  automatically", "iterate until green", or invokes `aider --auto-test`,
  `cline --yes`, or an OpenHands-style headless agent.
- The task has a **verifiable success command**: a non-zero exit code on
  failure (pytest, ruff, mypy, eslint, tsc, go test, cargo check, npm run
  build, make check, …).
- You're wrapping a code-editing LLM in a script/CI step and need to decide:
  *when does the agent return?*
- The agent just made an edit and the next message in the loop would be
  "here's what the verifier said".

**Do not activate** when:

- Success is **subjective** (writing prose, designing UX). The loop has no
  feedback signal worth replaying.
- The verifier is **slow + interactive** (full E2E suite, multi-min builds).
  Either async-ify the loop, or run a fast subset (`pytest -x -k changed`) in
  the loop and gate the slow suite at PR review.
- The gate is **human approval**, not a machine check — use the HITL skill.

---

## 2. 核心心智模型 (Core Mental Model)

### 2.1 The test result IS the next prompt

The agent's *next turn* is conditioned almost entirely on the message you
inject between edit-N and edit-N+1. That message — formatted from
`stdout`, `stderr`, `exit_code` — **is the prompt**. The framework labels it
"tool result" or "verifier output" but mechanically it is a user-role message
the LM consumes verbatim.

⇒ **Framing the feedback dominates the model choice.** A 4000-line raw pytest
dump prompts a worse fix than a 30-line "first failing test, traceback, the
diff you just applied" digest, *regardless of the model behind it*.

### 2.2 Four primitives

```
+-----------------+   +-----------------+   +-----------------+   +-----------------+
| 1. Verifier     |   | 2. Capture      |   | 3. Format       |   | 4. Iteration    |
|    command      |   |    (stdout +    |   |    feedback     |   |    bound        |
|                 |   |     stderr +    |   |    message      |   |                 |
| - pytest -x     |   |     exit_code)  |   | - first error   |   | - max N tries   |
| - ruff check    |   | - timeout cap   |   | - last K lines  |   | - escalate /    |
| - mypy --strict |   | - byte cap      |   | - drop noise    |   |   commit / skip |
| - eslint .      |   | - kill on hang  |   | - keep colors=0 |   |                 |
+-----------------+   +-----------------+   +-----------------+   +-----------------+
```

Drop any one of these and the loop fails:

- No verifier → no signal; the agent guesses "done".
- No capture → the model can't read stderr; tracebacks live in stderr.
- No formatting → 25k-token output distracts the model
  (see Aider's 25k context-drift threshold).
- No iteration bound → infinite loop; the OpenHands SWE-Bench infinite-loop
  bug `[oh/6357]` is the canonical failure case.

### 2.3 Why a separate skill (vs "just give the agent a bash tool")

Naively: "let the agent run `pytest` and read the output". This breaks because:

1. The agent doesn't know **which** command to run (project-specific).
2. The agent dumps the **full output** into context every iteration, blowing
   the 25k threshold by iter 3.
3. The agent has **no termination contract** — it'll keep trying after the
   test passes "to be safe", or keep trying after 30 failures "to be helpful".
4. The agent makes **edits with no audit trail** — if iter 4 was the right
   fix, you can't bisect because nothing is committed.

The loop is a contract: *verifier wiring + output capture + feedback framing
+ iteration cap + per-fix git commit*. Treat it as one operation, not five.

### 2.4 What "green" means

| Verifier returns | Interpretation | Next action |
|---|---|---|
| `exit 0`, no diagnostics | True success | Commit + exit loop |
| `exit 0`, warnings | Soft success | Commit + log; optionally surface to user |
| `exit != 0`, parseable error | Actionable failure | Format → feed back → next iter |
| `exit != 0`, unparseable (e.g. segfault, OOM) | Environment / infra failure | Escalate; do not re-prompt the LM |
| Timeout / hang | Likely infinite loop in code | Kill, format as timeout error, escalate after 1 retry |

---

## 3. SOP 工作流 (Agentic Protocol)

### Step 1 · Wire the verifier command

Pick the cheapest verifier that catches the class of bug you care about.
Cascade from fastest to slowest:

| Stage | Command (concrete) | Catches | Typical latency |
|---|---|---|---|
| 1. Format | `ruff format --check .` / `prettier --check .` | Style | <1 s |
| 2. Lint  | `ruff check .` / `eslint .` | Style + obvious bugs | 1–5 s |
| 3. Type  | `mypy --strict src/` / `tsc --noEmit` | Type errors | 5–30 s |
| 4. Test  | `pytest -x --ff` / `vitest run --bail 1` | Behavioural | 10 s–min |
| 5. Build | `cargo build` / `go build ./...` / `npm run build` | Link / compile | 10 s–min |

**Rule**: bind `--lint-cmd` and `--test-cmd` to **stages 1–4 combined into one
shell command** (`ruff check . && pytest -x`). This way one feedback message
covers all signals; you don't loop separately on lint then on tests.

For Aider:

```bash
aider --auto-lint --lint-cmd "ruff check ." \
      --auto-test --test-cmd "pytest -x --tb=short"
```

For Claude Code / generic agent:

```python
result = subprocess.run(
    ["bash", "-c", "ruff check . && pytest -x --tb=short"],
    capture_output=True, text=True, timeout=120
)
```

### Step 2 · Capture stdout + stderr + exit code (all three)

```python
result = subprocess.run(
    cmd, capture_output=True, text=True, timeout=120, env={**os.environ, "NO_COLOR": "1"}
)
captured = {
    "exit_code": result.returncode,
    "stdout": result.stdout,
    "stderr": result.stderr,
    "timed_out": False,
}
```

Common mistakes:

- Capturing only stdout — tracebacks in pytest go to **stdout**, but compiler
  errors in `tsc` / `cargo` go to **stderr**. Always capture both.
- Not setting `NO_COLOR=1` — ANSI escapes burn tokens and confuse the model.
- No timeout — a single infinite-loop unit test halts the whole agent.
- No byte cap — a 50MB `cargo build` log kills your context window.

### Step 3 · Format the feedback message (the load-bearing step)

The single biggest lever in this skill. **Don't paste raw output.** Distill to:

```
The verifier failed (exit 1, pytest -x --tb=short).

FIRST FAILING TEST:
tests/test_auth.py::test_jwt_expiry — AssertionError: expected 401, got 200

TRACEBACK (last frame):
  File "src/auth.py", line 47, in verify_token
    if exp < now: return None
  TypeError: '<' not supported between instances of 'NoneType' and 'datetime'

YOUR LAST EDIT touched src/auth.py:40-50.

Hypothesis: `exp` is None when the JWT lacks an `exp` claim. Either default
it or guard the comparison.
```

Formatting recipe:

1. **First error only.** If there are 12 failing tests, show the first.
   Subsequent ones often cascade from the first fix.
2. **Last frame of the traceback.** Earlier frames are usually framework noise.
3. **Anchor to the last edit.** "You just changed `src/auth.py:40-50`" makes
   the model attribute the failure correctly.
4. **Drop unchanged-between-iters noise** — pytest's collection summary,
   coverage totals, deprecation warnings.
5. **Hard byte cap**: target ≤ 2k tokens of feedback. If a single failure
   doesn't fit, truncate the traceback middle (keep top + bottom).
6. **No "please fix"** — the framing is enough. Imperative pleas degrade
   instruction-following in some models.

### Step 4 · Bound the iterations

Two limits, both required:

- **Hard cap** (`MAX_ITERS = 5` is a sane default; Aider uses ~3, OpenHands
  uses 50–100 for SWE-Bench).
- **Stall detector**: if the **same** error message appears twice in a row,
  break early — the model is stuck on the wrong hypothesis.

```python
seen_errors = []
for i in range(MAX_ITERS):
    edit = agent.propose_edit(feedback if i else initial_task)
    apply_edit(edit)
    git_commit(f"agent: iter {i+1}")           # always commit each iter
    verifier = run_verifier()
    if verifier["exit_code"] == 0:
        return Success(iters=i+1)
    feedback = format_feedback(verifier, last_edit=edit)
    if feedback in seen_errors[-1:]:           # exact repeat
        return Stall(reason="same error twice", last=feedback)
    seen_errors.append(feedback)
return Escalate(reason=f"exhausted {MAX_ITERS} iters", last=feedback)
```

### Step 5 · Per-iteration commit (the audit lever)

After every edit, before the verifier runs, commit with a structured message:

```
git commit -am "agent[iter 3/5]: tighten exp guard in verify_token"
```

Why mandatory:

- If iter 3 made it worse and iter 5 fixed it the "wrong" way, you can bisect
  with `git log --oneline | head -5`.
- The agent never overwrites its own previous attempt — each iter is recoverable.
- `git diff HEAD~1` gives the formatter a precise "what you just changed" anchor.

Aider's `--auto-commits` (on by default) does this. For non-Aider agents,
wrap the loop in commit logic yourself.

### Step 6 · Detect success precisely

| Signal | Good or false-positive? |
|---|---|
| `exit 0` from full verifier command | Good |
| `exit 0` but `stderr` contains "warning" | Soft success; surface to user, don't loop |
| `exit 0` because no tests collected (`pytest` returns 5) | **False positive** — check `pytest --collect-only` count |
| `exit 0` from a `\|\| true`-swallowed command | **False positive** — strip suppression from `--test-cmd` |
| `exit 0` but agent disabled / skipped tests to pass | **Critical** — diff for `pytest.skip`, `@pytest.mark.skip`, `xfail` added in last iter |

The agent disabling tests to "pass" is the most common pathological success.
Add a post-success diff check: `git log -p -1 | grep -E '(skip|xfail|@disable)'`.

### Step 7 · Escalate or commit on exit

When the loop exits without success:

1. **Surface the last formatted feedback** — that's the message the human
   needs to read, not the raw pytest log.
2. **Leave the WIP commits intact** — the user may want to inspect iter 3
   even if iter 5 failed.
3. **Tag the escalation reason**: `exhausted`, `stalled`, `env_failure`,
   `timeout`. The user's fix differs per cause.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger → Action → Output → Evidence**.

### OP-1 · Wire a one-shot verifier
- **Trigger**: User wants the agent to verify once after editing, no loop yet.
- **Action**: Run `<lint> && <type> && <test>` once, capture three-tuple
  `(stdout, stderr, exit_code)`.
- **Output**: Pass/fail signal. If fail, structured digest ready to feed back.
- **Evidence**: `[aider/lint-test]` "Aider will try and fix any errors if the
  command returns a non-zero exit code."

### OP-2 · Format raw verifier output into ≤2k-token feedback
- **Trigger**: Verifier failed; about to construct the next prompt.
- **Action**: Extract first failure, last traceback frame, anchor to changed
  file:lines from `git diff HEAD~1 --name-only -U0`. Strip ANSI, coverage,
  deprecation warnings. Hard byte cap.
- **Output**: A digest under 2k tokens with a hypothesis line.
- **Evidence**: `[aider/edit-errors]` "Above about 25k tokens of context,
  most models start to become distracted." Each iteration adds context; keep
  the per-iter delta tiny.

### OP-3 · Bound the loop
- **Trigger**: About to enter or continue a fix loop.
- **Action**: Set `MAX_ITERS` (3–5 interactive, 50–100 SWE-Bench), detect
  stall (same error twice = break), enforce total wall-clock cap.
- **Output**: A loop with explicit termination, never `while True`.
- **Evidence**: `[oh/6357]` OpenHands infinite-loop bug + `[langgraph/recursion]`
  "Hitting recursion_limit indicates an underlying design flaw" — same lesson.

### OP-4 · Commit per iteration
- **Trigger**: Agent has just applied an edit, before re-running verifier.
- **Action**: `git add -A && git commit -m "agent[iter N]: <one-line>"`.
  Never `--amend`.
- **Output**: A bisectable audit trail; iter K is always recoverable.
- **Evidence**: `[aider/git]` per-edit auto-commit; `[cline/auto-approve]`
  Cline mirrors the same "edit→commit→test" rhythm.

### OP-5 · Detect success without false positives
- **Trigger**: Verifier exits 0.
- **Action**: Confirm (a) tests were actually collected (`pytest` exit 5 ≠
  success), (b) no test was newly skipped/xfailed in the last commit, (c) no
  `|| true` suppression in the verifier command itself.
- **Output**: Trusted "green" signal.
- **Evidence**: pytest exit-code spec; `[aider/lint-test]` formatter wrapper
  caveat (auto-formatters that rewrite + return non-zero need double-run).

### OP-6 · Handle environment failure (escalate, don't re-prompt)
- **Trigger**: Verifier output indicates infra issue — `ImportError`,
  `command not found`, `OOM`, network 503, `ConnectionRefused` to test DB.
- **Action**: Do **not** feed the error back as a code-fix prompt. Surface
  to user with tag `env_failure`. The agent cannot fix `pytest: command not
  found` by editing source.
- **Output**: Loop exits; user is told to fix the environment.
- **Evidence**: SWE-Gym docs note: env failures from "missing system
  dependencies" must be solved at the harness level, not by the agent.

### OP-7 · Partial-success handling
- **Trigger**: 8 of 10 failing tests now pass; 2 remain.
- **Action**: Acknowledge progress in the feedback ("8 tests now pass; 2 still
  fail"), then format only the remaining 2. Reset stall detector — different
  error class = real progress.
- **Output**: Loop continues on the smaller error surface; model not whipped
  for the failures it just fixed.
- **Evidence**: Empirical: models given "you broke things" framing tend to
  revert good fixes. Anchor to **net delta**.

### OP-8 · Auto-formatter that rewrites + returns non-zero
- **Trigger**: `ruff format` or `prettier --write` modify files **and** return
  non-zero on first pass (means "I changed something").
- **Action**: Wrap in a two-pass script: pass 1 writes, pass 2 verifies.
  Treat only pass-2 exit code as the signal.
- **Output**: Loop doesn't get stuck re-running the same successful format.
- **Evidence**: `[aider/lint-test]` explicit guidance on formatter wrappers.

---

## 5. 困境决策案例 (Dilemma Cases)

### Case 1 · "Pytest output is 4000 lines — the agent fixes the wrong test"
- **困境**: A failing pytest run dumps 4k lines (12 failures, collection
  warnings, deprecation notices, full tracebacks each). The agent reads the
  *last* traceback (most recent in the output) and tries to fix that, but
  the *first* failure was the root cause; the others cascade from it. Three
  iterations later the agent has touched 5 files and broken more tests.
- **约束**:
  - Cannot truncate to first-error-only naively — some failures are
    independent (parallel test runners surface them in arbitrary order).
  - The user wants to see *all* failures in the final report, even if the
    agent only iterates on one.
- **决策步骤**:
  1. Run with `pytest -x` (`--exitfirst`) so the test runner itself stops at
     the first failure. The output is naturally bounded.
  2. If the project genuinely needs all failures listed for the user, run
     **twice**: once with `-x` for the agent loop, once with full output
     captured into a side-file for the human report. Don't conflate the
     two streams.
  3. In the formatted feedback, anchor to `git diff HEAD~1 --name-only`:
     "your last edit touched X; the first failure is in a test of Y." The
     anchor breaks the "fix the last thing I read" bias.
- **结果**: Bounded feedback, root-cause focused, full report preserved
  separately.
- **可提取的操作**: OP-2. **`-x` for the loop, full run for the human.**

### Case 2 · "The test fails because the dev container is missing libpq"
- **困境**: First iteration: `ImportError: No module named psycopg2`. The
  agent obediently rewrites `from psycopg2 import ...` to `import psycopg`,
  next iter: `No module named psycopg`. Iter 3: it removes the DB layer
  entirely. The loop has hit its cap; the codebase is now broken.
- **约束**:
  - The agent can't fix the *environment*; only the user can `apt-get install
    libpq-dev`.
  - The error syntactically looks like a code error (`ImportError`).
- **决策步骤**:
  1. Maintain a small classifier in the feedback formatter:
     ```python
     ENV_PATTERNS = [
       r"No module named",
       r"command not found",
       r"OSError: \[Errno 28\]",     # disk full
       r"ConnectionRefusedError",     # service down
       r"libpq.so",                   # missing system lib
     ]
     ```
     If a pattern matches **and** the file mentioned wasn't touched in the
     agent's edits, classify as `env_failure`.
  2. On `env_failure`: **don't** call `agent.propose_edit(...)`. Exit the
     loop immediately with a message to the user: "Verifier failed with
     what looks like an environment issue (`No module named psycopg2`). The
     agent has not edited files; please fix the environment and re-run."
  3. Allow one retry: env failures sometimes flake (network blip). Twice =
     escalate.
- **结果**: One iteration "wasted" on detection, then human-in-the-loop.
  The codebase is intact.
- **可提取的操作**: OP-6. **Pattern-match env errors before re-prompting the LM.**

### Case 3 · "Agent passes by adding `@pytest.mark.skip`"
- **困境**: Iter 4 returns `exit 0`. You celebrate. Then the user runs the
  tests themselves and discovers the failing test now has `@pytest.mark.skip`
  added by the agent. Technically green; pathologically wrong.
- **约束**:
  - You can't ban `skip` outright — there are legitimate skips.
  - The agent's reasoning ("the test was wrong, the implementation is right")
    may even be correct sometimes.
- **决策步骤**:
  1. Post-success diff check:
     ```bash
     git log -p $(git merge-base HEAD origin/main)..HEAD -- '*.py' \
       | grep -E '^\+.*(skip|xfail|@disabled|pass  # TODO)' && echo "POSSIBLE CHEAT"
     ```
  2. If matches found, **don't** auto-commit/exit. Surface to user:
     "Verifier passed but the agent added 2 `pytest.skip` annotations. Review
     the diff." Loop exit tag: `suspicious_pass`.
  3. Stronger version: pin the test file set with a pre-loop snapshot;
     after success, assert `tests_pre.count() == tests_post.count()`. Any
     reduction = cheat-suspect.
- **结果**: Pathological green caught at exit; user makes the call.
- **可提取的操作**: OP-5. **Success ≠ exit 0. Success = exit 0 AND no
  weakened tests.**

### Case 4 · "Same error two iterations in a row — push through or break?"
- **困境**: Iter 2 and iter 3 produce the identical `AssertionError`. The
  agent edited different lines each time but the error didn't change. You
  have 2 iters left in your budget. Push through, or break early?
- **约束**:
  - Iter budget is precious (LLM cost, wall clock).
  - Sometimes the third look at the same error *does* unlock the fix
    (different file edited, broader context).
- **决策步骤**:
  1. **Break on exact match**, not on similar match. If the error string
     is byte-identical to the previous iter, the model is genuinely stuck —
     break and escalate.
  2. **Continue on different file context**. If the error is the same but
     the agent's last `git diff` touched a different file, that's exploration;
     give it one more iter.
  3. **Always** include in the feedback: "This is the 3rd time you've seen
     this error. Previous attempts touched X and Y. Try a different
     hypothesis." Naming the loop pattern often breaks it.
- **结果**: Cheap stall detection without false-positive escalation.
- **可提取的操作**: OP-3. **Stall = exact-match repeat; surface the loop to
  the model itself.**

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Concrete don'ts

- **Don't dump raw verifier output.** A 4000-line pytest log past the 25k
  context threshold tanks model accuracy `[aider/edit-errors]`. Format first.
- **Don't loop without an iteration cap.** OpenHands' SWE-Bench infinite-loop
  bug `[oh/6357]` is the textbook case — even mature frameworks get this wrong.
- **Don't treat `exit 0` as ground truth.** Check for (a) tests actually ran,
  (b) no skips added this iter, (c) no `|| true` swallowed.
- **Don't `--amend` between iterations.** You lose the bisect trail. Each
  iter is its own commit.
- **Don't suppress stderr.** Tracebacks for `pytest` live in stdout; for
  `mypy`, `tsc`, `cargo` they live in stderr. You need both.
- **Don't re-prompt the LM with environment errors.** `ModuleNotFoundError`
  for a missing system lib will never be fixed by editing source. Classify
  and escalate.
- **Don't feed back "please fix this".** The error message *is* the prompt;
  imperatives add noise. Let the model infer the task from the failure.
- **Don't let the loop edit the test suite without asking.** If the agent's
  diff modifies `tests/`, surface for review — agents fix code by weakening
  tests more often than humans like to admit.
- **Don't run the slow suite in-loop.** Use `pytest -x -k <changed>` or
  `--testmon` for the loop; gate the full suite at PR time.

### Hard boundaries (this loop is the wrong tool when)

| Scenario | Use instead |
|---|---|
| Success is subjective (writing, UX, design) | Human-in-the-loop / pairwise eval |
| Verifier takes >5 min and you need interactive UX | Async/CI runner with a notification, not an in-loop wait |
| Multi-step verifier with branching (deploy → smoke → rollback) | A state graph (LangGraph) — the loop is not enough |
| You don't have git | Wrap in any other VCS or filesystem snapshot — the per-iter rollback is non-negotiable |
| The agent has no ability to read structured tool results | Use a framework that does (Aider, LangGraph, Claude Code tool use) — naked text-completion loops won't carry the feedback |

### Known engineering pitfalls

- **Aider `--no-auto-commits`** disables the per-iter commit. Don't turn it
  off "to keep history clean" — `git rebase -i` after the loop is the right
  cleanup. `[aider/git]`
- **Pytest exit code 5** = "no tests collected". A passing-because-nothing-ran
  config bug will silently report success.
- **Mypy with `--ignore-missing-imports`** can mask real import errors;
  prefer `--strict` in the loop, relax for general use.
- **`ruff --fix`** rewrites files. Either commit before re-running, or use
  `ruff check` (no `--fix`) in the loop and let the agent do the fixing.
- **Sonnet truncating at 4k tokens mid-fix** — keep per-iter context lean
  so the model has room to write the full diff `[aider/sonnet-not-lazy]`.

---

## 7. 跨框架对照 (Ecosystem Context)

| | Aider `--auto-lint`/`--auto-test` | OpenHands SWE-Bench harness | Cline auto-approve | Claude Code (bash + read) | Manual LangGraph cycle |
|---|---|---|---|---|---|
| Verifier wiring | `--lint-cmd`, `--test-cmd` flags | `eval_config.json` per instance | allowlist + run command | `Bash` tool the agent calls | Tool node returns stdout/stderr/exit |
| Iteration bound | ~3 internal retries on lint/test fail | `max_iterations` (50–100) | none built-in; user-set timeout | model-controlled (no hard cap) | `recursion_limit` + retry counter in state |
| Output formatting | Strips ANSI, sends to chat verbatim if non-zero | Raw observation injected into history | Raw terminal output to chat | Raw bash output (no compaction) | User-implemented in tool node |
| Per-iter commit | Yes (`--auto-commits` on) | Optional (eval mode) | Manual / via terminal tool | Manual (agent calls `git`) | Manual node |
| Escalation hook | "gives up after sensible tries" (silent) | Returns failure obs to harness | Stops on cap; user resumes | Returns to user | Conditional edge to `END` |
| Env-failure detection | Limited (treats all non-zero same) | Limited; SWE-Gym extends with infra setup phase | None | None | User-implemented |
| Sweet spot | Interactive pair-programming with one verifier | Batch evaluation; high iter budget | VS Code interactive | Generic agent harness | Custom workflows with non-trivial topology |

### Decision heuristics

- **Pair-programming, one verifier, you want auto-commit and undo**: Aider's
  `--auto-lint --auto-test --auto-commits` is the minimum-effort win.
  `[aider/lint-test]`
- **Batch benchmark / many issues, want to log every iter**: an OpenHands or
  SWE-Agent style harness with explicit `max_iterations` per instance.
  Beware the context-overflow infinite-loop pattern. `[oh/6357]`
- **In-IDE, terminal commands as part of the loop**: Cline's auto-approve
  with a small allowlist (`npm test`, `npm run lint`, `pnpm build`) is the
  ergonomic shape. `[cline/auto-approve]`
- **Building your own agent harness from scratch**: write the loop yourself
  with this skill's 7-step SOP — don't take a dependency on a framework
  unless you need its other features (graph state, multi-agent, HITL).
- **Need conditional branching (deploy after green, rollback if not)**:
  graduate to LangGraph with `interrupt()` at the deploy step. The loop is
  the inner node, the graph is the orchestration. `[langgraph/persistence]`

### Lessons that travel across frameworks

1. **The 25k token wall.** Aider documented it; LangGraph hits it via state
   bloat; OpenHands' infinite-loop bug is its manifestation. Always cap
   per-iter feedback.
2. **Per-iter commit beats clever history.** Aider's per-edit commit, Cline's
   per-step approval, and SWE-Bench's instance-level diff are all the same
   pattern: never lose state at iter K.
3. **The verifier output IS the prompt.** Models that score well on
   benchmark-tuned prompts can still fail when handed raw `pytest` output.
   Formatting is engineering work, not cosmetics.
4. **Models cheat at metrics.** Across Aider, OpenHands, and Cline, the
   pathological "pass by skipping" pattern is documented. Always diff-check
   the test suite after success.
5. **Env failures are not code failures.** Every framework that conflates
   them produces a "the agent broke my codebase trying to fix `apt-get`"
   incident. Classify before re-prompting.

---

## 附录: 引用速查 (Citation Index)

- `[aider/lint-test]` = https://aider.chat/docs/usage/lint-test.html
- `[aider/edit-errors]` = https://aider.chat/docs/troubleshooting/edit-errors.html
- `[aider/git]` = https://aider.chat/docs/git.html
- `[aider/sonnet-not-lazy]` = https://aider.chat/2024/07/01/sonnet-not-lazy.html
- `[oh/6357]` = https://github.com/All-Hands-AI/OpenHands/issues/6357 (SWE-Bench infinite loop on context overflow)
- `[oh/swe-bench]` = https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks/swe_bench/README.md
- `[swe-gym]` = https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/OpenHands.md
- `[cline/auto-approve]` = https://docs.cline.bot/features/auto-approve
- `[cline/cli]` = https://cline.bot/blog/introducing-cline-cli-2-0
- `[langgraph/recursion]` = https://docs.langchain.com/oss/python/langgraph/errors (GRAPH_RECURSION_LIMIT)
- `[langgraph/persistence]` = https://docs.langchain.com/oss/python/langgraph/persistence
- `[pytest/exit-codes]` = https://docs.pytest.org/en/stable/reference/exit-codes.html
