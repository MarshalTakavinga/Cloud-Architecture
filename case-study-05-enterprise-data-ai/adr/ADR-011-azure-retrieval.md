# ADR-011: Azure-Track Retrieval — Azure AI Search with the Security-Filter Pattern

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 5 pipeline

## Context

[ADR-003](ADR-003-permission-aware-retrieval.md) requires pre-filtered hybrid search with ACL attributes on every chunk, a final authorization check, and zero leaks. [ADR-006](ADR-006-retrieval-scope-and-chunking.md) requires three tiers: **hot** (hybrid + rerank), **reference** (hybrid, versioned), and **warm** (lexical only). There are about 40M text documents, of which about 25% are in the hot tier.

Azure AI Search offers four approaches to document-level security:
- **Security filters (GA):** the application passes identity attributes as a filter.
- **Native Entra ACL/RBAC enforcement (preview):** supports ADLS Gen2, Blob, SharePoint, and OneLake sources only.
- **Purview sensitivity labels (preview).**
- **SharePoint ACLs (preview).**

Harborline's ECM is not a supported native source.

## Decision

**Azure AI Search** hosts all three tiers as separate indexes:
- **Hot:** vector + BM25 hybrid with the semantic ranker.
- **Reference:** hybrid, with edition and state fields.
- **Warm:** lexical only.

Permissions use the **GA security-filter pattern**:
- Every chunk document carries `line`, `state`, `claim_id`, `assigned_units`, and `restricted` fields. The ACL Sync job updates them by merge, with no re-embedding.
- The Retrieval Service builds the filter from the user's entitlements ([ADR-010](ADR-010-azure-governance-plane.md)) and runs the **final authorization check** on citations.
- Embedding model changes use blue/green index versions behind an alias.

The native Entra ACL feature is **not used**. It is preview, and it does not cover the ECM source.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Mosaic AI Vector Search (Databricks).** Its index is governed as a Unity Catalog object, which strengthens ADR-002. It is vector-first, however, while this design leans on mature hybrid and lexical search plus a semantic ranker, including a lexical-only warm tier over tens of millions of documents. The per-user filter would still be application-supplied metadata. It remains the fallback if AI Search costs or limits bind.
2. **Cortex Search (Snowflake).** Not applicable, since Snowflake was not selected ([ADR-009](ADR-009-azure-data-platform.md)).
3. **Waiting for native ACL enforcement to reach GA and cover ECM.** Rejected, because the assistant timeline cannot depend on an unannounced source connector.

## Consequences

- **Positive:** It is a GA, well-understood filtering mechanism exactly matching ADR-003, with strong hybrid and lexical retrieval for all three tiers.
- **Negative / accepted trade-off:** Security correctness depends on Harborline-built application code (the retrieval service and ACL sync) rather than on the index enforcing identity. The red-team gate ([ADR-007](ADR-007-evaluation-and-release-gating.md)) and the final authorization check are the controls.
- **Negative / accepted trade-off:** Filtered queries over high-cardinality `claim_id` and `assigned_units` fields must be load-tested at 40M-document scale in the pilot.
