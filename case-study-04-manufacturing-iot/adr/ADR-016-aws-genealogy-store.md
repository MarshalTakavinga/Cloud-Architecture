# ADR-016: AWS Genealogy Store — Aurora PostgreSQL (Insert-Only) + S3 Object Lock

**Status:** Approved (AWS track)
**Date:** Step 7 of the Case Study 4 pipeline

## Context

C8 must be immutable for 15 years (NFR-8), enforce [ADR-004](ADR-004-genealogy-exactly-once-record-path.md)'s idempotent keyed insert with conflict detection, answer per-serial queries in ≤ 5 s and recall scoping in ≤ 4 h (NFR-7), and keep EU records in the EU. The volume is about 105 GB a year, about 1.6 TB over 15 years (see [ADR-010](ADR-010-azure-genealogy-store.md)).

AWS's purpose-built ledger database, **Amazon QLDB, reached end of support on 31 July 2025**. AWS named **Aurora PostgreSQL** as the migration target, with pgAudit, S3, and Aurora Database Activity Streams as replacements for QLDB's journal, history, and streams. AWS has no engine-level equivalent of Azure SQL's append-only ledger tables.

## Decision

**Amazon Aurora PostgreSQL**, one cluster per region (us-east-2 and eu-central-1), Multi-AZ:

- **Idempotent insert:** a unique index on `(part_number, serial, record_version)`. The loader (a Lambda consuming the Kinesis `genealogy` stream) inserts records. On conflict it compares content hashes: the same hash is a no-op, and a different hash is written to `genealogy_conflict` and raises a quality-system alert.
- **Insert-only enforcement:**
  - The application role has **INSERT and SELECT only**.
  - A `BEFORE UPDATE OR DELETE` trigger raises an exception for *any* role.
  - Changes to that trigger or to role grants are captured by **Database Activity Streams** and alerted on.
  - **pgAudit** logs all DDL.
- **Tamper evidence:**
  - Each row stores the plant's hash-chain link (ADR-004).
  - A nightly job computes a regional digest (a Merkle root over the day's records) and writes it to **S3 Object Lock in compliance mode**, so later alteration of the table is detectable against a digest that no one, including the root account, can delete during the retention period.
- **Retention and portability:** a daily Parquet export also goes to **S3 Object Lock (compliance mode, 15-year retention)**. Aurora holds all 15 years online, since about 1.6 TB is within Aurora's storage limits.
- **Queries:** indexes on serial, lot, tool, asset, and time, as in ADR-010.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Amazon QLDB.** Retired. It is recorded because it would have been the natural choice, and its retirement is direct evidence for the vendor-churn risk.
2. **Amazon DynamoDB, with Streams to an S3 Object Lock archive.** Point lookups by serial would be excellent. Rejected for the same reason Cosmos DB was on Azure: multi-attribute recall scoping is awkward and expensive, and insert-only would rest entirely on IAM policy.
3. **S3 Object Lock only.** Rejected as the query store, as on Azure. It is retained as the archive and digest store.

## Consequences

- **Positive:** A standard PostgreSQL engine gives the most portable genealogy store of the three tracks.
- **Positive:** S3 Object Lock compliance mode gives a strong, independently verifiable immutability anchor for digests and the archive.
- **Negative / accepted trade-off:** Immutability of the **live table** is enforced by privileges and a trigger, and monitored, **not by the engine itself**. A sufficiently privileged administrator could disable the trigger. That would be detected by activity streams and by digest mismatch, but not prevented. This is weaker than Azure's engine-enforced append-only ledger ([ADR-010](ADR-010-azure-genealogy-store.md)) and is scored accordingly under regulatory/quality evidence in Step 9.
- **Negative / accepted trade-off:** The digest job, trigger, and monitoring are Kestrel-built controls that must be tested and evidenced for OEM audits. On Azure, the equivalent is a platform feature.
