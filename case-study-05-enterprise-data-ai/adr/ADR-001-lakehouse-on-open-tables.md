# ADR-001: Analytical Platform — Lakehouse on an Open Table Format

**Status:** Approved
**Date:** Step 4 of the Case Study 5 pipeline

## Context

Harborline must leave Teradata (driver 3). It also needs one governed copy of data that serves SQL analytics, BI, actuarial notebooks replacing SAS, and the retrieval pipelines behind the claims assistant (drivers 1, 2, and 4). NFR-12 requires an **open table format readable by more than one engine**. That requirement was written directly from the Teradata experience: 12 years of data in a format only one vendor's engine can read, priced at that vendor's discretion.

## Decision

Build a **lakehouse on an open table format** (Apache Iceberg or Delta Lake), laid out as a **medallion**:

- **Bronze:** raw data exactly as landed from CDC, files, and feeds.
- **Silver:** cleaned and conformed data, including the unified customer, policy, claim, and loss model (driver 4).
- **Gold:** business-ready marts for reserving, regulatory reporting, and BI.

The table format is decided per platform track in Steps 6–8. It must be readable by at least one engine other than the one that writes it.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Teradata's cloud offering.** It is the fastest way off the aging hardware, but it keeps the proprietary format and pricing that driver 3 is meant to escape. It fails NFR-12.
2. **A cloud warehouse with proprietary managed storage as the system of record.** Rejected at the *storage* layer only. Warehouse *engines* stay eligible as query engines over open tables, and several now support that directly.
3. **A data lake plus a separate warehouse.** It means two copies, two security models, and duplicated cost, with governance split across both.

## Consequences

- **Positive:** One governed copy serves every workload, the AI pipelines included. A future engine change becomes a compute decision, not a data migration.
- **Positive:** The medallion layout gives the Teradata migration a natural shape. Translated logic lands in silver and gold, while bronze keeps raw history for reprocessing.
- **Negative / accepted trade-off:** Open-format tables need catalog and maintenance discipline (compaction, snapshot expiry, schema evolution) that a managed warehouse hides. The platform chosen must automate it, and this is scored under operational fit in Step 9.
- **Negative / accepted trade-off:** "Readable by another engine" has to be *tested*, not assumed. Each platform track must name the second engine and show a real read path.
