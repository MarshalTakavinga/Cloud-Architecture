# ADR-025: GCP-Track Ingestion, Document Pipeline, and Teradata Translation

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 5 pipeline

## Context

The requirements are the same as on the other tracks. GCP provides:
- **Datastream** (log-based Oracle CDC into BigQuery)
- **Document AI** (OCR and layout)
- Vertex AI embeddings
- **BigQuery Migration Service**, whose translators list Teradata **SQL, BTEQ, and TPT** as fully supported (non-preview)
- **BigQuery Data Transfer Service** for Teradata data

## Decision

- **I1:** **Datastream** (Oracle) → BigQuery bronze, merged into Iceberg-managed tables, ≤ 15 min.
- **I3:** ECM change feed → **Document AI** → Harborline chunker (Dataflow) → **Vertex AI embeddings (US)** → Vector Search (hot/reference), plus BigQuery warm-tier tables with search indexes.
- **Teradata:** BigQuery Migration Service **assessment → batch translation of SQL, BTEQ, and TPT** → GoogleSQL, domain by domain. BigQuery Data Transfer Service moves the historical data, alongside Transfer Appliance for the bulk load.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **A third-party CDC product.** Unnecessary, since Datastream is first-party. It is the fallback if the proof of concept shows latency or coverage gaps.
2. **Rewriting BTEQ by hand.** Rejected, because first-party GA translation exists.

## Consequences

- **Positive:** It has the **broadest first-party Teradata coverage** of the three tracks, since SQL, BTEQ, and TPT are all GA.
- **Negative / accepted trade-off:** Translated logic becomes GoogleSQL. The data stays open, but the logic is platform-shaped.
