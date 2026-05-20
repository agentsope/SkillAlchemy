---
name: agentsop-idempotent-ingestion
version: 0.1.0
description: |
  Re-ingest-correctness SOP for production RAG. Activate when a calling agent
  builds, reviews, or debugs an ingestion pipeline that runs more than once over
  a changing corpus — scheduled re-index, incremental updates, CI re-ingest, or
  a "retrieval has duplicates / shows deleted docs" bug. Encodes the rule —
  **ingestion must be idempotent: a document's content hash decides
  insert/update/skip, so re-running over unchanged docs is a no-op** — plus the
  docstore + doc-hash upsert machinery (LlamaIndex `IngestionPipeline` +
  `DocstoreStrategy`), the delete-propagation problem, and cross-framework
  equivalents (LangChain `index()` + `RecordManager`, manual hash table). ENHANCE
  overlay over [[llamaindex]]: the IngestionPipeline exists in the base skill but
  the re-ingest-correctness contract is not surfaced.
trigger_keywords:
  - "idempotent ingestion"
  - "re-ingest"
  - "re-index"
  - "docstore"
  - "doc hash"
  - "upsert"
  - "duplicate chunks"
  - "IngestionPipeline"
  - "RecordManager"
  - "incremental update"
  - "scheduled reindex"
when_to_use:
  - "any ingestion pipeline that will run more than once (cron, CI, webhook, manual re-run)"
  - "a corpus where source documents are added, edited, or deleted over time"
  - "debugging duplicate / stale chunks polluting retrieval after a re-run"
  - "reviewing a PR that calls VectorStoreIndex.from_documents / pipeline.run without a docstore"
  - "designing the ingestion side of a production RAG before first deploy"
when_not_to_use:
  - "a one-shot index built once and never refreshed (static corpus, throwaway notebook)"
  - "the corpus is small enough to fully rebuild from scratch in seconds and rebuild-on-every-run is genuinely acceptable (measure first)"
  - "pure retrieval / query-time work with no ingestion path"
---

# Idempotent Ingestion · Re-Ingest-Correctness SOP

> Third-person operating model for a coder agent that owns ingestion
> correctness across repeated runs. The audience is the LLM agent writing or
> reviewing the pipeline code — not the end user.

> **One sentence**: *The interesting run is the second one. A correct pipeline
> hashes each document, looks the hash up in a docstore, and inserts / updates
> / skips accordingly — so re-running over unchanged docs changes nothing.*

This skill is an **ENHANCE overlay** over [[llamaindex]]. The base skill names
`IngestionPipeline` with `docstore` + `UPSERTS_AND_DELETE` as a hardening
must-have (OP-08, anti-pattern A10) but stops at "use it". This overlay
surfaces the *correctness contract* — what idempotency actually means, how the
hash decides the action, and how it generalises beyond LlamaIndex.

---

## 1. 何时激活 (Activation Rules)

Activate this skill whenever **any** of the following holds:

1. The codebase contains an ingestion call (`VectorStoreIndex.from_documents`,
   `pipeline.run(documents=...)`, `vectorstore.add_documents`, a custom embed
   + upsert loop) **and** that call will execute more than once over a corpus
   that can change between runs.
2. The user mentions any of: re-ingest, re-index, scheduled / nightly index
   refresh, incremental document updates, docstore, doc hash, upsert,
   `RecordManager`, "keep the index in sync with the source".
3. A bug report says "I see the same answer chunk twice", "retrieval returns
   duplicates", "deleted a file but it still shows up in answers", "the index
   keeps growing every night even though nothing changed".
4. PR review: new ingestion code that builds the index with no docstore / no
   hash-keyed dedup and the corpus is live (LlamaIndex base skill A10).
5. A production RAG is about to ship and the ingestion side has only ever been
   tested as a cold first run.

Do **not** activate when:

- The index is built **once** from a static corpus and never refreshed — there
  is no second run to make idempotent.
- The corpus is tiny and rebuilding from scratch each run is *measurably*
  cheaper than maintaining a docstore (rare; verify, don't assume).
- The task is purely query-time (retrieval, rerank, synthesis) with no
  ingestion path in scope.

---

## 2. 核心心智模型 (Core Mental Model)

Three principles. Violating any one means a second run can duplicate or corrupt
the index — regardless of how good the retrieval stack downstream is.

### Principle 1 — Ingestion must be idempotent; the hash is the decision

> **Re-running the pipeline over an unchanged document is a no-op.** Run it
> once, run it a thousand times — same index. The mechanism: each document is
> reduced to a stable **content hash** (and a stable **doc id**); that hash is
> looked up in a **docstore** (a key→hash record store separate from the vector
> store); the lookup result decides the action.

```
            doc_id seen?           hash changed?
                │                       │
   ┌────────────┴───────────┐    ┌──────┴──────┐
   no                       yes  no            yes
   │                         │   │              │
INSERT (embed + upsert)      │  SKIP        UPDATE
                             └──────────────►(delete old chunks,
                                              re-embed, upsert)
```

The hash is the whole game. Without it, the pipeline cannot tell "I have seen
this exact content" from "this is new" — so it re-embeds and re-adds
everything, and the vector store accumulates duplicates. (LlamaIndex base skill
failure #3 / A10; `developers.llamaindex.ai/.../loading/ingestion_pipeline/`.)

### Principle 2 — The docstore is a separate ledger, not the vector store

The vector store holds embeddings keyed by node id. The **docstore** holds, per
document, `{doc_id → content_hash}` (and the node ids derived from it). They are
two stores with two jobs:

| Store | Holds | Answers |
|---|---|---|
| Docstore | `doc_id → hash`, doc→node mapping | "have I seen this content before?" |
| Vector store | `node_id → embedding + metadata` | "what is semantically near this query?" |

The dedup decision happens **against the docstore**, *before* any embedding
call — so an unchanged corpus costs zero embedding tokens on re-run. If the
docstore is ephemeral (in-memory, lost on restart), every cold start looks like
a first run and re-embeds the world. **The docstore must be persisted to the
same durability tier as the vector store** (`SimpleDocumentStore.persist()`,
Redis, MongoDB, Postgres). A docstore that doesn't survive the process is not a
docstore.

### Principle 3 — Deletes don't propagate for free

Insert and update are driven by *documents that are present*. A document that
**disappeared** from the source emits no event — so a naive upsert pipeline
never learns it should remove the orphaned chunks. Stale content keeps getting
retrieved long after the source file is gone. Propagating deletes requires the
pipeline to compare the **full set of doc_ids seen this run** against the set in
the docstore, and purge the difference. In LlamaIndex this is the `_AND_DELETE`
half of `DocstoreStrategy.UPSERTS_AND_DELETE`; in LangChain it is
`cleanup="full"` / `cleanup="incremental"`. Choosing the upsert-only strategy
silently accepts stale ghosts — sometimes correct (append-only corpus), usually
not.

---

## 3. SOP 工作流 (Agentic Protocol)

Five stages. Each gates the next. Stop and remediate at the first failure. The
gate that matters most is Stage 4 — *prove the second run is a no-op*.

### Stage 0 — Frame the re-run

Before code, answer:

1. **Run cadence**: how does the pipeline get re-triggered? (cron / webhook /
   CI / manual). If the honest answer is "never, it's one-shot" → this skill is
   over-engineering; stop.
2. **Change shape**: do source docs get *added* only, or also *edited* and
   *deleted*? This decides upsert-only vs upsert-and-delete (Principle 3).
3. **Doc identity**: what is the stable `doc_id`? It must survive across runs —
   a file path, a CMS id, a URL. **Not** a random uuid generated at load time
   (that makes every run look new). LlamaIndex derives a hash from content +
   `doc_id`; if `doc_id` is unstable, idempotency breaks even with a docstore.
4. **Durability tier**: where does the docstore live so it survives restarts?

### Stage 1 — Attach a persisted docstore

```python
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=1024, chunk_overlap=20),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ],
    docstore=SimpleDocumentStore(),          # the dedup ledger
    vector_store=vector_store,               # the embedding store
    docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
)
```

For production, swap `SimpleDocumentStore` for a server-backed one
(`RedisDocumentStore`, `MongoDocumentStore`, `PostgresDocumentStore`) so the
ledger is shared across workers and survives restarts. A `SimpleDocumentStore`
that is never `.persist()`-ed is the #1 cause of "it re-embeds everything every
night".

### Stage 2 — Pin stable doc ids and let the pipeline hash

```python
docs = SimpleDirectoryReader("./data", filename_as_id=True).load_data()
# filename_as_id=True → doc.id_ is the file path → stable across runs.
# LlamaIndex then computes the content hash internally per node.
pipeline.run(documents=docs)
```

Hard rules:

- `doc_id` comes from a **stable external identity** (path / CMS id / URL),
  never a fresh uuid per load. Set `filename_as_id=True` or assign `doc.id_`
  explicitly.
- Do **not** mutate document text in a non-deterministic transformation before
  the hash is taken (e.g. injecting `datetime.now()` into metadata) — that makes
  the hash change every run and defeats the skip path. Keep volatile metadata
  out of the hashed payload.
- The embedding model is part of the index identity: changing it requires a
  **full re-embed** (LlamaIndex base skill A2), not an incremental upsert.

### Stage 3 — Choose the upsert strategy deliberately

| Strategy | Re-run behaviour | Use when |
|---|---|---|
| `UPSERTS` | new+changed docs upserted; deletes **not** propagated | append-mostly corpus; deletes handled out-of-band |
| `UPSERTS_AND_DELETE` | new+changed upserted; vanished docs purged | the corpus is a *mirror* of a source that can shrink |
| `DUPLICATES_ONLY` | dedup identical docs *within one run*; no cross-run update | one-shot batch that may contain dupes; no live sync |

Default for any system that mirrors a mutable source: **`UPSERTS_AND_DELETE`**.
`DUPLICATES_ONLY` is **not** a re-ingest strategy — it only de-dupes within a
single `.run()`; a second `.run()` with the same docs will *not* skip them.

### Stage 4 — Prove the second run is a no-op (the gate)

Before merging, the PR must include — and CI must run — a test that runs the
pipeline **twice** and asserts the second run did nothing observable:

```python
def test_reingest_is_idempotent(pipeline, docs, vector_store):
    n1 = len(pipeline.run(documents=docs))      # cold run
    count_after_first = vector_store.count()

    n2 = len(pipeline.run(documents=docs))       # identical re-run
    count_after_second = vector_store.count()

    assert n2 == 0,                       "re-run re-processed unchanged docs"
    assert count_after_second == count_after_first, "re-run duplicated vectors"
```

`pipeline.run()` returns the list of nodes it actually *processed*; on a
clean idempotent re-run over unchanged input that list is **empty**. If it
isn't, the docstore is missing, ephemeral, or the doc ids / hashes are
unstable — go back to Stage 1-2. Then add the edit case (change one doc → exactly
that doc's chunks replaced) and, for `UPSERTS_AND_DELETE`, the delete case
(remove one doc → its chunks gone, others untouched). See OP-06 / OP-07.

### Stage 5 — Schedule, persist, observe

- Persist the docstore *after every run* (`storage_context.persist()` /
  server-backed store auto-persists) — otherwise the next cold start re-embeds
  everything.
- Run on a schedule, not by hand (LlamaIndex base skill OP-08): cron / Airflow /
  serverless cron. The whole point of idempotency is that a missed-or-doubled
  trigger is harmless.
- Log per run: `{docs_in, inserted, updated, skipped, deleted,
  embedding_calls}`. On a steady-state corpus, `inserted+updated+deleted` should
  trend to ~0 and `skipped ≈ docs_in`. A run that re-embeds everything every
  night is the loud signal that idempotency is broken.

---

## 4. 操作模型 (Operation Models)

Format: **Trigger / Action / Output / Evidence**. Machine-readable in
`intermediate/operation_candidates.json`.

### OP-01 AttachDocstore

- **Trigger**: any `IngestionPipeline` / ingestion path that will run more than
  once with no docstore wired.
- **Action**: pass `docstore=` (persisted: Redis/Mongo/Postgres in prod,
  `SimpleDocumentStore` only for tests) plus `docstore_strategy=`. The docstore
  is the dedup ledger; without it dedup is structurally impossible.
- **Output**: pipeline that can answer "have I seen this content?" before
  embedding.
- **Evidence**: `developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/`; [[llamaindex]] OP-08 / A10.

### OP-02 PinStableDocId

- **Trigger**: docs loaded with random / per-run ids; "re-run re-adds
  everything" symptom.
- **Action**: set `filename_as_id=True` or assign `doc.id_` from a stable
  external identity (path / CMS id / URL). Never a fresh uuid per load.
- **Output**: the same source document hashes to the same key across runs → the
  skip path can fire.
- **Evidence**: LlamaIndex `Document.doc_id` / `SimpleDirectoryReader(filename_as_id=True)` docs.

### OP-03 HashBeforeEmbed

- **Trigger**: designing or reviewing the dedup decision point.
- **Action**: ensure the content hash is computed and looked up in the docstore
  *before* the embedding transformation runs, so unchanged docs cost zero
  embedding tokens. In LlamaIndex this is automatic given a docstore; in a
  manual pipeline, hash first, embed only on miss/change.
- **Output**: re-run cost on a steady corpus ≈ 0 embedding calls.
- **Evidence**: IngestionPipeline dedup section; LangChain indexing API
  ("avoids re-writing unchanged content, avoids re-computing embeddings").

### OP-04 PickUpsertStrategy

- **Trigger**: choosing pipeline behaviour for the corpus's change shape.
- **Action**: `UPSERTS` (append-mostly), `UPSERTS_AND_DELETE` (mirror of a
  shrinkable source — the production default), `DUPLICATES_ONLY` (in-run dedup
  only, **not** cross-run). Decide from Stage 0 change shape, not by default.
- **Output**: documented strategy + one-line rationale.
- **Evidence**: `DocstoreStrategy` enum; LlamaIndex ingestion docs.

### OP-05 PropagateDeletes

- **Trigger**: source docs can be deleted and stale chunks must not be
  retrieved.
- **Action**: use `UPSERTS_AND_DELETE`; the pipeline diffs the doc_ids seen this
  run against the docstore and purges orphans. (LangChain: `cleanup="full"` for
  a full snapshot run, `cleanup="incremental"` for streamed batches.)
- **Output**: deleted source docs → their vectors removed; retrieval stays in
  sync.
- **Evidence**: `DocstoreStrategy.UPSERTS_AND_DELETE`; LangChain `index(...,
  cleanup=...)` docs.

### OP-06 ReingestNoOpTest

- **Trigger**: any ingestion code change merges.
- **Action**: run the pipeline twice over identical input; assert the second
  `run()` returns 0 processed nodes and the vector count is unchanged (Stage 4).
- **Output**: regression gate proving idempotency is wired through.
- **Evidence**: `pipeline.run()` returns processed nodes; direct application of
  Principle 1.

### OP-07 IncrementalUpdateTest

- **Trigger**: corpus supports edits and/or deletes.
- **Action**: edit one doc → assert exactly that doc's old chunks are gone and
  new ones present, others untouched. Delete one doc (under
  `UPSERTS_AND_DELETE`) → assert its chunks gone, neighbours intact.
- **Output**: proof that update/delete are surgical, not full-rebuild.
- **Evidence**: hash-change → update path; delete path of
  `UPSERTS_AND_DELETE`.

### OP-08 PersistDocstore

- **Trigger**: `SimpleDocumentStore` used, or docstore not persisted after run.
- **Action**: `storage_context.persist(persist_dir=...)` after each run, or use
  a server-backed docstore that auto-persists and is shared across workers.
- **Output**: cold start reads the ledger → does not re-embed the world.
- **Evidence**: LlamaIndex storage / persistence docs;
  Redis/Mongo/Postgres docstore integrations.

### OP-09 ManualHashUpsert

- **Trigger**: no framework available (raw vector-store SDK, custom loader).
- **Action**: maintain a `{doc_id → sha256(content)}` table next to the vector
  store; on each doc compute the hash, compare, and INSERT / UPDATE
  (delete-then-add chunks) / SKIP; track seen ids for delete propagation.
- **Output**: framework-free idempotent ingestion with the same contract.
- **Evidence**: this is what `IngestionPipeline` / `RecordManager` automate; see
  R2 cross-framework table.

---

## 5. 困境决策案例 (Dilemma Cases)

### Dilemma 1 — A document changed slightly: re-embed all, or diff?

**困境**: A 200-page handbook had one paragraph edited. The naive idempotent
pipeline hashes at the **document** level → the whole doc's hash changes → all
its chunks are deleted and re-embedded. Correct for safety, but on a large doc a
one-line edit triggers a full re-embed of that document. Should the pipeline
diff at the chunk level instead?

**约束**:
- LlamaIndex's docstore dedup keys on the **document** hash by default — any
  change re-processes the whole document's nodes.
- Chunk-level diffing requires stable chunk identity across edits, but
  `SentenceSplitter` re-segments the whole doc when text shifts, so chunk
  boundaries (and ids) move even for unedited text downstream of the edit.
- Re-embedding one document is usually cheap; re-embedding the *whole corpus*
  every run (the failure this skill prevents) is the expensive thing.

**决策步骤**:
1. Default to **document-level** hashing — it is correct and simple. A
   per-document re-embed on edit is acceptable for most corpora.
2. If single documents are huge *and* edited frequently, **split the source into
   smaller logical documents** (per section / per page) so the hash granularity
   matches the edit granularity — each becomes its own `doc_id`.
3. Only build true chunk-level content-addressed dedup (hash each chunk, stable
   chunk id) if profiling proves per-document re-embed is the real bottleneck.
   It is rarely worth the complexity.

**结果**: Move the granularity by **splitting documents**, not by hand-rolling
chunk-diffing. Document-level hashing stays the default; the fix is upstream in
how the source is segmented into docs.

**可提取的操作**: OP-02, OP-03, OP-04.

### Dilemma 2 — Source documents were deleted: purge from the index, or keep?

**困境**: 50 files were removed from the source folder. The upsert-only pipeline
leaves their chunks in the vector store forever — they keep surfacing in
retrieval and the LLM cites documents that no longer exist. Switch to
`UPSERTS_AND_DELETE`? But what if a run sees a *partial* corpus (a flaky reader
returned only half the files) — would it then delete everything legitimately
missing-this-run?

**约束**:
- `UPSERTS_AND_DELETE` purges any doc_id in the docstore that was **not seen**
  in the current run. If the run's input is incomplete, that purge is
  catastrophic — it deletes live content.
- Therefore delete-propagation is only safe when the run input is a **complete
  snapshot** of the source (LangChain calls this `cleanup="full"`); for streamed
  / partial batches you need `cleanup="incremental"` (per-batch, scoped by
  source).
- Stale chunks are a *correctness* bug (wrong citations); over-aggressive delete
  is an *availability* bug (lost content). Both are bad.

**决策步骤**:
1. Confirm the run input is a **full snapshot**. If the reader can return a
   partial set on failure, gate the delete: abort the run (don't purge) if the
   seen-doc count drops more than a sane threshold vs the previous run.
2. Snapshot + complete → `UPSERTS_AND_DELETE` (LlamaIndex) / `cleanup="full"`
   (LangChain). Streamed batches scoped by source → `cleanup="incremental"`.
3. For regulated corpora, prefer **soft delete** (`deleted=true` metadata +
   query-time filter) over hard delete, so erasure is auditable and reversible.

**结果**: Purge — but only behind a "this is a complete snapshot" guard.
Idempotency for deletes is `UPSERTS_AND_DELETE` *plus* a partial-input circuit
breaker, never a blind diff-and-delete.

**可提取的操作**: OP-05, OP-07, OP-08.

---

## 6. 反模式与边界 (Anti-patterns & Boundaries)

### Top anti-patterns (instant red flags in code review)

| # | Anti-pattern | Why it's wrong | Correct move |
|---|---|---|---|
| A1 | `VectorStoreIndex.from_documents(docs)` re-run every cron tick | No docstore → re-embeds + re-adds everything; vector store grows without bound; duplicates pollute top-k | `IngestionPipeline(docstore=..., docstore_strategy=UPSERTS_AND_DELETE)` (OP-01) |
| A2 | `IngestionPipeline(...)` with no `docstore=` | The dedup decision has nowhere to look up the hash — same as no idempotency | Pass a persisted docstore ([[llamaindex]] A10) |
| A3 | `SimpleDocumentStore()` never `.persist()`-ed | Ledger lost on restart; every cold start looks like a first run | Persist after each run, or use Redis/Mongo/Postgres docstore (OP-08) |
| A4 | Random / per-load `doc_id` (fresh uuid each run) | Same content hashes to a new key each run → nothing ever skips | Stable external id: `filename_as_id=True` / explicit `doc.id_` (OP-02) |
| A5 | Volatile metadata (timestamps, run id) in the hashed payload | Hash changes every run even for unchanged content → constant re-embed | Keep volatile metadata out of the hashed body |
| A6 | `DUPLICATES_ONLY` treated as a re-ingest strategy | Only dedupes *within one run*; a second run does not skip | Use `UPSERTS` / `UPSERTS_AND_DELETE` for cross-run (OP-04) |
| A7 | Upsert-only on a corpus whose source files get deleted | Stale chunks linger; LLM cites deleted docs | `UPSERTS_AND_DELETE` behind a snapshot guard (OP-05, Dilemma 2) |
| A8 | Blind `UPSERTS_AND_DELETE` on a possibly-partial run input | A flaky reader returning half the files purges live content | Gate delete on "complete snapshot"; circuit-break on big drops |
| A9 | No twice-run test in CI | First duplicate / ghost found by a user in production | OP-06 mandatory on every PR |
| A10 | Swapping embedding model and expecting incremental upsert to "fix" old vectors | Old vectors were embedded by the old model; mixed space breaks retrieval | Full re-embed; tag index with model name+version ([[llamaindex]] A2) |

### Boundaries — when this skill is **not** the right move

- **B1** One-shot index, never refreshed → no second run; skip.
- **B2** Corpus tiny enough that full rebuild each run is *measurably* cheaper
  than docstore maintenance → rebuild is fine; but profile before deciding.
- **B3** Append-only event log that never edits or deletes → `UPSERTS` (or even
  plain add) is sufficient; delete propagation is dead weight.
- **B4** The "duplicate results" bug is actually a **chunk-overlap** or
  **retriever top_k** issue, not a re-ingest issue → diagnose first; don't add a
  docstore to a problem it doesn't solve.

### PR review smells

- `from_documents(...)` inside anything that runs on a schedule.
- `IngestionPipeline(...)` with no `docstore=` keyword.
- `SimpleDocumentStore()` and no `persist(` anywhere in the file.
- `doc.id_ = str(uuid4())` / loader without `filename_as_id`.
- `datetime.now()` / `time.time()` written into document metadata *before*
  ingestion.
- `docstore_strategy=DocstoreStrategy.DUPLICATES_ONLY` on a live-sync pipeline.
- A re-ingest function with no test that calls it twice.

---

## 7. 跨框架对照 (Cross-Framework Reference Table)

The same "hash → docstore → insert/update/skip" contract across the common
stacks. Compact below; **full runnable code in `references/R2-cross-framework.md`**.
Verified against current docs (May 2026).

- **LlamaIndex** — `IngestionPipeline(docstore=..., vector_store=...,
  docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE)`. Hash is on the
  document (content + `doc_id`); `pipeline.run(documents=docs)` returns only the
  nodes it *processed* — empty list = clean no-op. Persist the docstore
  (Redis/Mongo/Postgres in prod) to keep idempotency across restarts.
- **LangChain** — `index(docs, SQLRecordManager(...), vectorstore,
  cleanup="full", source_id_key="source")`. The `RecordManager` is the
  docstore-equivalent (a hash per `source_id` in a durable store). Returns
  `{num_added, num_updated, num_skipped, num_deleted}`; on an unchanged re-run
  `num_skipped == len(docs)` and the rest are 0. `cleanup="full"` propagates
  deletes for a complete snapshot, `"incremental"` for source-scoped batches.
- **Manual** — keep a persisted `{doc_id: sha256(text)}` table; per doc:
  `prev == h` → SKIP, `prev` set → delete-then-add (UPDATE), else INSERT; after
  the loop purge `stored_keys − seen` (DELETE); `persist()`. This is exactly
  what the two frameworks automate.

### 7.x Side-by-side: "what happens on the second run?"

| Stack | Mechanism | Unchanged re-run | Deletes propagate? |
|---|---|---|---|
| LlamaIndex `IngestionPipeline` + docstore | document hash in docstore | `run()` returns `[]` | only with `UPSERTS_AND_DELETE` |
| LangChain `index()` + `RecordManager` | hash per `source_id` in SQL/record store | `num_skipped == len(docs)` | only with `cleanup="full"`/`"incremental"` |
| Manual hash table | `{doc_id: sha256}` table | inner loop all `continue` | only if you diff `seen` vs stored keys |
| `from_documents` / raw add (no ledger) | none | re-embeds + re-adds → **duplicates** | never |

The bottom row is the anti-pattern (A1). Every correct row has the same shape:
a persisted hash ledger separate from the vector store, consulted before
embedding, with an explicit delete-propagation switch.

---

## References

### Primary docs (cited inline above)

- LlamaIndex — *Ingestion Pipeline* (docstore dedup, `DocstoreStrategy`):
  https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/
- LlamaIndex — *Document Management* (docstore + UPSERTS):
  https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/document_management/
- LlamaIndex — *Storage / persisting* (docstore durability):
  https://developers.llamaindex.ai/python/framework/module_guides/storing/
- LangChain — *Indexing* (RecordManager, `cleanup`):
  https://python.langchain.com/docs/how_to/indexing/

### Companion files

- `references/R1-source-evidence.md` — claims traced to base [[llamaindex]] skill + primary docs.
- `references/R2-cross-framework.md` — full LlamaIndex / LangChain / manual code with delete-propagation variants.
- `intermediate/operation_candidates.json` — OP-01..09 in machine-readable Trigger / Action / Output / Evidence form.

### Base skill (overlay relationship)

- `[[llamaindex]]` — base RAG SOP. This overlay enhances OP-08
  (`IngestionWithDocstore`) and anti-pattern A10 with the full
  re-ingest-correctness contract.
