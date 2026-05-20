# R2 · Cross-Tenant Property Tests — Copy-Pasteable Recipes

Five recipes. Drop into the project's `tests/` directory. Each one **must**:

1. Set up at least two tenants with distinct content.
2. Craft a query whose top-k in an unfiltered search *would* be a foreign
   tenant's document — otherwise the test is vacuous.
3. Assert all returned chunks carry the caller's `tenant_id`.
4. Assert symmetric direction (A as the attacker against B's data, and B
   against A's).

If your CI doesn't run one of these, treat the system as unverified.

---

## Recipe 1 — LlamaIndex + Qdrant

```python
# tests/test_cross_tenant_isolation_qdrant.py
import pytest
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.vector_stores import (
    MetadataFilter, MetadataFilters, FilterOperator,
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

@pytest.fixture
def shared_index(tmp_path):
    client = QdrantClient(":memory:")
    client.create_collection(
        "docs",
        vectors_config=models.VectorParams(size=1536, distance="Cosine"))
    client.create_payload_index(
        "docs", "tenant_id",
        field_schema=models.KeywordIndexParams(type="keyword", is_tenant=True))

    vs = QdrantVectorStore(client=client, collection_name="docs")
    idx = VectorStoreIndex.from_documents(
        [Document(text="Alpha's secret widget X1 specs.",
                  metadata={"tenant_id": "alpha"}),
         Document(text="Alpha quarterly review notes.",
                  metadata={"tenant_id": "alpha"}),
         Document(text="Beta confidential Q3 roadmap.",
                  metadata={"tenant_id": "beta"}),
         Document(text="Beta hiring plan.",
                  metadata={"tenant_id": "beta"})],
        vector_store=vs)
    return idx

def _retrieve(idx, tenant):
    return idx.as_retriever(
        similarity_top_k=8,
        filters=MetadataFilters(filters=[
            MetadataFilter(key="tenant_id", value=tenant,
                           operator=FilterOperator.EQ)]),
    )

def test_alpha_cannot_see_beta(shared_index):
    nodes = _retrieve(shared_index, "alpha").retrieve("Q3 roadmap details")
    assert nodes, "test setup invalid: no alpha results at all"
    assert all(n.metadata["tenant_id"] == "alpha" for n in nodes)

def test_beta_cannot_see_alpha(shared_index):
    nodes = _retrieve(shared_index, "beta").retrieve("widget X1 specs")
    assert nodes
    assert all(n.metadata["tenant_id"] == "beta" for n in nodes)

def test_unfiltered_baseline_would_leak(shared_index):
    """Sanity: confirm the unfiltered query *would* have returned foreign."""
    nodes = shared_index.as_retriever(similarity_top_k=4).retrieve(
        "Q3 roadmap details")
    tenants = {n.metadata["tenant_id"] for n in nodes}
    assert "beta" in tenants, (
        "test is vacuous: unfiltered top-k didn't contain beta. "
        "Rewrite the query or corpus.")
```

The third test is the lock — it proves the filter is what's protecting you,
not lucky semantics.

---

## Recipe 2 — LangChain + Chroma

```python
# tests/test_cross_tenant_chroma.py
import pytest
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings   # or any embedder

@pytest.fixture
def vs(tmp_path):
    store = Chroma(
        collection_name="docs",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=str(tmp_path))
    store.add_texts(
        ["Alpha widget X1 schematic.", "Alpha 2025 board minutes."],
        metadatas=[{"tenant_id": "alpha"}, {"tenant_id": "alpha"}])
    store.add_texts(
        ["Beta confidential Q3 roadmap.", "Beta acquisition target list."],
        metadatas=[{"tenant_id": "beta"},  {"tenant_id": "beta"}])
    return store

def test_alpha_isolation(vs):
    out = vs.similarity_search("Q3 roadmap", k=4,
                               filter={"tenant_id": {"$eq": "alpha"}})
    assert out
    assert all(d.metadata["tenant_id"] == "alpha" for d in out)

def test_beta_isolation(vs):
    out = vs.similarity_search("widget X1", k=4,
                               filter={"tenant_id": {"$eq": "beta"}})
    assert out
    assert all(d.metadata["tenant_id"] == "beta" for d in out)

def test_unfiltered_baseline_would_leak(vs):
    out = vs.similarity_search("Q3 roadmap", k=4)
    tenants = {d.metadata["tenant_id"] for d in out}
    assert "beta" in tenants
```

---

## Recipe 3 — Pinecone (namespace + filter belt-and-braces)

```python
# tests/test_cross_tenant_pinecone.py
import os, time, pytest
from pinecone import Pinecone

@pytest.fixture(scope="module")
def index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    idx = pc.Index("test-mt")
    idx.upsert(namespace="alpha", vectors=[
        {"id": "a1", "values": emb("widget X1 specs"),
         "metadata": {"tenant_id": "alpha"}}])
    idx.upsert(namespace="beta", vectors=[
        {"id": "b1", "values": emb("Q3 roadmap"),
         "metadata": {"tenant_id": "beta"}}])
    time.sleep(1)
    yield idx
    idx.delete(delete_all=True, namespace="alpha")
    idx.delete(delete_all=True, namespace="beta")

def query_as(idx, tenant, text, k=4):
    return idx.query(
        namespace=tenant,
        vector=emb(text),
        top_k=k,
        filter={"tenant_id": {"$eq": tenant}},
        include_metadata=True,
    )["matches"]

def test_alpha_query_yields_only_alpha(index):
    hits = query_as(index, "alpha", "Q3 roadmap")
    assert all(h["metadata"]["tenant_id"] == "alpha" for h in hits)

def test_beta_query_yields_only_beta(index):
    hits = query_as(index, "beta", "widget X1 specs")
    assert all(h["metadata"]["tenant_id"] == "beta" for h in hits)

def test_wrong_namespace_with_filter_returns_zero(index):
    """If app code accidentally queries beta's namespace with alpha's filter
       (or vice-versa), result must be empty — not foreign."""
    hits = index.query(
        namespace="beta",
        vector=emb("anything"),
        top_k=4,
        filter={"tenant_id": {"$eq": "alpha"}},
        include_metadata=True,
    )["matches"]
    assert hits == []
```

The third test catches the common "I selected the right namespace but the
filter says a different tenant" config bug.

---

## Recipe 4 — Weaviate (multi-tenancy enabled)

```python
# tests/test_cross_tenant_weaviate.py
import pytest, weaviate
from weaviate.classes.config import Configure
from weaviate.classes.tenants import Tenant

@pytest.fixture(scope="module")
def client():
    c = weaviate.connect_to_local()
    if c.collections.exists("Docs"):
        c.collections.delete("Docs")
    coll = c.collections.create(
        name="Docs",
        multi_tenancy_config=Configure.multi_tenancy(enabled=True))
    coll.tenants.create([Tenant(name="alpha"), Tenant(name="beta")])
    coll.with_tenant("alpha").data.insert(
        {"text": "Alpha widget X1 specs"}, vector=emb("Alpha widget X1 specs"))
    coll.with_tenant("beta").data.insert(
        {"text": "Beta Q3 roadmap"}, vector=emb("Beta Q3 roadmap"))
    yield c
    c.close()

def test_alpha_handle_only_sees_alpha(client):
    coll = client.collections.get("Docs").with_tenant("alpha")
    res = coll.query.near_vector(emb("Q3 roadmap"), limit=4)
    assert res.objects
    assert all(o.properties["text"].startswith("Alpha") for o in res.objects)

def test_missing_tenant_is_loud(client):
    coll = client.collections.get("Docs")  # no .with_tenant
    with pytest.raises(Exception):
        coll.query.near_vector(emb("anything"), limit=4)
```

The "missing tenant is loud" test documents Weaviate's safest-default
property. If a future SDK relaxes it the test catches the regression.

---

## Recipe 5 — pgvector + RLS

```python
# tests/test_cross_tenant_pgvector.py
import psycopg, pytest

@pytest.fixture(scope="module")
def conn(pg_url):
    c = psycopg.connect(pg_url)
    with c.cursor() as cur:
        cur.execute("""
            INSERT INTO chunks (chunk_id, tenant_id, doc_id, body, embedding)
            VALUES (gen_random_uuid(), %s, gen_random_uuid(),
                    'Alpha widget X1 specs', %s),
                   (gen_random_uuid(), %s, gen_random_uuid(),
                    'Beta Q3 roadmap',      %s);
        """, (ALPHA, emb("Alpha widget X1 specs"),
              BETA,  emb("Beta Q3 roadmap")))
    c.commit()
    yield c
    c.close()

def search(conn, tenant, query):
    with conn.cursor() as cur:
        cur.execute("BEGIN")
        cur.execute("SET LOCAL app.current_tenant = %s", (str(tenant),))
        cur.execute("""
            SELECT body, tenant_id
              FROM chunks
             ORDER BY embedding <=> %s
             LIMIT 4
        """, (emb(query),))
        rows = cur.fetchall()
        cur.execute("COMMIT")
    return rows

def test_alpha_session_sees_only_alpha(conn):
    rows = search(conn, ALPHA, "Q3 roadmap")
    assert rows
    assert all(t == ALPHA for _, t in rows)

def test_beta_session_sees_only_beta(conn):
    rows = search(conn, BETA, "widget X1")
    assert all(t == BETA for _, t in rows)

def test_no_setting_returns_nothing(conn):
    """No SET LOCAL app.current_tenant => RLS policy excludes all rows."""
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM chunks")
        (n,) = cur.fetchone()
    assert n == 0
```

The third test is the value proposition of RLS: forgetting the SET LOCAL
makes the query *empty*, not *wide-open*. The opposite of Chroma/Qdrant's
default.

---

## CI checklist

Before this skill is "done" on a project, the CI configuration must:

- Run at least one of Recipes 1–5 against the live stack on every PR.
- Fail the build on a `cross_tenant_leak` log line in any integration test
  (use a log filter assertion).
- Run the unfiltered-baseline test — it documents that the filter is doing
  work; without it the assertion is meaningless.
- Run nightly against a snapshot of production data shape (synthetic, not
  real PII) to catch schema drift.
