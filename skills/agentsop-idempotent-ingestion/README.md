# idempotent-ingestion skill

A coder-agent skill for **re-ingest correctness**: making an ingestion pipeline
safe to run more than once over a changing corpus, so the second (and
thousandth) run never duplicates or corrupts the index.

**Version**: 0.1.0
**Status**: ENHANCE overlay over `[[llamaindex]]`. Covers LlamaIndex
`IngestionPipeline` + docstore, LangChain indexing API + `RecordManager`, and a
framework-free manual hash table.

## The core rule

> **Ingestion must be idempotent: a document's content hash decides
> insert / update / skip — so re-running the pipeline over unchanged docs is a
> no-op.**

The interesting run is the *second* one. A correct pipeline keeps a persisted
hash ledger (a "docstore") separate from the vector store, consults it before
embedding, and inserts / updates / skips per document. Deletes need an explicit
switch and a complete-snapshot guard.

## Why this overlay exists

Phase B found that `[[llamaindex]]` names `IngestionPipeline` + docstore +
`UPSERTS_AND_DELETE` as a production must-have (its OP-08 / A10) but stops at
"use it" — the re-ingest-correctness *contract* is never surfaced. This is
foundational for any production RAG that re-indexes, so this overlay codifies:

- what idempotency actually means (no-op-on-re-run),
- how the document hash + docstore decide insert/update/skip,
- why deletes don't propagate for free,
- how to *prove* it with a twice-run test,
- and the cross-framework equivalents.

## What this skill answers

- How to make a scheduled / CI / webhook-triggered ingestion safe to re-run.
- How to wire a docstore so unchanged docs cost zero embedding tokens on re-run.
- When to use `UPSERTS` vs `UPSERTS_AND_DELETE` vs `DUPLICATES_ONLY`.
- How to handle a slightly-edited document (re-embed all, or split the source?).
- How to handle deleted source docs without accidentally purging live content.
- How to debug "retrieval returns duplicates" / "deleted file still shows up".

## Files

- `SKILL.md` — main skill (7 sections: activation → mental model → SOP →
  operation models → dilemma cases → anti-patterns → cross-framework table).
- `references/R1-source-evidence.md` — every claim traced to the base
  `[[llamaindex]]` skill + primary LlamaIndex / LangChain docs.
- `references/R2-cross-framework.md` — full code for LlamaIndex / LangChain /
  manual hash table, with delete-propagation variants and the decisive
  "second run" table.
- `intermediate/operation_candidates.json` — OP-01..09 in machine-readable
  Trigger / Action / Output / Evidence form.

## Quick start

If you just need to make one pipeline re-run-safe today:

1. Read `SKILL.md` §3 Stage 1-2 — attach a **persisted** docstore and pin
   **stable** doc ids.
2. Pick a strategy (§3 Stage 3): `UPSERTS_AND_DELETE` if the corpus mirrors a
   source that can shrink; `UPSERTS` if append-mostly.
3. Add the **twice-run test** (§3 Stage 4 / OP-06) — the second `run()` must
   process 0 nodes and not grow the vector count. This is the gate.
4. Persist the docstore after each run and schedule it (§3 Stage 5).

## Anti-patterns it catches

`from_documents()` on a cron tick · `IngestionPipeline` with no `docstore=` ·
`SimpleDocumentStore` never persisted · random per-load doc ids · timestamps in
the hashed payload · `DUPLICATES_ONLY` mistaken for cross-run dedup ·
upsert-only on a deletable corpus · blind `UPSERTS_AND_DELETE` on partial input ·
no twice-run test in CI.

## Source basis

- Base skill: `[[llamaindex]]` (`llamaindex-sop-skill/SKILL.md`) OP-08, A10.
- LlamaIndex — *Ingestion Pipeline* + *Document Management*
  (`developers.llamaindex.ai/.../loading/ingestion_pipeline/`).
- LangChain — *Indexing* (`RecordManager`, `cleanup`)
  (`python.langchain.com/docs/how_to/indexing/`).

Date stamp: May 2026. `DocstoreStrategy` / `RecordManager` APIs move; re-check
the current docs before relying on exact enum / kwarg names.
