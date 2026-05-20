# R1 — Source Evidence (verbatim quotes)

This file collects the verbatim quotes that back every non-obvious claim in `SKILL.md`. Quotes are grouped by claim. URLs are the citation keys used inline.

---

## Claim 1: repo-map is symbol-level, not chunked text

> "A concise map of your whole git repository that includes the most important classes and functions along with their types and call signatures."
> — [aider.chat/docs/repomap.html]

> "The map contains a list of the files in the repo, along with the key symbols which are defined in each file."
> — [aider.chat/docs/repomap.html]

> "The LLM can see classes, methods and function signatures from everywhere in the repo."
> — [aider.chat/docs/repomap.html]

Implication used in SKILL §2.1: the unit of context is the **signature**, not the chunk. This is what justifies "skeleton over snippets" as an invariant.

---

## Claim 2: tree-sitter is the parsing backend

> Aider uses "the py-tree-sitter-languages python module, which provides simple, pip-installable binary wheels for most popular programming languages."
> — [aider.chat/2023/10/22/repomap.html]

Implication used in SKILL §2.2 / §6: tree-sitter coverage is the dividing line between "first-class language" and "path-only fallback".

---

## Claim 3: PageRank-style graph ranking selects "most important" symbols

> Aider employs "a graph ranking algorithm, computed on a graph where each source file is a node and edges connect files which have dependencies."
> — [aider.chat/2023/10/22/repomap.html]

> The map "only includes the most important identifiers, the ones which are most often referenced by other portions of the code."
> — [aider.chat/2023/10/22/repomap.html]

Note: the Aider blog calls it "a graph ranking algorithm". The community/SWE-Bench writeups call it PageRank-style. `SKILL.md` uses "PageRank-style" with the source-language caveat.

Implication used in SKILL §2.1 / Op 1: importance is **graph-based**, not semantic. A widely-imported helper outranks a deep but isolated module.

---

## Claim 4: budget is dynamic relative to chat state

> "Aider solves this problem by sending just the most relevant portions of the repo map."
> — [aider.chat/docs/repomap.html]

> "The token budget is influenced by the `--map-tokens` switch, which defaults to 1k tokens."
> — [aider.chat/docs/repomap.html]

> "Aider adjusts the size of the repo map dynamically based on the state of the chat."
> — [aider.chat/docs/repomap.html]

Implication used in SKILL §2.1 invariant B: budget expands when no files added (give LLM more map), shrinks when files added (give LLM more code).

---

## Claim 5: 70.3% correct-file rate on SWE-Bench Lite

> Aider's repo-map "successfully identified the correct file to edit in 70.3% of the benchmark tasks."
> — [aider.chat/2024/05/22/swe-bench-lite.html]

> "Aider's interactive approach outperforming complex agentic systems… the pragmatic, user-controlled design was unexpectedly effective without specialized tools, web access, or code execution capabilities during reasoning."
> — [aider.chat/2024/05/22/swe-bench-lite.html]

Implication used in SKILL §1 / §5 / §7: this is the single best-benchmarked datapoint for any code-context primitive in 2024. Specifically:
- No embeddings.
- No code execution at reasoning time.
- No network calls.
- The repo-map alone is doing the navigation.

---

## Claim 6: 25k tokens is the attention degradation threshold

> "Above about 25k tokens of context, most models start to become distracted."
> — [aider.chat/docs/troubleshooting/edit-errors.html]

Implication used in SKILL §2.4 / §5 case 1: repo-map's budget interacts with this hard cap. Bigger map ≠ better; bigger map past the threshold = worse.

---

## Claim 7: LLM uses map to ask for specific files (navigation, not retrieval)

> "If it needs to see more code, the LLM can use the map to figure out which files it needs to look at."
> — [aider.chat/docs/repomap.html]

Implication used in SKILL §2.3 / Op 5: write-set authorization is separated from navigation. The LLM names candidates; the harness decides what becomes editable.

---

## Claim 8: edit-format and JSON-wrapping interact with context quality

> "JSON-wrapping may distract or challenge models in a way that reduces their ability to reason about solving coding problems."
> — [aider.chat/2024/08/14/code-in-json.html]

Used in SKILL §6 anti-patterns indirectly. Even outside Aider, if your harness wraps repo-map output inside a JSON tool-call payload, expect quality loss.

---

## Claim 9: udiff vs whole vs diff edit format selection

> Edit format docs: "Aider is configured to use the optimal format for most popular, common models."
> — [aider.chat/docs/more/edit-formats.html]

Used in SKILL §2 as illustration of the broader "wire-protocol affects model behavior" principle that motivates skeleton-format over JSON-wrapped symbol lists.

---

## Notes on attribution conventions

- Inline citations in `SKILL.md` use short bracketed URLs `[aider.chat/...]` matching this file.
- Where Aider's blog uses informal phrasing ("graph ranking algorithm") and the wider community uses formal terminology ("PageRank"), `SKILL.md` adopts the technically-precise term and marks the gap here.
- The 70.3% number is the only headline benchmark we lean on. Treat it as a **lower bound** for any new harness — beat it before claiming novelty.
