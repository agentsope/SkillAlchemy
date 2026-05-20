# R2 — The 5-Question Gate and Decision Tree

This is the actual gate. It runs in ≤ 60 seconds once you've memorized it.

## Pre-gate (three commands, ~15 seconds)

```bash
git log --oneline | wc -l      # N_commits
git ls-files | wc -l           # N_tracked
ls -la                          # top-level shape
```

Optional fourth: `git log --since='90 days ago' --oneline | wc -l` (recent activity).

Optional fifth: `git shortlog -sn | wc -l` (contributor count).

These numbers feed Q1.

## The 5 questions

### Q1 — Size

> `git ls-files | wc -l` … is it under 20?

- **A** (under 20): no symbol surface to lean on
- **B** (20+): symbol surface exists

The 20 threshold is generous on the low side; for monorepos, run Q1 inside the subdirectory you're working in.

### Q2 — Public API

> Does this code have **external consumers**? (Published to a registry, depended on by other repos, has a CHANGELOG with semver entries.)

- **A** (no): internal application or prototype
- **B** (yes): library/SDK — public surface matters

If Q2=B, **state = library-SDK regardless of other answers**. Library status dominates because the *behavior change cost* is qualitatively different (breaking external callers).

### Q3 — Familiarity

> Can you name the top 5 modules / packages **from memory**, without opening the repo?

- **A** (no): unfamiliar — you'd have to grep to find auth, models, etc.
- **B** (yes): familiar — you have a mental map

For an *agent*, the analogous question is "is there a CLAUDE.md / AGENTS.md / README that maps the architecture in <100 lines?" If yes and the agent has read it this session, treat as familiar.

### Q4 — Typical change scope

> A normal task touches how many files?

- **A** (1–3): focused changes
- **B** (4+): cross-cutting changes

This is a proxy for whether `/add` discipline buys you anything. Cross-cutting changes hit context budget faster and benefit more from repo-map.

### Q5 — Written conventions

> Is there a `CONVENTIONS.md` / `STYLE.md` / `CLAUDE.md` / `AGENTS.md` — or even a strict linter config the team treats as canonical?

- **A** (no): conventions are implicit or absent
- **B** (yes): conventions are written down

If Q5=B and Q1=B, you have a brownfield with installed guardrails — agent can use them.

## Decision tree

```
                        ┌────────────────────┐
                        │  Q2: public API?   │
                        └─────────┬──────────┘
                          B (yes) │ A (no)
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                ┌──────▼─────┐         ┌─────▼──────┐
                │ Library/SDK│         │ Q1: <20    │
                └────────────┘         │  files?    │
                                       └─────┬──────┘
                                       A     │     B
                                       │     │     │
                              ┌────────┘     │     └───────────┐
                              │              │                 │
                       ┌──────▼─────┐        │          ┌──────▼─────┐
                       │ Greenfield │        │          │ Q3: know   │
                       └────────────┘        │          │  layout?   │
                                             │          └─────┬──────┘
                                             │           B    │   A
                                             │           │    │   │
                                             │  ┌────────┘    │   └──────────┐
                                             │  │             │              │
                                             │  │      ┌──────▼─────┐  ┌─────▼──────┐
                                             │  │      │ Q4: 1-3    │  │ Brownfield │
                                             │  │      │  files?    │  │   large    │
                                             │  │      └─────┬──────┘  └────────────┘
                                             │  │       A    │    B
                                             │  │       │    │    │
                                             │  │  ┌────┘    │    └────────────┐
                                             │  │  │         │                 │
                                             │  │  │  ┌──────▼─────┐    ┌──────▼─────┐
                                             │  │  │  │ Mid-size   │    │ Brownfield │
                                             │  │  │  │  familiar  │    │   large    │
                                             │  │  │  └────────────┘    └────────────┘
```

## Quick-lookup table (alternative to the tree)

| Q2 | Q1 | Q3 | Q4 | → State |
|----|----|----|----|---------|
| B  | -  | -  | -  | Library / SDK |
| A  | A  | -  | -  | Greenfield |
| A  | B  | A  | -  | Brownfield-large |
| A  | B  | B  | A  | Mid-size-familiar |
| A  | B  | B  | B  | Brownfield-large (cross-cutting → behave as if unfamiliar) |

Q5 doesn't change the state — but it **changes the first action**:

- Q5=A → first action in any state except greenfield is *write a 50-line CONVENTIONS.md*.
- Q5=B → first action is `/read CONVENTIONS.md` and respect what's there.

## Multi-state / monorepo handling

For `monorepo/packages/foo/`, repeat the gate **inside the subdirectory**:

```bash
cd packages/foo
git ls-files . | wc -l                  # subtree files
git log --oneline -- . | wc -l          # subtree commits
ls -la
```

Different sub-packages can legitimately have different states. The agent should switch strategy when cwd changes.

For Aider specifically, use `--subtree-only` to scope repo-map to the cwd. For Claude Code, just `cd` and trust cwd discipline.

## What to do with the answer

Once you have a state, the SKILL.md §4 operations table tells you:

- which tool to launch
- which context primitive to enable (repo-map / scaffolder / docstring)
- how much autonomy to grant
- the file/token budget

Write one line into chat or notes:

```
[repo-state: brownfield-large @ 2026-05-19] tool=Aider, primitive=repo-map, autonomy=approve, budget=5 files/<25k tok
```

Future sessions: read this line, skip re-gating, save 5 minutes.

## When to re-gate

- More than a week since last gate AND the repo doubled in size
- New contributor joined
- You published v0.1.0 (greenfield/familiar → library)
- The agent has chosen wrong tools twice in a row (signal: state assumption is off)
- You merged a structural refactor

## References

- aider-sop-skill SKILL.md §3 Phase 1–2 (the bootstrap pattern this gate slots before)
- aider.chat/docs/troubleshooting/edit-errors.html (25k token threshold informs Q4 budget)
- BMAD method (gate-first project ritual)
- thegeneralpartnership.substack.com/p/a-practical-guide-to-brownfield-ai (familiarity question framing)
