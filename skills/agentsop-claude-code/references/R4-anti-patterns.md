# R4: Anti-Patterns & Boundaries

## Anti-patterns and the fix

| Anti-pattern | Fix |
|---|---|
| `cat`-ing whole large files | Grep to the region, then Read with `offset`/`limit` |
| Searching via `find`/`grep -r`/`cat` in Bash | Use Glob / Grep / Read |
| One giant turn with many unrelated edits | Split into 2–5 verifiable steps |
| Claiming "done" without running anything | Run the test/command and report the real output |
| Restating the same convention every time | Write it into `CLAUDE.md` once |
| Pushing / deleting / publishing without authorization | Confirm first, or do not act |

## Hard boundaries

- **Never touch production or databases** without explicit, current authorization.
- **Never publish outward-facing content** (it may be cached or indexed) unless the user explicitly asked.
- **Commit and push only when the user asks**; do not push on the default branch unprompted.
- **"Done" requires evidence** — a passing test, a successful command, an observed output — never a bare assertion.

These boundaries exist because the agentic loop makes irreversible actions cheap to trigger and hard to recall. The permission gate exists precisely to put a human decision in front of them.
