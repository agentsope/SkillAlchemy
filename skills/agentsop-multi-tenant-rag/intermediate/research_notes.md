# Research notes — provenance for `multi-tenant-rag` skill v0.1.0

Compiled May 2026 against current vendor docs.

## Vendor docs consulted

- Pinecone `docs.pinecone.io/guides/index-data/implement-multitenancy`
  (recommends one namespace per tenant in serverless; query RU is per-
  namespace size).
- Pinecone `docs.pinecone.io/troubleshooting/namespaces-vs-metadata-filtering`
  (explicit when-to-use rubric; $in capped at 10000 values).
- Pinecone disk-based metadata filtering (2025) — `pinecone.io/blog/optimizing-pinecone/`.
- Weaviate `docs.weaviate.io/weaviate/manage-collections/multi-tenancy`
  (multi-tenancy disabled by default; `multi_tenancy_config(enabled=True)`;
  `auto_tenant_activation` 2025 addition; tenant handle mandatory on CRUD).
- Weaviate `weaviate.io/blog/weaviate-multi-tenancy-architecture-explained`
  (per-shard, scales to millions of tenants).
- Qdrant `qdrant.tech/documentation/manage-data/multitenancy/`
  (single collection + payload partition recommended).
- Qdrant `qdrant.tech/articles/multitenancy/` (`is_tenant=true` payload index
  pattern, custom sharding for <1000-cardinality cases).
- Qdrant `qdrant.tech/blog/qdrant-1.16.x/` (tiered multi-tenancy hot/cold,
  Sept 2025).
- Chroma `docs.trychroma.com/docs/querying-collections/metadata-filtering`
  (`$eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $contains, $not_contains,
  $and, $or`).
- Chroma `cookbook.chromadb.dev/strategies/multi-tenancy/naive-multi-tenancy/`
  (user_id-per-doc strategy explicitly named "naive").
- LlamaIndex `developers.llamaindex.ai/python/examples/vector_stores/qdrant_metadata_filter/`
  (`MetadataFilter`, `MetadataFilters`, `FilterOperator` API, current).
- LlamaIndex `developers.llamaindex.ai/python/framework/integrations/vector_stores/qdrant_hybrid_rag_multitenant_sharding/`
  (custom sharding + filter combined pattern).
- LangChain `python.langchain.com/docs/concepts/vectorstores/` (filter dict
  is forwarded to vendor; no normalisation).

## Security references

- we45 `we45.com/post/rag-systems-are-leaking-sensitive-data` (CVE-2024-41892
  Pinecone post-retrieval RBAC bypass — primary citation for Principle 1).
- CSO Online `csoonline.com/article/4163888/securing-rag-pipelines-in-enterprise-saas.html`
  (EchoLeak Microsoft 365 Copilot, Slack AI Aug 2024 indirect prompt
  injection retrieval bug; "one retrieval filter prevents cross-tenant
  leakage" wording).
- Christian Schneider `christian-schneider.net/blog/rag-security-forgotten-attack-surface/`
  (general framing — RAG is the underspoken attack surface).
- Kiteworks `kiteworks.com/cybersecurity-risk-management/prevent-data-leakage-rag-pipelines/`
  (zero-trust patterns for RAG).
- BeyondScale `beyondscale.tech/blog/vector-database-security-rag-compliance-monitoring`
  (RBAC/ABAC at retrieval, audit logging patterns).

## Real incidents cited in the skill

- **CVE-2024-41892** — Pinecone, 2024. RBAC enforced *after* retrieval; allowed
  cross-namespace sentinel leakage. Canonical proof of Principle 1.
- **EchoLeak** — Microsoft 365 Copilot, late 2025. Unclicked email weaponises
  the RAG corpus.
- **Slack AI** — Aug 2024. Indirect prompt injection combined with RAG-style
  retrieval. Pre-retrieval authorisation was the fix.

## Design decisions

- Picked *namespace + filter* (defence in depth) over *namespace only* even
  for Pinecone — single-layer designs are one config typo from open.
- Refused to recommend any rerank-based filter (Dilemma 3) on security
  grounds — moving the boundary from a deterministic predicate to a
  probabilistic LLM is regression in auditability.
- Did **not** include vendor-specific RBAC features (Pinecone API key project
  scopes, Weaviate's RBAC) — those are infra concerns, not the coder agent's
  remit. Mentioned as Stage 5 layering only.
- Did **not** name OpenSearch, Vespa, ElasticSearch even though they support
  similar patterns — out of scope for "RAG" framing in the gap analysis
  (C6 lists Pinecone/Weaviate/Qdrant/Chroma/pgvector explicitly).

## Non-obvious things the skill must surface (and does)

- Type drift on `tenant_id` (str vs int vs UUID) silently breaks `$eq`
  (Anti-pattern A11).
- Cache keys collapsing across tenants is a leak at a different layer
  (Dilemma 4).
- Mock vector stores in tests that ignore `filter=` create false confidence
  (PR review smells).
- "Unfiltered baseline would have leaked" test — the one most teams forget,
  the one that proves the assertion isn't vacuous (R2 recipe 1, 2, 3).
- Postgres RLS bypass via table owner / superuser — `FORCE ROW LEVEL
  SECURITY` is the fix (R1 §5 gotcha).
