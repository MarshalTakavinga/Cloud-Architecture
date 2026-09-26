# ADR-013: Azure-Track Ingestion, Document Pipeline, and Teradata Translation

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 5 pipeline

## Context

- **CDC (I1):** ≤ 15 minutes from Guidewire's Oracle databases (NFR-7).
- **Document pipeline (I3):** OCR and layout extraction, structure-aware chunking, and embedding for the tiers in [ADR-006](ADR-006-retrieval-scope-and-chunking.md).
- **Teradata translation ([ADR-005](ADR-005-teradata-migration-approach.md)):** about 1,800 procedures and macros plus BTEQ scripts.

Fabric mirroring for Oracle (LogMiner + on-premises gateway) is Microsoft's native CDC, but it lands in OneLake mirrored databases. [ADR-009](ADR-009-azure-data-platform.md) selected Databricks on ADLS.

## Decision

- **I1:** a **log-based Oracle CDC product** replicating into ADLS as Delta bronze tables, over ExpressRoute. Procurement picks the product. The requirement is Oracle redo-log capture, exactly-once apply, and ≤ 15-minute latency.
- **I3:** Databricks jobs consume the ECM change feed, then:
  - **Azure AI Document Intelligence** extracts text and layout (OCR for scans)
  - Harborline's chunker splits by structure and adds citation anchors and ACL attributes
  - **Azure OpenAI embeddings** (Data Zone US) embed the chunks
  - the chunks are pushed to the AI Search tiers
- **Teradata translation:** **Databricks Lakebridge**, applied domain by domain (ADR-005), with Lakebridge's assessment output used to size the manual rewrite before any commitment.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Fabric mirroring for Oracle into OneLake, with Databricks reading it through a shortcut.** Considered as the native option. Rejected because it would split bronze across two storage and governance planes, although it stays viable if the CDC procurement fails.
2. **SnowConvert AI for translation into Databricks SQL.** Not applicable, since SnowConvert targets Snowflake.
3. **Nightly Informatica into the lakehouse.** Rejected. It fails NFR-7 and extends a tool being retired.

## Consequences

- **Positive:** One bronze layer on ADLS, with one governance plane over everything that lands.
- **Negative / accepted trade-off:** A third-party CDC product adds a licence and a vendor. This is scored under cost and operations.
- **Negative / accepted trade-off:** Lakebridge's real coverage on Harborline's Teradata code is unproven until the Step 11 proof of concept, and the migration timeline depends on it.
