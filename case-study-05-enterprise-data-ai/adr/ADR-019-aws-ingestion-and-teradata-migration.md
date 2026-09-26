# ADR-019: AWS-Track Ingestion, Document Pipeline, and Teradata Translation

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 5 pipeline

## Context

The requirements are ≤ 15-minute CDC from Guidewire's Oracle (NFR-7), the document pipeline ([ADR-006](ADR-006-retrieval-scope-and-chunking.md)), and Teradata translation ([ADR-005](ADR-005-teradata-migration-approach.md)). AWS provides **DMS** for Oracle CDC, **Textract** for OCR and layout, Bedrock embedding models, and **SCT**, which converts Teradata to Redshift, **including BTEQ scripts to Redshift RSQL**.

## Decision

- **I1:** **AWS DMS** (Oracle source, ongoing CDC) → S3 staging → **Glue streaming / EMR Serverless** MERGE into Iceberg bronze, every ≤ 15 minutes.
- **I3:** ECM change feed → **Textract** → Harborline chunker (with citation anchors and ACL attributes) → **Bedrock embedding model** (US) → OpenSearch.
- **Teradata:** **SCT** assessment first, to size the manual rewrite. Then conversion to Redshift SQL, and BTEQ → **RSQL**, domain by domain.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A third-party CDC product.** Unnecessary, since DMS is first-party. It remains the fallback if DMS latency or Oracle-feature coverage falls short in the proof of concept.
2. **Bedrock Knowledge Bases' managed ingestion for documents.** Rejected, because it cannot attach Harborline's structure-aware chunks, citation anchors, and ACL attributes the way ADR-003 and ADR-006 require.

## Consequences

- **Positive:** First-party tooling covers every hard ingestion and migration problem. That means fewer licences and one support path.
- **Negative / accepted trade-off:** **Translated Teradata logic lands as Redshift SQL/RSQL**, which is portable only to Redshift. The *data* stays open (Iceberg), but the *logic* is Redshift-shaped. This is the portability price of first-party translation, and it is scored in Step 9.
