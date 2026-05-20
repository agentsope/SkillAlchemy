# R1 · Source Material for the Test-Fix Loop SOP

Evidence base for every load-bearing claim in `SKILL.md`. Inline citations in
the skill resolve to the tags here.

---

## Aider — the canonical implementation

### `[aider/lint-test]` — Linting and testing

URL: https://aider.chat/docs/usage/lint-test.html

Key claims (verbatim or close paraphrase):

- "Aider will try and fix any errors if the command returns a non-zero exit
  code."
- "By default, aider will lint any files which it edits."
- "When the linter reports a violation, Aider reads the message, modifies the
  code to satisfy the rule, and re-runs until the linter is happy or it gives
  up after a sensible number of tries."
- "After every code change, Aider runs your test suite. If anything fails, it
  captures the output, reads the failing test and the changed code, and
  proposes a fix — then re-runs."
- Formatter caveat: auto-formatters that rewrite files *and* return non-zero
  need a two-pass wrapper script — pass 1 formats, pass 2 verifies. Only the
  second exit code is the signal.

CLI flags relevant to this skill:

```
--auto-lint                 # default on; lint touched files after each edit
--no-auto-lint              # disable
--lint-cmd "ruff check ."   # custom lint command (multiple langs comma-sep)
--auto-test                 # enable test-on-edit
--no-auto-test              # default off
--test-cmd "pytest -x"      # custom test command
--auto-commits              # default on; commit each edit
--no-auto-commits           # disable (loses /undo trail — not recommended)
```

### `[aider/edit-errors]` — Edit error troubleshooting

URL: https://aider.chat/docs/troubleshooting/edit-errors.html

The load-bearing quote:

> "Above about 25k tokens of context, most models start to become distracted."

This sets the hard upper bound on per-iteration feedback size. Each loop
iteration adds the verifier output to the chat history; without per-iter
distillation, you cross 25k by iter 3.

### `[aider/git]` — Git integration

URL: https://aider.chat/docs/git.html

- One git commit per edit, default.
- Aider's `/undo` walks the commit chain backwards.
- Recommended cleanup: `git rebase -i HEAD~N` post-loop, not `--no-auto-commits`
  in-loop.

### `[aider/sonnet-not-lazy]` — Sonnet truncation

URL: https://aider.chat/2024/07/01/sonnet-not-lazy.html

Sonnet truncates at 4k output tokens mid-edit when context is bloated. Keep
per-iter feedback lean so the model has output budget to emit the full fix.

---

## OpenHands — the SWE-Bench harness

### `[oh/swe-bench]` — SWE-Bench evaluation README

URL: https://github.com/All-Hands-AI/OpenHands/blob/main/evaluation/benchmarks/swe_bench/README.md

- `max_iterations` is configurable per instance (commonly 50–100 for
  SWE-Bench Verified).
- Each instance: one issue → repo state → agent runs → diff submitted.
- Test running is built into the eval harness (not the agent loop itself
  in SWE-Bench Lite mode — agent submits a patch, harness tests it).

### `[oh/6357]` — Infinite-loop on context overflow

URL: https://github.com/All-Hands-AI/OpenHands/issues/6357

> "The program enters an infinite loop and eventually times out when the
> conversation context exceeds the model's maximum window size. This issue
> arises from a previously introduced fix that attempts to truncate the
> agent's history when the context window exceeds its limit by truncating
> the history roughly in half. However, the problem is that this approach
> doesn't correctly manage the agent's internal state after truncation,
> which causes the agent to enter an infinite loop."

Canonical case of "no hard iteration cap + naive history truncation =
infinite loop". Direct evidence for OP-3 (bound the loop with a hard cap,
not just a context-window safety net).

### `[swe-gym]` — SWE-Gym extension

URL: https://github.com/SWE-Gym/SWE-Gym/blob/main/docs/OpenHands.md

Notable: SWE-Gym distinguishes infra-setup phase (provisioning the test
env) from agent-iteration phase. Env failures during the agent phase are
classified separately. Evidence for OP-6 (env-failure escalation).

---

## Cline — the IDE-side feedback loop

### `[cline/auto-approve]` — Auto-Approve & YOLO Mode

URL: https://docs.cline.bot/features/auto-approve

- Allowlist common safe commands: `npm test`, `npm run lint`, `pnpm build`,
  `pytest`, `cargo check`.
- Build commands and read-only queries are flagged "safe"; destructive
  operations (rm, git push --force, db migrations) always require explicit
  approval.
- "If a test fails, Cline reads the error, proposes a fix, applies it, and
  runs again. The implement-test-fix loop continues until the suite is green."
- The mental model is the same as Aider's — per-step approval (Cline) vs.
  per-step auto-commit + post-hoc `/undo` (Aider).

### `[cline/cli]` — Cline CLI 2.0

URL: https://cline.bot/blog/introducing-cline-cli-2-0

`-y` flag = full autonomy, no interactive TUI. Cline streams stdin/stdout
making it pipeline-friendly for CI loops.

---

## LangGraph — the bounded-loop lesson

### `[langgraph/recursion]` — `GRAPH_RECURSION_LIMIT`

URL: https://docs.langchain.com/oss/python/langgraph/errors

Key claim:

> "`recursion_limit` is not intended to be a primary control flow mechanism;
> hitting it indicates an underlying design flaw."

The lesson generalizes: any LLM loop without an explicit exit condition in
state (retry counter, error-class change) will fight its safety net. Same
underlying point as the OpenHands SWE-Bench infinite-loop bug.

### `[langgraph/persistence]` — Checkpointers

URL: https://docs.langchain.com/oss/python/langgraph/persistence

Per-superstep state snapshot. Analogous to Aider's per-edit commit: the
durability lever that lets you bisect or roll back the loop iter-by-iter.

---

## Cross-framework lessons (synthesis)

| Lesson | Aider source | OpenHands source | Cline source | LangGraph source |
|---|---|---|---|---|
| Bound iterations | "gives up after sensible tries" `[aider/lint-test]` | `max_iterations` + `[oh/6357]` bug | manual cap | `recursion_limit` `[langgraph/recursion]` |
| Per-iter durability | `--auto-commits` `[aider/git]` | per-instance diff submission | per-step approval `[cline/auto-approve]` | per-superstep checkpoint `[langgraph/persistence]` |
| Context bloat limit | 25k threshold `[aider/edit-errors]` | history truncation bug `[oh/6357]` | (implicit) | state bloat causes recursion-limit hits |
| Distinguish env vs. code failure | (limited) | SWE-Gym phase split `[swe-gym]` | (none documented) | (user-implemented) |

---

## External research signals (2025–2026)

- "Testing plays a critical role for code agents: it exposes regressions,
  validates hypotheses, and provides a feedback loop during patch development."
  — multiple SWE-Bench-derived papers, 2025.
- "Industrial studies report closed-loop pipelines that combine LLM-based
  test generation with mutation-guided feedback to steer or refine generated
  tests toward stronger fault-revealing capability." — confirms the
  "verifier-output-as-prompt" framing in §2.1.
- Agents struggle with: "specification alignment, edge case handling, time
  complexity optimization, and resource management" even with a feedback
  loop. Implication: the loop catches most regressions but not architectural
  bugs; pair with eval/review for those.

---

## Pytest exit-code reference

### `[pytest/exit-codes]`

URL: https://docs.pytest.org/en/stable/reference/exit-codes.html

| Code | Meaning |
|---|---|
| 0 | All tests passed |
| 1 | Tests failed |
| 2 | Interrupted (Ctrl-C, internal error) |
| 3 | Internal error |
| 4 | pytest CLI usage error |
| 5 | **No tests collected** (silent false-positive risk) |

Exit-code 5 is the silent killer: looks like "tests didn't fail" but means
"tests never ran". Always pair `exit 0` success detection with a
`--collect-only` count check or a config sanity probe.

---

## Concrete verifier-command recipes per stack

```bash
# Python (FastAPI/Django/lib)
ruff check . && mypy --strict src && pytest -x --tb=short

# TypeScript (Vite/Next)
eslint . && tsc --noEmit && vitest run --bail 1

# Go
gofmt -l . | (! grep .) && go vet ./... && go test ./...

# Rust
cargo fmt --check && cargo clippy -- -D warnings && cargo test --no-fail-fast=false

# Mixed monorepo (per-package via turbo)
turbo run lint typecheck test --filter=...[HEAD]
```

Each is a single `&&`-chained command — one exit code, one feedback message,
one iteration. This is the shape Aider's `--test-cmd` accepts and what every
manually wired loop should target.
