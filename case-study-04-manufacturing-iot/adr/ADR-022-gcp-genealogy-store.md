# ADR-022: GCP Genealogy Store — Cloud SQL for PostgreSQL (Insert-Only) + Cloud Storage Bucket Lock

**Status:** Approved (GCP track)
**Date:** Step 8 of the Case Study 4 pipeline

## Context

The requirements for C8 are the same as in [ADR-010](ADR-010-azure-genealogy-store.md) and [ADR-016](ADR-016-aws-genealogy-store.md): 15-year immutability, ADR-004's keyed idempotent insert with conflict detection, a ≤ 5 s per-serial query, ≤ 4 h recall scoping, and EU residency. The volume is about 1.6 TB over 15 years. GCP has no ledger-table equivalent. Cloud Storage **Bucket Lock** makes a retention policy irreversible, so objects cannot be deleted or overwritten until retention expires.

## Decision

**Cloud SQL for PostgreSQL, Enterprise Plus edition, with high availability.** There is one instance per region (us-east5, europe-west3), each with a private IP inside the regional VPC Service Controls perimeter. The design mirrors [ADR-016](ADR-016-aws-genealogy-store.md):

- **Idempotent insert:** a unique index on `(part_number, serial, record_version)`. On a key violation the loader compares hashes: the same hash is a no-op, and a different hash goes to `genealogy_conflict` with an alert. The loader is a Cloud Run subscriber on the `genealogy` topic.
- **Insert-only enforcement:** the application role can only INSERT and SELECT. A trigger blocks `UPDATE` and `DELETE`, and pgAudit plus Cloud Audit Logs record any DDL or change to grants or triggers.
- **Digests and archive:** a nightly Merkle digest and a daily Parquet export are written to **Cloud Storage with a locked 15-year retention policy (Bucket Lock)**.

## Alternatives Considered (rejected, retained here rather than deleted)

1. **Cloud Spanner.** It offers excellent scale and multi-region consistency, but it is oversized for about 1.6 TB, and it has no append-only or ledger primitive either. It would cost more without adding an immutability guarantee.
2. **BigQuery as the system of record.** Rejected, because BigQuery primary keys are **not enforced**, so ADR-004's conflict detection could not be a guarantee at insert time. Genealogy is still *mirrored* to BigQuery for analytics.
3. **AlloyDB.** It is a viable alternative with more headroom. It was not chosen because Cloud SQL is simpler and sufficient at this size, and the immutability model would be the same.

## Consequences

- **Positive:** Standard PostgreSQL means high portability, and Bucket Lock gives a strong immutable anchor for digests and the archive.
- **Negative / accepted trade-off:** As on AWS, immutability of the live table depends on permissions and a trigger, monitored and detectable but not engine-enforced. It is scored the same as AWS in Step 9, below Azure's append-only ledger tables.
