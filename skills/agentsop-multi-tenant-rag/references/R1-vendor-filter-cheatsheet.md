# R1 · Vendor Filter Cheatsheet — Multi-Tenant RAG

Drop-in code blocks for each supported vector store. All snippets assume:

```python
ctx.tenant_id   # bound to authenticated session, never user input
emb             # query embedding from the same model that produced stored vectors
```

The rule is the same everywhere: **the tenant key crosses the vector store
boundary inside the filter argument, not after the call returns.**

---

## 1. Pinecone (serverless)

### Setup — namespace per tenant (preferred)

```python
from pinecone import Pinecone, ServerlessSpec
pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("rag")

# Upsert under tenant namespace
index.upsert(
    namespace=tenant_id,
    vectors=[{
        "id": chunk_id,
        "values": emb,
        "metadata": {"tenant_id": tenant_id,
                     "doc_id":    doc_id,
                     "doc_type":  doc_type},
    }],
)
```

### Query

```python
index.query(
    namespace=ctx.tenant_id,                       # primary
    vector=emb,
    top_k=8,
    filter={"tenant_id": {"$eq": ctx.tenant_id}},  # defence-in-depth
    include_metadata=True,
)
```

### Offboarding (GDPR erasure)

```python
index.delete(delete_all=True, namespace=tenant_id)
```

### Operators

`$eq, $ne, $gt, $gte, $lt, $lte, $in (≤10000), $nin, $and, $or`.
Source: `docs.pinecone.io/guides/index-data/implement-multitenancy`,
`docs.pinecone.io/troubleshooting/namespaces-vs-metadata-filtering`.

### Gotchas

- Namespace argument missing defaults to the empty namespace `""` — not the
  tenant's. Treat as a hard runtime assertion.
- `$in` over a list of tenant ids is capped at 10000 elements — never use
  that pattern for tenancy; namespace per tenant or one filter call per
  tenant.

---

## 2. Weaviate (multi-tenancy enabled)

### Setup

```python
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant

client.collections.create(
    name="Docs",
    multi_tenancy_config=Configure.multi_tenancy(
        enabled=True,
        auto_tenant_activation=True),
)
client.collections.get("Docs").tenants.create([Tenant(name=tenant_id)])
```

### Write / read — `.with_tenant(...)` is mandatory

```python
coll = client.collections.get("Docs").with_tenant(ctx.tenant_id)

# Insert
coll.data.insert(properties={"text": chunk, "doc_type": "policy"},
                 vector=emb)

# Query
res = coll.query.near_vector(near_vector=emb, limit=8)
```

### Combine with property filter

```python
from weaviate.classes.query import Filter
res = coll.query.near_vector(
    near_vector=emb, limit=8,
    filters=Filter.by_property("doc_type").equal("policy"),
)
```

### Why this is "loud-fail"

`coll.query.near_vector(...)` without `.with_tenant()` on a multi-tenant
collection raises — there is no silent fall-through. This is the strongest
default among the vendors here.

Source: `docs.weaviate.io/weaviate/manage-collections/multi-tenancy`.

---

## 3. Qdrant

### Setup — payload index with `is_tenant`

```python
from qdrant_client import QdrantClient, models

client = QdrantClient(url=os.environ["QDRANT_URL"])

client.create_collection(
    collection_name="docs",
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)
client.create_payload_index(
    collection_name="docs",
    field_name="tenant_id",
    field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True),
)
```

### Upsert

```python
client.upsert(
    collection_name="docs",
    points=[models.PointStruct(
        id=chunk_id,
        vector=emb,
        payload={"tenant_id": tenant_id, "doc_id": doc_id, "doc_type": doc_type},
    )],
)
```

### Query (mandatory filter)

```python
client.query_points(
    collection_name="docs",
    query=emb, limit=8,
    query_filter=models.Filter(must=[
        models.FieldCondition(key="tenant_id",
            match=models.MatchValue(value=ctx.tenant_id)),
        models.FieldCondition(key="doc_type",
            match=models.MatchValue(value="policy")),
    ]),
)
```

### Gotchas

- Forgetting `query_filter` returns *all tenants*' points. Silent. Pair with
  OP-10 runtime assertion.
- `is_tenant=True` is purely a *performance* hint (per-tenant sub-indexes);
  it does **not** enforce filtering. The `must=[...]` clause does.

### Tiered multi-tenancy (1.16+)

Hot collection (small/active) + cold archive (`on_disk` payload + vectors).
Same filter shape both sides.

Sources: `qdrant.tech/documentation/manage-data/multitenancy/`,
`qdrant.tech/articles/multitenancy/`, `qdrant.tech/blog/qdrant-1.16.x/`.

---

## 4. Chroma

### Setup

```python
import chromadb
client = chromadb.PersistentClient(path="./store")
coll = client.get_or_create_collection("docs")
```

### Add

```python
coll.add(
    embeddings=[emb],
    documents=[chunk_text],
    metadatas=[{"tenant_id": tenant_id, "doc_id": doc_id, "doc_type": doc_type}],
    ids=[chunk_id],
)
```

### Query

```python
coll.query(
    query_embeddings=[emb], n_results=8,
    where={"$and": [
        {"tenant_id": {"$eq": ctx.tenant_id}},
        {"deleted":   {"$eq": False}},
    ]},
)
```

### Operators

`$eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $contains, $not_contains,
$and, $or`. Source: `docs.trychroma.com/docs/querying-collections/metadata-filtering`.

### Gotchas

- Missing `where` → returns across all tenants. Silent. Wrap the call in a
  helper that always injects `tenant_id`.
- Same `where=` is required on `get/update/delete` — forgotten there too
  leaks via maintenance scripts.

---

## 5. pgvector + Postgres RLS (recommended for Postgres-native stacks)

### Schema

```sql
CREATE TABLE chunks (
    chunk_id   uuid PRIMARY KEY,
    tenant_id  uuid NOT NULL,
    doc_id     uuid NOT NULL,
    body       text NOT NULL,
    embedding  vector(1536) NOT NULL
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks (tenant_id);

ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON chunks
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

### Per-request

```python
with conn.cursor() as cur:
    cur.execute("SET LOCAL app.current_tenant = %s", (ctx.tenant_id,))
    cur.execute("""
        SELECT chunk_id, body, 1 - (embedding <=> %s) AS score
          FROM chunks
         ORDER BY embedding <=> %s
         LIMIT 8
    """, (emb, emb))
```

The application's `SELECT` cannot see other tenants' rows — RLS is enforced
inside Postgres. ORMs, ad-hoc psql, ETL all respect the policy.

### Gotchas

- `SET LOCAL` must be inside the same transaction as the query. A
  connection-pooled bug where it lives outside the txn = open access.
- The superuser / table owner bypasses RLS — make the app role NOT the
  owner and NOT a superuser. `ALTER TABLE ... FORCE ROW LEVEL SECURITY` if
  the app role is also the owner.

---

## 6. LlamaIndex (vendor-agnostic adapter, current API)

```python
from llama_index.core.vector_stores import (
    MetadataFilter, MetadataFilters, FilterOperator, FilterCondition,
)

filters = MetadataFilters(
    filters=[
        MetadataFilter(key="tenant_id", value=ctx.tenant_id,
                       operator=FilterOperator.EQ),
        MetadataFilter(key="doc_type",  value=["policy", "wiki"],
                       operator=FilterOperator.IN),
    ],
    condition=FilterCondition.AND,
)
retriever = index.as_retriever(similarity_top_k=8, filters=filters)
```

Operators: `EQ, NE, GT, LT, GTE, LTE, IN, NIN, TEXT_MATCH`.
Source: `developers.llamaindex.ai/python/examples/vector_stores/qdrant_metadata_filter/`.

Caveat: the in-memory default vector store does not honour filters. Use
Qdrant/Chroma/Pinecone/Weaviate/pgvector for any deployment that matters.

### Auto-retriever with pinned tenant

```python
from llama_index.core.retrievers import VectorIndexAutoRetriever
from llama_index.core.vector_stores import VectorStoreInfo, MetadataInfo

info = VectorStoreInfo(
    content_info="company docs",
    metadata_info=[
        MetadataInfo(name="doc_type", type="str", description="policy|wiki|faq"),
        MetadataInfo(name="date",     type="str", description="ISO yyyy-mm-dd"),
        # NOTE: tenant_id NOT exposed to the auto-retriever
    ],
)
auto = VectorIndexAutoRetriever(
    index, vector_store_info=info,
    extra_filters=MetadataFilters(filters=[
        MetadataFilter(key="tenant_id", value=ctx.tenant_id,
                       operator=FilterOperator.EQ),
    ]),
)
```

The LLM picks `doc_type` / `date` filters; tenant is server-injected.

---

## 7. LangChain (vendor-agnostic adapter)

```python
docs = vectorstore.similarity_search(
    query, k=8,
    filter={"tenant_id": ctx.tenant_id},
)

# Chroma operators pass through:
docs = vectorstore.similarity_search(
    query, k=8,
    filter={"$and": [
        {"tenant_id": {"$eq": ctx.tenant_id}},
        {"deleted":   {"$eq": False}},
    ]},
)
```

LangChain does *not* normalise filter syntax across stores; the dict is
forwarded to the underlying vendor. Test against the actual backend.

---

## 8. Side-by-side fail-mode table

| Stack | Forgot the filter → result | Defence-in-depth recommendation |
|---|---|---|
| Pinecone (namespace only) | Default `""` namespace returned (silent if you ever wrote there) | Add `filter={tenant_id: {$eq: ...}}` |
| Weaviate (MT on) | Client raises (no tenant = no op) | Already loud; combine with property filters for ABAC |
| Qdrant (`is_tenant` only) | Returns all tenants' vectors (silent) | OP-10 runtime assertion mandatory |
| Chroma | Returns all docs (silent) | OP-10 runtime assertion + helper-only access |
| pgvector + RLS | Returns nothing (safe by default) | Make app role non-owner; `FORCE ROW LEVEL SECURITY` |
| LlamaIndex / LangChain | Same as underlying vendor | Same as underlying vendor |

Choose your stack with this table in front of you. "Silent" stacks are not
disqualified — they just require the runtime assertion (OP-10) as a non-
negotiable companion.
