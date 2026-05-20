# R2 · Cross-Framework Reference — Idempotent Ingestion

Drop-in code for each stack. All snippets assume:

```python
docs            # list of documents with STABLE ids (path / CMS id / URL)
vector_store    # any backend that supports keyed upsert + delete-by-metadata
embed_model     # the SAME embedding model that produced the stored vectors
```

The contract is identical everywhere: **hash each doc → look it up in a
persisted ledger → insert / update / skip → purge orphans → persist.** Only the
names change.

---

## 1. LlamaIndex — `IngestionPipeline` + docstore (reference impl)

### Setup

```python
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding

docstore = SimpleDocumentStore()              # prod: Redis/Mongo/Postgres
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=1024, chunk_overlap=20),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ],
    docstore=docstore,
    vector_store=vector_store,
    docstore_strategy=DocstoreStrategy.UPSERTS_AND_DELETE,
)
```

### Stable ids + run

```python
from llama_index.core import SimpleDirectoryReader, StorageContext

docs = SimpleDirectoryReader("./data", filename_as_id=True).load_data()
nodes = pipeline.run(documents=docs)          # processed nodes; [] on no-op re-run
pipeline.persist("./pipeline_storage")        # persist the dedup ledger
```

### Production docstore (survives restarts, shared across workers)

```python
from llama_index.storage.docstore.redis import RedisDocumentStore
docstore = RedisDocumentStore.from_host_and_port("localhost", 6379,
                                                 namespace="rag_docstore")
```

### Idempotency test

```python
def test_reingest_no_op(pipeline, docs, vector_store):
    pipeline.run(documents=docs)
    base = vector_store.count()
    second = pipeline.run(documents=docs)
    assert len(second) == 0
    assert vector_store.count() == base
```

---

## 2. LangChain — indexing API + `RecordManager`

### Setup

```python
from langchain.indexes import index, SQLRecordManager

record_manager = SQLRecordManager(
    namespace="rag/my_corpus",
    db_url="postgresql+psycopg://user:pass@host/db",  # durable; not in-memory
)
record_manager.create_schema()
```

### Run with delete propagation

```python
result = index(
    docs,
    record_manager,
    vectorstore,
    cleanup="full",            # "full" = complete-snapshot purge of vanished docs
    source_id_key="source",    # stable per-doc identity (the doc_id analogue)
)
# result == {"num_added": .., "num_updated": .., "num_skipped": .., "num_deleted": ..}
```

### Cleanup mode decision

| Mode | Deletes? | Use when |
|---|---|---|
| `None` | no | append-only; deletes handled out of band |
| `"incremental"` | per-batch, scoped by `source_id` | streamed / chunked batches |
| `"full"` | any doc absent from this run | the run is a **complete snapshot** |

### Idempotency test

```python
def test_reingest_no_op(docs):
    index(docs, rm, vs, cleanup="full", source_id_key="source")
    r = index(docs, rm, vs, cleanup="full", source_id_key="source")
    assert r["num_skipped"] == len(docs)
    assert r["num_added"] == r["num_updated"] == r["num_deleted"] == 0
```

---

## 3. Manual hash table (no framework)

```python
import hashlib, json, os

class HashLedger:
    """Persisted {doc_id: content_hash}. The docstore, by hand."""
    def __init__(self, path): self.path = path; self._load()
    def _load(self):
        self.m = json.load(open(self.path)) if os.path.exists(self.path) else {}
    def get(self, k): return self.m.get(k)
    def set(self, k, v): self.m[k] = v
    def delete(self, k): self.m.pop(k, None)
    def keys(self): return set(self.m)
    def persist(self): json.dump(self.m, open(self.path, "w"))

def doc_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def ingest(docs, ledger: HashLedger, vs, embed, split):
    seen = set()
    for d in docs:
        seen.add(d.id)
        h = doc_hash(d.text)
        prev = ledger.get(d.id)
        if prev == h:
            continue                                  # SKIP — unchanged
        if prev is not None:
            vs.delete(where={"doc_id": d.id})         # UPDATE — drop old chunks
        chunks = split(d.text)
        vs.add([embed(c) for c in chunks], doc_id=d.id)  # INSERT/UPDATE
        ledger.set(d.id, h)
    for orphan in ledger.keys() - seen:               # DELETE — vanished docs
        vs.delete(where={"doc_id": orphan})
        ledger.delete(orphan)
    ledger.persist()                                  # durability (Principle 2)
```

### Partial-snapshot guard (Dilemma 2)

```python
def ingest_guarded(docs, ledger, vs, embed, split, prev_count, max_drop=0.5):
    if prev_count and len(docs) < prev_count * (1 - max_drop):
        raise RuntimeError("input shrank too much; refusing to purge — "
                           "likely a partial/failed read, not real deletes")
    ingest(docs, ledger, vs, embed, split)
```

---

## 4. "What happens on the second run?" — the decisive table

| Stack | Ledger | Unchanged re-run | Edit one doc | Delete one source doc |
|---|---|---|---|---|
| LlamaIndex `IngestionPipeline` + docstore | docstore (`doc_id`→hash) | `run()` → `[]` | only that doc's nodes re-embedded | purged only with `UPSERTS_AND_DELETE` |
| LangChain `index()` + `RecordManager` | RecordManager (SQL) | `num_skipped == N` | `num_updated == 1` | `num_deleted == 1` only with `cleanup="full"`/`"incremental"` |
| Manual hash table | `{doc_id: sha256}` file/DB | inner loop all `continue` | delete-then-add for that id | orphan purge via `keys - seen` |
| `from_documents` / raw add (no ledger) | none | re-embeds + re-adds → **DUPLICATES** | adds a second copy | never removed → **STALE GHOST** |

The bottom row is anti-pattern A1. Every correct row shares the same four moves:
**(1)** a persisted hash ledger separate from the vector store, **(2)** consulted
before embedding, **(3)** with an explicit delete-propagation switch, **(4)**
provable by a twice-run test.
