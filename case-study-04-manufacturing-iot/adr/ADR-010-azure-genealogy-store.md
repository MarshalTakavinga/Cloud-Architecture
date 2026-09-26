# ADR-010: Azure Genealogy Store — Azure SQL Hyperscale with Append-Only Ledger Tables

**Status:** Approved (Azure track)
**Date:** Step 6 of the Case Study 4 pipeline

## Context

C8 must meet four requirements:
- keep genealogy records **immutably for 15 years** (NFR-8)
- enforce [ADR-004](ADR-004-genealogy-exactly-once-record-path.md)'s idempotent insert on `(part number, serial, record version)`, where the same hash is a no-op and a different hash raises an exception
- answer per-serial queries in ≤ 5 s and recall scoping in ≤ 4 h (NFR-7)
- keep EU records in the EU (NFR-10)

Working volume assumption: about 35 million serialized safety-critical parts per year across both regions (about 28 million US/MX and 7 million DE), at about 3 KB per record including the process-parameter snapshot. That is roughly **105 GB per year, or about 1.6 TB over 15 years** before indexes. It is modest in size but long in duration, and it must be tamper-evident, which is what an OEM supplier-quality audit asks for.

## Decision

Use **Azure SQL Database Hyperscale**, one database per region (East US 2 and Germany West Central), with genealogy stored in **append-only ledger tables**:

- **Idempotent insert:** there is a unique index on `(part_number, serial, record_version)`. The loader (an Azure Function consuming the `genealogy` event hub) inserts each record. On a key violation it compares content hashes: the same hash is a no-op, and a different hash writes to a separate `genealogy_conflict` table and raises a quality-system alert. **Nothing is ever updated or deleted.** Append-only ledger tables reject `UPDATE` and `DELETE` at the engine level, which enforces ADR-004's "never update in place" in the database itself rather than only in application code.
- **Tamper evidence:** ledger database digests are stored automatically in **immutable Azure Blob storage**, so any after-the-fact alteration of the table history is detectable. This complements, rather than replaces, the plant-side hash chain from ADR-004. Nightly verification compares each plant's journal chain head with the loaded records.
- **Queries:** there are indexes on serial, material lot, tooling ID, asset, and production time. A per-serial lookup is a single indexed read. Recall scoping by lot or tool across 15 years is an indexed range query, completing in minutes rather than hours.
- **Retention and portability:** all 15 years stay in the ledger table. Rows cannot be deleted, so there is no "archive and delete" tier, and Hyperscale's storage ceiling is well above the projected size. A daily export also goes to an **immutable (WORM, time-based retention) Blob container** as Parquet. This is a platform-independent 15-year copy for exit or for disaster recovery.
- **Residency and DR:** the EU database and its backups stay in Germany. Geo-redundant backup pairs Germany West Central with Germany North. Access is by private endpoint only.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Azure Cosmos DB.** Point reads by serial would be excellent. Rejected because recall scoping is an ad hoc, multi-attribute query ("every serial with this lot, *and* machined while this parameter was out of range"), which is expensive and awkward across partitions. It also has no engine-enforced append-only or ledger guarantee, so immutability would rest on application discipline.
2. **Store genealogy only in the Fabric Eventhouse or Lakehouse.** Rejected as the system of record. Neither enforces a **uniqueness constraint**, so ADR-004's conflict detection would become an after-the-fact check instead of a guarantee at insert time. Genealogy is still *mirrored* into the Lakehouse for analytics such as correlating process parameters with quality.
3. **Immutable Blob storage alone.** Rejected as the query store. It gives excellent immutability but cannot meet the ≤ 5 s per-serial query without a separate index, which would then be the real store. It is retained as the portability archive.

## Consequences

- **Positive:** Immutability and uniqueness are enforced **by the database engine**, which is the strongest guarantee among the options and a direct carry-over of what made Azure SQL Ledger decisive in Case Study 2's decision matrix.
- **Positive:** Two independent integrity mechanisms (the plant hash chain and the SQL ledger digests) mean an auditor does not have to trust any single component.
- **Negative / accepted trade-off:** Append-only means a genuinely wrong record (for example, a mis-scanned material lot) can only be corrected by appending a new record version that supersedes it. That is the correct quality-system behavior, but query logic must always resolve "latest version", which is built into the recall query service views.
- **Negative / accepted trade-off:** Two regional databases double the operational surface. A recall that spans both regions (a lot used in both the US and Germany) runs as two queries whose *results* are combined. No raw EU records are moved.
