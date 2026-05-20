# R2 · Feedback-Formatting Recipes

Concrete before/after examples for distilling verifier output into ≤2k-token
feedback messages. Operationalizes `SKILL.md` §3 Step 3 (the load-bearing
step) and OP-2.

> The single biggest lever in this skill is *what message gets injected
> between iter N and iter N+1*. These recipes target the common verifiers.

---

## Recipe 1 · pytest

### Raw (DON'T paste this)

```
============================= test session starts ==============================
platform darwin -- Python 3.12.4, pytest-8.3.2, pluggy-1.5.0
rootdir: /Users/dev/project
configfile: pyproject.toml
plugins: cov-5.0.0, anyio-4.4.0, asyncio-0.23.8
collected 47 items

tests/test_auth.py ..F....                                              [ 15%]
tests/test_billing.py ............                                      [ 40%]
tests/test_routes.py ..............                                     [ 70%]
tests/test_models.py ..............                                     [100%]

=================================== FAILURES ===================================
__________________________ test_jwt_expiry_handling ____________________________

    def test_jwt_expiry_handling():
        token = make_token(exp=None)
>       assert verify_token(token) is None
E       TypeError: '<' not supported between instances of 'NoneType' and 'datetime.datetime'

tests/test_auth.py:42: TypeError
[lots more boilerplate, coverage report, warnings...]
=========================== short test summary info ============================
FAILED tests/test_auth.py::test_jwt_expiry_handling - TypeError: '<' not...
=================== 1 failed, 46 passed in 3.21s ===========================
```

≈ 1800 tokens of mostly noise.

### Distilled

```
Verifier failed (exit 1, `pytest -x --tb=short`).

FAILING TEST (1 of 1):
  tests/test_auth.py::test_jwt_expiry_handling

ERROR:
  TypeError: '<' not supported between instances of 'NoneType' and 'datetime.datetime'

LAST FRAME:
  src/auth.py:47 in verify_token
      if exp < now: return None

YOUR LAST EDIT touched src/auth.py:40-50.

Hint: `exp` is None when the JWT lacks an `exp` claim — the test passes
exp=None deliberately. Either default exp or guard the comparison.
```

≈ 110 tokens. The model has *more* information for fixing (the file:line, the
hint) and 16× less noise.

### Formatter pseudo-code

```python
def format_pytest_failure(stdout: str, stderr: str, exit_code: int, last_diff: str) -> str:
    if exit_code == 5:
        return "Verifier exited with code 5 (no tests collected). Check pytest config and test discovery paths."
    if exit_code == 0:
        return None  # success

    # Pull first FAILURES block
    m = re.search(r"_+ (.+?) _+\n(.*?)(?=\n=+|\Z)", stdout, re.DOTALL)
    test_name = m.group(1) if m else "(unknown)"
    body = m.group(2).strip() if m else stdout[-2000:]

    # Last frame = last line with file:line: ErrorType
    last_frame = re.findall(r"^(.+\.py):(\d+):.*$", body, re.MULTILINE)
    frame_str = f"{last_frame[-1][0]}:{last_frame[-1][1]}" if last_frame else "(no frame)"

    # Last edit anchor (from git diff HEAD~1 --name-only -U0)
    edited_files = [l for l in last_diff.split("\n") if l.endswith(".py")]

    return f"""Verifier failed (exit {exit_code}, pytest).

FAILING TEST: {test_name}

ERROR:
{body.splitlines()[-1][:200]}

LAST FRAME: {frame_str}

YOUR LAST EDIT touched: {', '.join(edited_files[:5])}
"""
```

---

## Recipe 2 · mypy

### Raw

```
src/auth.py:47: error: Unsupported operand types for < ("None" and "datetime")  [operator]
src/auth.py:47: note: Left operand is of type "Optional[datetime]"
src/billing/charge.py:103: error: Item "None" of "Optional[User]" has no attribute "id"  [union-attr]
src/billing/charge.py:118: error: Argument 1 to "send_receipt" has incompatible type "Optional[str]"; expected "str"  [arg-type]
src/routes/admin.py:34: error: Returning Any from function declared to return "User"  [no-any-return]
src/routes/admin.py:45: error: Missing return statement  [return]
Found 5 errors in 3 files (checked 47 source files)
```

### Distilled (still readable, but ordered by relevance)

```
mypy --strict failed (5 errors, 3 files).

FIRST ERROR (in your last-edited file src/auth.py):
  L47 [operator]: Unsupported operand types for < ("None" and "datetime")
       Left operand is of type "Optional[datetime]"

OTHER ERRORS (summary):
  src/billing/charge.py: 2 errors (union-attr, arg-type)
  src/routes/admin.py: 2 errors (no-any-return, return)

Fix L47 first — the others may resolve transitively if exp/None handling
is the root cause.
```

Key move: **anchor the first error to the file the agent just edited**.
Mypy already prints in source order, but the model doesn't know which file
the agent touched. Adding that anchor cuts wrong-file fixes drastically.

---

## Recipe 3 · ruff

### Raw

```
src/auth.py:12:1: F401 [*] `os` imported but unused
src/auth.py:47:5: E712 Comparison to `None` should be `cond is None`
src/billing/charge.py:88:80: E501 Line too long (102 > 79)
src/billing/charge.py:103:5: E711 Comparison to `None` should be `cond is None`
src/routes/admin.py:34:5: F841 Local variable `result` is assigned to but never used
Found 5 errors.
[*] 1 fixable with `ruff check --fix`.
```

### Distilled

```
ruff check failed (5 issues).

  src/auth.py:12  F401 unused import `os`
  src/auth.py:47  E712 `== None` → use `is None`
  src/billing/charge.py:88  E501 line too long
  src/billing/charge.py:103  E711 `!= None` → use `is not None`
  src/routes/admin.py:34  F841 unused variable `result`

1 issue is auto-fixable; the rest need manual fixes.
```

Ruff output is already terse. Recipe: pass through, prepend the count.
Don't bother with `--show-source` in loop mode — the line numbers are enough.

**Anti-pattern**: piping `ruff check --fix` into the loop. The fixer rewrites
files; the loop then thinks the agent edited them. Use plain `ruff check`
and let the LM emit the fixes.

---

## Recipe 4 · eslint

### Raw

```
/Users/dev/project/src/auth.ts
  12:1   error    'os' is defined but never used  no-unused-vars
  47:5   error    Expected '===' and instead saw '=='  eqeqeq
  88:80  warning  Line 88 exceeds the maximum line length of 80  max-len

/Users/dev/project/src/billing.ts
  103:5  error  'foo' is defined but never used  no-unused-vars

✖ 4 problems (3 errors, 1 warning)
  3 errors and 0 warnings potentially fixable with the `--fix` option.
```

### Distilled

```
eslint failed (3 errors, 1 warning).

  src/auth.ts:12   no-unused-vars: 'os' unused
  src/auth.ts:47   eqeqeq: use === not ==
  src/billing.ts:103  no-unused-vars: 'foo' unused

(Plus 1 max-len warning, ignored.)
```

Recipe: strip absolute paths to project-relative; drop warnings if there are
errors; keep the rule name (the agent uses it to look up the fix pattern).

---

## Recipe 5 · tsc (TypeScript compiler)

### Raw

```
src/auth.ts:47:13 - error TS2367: This comparison appears to be unintentional because the types 'Date | undefined' and 'Date' have no overlap.

47     if (exp < now) {
                ~~~

src/billing/charge.ts:103:11 - error TS2532: Object is possibly 'undefined'.

103     return user.id;
                ~~~~~~~

Found 2 errors in 2 files.
```

### Distilled

```
tsc --noEmit failed (2 errors).

FIRST (in your last-edited file src/auth.ts):
  L47 TS2367: comparison between Date|undefined and Date has no overlap
    if (exp < now) {

OTHER:
  src/billing/charge.ts:103 TS2532: `user.id` — object possibly undefined

Both look like missing null/undefined guards.
```

tsc emits readable output; recipe is just to anchor to last-edited file.

---

## Recipe 6 · cargo / rust

### Raw

```
error[E0599]: no method named `unwrap_or_default` found for struct `Vec<u8>` in the current scope
  --> src/parser.rs:42:18
   |
42 |     let bytes = read_bytes(&path).unwrap_or_default();
   |                                   ^^^^^^^^^^^^^^^^^ method not found in `Vec<u8>`
   |
   = help: items from traits can only be used if the trait is in scope
help: there is a method `unwrap_or` with a similar name
  --> src/parser.rs:42:18
   |
42 |     let bytes = read_bytes(&path).unwrap_or(...);
   |                                   ~~~~~~~~~

error: aborting due to 1 previous error
```

### Distilled

```
cargo check failed (1 error).

  src/parser.rs:42 E0599: no method `unwrap_or_default` on `Vec<u8>`

COMPILER SUGGESTS: use `unwrap_or(...)` instead.
```

Recipe: rust's compiler hints are gold — extract the `help:` line. Drop the
ASCII art arrows; the model doesn't benefit from them.

---

## Recipe 7 · Build error (go / npm / etc.)

### Raw (npm run build, vite)

```
> project@1.0.0 build
> vite build

vite v5.0.0 building for production...
✓ 234 modules transformed.
[plugin:vite:resolve] Failed to resolve import "./missing.js" from "src/index.ts"
file: /Users/dev/project/src/index.ts:3:18

  1  | import { foo } from './existing.js';
  2  | import { bar } from './also-existing.js';
  3  | import { baz } from './missing.js';
                          ^

error during build:
Error: Failed to resolve import "./missing.js" from "src/index.ts". Does the file exist?
    at ...stack trace...
```

### Distilled

```
Build failed: vite cannot resolve import.

  src/index.ts:3  cannot resolve `./missing.js`

Either the file should exist (create it) or the import is wrong (rename).
```

Recipe: build errors are usually one root cause buried in stack noise.
Extract the first `error:` or `Failed to resolve` line. Drop everything else.

---

## Truncation strategy when a single failure is too big

Some pytest tracebacks are genuinely long (deep frameworks, async stack
unwinding). When the formatted failure exceeds 2k tokens:

1. **Keep**: file:line, error type, last 3 frames.
2. **Truncate middle**: replace 20+ frames in the middle with
   `... [N frames omitted, mostly framework internals] ...`.
3. **Keep**: any frame whose path matches `^src/` or the agent's last-edit
   files.
4. **Last resort**: emit "Traceback omitted (too long). First exception:
   `<type>: <message>`. Edited files: X, Y."

---

## When *not* to format — pass through raw

Some signals are best preserved verbatim:

- **Test assertion diffs** from pytest's `assert` rewriting — the diff
  between expected and actual is exactly what the model needs.
- **Snapshot test diffs** (jest's snapshot diff, insta in rust) — raw is the
  signal.
- **Single-line errors** under 200 chars — formatting overhead exceeds
  payload.

Rule: format when the noise ratio is >80%. Pass through when signal density
is already high.

---

## Common formatting bugs (don't make these)

1. **Stripping the file path entirely.** The model needs `src/auth.py:47`
   to make the right fix. Keep the path; just relativize it.
2. **Dropping the error class/code.** `E712`, `TS2367`, `E0599` are
   look-uppable. Keep them.
3. **Adding "Please fix this carefully."** Imperatives degrade
   instruction-following on some models. The error message is the prompt.
4. **Showing ANSI escapes.** `\x1b[31m` burns tokens. Set `NO_COLOR=1`
   or strip after capture.
5. **Including coverage reports / collection summaries / warnings about
   plugins.** Noise.
6. **Concatenating stdout + stderr without labels.** Different verifiers
   put different things in each. Label when ambiguous.

---

## Quick reference: per-verifier output channel

| Verifier | Errors in stdout? | Errors in stderr? | Exit codes worth checking |
|---|---|---|---|
| `pytest` | Yes (FAILURES block) | Rarely | 0=pass, 1=fail, 5=no-tests |
| `ruff check` | Yes | No | 0=clean, 1=issues |
| `mypy` | Yes | No | 0=clean, 1=errors |
| `eslint` | Yes | No | 0=clean, 1=warnings, 2=errors |
| `tsc --noEmit` | Yes | No | 0=clean, 1=errors |
| `cargo check` | No | **Yes** | 0=clean, ≠0=errors |
| `go test` | Yes | Rarely | 0=pass, 1=fail, 2=build error |
| `go vet` | No | **Yes** | 0=clean, ≠0=issues |
| `gofmt -l` | Yes (filenames!) | No | 0 always; check stdout empty |

Notable: `gofmt -l` returns 0 even when files need formatting; the signal is
stdout being non-empty. A naive `exit_code == 0` check misses it.
