# R1 — The Four Repo States

The taxonomy is deliberately coarse: four buckets, not twelve. Coarser = faster to classify, and the strategy delta between adjacent buckets is large enough that finer distinctions don't pay back the gate time.

## 1. Greenfield

**Definition**: Empty or near-empty repo. No established symbols, no internal API surface, no encoded conventions. Either `git init` minutes ago, or a fresh `npx create-next-app` / `cargo new` scaffold with the default files only.

**Indicators**:

- `git ls-files | wc -l` < 20
- `git log --oneline | wc -l` < 10
- No `CONVENTIONS.md` / `STYLE.md`; lint config is the framework default
- No published package (not on npm/PyPI/crates)
- No test files yet, or only `*.example.test.*` from a scaffolder

**Edge cases**:

- *Just-after-scaffold*: still greenfield. Scaffolder boilerplate doesn't count as "your code." Repo-map of `create-next-app` output is noise.
- *Half-finished prototype (<200 LOC)*: still greenfield; conventions aren't real yet.
- *Spike branch in an old repo*: NOT greenfield; the parent repo's conventions still bind. Treat as the parent's state.

**Implication for agent**:

- repo-map ≈ empty; no leverage.
- LLM autonomy can be **high**: there's nothing to break.
- Scaffolders (`create-next-app`, `uv init`, `cookiecutter`, `dotnet new`, `bun init`) beat LLM file-generation for the shell.
- After scaffold, **commit before letting the agent loose** so /undo works.

---

## 2. Brownfield-large

**Definition**: A mature repo big enough that you can't hold all the symbols in your head, or unfamiliar enough that you genuinely don't know where things are. Strong conventions exist (whether documented or implicit). Touching the wrong file silently breaks something.

**Indicators**:

- `git ls-files | wc -l` ≥ 200 (rough heuristic; could be lower if structure is opaque)
- `git log --oneline | wc -l` > 200
- Multiple contributors (`git shortlog -sn | wc -l` > 3)
- Linter config, type-check config, CI workflow already present
- You can't answer "where is X implemented?" without grepping
- Has a CHANGELOG, ADRs, or `docs/` folder

**Edge cases**:

- *You wrote 80% of it and are still the maintainer*: NOT brownfield-large; it's mid-size-familiar. Familiarity > size.
- *Big but very modular* (microservice repo where each service is small): use op-7 (multi-state); each service is its own gate.
- *Recently forked and unstable*: treat as brownfield-large until you stabilize; conventions of upstream still apply.

**Implication for agent**:

- repo-map / symbol index is the **primary unlock** (Aider's tree-sitter, ctags, LSP).
- Autonomy **low**; approve each edit. The cost of editing the wrong file is high.
- `/add` budget: 2–5 files, < 25k tokens of code [aider edit-errors troubleshooting].
- `/ask` before `/code` — let the agent locate before letting it write.
- CONVENTIONS.md is a *required* artifact; if it doesn't exist, write it before the second session.

---

## 3. Mid-size familiar

**Definition**: A repo you (or the human driving the agent) wrote or substantially own. You can name the modules from memory and draw the architecture on a napkin. 100–800 files typical, but the bound is "in your head," not LOC.

**Indicators**:

- You can answer "where is auth?" in < 5 seconds without grep
- You wrote the conventions (or know them implicitly)
- Single primary maintainer; few-week-old context loss is rare
- Single-language / single-framework typically
- Test suite you trust

**Edge cases**:

- *Familiar but old (last touched 6 months ago)*: degrades toward brownfield-large; do a quick refresh `git log -p -- src/` on key files first.
- *Familiar to you but not the agent*: if the agent is fresh, this is *operationally* brownfield-large. The agent doesn't share your mental model — supplement with explicit /add and a 5-line architecture summary at session start.

**Implication for agent**:

- Don't waste repo-map budget; you know which files matter.
- Pre-load with explicit `/add` (or paths in CLI args) — skip the discovery dance.
- `/ask` to discuss design, `/code` to execute. Architect mode (Aider `--architect`) often shines.
- Autonomy **medium**; trust the test suite to catch regressions.

---

## 4. Library / SDK

**Definition**: Your code is consumed by other code. There exists a public API surface (a `package.json`'s `exports`, a Python package's `__init__.py`, a Rust `pub` API, an OpenAPI spec). Backward compatibility is a feature.

**Indicators**:

- Published to a registry (npm/PyPI/crates/Maven/RubyGems)
- Has a `CHANGELOG.md` with semver entries
- Has `docs/` or hosted docs (readthedocs, docusaurus)
- Has type stubs / `.pyi` / `.d.ts`
- "Internal" and "public" code are explicitly separated (often a `_private` or `internal/` folder)
- Issue tracker has "API change" / "breaking change" labels

**Edge cases**:

- *Internal-only "library" used by 3 services in the same monorepo*: this is library-SDK *behavior*. Treat as library — those 3 services depend on you.
- *Public library that's pre-1.0 and explicitly unstable*: still library-SDK; the *expectation* of stability is what matters, not the version number.

**Implication for agent**:

- The bar for editing public symbols is qualitatively higher.
- Test-fix loop is the highest-value primitive (Aider `--auto-test`, Claude Code with pytest).
- Any change to a public signature must be accompanied by: CHANGELOG entry, docstring update, semver consideration, and (if breaking) a deprecation path.
- Autonomy **low for public surface, medium for internals**.

---

## State transitions

Repos move between states over time:

- greenfield → mid-size-familiar (typical 1–3 months)
- mid-size-familiar → brownfield-large (typical handoff, or 2+ years)
- mid-size-familiar → library-SDK (when you publish v0.1.0)
- brownfield-large → mid-size-familiar (rare, requires deliberate refactoring + documentation)

Re-gate when:

- You publish v0.1.0 (mid → library)
- A new contributor joins (familiar → consider brownfield from *their* POV)
- You merge a feature that doubles the file count
- Six months pass without your touching it

---

## Why four, not more

We considered finer splits (greenfield-empty vs greenfield-scaffolded; brownfield-modular vs brownfield-tangled; library-stable vs library-pre-1.0). The strategy delta within each pair is too small to justify a separate row in the operation model. Coarse buckets, sharp lines.

## References

- aider-sop-skill SKILL.md §1 §6 + R4 §1
- The Brownfield Problem (jjmasse 2026): "AI development advice ignores your actual codebase"
- BMAD method (Vishal Mysore 2025): explicit greenfield/brownfield gate at project kickoff
- GSD workflow (bswen 2026): /gsd-map-codebase for brownfield onboarding
