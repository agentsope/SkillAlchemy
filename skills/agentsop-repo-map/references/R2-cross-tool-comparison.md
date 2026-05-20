# R2 — Cross-Tool Comparison: How Other Coder-Agents Handle Code Context

`SKILL.md` §7 has the summary table. This file goes deeper for each tool and surfaces the design tensions explicitly.

---

## Aider — tree-sitter + PageRank repo-map

- **Mechanism**: parse all git-tracked source with tree-sitter; build a graph where nodes are files and edges follow symbol references; rank nodes with a PageRank-style algorithm; render top-ranked symbols as skeleton text within a token budget.
- **Storage**: none persistent. Rebuilt per session (with file-level mtime caching).
- **Update**: per-edit incremental refresh.
- **What LLM sees**: real signatures in plain text.
- **Auditability**: `/map` dumps the exact skeleton.
- **Failure modes**:
  - Long-tail symbols truncated when budget tight.
  - Unsupported languages get path-only fallback.
  - Stale map after large refactor (mitigation: `--map-refresh always`).
- **Public benchmark**: 70.3% correct-file on SWE-Bench Lite.
- **Strengths to copy**: dynamic budget, dump-to-text auditability, write-set / read-set separation.

---

## Embedding RAG (LlamaIndex, Chroma, custom code chunkers)

- **Mechanism**: split source into chunks (often by AST node or by lines), embed each chunk, store in vector DB; retrieve top-k by cosine similarity to the task query.
- **Storage**: persistent vector store; non-trivial size.
- **Update**: re-embed on file change. Latency depends on embedding model.
- **What LLM sees**: text snippets (often function bodies), not necessarily signatures.
- **Auditability**: weak. The chunk-selection ranking is hard to explain without exposing similarity scores.
- **Failure modes**:
  - Semantic distance ≠ call-graph distance: a doc string about "auth" can outrank the real `auth_handler` if names diverge.
  - Embedding API changes invalidate the index.
  - Chunk boundaries cut across function bodies → fragmented context.
- **Public benchmark on code editing**: no widely-cited SWE-Bench-equivalent for embedding-only retrieval beating Aider's 70.3%.
- **When to use anyway**: documents, ADRs, READMEs, historical commit messages — *not* primary code navigation.

---

## Cursor codebase index

- **Mechanism**: closed-source. Public docs indicate a hybrid of AST extraction and embeddings, with cloud sync.
- **Storage**: cloud (concern for sensitive code).
- **Update**: background sync.
- **What LLM sees**: not directly exposed; surfaced through Composer / chat / inline.
- **Auditability**: very weak. UI shows which files are "in context" but not the ranking logic.
- **Failure modes**:
  - Data leaves the local machine (compliance issue for many orgs).
  - Quality regressions across Cursor releases are not user-controllable.
- **When it shines**: VS-Code-native developers who accept the cloud trade-off and value UI integration.

---

## Cline — file tree + on-demand `read_file` tool

- **Mechanism**: no pre-built index. LLM is given a file tree (paths only) and a `read_file` tool. It calls the tool when it wants content.
- **Storage**: none.
- **Update**: trivially fresh (each `read_file` reads from disk).
- **What LLM sees**: only what it asks for.
- **Auditability**: tool-call history is the audit trail.
- **Failure modes**:
  - Many round-trips when the LLM doesn't know where to look — tokens spent on tool-call chatter, latency spent on round-trips.
  - File-name-only navigation: if filenames are uninformative, the LLM probes blindly.
- **When it shines**: small repos; tasks where the user already knows the files; environments needing step-by-step user approval.

---

## Continue — IDE-side RAG

Conceptually similar to Embedding RAG but with IDE-native chunking and a unified Edit/Chat/Agent/Autocomplete surface. Same design trade-offs apply.

---

## OpenHands — agentic plan→read→edit

- **Mechanism**: full agent loop. Reads files via shell/tool-calls in a sandboxed VM as needed.
- **Storage**: none; relies on agent's planning capability.
- **Update**: always fresh.
- **What LLM sees**: whatever the planner read this turn.
- **Auditability**: trajectory logs.
- **Failure modes**: heavy token / latency cost when planning explores poorly.

---

## Design tensions surfaced by the comparison

### Tension 1: Determinism vs adaptiveness

- repo-map: deterministic. Same code, same map.
- RAG: deterministic if model + chunker fixed, but model upgrades shift results.
- Agentic exploration: non-deterministic by design.

Lesson: for code review and reproducible CI agents, determinism is a hard requirement. repo-map wins. For exploratory human-in-the-loop, adaptiveness can be fine.

### Tension 2: Token cost of context vs token cost of navigation

- repo-map: pays tokens upfront (skeleton in every prompt).
- Cline-style: pays tokens lazily (per `read_file`). Total often higher on multi-file tasks.
- RAG: middle ground (only retrieved chunks).

repo-map wins when the same map is reused across many turns. Cline wins for single-shot small tasks.

### Tension 3: Auditability vs UX polish

- repo-map: ugly text dump, easy to audit.
- Cursor: pretty UI, opaque internals.

Compliance-heavy orgs should bias to repo-map. Solo devs may prefer Cursor.

### Tension 4: Write-set / read-set separation

This is the under-appreciated design lesson. Aider enforces it; Cursor blurs it; agentic systems often skip it entirely. Skipping it correlates with the "wrong file edited" failure mode in SKILL §5 case 2.

---

## Recommendation matrix

| Constraint | First choice | Second |
|---|---|---|
| Can't send code off-machine | repo-map | Cline file-tree |
| Need reviewer-auditable context | repo-map | — |
| tree-sitter doesn't cover your language | RAG / Cline | repo-map with path-only fallback |
| Very large monorepo, single team | repo-map with `--subtree-only` | Cursor (if cloud ok) |
| Mixed code + docs + ADRs | repo-map + RAG (two layers) | Cursor |
| Want full IDE UX | Cursor / Continue | — |
| Building a custom agent | repo-map as primitive | + agent loop on top |

---

## Open questions / future work

- Has any open benchmark reproduced or beaten Aider's 70.3%? Not as of the latest pass through the source set.
- Hybrid repo-map + RAG: under-explored. Worth a controlled experiment in a follow-up skill.
- Cross-repo repo-map (monorepo with package boundaries): partly addressed by `--subtree-only` but no public benchmark on multi-package navigation accuracy.
