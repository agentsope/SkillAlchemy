# R1 · Source Evidence — idempotent-ingestion

This skill is an **ENHANCE overlay** over the base [[llamaindex]] SOP. The base
skill names `IngestionPipeline` + docstore + `UPSERTS_AND_DELETE` as a
production must-have but does **not** surface the re-ingest-correctness
contract: *what idempotency means, how the hash decides the action, and how it
generalises across frameworks*. Each evidence anchor below ties a claim in
`SKILL.md` to its primary source.

---

## S1 · LlamaIndex base skill — IngestionWithDocstore (the seed)

- **Primary (in-repo)**:
  `/Users/5imp1ex/Desktop/Skill-Workplace/output/llamaindex-sop-skill/SKILL.md`
  - **OP-08 IngestionWithDocstore**:
    > "**Trigger**: Documents will update/delete over time (any production
    > system). **Action**: `IngestionPipeline(transformations=..., docstore=...,
    > vector_store=..., docstore_strategy=UPSERTS_AND_DELETE)`. Run on a
    > schedule, not manually. **Output**: Idempotent re-ingestion; no duplicate
    > vectors; deletes propagate. **Evidence**: failure #3."
  - **Anti-pattern A10**:
    > "Ingest once at deploy, never reconcile → `IngestionPipeline` +
    > `docstore` + `UPSERTS_AND_DELETE`."
  - **Stage 5 hardening, non-negotiable #1**:
    > "`IngestionPipeline` with `docstore` + `UPSERTS_AND_DELETE` for any live
    > corpus."
  - **PR-review smell**:
    > "`IngestionPipeline(...)` without `docstore=` → A10."
- **What this overlay adds the base skill does not state**: the *mechanism*
  (document content hash → docstore lookup → insert/update/skip), the
  *no-op-on-re-run* invariant (Principle 1), the docstore-is-a-separate-ledger
  model (Principle 2), delete-doesn't-propagate-for-free (Principle 3), the
  twice-run test gate (Stage 4 / OP-06), and the partial-snapshot delete hazard
  (Dilemma 2).
- **Used in SKILL.md**: Principles 1-3; OP-01, OP-03, OP-04, OP-05, OP-06,
  OP-07, OP-08; A1, A2.

---

## S2 · LlamaIndex Ingestion Pipeline docs — DocstoreStrategy + doc hash

- **Primary**:
  [developers.llamaindex.ai/.../loading/ingestion_pipeline/](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/)
  and the *Document Management* sub-page.
- **Doctrine** (the dedup contract):
  > "Attaching a `docstore` to the ingestion pipeline will enable document
  > management. Using the `doc_id` (or `node.ref_doc_id` as a grounding) of
  > each document, we can handle duplicate documents. The pipeline will
  > de-duplicate based on the hash of the document content and the `doc_id`."
- **`DocstoreStrategy` values**: `UPSERTS` (default — skip unchanged, upsert
  changed/new), `UPSERTS_AND_DELETE` (also delete docs no longer present),
  `DUPLICATES_ONLY` (only check duplicate hashes, no upsert), `NONE`.
- **Persistence**: a `SimpleDocumentStore` must be persisted
  (`storage_context.persist()`) or swapped for `RedisDocumentStore` /
  `MongoDocumentStore` / `PostgresDocumentStore` to survive restarts and be
  shared across workers — otherwise dedup state is lost.
- **Doc identity**: `SimpleDirectoryReader(filename_as_id=True)` sets `doc.id_`
  to the file path, giving a stable cross-run key. A random per-load id defeats
  dedup.
- **Used in SKILL.md**: Principle 1 (hash decision), Principle 2 (docstore as
  ledger), OP-01, OP-02, OP-04, OP-05, OP-08; A3, A4, A6; 7.1 reference impl.

---

## S3 · LangChain Indexing API — RecordManager (cross-framework anchor)

- **Primary**:
  [python.langchain.com/docs/how_to/indexing/](https://python.langchain.com/docs/how_to/indexing/)
- **Doctrine** (the same contract, different names):
  > "The indexing API ... helps avoid writing duplicated content into the
  > vector store and avoid re-writing unchanged content and re-computing
  > embeddings over unchanged content."
- **Mechanism**: a `RecordManager` (e.g. `SQLRecordManager`) stores a hash per
  document keyed by `source_id_key`. `index(docs, record_manager, vectorstore,
  cleanup=..., source_id_key=...)` returns
  `{num_added, num_updated, num_skipped, num_deleted}`.
- **Cleanup modes** (the delete-propagation switch):
  - `cleanup=None` — no delete; append/skip only.
  - `cleanup="incremental"` — per-batch, deletes prior versions of the same
    source; safe for streamed batches scoped by source.
  - `cleanup="full"` — deletes any doc not present in the current (complete
    snapshot) run.
- **Used in SKILL.md**: OP-03, OP-04, OP-05; Principle 3; Dilemma 2 (full vs
  incremental and the partial-input hazard); 7.2 reference impl; 7.4 table.

---

## S4 · Storage durability — the "re-embeds everything every night" failure

- **Primary**: LlamaIndex *Storage* module guide
  ([developers.llamaindex.ai/.../storing/](https://developers.llamaindex.ai/python/framework/module_guides/storing/))
  and the docstore integration pages (Redis / Mongo / Postgres).
- **Failure shape**: an in-memory `SimpleDocumentStore` not persisted means the
  hash ledger evaporates on process restart, so the next cold run sees an empty
  ledger and treats every document as new — re-embedding the entire corpus.
  This is the single most common idempotency regression in the wild and the
  loud observability signal (`embedding_calls ≈ corpus_size` on a steady-state
  re-run).
- **Used in SKILL.md**: Principle 2 (durability tier), Stage 5 (persist after
  every run + observability counters), OP-08, A3.

---

## Cross-source synthesis

Every source tells the same story under different names:

1. A correct ingestion pipeline keeps a **persisted hash ledger separate from
   the vector store** (LlamaIndex `docstore`, LangChain `RecordManager`, a
   manual `{doc_id: sha256}` table).
2. The ledger is consulted **before embedding**, so the **second run over
   unchanged docs is a no-op** — zero duplicate vectors, zero wasted embedding
   tokens.
3. **Deletes do not propagate for free** — they need an explicit switch
   (`UPSERTS_AND_DELETE` / `cleanup="full"|"incremental"`) and a
   complete-snapshot guard so a partial run doesn't purge live content.

The base [[llamaindex]] skill prescribes the LlamaIndex incantation; this
overlay codifies *why* and generalises the contract so a coder agent applies it
correctly across any RAG stack and can prove it with a twice-run test.
