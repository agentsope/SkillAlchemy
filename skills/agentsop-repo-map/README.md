# repo-map skill

Phase D / C1 of the 7-SOP coder-agent skill landscape.

This skill distills **symbol-level repo-map context** as a reusable, framework-agnostic primitive for LLM-driven code editing. The canonical implementation is Aider's tree-sitter + PageRank repo-map, which hit **70.3% correct-file-identification on SWE-Bench Lite** with no embeddings, no code execution, and no network calls.

## Why this is a standalone skill

Most coder-agent harnesses re-invent some form of "give the LLM a map of the codebase". Aider's experiment is the most thoroughly benchmarked public design. Extracting it as a reusable skill lets:

- Custom agent authors lift the mental model without lifting Aider's CLI.
- Cursor / Cline / Continue users understand what they're (or aren't) getting from their built-in indexers.
- Reviewers audit what the LLM actually saw at decision time.

## Files

- `SKILL.md` — 7-section operational skill. Front-matter `name: repo-map`, `version: 0.1.0`.
- `references/R1-source-evidence.md` — verbatim source quotes with citations.
- `references/R2-cross-tool-comparison.md` — deeper comparison vs RAG, Cursor, Cline.
- `intermediate/operation_candidates.json` — operation-extraction working notes.

## How to use

Read `SKILL.md` end-to-end before the first multi-file edit task. For day-to-day reference jump to:

- §3 SOP — bootstrap / use / refresh / scope cycles.
- §4 operations — 8 named ops with Trigger/Action/Output/Evidence.
- §5 dilemmas — repo-too-big and wrong-file-edited decision trees.

## Citation policy

All non-obvious factual claims cite an Aider source URL inline (`[aider.chat/...]`). The 70.3% figure traces to `aider.chat/2024/05/22/swe-bench-lite.html`. The 25k-token attention degradation traces to `aider.chat/docs/troubleshooting/edit-errors.html`.

## Status

`v0.1.0` — first published distillation. Not yet validated against non-Aider harnesses; the design choices generalize but operation names are conventions, not standards.
